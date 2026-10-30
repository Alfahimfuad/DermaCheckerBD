from django import forms
from django.conf import settings


class ImageUploadForm(forms.Form):
    image_type = forms.ChoiceField(
        label="Image type",
        choices=[("dermoscopic", "Dermoscopic"), ("phone", "Phone")],
        required=True,
        widget=forms.HiddenInput(attrs={"id": "id_image_type"}),
    )
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
    age = forms.IntegerField(
        label="Age",
        required=False,
        min_value=0,
        max_value=120,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "min": "0",
            "max": "120",
            "placeholder": "Patient age",
            "id": "id_age",
        }),
    )
    sex = forms.ChoiceField(
        label="Sex",
        required=False,
        choices=[("", "Select…")],
        widget=forms.Select(attrs={"class": "form-control", "id": "id_sex"}),
    )
    lesion_location = forms.ChoiceField(
        label="Lesion location",
        required=False,
        choices=[("", "Select…")],
        widget=forms.Select(attrs={"class": "form-control", "id": "id_lesion_location"}),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sex_choices = [("", "Select…")] + [
            (s, s.capitalize()) for s in getattr(settings, "PHONE_SEX_CHOICES", [])
        ]
        self.fields["sex"].choices = sex_choices
        loc_choices = [("", "Select…")] + [
            (loc, loc.capitalize())
            for loc in getattr(settings, "PHONE_LESION_LOCATIONS", [])
        ]
        self.fields["lesion_location"].choices = loc_choices

    def clean_image_type(self):
        value = (self.cleaned_data.get("image_type") or "").strip().lower()
        if value not in ("dermoscopic", "phone"):
            raise forms.ValidationError("Please select an image type.")
        return value

    def clean_age(self):
        value = self.cleaned_data.get("age")
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            raise forms.ValidationError("Age must be a whole number.")

    def clean(self):
        cleaned = super().clean()
        image_type = cleaned.get("image_type")
        if image_type == "phone":
            if not getattr(settings, "PHONE_MODEL_USES_AGE", True):
                cleaned["age"] = None
            elif cleaned.get("age") in (None, ""):
                self.add_error("age", "Age is required for phone images.")
            if not getattr(settings, "PHONE_MODEL_USES_SEX", True):
                cleaned["sex"] = ""
            elif not cleaned.get("sex"):
                self.add_error("sex", "Sex is required for phone images.")
            if not getattr(settings, "PHONE_MODEL_USES_LOCATION", True):
                cleaned["lesion_location"] = ""
            elif not cleaned.get("lesion_location"):
                self.add_error(
                    "lesion_location", "Lesion location is required for phone images."
                )
        else:
            for field in ("age", "sex", "lesion_location"):
                cleaned[field] = cleaned.get(field) or ("" if field != "age" else None)
        return cleaned


class MultiImageUploadForm(forms.Form):
    images = forms.FileField(
        label="Multiple photos of the same lesion",
        widget=forms.ClearableFileInput(attrs={
            "accept": "image/jpeg,image/png,image/webp",
            "class": "form-control",
        }),
    )
