from __future__ import annotations

import io
import json
import logging
import math
import secrets
from pathlib import Path

from PIL import Image as PILImage

from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_http_methods

from apps.common.services.ai_api import NonSkinImageError, validate_skin_image
from apps.common.services.prediction import (
    InvalidImageError, ModelNotLoadedError, PredictionError, PredictionService,
    confidence_to_fraction,
)
from apps.common.services.phone_prediction import (
    PhoneImagePredictionService,
    PhoneInvalidImageError,
    PhoneModelNotLoadedError,
    PhonePredictionError,
)
from apps.common.services.image_quality import ImageQualityService
from apps.common.services.reliability import ReliabilityService
from apps.common.services.wrong_input import WrongInputService
from apps.common.services.pdf_report import PdfReportService
from apps.common.services._hydrate import hydrate

from .forms import ImageUploadForm
from .models import PredictionRecord

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 10 * 1024 * 1024

IMAGE_TYPE_DERMOSCOPIC = "dermoscopic"
IMAGE_TYPE_PHONE = "phone"


class _UploadRejected(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def _new_reference_id() -> str:
    return secrets.token_hex(8).upper()


def _save_pil_image_to_field(record: PredictionRecord, pil_image: PILImage, original_name: str):
    buf = io.BytesIO()
    pil_image.convert("RGB").save(buf, format="JPEG", quality=92)
    safe_name = get_valid_filename(original_name.strip())[:100] or "patient"
    record.image.save(
        f"{safe_name}_{record.reference_id}.jpg",
        ContentFile(buf.getvalue()),
        save=False,
    )


def _resolve_session_key(request) -> str:
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key or ""


def _scope_queryset(request):
    if request.user.is_authenticated:
        return PredictionRecord.objects.filter(user=request.user)
    sk = _resolve_session_key(request)
    return PredictionRecord.objects.filter(session_key=sk)


def _upload_context(form: ImageUploadForm | None = None, **extra) -> dict:
    form = form or ImageUploadForm()
    return {
        "form": form,
        "classes": PredictionService.class_metadata(),
        "phone_classes": PhoneImagePredictionService.class_metadata(),
        "phone_configured": PhoneImagePredictionService.is_configured(),
        "lesion_locations": getattr(settings, "PHONE_LESION_LOCATIONS", []),
        "sex_choices": getattr(settings, "PHONE_SEX_CHOICES", []),
        "phone_uses_age": getattr(settings, "PHONE_MODEL_USES_AGE", True),
        "phone_uses_sex": getattr(settings, "PHONE_MODEL_USES_SEX", True),
        "phone_uses_location": getattr(settings, "PHONE_MODEL_USES_LOCATION", True),
        "dermoscopic_model_name": getattr(settings, "HAM10000_MODEL_NAME", "Dermoscopic ResNet50"),
        "phone_model_name": getattr(
            settings, "SKINDISNET_MODEL_NAME",
            "Phone-image EfficientNetB0 + Metadata Fusion",
        ),
        **extra,
    }


def _reject_upload(request, message, **extra):
    return render(request, "predictor/upload.html", _upload_context(error=message, **extra))


def _predict_dermoscopic(uploaded, pil_image):
    model_name = getattr(settings, "HAM10000_MODEL_NAME", "Dermoscopic ResNet50")
    model_version = getattr(settings, "HAM10000_MODEL_VERSION", "")
    backend = PredictionService._resolve_backend()
    try:
        from apps.common.services.prediction import _APIBackend
        if isinstance(backend, _APIBackend):
            uploaded.seek(0)
            prediction = PredictionService.predict_uploaded(uploaded)
        else:
            prediction = PredictionService.predict_pil(pil_image)
    except InvalidImageError as e:
        raise _UploadRejected(f"Could not process image: {e}")
    except ModelNotLoadedError as e:
        raise _UploadRejected(f"Model is not loaded. {e}")
    except PredictionError:
        logger.exception("Dermoscopic prediction failed.")
        raise _UploadRejected(
            "Prediction could not be completed. Please try again later."
        )
    return prediction, model_name, model_version


def _predict_phone(form, uploaded, pil_image):
    model_name = getattr(
        settings, "SKINDISNET_MODEL_NAME",
        "Phone-image EfficientNetB0 + Metadata Fusion",
    )
    model_version = getattr(settings, "SKINDISNET_MODEL_VERSION", "")
    metadata = {
        "age": form.cleaned_data.get("age"),
        "sex": form.cleaned_data.get("sex"),
        "lesion_location": form.cleaned_data.get("lesion_location"),
    }
    backend = PhoneImagePredictionService._resolve_backend()
    try:
        from apps.common.services.phone_prediction import _PhoneAPIBackend
        if isinstance(backend, _PhoneAPIBackend):
            uploaded.seek(0)
            prediction = PhoneImagePredictionService.predict_uploaded(
                uploaded, metadata=metadata
            )
        else:
            prediction = PhoneImagePredictionService.predict_pil(
                pil_image, metadata=metadata
            )
    except PhoneInvalidImageError as e:
        raise _UploadRejected(f"Could not process image: {e}")
    except PhoneModelNotLoadedError as e:
        raise _UploadRejected(f"Model is not loaded. {e}")
    except PhonePredictionError:
        logger.exception("Phone-image prediction failed.")
        raise _UploadRejected(
            "Prediction could not be completed. Please try again later."
        )
    return prediction, model_name, model_version


@require_http_methods(["GET", "POST"])
def upload_view(request):
    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            error_msg = "Please correct the errors below."
            if form.errors:
                try:
                    first_field = next(iter(form.errors))
                    error_msg = "; ".join(form.errors[first_field])
                except Exception:
                    pass
            return _reject_upload(request, error_msg)

        image_type = form.cleaned_data["image_type"]
        uploaded = request.FILES["image"]
        if uploaded.content_type not in ALLOWED_TYPES:
            return _reject_upload(
                request,
                f"Unsupported file type {uploaded.content_type!r}. Use JPG, PNG, or WEBP.",
            )
        if uploaded.size > MAX_BYTES:
            return _reject_upload(
                request,
                f"File too large ({uploaded.size//1024} KB). Maximum is 10 MB.",
            )

        image_bytes = uploaded.read()
        uploaded.seek(0)

        try:
            validate_skin_image(
                image_bytes,
                filename=uploaded.name,
                content_type=uploaded.content_type,
            )
        except NonSkinImageError:
            return _reject_upload(
                request,
                "This image was classified as non-skin. Please upload a clear "
                "photo of a skin lesion to continue.",
            )
        except PredictionError:
            logger.exception("Skin/non-skin validation failed.")
            return _reject_upload(
                request,
                "Image validation could not be completed. Please try again later.",
            )

        wrong_report, pil_image = WrongInputService.validate_bytes(image_bytes)
        if not wrong_report.is_valid_image or not pil_image:
            return _reject_upload(
                request,
                wrong_report.warning,
                details=wrong_report.details,
                suggestions=wrong_report.suggestions,
            )

        try:
            quality_report = ImageQualityService.assess_pil(pil_image)
        except Exception as e:
            logger.warning("Quality check failed: %s", e)
            quality_report = None

        try:
            if image_type == IMAGE_TYPE_PHONE:
                prediction, model_name, model_version = _predict_phone(form, uploaded, pil_image)
            else:
                prediction, model_name, model_version = _predict_dermoscopic(uploaded, pil_image)
        except _UploadRejected as exc:
            return _reject_upload(request, exc.message)

        reliability_report = None
        if image_type != IMAGE_TYPE_PHONE:
            try:
                reliability_report = ReliabilityService.assess_pil(pil_image)
            except Exception as e:
                logger.warning("Reliability check failed: %s", e)
                reliability_report = None

        session_key = "" if request.user.is_authenticated else _resolve_session_key(request)
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
            image_type=image_type,
            model_name=model_name,
            model_version=model_version,
            predicted_class=prediction.predicted_class,
            predicted_name=prediction.predicted_name,
            category=getattr(prediction, "category", "unknown"),
            confidence=prediction.confidence,
            probabilities=prediction.probabilities,
            quality_report=quality_report.as_dict() if quality_report else {},
            reliability_report=reliability_report.as_dict() if reliability_report else {},
            wrong_input_report=wrong_report.as_dict(),
            backend=prediction.backend,
        )
        if image_type == IMAGE_TYPE_PHONE:
            if getattr(settings, "PHONE_MODEL_USES_AGE", True):
                record.patient_age = form.cleaned_data.get("age")
            if getattr(settings, "PHONE_MODEL_USES_SEX", True):
                record.patient_sex = form.cleaned_data.get("sex") or ""
            if getattr(settings, "PHONE_MODEL_USES_LOCATION", True):
                record.lesion_location = form.cleaned_data.get("lesion_location") or ""
        _save_pil_image_to_field(record, pil_image, record.image_name)
        record.save()

        return redirect("predictor:result", reference_id=record.reference_id)

    return render(request, "predictor/upload.html", _upload_context())


