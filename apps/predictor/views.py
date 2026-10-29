"""Predictor views: upload, predict, result, history, PDF download."""
from __future__ import annotations

import io
import json
import logging
import math
import secrets
from pathlib import Path

from PIL import Image as PILImage

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import get_valid_filename
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.common.services.ai_api import NonSkinImageError, validate_skin_image
from apps.common.services.prediction import (
    InvalidImageError, ModelNotLoadedError, PredictionError, PredictionService,
    confidence_to_fraction,
)
from apps.common.services.phone_prediction import (
    PhoneImagePredictionService, PhoneInvalidImageError,
    PhoneModelNotLoadedError, PhonePredictionError,
    phone_confidence_to_fraction, _PhoneAPIBackend,
)
from apps.common.services.image_quality import ImageQualityService
from apps.common.services.reliability import ReliabilityService
from apps.common.services.wrong_input import WrongInputService
from apps.common.services.pdf_report import PdfReportService
from apps.common.services._hydrate import hydrate

from .forms import ImageUploadForm, PhoneImageMetadataForm
from .models import PredictionRecord

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 10 * 1024 * 1024


def _new_reference_id() -> str:
    return secrets.token_hex(8).upper()


def _save_pil_image_to_field(record: PredictionRecord, pil_image: PILImage, original_name: str):
    """Save a PIL image to the record.image field as JPEG."""
    buf = io.BytesIO()
    pil_image.convert("RGB").save(buf, format="JPEG", quality=92)
    safe_name = get_valid_filename(original_name.strip())[:100] or "patient"
    record.image.save(
        f"{safe_name}_{record.reference_id}.jpg",
        ContentFile(buf.getvalue()),
        save=False,
    )


def _resolve_session_key(request) -> str:
    """Return the visitor's session key, ensuring the session exists."""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key or ""


def _scope_queryset(request):
    """Return a queryset of PredictionRecords visible to this request.

    - Authenticated user → their own records only.
    - Anonymous visitor → records created in this session (via session_key).
      Records with session_key='' (legacy) are link-only.
    """
    if request.user.is_authenticated:
        return PredictionRecord.objects.filter(user=request.user)
    sk = _resolve_session_key(request)
    return PredictionRecord.objects.filter(session_key=sk)


@require_http_methods(["GET", "POST"])
def upload_view(request):
    """Upload + predict + report page. Single endpoint for simplicity."""
    if request.method == "POST":
        return _handle_upload(request)
    form = ImageUploadForm()
    return render(request, "predictor/upload.html", _upload_context(form))



def _upload_context(form, **extra):
    """Shared context for every render of predictor/upload.html.

    Keeps the unified upload card's two prediction buttons + the
    supported-category cards working across every error path in
    _handle_upload.
    """
    ctx = {
        "form": form,
        "classes": PredictionService.class_metadata(),
        "phone_classes": PhoneImagePredictionService.class_metadata(),
        "phone_model_configured": PhoneImagePredictionService.is_configured(),
        "prediction_min_quality_score": settings.PREDICTION_MIN_QUALITY_SCORE,
    }
    ctx.update(extra)
    return ctx


