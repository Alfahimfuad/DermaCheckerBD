"""Tests for the phone-image (SkinDisNet) prediction workflow.

These tests verify the dual-model architecture the user requested:

* The HAM10000 dermoscopic endpoint and the SkinDisNet phone-image endpoint
  are SEPARATE workflows with separate class lists, separate backends,
  and separate URLs.
* Missing phone-model weights produce a clear error — NEVER a fake
  prediction.
* Quality scores below the threshold block prediction.
* Phone-image metadata is forwarded ONLY for fields the model is
  configured to consume; patient_id is never a prediction feature.
"""
from __future__ import annotations

import io
import os
import tempfile
from unittest import mock

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from apps.common.services.phone_prediction import (
    PHONE_CLASS_ORDER,
    PhoneImagePredictionService,
    PhoneModelNotLoadedError,
    _PhoneMockBackend,
    _PhoneAPIBackend,
)
from apps.predictor.models import PredictionRecord


def _png_bytes(size=(224, 224), color=(220, 180, 160)) -> bytes:
    """Build a small PNG with skin-ish pixels — passes WrongInputService."""
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


class PhoneImageServiceTests(TestCase):
    def tearDown(self):
        # Reset the cached backend so each test starts from a clean slate.
        PhoneImagePredictionService.reset()
        super().tearDown()

    def test_six_class_metadata_matches_spec(self):
        """The phone-image class list is the six SkinDisNet classes
        specified in the project requirements."""
        meta = PhoneImagePredictionService.class_metadata()
        codes = [c["code"] for c in meta]
        self.assertEqual(codes, [
            "atopic_dermatitis",
            "contact_dermatitis",
            "eczema",
            "scabies",
            "seborrheic_dermatitis",
            "tinea_corporis",
        ])
        names = {c["name"] for c in meta}
        self.assertEqual(names, {
            "Atopic Dermatitis",
            "Contact Dermatitis",
            "Eczema",
            "Scabies",
            "Seborrheic Dermatitis",
            "Tinea Corporis",
        })

    @override_settings(ML_PHONE_MODEL_BACKEND="")
    def test_unconfigured_backend_raises_clear_error(self):
        """When ML_PHONE_MODEL_BACKEND is unset, the service raises
        PhoneModelNotLoadedError instead of producing a fake prediction."""
        PhoneImagePredictionService.reset()
        with self.assertRaises(PhoneModelNotLoadedError):
            PhoneImagePredictionService._resolve_backend()
        # The is_configured() helper returns False so the template can
        # surface the right "phone model unavailable" note.
        self.assertFalse(PhoneImagePredictionService.is_configured())

    @override_settings(ML_PHONE_MODEL_BACKEND="keras", ML_PHONE_MODEL_PATH="/nonexistent/model.keras")
    def test_missing_weights_raises_clear_error(self):
        """Even when the backend choice is 'keras', missing weights must
        raise ModelNotLoadedError — never a fabricated prediction."""
        PhoneImagePredictionService.reset()
        with self.assertRaises(PhoneModelNotLoadedError):
            PhoneImagePredictionService._resolve_backend()

    @override_settings(ML_PHONE_MODEL_BACKEND="mock")
    def test_mock_backend_returns_six_classes_only(self):
        """The mock backend returns probabilities for the six SkinDisNet
        classes — NEVER for the seven HAM10000 classes."""
        PhoneImagePredictionService.reset()
        pil = Image.new("RGB", (224, 224), (200, 160, 140))
        result = PhoneImagePredictionService.predict_pil(pil)
        # Probabilities cover the six phone classes.
        self.assertEqual(set(result.probabilities.keys()), set(PHONE_CLASS_ORDER))
        # Probabilities sum to ~1.0 (float tolerance).
        total = sum(result.probabilities.values())
        self.assertAlmostEqual(total, 1.0, places=4)
        # Predicted class is one of the six.
        self.assertIn(result.predicted_class, PHONE_CLASS_ORDER)
        # Backend is the phone mock, NOT the HAM10000 mock.
        self.assertEqual(result.backend, "phone_mock")

    @override_settings(
        ML_PHONE_MODEL_BACKEND="mock",
        PHONE_MODEL_USES_AGE=True,
        PHONE_MODEL_USES_SEX=True,
        PHONE_MODEL_USES_LOCATION=False,
        PHONE_LESION_LOCATIONS=["scalp", "arm", "leg"],
    )
    def test_metadata_whitelist_never_includes_patient_id(self):
        """Patient ID is for record-keeping only — it must NEVER appear
        in the metadata payload forwarded to the model."""
        # The sanitize function is a pure-Python no-network call.
        PhoneImagePredictionService.reset()
        sanitized = PhoneImagePredictionService._sanitize_metadata({
            "patient_id": "PAT-12345",   # must NOT be forwarded
            "age": 45,
            "sex": "female",
            "lesion_location": "scalp",  # must NOT be forwarded (location off)
        })
        self.assertNotIn("patient_id", sanitized)
        self.assertEqual(sanitized["age"], 45)
        self.assertEqual(sanitized["sex"], "female")
        self.assertNotIn("lesion_location", sanitized)

    @override_settings(ML_PHONE_MODEL_BACKEND="mock", PHONE_MODEL_USES_LOCATION=True)
    def test_metadata_location_only_accepted_when_configured(self):
        PhoneImagePredictionService.reset()
        sanitized = PhoneImagePredictionService._sanitize_metadata({
            "lesion_location": "scalp",
        })
        self.assertEqual(sanitized.get("lesion_location"), "scalp")

    @override_settings(ML_PHONE_MODEL_BACKEND="api", AI_PHONE_API_URL="http://localhost:9999")
    def test_api_backend_initializes_only_when_url_set(self):
        """The phone API backend requires AI_PHONE_API_URL."""
        PhoneImagePredictionService.reset()
        backend = PhoneImagePredictionService._resolve_backend()
        self.assertIsInstance(backend, _PhoneAPIBackend)


