// ChatGPT-style chat: auto-grow input, Enter-to-send, copy, regenerate, rename.
(function () {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const win = document.getElementById("chat-window");
  if (!form || !win || !input) return;
  const sessionId = win.dataset.sessionId;
  if (!sessionId) return;

  let userInitial = "U";
  const initEl = document.getElementById("cg-init");
  if (initEl) {
    try { userInitial = JSON.parse(initEl.textContent).userInitial || "U"; }
    catch (e) {}
  }

  function autoGrow() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 200) + "px";
  }
  input.addEventListener("input", autoGrow);

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  function refreshRegen() {
    win.querySelectorAll(".regen-msg").forEach((b) => b.remove());
    const assistants = win.querySelectorAll(".cg-msg-assistant");
    const last = assistants[assistants.length - 1];
    if (!last) return;
    const actions = last.querySelector(".cg-msg-actions");
    if (!actions || actions.querySelector(".regen-msg")) return;
    const btn = document.createElement("button");
    btn.className = "cg-action regen-msg";
    btn.title = "Regenerate";
    btn.textContent = "↻ Regenerate";
    actions.appendChild(btn);
  }

  function escapeHtml(s) {
    return (s || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[c]);
  }

  function addMessage(role, content, isHtml) {
    const welcome = win.querySelector(".cg-welcome");
    if (welcome) welcome.remove();
    const wrap = document.createElement("div");
    wrap.className = "cg-msg cg-msg-" + role;
    wrap.innerHTML = `
      <div class="cg-msg-avatar">${role === "user" ? escapeHtml(userInitial) : "✦"}</div>
      <div class="cg-msg-body">
        <div class="cg-msg-role">${role === "user" ? "You" : "Aether AI"}</div>
        <div class="cg-msg-content"></div>
        ${role === "assistant" ? `
          <div class="cg-msg-actions">
            <button class="cg-action copy-msg" title="Copy">📋 Copy</button>
          </div>` : ""}
      </div>`;
    const contentEl = wrap.querySelector(".cg-msg-content");
    if (isHtml) contentEl.innerHTML = content;
    else contentEl.textContent = content;
    win.appendChild(wrap);
    if (role === "assistant") refreshRegen();
    win.scrollTop = win.scrollHeight;
    return wrap;
  }

  document.querySelectorAll(".cg-suggest[data-prompt]").forEach((btn) => {
    btn.addEventListener("click", () => {
      input.value = btn.dataset.prompt;
      autoGrow();
      form.requestSubmit();
    });
  });

  async function sendMessage(message) {
    addMessage("user", message, false);
    const thinking = addMessage("assistant",
      '<span class="thinking-dots"><span></span><span></span><span></span></span>',
      true);
    try {
      const res = await fetch(`/chat/${sessionId}/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      const contentEl = thinking.querySelector(".cg-msg-content");
      contentEl.innerHTML = data.reply_html || data.reply || "(no reply)";
      contentEl.dataset.raw = data.reply || "";
      if (data.title) {
        const active = document.querySelector(".cg-item.active .cg-item-title");
        if (active) active.textContent = data.title;
      }
    } catch (err) {
      thinking.querySelector(".cg-msg-content").innerHTML =
        "<em>Error contacting AI service.</em>";
    }
    refreshRegen();
    win.scrollTop = win.scrollHeight;
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    autoGrow();
    sendMessage(message);
  });

  win.addEventListener("click", async (e) => {
    const copyBtn = e.target.closest(".copy-msg");
    if (copyBtn) {
      const content = copyBtn.closest(".cg-msg-body").querySelector(".cg-msg-content");
      const text = content.dataset.raw || content.textContent;
      try {
        await navigator.clipboard.writeText(text);
        const orig = copyBtn.textContent;
        copyBtn.textContent = "✓ Copied!";
        setTimeout(() => { copyBtn.textContent = orig; }, 1500);
      } catch (err) { alert("Copy failed: " + err.message); }
      return;
    }
    const regenBtn = e.target.closest(".regen-msg");
    if (regenBtn) {
      const msg = regenBtn.closest(".cg-msg");
      const contentEl = msg.querySelector(".cg-msg-content");
      const actions = msg.querySelector(".cg-msg-actions");
      const oldHtml = contentEl.innerHTML;
      contentEl.innerHTML = '<span class="thinking-dots"><span></span><span></span><span></span></span>';
      if (actions) actions.style.opacity = "0";
      try {
        const res = await fetch(`/chat/${sessionId}/regenerate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        const data = await res.json();
        if (data.error) {
          contentEl.innerHTML = oldHtml;
          alert(data.error);
        } else {
          contentEl.innerHTML = data.reply_html || data.reply || "(no reply)";
          contentEl.dataset.raw = data.reply || "";
        }
      } catch (err) {
        contentEl.innerHTML = oldHtml;
        alert("Regenerate failed: " + err.message);
      }
      if (actions) actions.style.opacity = "";
      win.scrollTop = win.scrollHeight;
    }
  });

  document.querySelectorAll(".rename-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const item = btn.closest(".cg-item");
      const sid = item.dataset.sessionId;
      const titleEl = item.querySelector(".cg-item-title");
      const cur = titleEl.textContent.trim();
      const next = prompt("Rename chat:", cur);
      if (next && next.trim() && next.trim() !== cur) {
        try {
          const res = await fetch(`/chat/${sid}/rename`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: next.trim() }),
          });
          const data = await res.json();
          if (data.ok) titleEl.textContent = data.title;
        } catch (err) { alert("Rename failed: " + err.message); }
      }
    });
  });

  autoGrow();
  input.focus();
  win.scrollTop = win.scrollHeight;
})();