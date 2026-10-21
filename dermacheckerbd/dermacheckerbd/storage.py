"""Storage backend selection for uploaded media."""
from django.core.exceptions import ImproperlyConfigured


CLOUDINARY_MEDIA_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
LOCAL_MEDIA_STORAGE = "django.core.files.storage.FileSystemStorage"


def resolve_media_storage_backend(debug: bool, cloudinary_url: str) -> str:
    """Select Cloudinary when configured and reject unsafe production fallback."""
    cloudinary_url = (cloudinary_url or "").strip()
    if cloudinary_url:
        if not cloudinary_url.startswith("cloudinary://"):
            raise ImproperlyConfigured(
                "CLOUDINARY_URL must start with 'cloudinary://' when set."
            )
        return CLOUDINARY_MEDIA_STORAGE

    if not debug:
        raise ImproperlyConfigured(
            "CLOUDINARY_URL must be set when DJANGO_DEBUG is False; "
            "production media uploads cannot use local disk."
        )

    return LOCAL_MEDIA_STORAGE
