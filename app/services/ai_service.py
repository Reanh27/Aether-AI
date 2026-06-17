"""AI gateway — Groq first, Gemini fallback, mock last."""
import json
import random
import re
from flask import current_app
from . import wiki

SYSTEM_TUTOR = (
    "You are Aether AI, a friendly and rigorous study tutor. "
    "Always answer clearly, structure with short paragraphs and bullet lists "
    "where useful, and use Markdown (headings, bold, bullet points, code). "
    "Be accurate and concise. If you are unsure, say so."
)


def _provider():
    pref = (current_app.config.get("AI_PROVIDER") or "groq").lower()
    has_groq = bool(current_app.config.get("GROQ_API_KEY"))
    has_gem = bool(current_app.config.get("GEMINI_API_KEY"))
    if pref == "groq" and has_groq:
        return "groq"
    if pref == "gemini" and has_gem:
        return "gemini"
    if has_groq:
        return "groq"
    if has_gem:
        return "gemini"
    return "mock"


def _groq_ask(prompt, system=SYSTEM_TUTOR, history=None):
    from groq import Groq
    client = Groq(api_key=current_app.config["GROQ_API_KEY"])
    msgs = [{"role": "system", "content": system}]
    if history:
        msgs.extend(history)
    msgs.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model=current_app.config["GROQ_MODEL"],
        messages=msgs,
        temperature=0.7,
    )
    return (resp.choices[0].message.content or "").strip()


def _gemini_ask(prompt, system=SYSTEM_TUTOR, history=None):
    import google.generativeai as genai
    genai.configure(api_key=current_app.config["GEMINI_API_KEY"])
    model = genai.GenerativeModel(current_app.config["GEMINI_MODEL"],
                                  system_instruction=system)
    if history:
        gem_hist = [{"role": "user" if m["role"] == "user" else "model",
                     "parts": [m["content"]]} for m in history]
        chat = model.start_chat(history=gem_hist)
        resp = chat.send_message(prompt)
    else:
        resp = model.generate_content(prompt)
    return (resp.text or "").strip()


def _ask(prompt, system=SYSTEM_TUTOR, history=None):
    p = _provider()
    last_err = None
    for backend in [p, "gemini", "groq"]:
        if backend == "groq" and current_app.config.get("GROQ_API_KEY"):
            try:
                return _groq_ask(prompt, system, history)
            except Exception as e:
                last_err = e
        elif backend == "gemini" and current_app.config.get("GEMINI_API_KEY"):
            try:
                return _gemini_ask(prompt, system, history)
            except Exception as e:
                last_err = e
        else:
            continue
    if last_err:
        raise last_err
    return None


def _strip_fences(text):
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t)
    return t.strip()


