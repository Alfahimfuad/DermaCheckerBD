"""Minimal FastAPI mock server for the PHONE-IMAGE (SkinDisNet) workflow.

This is the phone-image counterpart to ``scripts/mock_fastapi.py`` — it
exposes a separate ``/predict`` endpoint that returns the SIX SkinDisNet
classes, NOT the seven dermoscopic HAM10000 classes. Use it to verify
the Django phone-image workflow end-to-end without a real Keras model.

Run:
    pip install "fastapi<0.115" uvicorn python-multipart pillow
    python scripts/mock_fastapi_phone.py
    # -> listens on http://127.0.0.1:8002

Then in Django's .env:
    ML_PHONE_MODEL_BACKEND=api
    AI_PHONE_API_URL=http://127.0.0.1:8002

The response JSON shape mirrors the dermoscopic mock's contract, but
with the six SkinDisNet classes in place of the seven HAM10000 classes:

    {
      "success": true,
      "predicted_class": "atopic_dermatitis",
      "confidence": 0.5234,
      "probabilities": {
        "atopic_dermatitis": 0.52, "contact_dermatitis": 0.10, ...
      },
      "backend": "phone_mock_api",
      "input_size": 224
    }

Optional metadata form fields (age, sex, lesion_location) are accepted
but ignored by the mock — they would only matter for a model that was
actually trained to consume them.
"""

import hashlib
import io
import math

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image

CLASS_ORDER = [
    "atopic_dermatitis",
    "contact_dermatitis",
    "eczema",
    "scabies",
    "seborrheic_dermatitis",
    "tinea_corporis",
]
CLASS_NAMES = {
    "atopic_dermatitis": "Atopic Dermatitis",
    "contact_dermatitis": "Contact Dermatitis",
    "eczema": "Eczema",
    "scabies": "Scabies",
    "seborrheic_dermatitis": "Seborrheic Dermatitis",
    "tinea_corporis": "Tinea Corporis",
}

app = FastAPI(
    title="DermaCheckerBD Phone-Image Mock AI",
    version="0.1.0",
)

# Allow local Django (any port) to call us during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000", "http://127.0.0.1:8000",
        "http://localhost:8001", "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"service": "phone-image-mock", "classes": CLASS_ORDER}


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    age: str | None = Form(None),
    sex: str | None = Form(None),
    lesion_location: str | None = Form(None),
):
    """Return deterministic, six-class SkinDisNet probabilities.

    The probabilities are seeded from the uploaded file's first 1024 bytes
    so the same image always produces the same prediction. The optional
    metadata form fields (age/sex/lesion_location) are accepted but
    ignored by the mock — only a real model trained on those features
    would actually use them.
    """
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file upload.")

    try:
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Could not decode image: {exc}"
        ) from exc

    # Deterministic hash of pixel content.
    img.thumbnail((64, 64))
    h = hashlib.sha1(img.tobytes()).digest()
    seeds = list(h[:6])
    base_logits = [0.4, -0.3, 0.2, -0.6, -0.1, 0.1]
    noise = [(b - 128) / 128.0 for b in seeds]
    logits = [b + n for b, n in zip(base_logits, noise)]
    z = [l / 0.6 for l in logits]
    m = max(z)
    exp = [math.exp(zi - m) for zi in z]
    s = sum(exp)
    probs = [e / s for e in exp]

    probabilities = {k: float(p) for k, p in zip(CLASS_ORDER, probs)}
    predicted_class = max(probabilities, key=probabilities.get)
    return JSONResponse({
        "success": True,
        "predicted_class": predicted_class,
        "predicted_name": CLASS_NAMES.get(predicted_class, predicted_class),
        "confidence": probabilities[predicted_class],
        "probabilities": probabilities,
        "backend": "phone_mock_api",
        "input_size": 224,
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
