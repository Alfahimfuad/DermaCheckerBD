"""Predefined FAQ list for anonymous (logged-out) chatbot users.

SECURITY / RESOURCE CONTRACT:
- These responses are returned to anonymous visitors WITHOUT calling the
  Gemini API. They keep Render memory and CPU usage flat regardless of
  anonymous traffic.
- Answers are static, educational, and reviewed to match the project's
  existing medical disclaimer. They never claim to diagnose.
- Logged-in users continue to receive the full Gemini-powered chatbot —
  this module is only consulted when ``request.user.is_authenticated``
  is False.

Each FAQ exposes:
    id        – stable slug used by the chatbot frontend (FAQ button payload)
    question  – {en, bn} short label shown on the button
    answer    – {en, bn} pre-written reply (HTML allowed: b, i, em, strong,
                code, br, ul, ol, li, p — same allowlist as Gemini replies)

The list is intentionally kept to 7 items so the FAQ button bar stays
compact on mobile.
"""
from __future__ import annotations

from typing import List, Dict, Optional


# 7 predefined FAQs (must stay at 7 — tests rely on this count).
FAQS: List[Dict[str, object]] = [
    {
        "id": "what_is",
        "question": {
            "en": "What is DermaCheckerBD?",
            "bn": "DermaCheckerBD কী?",
        },
        "answer": {
            "en": (
                "<p><b>DermaCheckerBD</b> is an experimental research prototype that "
                "wraps a fine-tuned ResNet50 image-classification model with practical "
                "transparency features (photo guide, reliability check, multi-image "
                "comparison, lesion tracker). It was built by <b>AL Fahim Fuad and his "
                "team</b> as a CSE Capstone Project at <b>East West University (EWU)</b>.</p>"
                "<p>It is <b>NOT a medical device</b> and does not provide a diagnosis. "
                "Every prediction is unverified and may be wrong.</p>"
            ),
            "bn": (
                "<p><b>DermaCheckerBD</b> একটি পরীক্ষামূলক গবেষণা প্রোটোটাইপ, যেখানে "
                "একটি ফাইন-টিউনড ResNet50 ইমেজ-শ্রেণিবিন্যাস মডেলের সাথে কিছু সহায়ক "
                "বৈশিষ্ট্য যুক্ত আছে (ছবি গাইড, নির্ভরযোগ্যতা যাচাই, একাধিক ছবি তুলনা, "
                "লেসন ট্র্যাকার)। এটি তৈরি করেছেন <b>AL Fahim Fuad ও তাঁর দল</b>, "
                "<b>East West University (EWU)</b>-এর CSE Capstone Project হিসেবে।</p>"
                "<p>এটি <b>চিকিৎসা-নির্ণয় দেয় না</b> এবং প্রতিটি ফলাফল যাচাইহীন — ভুলও "
                "হতে পারে।</p>"
            ),
        },
    },
    {
        "id": "accuracy",
        "question": {
            "en": "How accurate are the predictions?",
            "bn": "প্রেডিকশনগুলো কতটা নির্ভুল?",
        },
        "answer": {
            "en": (
                "<p>A higher <b>confidence score</b> means the model is more sure about "
                "its top-class guess — <b>not</b> that the guess is medically correct. "
                "Even a 99% confidence can be wrong.</p>"
                "<p>The optional <b>AI Reliability Check</b> reports how often the "
                "top-class prediction stayed the same across mild image transforms "
                "(brightness, contrast, slight rotation). High agreement means the "
                "model is <i>stable</i> on this image, not that it is <i>correct</i>.</p>"
                "<p>Treat every output as unverified information that needs professional "
                "review.</p>"
            ),
            "bn": (
                "<p><b>আস্থার স্কোর</b> বেশি হলে বোঝায় মডেলটি তার প্রধান শ্রেণির "
                "অনুমানে বেশি নিশ্চিত — ফলাফলটি চিকিৎসাগতভাবে সঠিক, তা নয়। "
                "৯৯% স্কোরও ভুল হতে পারে।</p>"
                "<p><b>নির্ভরযোগ্যতা যাচাই</b> দেখায়, ছবিতে সামান্য পরিবর্তন করলে "
                "মডেলের প্রধান শ্রেণির অনুমান কতবার একই থাকে। বেশি মিল মানে মডেলটি "
                "এই ছবিতে স্থিতিশীল — রোগ নির্ণয় সঠিক, তা নয়।</p>"
                "<p>প্রতিটি ফলাফলকে যাচাইহীন তথ্য হিসেবে দেখুন।</p>"
            ),
        },
    },
    {
        "id": "photo_guide",
        "question": {
            "en": "How do I upload a clear photo?",
            "bn": "পরিষ্কার ছবি কীভাবে দিব?",
        },
        "answer": {
            "en": (
                "<p>For best results:</p>"
                "<ul>"
                "<li>Use <b>good, even lighting</b> (daylight is ideal; avoid harsh shadows).</li>"
                "<li>Fill the frame with the lesion but keep <b>some surrounding skin</b> visible.</li>"
                "<li>Hold the camera <b>parallel</b> to the skin and <b>steady</b> to avoid blur.</li>"
                "<li>Use JPG, PNG, or WEBP; max 10 MB.</li>"
                "</ul>"
                "<p>The Smart Photo Guide checks blur, exposure, framing, and skin "
                "plausibility before any prediction runs.</p>"
            ),
            "bn": (
                "<p>ভালো ফলাফলের জন্য:</p>"
                "<ul>"
                "<li><b>সমভাবে আলো</b> ব্যবহার করুন (দিনের আলো আদর্শ; তীব্র ছায়া এড়ান)।</li>"
                "<li>দাগটি ফ্রেমে আনুন, সাথে <b>কিছুটা চারপাশের ত্বক</b> রাখুন।</li>"
                "<li>ক্যামেরা ত্বকের সাথে <b>সমান্তরাল</b> ও <b>স্থির</b> রাখুন।</li>"
                "<li>JPG, PNG বা WEBP; সর্বোচ্চ ১০ MB।</li>"
                "</ul>"
                "<p>স্মার্ট ফটো গাইড প্রেডিকশনের আগেই ঝাপসা, আলো, ফ্রেমিং ও ত্বক "
                "যাচাই করে।</p>"
            ),
        },
    },
    {
        "id": "class_names",
        "question": {
            "en": "What do the class names (mel, nv, bcc…) mean?",
            "bn": "শ্রেণির নামগুলো (mel, nv, bcc…) কী বোঝায়?",
        },
        "answer": {
            "en": (
                "<p>The model classifies a lesion into one of seven HAM10000 classes:</p>"
                "<ul>"
                "<li><b>akiec</b> — Actinic Keratoses / Bowen's Disease (pre-malignant)</li>"
                "<li><b>bcc</b> — Basal Cell Carcinoma (malignant)</li>"
                "<li><b>bkl</b> — Benign Keratosis-like Lesions (benign)</li>"
                "<li><b>df</b> — Dermatofibroma (benign)</li>"
                "<li><b>mel</b> — Melanoma (malignant)</li>"
                "<li><b>nv</b> — Melanocytic Nevi (benign)</li>"
                "<li><b>vasc</b> — Vascular Lesions (benign)</li>"
                "</ul>"
                "<p>These are research labels, not a diagnosis.</p>"
            ),
            "bn": (
                "<p>মডেলটি একটি দাগকে নিচের সাতটি HAM10000 শ্রেণির যেকোনো একটিতে "
                "ভাগ করে:</p>"
                "<ul>"
                "<li><b>akiec</b> — অ্যাক্টিনিক কেরাটোসিস / বোয়েন রোগ (প্রি-ম্যালিগন্যান্ট)</li>"
                "<li><b>bcc</b> — বেসাল সেল কার্সিনোমা (ম্যালিগন্যান্ট)</li>"
                "<li><b>bkl</b> — বিনাইন কেরাটোসিস-সদৃশ ক্ষত (বিনাইন)</li>"
                "<li><b>df</b> — ডার্মাটোফাইব্রোমা (বিনাইন)</li>"
                "<li><b>mel</b> — মেলানোমা (ম্যালিগন্যান্ট)</li>"
                "<li><b>nv</b> — মেলানোসাইটিক নেভাই (বিনাইন)</li>"
                "<li><b>vasc</b> — ভাসকুলার ক্ষত (বিনাইন)</li>"
                "</ul>"
                "<p>এগুলো গবেষণামূলক লেবেল, চিকিৎসা-নির্ণয় নয়।</p>"
            ),
        },
    },
    {
        "id": "disclaimer",
        "question": {
            "en": "Is this a medical diagnosis?",
            "bn": "এটা কি চিকিৎসা-নির্ণয়?",
        },
        "answer": {
            "en": (
                "<p><b>No.</b> DermaCheckerBD is an experimental prototype and does "
                "<b>not</b> provide a medical diagnosis.</p>"
                "<p>If a lesion is <b>changing, bleeding, growing, or painful</b>, "
                "consult a qualified dermatologist promptly. Do not delay professional "
                "evaluation based on this tool's output.</p>"
            ),
            "bn": (
                "<p><b>না।</b> DermaCheckerBD একটি পরীক্ষামূলক প্রোটোটাইপ এবং এটি "
                "<b>চিকিৎসা-নির্ণয় দেয় না</b>।</p>"
                "<p>কোনো দাগ <b>বদলালে, রক্তপাত করলে, বড় হলে বা ব্যথা হলে</b>, দ্রুত "
                "যোগ্য চর্মরোগ বিশেষজ্ঞের পরামর্শ নিন। এই টুলের ফলাফলের ওপর নির্ভর "
                "করে পেশাদার পরীক্ষা পিছাবেন না।</p>"
            ),
        },
    },
    {
        "id": "find_doctor",
        "question": {
            "en": "How do I find a dermatologist nearby?",
            "bn": "কাছের চর্মরোগ বিশেষজ্ঞ কীভাবে খুঁজে পাব?",
        },
        "answer": {
            "en": (
                "<p>Open the <b>Nearby Doctors &amp; Hospitals</b> page from the top "
                "navigation. Enter your location (e.g. <i>Dhaka</i>) and pick a search "
                "radius. The page lists nearby dermatologists and hospitals using the "
                "Geoapify Places API.</p>"
                "<p>If the search returns <i>API not configured</i>, the site owner has "
                "not yet set the Geoapify key. The page still loads without errors.</p>"
            ),
            "bn": (
                "<p>উপরের নেভিগেশন থেকে <b>কাছের চিকিৎসক ও হাসপাতাল</b> পাতা খুলুন। "
                "অবস্থান লিখুন (যেমন <i>ঢাকা</i>) এবং অনুসন্ধান ব্যাসার্ধ বেছে নিন। "
                "Geoapify Places API ব্যবহার করে পাতাটি কাছের চর্মরোগ বিশেষজ্ঞ ও "
                "হাসপাতালের তালিকা দেখায়।</p>"
                "<p><i>API not configured</i> ফেরালে মালিক এখনো Geoapify কী সেট করেননি। "
                "পাতাটি তবুও সাধারণ আকারে খোলে।</p>"
            ),
        },
    },
    {
        "id": "signup",
        "question": {
            "en": "How do I sign up or log in?",
            "bn": "কীভাবে অ্যাকাউন্ট খুলব বা লগ-ইন করব?",
        },
        "answer": {
            "en": (
                "<p>Click <b>Sign up</b> in the top navigation. You only need a "
                "username and a password of at least 8 characters.</p>"
                "<p>After signing in you can: see your own <b>prediction history</b>, "
                "save and track lesions over time, download PDF reports, and ask the "
                "assistant about <b>your own dashboard</b>. Anonymous visitors get "
                "these predefined FAQs only.</p>"
            ),
            "bn": (
                "<p>উপরের নেভিগেশনে <b>সাইন আপ</b> ক্লিক করুন। শুধু একটি ইউজারনেম ও "
                "অন্তত ৮ অক্ষরের পাসওয়ার্ড লাগবে।</p>"
                "<p>সাইন ইন করলে আপনি পাবেন: নিজের <b>প্রেডিকশন হিস্ট্রি</b>, লেসন "
                "ট্র্যাকার, পিডিএফ রিপোর্ট, এবং <b>নিজের ড্যাশবোর্ড</b> সম্পর্কে "
                "সহকারীকে প্রশ্ন করার সুবিধা। অতিথি ব্যবহারকারীরা শুধু এই পূর্বনির্ধারিত "
                "FAQ-গুলো দেখতে পান।</p>"
            ),
        },
    },
]