def _handle_upload(request):
    """Process an upload: validate, quality-check, predict, optionally
    reliability-check, save, and redirect to the result page."""
    form = ImageUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        # Surface the actual form errors instead of a generic message so
        # the user knows what went wrong (file type, file size, missing).
        error_msg = "Please correct the errors below."
        if form.errors:
            try:
                first_field = next(iter(form.errors))
                error_msg = "; ".join(form.errors[first_field])
            except Exception:
                pass
        return render(request, "predictor/upload.html", _upload_context(form, error=error_msg))

    uploaded = request.FILES["image"]
    if uploaded.content_type not in ALLOWED_TYPES:
        return render(request, "predictor/upload.html", _upload_context(
            form, error=f"Unsupported file type {uploaded.content_type!r}. Use JPG, PNG, or WEBP."
        ))
    if uploaded.size > MAX_BYTES:
        return render(request, "predictor/upload.html", _upload_context(form, error=f"File too large ({uploaded.size//1024} KB). Maximum is 10 MB."))

    # Read bytes once
    image_bytes = uploaded.read()
    uploaded.seek(0)

    # Gate every upload through the separate Skin/Non-Skin API before any
    # lesion prediction. Existing validation and prediction paths continue
    # unchanged after the API confirms the image is skin.
    try:
        validate_skin_image(
            image_bytes,
            filename=uploaded.name,
            content_type=uploaded.content_type,
        )
    except NonSkinImageError:
        return render(request, "predictor/upload.html", _upload_context(
            form,
            error=(
                "This image was classified as non-skin. Please upload a clear "
                "photo of a skin lesion to continue."
            )
        ))
    except PredictionError:
        logger.exception("Skin/non-skin validation failed.")
        return render(request, "predictor/upload.html", _upload_context(
            form,
            error="Image validation could not be completed. Please try again later."
        ))

    # Wrong-input protection (corrupt file / non-skin)
    wrong_report, pil_image = WrongInputService.validate_bytes(image_bytes)
    if not wrong_report.is_valid_image or not pil_image:
        return render(request, "predictor/upload.html", _upload_context(form, error=wrong_report.warning, details=wrong_report.details, suggestions=wrong_report.suggestions))

    # Quality check
    try:
        quality_report = ImageQualityService.assess_pil(pil_image)
    except Exception as e:
        logger.warning("Quality check failed: %s", e)
        quality_report = None

    # Predict
    # When the backend is the FastAPI ``api`` backend, forward the
    # ORIGINAL uploaded file to FastAPI — not a PIL-re-encoded version.
    # This guarantees the prediction matches what FastAPI's own Swagger
    # UI returns for the same image (no JPEG re-compression round-trip).
    # For local backends (mock / keras / onnx), keep using the PIL image
    # we already opened (so quality + reliability checks share the same
    # pixels).
    try:
        from apps.common.services.prediction import _APIBackend, PredictionService as _PS
        backend = _PS._resolve_backend()
        if isinstance(backend, _APIBackend):
            # Rewind the uploaded file so FastAPI sees the full bytes.
            uploaded.seek(0)
            prediction = _PS.predict_uploaded(uploaded)
        else:
            prediction = PredictionService.predict_pil(pil_image)
    except InvalidImageError as e:
        return render(request, "predictor/upload.html", _upload_context(form, error=f"Could not process image: {e}"))
    except ModelNotLoadedError as e:
        return render(request, "predictor/upload.html", _upload_context(form, error=f"Model is not loaded. {e}"))
    except PredictionError:
        logger.exception("Prediction failed.")
        return render(request, "predictor/upload.html", _upload_context(form, error="Prediction could not be completed. Please try again later."))

    # Reliability check (run automatically; user can ignore if not interested)
    try:
        reliability_report = ReliabilityService.assess_pil(pil_image)
    except Exception as e:
        logger.warning("Reliability check failed: %s", e)
        reliability_report = None

    # Save record — scope by user OR session_key for anonymous visitors
    session_key = "" if request.user.is_authenticated else _resolve_session_key(request)
    # ``patient_name`` is accepted only for compatibility with older clients.
    # New uploads store an image label and leave personal patient details empty.
    legacy_patient_name = (request.POST.get("patient_name") or "").strip()
    image_name = (
        form.cleaned_data["image_name"].strip()
        or legacy_patient_name
        or Path(uploaded.name).stem
        or "skin-image"
    )[:255]
    record = PredictionRecord(
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key,
        reference_id=_new_reference_id(),
        image_name=image_name,
        patient_name=legacy_patient_name,
        predicted_class=prediction.predicted_class,
        predicted_name=prediction.predicted_name,
        category=prediction.category,
        confidence=prediction.confidence,
        probabilities=prediction.probabilities,
        quality_report=quality_report.as_dict() if quality_report else {},
        reliability_report=reliability_report.as_dict() if reliability_report else {},
        wrong_input_report=wrong_report.as_dict(),
        backend=prediction.backend,
        # The existing /predict/ upload endpoint uses the HAM10000
        # dermoscopic model — explicitly tag the record so the result
        # template knows to render the seven-class probability table.
        model_type="dermoscopic",
    )
    _save_pil_image_to_field(record, pil_image, record.image_name)
    record.save()

    return redirect("predictor:result", reference_id=record.reference_id)


