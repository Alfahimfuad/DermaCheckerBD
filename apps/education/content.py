"""Curated, medically-reviewed educational content for each HAM10000 class.

Every entry is grounded in publicly available dermatology references
(AAD, CDC, ISIC, dermatology textbooks). The text is intentionally
neutral and educational — it never says "you have X" based on a
prediction, only "here is what class X means and what to do in general".

Sources cited per entry; users are encouraged to verify with a
qualified dermatologist.
"""
from __future__ import annotations

# Each entry is a dict with:
# - code: HAM10000 class code
# - name: full medical name
# - short_name: layperson-friendly name (English)
# - bangla_name: Bangla name (rendered in Bengali script)
# - category: 'benign' | 'malignant' | 'pre malignant'
# - overview: 1-paragraph plain-English explanation
# - appearance: typical visual characteristics
# - symptoms: common symptoms / warning signs
# - care: skin care and sun protection guidance
# - when_to_see_doctor: specific situations requiring professional review
# - references: list of (label, url) tuples
# - bangla_summary: short Bangla summary for the assistant / i18n

EDUCATION_CONTENT = {
    "nv": {
        "code": "nv",
        "name": "Melanocytic nevus",
        "short_name": "Melanocytic nevus (common mole)",
        "bangla_name": "মেলানোসাইটিক নেভাস (সাধারণ তিল)",
        "category": "benign",
        "overview": (
            "A melanocytic nevus, commonly called a mole, is a benign "
            "growth of pigment-producing cells (melanocytes). Most adults "
            "have 10–40 moles by adulthood. They may be present at birth "
            "or appear later in life, especially during childhood and "
            "adolescence. The vast majority remain harmless throughout "
            "life. A mole is not cancer — but a small subset can transform "
            "into melanoma over time, so any changing mole warrants "
            "professional evaluation."
        ),
        "appearance": (
            "Typically a small (under 6 mm) round or oval spot with a "
            "smooth, well-defined border. Colours range from flesh-toned "
            "to pink, tan, brown, or black. The surface may be flat or "
            "raised, smooth or slightly pebbled. Most are uniform in colour "
            "and symmetric."
        ),
        "symptoms": (
            "Usually asymptomatic. A stable mole does not itch, bleed, "
            "or hurt. Warning signs that should prompt review: rapid "
            "growth, colour change, irregular border, itching, bleeding, "
            "or pain. The ABCDE rule (Asymmetry, Border, Colour, Diameter, "
            "Evolving) helps decide when a mole deserves evaluation."
        ),
        "care": (
            "No treatment is needed for stable, benign-appearing moles. "
            "Sun protection is the single most useful daily habit: "
            "broad-spectrum SPF 30+ sunscreen, re-applied every 2 hours "
            "outdoors, protective clothing, and avoiding peak UV hours "
            "(10 AM–4 PM). Do not pick or scratch moles. Track changes "
            "with monthly self-examination using a mirror or partner."
        ),
        "when_to_see_doctor": (
            "See a dermatologist if a mole changes in size, shape, colour, "
            "or elevation; becomes itchy, tender, or bleeds; or looks "
            "visually different from your other moles (the 'ugly duckling' "
            "sign). Anyone with more than 50 moles, a personal or family "
            "history of melanoma, or fair skin with frequent sunburns "
            "should have a baseline professional skin check."
        ),
        "references": [
            ("American Academy of Dermatology — Moles", "https://www.aad.org/public/everyday-care/injured-skin/treat-burns-and-cuts/moles"),
            ("CDC — Skin Cancer Basics", "https://www.cdc.gov/cancer/skin/basic_info/"),
            ("ISIC Archive — HAM10000 dataset", "https://doi.org/10.1038/sdata2018.161"),
        ],
        "bangla_overview": (
                "মেলানোসাইটিক নেভাস বা সাধারণ তিল মেলানোসাইট কোষের একটি নিরীহ বৃদ্ধি। "
                "বেশিরভাগ প্রাপ্তবয়স্কদের শরীরে ১০–৪০টি তিল থাকে। সাধারণত জন্ম থেকে বা "
                "শৈশব-কৈশোরে দেখা যায় এবং সারাজীবন নিরীহ থাকে। অল্প কিছু তিল সময়ের "
                "সাথে মেলানোমায় রূপ নিতে পারে, তাই পরিবর্তনশীল তিল দেখালে বিশেষজ্ঞের "
                "পরামর্শ নিন।"
        ),
        "bangla_appearance": (
                "সাধারণত ৬ মিমির ছোট, গোল বা ডিম্বাকৃতি দাগ। সীমানা সুস্পষ্ট ও মসৃণ। রঙ "
                "গোঁৎ-টোন, গোলাপি, বাদামি বা কালো হতে পারে। সমতল বা সামান্য উঁচু, পৃষ্ঠ "
                "মসৃণ বা সামান্য খসখসে। সাধারণত একরঙা ও প্রতিসম।"
        ),
        "bangla_symptoms": (
                "সাধারণত কোনো লক্ষণ থাকে না। স্থিতিশীল তিলে চুলকানি, রক্তপাত বা ব্যথা "
                "হয় না। সতর্ক চিহ্ন: দ্রুত বৃদ্ধি, রঙ পরিবর্তন, অনিয়মিত সীমানা, "
                "চুলকানি, রক্তপাত বা ব্যথা। ABCDE নিয়ম (প্রতিসার্যতা, সীমানা, রঙ, "
                "ব্যাস, পরিবর্তনশীলতা) ব্যবহার করে মূল্যায়ন করুন।"
        ),
        "bangla_care": (
                "স্থিতিশীল নিরীহ তিলের জন্য কোনো চিকিৎসা প্রয়োজন নেই। সূর্য সুরক্ষাই "
                "সবচেয়ে গুরুত্বপূর্ণ অভ্যাস—ব্রড-স্পেকট্রাম SPF 30+ সানস্ক্রিন প্রতি ২ "
                "ঘণ্টায় মাখুন, সুরক্ষামূলক পোশাক পরুন, দুপুর ১০টা–বিকেল ৪টা পর্যন্ত "
                "রোদ এড়িয়ে চলুন। তিল আঁচড়াবেন না বা ছিলবেন না। মাসিক স্ব-পরীক্ষায় "
                "পরিবর্তন লক্ষ্য রাখুন।"
        ),
        "bangla_when_to_see_doctor": (
                "তিলের আকার, আকৃতি, রঙ বা উচ্চতা পরিবর্তন হলে; চুলকানি, ব্যথা বা "
                "রক্তপাত হলে; অথবা অন্যান্য তিল থেকে দৃশ্যত আলাদা মনে হলে ('ugly "
                "duckling' লক্ষণ) চর্ম বিশেষজ্ঞ দেখান। যাদের তিল ৫০+ আছে, পরিবারে "
                "মেলানোমার ইতিহাস আছে, বা প্রায়ই রোদে পোড়েন তাদের বেসলাইন পরীক্ষা "
                "করানো উচিত।"
        ),

        "bangla_summary": (
            "মেলানোসাইটিক নেভাস বা সাধারণ তিল একটি নিরীহ চর্ম বিবর্তন। "
            "বেশিরভাগ মানুষেরই শরীরে একাধিক তিল থাকে এবং সারাজীবন ক্ষতি করে না। "
            "তবে তিলের আকার, রঙ, সীমানা পরিবর্তন হলে বা রক্তপাত হলে দ্রুত "
            "চর্ম বিশেষজ্ঞকে দেখানো উচিত।"
        ),
    },

    "mel": {
        "code": "mel",
        "name": "Melanoma",
        "short_name": "Melanoma",
        "bangla_name": "মেলানোমা (গুরুতর ত্বকের ক্যান্সার)",
        "category": "malignant",
        "overview": (
            "Melanoma is a serious cancer of melanocytes, the pigment-"
            "producing cells of the skin. It is the most dangerous form "
            "of skin cancer because it can spread (metastasize) to lymph "
            "nodes and other organs if not treated early. With early "
            "detection and surgical removal, the 5-year survival rate "
            "is very high; once it has spread, outcomes worsen "
            "significantly. UV exposure and genetic factors are the main "
            "risk factors."
        ),
        "appearance": (
            "Often an irregularly shaped, multi-coloured patch — brown, "
            "black, blue, red, or white. The border is usually notched "
            "or blurred. Size is often over 6 mm (about the diameter of "
            "a pencil eraser). The ABCDE rule is the standard screening "
            "tool: Asymmetry, Border irregularity, Colour variation, "
            "Diameter > 6 mm, Evolving over time."
        ),
        "symptoms": (
            "Warning signs: a new dark spot that grows; an existing mole "
            "that changes in size, shape, colour, or elevation; a spot "
            "that itches, bleeds, or hurts; a sore that does not heal; "
            "pigment spreading beyond the border into surrounding skin. "
            "The 'ugly duckling' sign — a mole that looks different from "
            "all your others — is also a red flag."
        ),
        "care": (
            "Melanoma requires professional medical treatment, not self-"
            "care alone. Until you see a dermatologist: do not scratch, "
            "pick, or attempt home removal; protect the area from sun; "
            "do not apply unprescribed creams or remedies. Sun protection "
            "(SPF 30+, protective clothing, avoiding peak UV) reduces the "
            "risk of new melanomas."
        ),
        "when_to_see_doctor": (
            "URGENTLY. If you suspect melanoma — especially a changing, "
            "bleeding, or rapidly growing pigmented lesion — see a "
            "dermatologist within days, not weeks. Bring a list of when "
            "the change started and any photos from earlier. Do not wait "
            "for the prediction of any AI tool to confirm or deny the "
            "concern; an in-person exam and biopsy are required."
        ),
        "references": [
            ("American Academy of Dermatology — Melanoma", "https://www.aad.org/public/diseases/skin-cancer/types/common/melanoma"),
            ("CDC — Skin Cancer", "https://www.cdc.gov/cancer/skin/"),
            ("Skin Cancer Foundation — Melanoma", "https://www.skincancer.org/skin-cancer-information/melanoma/"),
            ("ISIC Archive — HAM10000 dataset", "https://doi.org/10.1038/sdata2018.161"),
        ],
        "bangla_overview": (
                "মেলানোমা মেলানোসাইট কোষের একটি গুরুতর ক্যানসার। এটি ত্বকের ক্যানসারের "
                "সবচেয়ে বিপজ্জনক রূপ—কারণ শীঘ্র চিকিৎসা না হলে লিম্ফ নোড ও অন্যান্য "
                "অঙ্গে ছড়িয়ে পড়তে পারে। প্রাথমিক অবস্থায় শনাক্ত করে অস্ত্রোপচারের "
                "মাধ্যমে অপসারণ করলে ৫-বছরের বেঁচে থাকার হার অনেক বেশি। অতিরিক্ত রোদ ও "
                "জেনেটিক কারণ প্রধান ঝুঁকি।"
        ),
        "bangla_appearance": (
                "প্রায়শই একটি অনিয়মিত আকৃতির, বহুরঙা দাগ—বাদামি, কালো, নীল, লাল বা "
                "সাদা। সীমানা সাধারণত খাঁজকাটা বা ঝাপসা। ব্যাস সাধারণত ৬ মিমির বেশি। "
                "ABCDE নিয়ম: প্রতিসার্যতা, সীমানা অনিয়মিত, রঙের বৈচিত্র্য, ব্যাস > ৬ "
                "মিমি, এবং পরিবর্তনশীলতা।"
        ),
        "bangla_symptoms": (
                "সতর্ক চিহ্ন: নতুন কালো দাগ যা বড় হচ্ছে; পুরোনো তিলের আকার, আকৃতি, রঙ "
                "বা উচ্চতা পরিবর্তন; চুলকানি, রক্তপাত বা ব্যথা; এমন ঘা যা শুকায় না; "
                "সীমানার বাইরে রঙ ছড়ানো। 'Ugly duckling' লক্ষণ—অন্যান্য তিল থেকে "
                "দৃশ্যত আলাদা—ও একটি সতর্ক চিহ্ন।"
        ),
        "bangla_care": (
                "মেলানোমার চিকিৎসা পেশাদার মূল্যায়ন ছাড়া সম্ভব নয়। চিকিৎসক দেখানোর "
                "আগে: আঁচড়াবেন না, কাটবেন না, ঘরোয়া অপসারণ চেষ্টা করবেন না; অংশটি রোদ "
                "থেকে সুরক্ষিত রাখুন; অনির্ধারিত ক্রিম বা ওষুধ মাখবেন না। সূর্য সুরক্ষা "
                "নতুন মেলানোমার ঝুঁকি কমায়।"
        ),
        "bangla_when_to_see_doctor": (
                "জরুরি। মেলানোমা সন্দেহ হলে—বিশেষত পরিবর্তনশীল, রক্তপাতকারী বা দ্রুত "
                "বর্ধনশীল দাগ—কয়েক সপ্তাহ নয়, কয়েক দিনের মধ্যে চর্ম বিশেষজ্ঞ দেখান। "
                "পরিবর্তন শুরুর সময় ও পুরোনো ছবি সাথে আনুন। যেকোনো AI টুলের "
                "প্রেডিকশনের জন্য অপেক্ষা করবেন না; সরাসরি পরীক্ষা ও বায়োপসি প্রয়োজন।"
        ),

        "bangla_summary": (
            "মেলানোমা ত্বকের একটি গুরুতর ক্যান্সার। দ্রুত শনাক্ত করে অপসারণ "
            "করলে সুস্থ হওয়ার সম্ভাবনা অনেক বেশি। ত্বকের দাগের আকার, রঙ বা "
            "সীমানা পরিবর্তন, রক্তপাত, বা দ্রুত বৃদ্ধি হলে অবিলম্বে চর্ম "
            "বিশেষজ্ঞের শরণাপন্ন হোন।"
        ),
    },

    "bkl": {
        "code": "bkl",
        "name": "Benign keratosis-like lesions",
        "short_name": "Benign keratosis-like lesions",
        "bangla_name": "বিনাইন কেরাটোসিস (নিরীহ ত্বকের দাগ)",
        "category": "benign",
        "overview": (
            "This class groups together benign growths that include "
            "solar lentigines ('sun spots' or 'liver spots') and "
            "seborrheic keratoses ('barnacles of aging'). Both are "
            "extremely common in middle-aged and older adults. They are "
            "not cancer and do not turn into cancer, although they can "
            "sometimes resemble melanoma clinically — which is why a "
            "dermatologist's examination matters when there is doubt."
        ),
        "appearance": (
            "Solar lentigines are flat, light to dark brown patches on "
            "sun-exposed skin (face, hands, shoulders). Seborrheic "
            "keratoses are raised, waxy, 'stuck-on' appearing growths "
            "with colours ranging from tan to dark brown. They may look "
            "pasted onto the skin surface."
        ),
        "symptoms": (
            "Generally asymptomatic. Seborrheic keratoses may itch "
            "occasionally or catch on clothing. They do not bleed on "
            "their own. Any bleeding, rapid growth, or colour change "
            "should prompt evaluation because they can mimic melanoma."
        ),
        "care": (
            "No treatment is medically required. Cosmetic removal "
            "(cryotherapy, curettage, laser) is an option if the lesion "
            "is cosmetically bothersome or chronically irritated. Sun "
            "protection helps prevent new solar lentigines."
        ),
        "when_to_see_doctor": (
            "See a dermatologist if a lesion changes rapidly, bleeds, "
            "is painful, or if you are uncertain whether it is benign — "
            "pigmented lesions can be hard to distinguish clinically, "
            "and a dermoscopy exam or biopsy may be needed."
        ),
        "references": [
            ("American Academy of Dermatology — Seborrheic keratoses", "https://www.aad.org/public/diseases/a-z/seborrheic-keratoses-overview"),
            ("Mayo Clinic — Age spots (liver spots)", "https://www.mayoclinic.org/diseases-conditions/age-spots/symptoms-causes/syc-20355601"),
            ("ISIC Archive — HAM10000 dataset", "https://doi.org/10.1038/sdata2018.161"),
        ],
        "bangla_overview": (
                "এই শ্রেণিতে নিরীহ বৃদ্ধি অন্তর্ভুক্ত—সোলার লেন্টিজিন ('সান স্পট' বা "
                "'লিভার স্পট') এবং সেবোরিক কেরাটোসিস ('বার্নেকল অফ এজিং')। উভয়ই "
                "মধ্যবয়স্ক ও বয়স্কদের মধ্যে খুবই সাধারণ। এগুলো ক্যানসার নয় এবং "
                "ক্যানসারে রূপ নেয় না—তবে মেলানোমার মতো দেখাতে পারে, তাই সন্দেহ হলে "
                "চর্ম বিশেষজ্ঞের পরীক্ষা জরুরি।"
        ),
        "bangla_appearance": (
                "সোলার লেন্টিজিন সমতল, হালকা থেকে গাঢ় বাদামি দাগ—রোদে পোড়া অংশে (মুখ, "
                "হাত, কাঁধ)। সেবোরিক কেরাটোসিস উঁচু, মোমের মতো, 'স্টাক-অন' চেহারার "
                "বৃদ্ধি—তন থেকে গাঢ় বাদামি রঙের। ত্বকের উপর সাঁটানো মনে হতে পারে।"
        ),
        "bangla_symptoms": (
                "সাধারণত লক্ষণহীন। সেবোরিক কেরাটোসিস মাঝে মাঝে চুলকাতে পারে বা পোশাকে "
                "আটকে যেতে পারে। নিজে থেকে রক্তপাত হয় না। রক্তপাত, দ্রুত বৃদ্ধি বা রঙ "
                "পরিবর্তন হলে মেলানোমার অনুকরণ করতে পারে বলে মূল্যায়ন প্রয়োজন।"
        ),
        "bangla_care": (
                "চিকিৎসাগতভাবে কোনো চিকিৎসা আবশ্যক নয়। প্রসাধনগত কারণে বা দীর্ঘস্থায়ী "
                "উত্তেজনার জন্য ক্রায়োথেরাপি, কিউরেটেজ বা লেজার অপসারণ বিকল্প। সূর্য "
                "সুরক্ষা নতুন সোলার লেন্টিজিন প্রতিরোধ করে।"
        ),
        "bangla_when_to_see_doctor": (
                "দাগ দ্রুত পরিবর্তিত হলে, রক্তপাত হলে, ব্যথা হলে, অথবা নিরীহ কিনা "
                "নিশ্চিত না হলে চর্ম বিশেষজ্ঞ দেখান—রঞ্জক ক্ষত ক্লিনিক্যালি আলাদা করা "
                "কঠিন, ডার্মোস্কোপি বা বায়োপসি প্রয়োজন হতে পারে।"
        ),

        "bangla_summary": (
            "বিনাইন কেরাটোসিস বা সূর্যের দাগ সাধারণত বয়স্কদের ত্বকে দেখা যায় "
            "এবং নিরীহ। ক্যান্সারে পরিণত হয় না। দাগে পরিবর্তন বা রক্তপাত "
            "হলে চিকিৎসকের পরামর্শ নিন।"
        ),
    },

    "bcc": {
        "code": "bcc",
        "name": "Basal cell carcinoma",
        "short_name": "Basal cell carcinoma",
        "bangla_name": "বেসাল সেল কার্সিনোমা (ত্বকের সাধারণ ক্যান্সার)",
        "category": "malignant",
        "overview": (
            "Basal cell carcinoma (BCC) is the most common form of skin "
            "cancer. It grows slowly and rarely metastasizes, but it can "
            "cause significant local tissue destruction if neglected. "
            "BCC is strongly linked to cumulative UV exposure, so it "
            "most often appears on sun-exposed areas: face, ears, neck, "
            "scalp, shoulders, and back. Early treatment is highly "
            "effective."
        ),
        "appearance": (
            "Often a pearly or waxy bump, a flat flesh-coloured or "
            "brown scar-like lesion, or a pinkish patch with visible "
            "blood vessels. It may bleed, scab, and heal cyclically — "
            "the 'bleeding-then-healing' lesion is a classic sign."
        ),
        "symptoms": (
            "An open sore that bleeds, oozes, or crusts and persists "
            "for weeks; a reddish irritated patch that may itch or hurt; "
            "a shiny bump that is translucent or pearly; a pink growth "
            "with a rolled border and central indentation; a scar-like "
            "area that is white, yellow, or waxy with poorly defined "
            "borders."
        ),
        "care": (
            "BCC requires professional treatment — surgical excision, "
            "Mohs micrographic surgery, curettage, or topical "
            "chemotherapy depending on type and location. Until you see "
            "a dermatologist: keep the area clean, do not pick at it, "
            "and protect it from further sun. Sunscreen and protective "
            "clothing reduce the risk of new BCCs."
        ),
        "when_to_see_doctor": (
            "Schedule a dermatology appointment within a few weeks. "
            "Although BCC grows slowly, early treatment minimises "
            "scarring and tissue loss. If the lesion is bleeding "
            "uncontrollably, on the face near the eye or ear, or grows "
            "rapidly, seek care sooner."
        ),
        "references": [
            ("American Academy of Dermatology — BCC", "https://www.aad.org/public/diseases/skin-cancer/types/common/bcc"),
            ("Skin Cancer Foundation — BCC", "https://www.skincancer.org/skin-cancer-information/basal-cell-carcinoma/"),
            ("ISIC Archive — HAM10000 dataset", "https://doi.org/10.1038/sdata2018.161"),
        ],
        "bangla_overview": (
                "বেসাল সেল কার্সিনোমা (BCC) ত্বকের সবচেয়ে সাধারণ ক্যানসার। এটি ধীরে "
                "বাড়ে এবং খুব কমই ছড়ায়, তবে অবহেলা করলে স্থানীয় ক্ষতিস্থান বড় হতে "
                "পারে। দীর্ঘস্থায়ী সূর্যালোক-প্রকাশিত ত্বকে বেশি দেখা যায়—মুখ, কান, "
                "ঘাড়, স্কাল্প, হাত। শীঘ্র চিকিৎসা করলে প্রায় সবসময়ই সম্পূর্ণ সুস্থতা "
                "আসে।"
        ),
        "bangla_appearance": (
                "প্রায়শই একটি ছোট, উঁচু, চকচকে বা মুক্তার মতো দাগ, যার কেন্দ্রে একটি "
                "ক্ষুদ্র ফোঁড়া বা ঘা থাকতে পারে। মাঝে মাঝে রক্তপাত হয় এবং সহজে শুকায় "
                "না। রঙ গোঁৎ-টোন, গোলাপি বা বাদামি। সীমানায় দৃশ্যমান রক্তনালী "
                "(telangiectasia) থাকতে পারে।"
        ),
        "bangla_symptoms": (
                "সাধারণত ব্যথা হয় না। লক্ষণ: ধীরে বড় হওয়া দাগ, বারবার রক্তপাত, ঘা যা "
                "শুকায় না, মাঝে মাঝে চুলকানি। খোলস তৈরি হতে পারে। চোখ, নাক বা কানের "
                "কাছে হলে ঝুঁকি বেশি।"
        ),
        "bangla_care": (
                "BCC-র নিশ্চিত চিকিৎসা পেশাদার অপসারণ। চিকিৎসক দেখানোর আগে: আঁচড়াবেন "
                "না, ঘা খুলবেন না, অনির্ধারিত ক্রিম মাখবেন না। রোদ থেকে অংশটি সুরক্ষিত "
                "রাখুন। নির্ধারিত অপসারণ চিকিৎসায় হাসপাতালে যান।"
        ),
        "bangla_when_to_see_doctor": (
                "সাধারণত কয়েক সপ্তাহের মধ্যে চর্ম বিশেষজ্ঞের সাথে অ্যাপয়েন্টমেন্ট "
                "নিন। দাগ দ্রুত বড় হলে, রক্তপাত এড়িয়ে যাচ্ছে না চাইলে, চোখ, নাক বা "
                "ঠোঁটের কাছে হলে—দ্রুত দেখান।"
        ),

        "bangla_summary": (
            "বেসাল সেল কার্সিনোমা ত্বকের সবচেয়ে সাধারণ ক্যান্সার। ধীরে বাড়ে, "
            "খুব কমই ছড়ায়, কিন্তু অবহেলা করলে স্থানীয় ক্ষতি করতে পারে। "
            "রৌদ্রজনিত অংশে বেশি দেখা যায়। চিকিৎসকের পরামর্শে দ্রুত "
            "চিকিৎসা নিন।"
        ),
    },

    "akiec": {
        "code": "akiec",
        "name": "Actinic keratoses and intraepidermal carcinoma",
        "short_name": "Actinic keratosis / Bowen disease",
        "bangla_name": "অ্যাকটিনিক কেরাটোসিস (প্রি-ক্যান্সার)",
        "category": "pre malignant",
        "overview": (
            "Actinic keratoses (AKs) are pre-cancerous lesions caused by "
            "long-term UV exposure. They are not cancer yet, but a small "
            "percentage progress to squamous cell carcinoma if left "
            "untreated. They appear on sun-exposed areas — face, lips, "
            "ears, scalp, back of hands, forearms. Treatment reduces the "
            "risk of progression."
        ),
        "appearance": (
            "Rough, scaly, slightly raised patches that feel like "
            "sandpaper. Colours range from skin-toned to pink, red, or "
            "brown. They are often easier to feel than to see. Size "
            "ranges from a few millimetres to over a centimetre."
        ),
        "symptoms": (
            "Rough texture, mild itching, tenderness, or a prickling "
            "sensation, especially when touched. Lips may become dry, "
            "cracked, and pale (actinic cheilitis). Bleeding is uncommon "
            "without trauma. New lesions may continue to appear over "
            "years on chronically sun-damaged skin."
        ),
        "care": (
            "AKs warrant treatment to prevent progression. Options "
            "include cryotherapy, topical 5-fluorouracil or imiquimod, "
            "photodynamic therapy, and chemical peels — chosen by a "
            "dermatologist based on number, location, and thickness. "
            "Sun protection is critical to prevent new lesions."
        ),
        "when_to_see_doctor": (
            "Schedule a dermatology appointment within weeks. See a "
            "doctor sooner if a lesion becomes thick, tender, bleeds, "
            "or grows rapidly — these are signs of possible progression "
            "to squamous cell carcinoma."
        ),
        "references": [
            ("American Academy of Dermatology — Actinic keratosis", "https://www.aad.org/public/diseases/a-z/actinic-keratoses-overview"),
            ("Skin Cancer Foundation — AK", "https://www.skincancer.org/skin-cancer-information/actinic-keratosis/"),
            ("ISIC Archive — HAM10000 dataset", "https://doi.org/10.1038/sdata2018.161"),
        ],
        "bangla_overview": (
                "অ্যাকটিনিক কেরাটোসিস (AKs) দীর্ঘস্থায়ী রোদে পোড়ার ফলে সৃষ্ট "
                "প্রি-ক্যানসারাস দাগ। এগুলো এখনও ক্যানসার নয়, তবে চিকিৎসা না করালে "
                "অল্প শতাংশ স্কোয়ামাস সেল কার্সিনোমায় রূপ নিতে পারে। রোদে পোড়া অংশে "
                "দেখা যায়—মুখ, ঠোঁট, কান, স্কাল্প, হাতের পিছন, অগ্রবাহু।"
        ),
        "bangla_appearance": (
                "অমসৃণ, খসখসে, সামান্য উঁচু দাগ—বালির কাগজের মতো অনুভূত হয়। রঙ "
                "গোঁৎ-টোন থেকে গোলাপি, লাল বা বাদামি। দেখার চেয়ে স্পর্শ করে বোঝা সহজ। "
                "আকার কয়েক মিমি থেকে ১ সেমির বেশি হতে পারে।"
        ),
        "bangla_symptoms": (
                "অমসৃণ অনুভূতি, হালকা চুলকানি, কোমলতা বা শিহরণ—বিশেষত স্পর্শ করলে। ঠোঁট "
                "শুষ্ক, ফাটা ও ফ্যাকাশে হতে পারে (অ্যাকটিনিক কেইলাইটিস)। আঘাত ছাড়া "
                "রক্তপাত সাধারণ নয়। নতুন দাগ বছরের পর বছর যুক্ত হতে পারে।"
        ),
        "bangla_care": (
                "AKs-র চিকিৎসা প্রয়োজন—ক্রায়োথেরাপি, টপিক্যাল ৫-ফ্লোরোইউরাসিল বা "
                "ইমিকুইমড, ফটোডায়নামিক থেরাপি বা কেমিক্যাল পিল। চিকিৎসক সংখ্যা, "
                "অবস্থান ও পুরুত্ব অনুযায়ী পদ্ধতি বেছে নেন। নতুন দাগ প্রতিরোণে সূর্য "
                "সুরক্ষা জরুরি।"
        ),
        "bangla_when_to_see_doctor": (
                "কয়েক সপ্তাহের মধ্যে চর্ম বিশেষজ্ঞের অ্যাপয়েন্টমেন্ট নিন। দাগ পুরু "
                "হলে, কোমল হলে, রক্তপাত হলে বা দ্রুত বড় হলে—এগুলো স্কোয়ামাস সেল "
                "কার্সিনোমায় রূপান্তরের লক্ষণ—শীঘ্রই চিকিৎসক দেখান।"
        ),

        "bangla_summary": (
            "অ্যাকটিনিক কেরাটোসিস প্রি-ক্যান্সার অবস্থা। সঠিক চিকিৎসা না "
            "করালে কিছু ক্ষেত্রে স্কোয়ামাস সেল কার্সিনোমায় রূপ নিতে পারে। "
            "রৌদ্রজনিত ত্বকে এলে চর্ম বিশেষজ্ঞের পরামর্শ নিন।"
        ),
    },

    "vasc": {
        "code": "vasc",
        "name": "Vascular lesions",
        "short_name": "Vascular lesions",
        "bangla_name": "ভাসকুলার লেসন (রক্তবাহী দাগ)",
        "category": "benign",
        "overview": (
            "Vascular lesions include cherry angiomas, angiokeratomas, "
            "and other benign growths of blood vessels. They are very "
            "common, usually appear in adulthood, and are harmless. "
            "They can bleed if traumatised. They are not cancerous."
        ),
        "appearance": (
            "Bright red to deep purple smooth, raised papules, usually "
            "small (1–5 mm). Cherry angiomas are the most common — "
            "small, bright-red dots typically on the trunk."
        ),
        "symptoms": (
            "Usually asymptomatic. They may bleed if scratched or "
            "traumatised because they are vascular. They do not usually "
            "itch or hurt. New ones can appear with age."
        ),
        "care": (
            "No treatment is medically required. Cosmetic removal "
            "(laser, electrocautery) is an option if desired. Avoid "
            "scratching or picking to prevent bleeding."
        ),
        "when_to_see_doctor": (
            "See a doctor if a vascular lesion bleeds persistently, "
            "grows rapidly, changes colour, or is painful — these signs "
            "are unusual and warrant evaluation."
        ),
        "references": [
            ("American Osteopathic College of Dermatology — Cherry angioma", "https://www.aocd.org/page/CherryAngioma"),
            ("Cleveland Clinic — Hemangioma", "https://my.clevelandclinic.org/health/diseases/21755-hemangioma"),
            ("ISIC Archive — HAM10000 dataset", "https://doi.org/10.1038/sdata2018.161"),
        ],
        "bangla_overview": (
                "ভাসকুলার লেসনে চেরি অ্যাঞ্জিওমা, অ্যাঞ্জিওকেরাটোমা ও রক্তনালীর "
                "অন্যান্য নিরীহ বৃদ্ধি অন্তর্ভুক্ত। এগুলো রক্তনালী থেকে উৎপন্ন এবং "
                "সাধারণত নিরীহ। চেরি অ্যাঞ্জিওমা প্রায়শই ৩০ বছরের পরে দেখা দেয় এবং "
                "বয়সের সাথে সংখ্যা বাড়ে।"
        ),
        "bangla_appearance": (
                "চেরি অ্যাঞ্জিওমা ছোট, উঁচু, উজ্জ্বল লাল থেকে বেগুনি দাগ। "
                "অ্যাঞ্জিওকেরাটোমা গাঢ় লাল-বেগুনি, সামান্য উঁচু, কখনো খসখসে পৃষ্ঠের "
                "দাগ। সাধারণত কাণ্ডে বা কাণ্ড-প্রদেশে দেখা যায়।"
        ),
        "bangla_symptoms": (
                "সাধারণত লক্ষণহীন। চেরি অ্যাঞ্জিওমা মাঝে মাঝে আঘাত পেলে রক্তপাত করতে "
                "পারে। অ্যাঞ্জিওকেরাটোমা কখনো চুলকায় বা রক্তপাত করে। দ্রুত বৃদ্ধি বা "
                "রঙ পরিবর্তন হলে মূল্যায়ন জরুরি।"
        ),
        "bangla_care": (
                "চিকিৎসাগতভাবে চিকিৎসা আবশ্যক নয়। প্রসাধনগত কারণে লেজার, ক্রায়োথেরাপি "
                "বা ইলেকট্রোক্যাটেরির মাধ্যমে অপসারণ সম্ভব। রক্তপাত হলে পরিষ্কার করে "
                "চাপ দিন এবং পুনরায় রক্তপাত হলে চিকিৎসক দেখান।"
        ),
        "bangla_when_to_see_doctor": (
                "দাগ দ্রুত পরিবর্তিত হলে, রঙ বা আকৃতি পরিবর্তন হলে, বারবার রক্তপাত হলে "
                "বা নিরীহ কিনা নিশ্চিত না হলে চর্ম বিশেষজ্ঞ দেখান। বাচ্চাদের বড় বা "
                "পরিবর্তনশীল ভাসকুলার দাগ দ্রুত মূল্যায়ন করানো উচিত।"
        ),

        "bangla_summary": (
            "ভাসকুলার লেসন সাধারণত নিরীহ রক্তবাহী দাগ। ক্যান্সার নয়। তবে "
            "দাগে অতিরিক্ত পরিবর্তন বা রক্তপাত হলে চিকিৎসকের পরামর্শ নিন।"
        ),
    },

    "df": {
        "code": "df",
        "name": "Dermatofibroma",
        "short_name": "Dermatofibroma",
        "bangla_name": "ডার্মাটোফাইব্রোমা (নিরীহ ত্বকের নোডিউল)",
        "category": "benign",
        "overview": (
            "A dermatofibroma is a common benign fibrous nodule usually "
            "found on the legs. It is thought to be a reactive process "
            "to minor trauma (insect bite, folliculitis). It is not "
            "cancer. Most remain stable for years and require no "
            "treatment."
        ),
        "appearance": (
            "A firm, raised papule 3–10 mm in diameter, pink to dark "
            "brown in colour. It dimples inward when pinched (the "
            "'dimple sign' or Fitzpatrick sign) — a useful bedside "
            "diagnostic clue. The surface may be smooth or slightly "
            "scaly."
        ),
        "symptoms": (
            "Usually asymptomatic. May itch or be tender. It does not "
            "bleed unless traumatised. Stable in size over years."
        ),
        "care": (
            "No treatment needed. Surgical excision is reserved for "
            "lesions that are symptomatic, growing, or cosmetically "
            "troubling — recurrence is possible."
        ),
        "when_to_see_doctor": (
            "See a dermatologist if the nodule grows rapidly, changes "
            "colour, bleeds, or becomes painful — these are atypical "
            "features that warrant evaluation."
        ),
        "references": [
            ("American Osteopathic College of Dermatology — Dermatofibroma", "https://www.aocd.org/page/Dermatofibroma"),
            ("Mayo Clinic — Dermatofibroma", "https://www.mayoclinic.org/diseases-conditions/dermatofibroma/symptoms-causes/syc-20371419"),
            ("ISIC Archive — HAM10000 dataset", "https://doi.org/10.1038/sdata2018.161"),
        ],
        "bangla_overview": (
                "ডার্মাটোফাইব্রোমা সাধারণত পায়ে দেখা যায় এমন একটি নিরীহ ফাইব্রাস "
                "নোডিউল। এটি ক্যানসার নয়। সাধারণত স্থিতিশীল থাকে এবং সারাজীবন স্থায়ী "
                "হয়। কিছু ক্ষেত্রে পূর্ববর্তী আঘাত (যেমন মশা কামড় বা ছোট আঁচড়) "
                "সেখানে ডার্মাটোফাইব্রোমা গঠিত হয়।"
        ),
        "bangla_appearance": (
                "সাধারণত একটি শক্ত, উঁচু দাগ—ব্যাস ৩–১০ মিমি। রঙ গোঁৎ-টোন থেকে গোলাপি, "
                "বাদামি বা লালচে-বাদামি। পার্শ্ববর্তী ত্বকের চেয়ে গাঢ় হতে পারে। "
                "প্রায়শই কেন্দ্রে একটি ছোট হালকা বিন্দু থাকে। পাশ থেকে চিমটে ধরলে "
                "'ডিম্পল সাইন' দেখা যায়—এটি একটি নির্ণায়ক লক্ষণ।"
        ),
        "bangla_symptoms": (
                "সাধারণত লক্ষণহীন। মাঝে মাঝে চুলকানি বা কোমলতা হতে পারে। রক্তপাত সাধারণ "
                "নয়। যদি দ্রুত বৃদ্ধি, রঙ পরিবর্তন বা আক্রমণাত্মক আচরণ দেখা যায় তবে "
                "অন্য রোগ নিয়ে ভাবতে হবে।"
        ),
        "bangla_care": (
                "চিকিৎসাগতভাবে চিকিৎসা আবশ্যক নয়। স্থায়ী এবং স্থিতিশীল। প্রসাধনগত "
                "কারণে বা দীর্ঘস্থায়ী উত্তেজনার জন্য অস্ত্রোপচার অপসারণ বিকল্প, তবে "
                "দাগ অপসারণের জায়গায় নতুন দাগ থাকতে পারে।"
        ),
        "bangla_when_to_see_doctor": (
                "দাগ দ্রুত বড় হলে, রঙ পরিবর্তন হলে, ব্যথা হলে বা নিরীহ কিনা নিশ্চিত না "
                "হলে চর্ম বিশেষজ্ঞ দেখান। ডার্মাটোফাইব্রোমা মেলানোমা বা অন্য ত্বকের "
                "ক্যানসারের অনুকরণ করতে পারে, তাই সন্দেহ হলে ডার্মোস্কোপি বা বায়োপসি "
                "প্রয়োজন।"
        ),

        "bangla_summary": (
            "ডার্মাটোফাইব্রোমা সাধারণত পায়ে দেখা যায় এমন একটি নিরীহ "
            "নোডিউল। ক্যান্সার নয়। স্থিতিশীল থাকে। দ্রুত বৃদ্ধি বা "
            "পরিবর্তন হলে চিকিৎসকের কাছে যান।"
        ),
    },
}


