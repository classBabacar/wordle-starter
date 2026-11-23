export default function Board({ game, current, shakeRow, revealRow }) {
  const rows = [];
  for (let r = 0; r < game.max_guesses; r++) {
    const guess = game.guesses[r];
    const isCurrent =
      !guess && r === game.guesses.length && game.status === "in_progress";
    const letters = guess ? guess.word : isCurrent ? current : "";
    const tiles = [];
    for (let c = 0; c < game.word_length; c++) {
      const state = guess ? guess.feedback[c] : letters[c] ? "typed" : "empty";
      tiles.push(
        <div
          key={c}
          className={`tile ${state}${guess && r === revealRow ? " reveal" : ""}`}
          style={{ "--i": c }}
          aria-label={guess ? `${letters[c]}, ${state}` : letters[c] || "empty"}
        >
          {letters[c] ?? ""}
        </div>,
      );
    }
    rows.push(
      <div
        key={r}
        className={`row${isCurrent && shakeRow ? " shake" : ""}`}
        style={{ "--n": game.word_length }}
        role="group"
        aria-label={`Guess ${r + 1}`}
      >
        {tiles}
      </div>,
    );
  }
  return <div className="board">{rows}</div>;
}
