import pytest

from logic import ABSENT as A, CORRECT as C, PRESENT as P
from logic import ANSWERS, is_valid_word, max_guesses, score_guess

def test_all_correct():
    assert score_guess("crane", "crane") == [C] * 5

def test_all_absent():
    assert score_guess("moldy", "crane") == [A] * 5

def test_present_and_correct_mix():
    assert score_guess("nacre", "crane") == [P, P, P, P, C]

def test_guess_has_more_copies_than_answer():
    # answer "crane" has a single E (index 4). The first E in "eerie" is misplaced
    # and claims it; the second E has no copy left, and the final E is exact.
    assert score_guess("eerie", "crane") == [A, A, P, A, C]

def test_exact_match_beats_present_for_same_letter():
    # answer "allow" has two Ls (1, 2). In "lolly" the exact L at index 2 is
    # claimed first, leaving one L for the misplaced L at index 0; index 3 gets none.
    assert score_guess("lolly", "allow") == [P, P, C, A, A]

def test_answer_has_more_copies_than_guess():
    # answer "geese": Es at 1, 2, 4. Guess "eerie": exact at 1 and 4, leaving one for index 0.
    assert score_guess("eerie", "geese") == [P, C, A, A, C]

@pytest.mark.parametrize("n", range(5, 9))
def test_every_length_has_answers_that_are_valid_words(n):
    assert len(ANSWERS[n]) > 500
    assert all(len(w) == n and is_valid_word(w) for w in ANSWERS[n][:200])

def test_answers_are_not_plural():
    for words in ANSWERS.values():
        for w in words:
            assert not (w.endswith("s") and not w.endswith(("ss", "us", "is")))

def test_turn_limit_is_length_plus_one():
    assert [max_guesses(n) for n in range(5, 9)] == [6, 7, 8, 9]
