(function () {
  "use strict";
  const materials = window.STUDY_MATERIALS;
  const setSelect = document.getElementById("set");
  const loadSelect = document.getElementById("load");
  const links = document.getElementById("page-links");
  const status = document.getElementById("status");
  const progress = document.getElementById("launch-progress");
  const openButton = document.getElementById("open-tabs");
  const openAllHint = document.getElementById("open-all-hint");
  const nextButton = document.getElementById("open-next");
  const resetButton = document.getElementById("reset");
  const popupHelp = document.getElementById("popup-help");
  const openedWindows = new Map();
  if (!materials || !Array.isArray(materials.sets)) {
    status.textContent = "The content-set list could not load. Refresh this page and check that assets/manifest.js is present beside the other setup files.";
    status.dataset.state = "blocked";
    openButton.disabled = true;
    nextButton.disabled = true;
    return;
  }
  materials.sets.forEach(function (set) {
    const option = document.createElement("option");
    option.value = String(set.number);
    option.textContent = "Set " + set.number + ": " + set.topic + (set.extra ? " (extra)" : "");
    setSelect.appendChild(option);
  });
  function selectedSet() {
    return materials.sets.find(function (set) { return String(set.number) === setSelect.value; });
  }
  function plannedPages() {
    const set = selectedSet();
    return [{ path: materials.neutral_page, title: "Study Start — neutral starting tab" }]
      .concat(set[loadSelect.value].map(function (path) {
        return set.pages.find(function (page) { return page.path === path; });
      }));
  }
  function pruneClosedTabs() {
    openedWindows.forEach(function (handle, path) {
      if (handle.closed) openedWindows.delete(path);
    });
  }
  function openOne(path) {
    const handle = window.open(new URL(path, window.location.href).href, "_blank");
    if (!handle) return false;
    handle.opener = null;
    openedWindows.set(path, handle);
    return true;
  }
  function blockedMessage() {
    const origin = window.location.protocol === "file:" ? "this page" : window.location.origin;
    return "The browser blocked another tab. Return to this setup tab after viewing Study Start. Allow pop-ups for " + origin + " and click OPEN ALL TABS again, or use Open next tab once per tab. Tabs already opened in this preparation will not be duplicated.";
  }
  function render(message, blocked) {
    pruneClosedTabs();
    const pages = plannedPages();
    const count = openedWindows.size;
    const complete = count === pages.length;
    setSelect.disabled = count > 0;
    loadSelect.disabled = count > 0;
    openButton.disabled = complete;
    nextButton.disabled = complete;
    openButton.textContent = complete ? "ALL TABS OPEN" : "OPEN ALL TABS";
    const loadLabel = loadSelect.value === "low_load" ? "Low load" : "High load";
    openAllHint.textContent = selectedSet().topic + " · " + loadLabel + " · " + pages.length + " tabs: " + (pages.length - 1) + " task pages + Study Start." +
      (count && !complete ? " Opens the " + (pages.length - count) + " remaining tabs; tabs opened in this preparation are skipped." : "") +
      (complete ? "" : " Allow pop-ups for one-click opening.");
    nextButton.textContent = complete ? "All tabs opened" : "Open next tab (" + (count + 1) + " of " + pages.length + ")";
    progress.textContent = count + " / " + pages.length + " study tabs opened";
    status.dataset.state = blocked ? "blocked" : "ready";
    if (complete) {
      status.textContent = "All " + pages.length + " tabs are open for " + selectedSet().topic + ". Close this setup tab and unrelated tabs. Keep Study Start first, verify the task-page order, then activate Study Start before the recorded prompt.";
      popupHelp.open = false;
    } else if (message) {
      status.textContent = message;
    }
    if (blocked) popupHelp.open = true;
    links.replaceChildren();
    pages.forEach(function (page) {
      const item = document.createElement("li");
      const link = document.createElement("a");
      const opened = openedWindows.has(page.path);
      link.href = page.path;
      link.target = "_blank";
      link.rel = "noopener";
      link.textContent = (opened ? "Opened — " : "") + page.title;
      if (opened) item.className = "opened";
      link.addEventListener("click", function (event) {
        event.preventDefault();
        pruneClosedTabs();
        const existing = openedWindows.get(page.path);
        if (existing) { existing.focus(); return; }
        const successful = openOne(page.path);
        render(successful ? "One tab opened. Return to this setup tab to continue; use the listed opening order." : blockedMessage(), !successful);
      });
      item.appendChild(link);
      links.appendChild(item);
    });
  }
  function selectionChanged() {
    render("Click OPEN ALL TABS after allowing pop-ups, or use Open next tab. Each click on Open next tab opens one page; return here between clicks.", false);
  }
  setSelect.addEventListener("change", selectionChanged);
  loadSelect.addEventListener("change", selectionChanged);
  document.getElementById("setup-form").addEventListener("submit", function (event) {
    event.preventDefault();
    pruneClosedTabs();
    let blocked = false;
    for (const page of plannedPages()) {
      if (openedWindows.has(page.path)) continue;
      if (!openOne(page.path)) { blocked = true; break; }
    }
    render(blocked ? blockedMessage() : undefined, blocked);
  });
  nextButton.addEventListener("click", function () {
    pruneClosedTabs();
    const page = plannedPages().find(function (candidate) { return !openedWindows.has(candidate.path); });
    if (!page) return render();
    const successful = openOne(page.path);
    render(successful ? "One tab opened. Return to this setup tab and click Open next tab again. Continue until the counter is complete." : blockedMessage(), !successful);
  });
  resetButton.addEventListener("click", function () {
    openedWindows.forEach(function (handle) { if (!handle.closed) handle.close(); });
    openedWindows.clear();
    popupHelp.open = false;
    render("Study tabs opened by this page have been closed. Choose a set and load for a new block. If this page was refreshed earlier, close any leftover study tabs manually.", false);
  });
  window.addEventListener("focus", function () { render(); });
  render("Click OPEN ALL TABS after allowing pop-ups, or use Open next tab. Return to this setup tab between individual openings.", false);
})();
