"""Remove all chat-related blocks from styles.css"""
import re

PATH = "app/static/css/styles.css"

with open(PATH, "r", encoding="utf-8") as f:
    css = f.read()

kill = [
    r"\.aichat", r"\.bubble", r"\.thinking-dots",
    r"\.cg-sidebar", r"\.cg-main", r"\.cg-msg", r"\.cg-window",
    r"\.cg-welcome", r"\.cg-form", r"\.cg-input", r"\.cg-send",
    r"\.cg-list", r"\.cg-item", r"\.cg-icon-btn", r"\.cg-action",
    r"\.cg-new", r"\.cg-history", r"\.cg-group", r"\.cg-suggest",
    r"\.chatgpt-layout",
]

def strip(text):
    out, i, n = [], 0, len(text)
    while i < n:
        brace = text.find("{", i)
        if brace == -1:
            out.append(text[i:]); break
        sel = text[i:brace]
        depth, j = 1, brace + 1
        while j < n and depth > 0:
            if text[j] == "{": depth += 1
            elif text[j] == "}": depth -= 1
            j += 1
        block = text[i:j]
        skip = any(re.search(p + r"(\s|[,{:.\[])", sel) for p in kill)
        if not skip and "@media" in sel:
            inner = text[brace+1:j-1]
            cleaned = strip(inner)
            if cleaned.strip():
                out.append(sel + "{" + cleaned + "}")
        elif not skip:
            out.append(block)
        i = j
    return "".join(out)

cleaned = strip(css)
cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(cleaned)

print(f"✅ Cleaned styles.css — removed {len(css) - len(cleaned)} chars")