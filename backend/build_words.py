import re
from pathlib import Path
from wordfreq import zipf_frequency

SRC = "/usr/share/dict/words"          # dictionary that keeps capitals
OUT = Path(__file__).parent / "data"
LENGTHS = range(5, 9)
MIN_ZIPF = 3.5                         # tune: higher = fewer, more common answers

def is_plural(w: str) -> bool:
    if w.endswith(("ss", "us", "is")):
        return False
    return w.endswith("s")

valid = set()
for line in open(SRC, encoding="utf-8"):
    w = line.strip()
    # lowercase-only drops proper nouns ("Aaron"); regex drops apostrophes, hyphens, digits
    if w.islower() and re.fullmatch(r"[a-z]+", w) and len(w) in LENGTHS:
        valid.add(w)

answers = {
    w for w in valid
    if zipf_frequency(w, "en") >= MIN_ZIPF
    and not is_plural(w)
    and not w.endswith("ed")           # Wordle also avoids past-tense answers
}
valid |= answers

(OUT / "valid_words.txt").write_text("\n".join(sorted(valid)) + "\n")
(OUT / "answers.txt").write_text("\n".join(sorted(answers)) + "\n")

for n in LENGTHS:
    print(n, sum(len(w) == n for w in valid), sum(len(w) == n for w in answers))