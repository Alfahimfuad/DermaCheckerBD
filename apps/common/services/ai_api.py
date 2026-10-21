"""FastAPI prediction client.

When ``settings.ML_MODEL_BACKEND == "api"`` the Django prediction service
forwards every uploaded image to a FastAPI service (running ResNet50 in a
separate process) instead of loading TensorFlow in-process.

Contract with the FastAPI service
---------------------------------
- Endpoint: ``POST {AI_API_URL}/predict``
- Multipart form field: ``file``  (a single image)
- Optional auth: bearer token via ``AI_API_TOKEN``
- Response JSON shape::

    {
      "success": true,
      "predicted_class": "mel",         # one of HAM10000 codes
      "confidence": 0.8723,             # float in [0, 1]
      "probabilities": {                # all 7 HAM10000 classes
        "akiec": 0.0123,
        "bcc":   0.0456,
        "bkl":   0.0789,
        "df":    0.0011,
        "mel":   0.8723,
        "nv":    0.0312,
        "vasc":  0.0006
      }
    }

On failure the service may return ``{"success": false, "error": "..."}`` or
a non-2xx status code; both are translated to :class:`PredictionError`.
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict

import requests
from django.conf import settings

from apps.common.services.prediction import CLASS_ORDER, PredictionError

logger = logging.getLogger(__name__)

class NonSkinImageError(PredictionError):
    """Raised when the validation API classifies an upload as non-skin."""


def _skin_class_from_response(payload: Any) -> bool:
    """Return the Skin/Non-Skin result from common classifier API payloads.

    Unknown labels and response shapes fail closed: the lesion classifier must
    not run unless the validation API explicitly identifies the image as Skin.
    """
    if isinstance(payload, str):
        label = payload
    elif isinstance(payload, dict):
        if payload.get("success") is False:
            raise PredictionError("The skin validation service reported failure.")

        is_skin = payload.get("is_skin")
        if isinstance(is_skin, bool):
            return is_skin

        label = None
        for key in ("predicted_class", "prediction", "label", "class_name", "class", "result"):
            candidate = payload.get(key)
            if isinstance(candidate, str):
                label = candidate
                break

        if label is None:
            for key in ("probabilities", "scores", "class_probabilities"):
                scores = payload.get(key)
                if isinstance(scores, dict) and scores:
                    numeric_scores = {}
                    for score_label, score in scores.items():
                        try:
                            value = float(score)
                        except (TypeError, ValueError):
                            continue
                        if math.isfinite(value):
                            numeric_scores[str(score_label)] = value
                    if numeric_scores:
                        ordered = sorted(
                            numeric_scores.items(),
                            key=lambda item: item[1],
                            reverse=True,
                        )
                        if len(ordered) > 1 and ordered[0][1] == ordered[1][1]:
                            raise PredictionError(
                                "The skin validation service returned an ambiguous result."
                            )
                        label = ordered[0][0]
                        break
    else:
        label = None

    normalized = "".join(ch for ch in str(label or "").lower() if ch.isalnum())
    if normalized in {"skin", "skinimage"}:
        return True
    if normalized in {"nonskin", "nonskinimage", "notskin"}:
        return False
    raise PredictionError(
        "The skin validation service returned an unrecognized classification."
    )


def validate_skin_image(
    image_bytes: bytes,
    filename: str = "skin_image.jpg",
    content_type: str = "image/jpeg",
) -> None:
    """Call the separate Skin/Non-Skin API before lesion prediction.

    ``AI_SKIN_API_URL`` is the complete validation endpoint URL. It is
    intentionally separate from ``AI_API_URL``, which is the base URL for the
    seven-class lesion API. Both APIs may share the optional bearer token and
    timeout.
    """
    endpoint = getattr(settings, "AI_SKIN_API_URL", "").strip()
    if not endpoint:
        raise PredictionError("The skin validation service is not configured.")

    file_field = (
        getattr(settings, "AI_SKIN_API_FILE_FIELD", "file").strip() or "file"
    )
    headers = {}
    skin_api_token = getattr(
        settings,
        "AI_SKIN_API_TOKEN",
        getattr(settings, "AI_API_TOKEN", ""),
    ).strip() or getattr(settings, "AI_API_TOKEN", "").strip()
    if skin_api_token:
        headers["Authorization"] = f"Bearer {skin_api_token}"

    try:
        response = requests.post(
            endpoint,
            files={
                file_field: (
                    filename or "skin_image.jpg",
                    image_bytes,
                    content_type or "image/jpeg",
                )
            },
            headers=headers or None,
            timeout=getattr(settings, "AI_API_TIMEOUT", 120),
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.warning("Skin validation API request failed: %s", exc)
        raise PredictionError(
            "The skin validation service could not be reached."
        ) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        logger.warning("Skin validation API returned a non-JSON response.")
        raise PredictionError(
            "The skin validation service returned an invalid response."
        ) from exc

    if not _skin_class_from_response(payload):
        raise NonSkinImageError("This image was classified as non-skin.")


def predict_skin_image(image_file) -> Dict[str, Any]:
    """Forward an uploaded image to the FastAPI prediction service.

    Args:
        image_file: any file-like object with ``.read()``, optionally
            exposing ``.name`` and ``.content_type`` (a Django
            ``UploadedFile`` qualifies, as does a wrapped ``io.BytesIO``).

    Returns:
        The parsed JSON response from FastAPI. Always contains
        ``success=True`` and a ``probabilities`` dict on the happy path.

    Raises:
        PredictionError: on any network failure, non-2xx response, or
            ``success=False`` payload from the FastAPI service.
    """
    url = f"{settings.AI_API_URL.rstrip('/')}/predict"

    # Rewind to start so the same file object can be re-used by other
    # services (quality check, wrong-input check) before/after this call.
    try:
        image_file.seek(0)
    except Exception:
        # Some file-like objects don't support seek; that's fine, the
        # caller is responsible for handing us a fresh-readable object.
        pass

    files = {
        "file": (
            getattr(image_file, "name", "skin_image.jpg") or "skin_image.jpg",
            image_file,
            getattr(image_file, "content_type", "image/jpeg") or "image/jpeg",
        )
    }

    headers: Dict[str, str] = {}
    if getattr(settings, "AI_API_TOKEN", "").strip():
        headers["Authorization"] = f"Bearer {settings.AI_API_TOKEN.strip()}"

    try:
        response = requests.post(
            url,
            files=files,
            headers=headers or None,
            timeout=getattr(settings, "AI_API_TIMEOUT", 120),
        )
    except requests.exceptions.Timeout as exc:
        logger.warning("FastAPI /predict timed out: %s", exc)
        raise PredictionError(
            "The prediction service did not respond in time. Please try again."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        logger.warning("FastAPI /predict connection error: %s", exc)
        raise PredictionError(
            "Could not reach the prediction service. Please try again later."
        ) from exc
    except requests.exceptions.RequestException as exc:
        logger.warning("FastAPI /predict request failed: %s", exc)
        raise PredictionError(
            "The prediction service could not be contacted."
        ) from exc

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        # Try to surface the upstream error message if present.
        try:
            payload = response.json()
            upstream_msg = (payload or {}).get("error") or (payload or {}).get("detail")
        except ValueError:
            upstream_msg = None
        logger.warning("FastAPI /predict returned %s: %s", response.status_code, upstream_msg or exc)
        raise PredictionError(
            upstream_msg or "The prediction service returned an error."
        ) from exc

    try:
        result = response.json()
    except ValueError as exc:
        logger.warning("FastAPI /predict returned non-JSON body: %r", response.text[:200])
        raise PredictionError(
            "The prediction service returned an invalid response."
        ) from exc

    if not isinstance(result, dict):
        logger.warning("FastAPI /predict returned a non-object JSON response.")
        raise PredictionError(
            "The prediction service returned an invalid response."
        )

    if not result.get("success"):
        upstream_msg = result.get("error") or "Prediction failed on the FastAPI side."
        logger.warning("FastAPI /predict returned success=False: %s", upstream_msg)
        raise PredictionError(upstream_msg)

    predicted_class = str(result.get("predicted_class") or "").strip().lower()
    if predicted_class not in CLASS_ORDER:
        logger.warning(
            "FastAPI /predict returned an unsupported class: %r", predicted_class
        )
        raise PredictionError(
            "The prediction service returned an unsupported class."
        )

    raw_probabilities = result.get("probabilities")
    if (
        not isinstance(raw_probabilities, dict)
        or set(raw_probabilities) != set(CLASS_ORDER)
    ):
        logger.warning(
            "FastAPI /predict did not return probabilities for all configured "
            "classes: %r",
            raw_probabilities,
        )
        raise PredictionError(
            "The prediction service returned an incomplete response."
        )

    probabilities = {}
    for class_code in CLASS_ORDER:
        try:
            probability = float(raw_probabilities[class_code])
        except (TypeError, ValueError):
            probability = math.nan
        if not math.isfinite(probability) or probability < 0:
            logger.warning(
                "FastAPI /predict returned an invalid probability for %s.",
                class_code,
            )
            raise PredictionError(
                "The prediction service returned invalid probabilities."
            )
        probabilities[class_code] = probability

    result = dict(result)
    result["predicted_class"] = predicted_class
    result["probabilities"] = probabilities
    return result
