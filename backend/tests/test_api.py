import threading

import pytest
from fastapi.testclient import TestClient

import logic
import store

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "test.db")
    from main import app

    with TestClient(app) as c:
        yield c

@pytest.fixture()
def new_game(client, monkeypatch):
    """Create a game with a pinned answer. monkeypatch undoes the pin after each test."""

    def make(n=5, answer="crane"):
        assert len(answer) == n
        monkeypatch.setattr(logic, "pick_answer", lambda length: answer)
        r = client.post("/games", json={"word_length": n})
        assert r.status_code == 201
        return r.json()

    return make

def test_create_game_hides_answer(client, new_game):
    g = new_game()
    assert g["word_length"] == 5 and g["max_guesses"] == 6
    assert g["status"] == "in_progress" and g["answer"] is None and g["guesses"] == []

@pytest.mark.parametrize("n", [4, 9, 0, -1])
def test_rejects_bad_word_length(client, n):
    assert client.post("/games", json={"word_length": n}).status_code == 422

def test_get_unknown_game_404(client):
    assert client.get("/games/nope").status_code == 404
    assert client.post("/games/nope/guesses", json={"guess": "crane"}).status_code == 404

def test_guess_feedback_and_state(client, new_game):
    g = new_game()
    r = client.post(f"/games/{g['id']}/guesses", json={"guess": "NACRE"})
    assert r.status_code == 201
    body = r.json()
    assert body["guesses"][0] == {
        "word": "nacre",
        "feedback": ["present", "present", "present", "present", "correct"],
    }
    assert client.get(f"/games/{g['id']}").json()["guesses"] == body["guesses"]

@pytest.mark.parametrize("guess", ["cran", "cranes", "cr4ne", "     ", "zzzzz"])
def test_invalid_guesses_rejected_and_not_counted(client, new_game, guess):
    g = new_game()
    assert client.post(f"/games/{g['id']}/guesses", json={"guess": guess}).status_code == 422
    assert client.get(f"/games/{g['id']}").json()["guesses"] == []

def test_win_reveals_answer_and_locks_game(client, new_game):
    g = new_game()
    body = client.post(f"/games/{g['id']}/guesses", json={"guess": "crane"}).json()
    assert body["status"] == "won" and body["answer"] == "crane"
    assert client.post(f"/games/{g['id']}/guesses", json={"guess": "pound"}).status_code == 409

@pytest.mark.parametrize(
    "n,answer,wrong", [(5, "crane", "pound"), (8, "abstract", "daughter")]
)
def test_loss_after_n_plus_one_guesses(client, new_game, n, answer, wrong):
    g = new_game(n, answer)
    for i in range(n + 1):
        body = client.post(f"/games/{g['id']}/guesses", json={"guess": wrong}).json()
        assert body["status"] == ("lost" if i == n else "in_progress")
    assert body["answer"] == answer
    assert len(body["guesses"]) == n + 1

def test_multiple_games_are_independent_and_listed(client, new_game):
    a = new_game(5, "crane")
    b = new_game(6, "planet")
    client.post(f"/games/{a['id']}/guesses", json={"guess": "pound"})
    listing = client.get("/games").json()
    by_id = {g["id"]: g for g in listing}
    assert by_id[a["id"]]["guess_count"] == 1 and by_id[b["id"]]["guess_count"] == 0
    assert "answer" not in by_id[a["id"]]

def test_stale_guess_is_rejected_and_not_stored(client, new_game):
    g = new_game()
    feedback = ["absent"] * 5
    store.add_guess(g["id"], 1, "pound", feedback, "in_progress")
    # A second writer that read the game before the first guess landed:
    with pytest.raises(store.GuessConflict):
        store.add_guess(g["id"], 1, "slate", feedback, "in_progress")
    assert [x["word"] for x in client.get(f"/games/{g['id']}").json()["guesses"]] == ["pound"]

def test_cannot_exceed_turn_limit_with_a_stale_read(client, new_game):
    g = new_game()
    feedback = ["absent"] * 5
    for pos in range(1, 6):
        store.add_guess(g["id"], pos, "pound", feedback, "in_progress")
    store.add_guess(g["id"], 6, "pound", feedback, "lost")
    # A request that read the game while it still had 6 turns' worth of room:
    with pytest.raises(store.GuessConflict):
        store.add_guess(g["id"], 7, "pound", feedback, "in_progress")
    body = client.get(f"/games/{g['id']}").json()
    assert len(body["guesses"]) == 6 and body["status"] == "lost"

def test_simultaneous_guesses_never_corrupt_a_game(client, new_game):
    words = ["slate", "raise", "stare", "audio", "adieu", "about", "above", "abuse", "actor", "pound"]
    for _ in range(5):  # the original race showed up in roughly every trial; repeat for confidence
        g = new_game()
        codes, errors = [], []

        def submit(word):
            try:
                codes.append(client.post(f"/games/{g['id']}/guesses", json={"guess": word}).status_code)
            except Exception as e:  # a server crash surfaces here
                errors.append(e)

        threads = [threading.Thread(target=submit, args=(words[i % len(words)],)) for i in range(25)]
        [t.start() for t in threads]
        [t.join() for t in threads]

        body = client.get(f"/games/{g['id']}").json()
        assert not errors
        assert set(codes) <= {201, 409}
        assert len(body["guesses"]) == codes.count(201) <= 6
        if len(body["guesses"]) == 6:
            assert body["status"] == "lost"

