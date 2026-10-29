"""Context processor exposing feature flags + chatbot config to all templates."""
from django.conf import settings
from apps.chatbot.faqs import list_faqs
from apps.common.services.gemini import GeminiService


def feature_flags(request):
    user = request.user
    chatbot_staff_scope = bool(
        user.is_authenticated
        and (
            user.is_staff
            or user.has_perm("predictor.view_medical_priority_queue")
        )
    )
    if not user.is_authenticated:
        chatbot_role = "public"
        chatbot_scope = "public"
    elif chatbot_staff_scope:
        chatbot_role = "staff"
        chatbot_scope = f"staff-{user.pk}"
    else:
        chatbot_role = "user"
        chatbot_scope = f"user-{user.pk}"

    # Pre-compute the FAQ quick-reply list for the chatbot template. We use
    # the request's UI language so the buttons render in the right script.
    ui_language = (
        request.LANGUAGE_CODE[:2]
        if getattr(request, "LANGUAGE_CODE", "en").startswith(("en", "bn"))
        else "en"
    )
    faq_lang = "bn" if ui_language == "bn" or request.COOKIES.get("derma_lang") == "bn" else "en"

    return {
        "similar_cases_enabled": settings.SIMILAR_CASES_ENABLED,
        "chatbot_configured": GeminiService.is_configured(),
        "chatbot_role": chatbot_role,
        "chatbot_scope": chatbot_scope,
        "chatbot_faqs": list_faqs(faq_lang),
        "ml_backend": settings.ML_MODEL_BACKEND,
        "show_research_banner": settings.DEBUG,
        "ui_language": ui_language,
        # Phone-image (SkinDisNet) metadata visibility toggles. The
        # upload.html / quality_check.html templates use these to decide
        # whether to render the age / sex / lesion_location fields. We
        # never assume the model uses any of them — defaults are False.
        "PHONE_MODEL_USES_AGE": settings.PHONE_MODEL_USES_AGE,
        "PHONE_MODEL_USES_SEX": settings.PHONE_MODEL_USES_SEX,
        "PHONE_MODEL_USES_LOCATION": settings.PHONE_MODEL_USES_LOCATION,
        "PHONE_LESION_LOCATIONS": settings.PHONE_LESION_LOCATIONS,
        "PHONE_MODEL_AGE_MIN": settings.PHONE_MODEL_AGE_MIN,
        "PHONE_MODEL_AGE_MAX": settings.PHONE_MODEL_AGE_MAX,
    }