def _parse_json_array(text):
    try:
        return json.loads(_strip_fences(text))
    except Exception:
        m = re.search(r"\[.*\]", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return None


def summarize(text):
    try:
        out = _ask(
            "Summarize the following study material in a neat, point-wise "
            "Markdown summary.\n\n"
            "Required format:\n"
            "## Overview\n"
            "1-2 sentence overview.\n\n"
            "## Key Points\n"
            "- bullet\n- bullet (5-8 bullets total)\n\n"
            "## Important Terms\n"
            "- **Term** — short definition\n\n"
            "Source text:\n" + text)
        if out:
            return out
    except Exception as e:
        return f"_(AI error: {e})_"
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    bullets = sentences[:5] if len(sentences) >= 5 else sentences
    return ("## Summary (offline)\n\n"
            + "\n".join(f"- {s}" for s in bullets if s))


def chat_reply(user_message, history):
    augmented = user_message
    if _looks_factual(user_message):
        ctx = wiki.context_for(user_message, max_chars=1500)
        if ctx:
            augmented = (
                f"Use the following Wikipedia context to ground your answer. "
                f"Don't quote it verbatim — explain in your own words and add "
                f"examples.\n\n---WIKIPEDIA---\n{ctx}\n---END---\n\n"
                f"User question: {user_message}")
    try:
        out = _ask(augmented, history=history)
        if out:
            return out
    except Exception as e:
        return f"_(AI service error: {e}.)_ Try again in a moment."
    return (f"_(mock reply)_\n\nYou asked: **{user_message}**\n\n"
            "Set `AI_PROVIDER=groq` and `GROQ_API_KEY` in `.env` for real answers.")


def generate_flashcards(topic_or_text, n=6):
    source_text = topic_or_text
    if len(topic_or_text) < 120:
        ctx = wiki.context_for(topic_or_text, max_chars=2500)
        if ctx:
            source_text = ctx
    try:
        raw = _ask(
            f"Create exactly {n} high-quality flashcards from the material below. "
            f"Each flashcard must test a different concept. "
            f"Answers should be 1-2 sentences. "
            f'Return ONLY a JSON array like '
            f'[{{"question":"...","answer":"..."}}]. '
            f"No markdown, no commentary, no fences.\n\n"
            f"Material:\n{source_text}",
            system="You write study flashcards. Output strict JSON only.")
        data = _parse_json_array(raw) if raw else None
        if data:
            return data[:n]
    except Exception:
        pass
    return [{"question": f"Sample Q{i} about {topic_or_text[:40]}?",
             "answer": f"Sample answer {i}."} for i in range(1, n + 1)]


def generate_quiz(topic, n=5, difficulty="medium"):
    """Generates MCQs grounded with Wikipedia context."""
    ctx = wiki.context_for(topic, max_chars=2500)
    extra = f"\n\nReference material:\n{ctx}" if ctx else ""
    diff_hint = {
        "easy":   "Questions should be straightforward and test core definitions.",
        "medium": "Questions should test understanding, not just recall.",
        "hard":   "Questions should test deep reasoning, edge cases, and application.",
    }.get(difficulty, "")
    try:
        raw = _ask(
            f"Create exactly {n} multiple-choice questions about '{topic}'. "
            f"{diff_hint} "
            f"Each question must have 4 plausible options and ONE correct answer. "
            f"Also include a short 1-sentence 'explanation' field for each. "
            f'Return ONLY a JSON array like '
            f'[{{"question":"...","options":["a","b","c","d"],'
            f'"correct_index":0,"explanation":"..."}}]. '
            f"No markdown, no commentary, no fences.{extra}",
            system="You write multiple-choice quiz questions. Output strict JSON only.")
        data = _parse_json_array(raw) if raw else None
        if data:
            cleaned = []
            for q in data[:n]:
                opts = q.get("options") or []
                if len(opts) >= 4 and isinstance(q.get("correct_index"), int):
                    cleaned.append({
                        "question": q.get("question", "Question?"),
                        "options": opts[:4],
                        "correct_index": max(0, min(3, q["correct_index"])),
                        "explanation": q.get("explanation", ""),
                    })
            if cleaned:
                return cleaned
    except Exception:
        pass
    questions = []
    for i in range(1, n + 1):
        correct = random.randint(0, 3)
        opts = [f"Option {chr(65+j)} about {topic}" for j in range(4)]
        opts[correct] = f"Correct fact about {topic} (#{i})"
        questions.append({"question": f"Sample question {i} about {topic}?",
                          "options": opts, "correct_index": correct,
                          "explanation": ""})
    return questions


def generate_plan(goal, days=7):
    ctx = wiki.context_for(goal, max_chars=2000)
    extra = f"\n\nBackground reference:\n{ctx}" if ctx else ""
    try:
        raw = _ask(
            f"Create a focused, practical {days}-day study plan for the goal: "
            f"'{goal}'. Each day must have a specific topic (not generic) and "
            f"actionable detail (1-2 concrete tasks). Progress from basics to advanced. "
            f'Return ONLY a JSON array like '
            f'[{{"day":"Day 1","topic":"...","detail":"..."}}]. '
            f"No markdown, no commentary, no fences.{extra}",
            system="You build clear day-by-day study plans. Output strict JSON only.")
        data = _parse_json_array(raw) if raw else None
        if data:
            return data[:days]
    except Exception:
        pass
    return [{"day": f"Day {i}",
             "topic": f"{goal} — part {i}",
             "detail": f"Study the basics for day {i}. Take notes and try 5 practice questions."}
            for i in range(1, days + 1)]


def _looks_factual(question):
    q = question.lower().strip()
    if len(q) < 5:
        return False
    triggers = ["what is", "what are", "who is", "who was", "who were",
                "when did", "when was", "where is", "where was",
                "explain", "define", "history of", "tell me about",
                "describe", "how does", "how do", "why does", "why did",
                "summary of", "summarise", "summarize"]
    return any(t in q for t in triggers)