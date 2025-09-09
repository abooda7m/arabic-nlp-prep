# arabic-nlp-prep

Arabic NLP preprocessing & quick EDA (print-only) using NLTK.  
Pipeline: Normalization → Tokenization → Stopwords (+extra, normalization-aware) → Stemming (ISRI/Snowball/none) → Top-K word frequencies → Bigram collocations (PMI) → Regex (emails/dates/numbers).  
All outputs are printed to stdout. No files are written.

---

## Why this tool?

- توحيد **preprocessing** العربي بشكل قياسي قبل أي نموذج IR/Classification/RAG.
- **Normalization-aware stopwords**: نطبّع قائمة NLTK بنفس سياسة التطبيع حتى لا تفلت كلمات مثل "على" التي تصبح "علي".
- استكشاف سريع للداتا (quick EDA): Top-K و PMI لاستخراج **keywords** و**key phrases**.
- خفيف، يعتمد على NLTK فقط، ويضمن تنزيل corpora محليًا بجانب السكربت.

---

## Features

- **Normalization**: إزالة diacritics/tatweel، توحيد alef، تحويل hamza، خيار ta marbuta.
- **Tokenization (regex)**: التقاط الكلمات العربية فقط، لا أرقام ولا ترقيم.
- **Stopwords**: من NLTK + إمكانية إضافة domain stopwords عبر CLI، مع تطبيع متوافق.
- **Stemming**: اختيار ISRI أو Snowball أو تعطيله تمامًا.
- **Statistics**: Top-K word frequencies بعد التنقية.
- **Collocations**: Bigram PMI مع درجات، وعَتبة تكرار `min_freq` لتقليل الضجيج.
- **Regex utilities**: استخراج emails/dates، وأرقام تستثني أجزاء التواريخ.
- **Print-only**: لا يحفظ ملفات، مناسب للـdemo والـEDA السريع.

---

## Requirements

- Python 3.10+
- `nltk>=3.8.1`
- اتصال إنترنت أول مرة فقط لتنزيل NLTK corpora (يتم حفظها داخل `./nltk_data` بجوار السكربت)

`requirements.txt`:
```
nltk>=3.8.1
```

---

## Installation

Linux/Mac:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
```

ضع الملف باسم `nlp_ar_prep.py` في جذر المشروع.

---

## Quickstart

نص افتراضي مضمّن:
```bash
python nlp_ar_prep.py
```

نص مخصّص مباشرة:
```bash
python nlp_ar_prep.py --text "هذا نص عربي للتجربة في NLP" --min_freq 1
```

من ملف:
```bash
python nlp_ar_prep.py --file my_text.txt --topk 30 --min_freq 2
```

---

## CLI Options

| Option | Type / Values | Default | Purpose |
|---|---|---:|---|
| `--text` | str |  | تمرير النص مباشرة |
| `--file` | path |  | قراءة النص من ملف UTF-8 |
| `--topk` | int | 20 | عدد أعلى الكلمات تكرارًا بعد التنقية |
| `--min_freq` | int | 2 | حد أدنى لتكرار الـbigrams قبل حساب PMI |
| `--keep_ta_marbuta` | flag | off | إبقاء `ة` كما هي وعدم تحويلها إلى `ه` |
| `--extra_stop` | str (comma-sep) | "" | إضافة domain stopwords (مثال: `"وفق,يجب,تطبيق"`) |
| `--min_len` | int | 2 | تجاهل التوكنز الأقصر من هذا الطول |
| `--stem` | `isri` \| `snowball` \| `none` | `isri` | اختيار نوع الـstemming أو تعطيله |

أمثلة:
```bash
# استخراج عبارات حتى مع نص قصير
python nlp_ar_prep.py --min_freq 1

# إضافة stopwords للدومين
python nlp_ar_prep.py --extra_stop "وفق,يجب,تطبيق,ضوابط,المعلومات,الالتزام,الممارسات,تواصل,عدد"

# مناسب لـRAG/Embeddings (بدون stemming، مع إبقاء التاء المربوطة)
python nlp_ar_prep.py --stem none --keep_ta_marbuta --min_len 2

