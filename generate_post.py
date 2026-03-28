"""
generate_post.py — Generates viral LinkedIn post using FREE APIs only.

PRIMARY:   Google Gemini 2.5 Flash (ai.google.dev — FREE, 250 req/day, no credit card)
FALLBACK:  Groq Llama 3.3 70B      (console.groq.com — FREE, generous daily limits)

Both APIs are 100% free. No credit card. No charges ever.
Get keys at:
  Gemini: https://aistudio.google.com/app/apikey
  Groq:   https://console.groq.com
"""

import os, json, requests
from datetime import datetime

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY","")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY","")

DAY_EMOJIS = {"Monday":"💪","Tuesday":"🔥","Wednesday":"⚡","Thursday":"🧠","Friday":"🎉","Saturday":"🚀","Sunday":"🌟"}

PROMPT_TEMPLATE = """You are a top LinkedIn AI influencer known for making complex AI news exciting and accessible to both technical and non-technical professionals.

Today is {date}. Write a viral LinkedIn post featuring EXACTLY these Top 10 AI news stories from around the world.

STORIES:
{stories}

STRICT FORMAT RULES — follow exactly:
1. First line: "{day_emoji} TOP 10 AI NEWS FROM AROUND THE WORLD 🌍"
2. Second line: "📅 {date}"
3. Separator: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
4. For EACH story (all 10, no skipping):
   Line 1: [FLAG] #[NUMBER] — [PUNCHY REWRITTEN TITLE IN CAPS]
   Line 2: [relevant emoji] [100-200 word engaging explanation — why it matters, human impact, what's surprising]
   Line 3: 💡 [One sharp insight or hot take]
   Line 4: "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
5. Final section:
   "💭 QUICK POLL — Drop your number in the comments:"
   "Which story matters most for YOUR career? 👇"
   "Repost if you found this useful ♻️"
   Blank line
   "#ArtificialIntelligence #AINews #MachineLearning #Innovation #TechTrends #AI2025 #FutureOfWork #GenAI #DeepLearning #Tech"

TONE: Like a brilliant, enthusiastic friend in AI. Smart but never boring. Use emojis naturally throughout each story. Make each story feel urgent and relevant.
DO NOT use asterisks, markdown, or HTML. Write plain text only. Write ALL 10 stories completely."""


def build_prompt(articles):
    date = datetime.now().strftime("%B %d, %Y")
    day_emoji = DAY_EMOJIS.get(datetime.now().strftime("%A"), "🌟")
    stories = ""
    for i, a in enumerate(articles, 1):
        stories += f"\n{i}. {a['flag']} [{a['country_name']}]\nTitle: {a['title']}\nContext: {a['description']}\nSource: {a['source']}\n"
    return PROMPT_TEMPLATE.format(date=date, day_emoji=day_emoji, stories=stories)


def call_gemini(prompt):
    """Google Gemini 2.5 Flash — completely free (250 req/day, no card needed)."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.85}
    }
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def call_groq(prompt):
    """Groq Llama 3.3 70B — completely free, blazing fast."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a top LinkedIn AI influencer. Write viral, engaging posts."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096,
        "temperature": 0.85,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def generate(articles):
    prompt = build_prompt(articles)

    # Try Gemini first (best quality, still free)
    if GEMINI_API_KEY:
        try:
            print("🤖 Using Google Gemini 2.5 Flash (free)...")
            text = call_gemini(prompt)
            print(f"✅ Gemini generated {len(text)} chars")
            return text
        except Exception as e:
            print(f"⚠️ Gemini failed: {e} — trying Groq fallback...")

    # Fallback: Groq Llama (also free)
    if GROQ_API_KEY:
        try:
            print("🤖 Using Groq Llama 3.3 70B (free)...")
            text = call_groq(prompt)
            print(f"✅ Groq generated {len(text)} chars")
            return text
        except Exception as e:
            print(f"⚠️ Groq failed: {e}")

    raise RuntimeError("Both Gemini and Groq failed. Check your API keys in GitHub Secrets.")


if __name__ == "__main__":
    with open("news.json", encoding="utf-8") as f:
        articles = json.load(f)

    post = generate(articles)

    with open("post.txt", "w", encoding="utf-8") as f:
        f.write(post)

    print("\n📋 Preview:")
    print("-"*60)
    print(post[:600] + "...")
    print("-"*60)
    print("✅ Saved to post.txt")
