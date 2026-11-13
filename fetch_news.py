"""
fetch_news.py — Fetches the Top 10 AI news stories into news.json.

Source 1: NewsAPI (free tier, needs NEWS_API_KEY)
Source 2: Google News RSS (no key needed) — used automatically if NewsAPI
          is unavailable or returns too few stories, so a run never ends empty.
"""
import os, json, re, html, requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

API_KEY = os.environ.get("NEWS_API_KEY", "").strip()
RSS_URL = "https://news.google.com/rss/search"
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
    "artificial intelligence OpenAI Google DeepMind",
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
    text = ((a.get("title") or "") + " " + (a.get("description") or "")).lower()
    s = 0
    for kw in ["gpt","claude","gemini","llm","openai","anthropic","deepmind","breakthrough","billion","robot","regulation","launch"]: s += 3 if kw in text else 0
    for kw in ["ai","artificial intelligence","machine learning","neural","model","chip","startup","funding"]: s += 1 if kw in text else 0
    return s

def make_article(title, description, url, source, published):
    cc = detect_country(url + " " + source.lower().replace(" ", ""))
    return {
        "title": title,
        "description": description or title,
        "url": url,
        "source": source,
        "publishedAt": published,
        "country_code": cc,
        "flag": COUNTRY_FLAGS.get(cc, "🌐"),
        "country_name": COUNTRY_NAMES.get(cc, "Global"),
        "score": score({"title": title, "description": description}),
    }


def fetch_newsapi(seen):
    if not API_KEY:
        print("ℹ️ No NEWS_API_KEY set — skipping NewsAPI")
        return []
    since = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    articles = []
    for q in QUERIES:
        try:
            r = requests.get(BASE_URL, params={"q": q, "from": since, "sortBy": "popularity", "language": "en", "pageSize": 5, "apiKey": API_KEY}, timeout=15)
            data = r.json()
            if data.get("status") != "ok":
                print(f"⚠️ NewsAPI said: {data.get('code')} — {str(data.get('message'))[:120]}")
                if data.get("code") in ("apiKeyInvalid", "apiKeyDisabled", "apiKeyExhausted", "rateLimited"):
                    break
                continue
            for a in data.get("articles", []):
                t = (a.get("title") or "").strip()
                if not t or t.lower() in seen or "[Removed]" in t or not a.get("description"):
                    continue
                seen.add(t.lower())
                articles.append(make_article(t, a["description"].strip(), a.get("url", ""), (a.get("source") or {}).get("name", ""), a.get("publishedAt", "")))
        except Exception as e:
            print(f"⚠️ NewsAPI query failed: {str(e).replace(API_KEY, '***')[:150]}")
    print(f"📰 NewsAPI: {len(articles)} stories")
    return articles


def parse_rss(xml_text, seen):
    articles = []
    for item in ET.fromstring(xml_text).iter("item"):
        raw = (item.findtext("title") or "").strip()
        src_el = item.find("source")
        source = (src_el.text or "").strip() if src_el is not None else ""
        title = raw[: -len(source) - 3].strip() if source and raw.endswith(f" - {source}") else raw
        if not title or title.lower() in seen:
            continue
        seen.add(title.lower())
        desc = re.sub(r"<[^>]+>", " ", html.unescape(item.findtext("description") or ""))
        desc = re.sub(r"\s+", " ", desc).strip()
        if desc.startswith(title):
            desc = title
        site = src_el.get("url", "") if src_el is not None else ""
        articles.append(make_article(title, desc, site or (item.findtext("link") or ""), source, item.findtext("pubDate") or ""))
    return articles


def fetch_rss(seen):
    articles = []
    for q in ["artificial intelligence when:1d", "AI model launch OR funding OR regulation when:1d"]:
        try:
            r = requests.get(RSS_URL, params={"q": q, "hl": "en-US", "gl": "US", "ceid": "US:en"}, headers={"User-Agent": "Mozilla/5.0 (news-digest)"}, timeout=20)
            r.raise_for_status()
            articles += parse_rss(r.content, seen)
        except Exception as e:
            print(f"⚠️ Google News RSS failed: {str(e)[:150]}")
    print(f"📰 Google News RSS: {len(articles)} stories")
    return articles


def fetch():
    seen = set()
    articles = fetch_newsapi(seen)
    if len(articles) < 10:
        articles += fetch_rss(seen)

    articles.sort(key=lambda x: x["score"], reverse=True)

    # Diversify countries first, then fill the remaining slots by score
    result, used = [], set()
    for a in articles:
        if a["country_code"] not in used:
            result.append(a)
            used.add(a["country_code"])
        if len(result) == 10: break
    for a in articles:
        if len(result) == 10: break
        if a not in result:
            result.append(a)

    return result[:10]

if __name__ == "__main__":
    print("🌐 Fetching global AI news...")
    news = fetch()
    if not news:
        raise SystemExit("❌ No news could be fetched from any source.")
    with open("news.json","w",encoding="utf-8") as f:
        json.dump(news, f, indent=2, ensure_ascii=False)
    print(f"✅ {len(news)} stories saved:")
    for i,a in enumerate(news,1):
        print(f"  {i}. {a['flag']} [{a['country_name']}] {a['title'][:65]}...")
