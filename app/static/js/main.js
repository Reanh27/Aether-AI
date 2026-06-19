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

// ---------- Password show/hide toggle ----------
document.querySelectorAll('input[type="password"]').forEach((input) => {
  // Skip if already wrapped
  if (input.parentElement.classList.contains("password-wrap")) return;

  // Wrap the input in a relative container
  const wrap = document.createElement("div");
  wrap.className = "password-wrap";
  input.parentNode.insertBefore(wrap, input);
  wrap.appendChild(input);

  // Create the eye toggle button
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "password-toggle";
  btn.setAttribute("aria-label", "Show password");
  btn.innerHTML = "👁";
  btn.addEventListener("click", () => {
    const isHidden = input.type === "password";
    input.type = isHidden ? "text" : "password";
    btn.innerHTML = isHidden ? "🙈" : "👁";
    btn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
  });
  wrap.appendChild(btn);
});