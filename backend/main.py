import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import logic
import store

IN_PROGRESS, WON, LOST = "in_progress", "won", "lost"

@asynccontextmanager
async def lifespan(_: FastAPI):
    store.init_db()
    yield

app = FastAPI(title="Wordle API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NewGame(BaseModel):
    word_length: int = 5

class NewGuess(BaseModel):
    guess: str

def public_game(game: dict) -> dict:
    """Shape a stored game for clients. The answer is revealed only once the game ends."""
    over = game["status"] != IN_PROGRESS
    return {
        "id": game["id"],
        "word_length": game["word_length"],
        "max_guesses": logic.max_guesses(game["word_length"]),
        "status": game["status"],
        "guesses": game["guesses"],
        "answer": game["answer"] if over else None,
        "created_at": game["created_at"],
    }

def load_game(game_id: str) -> dict:
    game = store.get_game(game_id)
    if game is None:
        raise HTTPException(404, "Game not found.")
    return game

@app.post("/games", status_code=201)
def create_game(body: NewGame):
    if not logic.MIN_LENGTH <= body.word_length <= logic.MAX_LENGTH:
        raise HTTPException(
            422, f"word_length must be between {logic.MIN_LENGTH} and {logic.MAX_LENGTH}."
        )
    game_id = store.create_game(body.word_length, logic.pick_answer(body.word_length))
    return public_game(load_game(game_id))

@app.get("/games")
def list_games():
    return [
        {**g, "max_guesses": logic.max_guesses(g["word_length"])} for g in store.list_games()
    ]

@app.get("/games/{game_id}")
def get_game(game_id: str):
    return public_game(load_game(game_id))

@app.post("/games/{game_id}/guesses", status_code=201)
def submit_guess(game_id: str, body: NewGuess):
    game = load_game(game_id)
    if game["status"] != IN_PROGRESS:
        raise HTTPException(409, "This game is already over.")

    guess = body.guess.strip().lower()
    n = game["word_length"]
    if len(guess) != n or not guess.isalpha() or not guess.isascii():
        raise HTTPException(422, f"Guess must be exactly {n} letters.")
    if not logic.is_valid_word(guess):
        raise HTTPException(422, f"“{guess}” is not in the word list.")

    feedback = logic.score_guess(guess, game["answer"])
    used = len(game["guesses"]) + 1
    if guess == game["answer"]:
        status = WON
    elif used >= logic.max_guesses(n):
        status = LOST
    else:
        status = IN_PROGRESS
    store.add_guess(game_id, used, guess, feedback, status)
    return public_game(load_game(game_id))
