from __future__ import annotations

import io
from unittest import mock

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
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def _skin_png_bytes(size=(224, 224)) -> bytes:
    return _png_bytes(size=size, color=(220, 180, 160))


class PhoneImageServiceTests(TestCase):
    def tearDown(self):
        PhoneImagePredictionService.reset()
        super().tearDown()

    def test_six_class_metadata_matches_spec(self):
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
        PhoneImagePredictionService.reset()
        with self.assertRaises(PhoneModelNotLoadedError):
            PhoneImagePredictionService._resolve_backend()
        self.assertFalse(PhoneImagePredictionService.is_configured())

    @override_settings(ML_PHONE_MODEL_BACKEND="keras", ML_PHONE_MODEL_PATH="/nonexistent/model.keras")
    def test_missing_weights_raises_clear_error(self):
        PhoneImagePredictionService.reset()
        with self.assertRaises(PhoneModelNotLoadedError):
            PhoneImagePredictionService._resolve_backend()

    @override_settings(ML_PHONE_MODEL_BACKEND="mock")
    def test_mock_backend_returns_six_classes_only(self):
        PhoneImagePredictionService.reset()
        pil = Image.new("RGB", (224, 224), (200, 160, 140))
        result = PhoneImagePredictionService.predict_pil(pil)
        self.assertEqual(set(result.probabilities.keys()), set(PHONE_CLASS_ORDER))
        total = sum(result.probabilities.values())
        self.assertAlmostEqual(total, 1.0, places=4)
        self.assertIn(result.predicted_class, PHONE_CLASS_ORDER)
        self.assertEqual(result.backend, "phone_mock")

    @override_settings(
        ML_PHONE_MODEL_BACKEND="mock",
        PHONE_MODEL_USES_AGE=True,
        PHONE_MODEL_USES_SEX=True,
        PHONE_MODEL_USES_LOCATION=False,
        PHONE_LESION_LOCATIONS=["scalp", "arm", "leg"],
    )
    def test_metadata_whitelist_never_includes_patient_id(self):
        PhoneImagePredictionService.reset()
        sanitized = PhoneImagePredictionService._sanitize_metadata({
            "patient_id": "PAT-12345",
            "age": 45,
            "sex": "female",
            "lesion_location": "scalp",
        })
        self.assertNotIn("patient_id", sanitized)
        self.assertEqual(sanitized["age"], 45)
        self.assertEqual(sanitized["sex"], "female")
        self.assertNotIn("lesion_location", sanitized)

    @override_settings(ML_PHONE_MODEL_BACKEND="api", SKINDISNET_API_URL="http://localhost:9999")
    def test_api_backend_initializes_only_when_url_set(self):
        PhoneImagePredictionService.reset()
        backend = PhoneImagePredictionService._resolve_backend()
        self.assertIsInstance(backend, _PhoneAPIBackend)


class UploadPageSelectableCardTests(TestCase):
    def test_upload_page_renders_image_type_selector(self):
        response = self.client.get("/predict/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select Your Image Type")
        self.assertContains(response, "Dermoscopic Image")
        self.assertContains(response, "Phone Image")

    def test_upload_page_renders_both_model_info_cards(self):
        response = self.client.get("/predict/")
        self.assertContains(response, "HAM10000 ResNet50")
        self.assertContains(response, "SkinDisNet EfficientNetB0")
        self.assertContains(response, "7-class")
        self.assertContains(response, "6-class")

    def test_upload_page_renders_both_category_lists(self):
        response = self.client.get("/predict/")
        for code in ("akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"):
            self.assertContains(response, code)
        for name in (
            "Atopic Dermatitis", "Contact Dermatitis", "Eczema",
            "Scabies", "Seborrheic Dermatitis", "Tinea Corporis",
        ):
            self.assertContains(response, name)

    def test_upload_page_has_phone_metadata_fields(self):
        response = self.client.get("/predict/")
        self.assertContains(response, 'id="id_age"')
        self.assertContains(response, 'id="id_sex"')
        self.assertContains(response, 'id="id_lesion_location"')

    def test_upload_page_disclaimer_after_cards(self):
        response = self.client.get("/predict/")
        html = response.content.decode()
        card_idx = html.find("Phone Image")
        disc_idx = html.find("predict-final-disclaimer")
        self.assertGreater(card_idx, 0)
        self.assertGreater(disc_idx, card_idx)


