(function () {
  const style = document.createElement("style");
  style.textContent = [
    ".ai-mode-badge{display:inline-flex;align-items:center;font-size:0.72rem;font-weight:700;letter-spacing:0.01em;padding:2px 8px;border-radius:999px;line-height:1.45;}",
    ".ai-mode-badge.is-live{background:#ecfdf5;color:#047857;border:1px solid #a7f3d0;}",
    ".ai-mode-badge.is-demo{background:#f8fafc;color:#475569;border:1px solid #e2e8f0;}",
    ".ai-mode-notice{font-size:0.82rem;color:#92400e;margin-top:0.6rem;}",
    "nav .ai-mode-badge.is-demo{background:rgba(255,255,255,0.16);color:#fff;border-color:transparent;}",
    "nav .ai-mode-badge.is-live{background:#ecfdf5;color:#047857;border-color:transparent;}",
  ].join("");
  document.head.appendChild(style);

  function applyBadge(el, data) {
    if (!el) return;
    const live = !!(data && data.ai_mode === "live");
    el.hidden = false;
    el.textContent = live ? "Live AI" : "Demo output";
    el.className = "ai-mode-badge " + (live ? "is-live" : "is-demo");
  }

  function applyNotice(el, data) {
    if (!el) return;
    const notice = data && data.notice ? String(data.notice) : "";
    el.hidden = !notice;
    el.textContent = notice;
  }

  window.KeyProse = { applyBadge, applyNotice };
})();
