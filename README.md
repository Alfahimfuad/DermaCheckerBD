# DermaCheckerBD — Skin Cancer Prediction Website (Django)

An experimental, research-support prototype for skin-lesion analysis. Built as
a university CSE capstone. **Not a medical device. Predictions are unverified
and may be wrong.**

> ⚠️ **Medical disclaimer**: This prototype does NOT provide a medical diagnosis.
> If you are concerned about a skin lesion — especially one that is changing,
> bleeding, growing, or painful — consult a qualified dermatologist promptly.
> Do not delay professional evaluation based on this tool's output.

---

## What this project is

A Django web application that wraps a skin-lesion classification model with
practical, transparency-oriented features:

| Feature                       | What it does                                                              |
| ----------------------------- | -------------------------------------------------------------------------- |
| **Smart Photo Guide**         | Detects blur, exposure, framing, and skin-plausibility before prediction. |
| **AI Reliability Check**      | Runs predictions across mild image transforms; reports agreement %.      |
| **Multi-Image Disagreement**  | Compares predictions across N photos of the same lesion.                  |
| **Lesion Follow-up Tracker**  | Private per-user lesion records with a timeline + PDF summary.            |
| **Gemini Floating Assistant** | Role-scoped chatbot for public help, a user's own dashboard, and staff aggregates. Never diagnoses. |
| **Wrong-Input Protection**    | Flags non-skin / corrupt / out-of-range inputs before predicting.        |
| **Similar Case Explorer**    | Modular stub. Plug in a reference dataset to enable.                      |

The default prediction backend is the supplied fine-tuned HAM10000 ResNet50
Keras model. A deterministic mock backend remains available for tests and demos;
the ONNX backend is an optional integration point.

---

## Tech stack

- **Backend**: Python 3.12, Django 5.1, Django REST Framework
- **Frontend**: HTML5, CSS3, Bootstrap 5, vanilla JavaScript, Lucide icons
- **Database**: SQLite (local) → PostgreSQL via `DATABASE_URL` (production, e.g., Neon)
- **ML**: TensorFlow/Keras ResNet50, OpenCV, Pillow, NumPy
- **PDF**: ReportLab
- **AI assistant**: Google Gemini (`google-genai` SDK) — called server-side only
- **Static**: WhiteNoise (compressed, manifest-hashed)
- **WSGI**: Gunicorn
- **Deployment**: Render (Render Blueprint in `render.yaml`)

---

## Quick start (local development in VS Code)

```bash
# 1. Clone & cd in
git clone <your-repo-url> dermacheckerbd
cd dermacheckerbd

# 2. Create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
# For the bundled local Keras model:
pip install -r requirements-ml.txt
# For an API-only setup, install requirements.txt instead.

# 4. Configure environment
cp .env.example .env
# Windows PowerShell alternative: Copy-Item .env.example .env
# For local PostgreSQL, uncomment LOCAL_DB_* in .env and enter your local
# database password there. Leave them commented to use SQLite.

# 5. Apply database migrations
python manage.py migrate

# 6. (Optional) Create an admin user
python manage.py createsuperuser

# 7. Run the development server
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser.

---

## Doctor follow-up queue

The doctor panel is available at `/doctors/panel/`. After migrations, an
administrator can create a Django auth group for doctors and grant it the
`Can access and manage the medical follow-up queue` permission. Add doctor
accounts to that group; the panel link then appears for those users. Priority
groups and review statuses are follow-up workflow aids, not diagnoses.

---

## Project layout

```
dermacheckerbd/              # Django project package (settings, urls, wsgi, asgi)
apps/                    # Local apps
  accounts/              # signup, login, profile
  core/                  # home, about, how_it_works, privacy
  predictor/             # upload, predict, result, history, PDF report
  photo_guide/           # standalone image-quality checker
  reliability/           # standalone AI Reliability Check page
  multi_image/           # multi-image disagreement
  tracker/               # lesion follow-up tracker
  chatbot/               # Gemini floating assistant endpoint
  similar_cases/         # stubbed similar-case explorer
  common/                # shared services (no URLs, no models)
    services/
      prediction.py      # pluggable PredictionService (keras/mock/onnx)
      image_quality.py   # Smart Photo Guide checks
      reliability.py     # reliability check transforms
      multi_image.py     # multi-image disagreement
      gemini.py          # Gemini client wrapper + safe-mode fallback
      pdf_report.py      # ReportLab PDF report builder
      wrong_input.py    # wrong-input protection
      similar_cases.py   # modular stub
