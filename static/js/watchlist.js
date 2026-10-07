"use strict";
(function () {
  const form = document.getElementById("watch-form");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const error = document.getElementById("watch-error");
    error.hidden = true;
    const body = {
      ticker: document.getElementById("watch-ticker").value,
      target: parseFloat(document.getElementById("watch-target").value),
      direction: document.getElementById("watch-direction").value,
    };
    const r = await fetch("/api/watchlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await r.json();
    if (!r.ok) {
      error.textContent = data.error || "Could not watch ticker.";
      error.hidden = false;
      return;
    }
    location.reload();
  });
  for (const button of document.querySelectorAll(".unwatch")) {
    button.addEventListener("click", async () => {
      await fetch("/api/watchlist", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: button.dataset.ticker }),
      });
      location.reload();
    });
  }
})();
