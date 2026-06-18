// Global helpers + mobile sidebar toggle
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

  // Mobile sidebar toggle
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

  // Close sidebar after clicking a link (mobile UX)
  sidebar?.querySelectorAll(".side-nav a, .side-logout").forEach((link) => {
    link.addEventListener("click", () => {
      if (window.innerWidth < 900) closeSidebar();
    });
  });

  // Close on Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeSidebar();
  });

  // Auto-grow textareas
  document.querySelectorAll("textarea.input, textarea.textarea").forEach((ta) => {
    const grow = () => {
      ta.style.height = "auto";
      ta.style.height = ta.scrollHeight + "px";
    };
    ta.addEventListener("input", grow);
  });
});