# Map for O(1) lookup by id.
FAQS_BY_ID: Dict[str, Dict[str, object]] = {item["id"]: item for item in FAQS}


def list_faqs(language: str = "en") -> List[Dict[str, str]]:
    """Return a lightweight, JSON-serializable list of FAQ id + question.

    Used by the chatbot template/JS to render the FAQ quick-reply buttons.
    Only ``id`` and ``question`` are exposed here; the answer is returned
    only when a FAQ is actually selected (so we do not leak every answer
    into the page HTML for anonymous visitors).
    """
    lang = "bn" if language == "bn" else "en"
    return [
        {"id": str(item["id"]), "question": str(item["question"][lang])}
        for item in FAQS
    ]


def get_faq_answer(faq_id: str, language: str = "en") -> Optional[str]:
    """Return the canned answer for a FAQ id, or None if unknown."""
    lang = "bn" if language == "bn" else "en"
    item = FAQS_BY_ID.get(faq_id)
    if not item:
        return None
    return str(item["answer"][lang])


def find_faq_id_by_text(text: str, language: str = "en") -> Optional[str]:
    """Best-effort match a free-text question to one of the 7 FAQs.

    Anonymous users can still type a question instead of clicking a button.
    We do a normalized substring match against the FAQ question labels so a
    visitor typing "what is dermacheckerbd" is routed to the canned answer
    instead of being told to sign in. The match is intentionally conservative
    to avoid misrouting; when no FAQ matches, the view returns a guidance
    message (still NO Gemini call).
    """
    lang = "bn" if language == "bn" else "en"
    needle = (text or "").strip().lower()
    if not needle:
        return None
    # Exact-ish match against any FAQ question (en or bn) first.
    for item in FAQS:
        for lang_code in ("en", "bn"):
            q = str(item["question"][lang_code]).strip().lower()
            if q and (needle == q or needle == q.rstrip("?।!.")):
                return str(item["id"])
    # Substring match against the selected language question.
    for item in FAQS:
        q = str(item["question"][lang]).strip().lower().rstrip("?।!.")
        if q and q in needle:
            return str(item["id"])
    # Keyword fallback for very short typed queries.
    keyword_map = {
        "what_is": ("dermacheckerbd", "derma checker", "what is this", "এটা কী", "এটি কী"),
        "accuracy": ("accura", "confiden", "score", "reliab", "নির্ভুল", "আস্থা"),
        "photo_guide": ("upload", "photo", "image", "picture", "ছবি", "আপলোড"),
        "class_names": ("class", "mel", "nv", "bcc", "akiec", "vasc", "শ্রেণি", "ক্লাস"),
        "disclaimer": ("diagnos", "medical advice", "safe", "নির্ণয়", "চিকিৎসা"),
        "find_doctor": ("doctor", "dermatologist", "hospital", "nearby", "চিকিৎসক", "হাসপাতাল"),
        "signup": ("sign up", "signup", "login", "log in", "register", "অ্যাকাউন্ট", "লগ"),
    }
    for faq_id, keywords in keyword_map.items():
        if any(kw in needle for kw in keywords):
            return faq_id
    return None