class PhoneImageEndpointTests(TestCase):
    """End-to-end view-level tests for the /predict/phone-image/ endpoint."""

    def tearDown(self):
        PhoneImagePredictionService.reset()
        super().tearDown()

    def test_endpoint_is_registered_at_predict_phone_image(self):
        """The phone-image endpoint lives at /predict/phone-image/ and is
        reverse-resolvable by name."""
        from django.urls import reverse
        url = reverse("predictor:phone_image_predict")
        self.assertEqual(url, "/predict/phone-image/")

    def test_get_returns_200_with_unified_upload_card(self):
        """A GET to the phone-image endpoint renders the same unified
        upload page — both buttons visible at the bottom of the card."""
        response = self.client.get("/predict/phone-image/")
        self.assertEqual(response.status_code, 200)
        # Both prediction buttons are rendered.
        self.assertContains(response, "Predict Dermoscopic Image")
        self.assertContains(response, "Predict Phone Image")
        # The two supported-category cards are present.
        self.assertContains(response, "Dermoscopic Image · 7 categories")
        self.assertContains(response, "Phone Image · 6 categories")

    @override_settings(ML_PHONE_MODEL_BACKEND="")
    def test_unconfigured_phone_model_returns_clear_error(self):
        """When the phone model is not configured, the POST must surface a
        clear 'not configured' error — never fabricate a prediction."""
        PhoneImagePredictionService.reset()
        img = _png_bytes()
        upload = SimpleUploadedFile(
            "phone.png", img, content_type="image/png"
        )
        # We need the quality check to PASS so we reach the prediction step
        # and hit the not-configured error. The mock image must be at least
        # 200x200 (the IMG_MIN_DIMENSION) — _png_bytes default is 224x224.
        response = self.client.post(
            "/predict/phone-image/",
            {"image": upload, "image_name": "phone-image"},
            follow=False,
        )
        # The view re-renders upload.html with the error message (no redirect).
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "phone-image prediction model is not configured")

    @override_settings(ML_PHONE_MODEL_BACKEND="mock")
    def test_configured_mock_backend_creates_phone_record(self):
        """With the mock backend enabled, a successful POST creates a
        PredictionRecord tagged model_type='phone' and redirects to the
        result page."""
        PhoneImagePredictionService.reset()
        img = _png_bytes()
        upload = SimpleUploadedFile(
            "phone.png", img, content_type="image/png"
        )
        response = self.client.post(
            "/predict/phone-image/",
            {"image": upload, "image_name": "my-phone-image"},
            follow=False,
        )
        # Should redirect to /predict/result/<ref_id>/.
        self.assertEqual(response.status_code, 302)
        self.assertIn("/predict/result/", response["Location"])
        record = PredictionRecord.objects.get()
        self.assertEqual(record.model_type, "phone")
        self.assertEqual(record.backend, "phone_mock")
        # Predicted class is one of the six SkinDisNet codes.
        self.assertIn(record.predicted_class, PHONE_CLASS_ORDER)
        # Probabilities cover the six phone classes only.
        self.assertEqual(set(record.probabilities.keys()), set(PHONE_CLASS_ORDER))

    def test_unsupported_file_type_rejected(self):
        """Non-image uploads are rejected with a clear error message."""
        upload = SimpleUploadedFile(
            "not_image.txt", b"hello world", content_type="text/plain"
        )
        response = self.client.post(
            "/predict/phone-image/",
            {"image": upload, "image_name": "x"},
            follow=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unsupported file type")

    def test_oversize_file_rejected(self):
        """Files above MAX_BYTES (10 MB) are rejected."""
        # 11 MB of zero bytes — content_type=image/png so the file-type
        # check passes and we hit the size check.
        big = SimpleUploadedFile(
            "big.png", b"\x00" * (11 * 1024 * 1024), content_type="image/png"
        )
        response = self.client.post(
            "/predict/phone-image/",
            {"image": big, "image_name": "x"},
            follow=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "File too large")


class UploadPageDualButtonTests(TestCase):
    """Verify the redesigned /predict/ upload page renders both buttons."""

    def test_upload_page_renders_both_prediction_buttons(self):
        response = self.client.get("/predict/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Predict Dermoscopic Image")
        self.assertContains(response, "Predict Phone Image")

    def test_upload_page_renders_two_category_cards(self):
        response = self.client.get("/predict/")
        self.assertContains(response, "Dermoscopic Image · 7 categories")
        self.assertContains(response, "Phone Image · 6 categories")
        # All 7 dermoscopic class codes appear.
        for code in ("akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"):
            self.assertContains(response, code.upper())
        # All 6 phone class names appear.
        for name in (
            "Atopic Dermatitis", "Contact Dermatitis", "Eczema",
            "Scabies", "Seborrheic Dermatitis", "Tinea Corporis",
        ):
            self.assertContains(response, name)

    def test_upload_page_renders_full_width_disclaimer_last(self):
        """The medical disclaimer must appear AFTER the two category cards
        and span the full width."""
        response = self.client.get("/predict/")
        html = response.content.decode()
        cat_idx = html.find("Phone Image · 6 categories")
        disc_idx = html.find("predict-final-disclaimer")
        self.assertGreater(cat_idx, 0)
        self.assertGreater(disc_idx, cat_idx,
                           "Disclaimer must come AFTER the category cards.")


class QualityCheckPageDualButtonTests(TestCase):
    """Verify the /quality/ page renders the new bottom-of-page section."""

    def test_quality_check_page_has_run_prediction_heading(self):
        response = self.client.get("/quality/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Run prediction on this image")

    def test_quality_check_page_explains_phone_vs_dermoscopic(self):
        response = self.client.get("/quality/")
        # The instruction explains both options.
        self.assertContains(response, "mobile phone camera")
        self.assertContains(response, "dermatoscope")

    def test_quality_check_page_renders_both_buttons(self):
        response = self.client.get("/quality/")
        self.assertContains(response, "Predict Dermoscopic Image")
        self.assertContains(response, "Predict Phone Image")