templates/               # Django templates (base, includes/, per-app dirs)
static/                  # CSS, JS, images
  css/main.css           # design system
  js/main.js             # global JS
  js/image-upload.js     # drag-and-drop upload component
  js/chatbot.js          # floating chatbot client
media/                   # user uploads (gitignored)
  uploads/               # uploaded prediction images
  tracked/               # follow-up tracker photos
  reference/             # reference dataset for Similar Cases (when enabled)
scripts/                 # development scripts (smoke tests, etc.)
tests/                   # Django test suite
db/                      # SQLite db + cache (gitignored)
download/                # generated PDFs / images from smoke tests
.env / .env.example      # environment configuration
Procfile                 # Render/Heroku-style process file
render.yaml              # Render Blueprint
runtime.txt              # Python version pin
requirements.txt
requirements-ml.txt          # optional TensorFlow/Keras inference dependencies
manage.py
```

---

## Configuration (environment variables)

| Variable                   | Default                                          | Notes                                                |
| -------------------------- | ------------------------------------------------ | ---------------------------------------------------- |
| `DJANGO_DEBUG`             | `True`                                           | Set `False` in production.                          |
| `DJANGO_SECRET_KEY`        | `dev-insecure-...`                               | Generate a long random string for production.       |
| `DJANGO_ALLOWED_HOSTS`     | `localhost,127.0.0.1,...`                        | Comma-separated. Render domain is auto-added.       |
| `DATABASE_URL`             | unset                                            | Hosted PostgreSQL connection string; SSL is required. |
| `CLOUDINARY_URL`           | unset locally                                    | Required when `DJANGO_DEBUG=False`; use `cloudinary://API_KEY:API_SECRET@CLOUD_NAME`. |
| `LOCAL_DB_HOST`            | unset                                            | Set to `127.0.0.1` to use PostgreSQL installed on your PC. |
| `LOCAL_DB_PORT`            | `5432`                                           | Local PostgreSQL port.                               |
| `LOCAL_DB_NAME`            | unset                                            | Local database name; required when `LOCAL_DB_HOST` is set. |
| `LOCAL_DB_USER`            | unset                                            | Local database user; required when `LOCAL_DB_HOST` is set. |
| `LOCAL_DB_PASSWORD`        | blank                                            | Local database password; keep it in your ignored `.env`. |
| `LOCAL_DB_SSLMODE`         | `disable`                                        | Local connection SSL mode; use `require` only if configured. |
| `ML_MODEL_BACKEND`         | `keras`                                          | `keras` / `mock` / `onnx` / `api`. Render uses `api`. |
| `ML_MODEL_PATH`            | attached `.keras` model                          | Path to the fine-tuned model file; defaults to `/tmp/dermacheckerbd/resnet50_finetuned_1791994962604.keras` when `MODEL_GDRIVE_URL` is set. |
| `MODEL_GDRIVE_URL`         | unset                                            | Optional public Google Drive share link. If the model is missing, it downloads at WSGI startup. |
| `AI_API_URL`               | local URL in development                         | Required in production when `ML_MODEL_BACKEND=api`; set to the HTTPS prediction API URL. |
| `AI_API_TOKEN`             | unset                                            | Optional bearer token for the prediction API. |
| `AI_API_TIMEOUT`           | `120` seconds                                    | Per-request timeout for the prediction API. |
| `AI_SKIN_API_URL`          | unset (falls back to `AI_API_URL`)               | Dedicated Skin/Non-Skin validation API URL. Every upload — on both the Smart Photo Guide and the Skin Image Prediction pages — is sent here first; non-skin images are never forwarded to the lesion classifier. |
| `ML_MODEL_INPUT_SIZE`      | `224`                                            | Resize dimension used in preprocessing.             |
| `ML_MODEL_CLASSES`         | `akiec,bcc,bkl,df,mel,nv,vasc`                   | Must match the trained model's output order.        |
| `ML_MODEL_RESAMPLE`        | `BILINEAR`                                       | Resize filter; matches the supplied training pipeline. |
| `GEMINI_API_KEY`           | unset                                            | Leave unset to run chatbot in offline mode.         |
| `GEMINI_MODEL`             | `gemini-2.0-flash`                               | Model name.                                          |
| `GEOAPIFY_API_KEY`         | unset                                            | Optional key for Nearby Doctors and Hospitals.      |
| `DJANGO_SUPERUSER_USERNAME`| unset                                            | Set in Render to create the initial admin account.   |
| `DJANGO_SUPERUSER_PASSWORD`| unset                                            | Set in Render; at least 12 characters.              |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | unset                                          | Optional comma-separated trusted origins. Replit preview origins are allowed automatically in development only. |
| `CHATBOT_RATE_LIMIT`       | `10/m`                                           | django-ratelimit spec (10 messages/minute/IP).      |
| `IMG_BLUR_THRESHOLD`       | `100.0`                                          | Laplacian-variance threshold for blur.              |
| `IMG_BRIGHTNESS_MIN/MAX`   | `40 / 220`                                       | Acceptable mean-intensity range.                    |
| `RELIABILITY_TRANSFORMS`   | `brightness_up,...,slight_rotation`              | Comma-separated transform names.                    |
| `SIMILAR_CASES_ENABLED`    | `False`                                          | Toggle Similar Case Explorer.                       |
| `IMAGE_RETENTION_DAYS`     | `0`                                              | 0 = keep forever.                                   |

