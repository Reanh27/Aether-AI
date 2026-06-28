// Aether AI — chat (StudyFlow-style)
(function () {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const win = document.getElementById("chat-window");
  if (!form || !win || !input) return;
  const sessionId = win.dataset.sessionId;
  if (!sessionId) return;

  function autoGrow() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 160) + "px";
  }
  input.addEventListener("input", autoGrow);

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  function addBubble(role, content, isHtml) {
    const empty = win.querySelector(".aichat-empty");
    if (empty) empty.remove();
    const wrap = document.createElement("div");
    wrap.className = "bubble bubble-" + role;
    const body = document.createElement("div");
    body.className = "bubble-content";
    if (isHtml) body.innerHTML = content;
    else body.textContent = content;
    wrap.appendChild(body);
    if (role === "assistant") {
      const actions = document.createElement("div");
      actions.className = "bubble-actions";
      actions.innerHTML = `
        <button class="bubble-action copy-msg" type="button" title="Copy">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          Copy
        </button>`;
      wrap.appendChild(actions);
    }
    win.appendChild(wrap);
    win.scrollTop = win.scrollHeight;
    return wrap;
  }

  function refreshRegen() {
    win.querySelectorAll(".regen-msg").forEach((b) => b.remove());
    const asst = win.querySelectorAll(".bubble-assistant");
    const last = asst[asst.length - 1];
    if (!last) return;
    const actions = last.querySelector(".bubble-actions");
    if (!actions) return;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "bubble-action regen-msg";
    btn.title = "Regenerate";
    btn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="23 4 23 10 17 10"></polyline>
        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
      </svg>
      Regenerate`;
    actions.appendChild(btn);
  }

  document.querySelectorAll(".aichat-chip[data-prompt]").forEach((btn) => {
    btn.addEventListener("click", () => {
      input.value = btn.dataset.prompt;
      autoGrow();
      form.requestSubmit();
    });
  });

  async function send(message) {
    addBubble("user", message, false);
    const thinking = addBubble("assistant",
      '<span class="thinking-dots"><span></span><span></span><span></span></span>',
      true);
    try {
      const res = await fetch(`/chat/${sessionId}/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      const body = thinking.querySelector(".bubble-content");
      body.innerHTML = data.reply_html || data.reply || "(no reply)";
      body.dataset.raw = data.reply || "";
      if (data.title) {
        const active = document.querySelector(".aichat-item.active .aichat-item-title");
        if (active) active.textContent = data.title;
      }
    } catch (err) {
      thinking.querySelector(".bubble-content").innerHTML =
        "<em>Error contacting AI service.</em>";
    }
    refreshRegen();
    win.scrollTop = win.scrollHeight;
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const msg = input.value.trim();
    if (!msg) return;
    input.value = "";
    autoGrow();
    send(msg);
  });

  win.addEventListener("click", async (e) => {
    const copyBtn = e.target.closest(".copy-msg");
    if (copyBtn) {
      const bubble = copyBtn.closest(".bubble");
      const body = bubble.querySelector(".bubble-content");
      const text = body.dataset.raw || body.textContent;
      try {
        await navigator.clipboard.writeText(text);
        const orig = copyBtn.innerHTML;
        copyBtn.innerHTML = "✓ Copied!";
        setTimeout(() => { copyBtn.innerHTML = orig; }, 1500);
      } catch (err) { alert("Copy failed: " + err.message); }
      return;
    }
    const regenBtn = e.target.closest(".regen-msg");
    if (regenBtn) {
      const bubble = regenBtn.closest(".bubble");
      const body = bubble.querySelector(".bubble-content");
      const actions = bubble.querySelector(".bubble-actions");
      const oldHtml = body.innerHTML;
      body.innerHTML = '<span class="thinking-dots"><span></span><span></span><span></span></span>';
      if (actions) actions.style.opacity = "0";
      try {
        const res = await fetch(`/chat/${sessionId}/regenerate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        const data = await res.json();
        if (data.error) {
          body.innerHTML = oldHtml;
          alert(data.error);
        } else {
          body.innerHTML = data.reply_html || data.reply || "(no reply)";
          body.dataset.raw = data.reply || "";
        }
      } catch (err) {
        body.innerHTML = oldHtml;
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
      const item = btn.closest(".aichat-item");
      const sid = item.dataset.sessionId;
      const titleEl = item.querySelector(".aichat-item-title");
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

  // Voice input (Web Speech API)
  const mic = document.getElementById("chat-mic");
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (mic && SR) {
    const recog = new SR();
    recog.continuous = false;
    recog.interimResults = false;
    recog.lang = "en-US";
    let listening = false;
    mic.addEventListener("click", () => {
      if (listening) { recog.stop(); return; }
      try { recog.start(); listening = true; mic.classList.add("listening"); }
      catch (e) { console.warn(e); }
    });
    recog.onresult = (e) => {
      const text = e.results[0][0].transcript;
      input.value = (input.value ? input.value + " " : "") + text;
      autoGrow(); input.focus();
    };
    recog.onend = () => { listening = false; mic.classList.remove("listening"); };
    recog.onerror = () => { listening = false; mic.classList.remove("listening"); };
  } else if (mic) {
    mic.style.display = "none";
  }

  autoGrow();
  input.focus();
  win.scrollTop = win.scrollHeight;
})();