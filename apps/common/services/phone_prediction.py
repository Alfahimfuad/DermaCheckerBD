from __future__ import annotations

import hashlib
import io
import logging
import math
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from PIL import Image

from django.conf import settings

from .prediction import confidence_to_fraction

logger = logging.getLogger(__name__)

PHONE_CLASS_NAMES: Dict[str, str] = getattr(settings, "SKINDISNET_CLASS_NAMES", {})
PHONE_CLASS_ORDER: list = list(getattr(settings, "ML_PHONE_MODEL_CLASSES", []))
PHONE_MODEL_NAME: str = getattr(
    settings, "SKINDISNET_MODEL_NAME", "Phone-image EfficientNetB0 + Metadata Fusion"
)
PHONE_MODEL_VERSION: str = getattr(settings, "SKINDISNET_MODEL_VERSION", "")


@dataclass(frozen=True)
class PhonePredictionResult:
    predicted_class: str
    predicted_name: str
    confidence: float
    probabilities: Dict[str, float] = field(default_factory=dict)
    backend: str = "phone_mock"
    model_name: str = PHONE_MODEL_NAME
    model_version: str = PHONE_MODEL_VERSION
    input_size: int = 224

    def as_dict(self) -> dict:
        return {
            "predicted_class": self.predicted_class,
            "predicted_name": self.predicted_name,
            "confidence": round(self.confidence, 4),
            "probabilities": {k: round(v, 4) for k, v in self.probabilities.items()},
            "backend": self.backend,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "input_size": self.input_size,
        }


class PhonePredictionError(Exception):
    pass


class PhoneModelNotLoadedError(PhonePredictionError):
    pass


class PhoneInvalidImageError(PhonePredictionError):
    pass


def preprocess_phone_image(
    image: Image.Image, target_size: Optional[int] = None
) -> np.ndarray:
    if target_size is None:
        target_size = int(getattr(settings, "ML_PHONE_MODEL_INPUT_SIZE", 224))
    if image is None:
        raise PhoneInvalidImageError("Image is None")
    try:
        image = image.convert("RGB")
    except Exception as exc:
        raise PhoneInvalidImageError(
            f"Could not convert image to RGB: {exc}"
        ) from exc
    if image.size[0] < 16 or image.size[1] < 16:
        raise PhoneInvalidImageError(
            f"Image dimensions {image.size} too small (minimum 16x16)."
        )
    resample_name = getattr(
        settings, "ML_PHONE_MODEL_RESAMPLE", settings.ML_MODEL_RESAMPLE
    ).upper()
    resampling = {
        "NEAREST": Image.Resampling.NEAREST,
        "BILINEAR": Image.Resampling.BILINEAR,
        "BICUBIC": Image.Resampling.BICUBIC,
        "LANCZOS": Image.Resampling.LANCZOS,
    }
    if resample_name not in resampling:
        raise PhoneModelNotLoadedError(
            f"Unsupported ML_PHONE_MODEL_RESAMPLE={resample_name!r}."
        )
    image = image.resize((target_size, target_size), resampling[resample_name])
    return np.asarray(image, dtype=np.float32) / 255.0


class _PhoneMockBackend:
    backend_name = "phone_mock"

    def predict(self, arr: np.ndarray) -> Dict[str, float]:
        h = hashlib.sha1(arr.tobytes()).digest()
        seeds = list(h[:6])
        base_logits = np.array(
            [0.4, -0.3, 0.2, -0.6, -0.1, 0.1], dtype=np.float32
        )
        noise = np.array(
            [(b - 128) / 128.0 for b in seeds], dtype=np.float32
        ) * 1.0
        logits = base_logits + noise
        z = logits / 0.6
        z = z - z.max()
        exp = np.exp(z)
        probs = exp / exp.sum()
        return {klass: float(p) for klass, p in zip(PHONE_CLASS_ORDER, probs)}