### Render Django admin account

Set `DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD` in the Render
web service environment. The Render start command runs migrations and
`ensure_render_superuser`, which creates the account once and never changes an
existing account's password. Both values are required for the Render Blueprint
to start. The footer's **Admin** link opens `/admin/`; only staff users can sign
in there. Do not commit the password to the repository.

---

## Prediction model

The default model is `attached_assets/resnet50_finetuned_1791994962604.keras`,
a fine-tuned ResNet50 for the seven HAM10000 diagnosis classes. Keep the model
at that path or set `ML_MODEL_PATH` to its location. It is about 201 MB and
should not be committed to Git.

Inference converts each upload to RGB, resizes it to 224×224 with bilinear
interpolation, converts pixels back to `[0, 255]`, and applies
`tf.keras.applications.resnet50.preprocess_input` before calling the model.
Output order is `akiec,bcc,bkl,df,mel,nv,vasc`. The `.keras` model is loaded
once per application process on the first prediction, then reused.

The model file was provided with reported test metrics of 73.49% accuracy,
61.67% macro F1, and 95.77% macro AUC; those figures have not been independently
verified and do not establish clinical validity. This is an educational/research
prototype, not a medical diagnostic tool. Consult a qualified dermatologist or
healthcare professional for proper evaluation.

Set `ML_MODEL_BACKEND=mock` to use deterministic demo predictions instead.

---

## Running tests

```bash
python manage.py test tests -v2
```

26 automated tests cover:

- Authentication & authorization (signup, login required for tracker/profile).
- Valid and invalid uploads (file-type, file-size, content).
- Image preprocessing and prediction service behavior (determinism, 7 classes,
  probabilities sum to 1, Keras preprocessing and model-load caching).
