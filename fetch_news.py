"""
fetch_news.py — Fetches Top 10 AI news globally (NewsAPI free tier)
Free: 100 requests/day — we use only 6 per run
"""
import os, json, requests
from datetime import datetime, timedelta

API_KEY = os.environ["NEWS_API_KEY"]
BASE_URL = "https://newsapi.org/v2/everything"

COUNTRY_FLAGS = {
    "us":"🇺🇸","gb":"🇬🇧","cn":"🇨🇳","de":"🇩🇪","jp":"🇯🇵","in":"🇮🇳",
    "fr":"🇫🇷","kr":"🇰🇷","ca":"🇨🇦","au":"🇦🇺","sg":"🇸🇬","br":"🇧🇷",
    "nl":"🇳🇱","se":"🇸🇪","il":"🇮🇱","ae":"🇦🇪","it":"🇮🇹","es":"🇪🇸",
}
COUNTRY_NAMES = {
    "us":"USA","gb":"UK","cn":"China","de":"Germany","jp":"Japan","in":"India",
    "fr":"France","kr":"South Korea","ca":"Canada","au":"Australia","sg":"Singapore",
    "br":"Brazil","nl":"Netherlands","se":"Sweden","il":"Israel","ae":"UAE",
}

QUERIES = [
    "artificial intelligence OpenAI Google DeepMind 2025",
    "AI model release machine learning breakthrough",
    "AI regulation policy chip semiconductor",
    "robotics generative AI startup funding",
    "AI healthcare education research",
    "large language model neural network latest",
]

def detect_country(url):
    u = url.lower()
    if any(x in u for x in [".co.uk","bbc.","guardian","telegraph"]): return "gb"
    if any(x in u for x in ["techcrunch","wired","venturebeat","theverge","wsj","nytimes","washingtonpost","bloomberg","cnn","forbes","businessinsider"]): return "us"
    if any(x in u for x in [".de","spiegel","heise","golem"]): return "de"
    if any(x in u for x in [".jp","nikkei","japantimes","asahi"]): return "jp"
    if any(x in u for x in [".cn","xinhua","scmp","globaltimes"]): return "cn"
    if any(x in u for x in [".in","hindustantimes","thehindu","ndtv","economictimes","livemint"]): return "in"
    if any(x in u for x in ["lemonde",".fr","lefigaro","bfmtv"]): return "fr"
    if any(x in u for x in [".kr","koreaherald","koreatimes"]): return "kr"
    if any(x in u for x in [".ca","globemail","cbc","nationalpost"]): return "ca"
    if any(x in u for x in [".au","abc.net","smh","theage"]): return "au"
    if any(x in u for x in [".sg","straitstimes","channelnewsasia"]): return "sg"
    if any(x in u for x in [".br","folha","estadao","globo"]): return "br"
    return "us"

def score(a):
    text = (a.get("title","") + " " + a.get("description","")).lower()
    s = 0
    for kw in ["gpt","claude","gemini","llm","openai","anthropic","deepmind","breakthrough","billion","robot","regulation","launch"]: s += 3 if kw in text else 0
    for kw in ["ai","artificial intelligence","machine learning","neural","model","chip","startup","funding"]: s += 1 if kw in text else 0
    return s

def fetch():
    yesterday = (datetime.now()-timedelta(days=1)).strftime("%Y-%m-%d")
    seen, articles = set(), []

    for q in QUERIES:
        try:
            r = requests.get(BASE_URL, params={"q":q,"from":yesterday,"sortBy":"popularity","language":"en","pageSize":5,"apiKey":API_KEY}, timeout=10)
            for a in r.json().get("articles",[]):
                t = a.get("title","")
                if not t or t in seen or "[Removed]" in t or not a.get("description"): continue
                seen.add(t)
                cc = detect_country(a.get("url",""))
                articles.append({
                    "title": t,
                    "description": a.get("description",""),
                    "url": a.get("url",""),
                    "source": a.get("source",{}).get("name",""),
                    "publishedAt": a.get("publishedAt",""),
                    "country_code": cc,
                    "flag": COUNTRY_FLAGS.get(cc,"🌐"),
                    "country_name": COUNTRY_NAMES.get(cc,"Global"),
                    "score": score(a),
                })
        except Exception as e:
            print(f"⚠️ Query failed: {e}")

    articles.sort(key=lambda x: x["score"], reverse=True)
    
    # Diversify countries
    result, used = [], set()
    for a in articles:
        if a["country_code"] not in used:
            result.append(a)
            used.add(a["country_code"])
        if len(result) == 10: break
    
    # Fill remaining slots if < 10
    for a in articles:
        if a not in result:
            result.append(a)
        if len(result) == 10: break

    return result[:10]

if __name__ == "__main__":
    print("🌐 Fetching global AI news...")
    news = fetch()
    with open("news.json","w",encoding="utf-8") as f:
        json.dump(news, f, indent=2, ensure_ascii=False)
    print(f"✅ {len(news)} stories saved:")
    for i,a in enumerate(news,1):
        print(f"  {i}. {a['flag']} [{a['country_name']}] {a['title'][:65]}...")
