# arabic-nlp-prep

Arabic NLP preprocessing and quick EDA (print-only) using NLTK.  
Pipeline: Normalization → Tokenization → Stopwords (+extra, normalization-aware) → Stemming (ISRI/Snowball/none) → Top-K word frequencies → Bigram collocations (PMI) → Regex (emails/dates/numbers).  
All outputs are printed to stdout. No files are written.

---

## Why this tool?

- Provides a standard Arabic text preprocessing baseline before any IR/Classification/RAG pipeline.
- Normalization-aware stopwords: the NLTK stopword list is normalized using the same policy as your text so matches are reliable (e.g., \"على\" → \"علي\" after normalization).
- Fast exploratory analysis (quick EDA): Top-K words and PMI bigrams to surface keywords and key phrases.
- Lightweight dependency footprint (NLTK only) and self-contained data directory next to the script.

---

## Features

- **Normalization**: remove diacritics and tatweel, unify alef forms, normalize hamza, optional ta marbuta handling.
- **Tokenization (regex)**: extract Arabic-letter tokens only (no digits or punctuation).
- **Stopwords**: load NLTK Arabic stopwords, normalize them with the same policy, and merge extra domain stopwords via CLI.
- **Stemming**: choose ISRI (aggressive), Snowball (lighter), or disable entirely.
- **Statistics**: Top-K word frequencies after cleaning.
- **Collocations**: Bigram PMI with scores; configurable frequency threshold `min_freq` to reduce noise.
- **Regex utilities**: extract emails and dates; extract numbers while excluding those that are part of date expressions.
- **Print-only**: no files are written; ideal for demos and quick EDA.

---

## Requirements

- Python 3.10+
- `nltk>=3.8.1`
- Internet connection on first run to download NLTK corpora (saved to `./nltk_data` next to the script)

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

Put the script in the project root as `nlp_ar_prep.py`.

---

## Quickstart

Built-in sample text:
```bash
python nlp_ar_prep.py
```

Custom inline text:
```bash
python nlp_ar_prep.py --text "Arabic sample text for NLP testing" --min_freq 1
```

From file:
```bash
python nlp_ar_prep.py --file my_text.txt --topk 30 --min_freq 2
```

---

## CLI Options

| Option | Type / Values | Default | Purpose |
|---|---|---:|---|
| `--text` | str |  | Pass input text directly |
| `--file` | path |  | Read input text from a UTF-8 file |
| `--topk` | int | 20 | Number of top frequent tokens to print |
| `--min_freq` | int | 2 | Minimum bigram frequency before PMI is computed |
| `--keep_ta_marbuta` | flag | off | Keep `ة` (do not convert to `ه`) |
| `--extra_stop` | str (comma-separated) | "" | Add domain stopwords (e.g., `"وفق,يجب,تطبيق"`) |
| `--min_len` | int | 2 | Drop tokens shorter than this length |
| `--stem` | `isri` \| `snowball` \| `none` | `isri` | Stemming algorithm or disable |

Examples:
```bash
# Show bigrams even on short text
python nlp_ar_prep.py --min_freq 1

# Add domain stopwords
python nlp_ar_prep.py --extra_stop "وفق,يجب,تطبيق,ضوابط,المعلومات,الالتزام,الممارسات,تواصل,عدد"

# RAG/Embeddings-friendly (no stemming, preserve ta marbuta)
python nlp_ar_prep.py --stem none --keep_ta_marbuta --min_len 2

# Use Snowball instead of ISRI
python nlp_ar_prep.py --stem snowball
```

---

## What the script prints

- **Summary**: token counts before and after stopword removal, number of stems, and which stemmer was used.
- **Top frequent tokens**: most frequent tokens after cleaning.
- **Top bigram collocations (PMI)**: best bigrams with PMI scores.
- **Regex extraction**: emails, dates, and numbers (excluding date parts).
- **Stemming examples**: a small demo showing the effect of the selected stemmer.

---

## How it works (internals)

1) **Normalization**  
   - Remove diacritics (`[\u064B-\u0652]`) and tatweel (`\u0640`)  
   - Unify alef forms: `إ أ آ ا → ا`  
   - `ى → ي`, `ؤ → و`, `ئ → ي`  
   - Optional ta marbuta normalization: `ة → ه` unless `--keep_ta_marbuta` is set  
   Purpose: reduce orthographic variance so downstream matching and statistics are more reliable.

2) **Tokenization (regex)**  
   - Pattern: `[\u0621-\u063A\u064F-\u064A]+` to return Arabic-only tokens (no digits, punctuation, or Latin).

3) **Stopwords (normalization-aware)**  
   - Load NLTK Arabic stopwords and normalize them using the same policy as the input.
   - Merge `--extra_stop` after normalizing those entries as well.
   - Remove stopwords and any tokens shorter than `--min_len`.

4) **Stemming (optional)**  
   - `ISRIStemmer`: rule-based and relatively aggressive; often approximates triliteral roots (may over-stem).
   - `SnowballStemmer("arabic")`: lighter stemming.
   - `none`: bypass stemming (often preferred for RAG/embedding scenarios).

5) **Statistics**  
   - `Counter` for top frequent tokens after cleaning.
   - `BigramCollocationFinder` + `PMI` for extracting key phrases; `min_freq` controls rare bigram noise.

6) **Regex utilities**  
   - Emails: general-purpose regex.
   - Dates: `YYYY-MM-DD` and `DD/MM/YYYY`.
   - Numbers: extracted with a filter that excludes numeric substrings belonging to dates.

---

## When to use which settings

- **RAG/Embeddings**: `--stem none --keep_ta_marbuta`  
  Preserve surface forms and meaning while doing light normalization.
- **IR/TF-IDF/Traditional Classification**: `--stem isri` or `--stem snowball`, and `--min_len 2` (or 3).  
- **Small corpora but you want collocations**: `--min_freq 1` to expose PMI bigrams on short texts.
- **Compliance-like domains**: use `--extra_stop` to extend the general NLTK stoplist.

---

## Limitations

- ISRI may over-stem; prefer Snowball or disable depending on your task.
- NLTK Arabic stopwords are generic; extend with domain stopwords via `--extra_stop`.
- Regex patterns are intentionally simple; for robust PII use stricter patterns or NER.

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

MIT License. Place the license text in `LICENSE` if desired.

---

## Acknowledgments

- Built with NLTK: stopwords corpus, ISRI/Snowball stemmers, and collocations utilities.

---

## Troubleshooting

- `LookupError: stopwords not found`  
  Ensure first run has internet access or install manually inside the project:
  ```bash
  python -c "import nltk; nltk.download('stopwords', download_dir='nltk_data'); nltk.download('punkt', download_dir='nltk_data')"
  ```
- Confirm your virtual environment is active and run the script from the same directory where it resides.