- Prediction failures are returned as a safe user-facing message.
- Image-quality checks (good image passes, tiny image fails).
- Reliability check (produces variants, computes agreement).
- Multi-image disagreement (returns modal class).
- Wrong-input protection (valid skin image passes, corrupt bytes fail).
- Tracker privacy (Alice can view her record; Bob gets 404; Bob cannot delete).
- Chatbot endpoint (returns JSON, rejects empty/invalid messages).
- Production-safe settings (CSRF middleware enabled).

Smoke tests (run them with `python scripts/`):

- `scripts/smoke_test_services.py` — exercises the service layer directly.
- `scripts/http_e2e_test.py` — exercises the full HTTP pipeline against a
  running server (start the server first, then run the script).

---

## Deployment to Render

### VS Code → GitHub → Render → Neon (Blueprint)

1. In Neon, create a PostgreSQL project and copy its **pooled** connection
   string. Keep it private.
2. In VS Code, commit and push this project to the GitHub `main` branch.
3. In Render, choose **New → Blueprint**, connect the GitHub repository, and
   select `render.yaml`. The Blueprint creates the web service; it does not
   create a database on Render.
4. When Render asks for environment values, set these on the web service:
   - `DATABASE_URL` — the Neon pooled connection string.
   - `DJANGO_SECRET_KEY` — a new, long random value (never the development
     placeholder).
   - `DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD` — your admin
     login; use a strong password of at least 12 characters.
   - `AI_API_URL` — the reachable HTTPS URL of your separate prediction API.
   - `AI_API_TOKEN` — only if that API requires bearer-token authentication.
   - `GEMINI_API_KEY` — optional; omit it to keep the assistant in offline mode.
   - `GEOAPIFY_API_KEY` — optional; only needed for Nearby Doctors.
5. Render deploys from `main` automatically after each push. The site health
   endpoint is `/healthz/`; Django admin is at `/admin/`.

The Blueprint sets `ML_MODEL_BACKEND=api`, so this website does not download or
load TensorFlow/model files. `requirements.txt` contains the web/API dependencies
only; `requirements-ml.txt` is for local Keras inference.

This Blueprint uses Render Free. Free web services do not support pre-deploy
commands, so the start command applies migrations and creates the admin before
starting one Gunicorn worker. These operations are safe to repeat on a single
instance. Render Free services can sleep when idle; use a paid plan and a
pre-deploy migration command if you later need always-on service or multiple
instances.

### Persistent image storage in production

Production requires a `CLOUDINARY_URL` deployment secret and uses Cloudinary
for uploaded images. Set its value to the full URL in this form:
`cloudinary://API_KEY:API_SECRET@CLOUD_NAME`. In Render, enter only the URL as
the secret value—do not include `CLOUDINARY_URL=` or wrap it in quotes.

The URL must use the `cloudinary://` scheme. A missing URL or one with a
different scheme causes Django to stop during startup instead of silently
saving uploads to the ephemeral local filesystem. Local development continues
to use `MEDIA_ROOT` when the URL is unset. Never commit or share the Cloudinary
URL.

---

## Database migrations on Render

The Free-plan Blueprint runs `python manage.py migrate --noinput` before each
web process starts, with one worker/instance. On a paid Render plan, prefer
Render's `preDeployCommand` for migrations so database changes finish before
the new web process starts.

---

## Enabling the Similar Case Explorer

The feature is shipped stubbed (`SIMILAR_CASES_ENABLED=False`). To enable:

1. Place your reference image dataset (e.g., HAM10000) under a directory your
   app can read.
2. Pre-compute image embeddings for that dataset using a ResNet50 / CLIP /
   EfficientNet backbone. Store them as a numpy matrix + a list of
   `(image_id, label)` pairs.
3. Implement `_compute_embedding()` and `search()` in
   `apps/common/services/similar_cases.py`. The view layer is already wired up.
