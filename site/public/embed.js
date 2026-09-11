/**
 * Placeholder for local dev and Amplify previews.
 * Production deploys copy the built bundle from embed/dist to this path.
 */
(function auritusEmbedPlaceholder() {
  if (typeof document === "undefined") {
    return;
  }
  var script = document.currentScript;
  var marker = document.createElement("div");
  marker.setAttribute("data-auritus-placeholder", "1");
  marker.textContent =
    "Auritus embed placeholder — production uses embed/dist output.";
  marker.style.cssText =
    "margin:1rem 0;padding:0.75rem 1rem;border:1px dashed #2f6f5e;" +
    "font:600 0.9rem system-ui,sans-serif;color:#14201a;background:#f4f7f5;";
  if (script && script.parentNode) {
    script.parentNode.insertBefore(marker, script.nextSibling);
  } else {
    document.body.appendChild(marker);
  }
})();
