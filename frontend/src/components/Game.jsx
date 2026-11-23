import { useCallback, useEffect, useRef, useState } from "react";
import { getGame, submitGuess } from "../api";
import Board from "./Board";
import Keyboard from "./Keyboard";

export default function Game({ id, onHome, onNewGame }) {
  const [game, setGame] = useState(null);
  const [current, setCurrent] = useState("");
  const [message, setMessage] = useState("");
  const [shake, setShake] = useState(false);
  const [busy, setBusy] = useState(false);
  const [revealRow, setRevealRow] = useState(-1);
  const [loadError, setLoadError] = useState("");
  const stateRef = useRef({});
  stateRef.current = { game, current, busy };

  useEffect(() => {
    let live = true;
    getGame(id)
      .then((g) => live && setGame(g))
      .catch((e) => live && setLoadError(e.message));
    return () => {
      live = false;
    };
  }, [id]);

  const press = useCallback(async (key) => {
    const { game, current, busy } = stateRef.current;
    if (!game || game.status !== "in_progress" || busy) return;
    if (key === "Backspace") return setCurrent(current.slice(0, -1));
    if (key === "Enter") {
      if (current.length < game.word_length) {
        setMessage(`Enter all ${game.word_length} letters.`);
        setShake(true);
        return;
      }
      setBusy(true);
      try {
        const next = await submitGuess(game.id, current);
        setGame(next);
        setRevealRow(next.guesses.length - 1);
        setCurrent("");
        setMessage("");
      } catch (e) {
        setMessage(e.message);
        setShake(true);
      } finally {
        setBusy(false);
      }
      return;
    }
    if (/^[a-z]$/i.test(key) && current.length < game.word_length) {
      setCurrent(current + key.toLowerCase());
      setMessage("");
    }
  }, []);

  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.key === "Enter" && document.activeElement?.tagName === "BUTTON")
        return;
      if (
        e.key === "Enter" ||
        e.key === "Backspace" ||
        /^[a-z]$/i.test(e.key)
      ) {
        e.preventDefault();
        press(e.key);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [press]);

  useEffect(() => {
    if (!shake) return;
    const t = setTimeout(() => setShake(false), 450);
    return () => clearTimeout(t);
  }, [shake]);

  if (loadError)
    return (
      <section className="panel">
        <p role="alert" className="error">
          {loadError}
        </p>
        <button className="btn" onClick={onHome}>
          Back to games
        </button>
      </section>
    );
  if (!game) return <p className="muted">Loading game…</p>;

  const over = game.status !== "in_progress";
  return (
    <section className="game">
      <header className="game-head">
        <button className="link" onClick={onHome}>
          All games
        </button>
        <p className="muted">
          {game.word_length} letters · guess{" "}
          {Math.min(game.guesses.length + (over ? 0 : 1), game.max_guesses)} of{" "}
          {game.max_guesses}
        </p>
      </header>

      <Board
        game={game}
        current={current}
        shakeRow={shake}
        revealRow={revealRow}
      />

      <p className="status" role="status" aria-live="polite">
        {message}
      </p>

      {over ? (
        <div className={`result ${game.status}`}>
          <p>
            {game.status === "won" ? (
              `Solved in ${game.guesses.length} of ${game.max_guesses}.`
            ) : (
              <>
                Out of guesses. The word was <strong>{game.answer}</strong>.
              </>
            )}
          </p>
          <div className="actions">
            <button className="btn" onClick={() => onNewGame(game.word_length)}>
              New {game.word_length}-letter game
            </button>
            <button className="btn ghost" onClick={onHome}>
              All games
            </button>
          </div>
        </div>
      ) : (
        <Keyboard guesses={game.guesses} onKey={press} disabled={busy} />
      )}
    </section>
  );
}
