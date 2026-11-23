"""Pure game logic: word lists and guess scoring. No I/O besides loading word files."""
import random
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
MIN_LENGTH, MAX_LENGTH = 5, 8

CORRECT, PRESENT, ABSENT = "correct", "present", "absent"

def _load(name: str) -> list[str]:
    return [w for w in DATA_DIR.joinpath(name).read_text().split() if w]

VALID_WORDS: frozenset[str] = frozenset(_load("valid_words.txt"))
ANSWERS: dict[int, list[str]] = {n: [] for n in range(MIN_LENGTH, MAX_LENGTH + 1)}
for _w in _load("answers.txt"):
    if len(_w) in ANSWERS:
        ANSWERS[len(_w)].append(_w)

def max_guesses(word_length: int) -> int:
    return word_length + 1

def pick_answer(word_length: int) -> str:
    return random.choice(ANSWERS[word_length])

def is_valid_word(word: str) -> bool:
    return word in VALID_WORDS

def score_guess(guess: str, answer: str) -> list[str]:
    """Return per-letter feedback, handling repeated letters like real Wordle.

    Pass 1 marks exact matches and tallies the answer letters left unmatched.
    Pass 2 marks a letter present only while unmatched copies remain, so a
    guess with two Es against an answer with one E yields one yellow/green E
    and one gray E.
    """
    assert len(guess) == len(answer)
    result = [ABSENT] * len(guess)
    remaining: dict[str, int] = {}
    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            result[i] = CORRECT
        else:
            remaining[a] = remaining.get(a, 0) + 1
    for i, g in enumerate(guess):
        if result[i] == CORRECT:
            continue
        if remaining.get(g, 0) > 0:
            result[i] = PRESENT
            remaining[g] -= 1
    return result
