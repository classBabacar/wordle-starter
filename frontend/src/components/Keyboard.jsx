const ROWS = ["qwertyuiop", "asdfghjkl", "+zxcvbnm-"];
const RANK = { absent: 1, present: 2, correct: 3 };

function letterStates(guesses) {
  const best = {};
  for (const { word, feedback } of guesses) {
    [...word].forEach((ch, i) => {
      if ((RANK[feedback[i]] ?? 0) > (RANK[best[ch]] ?? 0))
        best[ch] = feedback[i];
    });
  }
  return best;
}

export default function Keyboard({ guesses, onKey, disabled }) {
  const states = letterStates(guesses);
  return (
    <div className="keyboard" aria-label="On-screen keyboard">
      {ROWS.map((row) => (
        <div className="kb-row" key={row}>
          {[...row].map((k) => {
            const wide = k === "+" || k === "-";
            const label = k === "+" ? "Enter" : k === "-" ? "Delete" : k;
            return (
              <button
                key={k}
                type="button"
                disabled={disabled}
                className={`key ${wide ? "wide" : ""} ${states[k] ?? ""}`}
                onClick={() =>
                  onKey(k === "+" ? "Enter" : k === "-" ? "Backspace" : k)
                }
              >
                {label}
              </button>
            );
          })}
        </div>
      ))}
    </div>
  );
}