def result_view(request, reference_id: str):
    """Display a saved prediction record with all attached reports."""
    record = get_object_or_404(PredictionRecord, reference_id=reference_id)
    # Privacy: anonymous session-scoped records are visible only from the
    # same session; user-linked records require the owner. Legacy records
    # (session_key='' AND user IS NULL) remain link-only.
    if (
        record.user is not None
        and record.user != request.user
        and not request.user.has_perm("predictor.view_medical_priority_queue")
    ):
        return HttpResponseForbidden("This prediction record is private to its owner.")
    if (
        record.user is None
        and record.session_key
        and not request.user.has_perm("predictor.view_medical_priority_queue")
    ):
        # anonymous + session-scoped → require same session
        if _resolve_session_key(request) != record.session_key:
            return HttpResponseForbidden("This prediction record belongs to a different session.")

    # Hydrate the saved JSON dicts into attribute-access objects so the
    # template can use the same attribute syntax as live objects. This
    # replaces the fragile per-page _QualityDTO class.
    quality = hydrate(record.quality_report) if record.quality_report else None
    reliability = hydrate(record.reliability_report) if record.reliability_report else None
    wrong_input = hydrate(record.wrong_input_report) if record.wrong_input_report else None

    # Choose the right class metadata based on which workflow produced
    # this record. Phone records (SkinDisNet) use the 6-class list;
    # dermoscopic records (HAM10000) use the 7-class list.
    is_phone_record = (record.model_type == "phone")
    if is_phone_record:
        active_class_metadata = PhoneImagePredictionService.class_metadata()
    else:
        active_class_metadata = PredictionService.class_metadata()

    class_names = {
        item["code"]: item["name"]
        for item in active_class_metadata
    }
    probability_rows = []
    for code, raw_probability in (record.probabilities or {}).items():
        try:
            probability = float(raw_probability)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(probability):
            continue
        probability = min(1.0, max(0.0, probability))
        probability_rows.append({
            "code": code,
            "name": class_names.get(code, code),
            "probability": probability,
            "percent": probability * 100,
        })
    probability_rows.sort(key=lambda row: row["probability"], reverse=True)

    quality_score_percent = None
    if quality and getattr(quality, "overall_score", None) is not None:
        try:
            score = float(quality.overall_score)
            if math.isfinite(score):
                quality_score_percent = min(100.0, max(0.0, score))
        except (TypeError, ValueError):
            pass

    reliability_original_confidence_percent = None
    reliability_agreement_percent = None
    if reliability:
        original = getattr(reliability, "original", {}) or {}
        original_confidence = (
            original.get("confidence") if isinstance(original, dict)
            else getattr(original, "confidence", None)
        )
        try:
            confidence = float(original_confidence)
            if math.isfinite(confidence):
                reliability_original_confidence_percent = (
                    confidence_to_fraction(confidence) * 100
                )
        except (TypeError, ValueError):
            pass

        try:
            agreement = float(getattr(reliability, "agreement_pct", None))
            if math.isfinite(agreement):
                reliability_agreement_percent = min(100.0, max(0.0, agreement))
        except (TypeError, ValueError):
            pass

    return render(request, "predictor/result.html", {
        "record": record,
        "quality": quality,
        "reliability": reliability,
        "wrong_input": wrong_input,
        "classes": active_class_metadata,
        "is_phone_record": is_phone_record,
        "probability_rows": probability_rows,
        # JSON-encoded chart payload for Chart.js consumption on the client.
        # Each row contains {code, name, probability (0..1), percent (0..100)}.
        "probability_chart_json": json.dumps([
            {
                "code": row["code"],
                "name": row["name"],
                "percent": round(row["percent"], 2),
                "category": next(
                    (c.get("category") for c in active_class_metadata
                     if c["code"] == row["code"]),
                    "unknown",
                ),
            }
            for row in probability_rows
        ]),
        "confidence_percent": confidence_to_fraction(record.confidence) * 100,
        "quality_score_percent": quality_score_percent,
        "reliability_original_confidence_percent": reliability_original_confidence_percent,
        "reliability_agreement_percent": reliability_agreement_percent,
    })