class _PhoneKerasBackend:
    backend_name = "phone_keras"

    def __init__(self, model_path: str):
        path = Path(model_path)
        if not path.is_file():
            logger.error("Phone-image Keras model is missing: %s", path)
            raise PhoneModelNotLoadedError(
                "The phone-image prediction model is unavailable. "
                "Please try again later."
            )
        try:
            import tensorflow as tf
        except Exception:
            logger.exception("TensorFlow could not be imported for phone prediction.")
            raise PhoneModelNotLoadedError(
                "The phone-image prediction service is unavailable."
            )
        try:
            self.model = tf.keras.models.load_model(str(path), compile=False)
        except Exception:
            logger.exception("Could not load the configured phone-image model.")
            raise PhoneModelNotLoadedError(
                "The phone-image prediction model could not be loaded."
            )

        expected_dim = int(getattr(settings, "ML_PHONE_MODEL_INPUT_SIZE", 224))
        output_shape = self.model.output_shape
        if isinstance(output_shape, list):
            if len(output_shape) != 1:
                raise PhoneModelNotLoadedError(
                    "The phone-image model must have one classification output."
                )
            output_shape = output_shape[0]
        output_shape = tuple(output_shape)
        if len(output_shape) != 2 or output_shape[-1] != len(PHONE_CLASS_ORDER):
            logger.error(
                "Phone-image model output %s does not match %d classes.",
                output_shape, len(PHONE_CLASS_ORDER),
            )
            raise PhoneModelNotLoadedError(
                "The phone-image model does not match the configured classes."
            )
        self.preprocess_input = tf.keras.applications.efficientnet.preprocess_input

    def predict(self, arr: np.ndarray) -> Dict[str, float]:
        try:
            import tensorflow as tf  # noqa: F401
            pixels = np.asarray(arr, dtype=np.float32) * 255.0
            batch = self.preprocess_input(np.expand_dims(pixels, axis=0))
            predictions = self.model(batch, training=False)
            if hasattr(predictions, "numpy"):
                predictions = predictions.numpy()
            predictions = np.asarray(predictions, dtype=np.float32)
        except Exception as exc:
            logger.exception("Phone-image Keras inference failed.")
            raise PhonePredictionError(
                "The phone-image prediction service could not process this image."
            ) from exc
        if predictions.shape != (1, len(PHONE_CLASS_ORDER)):
            raise PhonePredictionError(
                "The phone-image prediction service returned an invalid result."
            )
        probabilities = predictions[0]
        if not np.isfinite(probabilities).all() or np.any(probabilities < 0):
            raise PhonePredictionError(
                "The phone-image prediction service returned an invalid result."
            )
        total = float(probabilities.sum())
        if total <= 0:
            raise PhonePredictionError(
                "The phone-image prediction service returned an invalid result."
            )
        probabilities = probabilities / total
        return {
            klass: float(p)
            for klass, p in zip(PHONE_CLASS_ORDER, probabilities)
        }


