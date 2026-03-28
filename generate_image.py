"""
generate_image.py — Creates 1-2 images for LinkedIn post. 100% FREE.

Method 1: Unsplash Source API (no key, no sign-up, completely free)
Method 2: SVG infographic generated from news data (zero cost, always works)

No paid APIs. No API keys needed for images.
"""

import json, requests, os
from datetime import datetime
from pathlib import Path


def fetch_unsplash(query, idx):
    """Unsplash Source API — no API key needed, completely free."""
    # Use multiple fallback queries if first fails
    queries = [query, query.split()[0], "technology future", "artificial intelligence"]
    
    for q in queries:
        try:
            url = f"https://source.unsplash.com/1200x628/?{q.replace(' ',',')}"
            r = requests.get(url, timeout=20, allow_redirects=True)
            if r.status_code == 200 and len(r.content) > 15_000:
                fname = f"image_{idx+1}.jpg"
                with open(fname, "wb") as f:
                    f.write(r.content)
                print(f"  ✅ Unsplash image {idx+1} ({len(r.content)//1024}KB): {fname}")
                return fname
        except Exception as e:
            print(f"  ⚠️ Unsplash '{q}' failed: {e}")
    return None


def make_svg_image(articles, idx):
    """
    Generates a professional SVG infographic card — zero cost, always works.
    LinkedIn renders SVG attachments fine.
    """
    today = datetime.now().strftime("%B %d, %Y")
    
    palettes = [
        {"bg1":"#0f0c29","bg2":"#302b63","accent":"#7c3aed","accent2":"#a78bfa","bar":"#6d28d9"},
        {"bg1":"#0a192f","bg2":"#0e2a47","accent":"#06b6d4","accent2":"#67e8f9","bar":"#0891b2"},
    ]
    p = palettes[idx % len(palettes)]
    
    # Build news rows for the infographic
    news_rows = ""
    flags_and_titles = [(a["flag"], a["country_name"], a["title"][:55]+"…" if len(a["title"])>55 else a["title"]) for a in articles[:5]]
    
    y = 310
    for i, (flag, country, title) in enumerate(flags_and_titles):
        news_rows += f"""
        <rect x="60" y="{y}" width="1080" height="52" rx="6" fill="rgba(255,255,255,0.04)"/>
        <text x="80" y="{y+33}" font-family="Arial,sans-serif" font-size="22" fill="{p['accent2']}" font-weight="bold">#{i+1}</text>
        <text x="120" y="{y+33}" font-family="Arial,sans-serif" font-size="20">{flag}</text>
        <text x="155" y="{y+33}" font-family="Arial,sans-serif" font-size="16" fill="rgba(255,255,255,0.5)" font-style="italic">{country} ·</text>
        <text x="240" y="{y+33}" font-family="Arial,sans-serif" font-size="17" fill="rgba(255,255,255,0.88)">{title}</text>"""
        y += 62
    
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="1200" height="628" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{p['bg1']}"/>
      <stop offset="100%" stop-color="{p['bg2']}"/>
    </linearGradient>
    <linearGradient id="bar" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{p['accent']}"/>
      <stop offset="100%" stop-color="{p['accent2']}"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="1200" height="628" fill="url(#bg)"/>
  
  <!-- Subtle grid -->
  <g opacity="0.04" stroke="white" stroke-width="0.5">
    {''.join(f'<line x1="0" y1="{y*50}" x2="1200" y2="{y*50}"/>' for y in range(13))}
    {''.join(f'<line x1="{x*100}" y1="0" x2="{x*100}" y2="628"/>' for x in range(13))}
  </g>
  
  <!-- Top accent bar -->
  <rect x="0" y="0" width="1200" height="5" fill="url(#bar)"/>
  
  <!-- Glow circles -->
  <circle cx="150" cy="150" r="200" fill="{p['accent']}" opacity="0.06"/>
  <circle cx="1100" cy="500" r="180" fill="{p['accent2']}" opacity="0.06"/>
  
  <!-- AI Badge -->
  <rect x="60" y="52" width="148" height="38" rx="19" fill="{p['accent']}" opacity="0.85"/>
  <text x="134" y="77" text-anchor="middle" font-family="Arial,sans-serif" font-size="15" font-weight="bold" fill="white">🤖 AI NEWS</text>
  
  <!-- Main Headline -->
  <text x="60" y="175" font-family="Arial,sans-serif" font-size="52" font-weight="900" fill="white">Top 10 AI Stories</text>
  <text x="60" y="238" font-family="Arial,sans-serif" font-size="52" font-weight="900" fill="url(#bar)">From Around The World 🌍</text>
  <text x="60" y="282" font-family="Arial,sans-serif" font-size="20" fill="rgba(255,255,255,0.45)">{today}</text>
  
  <!-- News rows -->
  {news_rows}
  
  <!-- Bottom hashtags -->
  <text x="60" y="606" font-family="Arial,sans-serif" font-size="15" fill="rgba(255,255,255,0.3)">#ArtificialIntelligence  #AINews  #MachineLearning  #Innovation  #TechTrends</text>
</svg>"""

    fname = f"image_{idx+1}.svg"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"  ✅ SVG infographic {idx+1} saved: {fname}")
    return fname


def get_image_query(article):
    """Extract a simple Unsplash search query from article title."""
    title = article["title"].lower()
    if any(x in title for x in ["robot","robotics"]): return "robot technology"
    if any(x in title for x in ["chip","semiconductor","gpu","nvidia"]): return "computer chip semiconductor"
    if any(x in title for x in ["regulation","policy","law","government"]): return "government technology policy"
    if any(x in title for x in ["health","medical","medicine","drug"]): return "medical AI technology"
    if any(x in title for x in ["fund","invest","billion","startup"]): return "tech startup investment"
    if any(x in title for x in ["brain","neural","research"]): return "neural network brain technology"
    return "artificial intelligence technology future"


if __name__ == "__main__":
    with open("news.json", encoding="utf-8") as f:
        articles = json.load(f)

    images = []
    print("🖼 Generating images (free)...")

    for idx in range(2):
        query = get_image_query(articles[idx] if idx < len(articles) else articles[0])
        print(f"\n  Image {idx+1}: '{query}'")
        
        fname = fetch_unsplash(query, idx)
        if not fname:
            fname = make_svg_image(articles, idx)
        
        if fname:
            images.append(fname)

    with open("images.json","w") as f:
        json.dump({"images": images, "generated_at": datetime.now().isoformat()}, f)

    print(f"\n✅ {len(images)} image(s) ready: {images}")
