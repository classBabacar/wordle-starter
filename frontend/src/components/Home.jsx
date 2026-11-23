import { useEffect, useState } from "react";
import { createGame, listGames } from "../api";

const LENGTHS = [5, 6, 7, 8];
const LABEL = { in_progress: "In progress", won: "Won", lost: "Lost" };

export default function Home({ onOpen, initialLength = 5 }) {
  const [length, setLength] = useState(initialLength);
  const [games, setGames] = useState(null);
  const [error, setError] = useState("");
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    listGames()
      .then(setGames)
      .catch((e) => {
        setError(e.message);
        setGames([]);
      });
  }, []);

  async function start() {
    setStarting(true);
    setError("");
    try {
      onOpen((await createGame(length)).id);
    } catch (e) {
      setError(e.message);
      setStarting(false);
    }
  }

  return (
    <>
      <section className="panel">
        <fieldset className="lengths">
          <legend>Word length</legend>
          {LENGTHS.map((n) => (
            <label key={n} className={n === length ? "on" : ""}>
              <input
                type="radio"
                name="len"
                checked={n === length}
                onChange={() => setLength(n)}
              />
              {n}
            </label>
          ))}
        </fieldset>
        <p className="muted">You get {length + 1} guesses.</p>
        <button className="btn" onClick={start} disabled={starting}>
          {starting ? "Starting…" : "Start game"}
        </button>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
      </section>

      <section aria-labelledby="games-h">
        <h2 id="games-h">Your games</h2>
        {games === null ? (
          <p className="muted">Loading…</p>
        ) : games.length === 0 ? (
          <p className="muted">No games yet. Pick a length and start one.</p>
        ) : (
          <ul className="games">
            {games.map((g) => (
              <li key={g.id}>
                <button className="game-item" onClick={() => onOpen(g.id)}>
                  <span className="len">{g.word_length}</span>
                  <span>
                    {g.guess_count} of {g.max_guesses} guesses
                  </span>
                  <span className={`badge ${g.status}`}>{LABEL[g.status]}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