4. Set `SIMILAR_CASES_ENABLED=True` and `SIMILAR_CASES_REFERENCE_DIR=...`.

---

## Enabling the live Gemini chatbot

1. Get a Gemini API key from
   <https://aistudio.google.com/app/apikey>.
2. Set `GEMINI_API_KEY=...` in your environment.
3. Restart the server. The floating chatbot will switch from offline
   canned responses to real Gemini calls.

The chatbot's system prompt (see `apps/common/services/gemini.py`) forbids
diagnosing cancer, prescribing medication, or promising a lesion is safe based
on the model output. Image bytes are never sent to Gemini — only text.

### Chatbot access and privacy

The floating assistant sends messages to Django; the browser never calls Gemini
directly. `GEMINI_API_KEY` stays on the server and should be stored in an
environment variable or the hosting platform's secrets manager, never in
frontend code or a committed file.

- **Visitors who are not signed in** can ask about public site information and
  general questions. They do not receive account, dashboard, prediction-history,
  profile, or lesion-tracker data. Requests for personal information are directed
  to sign in.
- **Signed-in users** can ask about their own dashboard and recent activity.
  The server builds private context only from the authenticated account;
  browser-supplied dashboard data is not accepted.
- **Django staff and doctors with the medical follow-up queue permission** can
  ask for anonymized site-wide totals and trends, such as user, prediction, and
  tracked-lesion counts or prediction/review-status summaries. The assistant
  does not receive usernames, contact details, individual histories, or
  individual records, and it refuses requests to reveal them.

The chatbot is informational only and does not provide a diagnosis. Gemini
receives text conversation only; uploaded images are not sent to the API.

---

## Research evaluation protocol

The system is designed for measurable experiments. Two features in particular
support research:

1. **AI Reliability Check** — compare stability (agreement %) against
   baselines: max-softmax confidence, predictive entropy, expected calibration
   error. Evaluate whether low-stability predictions correlate with wrong
   predictions, especially for melanoma (`mel`).
2. **Multi-Image Disagreement** — evaluate whether significant disagreement
   across photos of the same lesion is a useful referral signal (i.e., a
   proxy for "this case is uncertain; refer to a dermatologist").

Suggested metrics: **sensitivity, specificity, macro-F1, confusion matrix,
expected calibration error (ECE), and Brier score**. Use patient- or
lesion-level separation where the dataset provides identifiers — prevent
data leakage between training and evaluation splits.

Do not fabricate experimental results. Run the evaluation on real data and
report the numbers honestly, even if they are unfavourable.

---

## Security & privacy summary

- HTTPS enforced in production; HSTS, secure cookies, X-Frame-Options DENY.
- CSRF on every form & state-changing request.
- File type + size validation on every upload.
- Rate limiting on the chatbot endpoint (`10/m` per IP by default).
- API keys are read from environment variables — never exposed to the frontend.
- Chatbot context is role-scoped: public visitors get no private context, users
  get only their own data, and staff receive aggregate statistics only.
- Tracker records are scoped to the requesting user (`get_object_or_404`
  with `user=request.user` filter) — there is no way to enumerate another
  user's records.
- Image bytes are never sent to Gemini.
- `.env` is gitignored; `.env.example` contains placeholder values only.

---

## Acknowledgements

- **HAM10000** dataset: Tschandl, P., Rosendahl, C. & Kittler, H. (2018).
  _Scientific Data_. The class names and categories used in this project
  match the HAM10000 documentation.
- **Google Gemini** for the AI assistant SDK.
- **Bootstrap 5**, **Lucide icons**, **ReportLab**, **OpenCV**, **Pillow**.

---

## License

This project is provided as-is for educational purposes. It is NOT a medical
device. Use of the HAM10000 dataset, the Gemini API, and any other third-party
asset is subject to the respective upstream licenses.