def history_view(request):
    """Show the visitor's prediction history with search, class filter, date
    filter, and JSON export support.

    Query params:
      - q:        full-text search across image_name + predicted_class/name
      - class:    filter by predicted_class (e.g. ?class=mel)
      - since:    ISO date (YYYY-MM-DD) — only show records on/after that date
      - until:    ISO date (YYYY-MM-DD) — only show records on/before that date
      - export:   if 'json', return a JSON download of all matching records
                  (capped at 200 records) instead of the HTML page.
    """
    qs = _scope_queryset(request).order_by("-created_at")

    q = (request.GET.get("q") or "").strip()
    selected_class = (request.GET.get("class") or "").strip().lower()
    since = (request.GET.get("since") or "").strip()
    until = (request.GET.get("until") or "").strip()

    if q:
        qs = qs.filter(
            Q(image_name__icontains=q)
            | Q(predicted_class__icontains=q)
            | Q(predicted_name__icontains=q)
            | Q(reference_id__icontains=q)
        )
    if selected_class:
        qs = qs.filter(predicted_class=selected_class)
    if since:
        qs = qs.filter(created_at__date__gte=since)
    if until:
        qs = qs.filter(created_at__date__lte=until)

    # Export branch — return JSON download for the matched set (capped)
    if request.GET.get("export") == "json":
        export_qs = qs[:200]
        payload = [
            {
                "reference_id": r.reference_id,
                "predicted_class": r.predicted_class,
                "predicted_name": r.predicted_name,
                "category": r.category,
                "confidence": round(confidence_to_fraction(r.confidence), 4),
                "probabilities": r.probabilities,
                "backend": r.backend,
                "image_name": r.image_name,
                "created_at": r.created_at.isoformat(),
            }
            for r in export_qs
        ]
        resp = JsonResponse({"records": payload, "count": len(payload)})
        resp["Content-Disposition"] = (
            'attachment; filename="dermacheckerbd_history.json"'
        )
        return resp

    records = qs[:50]
    for record in records:
        record.confidence_percent = confidence_to_fraction(record.confidence) * 100
    # Class filter dropdown options
    class_filter_options = PredictionService.class_metadata()

    return render(request, "predictor/history.html", {
        "records": records,
        "class_filter_options": class_filter_options,
        # Replicate current filter state for the form's sticky values
        "filters": {
            "q": q,
            "class": selected_class,
            "since": since,
            "until": until,
        },
        "total_matches": qs.count(),
    })


def pdf_report_view(request, reference_id: str):
    """Generate and return a PDF report for a saved prediction."""
    record = get_object_or_404(PredictionRecord, reference_id=reference_id)
    if (
        record.user is not None
        and record.user != request.user
        and not request.user.has_perm("predictor.view_medical_priority_queue")
    ):
        return HttpResponseForbidden("This prediction record is private to its owner.")
    if (
        record.user is None
        and record.session_key
        and not request.user.has_perm("predictor.view_medical_priority_queue")
    ):
        if _resolve_session_key(request) != record.session_key:
            return HttpResponseForbidden("This prediction record belongs to a different session.")
    from apps.common.services.prediction import PredictionResult

    prediction = PredictionResult(
        predicted_class=record.predicted_class,
        predicted_name=record.predicted_name,
        category=record.category,
        confidence=confidence_to_fraction(record.confidence),
        probabilities=record.probabilities,
        backend=record.backend,
    )
    # Hydrate saved JSON dicts into attribute-access objects for the PDF service.
    quality = hydrate(record.quality_report) if record.quality_report else None
    reliability = hydrate(record.reliability_report) if record.reliability_report else None
    wrong_input = hydrate(record.wrong_input_report) if record.wrong_input_report else None

    # Determine the user's language preference for the PDF.
    # The derma_lang cookie is set client-side by main.js when the user
    # clicks the language toggle. Fall back to the request's Accept-Language
    # header, then to English.
    language = request.COOKIES.get("derma_lang", "").strip().lower()
    if language not in ("en", "bn"):
        accept = (request.META.get("HTTP_ACCEPT_LANGUAGE") or "").lower()
        language = "bn" if accept.startswith("bn") else "en"

    pdf_bytes = PdfReportService.build_prediction_report(
        reference_id=record.reference_id,
        prediction=prediction,
        quality=quality,
        reliability=reliability,
        wrong_input=wrong_input,
        language=language,
    )
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="dermacheckerbd_{record.reference_id}.pdf"'
    return resp


