const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request(path, options) {
  let res;
  try {
    res = await fetch(`${API_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error(
      "Can’t reach the server. Check that the backend is running.",
    );
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = body.detail;
    throw new Error(
      typeof detail === "string" ? detail : "Something went wrong.",
    );
  }
  return body;
}

export const listGames = () => request("/games");
export const getGame = (id) => request(`/games/${id}`);
export const createGame = (wordLength) =>
  request("/games", {
    method: "POST",
    body: JSON.stringify({ word_length: wordLength }),
  });
export const submitGuess = (id, guess) =>
  request(`/games/${id}/guesses`, {
    method: "POST",
    body: JSON.stringify({ guess }),
  });
