# LinkedIn AI News Auto-Poster

Posts the top 10 AI news stories to your LinkedIn profile every morning (around 6 AM IST), fully automatically, using only free services.

## How it works

Every day GitHub runs four small scripts in order:

| Step | File | What it does |
|---|---|---|
| 1 | `fetch_news.py` | Collects AI news from NewsAPI, with Google News as an automatic backup |
| 2 | `generate_post.py` | Writes the post with Gemini, then Groq, then a built-in template if both are down |
| 3 | `generate_image.py` | Draws a headline card image |
| 4 | `post_linkedin.py` | Checks your LinkedIn token and publishes the post |

The schedule lives in `.github/workflows/daily-ai-news.yml`.

## The one thing you must do every ~2 months

**LinkedIn access tokens expire after about 60 days.** When that happens the tool cannot post, and it opens an Issue in this repository titled *"LinkedIn auto-poster needs attention"* with these same steps:

1. Open <https://www.linkedin.com/developers/tools/oauth/token-generator>
2. Pick your app, tick `openid`, `profile` and `w_member_social`, click **Request access token**, and copy the token.
3. In this repository: **Settings → Secrets and variables → Actions → `LINKEDIN_ACCESS_TOKEN` → paste → Save**.
4. **Actions** tab → **Daily AI News to LinkedIn** → **Run workflow** to confirm it works.

Tip: tick **dry_run** in step 4 to test everything without publishing a post.

## Secrets used

Set under **Settings → Secrets and variables → Actions**.

| Secret | Needed? | Where to get it |
|---|---|---|
| `LINKEDIN_ACCESS_TOKEN` | Required | LinkedIn token generator (link above) |
| `LINKEDIN_PERSON_ID` | Optional | Only used if the token lacks the `openid` + `profile` permissions |
| `GEMINI_API_KEY` | Recommended | <https://aistudio.google.com/app/apikey> |
| `GROQ_API_KEY` | Optional backup | <https://console.groq.com> |
| `NEWS_API_KEY` | Optional | <https://newsapi.org> |

## Checking on it

- **Actions** tab: each run shows the exact post text in its summary.
- `post_log.json`: a history of the last 60 runs, updated automatically.
- **Issues** tab: anything that needs your attention appears here in plain English.

## Running on your own computer

```bash
pip install -r requirements.txt
```

```bash
python fetch_news.py && python generate_post.py && python generate_image.py
```

```bash
DRY_RUN=true LINKEDIN_ACCESS_TOKEN=your_token python post_linkedin.py
```
