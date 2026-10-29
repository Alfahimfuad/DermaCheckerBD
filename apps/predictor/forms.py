"""Forms for the predictor app."""
from django import forms
from django.conf import settings


class ImageUploadForm(forms.Form):
    """Single-image upload form. The actual validation is done in the view
    (file-type, file-size, integrity) because Django forms don't natively
    cover all our checks."""
    image_name = forms.CharField(
        label="Image name",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "autocomplete": "off",
            "placeholder": "Enter an image name",
        }),
    )
    image = forms.FileField(
        label="Skin lesion image",
        help_text="JPG, PNG, or WEBP. Max 10 MB.",
        widget=forms.ClearableFileInput(attrs={
            "accept": "image/jpeg,image/png,image/webp",
            "class": "form-control",
            "id": "id_image_file",
        }),
    )


class MultiImageUploadForm(forms.Form):
    """Multi-image upload form (for the Multi-Image Disagreement feature).

    NOTE: Django's ClearableFileInput doesn't support the HTML 'multiple'
    attribute natively. The multi_image app uses a plain ClearableFileInput
    in its view (request.FILES.getlist('images')) rather than this form.
    This class is kept for documentation purposes only.
    """
    images = forms.FileField(
        label="Multiple photos of the same lesion",
        widget=forms.ClearableFileInput(attrs={
            "accept": "image/jpeg,image/png,image/webp",
            "class": "form-control",
        }),
    )


class PhoneImageMetadataForm(forms.Form):
    """Metadata collected for phone-image (SkinDisNet) predictions.

    Only fields the trained model is configured to consume are rendered
    (see settings ``PHONE_MODEL_USES_*``). ``patient_id`` is for record
    association ONLY — it is never passed as a model feature.

    All fields are optional from the form's perspective; the view
    enforces required-ness based on the model's configuration.
    """

    patient_id = forms.CharField(
        label="Patient ID / Reference",
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control app-form-control",
            "autocomplete": "off",
            "placeholder": "Optional record-keeping reference",
        }),
        help_text="For record association only. Never used as a prediction feature.",
    )

    age = forms.IntegerField(
        label="Age",
        required=False,
        min_value=settings.PHONE_MODEL_AGE_MIN,
        max_value=settings.PHONE_MODEL_AGE_MAX,
        widget=forms.NumberInput(attrs={
            "class": "form-control app-form-control",
            "min": settings.PHONE_MODEL_AGE_MIN,
            "max": settings.PHONE_MODEL_AGE_MAX,
            "placeholder": "Patient age in years",
        }),
    )

    SEX_CHOICES = [
        ("", "— Select —"),
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
        ("unknown", "Prefer not to say"),
    ]

    sex = forms.ChoiceField(
        label="Sex",
        required=False,
        choices=SEX_CHOICES,
        widget=forms.Select(attrs={"class": "form-control app-form-control"}),
    )

    # Populated dynamically from settings.PHONE_LESION_LOCATIONS. If the
    # dataset/model did not register any location options, the field is
    # rendered as a single "N/A" disabled select so the form layout stays
    # stable but the model never receives an unsupported value.
    lesion_location = forms.ChoiceField(
        label="Lesion location",
        required=False,
        choices=[("", "— Select —")] +
                [(loc, loc) for loc in settings.PHONE_LESION_LOCATIONS],
        widget=forms.Select(attrs={"class": "form-control app-form-control"}),
    )

    image_name = forms.CharField(
        label="Image name",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control app-form-control",
            "autocomplete": "off",
            "placeholder": "Enter an image name",
        }),
    )
    image = forms.FileField(
        label="Phone-camera skin image",
        help_text="JPG, PNG, or WEBP. Max 10 MB.",
        widget=forms.ClearableFileInput(attrs={
            "accept": "image/jpeg,image/png,image/webp",
            "class": "form-control",
        }),
    )
