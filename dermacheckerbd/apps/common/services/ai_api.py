"""FastAPI prediction client.

When settings.ML_MODEL_BACKEND == "api", Django forwards uploaded images
to a separate FastAPI service for skin validation and lesion prediction.

Skin validation contract:
    POST {AI_SKIN_API_URL}/api/check-skin
    Multipart field: file

Lesion prediction contract:
    POST {AI_API_URL}/predict
    Multipart field: file

Optional authentication:
    Authorization: Bearer <AI_API_TOKEN>
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import requests
from django.conf import settings

from apps.common.services.prediction import PredictionError

logger = logging.getLogger(__name__)

# Skin / Non-Skin validation endpoint.
SKIN_NON_SKIN_ENDPOINT = "/api/check-skin"

# Lesion classification endpoint.
PREDICTION_ENDPOINT = "/predict"


class NonSkinImageError(PredictionError):
    """Raised when the validation API classifies an upload as non-skin."""


def _get_api_headers() -> Dict[str, str]:
    """Build optional API authentication headers."""
    headers: Dict[str, str] = {}

    token = getattr(settings, "AI_API_TOKEN", "") or ""
    token = token.strip()

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def _skin_class_from_response(payload: Any) -> bool:
    """Return True for Skin and False for Non-Skin.

    Unknown labels and response shapes fail closed. The lesion classifier
    must not run unless the validation API explicitly identifies the image
    as Skin.
    """
    if isinstance(payload, str):
        label = payload

    elif isinstance(payload, dict):
        if payload.get("success") is False:
            message = (
                payload.get("error")
                or payload.get("detail")
                or "The skin validation service reported failure."
            )
            raise PredictionError(str(message))

        is_skin = payload.get("is_skin")
        if isinstance(is_skin, bool):
            return is_skin

        label = None

        for key in (
            "predicted_class",
            "prediction",
            "label",
            "class_name",
            "class",
            "result",
        ):
            candidate = payload.get(key)

            if isinstance(candidate, str):
                label = candidate
                break

        # If the API returns class probabilities instead of a label,
        # choose the class with the highest numeric score.
        if label is None:
            for key in (
                "probabilities",
                "scores",
                "class_probabilities",
            ):
                scores = payload.get(key)

                if not isinstance(scores, dict) or not scores:
                    continue

                numeric_scores = {}

                for score_label, score in scores.items():
                    try:
                        numeric_scores[str(score_label)] = float(score)
                    except (TypeError, ValueError):
                        continue

                if numeric_scores:
                    ordered = sorted(
                        numeric_scores.items(),
                        key=lambda item: item[1],
                        reverse=True,
                    )

                    if (
                        len(ordered) > 1
                        and ordered[0][1] == ordered[1][1]
                    ):
                        raise PredictionError(
                            "The skin validation service returned "
                            "an ambiguous result."
                        )

                    label = ordered[0][0]
                    break

    else:
        label = None

    normalized = "".join(
        character
        for character in str(label or "").lower()
        if character.isalnum()
    )

    if normalized in {
        "skin",
        "skinimage",
    }:
        return True

    if normalized in {
        "nonskin",
        "nonskinimage",
        "notskin",
    }:
        return False

    raise PredictionError(
        "The skin validation service returned an unrecognized "
        "classification."
    )


def validate_skin_image(
    image_bytes: bytes,
    filename: str = "skin_image.jpg",
    content_type: str = "image/jpeg",
) -> None:
    """Validate an uploaded image before lesion classification."""

    skin_api_url = (
        getattr(settings, "AI_SKIN_API_URL", "") or ""
    ).strip()

    # Backward-compatible fallback for single-service deployments.
    if not skin_api_url:
        skin_api_url = (
            getattr(settings, "AI_API_URL", "") or ""
        ).strip()

    if not skin_api_url:
        raise PredictionError(
            "The skin validation service is not configured."
        )

    # IMPORTANT: the endpoint is /api/check-skin, not /skin_non_skin.
    url = (
        f"{skin_api_url.rstrip('/')}"
        f"{SKIN_NON_SKIN_ENDPOINT}"
    )

    headers = _get_api_headers()
    timeout = getattr(settings, "AI_API_TIMEOUT", 120)

    files = {
        "file": (
            filename or "skin_image.jpg",
            image_bytes,
            content_type or "image/jpeg",
        )
    }

    try:
        logger.info(
            "Sending image to Skin Validation API: %s",
            url,
        )

        response = requests.post(
            url,
            files=files,
            headers=headers or None,
            timeout=timeout,
        )

        response.raise_for_status()

    except requests.exceptions.Timeout as exc:
        logger.warning(
            "Skin validation API timed out: %s",
            exc,
        )
        raise PredictionError(
            "The skin validation service timed out. "
            "Please try again."
        ) from exc

    except requests.exceptions.HTTPError as exc:
        # Include the upstream response details in server logs.
        # Avoid exposing raw server details to end users.
        try:
            upstream_payload = response.json()
            upstream_message = (
                upstream_payload.get("detail")
                or upstream_payload.get("error")
                or upstream_payload.get("message")
            )
        except (ValueError, AttributeError):
            upstream_message = response.text[:300]

        logger.warning(
            "Skin validation API returned HTTP %s. URL: %s. "
            "Details: %s",
            response.status_code,
            url,
            upstream_message or str(exc),
        )

        raise PredictionError(
            "The skin validation service returned an error. "
            "Please try again later."
        ) from exc

    except requests.exceptions.ConnectionError as exc:
        logger.warning(
            "Skin validation API connection failed: %s",
            exc,
        )
        raise PredictionError(
            "Could not connect to the skin validation service. "
            "Please try again later."
        ) from exc

    except requests.exceptions.RequestException as exc:
        logger.warning(
            "Skin validation API request failed: %s",
            exc,
        )
        raise PredictionError(
            "The skin validation service could not be reached."
        ) from exc

    try:
        payload = response.json()

    except ValueError as exc:
        logger.warning(
            "Skin validation API returned non-JSON response: %r",
            response.text[:200],
        )
        raise PredictionError(
            "The skin validation service returned an invalid response."
        ) from exc

    # Continue to ResNet50 only if the image is explicitly classified
    # as Skin.
    if not _skin_class_from_response(payload):
        raise NonSkinImageError(
            "This image was classified as non-skin."
        )

    logger.info("Skin validation successful.")


def predict_skin_image(image_file: Any) -> Dict[str, Any]:
    """Forward an uploaded image to the lesion prediction API.

    Args:
        image_file: A file-like object with read(), optionally exposing
            name and content_type attributes.

    Returns:
        Parsed JSON response containing success=True and probabilities.

    Raises:
        PredictionError: If the API request fails or its response is invalid.
    """

    ai_api_url = (
        getattr(settings, "AI_API_URL", "") or ""
    ).strip()

    if not ai_api_url:
        raise PredictionError(
            "The prediction service is not configured."
        )

    url = f"{ai_api_url.rstrip('/')}{PREDICTION_ENDPOINT}"

    # Rewind the uploaded file before forwarding it.
    try:
        image_file.seek(0)
    except Exception:
        pass

    filename = (
        getattr(image_file, "name", None)
        or "skin_image.jpg"
    )

    content_type = (
        getattr(image_file, "content_type", None)
        or "image/jpeg"
    )

    files = {
        "file": (
            filename,
            image_file,
            content_type,
        )
    }

    headers = _get_api_headers()
    timeout = getattr(settings, "AI_API_TIMEOUT", 120)

    try:
        response = requests.post(
            url,
            files=files,
            headers=headers or None,
            timeout=timeout,
        )

    except requests.exceptions.Timeout as exc:
        logger.warning(
            "FastAPI /predict timed out: %s",
            exc,
        )
        raise PredictionError(
            "The prediction service did not respond in time. "
            "Please try again."
        ) from exc

    except requests.exceptions.ConnectionError as exc:
        logger.warning(
            "FastAPI /predict connection error: %s",
            exc,
        )
        raise PredictionError(
            "Could not reach the prediction service. "
            "Please try again later."
        ) from exc

    except requests.exceptions.RequestException as exc:
        logger.warning(
            "FastAPI /predict request failed: %s",
            exc,
        )
        raise PredictionError(
            "The prediction service could not be contacted."
        ) from exc

    try:
        response.raise_for_status()

    except requests.exceptions.HTTPError as exc:
        try:
            payload = response.json()

            upstream_message = (
                payload.get("error")
                or payload.get("detail")
                or payload.get("message")
            )

        except (ValueError, AttributeError):
            upstream_message = None

        logger.warning(
            "FastAPI /predict returned HTTP %s: %s",
            response.status_code,
            upstream_message or str(exc),
        )

        raise PredictionError(
            upstream_message
            or "The prediction service returned an error."
        ) from exc

    try:
        result = response.json()

    except ValueError as exc:
        logger.warning(
            "FastAPI /predict returned non-JSON response: %r",
            response.text[:200],
        )
        raise PredictionError(
            "The prediction service returned an invalid response."
        ) from exc

    if not isinstance(result, dict):
        raise PredictionError(
            "The prediction service returned an invalid response."
        )

    if not result.get("success"):
        upstream_message = (
            result.get("error")
            or result.get("detail")
            or "Prediction failed on the FastAPI side."
        )

        logger.warning(
            "FastAPI /predict returned success=False: %s",
            upstream_message,
        )

        raise PredictionError(str(upstream_message))

    probabilities = result.get("probabilities")

    if not isinstance(probabilities, dict):
        logger.warning(
            "FastAPI /predict missing probabilities dictionary: %r",
            result,
        )
        raise PredictionError(
            "The prediction service returned an incomplete response."
        )

    return result