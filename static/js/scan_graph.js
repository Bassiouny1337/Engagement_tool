(function () {
  "use strict";
  var elsEl = document.getElementById("els");
  var container = document.getElementById("graph");
  if (!elsEl || !container || typeof cytoscape === "undefined") return;

  var elements;
  try {
    elements = JSON.parse(elsEl.textContent);
  } catch (e) {
    return;
  }

  var css = getComputedStyle(document.body);
  var accent = (css.getPropertyValue("--accent") || "#2f81f7").trim();
  var green = (css.getPropertyValue("--accent-2") || "#3fb950").trim();
  var surface2 = (css.getPropertyValue("--surface-2") || "#1c2330").trim();
  var border = (css.getPropertyValue("--border") || "#30363d").trim();
  var text = (css.getPropertyValue("--text") || "#e6edf3").trim();

  var cy = cytoscape({
    container: container,
    elements: elements,
    style: [
      { selector: "node", style: {
          "label": "data(label)", "color": text, "font-size": "10px",
          "text-valign": "center", "text-halign": "center",
          "background-color": surface2, "border-width": 1, "border-color": border,
          "width": "label", "height": 22, "padding": "6px", "shape": "round-rectangle",
          "text-wrap": "none" } },
      { selector: 'node[kind="scan"]', style: {
          "background-color": accent, "color": "#fff", "font-weight": "bold" } },
      { selector: 'node[kind="host"][state="up"]', style: {
          "border-color": green, "border-width": 2 } },
      { selector: 'node[kind="service"]', style: {
          "background-color": "transparent", "border-color": accent } },
      { selector: "edge", style: {
          "width": 1, "line-color": border, "curve-style": "bezier",
          "target-arrow-shape": "none" } },
      { selector: ".faded", style: { "opacity": 0.2 } },
      { selector: ".sel", style: { "border-color": accent, "border-width": 3 } },
    ],
    layout: { name: "breadthfirst", directed: true, padding: 10, spacingFactor: 1.1 },
    wheelSensitivity: 0.2,
  });

  var rows = Array.prototype.slice.call(
    document.querySelectorAll("#svcTable tbody tr[data-host]"));
  var activeHostChip = document.getElementById("activeHost");
  var clearHost = document.getElementById("clearHost");
  var filterInput = document.getElementById("tableFilter");
  var currentHost = null;

  function applyFilters() {
    var q = (filterInput && filterInput.value || "").toLowerCase();
    rows.forEach(function (r) {
      var matchHost = !currentHost || r.getAttribute("data-host") === currentHost;
      var matchText = !q || r.textContent.toLowerCase().indexOf(q) !== -1;
      r.style.display = (matchHost && matchText) ? "" : "none";
    });
    if (activeHostChip && clearHost) {
      if (currentHost) {
        activeHostChip.textContent = "host: " + currentHost;
        activeHostChip.style.display = "";
        clearHost.style.display = "";
      } else {
        activeHostChip.style.display = "none";
        clearHost.style.display = "none";
      }
    }
  }

  cy.on("tap", 'node[kind="host"]', function (evt) {
    currentHost = evt.target.data("label");
    cy.elements().removeClass("sel");
    evt.target.addClass("sel");
    applyFilters();
  });
  cy.on("tap", function (evt) {
    if (evt.target === cy) { currentHost = null; cy.elements().removeClass("sel"); applyFilters(); }
  });
  if (clearHost) clearHost.addEventListener("click", function (e) {
    e.preventDefault(); currentHost = null; cy.elements().removeClass("sel"); applyFilters();
  });
  if (filterInput) filterInput.addEventListener("input", applyFilters);
})();
