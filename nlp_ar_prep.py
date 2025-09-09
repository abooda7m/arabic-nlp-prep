"""
written by abdulrahman alkholaifi

Arabic NLP quick pipeline using NLTK:
- Normalization (configurable ta marbuta handling)
- Tokenization (regex over Arabic letters)
- Stopwords removal (NLTK) with normalization-aware matching + extra domain stopwords
- Stemming (selectable: ISRI / Snowball / none)
- Word frequencies (Top-K)
- Bigram collocations (PMI) with scores
- Regex utilities: emails, dates, numbers (numbers exclude date parts)
"""

import os
import re
import argparse
from collections import Counter

# Force NLTK to use local ./nltk_data 
NLTK_DIR = os.path.join(os.path.dirname(__file__), "nltk_data")
os.makedirs(NLTK_DIR, exist_ok=True)
os.environ.setdefault("NLTK_DATA", NLTK_DIR)

import nltk
from nltk.corpus import stopwords
from nltk.stem.isri import ISRIStemmer
from nltk.stem.snowball import SnowballStemmer
from nltk.collocations import BigramCollocationFinder, BigramAssocMeasures


def ensure_nltk(pkgs):
    """Ensure required NLTK packages exist; download locally if missing."""
    for pkg in pkgs:
        try:
            sub = "tokenizers" if pkg == "punkt" else "corpora"
            nltk.data.find(f"{sub}/{pkg}")
        except LookupError:
            nltk.download(pkg, download_dir=NLTK_DIR, quiet=True)


# Make sure the minimal corpora exist
ensure_nltk(["stopwords", "punkt"])

# ----------------------- Normalization -----------------------
AR_DIACRITICS = re.compile(r"[\u0617-\u061A\u064B-\u0652]")
AR_TATWEEL = re.compile(r"\u0640")


def normalize_arabic(text: str, convert_ta_marbuta: bool = True) -> str:
    """Basic Arabic normalization commonly used in NLP preprocessing."""
    text = AR_DIACRITICS.sub("", text)
    text = AR_TATWEEL.sub("", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"[ؤ]", "و", text)
    text = re.sub(r"[ئ]", "ي", text)
    if convert_ta_marbuta:
        text = re.sub(r"ة", "ه", text)      
    return text

# ----------------------- Tokenization ------------------------
AR_LETTERS = r"[\u0621-\u063A\u0641-\u064A]+"


def tokenize_ar(text: str):
    """Tokenize Arabic by extracting Arabic letter sequences."""
    return re.findall(AR_LETTERS, text)

# ----------------------- Stopwords (normalized) --------------
AR_STOPWORDS_RAW = set(stopwords.words("arabic"))


def build_stopwords(convert_ta_marbuta: bool, extra: str):
    """Normalize NLTK Arabic stopwords and merge with extra comma-separated items."""
    base = {normalize_arabic(w, convert_ta_marbuta=convert_ta_marbuta) for w in AR_STOPWORDS_RAW}
    extra_items = {w.strip() for w in (extra.split(",") if extra else []) if w.strip()}
    extra_norm = {normalize_arabic(w, convert_ta_marbuta=convert_ta_marbuta) for w in extra_items}
    return base | extra_norm


def remove_stopwords(tokens, stop_set, min_len: int = 2):
    """Remove stopwords and tokens shorter than min_len."""
    return [t for t in tokens if t not in stop_set and len(t) >= min_len]

# ----------------------- Stemming ----------------------------
def make_stemmer(kind: str):
    """Return a stemmer instance based on kind."""
    if kind == "isri":
        return ISRIStemmer()
    if kind == "snowball":
        return SnowballStemmer("arabic")
    return None  # none


def stem_tokens(tokens, stemmer_obj):
    """Apply selected stemmer to tokens, or pass-through if None."""
    return tokens if stemmer_obj is None else [stemmer_obj.stem(t) for t in tokens]

# ----------------------- Regex utilities ---------------------
EMAIL_RE = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
DATE_ISO = r"\b\d{4}-\d{2}-\d{2}\b"
DATE_SL = r"\b\d{1,2}/\d{1,2}/\d{4}\b"
NUM_RE = r"\b\d+(?:\.\d+)?\b"


def extract_emails(text):
    return re.findall(EMAIL_RE, text)


