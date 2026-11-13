"""
generate_post.py — Writes the LinkedIn post from news.json into post.txt.

Order of attempts (all free):
  1. Google Gemini
  2. Groq Llama
  3. A built-in template that needs no AI at all

Step 3 means this script always produces a post, even if both AI services are down.
"""

import json
import os
import re
from datetime import datetime

import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

GEMINI_MODELS = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash"]
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

MAX_CHARS = 2900  # LinkedIn's hard limit is 3000
SEP = "━━━━━━━━━━━━━━━"
DAY_EMOJIS = {
    "Monday": "💪", "Tuesday": "🔥", "Wednesday": "⚡", "Thursday": "🧠",
    "Friday": "🎉", "Saturday": "🚀", "Sunday": "🌟",
}

PROMPT_TEMPLATE = """You are a top LinkedIn AI influencer who makes AI news exciting and easy for both technical and non-technical professionals.

Today is {date}. Write a LinkedIn post covering EXACTLY these {count} AI news stories.

STORIES:
{stories}

STRICT FORMAT — follow exactly:
1. First line: "{day_emoji} TOP {count} AI NEWS FROM AROUND THE WORLD 🌍"
2. Second line: "📅 {date}"
3. Then a line containing only: {sep}
4. For EACH story, in order, no skipping:
   Line 1: [FLAG] #[NUMBER] — [PUNCHY REWRITTEN TITLE IN CAPS, max 9 words]
   Line 2: [one relevant emoji] [25-35 words: what happened and why it matters]
   Line 3: 💡 [one sharp takeaway, max 12 words]
   Line 4: {sep}
5. Ending:
   "💭 Which story matters most for YOUR career? Drop the number below 👇"
   "♻️ Repost if this was useful"
   (blank line)
   "{hashtags}"

HARD LIMIT: the whole post must be under 2600 characters. Be concise.
Only state facts found in the stories above — never invent numbers, names or quotes.
Plain text only: no asterisks, no markdown, no HTML, no links."""


def hashtags():
    year = datetime.now().year
    return f"#ArtificialIntelligence #AINews #MachineLearning #GenAI #Innovation #TechTrends #FutureOfWork #AI{year}"


def build_prompt(articles):
    now = datetime.now()
    stories = ""
    for i, a in enumerate(articles, 1):
        stories += (
            f"\n{i}. {a['flag']} [{a['country_name']}]\n"
            f"Title: {a['title']}\nContext: {a['description']}\nSource: {a['source']}\n"
        )
    return PROMPT_TEMPLATE.format(
        date=now.strftime("%B %d, %Y"),
        day_emoji=DAY_EMOJIS.get(now.strftime("%A"), "🌟"),
        count=len(articles),
        stories=stories,
        sep=SEP,
        hashtags=hashtags(),
    )


def call_gemini(prompt, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    config = {"maxOutputTokens": 8192, "temperature": 0.8}
    r = requests.post(
        url,
        headers={"x-goog-api-key": GEMINI_API_KEY},
        json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": config},
        timeout=90,
    )
    r.raise_for_status()
    parts = r.json()["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts)


def call_groq(prompt, model):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "You write concise, engaging, factual LinkedIn posts."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 2048,
            "temperature": 0.8,
        },
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def template_post(articles):
    """No-AI fallback: a clean headline digest built straight from the news data."""
    now = datetime.now()
    lines = [
        f"{DAY_EMOJIS.get(now.strftime('%A'), '🌟')} TOP {len(articles)} AI NEWS FROM AROUND THE WORLD 🌍",
        f"📅 {now.strftime('%B %d, %Y')}",
        SEP,
    ]
    for i, a in enumerate(articles, 1):
        lines.append(f"{a['flag']} #{i} — {a['title'][:140]}")
        desc = re.sub(r"\s+", " ", a.get("description", "")).strip()
        if desc and desc.lower() != a["title"].lower():
            lines.append(f"📰 {desc[:150].rstrip()}{'…' if len(desc) > 150 else ''}")
        lines.append(f"🔗 Source: {a['source']}")
        lines.append(SEP)
    lines += [
        "💭 Which story matters most for YOUR career? Drop the number below 👇",
        "♻️ Repost if this was useful",
        "",
        hashtags(),
    ]
    return "\n".join(lines)


def clean(text):
    """Strip markdown the model may have added and tidy whitespace."""
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"^#{1,6}\s+(?=\S)", "", text, flags=re.M)  # markdown headings, not hashtags
    text = re.sub(r"^```.*$", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fit(text):
    """Guarantee the post fits LinkedIn's limit by dropping whole stories from the end."""
    if len(text) <= MAX_CHARS:
        return text
    footer = "\n💭 Which story matters most for YOUR career? 👇\n♻️ Repost if this was useful\n\n" + hashtags()
    blocks = text.split(SEP)
    kept = blocks[0]
    for block in blocks[1:-1]:
        if len(kept) + len(SEP) + len(block) + len(SEP) + len(footer) > MAX_CHARS:
            break
        kept += SEP + block
    result = kept + SEP + footer
    return result if len(result) <= MAX_CHARS else text[: MAX_CHARS - len(footer)].rstrip() + footer


def looks_valid(text, articles):
    return len(text) > 400 and text.count("#1") >= 1 and len(articles) > 0


def generate(articles):
    prompt = build_prompt(articles)
    attempts = []
    if GEMINI_API_KEY:
        attempts += [("Gemini", call_gemini, m) for m in GEMINI_MODELS]
    if GROQ_API_KEY:
        attempts += [("Groq", call_groq, m) for m in GROQ_MODELS]

    for name, fn, model in attempts:
        try:
            print(f"🤖 Trying {name} ({model})...")
            text = clean(fn(prompt, model))
            if looks_valid(text, articles):
                print(f"✅ {name} wrote {len(text)} characters")
                return fit(text)
            print(f"⚠️ {name} returned an unusable answer — trying the next option")
        except Exception as e:  # any failure just moves on to the next option
            msg = str(e).replace(GEMINI_API_KEY or "\0", "***").replace(GROQ_API_KEY or "\0", "***")
            print(f"⚠️ {name} ({model}) failed: {msg[:200]}")

    print("ℹ️ No AI service available — using the built-in headline template")
    return fit(template_post(articles))


if __name__ == "__main__":
    with open("news.json", encoding="utf-8") as f:
        articles = json.load(f)
    if not articles:
        raise SystemExit("❌ news.json is empty — nothing to write about.")

    post = generate(articles)
    with open("post.txt", "w", encoding="utf-8") as f:
        f.write(post)

    print(f"\n📋 Preview ({len(post)} characters):")
    print("-" * 60)
    print(post[:700] + ("..." if len(post) > 700 else ""))
    print("-" * 60)
    print("✅ Saved to post.txt")