def _class_metadata_for(record: PredictionRecord) -> list:
    if record.image_type == IMAGE_TYPE_PHONE:
        return PhoneImagePredictionService.class_metadata()
    return PredictionService.class_metadata()


def _image_type_label(record: PredictionRecord) -> str:
    return "Phone Image" if record.image_type == IMAGE_TYPE_PHONE else "Dermoscopic"


def result_view(request, reference_id: str):
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

    quality = hydrate(record.quality_report) if record.quality_report else None
    reliability = hydrate(record.reliability_report) if record.reliability_report else None
    wrong_input = hydrate(record.wrong_input_report) if record.wrong_input_report else None

    class_meta = _class_metadata_for(record)
    class_names = {item["code"]: item["name"] for item in class_meta}
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
        "classes": class_meta,
        "image_type_label": _image_type_label(record),
        "is_phone": record.image_type == IMAGE_TYPE_PHONE,
        "probability_rows": probability_rows,
        "probability_chart_json": json.dumps([
            {
                "code": row["code"],
                "name": row["name"],
                "percent": round(row["percent"], 2),
                "category": next(
                    (c.get("category", "unknown") for c in class_meta
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

    if request.GET.get("export") == "json":
        export_qs = qs[:200]
        payload = [
            {
                "reference_id": r.reference_id,
                "image_type": r.image_type,
                "model_name": r.model_name,
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
    class_filter_options = PredictionService.class_metadata()

    return render(request, "predictor/history.html", {
        "records": records,
        "class_filter_options": class_filter_options,
        "filters": {
            "q": q,
            "class": selected_class,
            "since": since,
            "until": until,
        },
        "total_matches": qs.count(),
    })


def pdf_report_view(request, reference_id: str):
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
    quality = hydrate(record.quality_report) if record.quality_report else None
    reliability = hydrate(record.reliability_report) if record.reliability_report else None
    wrong_input = hydrate(record.wrong_input_report) if record.wrong_input_report else None

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
        image_type=record.image_type,
        model_name=record.model_name,
    )
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="dermacheckerbd_{record.reference_id}.pdf"'
    return resp


@require_http_methods(["GET", "POST"])
def delete_record_view(request, reference_id: str):
    record = get_object_or_404(PredictionRecord, reference_id=reference_id)
    if record.user is not None and record.user != request.user:
        return HttpResponseForbidden("You can only delete your own records.")
    if record.user is None and record.session_key:
        if _resolve_session_key(request) != record.session_key:
            return HttpResponseForbidden("You can only delete your own records.")
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
