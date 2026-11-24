# Wordle Full Stack Assessment

## Background

Wordle is a simple game in which you have to guess a five-letter word. You get six guesses, learning a little more information with each guess, and eventually narrow your guesses down to find the answer.

You can play an online version of Wordle [here](https://www.nytimes.com/games/wordle/index.html).

## Requirements

1. [x] Letters that are in the answer and in the right place turn green.
2. [x] Letters that are in the answer but in the wrong place turn yellow.
3. [x] Letters that are not in the answer turn gray.
4. [x] Answers are never plural.
5. [x] Letters can appear more than once. So if your guess includes two of one letter, they may both turn yellow, both turn green, or one could be yellow and the other green.
6. [x] Each guess must be a valid word in Wordle's dictionary. You can't guess ABCDE, for instance.
7. [x] You do not have to include correct letters in subsequent guesses.
8. [x] You have six guesses to solve the Wordle.
9. [x] **Multiple Games**: The user can create and play as many games as they want.
10. [x] **Configurable Word Length**: The user can configure the number of letters in the target word to be anywhere between 5 to 8 letters, but they will always only have N+1 turns to guess the word. For instance, traditional Wordle involves guessing a five-letter word over six turns, but in our version, the user can pick 7 as the number of letters and get 8 turns to guess the word.

# Design Choices

**Q: Why SQLite?**

**A:** SQLite needs no extra service, so `docker compose up` still works, and the DB file lives in a bind-mounted folder so games survive restarts. All SQL is in `store.py`, so moving to Postgres means rewriting one module.

**Q: Where does the game logic live, and why is the answer server-side?**

**A:** Scoring and word lists are in `logic.py` (pure functions, no I/O) so they're easy to test. The answer never leaves the server until the game is won or lost (`answer` is `null` before that), so players can't read it from the network tab.

**Q: How do you handle repeated letters?**

**A:** Two passes. First mark exact matches (green) and count the answer's unmatched letters. Then mark a misplaced letter yellow only while an unmatched copy remains. So a guess with two Es against an answer with one E gets one colored E and one gray E.

**Q: How did you build the word lists, and what are the tradeoffs?**

**A:** `build_words.py`, keeps lowercase-only entries (this drops proper nouns), and picks answers with a word-frequency cutoff so answers are familiar words. It also drops likely plurals and "-ed" forms. This gives ~5,000 answers (1,100-1,300 per length) and ~32,000 valid guesses. Guesses are intentionally more permissive than answers, so plural guesses are accepted but never chosen as answers. Tradeoffs: the plural check is a heuristic, and the guess dictionary is smaller than NYT's, so some real words (e.g. "ebook") are rejected. The generated files are committed, so the app doesn't need the script at runtime.

**Q: How do multiple games and resuming work?**

**A:** Each game gets a UUID. The frontend keeps it in the URL hash, so a refresh or bookmark resumes the same game, and the home screen lists all games. There are no user accounts, so the game list is global. That's fine for this scope but would be the first thing to change in production.

**Q: What does the API do on bad input?**

**A:** 404 for an unknown game, 422 for a wrong-length or non-word guess (or a bad `word_length`), and 409 for a guess on a finished game. A rejected guess does not use up a turn. The frontend shows the server's message and shakes the row.

**Q: Where is validation done?**

**A:** In both places, but the server is the source of truth. The UI limits input to letters and the right length for fast feedback, while the API re-checks length, characters and dictionary membership.

**Q: How did you structure the frontend?**

**A:** A small component tree (`Home`, `Game`, `Board`, `Keyboard`) with one API module. I used URL-hash routing instead of a router library because there are only two views. Keyboard events go through a ref so the handler never reads stale state.

**Q: How is it tested?**

**A:** 28 pytest tests cover scoring (including repeated-letter edge cases), word-list invariants, and the API end to end against a temporary database: win, loss at N+1 guesses, invalid guesses, and independent concurrent games. There are no frontend tests.

**Q: What would you do with more time?**

1. Add player identity so games aren't global.
2. Paginate `GET /games`.
3. Improve plural detection, probably some nice algorithm out there.

## Development Workflow

1. Start the backend with `docker compose up --build`
2. Start the frontend with `cd frontend && npm install && npm run dev`
3. Build your API endpoints in `backend/main.py`
4. Build your UI in the `frontend/src/` directory
5. The frontend is configured to make requests to `http://localhost:8000`
