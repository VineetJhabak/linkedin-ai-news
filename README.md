# 🤖 LinkedIn AI News Auto-Poster — 100% FREE FOREVER

Fully automated LinkedIn posting: **Top 10 AI news from around the world, every day at 6:00 AM IST.**  
Country flags 🏳️, emoji ✨, AI-written content, contextual images — **zero cost, zero maintenance.**

---

## 💸 Total Monthly Cost: $0.00

| Service | Free Limit | You Use | Cost |
|---|---|---|---|
| **Google Gemini 2.5 Flash** | 250 req/day | 1/day | **FREE** |
| **Groq Llama 3.3 70B** | ~14,400 req/day | backup only | **FREE** |
| **NewsAPI** | 100 req/day | 6/day | **FREE** |
| **Unsplash Source API** | Unlimited | 2/day | **FREE** |
| **GitHub Actions** | 2,000 min/month | ~15 min/day | **FREE** |
| **LinkedIn API** | Unlimited posts | 1/day | **FREE** |
| **TOTAL** | | | **$0.00/month** |

---

## 📁 Files

```
├── .github/workflows/post-ai-news.yml   ← Scheduler (6 AM IST daily)
├── scripts/
│   ├── fetch_news.py       ← NewsAPI → news.json
│   ├── generate_post.py    ← Gemini/Groq → post.txt
│   ├── generate_image.py   ← Unsplash/SVG → image files
│   └── post_linkedin.py    ← Posts to LinkedIn
├── requirements.txt
└── README.md
```

---

## ⚡ Setup in 15 Minutes

### 1. Get Free API Keys (no credit card on any of these)

**Gemini API** (primary AI — best quality, free)
→ Go to https://aistudio.google.com/app/apikey
→ Sign in with Google → Create API key → Copy it

**Groq API** (backup AI — ultra fast, free)
→ Go to https://console.groq.com
→ Sign up → API Keys → Create → Copy it

**NewsAPI** (news source, free)
→ Go to https://newsapi.org
→ Get API Key → Sign up free → Copy it

**LinkedIn Access Token + Person ID**
→ Go to https://www.linkedin.com/developers/
→ Create App → Auth tab → add scope: `w_member_social`, `r_liteprofile`
→ Use Token Generator: https://www.linkedin.com/developers/tools/oauth/token-generator
→ Copy the Access Token

→ Get your Person ID:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.linkedin.com/v2/me
# Find "id" field in the JSON response
```

---

### 2. Fork This Repo & Add Secrets

Fork this repo on GitHub, then:
**Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Where to get it |
|---|---|
| `GEMINI_API_KEY` | aistudio.google.com/app/apikey |
| `GROQ_API_KEY` | console.groq.com (optional backup) |
| `NEWS_API_KEY` | newsapi.org |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn Developer tools |
| `LINKEDIN_PERSON_ID` | From the `/v2/me` API call above |

---

### 3. Enable GitHub Actions

1. Click the **Actions** tab in your repo
2. Click **"Enable workflows"**
3. Click **post-ai-news** → **Run workflow** → **Run workflow** ← test it now!
4. Check your LinkedIn profile — post should appear within 2 minutes ✅

---

## ⏰ Schedule

The cron `30 0 * * *` means **00:30 UTC = 6:00 AM IST**, daily, forever.

To change time, edit `.github/workflows/post-ai-news.yml`:
```yaml
- cron: '30 0 * * *'   # 6:00 AM IST
- cron: '30 2 * * *'   # 8:00 AM IST  
- cron: '0 3 * * *'    # 8:30 AM IST
```
Use https://crontab.guru to calculate UTC from your timezone.

---

## 🔄 LinkedIn Token Refresh (Every 60 Days)

LinkedIn tokens expire in 60 days. Set a calendar reminder:
1. Go to https://www.linkedin.com/developers/tools/oauth/token-generator
2. Generate new token
3. GitHub → Settings → Secrets → Update `LINKEDIN_ACCESS_TOKEN`

Takes 2 minutes. Everything else runs forever.

---

## 🤖 How the AI Works (Free Stack)

```
6:00 AM IST trigger (GitHub Actions)
        ↓
fetch_news.py — calls NewsAPI (free) for 10 global AI stories
        ↓
generate_post.py — calls Gemini 2.5 Flash (free) to write viral LinkedIn post
        ↓ (if Gemini fails)
              → falls back to Groq Llama 3.3 70B (free)
        ↓
generate_image.py — fetches 2 images from Unsplash (free, no key needed)
        ↓ (if Unsplash fails)
              → generates SVG infographic from news data (no API, always works)
        ↓
post_linkedin.py — posts text + images to LinkedIn API (free)
```

---

## 📊 Sample Post Format

```
🌟 TOP 10 AI NEWS FROM AROUND THE WORLD 🌍
📅 March 28, 2025
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🇺🇸 #1 — OPENAI DROPS O3 AND CHANGES EVERYTHING
🧠 [150-200 word engaging explanation — why it matters for YOU]
💡 Hot take: We're not ready for how fast science is about to move.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🇮🇳 #2 — INDIA LAUNCHES BHARATGPT FOR 1.4 BILLION PEOPLE
🙏 [150-200 word story about inclusive AI...]
💡 This is what AI for everyone actually looks like.

[... 8 more stories ...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💭 QUICK POLL — Which story matters most for YOUR career? 👇
Repost if you found this useful ♻️

#ArtificialIntelligence #AINews #MachineLearning #Innovation #TechTrends #AI2025
```

---

## 🚀 30-Day Influencer Roadmap

**Week 1-2:**
- Post goes live daily at 6 AM automatically ✅
- Reply to every comment within 2 hours (LinkedIn algorithm loves this)
- Send 20 personalized connection requests/day to AI professionals

**Week 3-4:**
- Start a LinkedIn Newsletter (subscribers get notified of every post)
- Go live once/week discussing that day's top story
- Share "my process for finding AI news" — behind-the-scenes content crushes

**LinkedIn Algorithm Tips:**
- First 90 minutes after posting = critical engagement window
- Comments > Likes in algorithm weight
- Ending with a question gets ~40% more comments
- 6 AM IST = peak for Indian + Asian professionals on morning scroll

---

## 🐛 Common Issues

**"API key not found"** → Check GitHub Secrets are set correctly (no spaces)

**"401 Unauthorized" on LinkedIn** → Token expired, refresh it at the developer tools page

**"No articles found"** → NewsAPI free tier is 100/day; check if limit hit (unlikely at 6/run)

**Post not showing** → Check `post_log.json` in your repo for the error message

**Gemini rate limit** → Free tier is 250/day; you use 1. If somehow hit, Groq backup kicks in.

---

⭐ Star this repo if it helps you become a LinkedIn AI influencer!