def extract_dates(text):
    return re.findall(DATE_ISO, text) + re.findall(DATE_SL, text)


def _find_spans(pattern, text):
    return [m.span() for m in re.finditer(pattern, text)]


def extract_numbers_excluding_dates(text):
    """Extract numbers but ignore those that are part of date expressions."""
    date_spans = _find_spans(DATE_ISO, text) + _find_spans(DATE_SL, text)
    nums = []
    for m in re.finditer(NUM_RE, text):
        s, _ = m.span()
        if not any(ds <= s < de for (ds, de) in date_spans):
            nums.append(m.group())
    return nums


def print_list(title, items, limit=None):
    print(f"\n{title}")
    if limit is not None:
        items = items[:limit]
    for x in items:
        print(x)


def main():
    parser = argparse.ArgumentParser(description="Arabic NLP ")
    parser.add_argument("--text", type=str, help="Direct input text (UTF-8).")
    parser.add_argument("--file", type=str, help="Path to a UTF-8 text file.")
    parser.add_argument("--topk", type=int, default=20, help="Top-K tokens to print.")
    parser.add_argument("--min_freq", type=int, default=2, help="Min frequency for bigram PMI.")
    parser.add_argument("--keep_ta_marbuta", action="store_true",
                        help="Keep ta marbuta (do not convert 'ة' to 'ه').")
    parser.add_argument("--extra_stop", type=str, default="",
                        help="Comma-separated extra Arabic stopwords to remove.")
    parser.add_argument("--min_len", type=int, default=2,
                        help="Minimum token length to keep.")
    parser.add_argument("--stem", choices=["isri", "snowball", "none"], default="isri",
                        help="Choose stemming algorithm or disable it.")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            raw = f.read()
    elif args.text:
        raw = args.text
    else:
        raw = (
            "تلتزم الشركة بحماية بيانات العملاء وفق السياسات واللوائح المعمول بها. "
            "يجب على الجهة المسؤولة تطبيق ضوابط أمن المعلومات والالتزام بأفضل الممارسات. "
            "تواصل معنا على privacy@example.com بتاريخ 2025-09-09. عدد الموظفين 120."
        )

    print("Raw text:")
    print(raw)

    # Normalization policy
    convert_ta = not args.keep_ta_marbuta

    # Pipeline
    norm = normalize_arabic(raw, convert_ta_marbuta=convert_ta)
    tokens = tokenize_ar(norm)
    stop_set = build_stopwords(convert_ta_marbuta=convert_ta, extra=args.extra_stop)
    no_stop = remove_stopwords(tokens, stop_set, min_len=args.min_len)

    chosen_stemmer = make_stemmer(args.stem)
    stems = stem_tokens(no_stop, chosen_stemmer)

    # Frequencies
    freq = Counter(no_stop).most_common(args.topk)

    # Collocations PMI
    min_freq = max(1, args.min_freq)
    bigram_measures = BigramAssocMeasures()
    finder = BigramCollocationFinder.from_words(no_stop)
    if min_freq > 1:
        finder.apply_freq_filter(min_freq)
    scored = finder.score_ngrams(bigram_measures.pmi)
    top_scored = [f"{a} {b}\t{score:.3f}" for ((a, b), score) in scored[:10]]

    # Regex extras
    emails = extract_emails(raw)
    dates = extract_dates(raw)
    numbers = extract_numbers_excluding_dates(raw)

    # Print summary
    print("\nSummary:")
    print(f"Total tokens (before stopword removal): {len(tokens)}")
    print(f"After stopword removal: {len(no_stop)}")
    print(f"Total stems: {len(stems)}")
    print(f"Stemmer used: {args.stem}")

    print_list("Top frequent tokens (word\\tcount):", [f"{w}\t{c}" for w, c in freq])
    print_list(f"Top bigram collocations (PMI, min_freq={min_freq}):", top_scored)

    print("\nRegex extraction:")
    print(f"Emails: {emails}")
    print(f"Dates: {dates}")
    print(f"Numbers (excluding date parts): {numbers}")

    # Optional quick stemming demo
    demo_words = ["الكتابات", "تطبيقات", "بالمدارس", "معلوماتهم", "والالتزام"]
    if chosen_stemmer is not None:
        print("\nStemming examples:")
        for w in demo_words:
            print(w, "->", chosen_stemmer.stem(w))


if __name__ == "__main__":
    main()
