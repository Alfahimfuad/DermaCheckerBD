from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings

from apps.common.services.ai_api import (
    NonSkinImageError,
    _skin_class_from_response,
    predict_skin_image,
    validate_skin_image,
)
from apps.common.services.prediction import (
    CLASS_ORDER,
    PredictionError,
    PredictionService,
)


@override_settings(
    AI_API_URL="https://prediction.example.test",
    AI_SKIN_API_URL="https://skin.example.test/v2/classify",
    AI_SKIN_API_FILE_FIELD="image",
    AI_API_TOKEN="test-token",
    AI_SKIN_API_TOKEN="skin-test-token",
    AI_API_TIMEOUT=17,
)
class SkinValidationApiTests(SimpleTestCase):
    @patch("apps.common.services.ai_api.requests.post")
    def test_posts_original_bytes_to_dedicated_route_and_accepts_skin(self, post):
        response = Mock()
        response.json.return_value = {"success": True, "prediction": "Skin"}
        post.return_value = response

        validate_skin_image(
            b"original-image-bytes",
            filename="lesion.png",
            content_type="image/png",
        )

        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://skin.example.test/v2/classify")
        self.assertEqual(
            kwargs["files"]["image"],
            ("lesion.png", b"original-image-bytes", "image/png"),
        )
        self.assertEqual(
            kwargs["headers"], {"Authorization": "Bearer skin-test-token"}
        )
        self.assertEqual(kwargs["timeout"], 17)

    @patch("apps.common.services.ai_api.requests.post")
    def test_missing_skin_endpoint_fails_without_calling_another_api(self, post):
        with override_settings(AI_SKIN_API_URL=""):
            with self.assertRaises(PredictionError):
                validate_skin_image(b"image-bytes")

        post.assert_not_called()

    @patch("apps.common.services.ai_api.requests.post")
    def test_skin_api_falls_back_to_shared_token_when_its_token_is_empty(self, post):
        response = Mock()
        response.json.return_value = {"is_skin": True}
        post.return_value = response

        with override_settings(AI_SKIN_API_TOKEN="", AI_API_TOKEN="shared-token"):
            validate_skin_image(b"image-bytes")

        self.assertEqual(
            post.call_args.kwargs["headers"],
            {"Authorization": "Bearer shared-token"},
        )

    @patch("apps.common.services.ai_api.requests.post")
    def test_non_skin_response_is_rejected(self, post):
        response = Mock()
        response.json.return_value = {"success": True, "predicted_class": "Non-Skin"}
        post.return_value = response

        with self.assertRaises(NonSkinImageError):
            validate_skin_image(b"image-bytes")

    def test_boolean_and_probability_response_shapes_are_supported(self):
        self.assertTrue(_skin_class_from_response({"is_skin": True}))
        self.assertFalse(_skin_class_from_response({"is_skin": False}))
        self.assertTrue(_skin_class_from_response({
            "probabilities": {"Skin": 0.9, "Non-Skin": 0.1}
        }))
        self.assertFalse(_skin_class_from_response({
            "probabilities": {"Skin": 0.1, "Non-Skin": 0.9}
        }))

    def test_unknown_or_ambiguous_results_fail_closed(self):
        for payload in (
            {"prediction": "class_1"},
            {"probabilities": {"Skin": 0.5, "Non-Skin": 0.5}},
            {"success": False, "error": "unavailable"},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(PredictionError):
                    _skin_class_from_response(payload)


class SevenClassPredictionApiTests(SimpleTestCase):
    @staticmethod
    def response_payload():
        return {
            "success": True,
            "predicted_class": "mel",
            "confidence": 0.8,
            "probabilities": {
                "akiec": 0.01,
                "bcc": 0.02,
                "bkl": 0.03,
                "df": 0.04,
                "mel": 0.8,
                "nv": 0.09,
                "vasc": 0.01,
            },
        }

    @override_settings(
        AI_API_URL="https://disease.example.test/api",
        AI_API_TIMEOUT=23,
        AI_API_TOKEN="disease-token",
    )
    @patch("apps.common.services.ai_api.requests.post")
    def test_posts_original_file_to_seven_class_predict_endpoint(self, post):
        response = Mock()
        response.json.return_value = self.response_payload()
        post.return_value = response
        upload = SimpleUploadedFile(
            "lesion.webp", b"original-image-bytes", content_type="image/webp"
        )

        result = predict_skin_image(upload)

        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://disease.example.test/api/predict")
        filename, file_object, content_type = kwargs["files"]["file"]
        self.assertEqual(filename, "lesion.webp")
        self.assertEqual(content_type, "image/webp")
        file_object.seek(0)
        self.assertEqual(file_object.read(), b"original-image-bytes")
        self.assertEqual(kwargs["headers"], {"Authorization": "Bearer disease-token"})
        self.assertEqual(kwargs["timeout"], 23)
        self.assertEqual(result["predicted_class"], "mel")
        self.assertEqual(list(result["probabilities"]), CLASS_ORDER)

    def test_seven_class_response_maps_to_existing_class_metadata(self):
        prediction = PredictionService._build_api_result(self.response_payload())

        self.assertEqual(CLASS_ORDER, ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"])
        self.assertEqual(prediction.predicted_class, "mel")
        self.assertEqual(prediction.predicted_name, "Melanoma")
        self.assertEqual(prediction.category, "malignant")
        self.assertEqual(set(prediction.probabilities), set(CLASS_ORDER))

    @override_settings(AI_API_URL="https://disease.example.test")
    @patch("apps.common.services.ai_api.requests.post")
    def test_rejects_incomplete_seven_class_probability_mapping(self, post):
        response = Mock()
        payload = self.response_payload()
        payload["probabilities"].pop("vasc")
        response.json.return_value = payload
        post.return_value = response

        with self.assertRaises(PredictionError):
            predict_skin_image(
                SimpleUploadedFile("lesion.jpg", b"image", content_type="image/jpeg")
            )