@require_http_methods(["GET", "POST"])
def delete_record_view(request, reference_id: str):
    """Delete a saved prediction record (owner or same-session only)."""
    record = get_object_or_404(PredictionRecord, reference_id=reference_id)
    # Authorization
    if record.user is not None and record.user != request.user:
        return HttpResponseForbidden("You can only delete your own records.")
    if record.user is None and record.session_key:
        if _resolve_session_key(request) != record.session_key:
            return HttpResponseForbidden("You can only delete your own records.")
    # Legacy records (no user, no session_key) are link-only and cannot
    # be deleted via this view — preserve original behaviour.
    if record.user is None and not record.session_key:
        return HttpResponseForbidden("This anonymous record cannot be deleted.")

    if request.method == "POST":
        if record.image:
            record.image.delete(save=False)
        record.delete()
        return redirect("predictor:history")
    return render(request, "predictor/confirm_delete.html", {"record": record})


@require_http_methods(["GET", "POST"])
def clear_history_view(request):
    """Confirm and delete all prediction records visible to this visitor."""
    records = _scope_queryset(request)
    if request.method == "POST":
        for record in records.only("id", "image").iterator():
            if record.image:
                record.image.delete(save=False)
        records.delete()
        return redirect("predictor:history")
    return render(request, "predictor/confirm_clear_history.html", {
        "record_count": records.count(),
    })


# ---------------------------------------------------------------------------
# Phone-image (SkinDisNet) prediction — completely separate workflow
# ---------------------------------------------------------------------------

def _phone_metadata_from_post(post) -> dict:
    """Extract phone-image metadata from POST data.

    Only fields the model is configured to consume are kept. ``patient_id``
    is NEVER returned here — it is collected in the form for record
    association but is intentionally excluded from the metadata payload
    so it can never reach the model.
    """
    out = {}
    if getattr(settings, "PHONE_MODEL_USES_AGE", False):
        age_raw = (post.get("age") or "").strip()
        if age_raw:
            try:
                age = int(age_raw)
                if settings.PHONE_MODEL_AGE_MIN <= age <= settings.PHONE_MODEL_AGE_MAX:
                    out["age"] = age
            except (TypeError, ValueError):
                pass
    if getattr(settings, "PHONE_MODEL_USES_SEX", False):
        sex = (post.get("sex") or "").strip().lower()
        if sex in {"male", "female", "other", "unknown"}:
            out["sex"] = sex
    if getattr(settings, "PHONE_MODEL_USES_LOCATION", False):
        loc = (post.get("lesion_location") or "").strip()
        if loc and loc in settings.PHONE_LESION_LOCATIONS:
            out["lesion_location"] = loc
    return out


