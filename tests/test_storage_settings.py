"""Tests for production-safe media storage selection."""
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from dermacheckerbd.storage import (
    CLOUDINARY_MEDIA_STORAGE,
    LOCAL_MEDIA_STORAGE,
    resolve_media_storage_backend,
)


class MediaStorageSettingsTests(SimpleTestCase):
    def test_local_development_uses_media_root_without_cloudinary(self):
        self.assertEqual(resolve_media_storage_backend(True, ""), LOCAL_MEDIA_STORAGE)

    def test_configured_cloudinary_url_selects_cloudinary_storage(self):
        self.assertEqual(
            resolve_media_storage_backend(
                False, "cloudinary://test-key:test-secret@example-cloud"
            ),
            CLOUDINARY_MEDIA_STORAGE,
        )

    def test_production_without_cloudinary_fails_instead_of_using_local_disk(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "CLOUDINARY_URL must be set when DJANGO_DEBUG is False",
        ):
            resolve_media_storage_backend(False, "")

        with self.assertRaises(ImproperlyConfigured):
            resolve_media_storage_backend(False, "   ")
