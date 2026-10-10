// Share-link panel on the account page: list, copy and revoke owned links.
(function () {
  var list = document.getElementById("share-list");
  if (!list) return;
  var message = document.getElementById("share-message");
  var offset = 0;
  var pageSize = 50;
  var loading = false;
  var hasOlder = false;
  var paging = document.createElement("div");
  var previous = button("Previous links", function () { load(Math.max(0, offset - pageSize)); });
  var next = button("Older links", function () { load(offset + pageSize); });
  paging.appendChild(previous);
  paging.appendChild(next);
  list.parentNode.insertBefore(paging, list.nextSibling);

  function status(text, isError) {
    message.textContent = text;
    message.className = "notice" + (isError ? " error" : "");
    message.hidden = false;
  }

  function describe(share) {
    if (share.revoked_at) return "Revoked";
    if (share.expires_at && share.expires_at <= new Date().toISOString()) return "Expired";
    return share.expires_at ? "Expires " + share.expires_at.slice(0, 10) : "No expiry";
  }

  function button(text, onClick) {
    var control = document.createElement("button");
    control.type = "button";
    control.className = "secondary";
    control.textContent = text;
    control.addEventListener("click", onClick);
    return control;
  }

  function copy(url) {
    if (!navigator.clipboard) {
      status("Copy is not available in this browser. Link: " + url, false);
      return;
    }
    navigator.clipboard.writeText(url).then(
      function () { status("Link copied.", false); },
      function () { status("Could not copy. Link: " + url, true); }
    );
  }

  function revoke(token) {
    fetch("/api/share/" + encodeURIComponent(token), {
      method: "DELETE",
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    })
      .then(function (response) {
        if (!response.ok) throw new Error("revoke");
        status("Link revoked. It stops working immediately.", false);
        load();
      })
      .catch(function () { status("Could not revoke that link.", true); });
  }

  function render(shares) {
    hasOlder = shares.length === pageSize;
    list.textContent = "";
    if (!shares.length) {
      var empty = document.createElement("li");
      empty.textContent = offset ? "No older links. Use Previous links to go back." : "No shared links yet.";
      list.appendChild(empty);
      return;
    }
    shares.forEach(function (share) {
      var item = document.createElement("li");
      var url = window.location.origin + "/v/" + share.token;
      var label = document.createElement("span");
      label.textContent = url + " · created " + share.created_at.slice(0, 10) + " · " + describe(share);
      item.appendChild(label);
      item.appendChild(button("Copy", function () { copy(url); }));
      if (!share.revoked_at) {
        item.appendChild(button("Revoke", function () { revoke(share.token); }));
      }
      list.appendChild(item);
    });
  }

  function controls() {
    previous.disabled = loading || offset === 0;
    next.disabled = loading || !hasOlder;
  }

  function load(requestedOffset) {
    if (loading) return;
    var targetOffset = requestedOffset === undefined ? offset : requestedOffset;
    loading = true;
    controls();
    fetch("/api/shares?offset=" + targetOffset, { credentials: "same-origin", headers: { Accept: "application/json" } })
      .then(function (response) {
        if (!response.ok) throw new Error("load");
        return response.json();
      })
      .then(function (shares) { offset = targetOffset; render(shares); })
      .catch(function () { status("Could not load shared links. Retry the same page.", true); })
      .finally(function () { loading = false; controls(); });
  }

  load();
})();