# Snowball بدل ISRI
python nlp_ar_prep.py --stem snowball
```

---

## What the script prints

- **Summary**: عدد tokens قبل وبعد إزالة stopwords، عدد stems، نوع الـstemmer المستخدم.
- **Top frequent tokens**: أعلى الكلمات تكرارًا (بعد التنقية).
- **Top bigram collocations (PMI)**: أفضل العبارات الثنائية مع درجات PMI.
- **Regex extraction**: Emails / Dates / Numbers (والأرقام تستثني أجزاء التواريخ).
- **Stemming examples**: توضيح تأثير الـstemmer على بعض الكلمات العربية.

---

## How it works (internals)

1) **Normalization**  
   - إزالة diacritics (`[\u064B-\u0652]`) وtatweel (`\u0640`)  
   - توحيد أشكال الألف: `إ أ آ ا → ا`  
   - `ى → ي` ، `ؤ → و` ، `ئ → ي`  
   - خيار `ta marbuta`: تحويل `ة → ه` إلا إذا فعّلت `--keep_ta_marbuta`  
   الهدف: تقليل التباين الكتابي لرفع دقة المطابقة لاحقًا.

2) **Tokenization (regex)**  
   - `[ء-غُ-ي]+` لإرجاع **سلاسل عربية فقط** (بدون أرقام/ترقيم/لاتيني).

3) **Stopwords (normalization-aware)**  
   - تحميل NLTK Arabic stopwords ثم **تطبيعها بنفس السياسة**  
   - دمج `--extra_stop` بعد تطبيعها  
   - إزالة stopwords وفلترة التوكنز القصيرة بـ `--min_len`

4) **Stemming (optional)**  
   - `ISRIStemmer`: rule-based قوي، غالبًا يرجّع قريب من الجذر الثلاثي (قد يعمل over-stemming).  
   - `SnowballStemmer("arabic")`: أخف.  
   - `none`: بدون stemming (مفضل لـRAG/Embeddings).

5) **Statistics**  
   - `Counter` لأعلى الكلمات تكرارًا بعد التنقية.  
   - `BigramCollocationFinder` + `PMI`: استخراج **key phrases**، مع `min_freq` لتقليل تحيز PMI للأزواج النادرة.

6) **Regex utilities**  
   - Emails: نمط عام.  
   - Dates: `YYYY-MM-DD` و `DD/MM/YYYY`.  
   - Numbers: تُستخرج ثم تُستبعد أي أرقام تقع داخل spans التواريخ.

---

## When to use which settings

- **RAG/Embeddings**: `--stem none --keep_ta_marbuta`  
  الهدف الحفاظ على الشكل والمعنى، مع Normalization خفيف لإزالة الضوضاء.
- **IR/TF-IDF/Classification**: `--stem isri` أو `--stem snowball`، و `--min_len 2` أو `3`.  
- **كوربس صغير وتبغى عبارات**: `--min_freq 1` لإظهار PMI حتى لو التكرار قليل.
- **Compliance domain**: استخدم `--extra_stop` لتوسيع stopwords العامة.

---

## Limitations

- ISRI أحيانًا يعمل over-stemming؛ جُرّب Snowball أو عطّل stemming.
- NLTK stopwords عامة؛ يفضل إضافة domain stopwords.
- Regex بسيطة عمدًا؛ للـPII المتقدم استخدم أنماط إضافية أو NER.

---

## Repository structure (suggested)

```
arabic-nlp-prep/
├─ nlp_ar_prep.py
├─ requirements.txt
├─ README.md
└─ .gitignore
```

`.gitignore`:
```
.venv/
__pycache__/
nltk_data/
*.pyc
.DS_Store
```

---

## License

MIT License. ضع نص الترخيص في `LICENSE` إن رغبت.

---

## Acknowledgments

- Built with NLTK: stopwords corpus, ISRI/Snowball stemmers, and collocations utilities.

---

## Troubleshooting

- `LookupError: stopwords not found`  
  شغّل السكربت مرة مع إنترنت أو نزّل يدويًا داخل المشروع:
  ```bash
  python -c "import nltk; nltk.download('stopwords', download_dir='nltk_data'); nltk.download('punkt', download_dir='nltk_data')"
  ```
- تأكد من تفعيل الـvenv وتشغيل الأمر من نفس مجلد السكربت.
