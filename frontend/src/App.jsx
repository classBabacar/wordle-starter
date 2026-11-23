import { useEffect, useState } from "react";
import { createGame } from "./api";
import Game from "./components/Game";
import Home from "./components/Home";
import "./App.css";

const idFromHash = () => window.location.hash.slice(1) || null;

export default function App() {
  const [gameId, setGameId] = useState(idFromHash);
  const [homeKey, setHomeKey] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    const sync = () => {
      setGameId(idFromHash());
      setHomeKey((k) => k + 1);
    };
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  const open = (id) => {
    window.location.hash = id ?? "";
  };

  async function again(length) {
    setError("");
    try {
      open((await createGame(length)).id);
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <main>
      <h1>
        <a href="#" onClick={() => open(null)}>
          Wordle
        </a>
      </h1>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {gameId ? (
        <Game
          key={gameId}
          id={gameId}
          onHome={() => open(null)}
          onNewGame={again}
        />
      ) : (
        <Home key={homeKey} onOpen={open} />
      )}
    </main>
  );
}
