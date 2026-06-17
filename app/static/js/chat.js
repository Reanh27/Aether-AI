// Chat send → POST to /chat/<id>/send
(function () {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const win = document.getElementById("chat-window");
  if (!form || !win) return;
  const sessionId = win.dataset.sessionId;
  if (!sessionId) return;

  function addMsg(role, text, isHtml) {
    const empty = win.querySelector(".empty-chat");
    if (empty) empty.remove();
    const div = document.createElement("div");
    div.className = "msg msg-" + role;
    if (isHtml) {
      div.innerHTML = text;
    } else {
      div.textContent = text;
    }
    win.appendChild(div);
    win.scrollTop = win.scrollHeight;
    return div;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    addMsg("user", message, false);
    input.value = "";
    const thinking = addMsg("assistant", "<em>…thinking</em>", true);
    try {
      const res = await fetch(`/chat/${sessionId}/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      thinking.innerHTML = data.reply_html || data.reply || "(no reply)";
      if (data.title) {
        const activeLink = document.querySelector(".chat-list li.active a");
        if (activeLink) {
          const ico = activeLink.querySelector(".ico");
          activeLink.textContent = " " + data.title;
          if (ico) activeLink.prepend(ico);
        }
      }
    } catch (err) {
      thinking.innerHTML = "<em>Error contacting AI service.</em>";
    }
    win.scrollTop = win.scrollHeight;
  });
})();