class UploadRoutingTests(TestCase):
    """Pipeline routing: dermoscopic → Skin/Non-Skin → HAM10000;
    phone → Skin/Non-Skin → SkinDisNet. Never both classifiers."""

    def setUp(self):
        from apps.common.services.prediction import PredictionService
        PredictionService.reset()
        PhoneImagePredictionService.reset()
        self.skin_patcher = mock.patch("apps.predictor.views.validate_skin_image")
        self.skin_patcher.start()
        self.addCleanup(self.skin_patcher.stop)

    @override_settings(ML_MODEL_BACKEND="mock", ML_PHONE_MODEL_BACKEND="mock")
    def test_dermoscopic_pipeline_calls_ham10000_not_phoneservice(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.common.services.prediction import PredictionResult
        dermo_result = PredictionResult(
            predicted_class="nv",
            predicted_name="Melanocytic Nevi",
            category="benign",
            confidence=0.9,
            probabilities={
                c: 0.1 for c in ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
            },
            backend="mock",
        )
        with mock.patch(
            "apps.predictor.views.PredictionService.predict_pil",
            return_value=dermo_result,
        ) as dermo_pred, mock.patch(
            "apps.predictor.views.PhoneImagePredictionService.predict_pil"
        ) as phone_pred:
            upload = SimpleUploadedFile(
                "lesion.jpg", _skin_png_bytes(), content_type="image/jpeg"
            )
            response = self.client.post("/predict/", {
                "image": upload,
                "image_type": "dermoscopic",
                "image_name": "dermo-test",
            }, follow=False)
        self.assertEqual(response.status_code, 302)
        dermo_pred.assert_called()
        phone_pred.assert_not_called()
        record = PredictionRecord.objects.get()
        self.assertEqual(record.image_type, "dermoscopic")
        self.assertIn("HAM10000", record.model_name)

    @override_settings(ML_MODEL_BACKEND="mock", ML_PHONE_MODEL_BACKEND="mock")
    def test_phone_pipeline_calls_phoneservice_not_ham10000(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.common.services.phone_prediction import PhonePredictionResult
        phone_result = PhonePredictionResult(
            predicted_class="eczema",
            predicted_name="Eczema",
            confidence=0.7,
            probabilities={c: 1.0 / len(PHONE_CLASS_ORDER) for c in PHONE_CLASS_ORDER},
            backend="phone_mock",
        )
        with mock.patch(
            "apps.predictor.views.PredictionService.predict_pil"
        ) as dermo_pred, mock.patch(
            "apps.predictor.views.PhoneImagePredictionService.predict_pil",
            return_value=phone_result,
        ) as phone_pred:
            upload = SimpleUploadedFile(
                "phone.jpg", _skin_png_bytes(), content_type="image/jpeg"
            )
            response = self.client.post("/predict/", {
                "image": upload,
                "image_type": "phone",
                "image_name": "phone-test",
                "age": "30",
                "sex": "male",
                "lesion_location": "arm",
            }, follow=False)
        self.assertEqual(response.status_code, 302)
        phone_pred.assert_called_once()
        dermo_pred.assert_not_called()
        record = PredictionRecord.objects.get()
        self.assertEqual(record.image_type, "phone")
        self.assertIn("SkinDisNet", record.model_name)
        self.assertEqual(record.patient_age, 30)
        self.assertEqual(record.patient_sex, "male")
        self.assertEqual(record.lesion_location, "arm")

    @override_settings(ML_MODEL_BACKEND="mock")
    def test_missing_image_type_is_rejected(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        upload = SimpleUploadedFile(
            "lesion.jpg", _skin_png_bytes(), content_type="image/jpeg"
        )
        response = self.client.post("/predict/", {
            "image": upload,
            "image_name": "no-type",
        }, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "select an image type")

    @override_settings(ML_MODEL_BACKEND="mock", ML_PHONE_MODEL_BACKEND="mock")
    def test_phone_pipeline_requires_metadata(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        upload = SimpleUploadedFile(
            "phone.jpg", _skin_png_bytes(), content_type="image/jpeg"
        )
        response = self.client.post("/predict/", {
            "image": upload,
            "image_type": "phone",
            "image_name": "no-metadata",
        }, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PredictionRecord.objects.exists())

    def test_non_skin_image_never_reaches_classifier(self):
        from apps.common.services.ai_api import NonSkinImageError
        from django.core.files.uploadedfile import SimpleUploadedFile
        with mock.patch(
            "apps.predictor.views.validate_skin_image",
            side_effect=NonSkinImageError,
        ), mock.patch(
            "apps.predictor.views.PredictionService.predict_pil"
        ) as dermo_pred, mock.patch(
            "apps.predictor.views.PhoneImagePredictionService.predict_pil"
        ) as phone_pred:
            upload = SimpleUploadedFile(
                "notskin.jpg", _skin_png_bytes(), content_type="image/jpeg"
            )
            response = self.client.post("/predict/", {
                "image": upload,
                "image_type": "dermoscopic",
            }, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "classified as non-skin")
        dermo_pred.assert_not_called()
        phone_pred.assert_not_called()
        self.assertFalse(PredictionRecord.objects.exists())

    def test_skin_validation_failure_stops_pipeline(self):
        from apps.common.services.prediction import PredictionError
        from django.core.files.uploadedfile import SimpleUploadedFile
        with mock.patch(
            "apps.predictor.views.validate_skin_image",
            side_effect=PredictionError("service down"),
        ), mock.patch(
            "apps.predictor.views.PredictionService.predict_pil"
        ) as dermo_pred:
            upload = SimpleUploadedFile(
                "lesion.jpg", _skin_png_bytes(), content_type="image/jpeg"
            )
            response = self.client.post("/predict/", {
                "image": upload,
                "image_type": "dermoscopic",
            }, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "could not be completed")
        dermo_pred.assert_not_called()
        self.assertFalse(PredictionRecord.objects.exists())

    @override_settings(ML_PHONE_MODEL_BACKEND="mock")
    def test_unsupported_file_type_rejected(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        upload = SimpleUploadedFile(
            "not_image.txt", b"hello world", content_type="text/plain"
        )
        response = self.client.post("/predict/", {
            "image": upload,
            "image_type": "dermoscopic",
        }, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unsupported file type")

    @override_settings(
        ML_PHONE_MODEL_BACKEND="mock",
        DATA_UPLOAD_MAX_MEMORY_SIZE=12 * 1024 * 1024,
    )
    def test_oversize_file_rejected(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        big = SimpleUploadedFile(
            "big.png", b"\x00" * (11 * 1024 * 1024), content_type="image/png"
        )
        response = self.client.post("/predict/", {
            "image": big,
            "image_type": "dermoscopic",
        }, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "File too large")


class ResultPageDualPipelineTests(TestCase):
    def setUp(self):
        from apps.common.services.prediction import PredictionService
        PredictionService.reset()
        PhoneImagePredictionService.reset()
        from django.core.files.base import ContentFile
        self._ContentFile = ContentFile
        self._img_bytes = _skin_png_bytes()

    def _attach_image(self, record):
        record.image.save(
            f"{record.reference_id}.jpg",
            self._ContentFile(self._img_bytes),
            save=False,
        )
        record.save()

    def test_dermoscopic_result_shows_model_banner(self):
        record = PredictionRecord.objects.create(
            reference_id="DERMO001",
            predicted_class="mel",
            predicted_name="Melanoma",
            category="malignant",
            confidence=0.8,
            probabilities={"mel": 0.8, "nv": 0.2},
            backend="mock",
            image_type="dermoscopic",
            model_name="HAM10000 ResNet50",
        )
        self._attach_image(record)
        response = self.client.get(f"/predict/result/{record.reference_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "HAM10000 ResNet50")
        self.assertContains(response, "Dermoscopic")
        self.assertContains(response, "Seven-class probabilities")

    def test_phone_result_shows_model_banner(self):
        record = PredictionRecord.objects.create(
            reference_id="PHONE001",
            predicted_class="eczema",
            predicted_name="Eczema",
            category="unknown",
            confidence=0.7,
            probabilities={"eczema": 0.7, "scabies": 0.3},
            backend="phone_mock",
            image_type="phone",
            model_name="SkinDisNet EfficientNetB0 + Metadata Fusion",
        )
        self._attach_image(record)
        response = self.client.get(f"/predict/result/{record.reference_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SkinDisNet EfficientNetB0")
        self.assertContains(response, "Phone Image")
        self.assertContains(response, "Six-class probabilities")
