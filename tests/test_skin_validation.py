from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from apps.common.services.ai_api import (
    NonSkinImageError,
    _skin_class_from_response,
    validate_skin_image,
)
from apps.common.services.prediction import PredictionError


@override_settings(
    AI_API_URL="https://prediction.example.test",
    AI_SKIN_API_URL="https://skin-validation.example.test",
    AI_API_TOKEN="test-token",
    AI_API_TIMEOUT=17,
)
class SkinValidationApiTests(SimpleTestCase):
    @patch("apps.common.services.ai_api.requests.post")
    def test_posts_original_bytes_to_dedicated_skin_api_and_accepts_skin(self, post):
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
        # The skin validation endpoint must be the dedicated AI_SKIN_API_URL,
        # NOT the prediction API's AI_API_URL — non-skin images must never
        # be forwarded to the lesion classifier.
        self.assertEqual(args[0], "https://skin-validation.example.test/skin_non_skin")
        self.assertEqual(
            kwargs["files"]["file"],
            ("lesion.png", b"original-image-bytes", "image/png"),
        )
        self.assertEqual(kwargs["headers"], {"Authorization": "Bearer test-token"})
        self.assertEqual(kwargs["timeout"], 17)

    @patch("apps.common.services.ai_api.requests.post")
    def test_non_skin_response_is_rejected(self, post):
        response = Mock()
        response.json.return_value = {"success": True, "predicted_class": "Non-Skin"}
        post.return_value = response

        with self.assertRaises(NonSkinImageError):
            validate_skin_image(b"image-bytes")

    @patch("apps.common.services.ai_api.requests.post")
    def test_falls_back_to_ai_api_url_when_skin_api_url_unset(self, post):
        # Legacy single-service deployments: when AI_SKIN_API_URL is empty,
        # validation reuses the prediction API's AI_API_URL so the workflow
        # still gates uploads on Skin/Non-Skin classification.
        response = Mock()
        response.json.return_value = {"is_skin": True}
        post.return_value = response
        with override_settings(AI_SKIN_API_URL=""):
            validate_skin_image(b"image-bytes")
        args, _ = post.call_args
        self.assertEqual(args[0], "https://prediction.example.test/skin_non_skin")

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