class _PhoneAPIBackend:
    backend_name = "phone_api"

    def __init__(self) -> None:
        try:
            import requests  # noqa: F401
        except ImportError as exc:
            raise PhoneModelNotLoadedError(
                "ML_PHONE_MODEL_BACKEND=api requires the `requests` package."
            ) from exc
        if not getattr(settings, "SKINDISNET_API_URL", "").strip():
            raise PhoneModelNotLoadedError(
                "ML_PHONE_MODEL_BACKEND=api but SKINDISNET_API_URL is not configured."
            )

    def predict_file(self, image_file, metadata: Optional[dict] = None) -> dict:
        import requests
        url = f"{settings.SKINDISNET_API_URL.rstrip('/')}/predict"
        try:
            image_file.seek(0)
        except Exception:
            pass
        file_field = getattr(settings, "SKINDISNET_API_FILE_FIELD", "file") or "file"
        files = {
            file_field: (
                getattr(image_file, "name", "phone_image.jpg") or "phone_image.jpg",
                image_file,
                getattr(image_file, "content_type", "image/jpeg") or "image/jpeg",
            )
        }
        data: Dict[str, Any] = {}
        if metadata:
            for key, value in metadata.items():
                if value is None or value == "":
                    continue
                data[key] = str(value)
        headers: Dict[str, str] = {}
        token = getattr(settings, "SKINDISNET_API_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            response = requests.post(
                url,
                files=files,
                data=data or None,
                headers=headers or None,
                timeout=int(getattr(settings, "SKINDISNET_API_TIMEOUT", 120)),
            )
        except requests.exceptions.Timeout as exc:
            raise PhonePredictionError(
                "The phone-image prediction service did not respond in time."
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise PhonePredictionError(
                "Could not reach the phone-image prediction service."
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise PhonePredictionError(
                "The phone-image prediction service could not be contacted."
            ) from exc
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            try:
                payload = response.json()
                upstream_msg = (payload or {}).get("error") or (payload or {}).get("detail")
            except ValueError:
                upstream_msg = None
            raise PhonePredictionError(
                upstream_msg or "The phone-image prediction service returned an error."
            ) from exc
        try:
            result = response.json()
        except ValueError as exc:
            raise PhonePredictionError(
                "The phone-image prediction service returned an invalid response."
            ) from exc
        if not isinstance(result, dict):
            raise PhonePredictionError(
                "The phone-image prediction service returned an invalid response."
            )
        if not result.get("success"):
            upstream_msg = result.get("error") or "Prediction failed on the phone-image API side."
            raise PhonePredictionError(upstream_msg)
        return result


class PhoneImagePredictionService:
    _backend = None
    _backend_name = None
    _backend_error = None
    _backend_lock = threading.Lock()

    _METADATA_KEYS = ("age", "sex", "lesion_location")

    @classmethod
    def _resolve_backend(cls):
        if cls._backend is not None:
            return cls._backend
        if cls._backend_error is not None:
            raise PhoneModelNotLoadedError(cls._backend_error)
        with cls._backend_lock:
            if cls._backend is not None:
                return cls._backend
            if cls._backend_error is not None:
                raise PhoneModelNotLoadedError(cls._backend_error)
            backend_choice = (
                getattr(settings, "ML_PHONE_MODEL_BACKEND", "").strip().lower()
            )
            try:
                if backend_choice == "mock":
                    cls._backend = _PhoneMockBackend()
                    cls._backend_name = "phone_mock"
                elif backend_choice == "keras":
                    model_path = getattr(settings, "ML_PHONE_MODEL_PATH", "")
                    if not model_path:
                        raise PhoneModelNotLoadedError(
                            "The phone-image prediction model is unavailable. "
                            "Please try again later."
                        )
                    cls._backend = _PhoneKerasBackend(model_path)
                    cls._backend_name = "phone_keras"
                elif backend_choice == "api":
                    cls._backend = _PhoneAPIBackend()
                    cls._backend_name = "phone_api"
                elif backend_choice in ("", "none"):
                    raise PhoneModelNotLoadedError(
                        "The phone-image prediction model is not configured. "
                        "Set ML_PHONE_MODEL_BACKEND to enable phone-image predictions."
                    )
                else:
                    raise PhoneModelNotLoadedError(
                        f"Unknown ML_PHONE_MODEL_BACKEND={backend_choice!r}"
                    )
            except PhoneModelNotLoadedError as exc:
                cls._backend_error = str(exc)
                raise
            logger.info(
                "PhoneImagePredictionService using backend=%s", cls._backend_name
            )
            return cls._backend

    @classmethod
    def reset(cls):
        with cls._backend_lock:
            cls._backend = None
            cls._backend_name = None
            cls._backend_error = None

    @classmethod
    def is_configured(cls) -> bool:
        choice = getattr(settings, "ML_PHONE_MODEL_BACKEND", "").strip().lower()
        return choice not in ("", "none")

    @classmethod
    def _sanitize_metadata(cls, metadata: Optional[dict]) -> Dict[str, Any]:
        if not metadata:
            return {}
        out: Dict[str, Any] = {}
        flags = {
            "age": "PHONE_MODEL_USES_AGE",
            "sex": "PHONE_MODEL_USES_SEX",
            "lesion_location": "PHONE_MODEL_USES_LOCATION",
        }
        for key in cls._METADATA_KEYS:
            if not getattr(settings, flags[key], False):
                continue
            value = metadata.get(key)
            if value is None or value == "":
                continue
            out[key] = value
        return out

    @classmethod
    def predict_pil(
        cls, image: Image.Image, metadata: Optional[dict] = None
    ) -> PhonePredictionResult:
        backend = cls._resolve_backend()
        if isinstance(backend, _PhoneAPIBackend):
            buf = io.BytesIO()
            buf.name = "phone_image.jpg"
            buf.content_type = "image/jpeg"
            try:
                image.convert("RGB").save(buf, format="JPEG", quality=95)
            except Exception as exc:
                raise PhoneInvalidImageError(
                    f"Could not encode image for phone API: {exc}"
                ) from exc
            buf.seek(0)
            api_response = backend.predict_file(
                buf, metadata=cls._sanitize_metadata(metadata)
            )
            return cls._build_api_result(api_response)
        arr = preprocess_phone_image(image)
        probs = backend.predict(arr)
        return cls._build_result(probs, backend.backend_name)

    @classmethod
    def predict_uploaded(
        cls, uploaded, metadata: Optional[dict] = None
    ) -> PhonePredictionResult:
        backend = cls._resolve_backend()
        if isinstance(backend, _PhoneAPIBackend):
            api_response = backend.predict_file(
                uploaded, metadata=cls._sanitize_metadata(metadata)
            )
            return cls._build_api_result(api_response)
        try:
            data = (
                uploaded.read() if hasattr(uploaded, "read") else bytes(uploaded)
            )
        except Exception as exc:
            raise PhoneInvalidImageError(
                f"Could not read uploaded file: {exc}"
            ) from exc
        try:
            image = Image.open(io.BytesIO(data))
        except Exception as exc:
            raise PhoneInvalidImageError(
                f"Could not open image bytes: {exc}"
            ) from exc
        return cls.predict_pil(image, metadata=metadata)

    @staticmethod
    def _build_result(
        probs: Dict[str, float], backend_name: str
    ) -> PhonePredictionResult:
        ordered = {k: float(probs.get(k, 0.0)) for k in PHONE_CLASS_ORDER}
        total = sum(ordered.values()) or 1.0
        ordered = {k: v / total for k, v in ordered.items()}
        predicted_class = max(ordered, key=ordered.get)
        return PhonePredictionResult(
            predicted_class=predicted_class,
            predicted_name=PHONE_CLASS_NAMES.get(predicted_class, predicted_class),
            confidence=ordered[predicted_class],
            probabilities=ordered,
            backend=backend_name,
            model_name=PHONE_MODEL_NAME,
            model_version=PHONE_MODEL_VERSION,
            input_size=int(getattr(settings, "ML_PHONE_MODEL_INPUT_SIZE", 224)),
        )

    @staticmethod
    def _build_api_result(api_response: dict) -> PhonePredictionResult:
        if not isinstance(api_response, dict):
            raise PhonePredictionError(
                "The phone-image prediction service returned an invalid response."
            )
        raw_probs = api_response.get("probabilities") or {}
        if not isinstance(raw_probs, dict):
            raise PhonePredictionError(
                "The phone-image prediction service returned an invalid "
                "probabilities field."
            )
        probabilities = {k: float(raw_probs.get(k, 0.0)) for k in PHONE_CLASS_ORDER}
        predicted_class = (
            str(api_response.get("predicted_class") or "").strip().lower()
        )
        if predicted_class not in PHONE_CLASS_ORDER:
            raise PhonePredictionError(
                f"The phone-image prediction service returned an unknown class: "
                f"{predicted_class!r}. Expected one of {PHONE_CLASS_ORDER}."
            )
        confidence_raw = api_response.get("confidence")
        try:
            confidence = confidence_to_fraction(confidence_raw)
        except (TypeError, ValueError):
            logger.warning(
                "Phone API response missing valid 'confidence'; falling back "
                "to probabilities[%s] = %s",
                predicted_class, probabilities.get(predicted_class),
            )
            confidence = probabilities.get(predicted_class, 0.0)
        confidence = min(1.0, max(0.0, confidence))
        api_backend = (
            str(api_response.get("backend") or "").strip().lower() or "phone_api"
        )
        try:
            input_size = int(
                api_response.get("input_size")
                or getattr(settings, "ML_PHONE_MODEL_INPUT_SIZE", 224)
            )
        except (TypeError, ValueError):
            input_size = int(getattr(settings, "ML_PHONE_MODEL_INPUT_SIZE", 224))
        return PhonePredictionResult(
            predicted_class=predicted_class,
            predicted_name=PHONE_CLASS_NAMES.get(predicted_class, predicted_class),
            confidence=confidence,
            probabilities=probabilities,
            backend=api_backend,
            model_name=PHONE_MODEL_NAME,
            model_version=PHONE_MODEL_VERSION,
            input_size=input_size,
        )

    @staticmethod
    def class_metadata() -> list:
        return [
            {"code": c, "name": PHONE_CLASS_NAMES.get(c, c)}
            for c in PHONE_CLASS_ORDER
        ]


def phone_confidence_to_fraction(value) -> float:
    return confidence_to_fraction(value)