def get_class_info(code: str) -> dict | None:
    """Return the education entry for a HAM10000 class code, or None."""
    return EDUCATION_CONTENT.get(code)


def all_classes() -> list:
    """Return all education entries in canonical HAM10000 order."""
    from apps.common.services.prediction import CLASS_ORDER
    return [EDUCATION_CONTENT[c] for c in CLASS_ORDER if c in EDUCATION_CONTENT]


# ---------------------------------------------------------------------------
# General skin health library (non-class-specific articles)
# ---------------------------------------------------------------------------

LIBRARY_ARTICLES = {
    "abcde-rule": {
        "slug": "abcde-rule",
        "title": "The ABCDE rule for spotting melanoma",
        "bangla_title": "মেলানোমা শনাক্তকরণের ABCDE নিয়ম",
        "summary": (
            "A simple five-point checklist dermatologists teach patients to "
            "self-screen moles for warning signs of melanoma."
        ),
        "bangla_summary": (
            "ডার্মাটোলজিস্টরা রোগীদের শেখানো একটি সহজ পাঁচ-ধাপের চেকলিস্ট, "
            "যা মেলানোমার সতর্ক লক্ষণগুলো নিজে পরীক্ষা করতে সাহায্য করে।"
        ),
        "icon": "alert-triangle",
        "body": [
            {
                "heading": "What is the ABCDE rule?",
                "text": (
                    "The ABCDE rule is a screening tool that helps you "
                    "decide whether a mole deserves a dermatologist's "
                    "attention. It is not a diagnostic tool — only a "
                    "professional examination (and, when indicated, a "
                    "biopsy) can confirm or rule out melanoma. Use it "
                    "monthly as part of a full-body self-examination."
                ),
            },
            {
                "heading": "A — Asymmetry",
                "text": (
                    "One half of the lesion does not match the other. "
                    "Benign moles are usually symmetric; melanomas often "
                    "have an irregular shape where one side looks "
                    "different from the other."
                ),
            },
            {
                "heading": "B — Border irregularity",
                "text": (
                    "The edges are ragged, notched, scalloped, or blurred "
                    "instead of smooth and even. Poorly defined borders "
                    "are a known warning sign."
                ),
            },
            {
                "heading": "C — Colour variation",
                "text": (
                    "The colour is not uniform. Multiple shades of brown, "
                    "black, blue, red, or white within a single lesion "
                    "are suspicious. Benign moles are usually one or two "
                    "shades of brown."
                ),
            },
            {
                "heading": "D — Diameter",
                "text": (
                    "The lesion is larger than 6 mm (about the diameter "
                    "of a pencil eraser). Melanomas are often larger, "
                    "though they can be smaller when first detected."
                ),
            },
            {
                "heading": "E — Evolving",
                "text": (
                    "The lesion is changing in size, shape, colour, or "
                    "elevation, or starts to itch, bleed, or crust. "
                    "Change is one of the strongest warning signs — even "
                    "if other ABCD criteria are not met."
                ),
            },
            {
                "heading": "Limitations",
                "text": (
                    "Some melanomas do not fit the ABCDE rule — "
                    "nodular melanomas, for instance, can be small, "
                    "symmetric, and uniformly coloured. The 'ugly "
                    "duckling sign' (a mole that looks different from "
                    "all your others) is an additional screening tool. "
                    "Any lesion that concerns you deserves professional "
                    "review, regardless of ABCDE score."
                ),
            },
        ],
        "references": [
            ("American Academy of Dermatology — How to spot melanoma", "https://www.aad.org/public/diseases/skin-cancer/find/know-how"),
            ("Skin Cancer Foundation — melanoma warning signs", "https://www.skincancer.org/skin-cancer-information/melanoma/melanoma-warning-signs/"),
            ("CDC — Skin cancer prevention", "https://www.cdc.gov/cancer/skin/basic_info/prevention.htm"),
        ],
    },

    "sun-protection": {
        "slug": "sun-protection",
        "title": "Sun protection: the single most important skin-cancer prevention habit",
        "bangla_title": "সূর্য সুরক্ষা: ত্বকের ক্যান্সার প্রতিরোধের সবচেয়ে গুরুত্বপূর্ণ অভ্যাস",
        "summary": (
            "UV exposure is the leading modifiable risk factor for skin "
            "cancer. Practical, evidence-based sun-protection habits."
        ),
        "bangla_summary": (
            "অতিরিক্ত সূর্যালোক ত্বকের ক্যান্সারের প্রধান পরিবর্তনযোগ্য কারণ। "
            "বাস্তবসম্মত ও বিজ্ঞান-ভিত্তিক সূর্য সুরক্ষা অভ্যাস।"
        ),
        "icon": "sun",
        "body": [
            {
                "heading": "Why it matters",
                "text": (
                    "Ultraviolet (UV) radiation from the sun (and tanning "
                    "beds) damages skin-cell DNA. Cumulative damage "
                    "drives most skin cancers, including basal cell "
                    "carcinoma, squamous cell carcinoma, and melanoma. "
                    "UV index forecasts are widely available — when the "
                    "index is 3 or higher, sun protection is "
                    "recommended for all skin types."
                ),
            },
            {
                "heading": "Sunscreen",
                "text": (
                    "Use a broad-spectrum, water-resistant sunscreen "
                    "with SPF 30 or higher. Apply 15 minutes before sun "
                    "exposure and reapply every 2 hours, or after "
                    "swimming or heavy sweating. Use about 30 ml (one "
                    "shot glass) for full-body coverage. Check the "
                    "expiry date — most sunscreens lose effectiveness "
                    "after 3 years."
                ),
            },
            {
                "heading": "Protective clothing",
                "text": (
                    "Long-sleeved shirts, long pants, and tightly-woven "
                    "fabrics block more UV than thin, light-coloured "
                    "fabrics. Some clothing carries a UPF (Ultraviolet "
                    "Protection Factor) rating — UPF 50+ blocks 98% of "
                    "UV. Wide-brimmed hats protect face, ears, and neck."
                ),
            },
            {
                "heading": "Shade and timing",
                "text": (
                    "UV intensity peaks between 10 AM and 4 PM. Seek "
                    "shade during these hours when possible. Remember "
                    "that UV reflects off water, sand, and snow — shade "
                    "alone does not eliminate exposure."
                ),
            },
            {
                "heading": "Sunglasses",
                "text": (
                    "Wear sunglasses that block 99-100% of UVA and UVB. "
                    "UV exposure contributes to cataracts and ocular "
                    "melanoma."
                ),
            },
            {
                "heading": "Tanning beds",
                "text": (
                    "Avoid tanning beds entirely. The International "
                    "Agency for Research on Cancer classifies UV "
                    "tanning devices as Group 1 carcinogens (the same "
                    "category as tobacco and asbestos)."
                ),
            },
        ],
        "references": [
            ("WHO — UV radiation and health", "https://www.who.int/health-topics/ultraviolet-radiation"),
            ("CDC — Sun safety", "https://www.cdc.gov/cancer/skin/basic_info/sun-safety.htm"),
            ("American Academy of Dermatology — Sunscreen", "https://www.aad.org/public/everyday-care/sun-protection/shade-clothing-sunscreen/sunscreen-how-to-apply"),
        ],
    },

    "self-exam": {
        "slug": "self-exam",
        "title": "How to perform a monthly skin self-examination",
        "bangla_title": "মাসিক ত্বক স্ব-পরীক্ষা যেভাবে করবেন",
        "summary": (
            "A 10-minute monthly routine that catches new and changing "
            "lesions early — when treatment is most effective."
        ),
        "bangla_summary": (
            "মাত্র ১০ মিনিটের মাসিক রুটিন, যা নতুন ও পরিবর্তনশীল ত্বকের দাগ "
            "শীঘ্রই ধরতে সাহায্য করে—যখন চিকিৎসা সবচেয়ে কার্যকর।"
        ),
        "icon": "search",
        "body": [
            {
                "heading": "Why monthly?",
                "text": (
                    "Most skin cancers, including melanoma, are first "
                    "detected by patients or their partners — not by "
                    "doctors. A monthly self-exam helps you build a "
                    "mental baseline so any change is noticeable. "
                    "Combined with annual professional skin checks for "
                    "high-risk individuals, this catches the vast "
                    "majority of concerning lesions early."
                ),
            },
            {
                "heading": "What you need",
                "text": (
                    "A full-length mirror, a hand-held mirror, a "
                    "brightly-lit room, a hair-dryer (for the scalp), "
                    "and a body map or smartphone camera to track "
                    "changes over time."
                ),
            },
            {
                "heading": "The routine",
                "text": (
                    "1) Face: check ears, lips, and around the eyes. "
                    "2) Scalp: use a hair-dryer on low to part hair "
                    "section by section, or ask a partner. "
                    "3) Hands: palms, backs, between fingers, "
                    "under nails. "
                    "4) Arms: full extension, including underarms. "
                    "5) Torso: front, back, and sides. Use the "
                    "hand-held mirror for hard-to-see areas. "
                    "6) Lower body: front and back of legs, feet "
                    "(including soles and between toes), genitals, "
                    "and buttocks."
                ),
            },
            {
                "heading": "What to look for",
                "text": (
                    "New moles (especially after age 40), changing "
                    "moles (size, shape, colour, elevation), the "
                    "'ugly duckling' that looks different from your "
                    "other moles, sores that don't heal within 3 weeks, "
                    "and any lesion that itches, bleeds, or hurts. Use "
                    "the ABCDE rule as a checklist."
                ),
            },
            {
                "heading": "When to seek care",
                "text": (
                    "Any change you can see, feel, or photograph over "
                    "2-3 months deserves evaluation. Take dated photos "
                    "of any concerning lesion next to a ruler for scale "
                    "— this helps the dermatologist judge whether it is "
                    "truly evolving."
                ),
            },
        ],
        "references": [
            ("American Academy of Dermatology — Skin cancer screenings", "https://www.aad.org/public/diseases/skin-cancer/find/screening"),
            ("Skin Cancer Foundation — Self-exam", "https://www.skincancer.org/skin-cancer-information/early-detection/"),
            ("American Cancer Society — Skin exams", "https://www.cancer.org/cancer/melanoma-skin-cancer/detection-diagnosis-staging/detection.html"),
        ],
    },

    "when-to-see-doctor": {
        "slug": "when-to-see-doctor",
        "title": "When to see a dermatologist",
        "bangla_title": "কখন ডার্মাটোলজিস্ট দেখাবেন",
        "summary": (
            "Clear, situation-specific guidance on when a lesion "
            "warrants professional review — and how soon."
        ),
        "bangla_summary": (
            "কখন কোনো ত্বকের দাগ পেশাদার পরীক্ষা প্রয়োজন—এবং কত দ্রুত—তার "
            "স্পষ্ট, পরিস্থিতিভিত্তিক নির্দেশিকা।"
        ),
        "icon": "stethoscope",
        "body": [
            {
                "heading": "Urgent (within days)",
                "text": (
                    "A lesion that is bleeding spontaneously, growing "
                    "rapidly, painful, or has been a non-healing sore "
                    "for 3+ weeks. A pigmented lesion that fits any of "
                    "the ABCDE criteria, especially 'Evolving'. A new "
                    "dark streak under a nail (especially thumb or big "
                    "toe) that is not from trauma."
                ),
            },
            {
                "heading": "Soon (within weeks)",
                "text": (
                    "A new mole that appeared after age 40. A mole that "
                    "looks different from your others (ugly duckling). "
                    "A persistent itch, tenderness, or crusting on a "
                    "lesion. A pearly or waxy bump that bleeds and "
                    "heals cyclically. A pink scaly patch on sun-"
                    "exposed skin that does not resolve."
                ),
            },
            {
                "heading": "Routine (within months)",
                "text": (
                    "Annual full-body skin checks if you have: more than "
                    "50 moles; fair skin with a history of frequent "
                    "sunburns; personal or family history of skin "
                    "cancer; immunosuppression; or extensive sun-"
                    "damaged skin. Anyone with these risk factors "
                    "should establish a baseline with a dermatologist."
                ),
            },
            {
                "heading": "What to bring to your appointment",
                "text": (
                    "A list of the lesions that concern you, with "
                    "approximate dates when you first noticed them. "
                    "Dated photos if you have them. Your full medical "
                    "history including any prior skin biopsies or "
                    "removals. A list of medications you take — some "
                    "cause photosensitivity. Family history of skin "
                    "cancer."
                ),
            },
            {
                "heading": "What to expect",
                "text": (
                    "A dermatologist uses bright light and a "
                    "dermatoscope (a 10x magnifier with polarised "
                    "light) to examine lesions. If anything looks "
                    "suspicious, a small biopsy (usually shave or "
                    "punch) is performed under local anaesthetic and "
                    "sent to a pathologist. Results typically take "
                    "1-2 weeks."
                ),
            },
        ],
        "references": [
            ("American Academy of Dermatology — Find a dermatologist", "https://www.aad.org/find-a-derm"),
            ("Mayo Clinic — Skin cancer diagnosis", "https://www.mayoclinic.org/diseases-conditions/skin-cancer/diagnosis-treatment/drc-20377605"),
            ("Bangladesh Dermatological Society", "https://www.bds.org.bd/"),
        ],
    },
}


def get_article(slug: str) -> dict | None:
    return LIBRARY_ARTICLES.get(slug)


def all_articles() -> list:
    return list(LIBRARY_ARTICLES.values())
