"use strict";
(function () {
  for (const button of document.querySelectorAll(".share-one")) {
    button.addEventListener("click", async () => {
      const status = document.getElementById("share-status");
      const r = await fetch("/api/share", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ valuation_id: button.dataset.id }),
      });
      const data = await r.json();
      if (!r.ok) {
        if (status) status.textContent = data.error || "Sharing failed.";
        return;
      }
      const url = `${location.origin}${data.url}`;
      try {
        await navigator.clipboard.writeText(url);
        if (status) status.textContent = `Link copied: ${url}`;
      } catch {
        if (status) status.textContent = `Share link: ${url}`;
      }
    });
  }
})();
