"""
post_linkedin.py — Publishes post.txt (plus an optional image) to LinkedIn.

Built to fail loudly and clearly:
  * checks the access token before doing anything else
  * works out the correct author ID itself whenever LinkedIn allows it
  * falls back to a text-only post if the image upload has a problem
  * writes a plain-English explanation to failure_reason.md when it cannot post

Set DRY_RUN=true to run every check without publishing anything.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://api.linkedin.com/v2"
MAX_CHARS = 3000
TOKEN_HELP = (
    "Your LinkedIn access token has expired or is not valid. LinkedIn tokens "
    "only last about 60 days, so this needs doing every two months.\n\n"
    "**How to fix (5 minutes):**\n"
    "1. Open https://www.linkedin.com/developers/tools/oauth/token-generator\n"
    "2. Pick your app, tick `openid`, `profile` and `w_member_social`, "
    "then click **Request access token** and copy the token.\n"
    "3. In this repository go to **Settings → Secrets and variables → Actions**, "
    "open `LINKEDIN_ACCESS_TOKEN`, paste the new token and save.\n"
    "4. Go to the **Actions** tab → **Daily AI News to LinkedIn** → "
    "**Run workflow** to test it.\n"
)


def fail(summary, details=""):
    """Record a human-readable reason, log it, and stop with an error."""
    print(f"\n❌ {summary}\n{details}")
    Path("failure_reason.md").write_text(f"### {summary}\n\n{details}\n", encoding="utf-8")
    log(False, error=summary)
    sys.exit(1)


def log(success, post_id=None, error=None, chars=0):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "success": success,
        "post_id": post_id,
        "chars": chars,
        "error": error,
    }
    log_file = Path("post_log.json")
    history = []
    if log_file.exists():
        try:
            history = json.loads(log_file.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            history = []
    history.append(entry)
    log_file.write_text(json.dumps(history[-60:], indent=2), encoding="utf-8")


def headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def normalise_urn(value):
    """Accept 'abc123', 'person:abc123' or a full URN and return a full URN."""
    value = (value or "").strip().strip('"').strip("'")
    if not value:
        return ""
    if value.startswith("urn:li:"):
        return value
    return f"urn:li:person:{value.split(':')[-1]}"


def resolve_author(token, configured_id):
    """
    Ask LinkedIn who owns the token. This both validates the token and gives
    the exact author ID, so a mistyped LINKEDIN_PERSON_ID secret cannot break posting.
    """
    for path, key in (("/userinfo", "sub"), ("/me", "id")):
        try:
            r = requests.get(f"{API}{path}", headers={"Authorization": f"Bearer {token}"}, timeout=30)
        except requests.RequestException as e:
            print(f"⚠️ Could not reach LinkedIn ({path}): {e}")
            continue
        if r.status_code == 401:
            fail("LinkedIn rejected the access token", TOKEN_HELP)
        if r.status_code == 200 and r.json().get(key):
            urn = f"urn:li:person:{r.json()[key]}"
            print("✅ Token is valid — author ID confirmed by LinkedIn")
            return urn
        print(f"ℹ️ {path} returned {r.status_code} (token lacks the profile permission)")

    urn = normalise_urn(configured_id)
    if not urn:
        fail(
            "LinkedIn author ID is unknown",
            "The token does not include the `openid` + `profile` permissions and the "
            "`LINKEDIN_PERSON_ID` secret is empty.\n\n" + TOKEN_HELP,
        )
    print("ℹ️ Using the LINKEDIN_PERSON_ID secret as the author")
    return urn


def upload_image(token, owner_urn, path):
    """Upload one PNG/JPG and return its asset URN, or None if anything goes wrong."""
    p = Path(path)
    ext = p.suffix.lower()
    if not p.exists() or ext not in (".png", ".jpg", ".jpeg"):
        print(f"⚠️ Skipping unsupported or missing image: {path}")
        return None
    try:
        reg = requests.post(
            f"{API}/assets?action=registerUpload",
            headers=headers(token),
            json={
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": owner_urn,
                    "serviceRelationships": [
                        {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
                    ],
                }
            },
            timeout=30,
        )
        if reg.status_code != 200:
            print(f"⚠️ Image registration failed {reg.status_code}: {reg.text[:200]}")
            return None
        value = reg.json()["value"]
        upload_url = value["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        up = requests.put(
            upload_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "image/png" if ext == ".png" else "image/jpeg",
            },
            data=p.read_bytes(),
            timeout=60,
        )
        if up.status_code in (200, 201):
            print(f"✅ Image uploaded: {p.name}")
            return value["asset"]
        print(f"⚠️ Image upload failed {up.status_code}")
    except (requests.RequestException, KeyError, ValueError) as e:
        print(f"⚠️ Image upload error: {e}")
    return None


def publish(token, author_urn, text, assets):
    content = {
        "shareCommentary": {"text": text},
        "shareMediaCategory": "IMAGE" if assets else "NONE",
    }
    if assets:
        content["media"] = [
            {
                "status": "READY",
                "description": {"text": "Top AI news of the day"},
                "media": a,
                "title": {"text": "Top AI News"},
            }
            for a in assets
        ]
    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": content},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    return requests.post(f"{API}/ugcPosts", headers=headers(token), json=payload, timeout=30)


def explain(resp):
    """Turn a LinkedIn error response into advice a non-developer can follow."""
    body = resp.text[:400]
    if resp.status_code == 401:
        return "LinkedIn rejected the access token", TOKEN_HELP
    if resp.status_code == 403:
        return (
            "LinkedIn says this token is not allowed to post",
            "The token is missing the `w_member_social` permission, or the author ID "
            "does not belong to the token's owner.\n\n" + TOKEN_HELP + f"\nLinkedIn said: `{body}`",
        )
    if resp.status_code == 422 and "duplicate" in body.lower():
        return "LinkedIn refused a duplicate post", "The same text was already posted recently."
    if resp.status_code == 429:
        return "LinkedIn rate limit reached", "Too many posts today. It will work again tomorrow."
    return f"LinkedIn returned error {resp.status_code}", f"LinkedIn said: `{body}`"


def main():
    dry_run = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()
    if not token:
        fail(
            "The LINKEDIN_ACCESS_TOKEN secret is missing",
            "No LinkedIn token is saved in this repository.\n\n" + TOKEN_HELP,
        )

    text = Path("post.txt").read_text(encoding="utf-8").strip()
    if not text:
        fail("The generated post is empty", "post.txt had no content.")
    if len(text) > MAX_CHARS:
        cut = text[: MAX_CHARS - 60].rfind("\n")
        text = text[:cut].rstrip() + "\n\n#AI #AINews #Tech #Innovation"
    print(f"📝 Post length: {len(text)} characters")

    author_urn = resolve_author(token, os.environ.get("LINKEDIN_PERSON_ID", ""))

    images = []
    if Path("images.json").exists():
        try:
            images = json.loads(Path("images.json").read_text()).get("images", [])
        except ValueError:
            images = []

    if dry_run:
        print("\n🧪 DRY RUN — all checks passed, nothing was published.")
        print(f"   Would post {len(text)} characters with {len(images)} image(s).")
        return

    assets = [a for a in (upload_image(token, author_urn, i) for i in images[:2]) if a]

    print("📤 Posting to LinkedIn...")
    resp = publish(token, author_urn, text, assets)
    if resp.status_code not in (200, 201) and assets:
        print(f"⚠️ Post with image failed ({resp.status_code}) — retrying as text only...")
        resp = publish(token, author_urn, text, [])

    if resp.status_code in (200, 201):
        pid = resp.headers.get("X-RestLi-Id", "unknown")
        print(f"\n✅ SUCCESS! Post ID: {pid}")
        log(True, pid, chars=len(text))
    else:
        fail(*explain(resp))


if __name__ == "__main__":
    main()
