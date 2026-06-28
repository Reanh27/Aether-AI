// Global helpers + mobile sidebar toggle + dark mode
document.addEventListener("DOMContentLoaded", () => {
  // Auto-dismiss flash messages
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity .4s, transform .4s";
      el.style.opacity = "0";
      el.style.transform = "translateY(-8px)";
    }, 4000);
    setTimeout(() => el.remove(), 4500);
  });

  // ---------- Dark mode toggle ----------
  const themeToggle = document.getElementById("theme-toggle");
  themeToggle?.addEventListener("click", () => {
    const root = document.documentElement;
    const current = root.getAttribute("data-theme") || "light";
    const next = current === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    localStorage.setItem("aether-theme", next);
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", next === "dark" ? "#0b1020" : "#f97316");
  });
  (function syncThemeMeta() {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", current === "dark" ? "#0b1020" : "#f97316");
  })();

  // ---------- Mobile sidebar toggle ----------
  const sidebar = document.getElementById("sidebar");
  const hamburger = document.getElementById("hamburger");
  const backdrop = document.getElementById("sidebar-backdrop");

  function openSidebar() {
    sidebar?.classList.add("open");
    backdrop?.classList.add("open");
    document.body.style.overflow = "hidden";
  }
  function closeSidebar() {
    sidebar?.classList.remove("open");
    backdrop?.classList.remove("open");
    document.body.style.overflow = "";
  }
  hamburger?.addEventListener("click", openSidebar);
  backdrop?.addEventListener("click", closeSidebar);

  sidebar?.querySelectorAll(".side-nav a, .side-logout").forEach((link) => {
    link.addEventListener("click", () => {
      if (window.innerWidth < 900) closeSidebar();
    });
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeSidebar();
  });

  // ---------- Auto-grow textareas ----------
  document.querySelectorAll("textarea.input, textarea.textarea").forEach((ta) => {
    const grow = () => {
      ta.style.height = "auto";
      ta.style.height = ta.scrollHeight + "px";
    };
    ta.addEventListener("input", grow);
  });
});
 
  // ---------- Password show/hide toggle (clean SVG icons) ----------
  const EYE = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>`;
  const EYE_OFF = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" y1="2" x2="22" y2="22"/></svg>`;

  document.querySelectorAll('input[type="password"]').forEach((input) => {
    if (input.parentElement.classList.contains("password-wrap")) return;
    const wrap = document.createElement("div");
    wrap.className = "password-wrap";
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "password-toggle";
    btn.setAttribute("aria-label", "Show password");
    btn.innerHTML = EYE;
    btn.addEventListener("click", () => {
      const isHidden = input.type === "password";
      input.type = isHidden ? "text" : "password";
      btn.innerHTML = isHidden ? EYE_OFF : EYE;
      btn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
    });
    wrap.appendChild(btn);
  });