@require_http_methods(["GET", "POST"])
def phone_image_predict_view(request):
    """Phone-camera image (SkinDisNet) prediction endpoint.

    Completely separate from the HAM10000 dermoscopic endpoint at
    /predict/. The phone workflow:

    1. Validate file type, file size, and readability.
    2. Run the existing wrong-input + image-quality checks.
    3. Reject any image whose quality score is below
       PREDICTION_MIN_QUALITY_SCORE (default 50%).
    4. Collect metadata ONLY for fields the model is configured to
       consume (settings PHONE_MODEL_USES_*). Patient ID is stored on
       the record but never sent to the model.
    5. Call PhoneImagePredictionService — never the HAM10000 service.
    6. Save a PredictionRecord tagged model_type='phone' and redirect
       to the existing result page.

    If the phone-image model is not configured (ML_PHONE_MODEL_BACKEND
    is unset or the weights are missing), return a clear error rather
    than fabricating a prediction.
    """
    if request.method != "POST":
        # GET: render the unified upload page (same template as the
        # dermoscopic flow) so users always land on the dual-button
        # upload card regardless of entry point.
        form = ImageUploadForm()
        return render(request, "predictor/upload.html", _upload_context(form))

    form = PhoneImageMetadataForm(request.POST, request.FILES)
    if not form.is_valid():
        return _phone_error_response(request, "Please correct the form errors below.")

    uploaded = request.FILES["image"]
    if uploaded.content_type not in ALLOWED_TYPES:
        return _phone_error_response(
            request,
            f"Unsupported file type {uploaded.content_type!r}. "
            "Use JPG, PNG, or WEBP.",
        )
    if uploaded.size > MAX_BYTES:
        return _phone_error_response(
            request,
            f"File too large ({uploaded.size//1024} KB). Maximum is 10 MB.",
        )

    image_bytes = uploaded.read()
    uploaded.seek(0)

    # Wrong-input protection (corrupt file / non-skin).
    wrong_report, pil_image = WrongInputService.validate_bytes(image_bytes)
    if not wrong_report.is_valid_image or not pil_image:
        return _phone_error_response(
            request,
            wrong_report.warning,
            details=wrong_report.details,
            suggestions=wrong_report.suggestions,
        )

    # Quality gate — reject anything below the configured threshold.
    try:
        quality_report = ImageQualityService.assess_pil(pil_image)
    except Exception as exc:
        logger.warning("Phone-image quality check failed: %s", exc)
        return _phone_error_response(
            request, "Could not assess image quality. Please try again."
        )
    quality_score = float(getattr(quality_report, "overall_score", 0.0) or 0.0)
    min_score = float(settings.PREDICTION_MIN_QUALITY_SCORE)
    if quality_score < min_score:
        return _phone_error_response(
            request,
            "This image's quality score is below "
            f"{min_score:.0f}%. Please upload a clearer, well-lit photo of "
            "the skin lesion before running a phone-image prediction.",
        )

    metadata = _phone_metadata_from_post(request.POST)

    # Predict — phone-image model ONLY.
    try:
        backend = PhoneImagePredictionService._resolve_backend()
        # Forward the original uploaded file to the API backend (zero copy,
        # exactly the user's pixels, mirrors the HAM10000 API path).
        if isinstance(backend, _PhoneAPIBackend):
            prediction = PhoneImagePredictionService.predict_uploaded(
                uploaded, metadata=metadata
            )
        else:
            prediction = PhoneImagePredictionService.predict_pil(
                pil_image, metadata=metadata
            )
    except PhoneModelNotLoadedError as exc:
        # Surface the exact reason the model is unavailable — never
        # fabricate a fake prediction.
        return _phone_error_response(
            request,
            f"The phone-image prediction model is not configured. {exc}",
        )
    except PhoneInvalidImageError as exc:
        return _phone_error_response(request, f"Could not process image: {exc}")
    except PhonePredictionError as exc:
        logger.exception("Phone-image prediction failed.")
        return _phone_error_response(
            request,
            "Phone-image prediction could not be completed. "
            "Please try again later.",
        )

    # Reliability check is meaningful only on the local backends. The API
    # backend can't be invoked on a PIL variant without re-encoding, so we
    # skip it for phone-API records (consistent with the HAM10000 API path).
    reliability_report = None
    if not isinstance(backend, _PhoneAPIBackend):
        try:
            reliability_report = ReliabilityService.assess_pil(pil_image)
        except Exception as exc:
            logger.warning("Phone-image reliability check failed: %s", exc)

    session_key = (
        "" if request.user.is_authenticated else _resolve_session_key(request)
    )
    image_name = (
        form.cleaned_data.get("image_name", "").strip()
        or Path(uploaded.name).stem
        or "phone-image"
    )[:255]
    record = PredictionRecord(
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key,
        reference_id=_new_reference_id(),
        image_name=image_name,
        patient_name=(request.POST.get("patient_id") or "").strip()[:150],
        predicted_class=prediction.predicted_class,
        predicted_name=prediction.predicted_name,
        category="unknown",  # SkinDisNet classes have no benign/malignant tag
        confidence=prediction.confidence,
        probabilities=prediction.probabilities,
        quality_report=quality_report.as_dict() if quality_report else {},
        reliability_report=(
            reliability_report.as_dict() if reliability_report else {}
        ),
        wrong_input_report=wrong_report.as_dict(),
        backend=prediction.backend,
        model_type="phone",
    )
    _save_pil_image_to_field(record, pil_image, record.image_name)
    record.save()
    return redirect("predictor:result", reference_id=record.reference_id)


def _phone_error_response(request, error, details=None, suggestions=None):
    """Render the unified upload page with an error message — used by
    the phone-image workflow so the user stays on the same upload card
    they were on when the error occurred."""
    ctx = _upload_context(ImageUploadForm(), error=error)
    if details is not None:
        ctx["details"] = details
    if suggestions is not None:
        ctx["suggestions"] = suggestions
    return render(request, "predictor/upload.html", ctx)
