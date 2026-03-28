"""
post_linkedin.py — Posts to LinkedIn API v2. LinkedIn API is FREE to use.
Supports text post + up to 2 image attachments.
"""

import os, json, requests
from pathlib import Path
from datetime import datetime

API = "https://api.linkedin.com/v2"

def headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

def upload_image(token, person_id, path):
    """Upload image to LinkedIn and return asset URN."""
    # Register upload
    reg = requests.post(f"{API}/assets?action=registerUpload", headers=headers(token), json={
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": f"urn:li:person:{person_id}",
            "serviceRelationships": [{"relationshipType":"OWNER","identifier":"urn:li:userGeneratedContent"}]
        }
    }, timeout=30)
    
    if reg.status_code != 200:
        print(f"  ⚠️ Register failed {reg.status_code}: {reg.text[:150]}")
        return None

    upload_url = reg.json()["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset = reg.json()["value"]["asset"]

    p = Path(path)
    if not p.exists():
        print(f"  ⚠️ File not found: {path}")
        return None

    ext = p.suffix.lower()
    ct = "image/jpeg" if ext in [".jpg",".jpeg"] else "image/png" if ext==".png" else "image/svg+xml"

    with open(p,"rb") as f: data = f.read()
    up = requests.put(upload_url, headers={"Authorization":f"Bearer {token}","Content-Type":ct}, data=data, timeout=60)
    
    if up.status_code in [200,201]:
        print(f"  ✅ Uploaded: {asset}")
        return asset
    print(f"  ⚠️ Upload failed {up.status_code}")
    return None

def post(token, person_id, text, images=None):
    person_urn = f"urn:li:person:{person_id}"
    assets = []

    if images:
        print(f"📤 Uploading {len(images)} image(s)...")
        for img in images[:2]:
            a = upload_image(token, person_id, img)
            if a: assets.append(a)

    if assets:
        payload = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "IMAGE",
                    "media": [{"status":"READY","description":{"text":"AI News"},"media":a,"title":{"text":"Top 10 AI News"}} for a in assets],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
    else:
        payload = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }

    print("📤 Posting to LinkedIn...")
    return requests.post(f"{API}/ugcPosts", headers=headers(token), json=payload, timeout=30)

def log(success, post_id=None, error=None, chars=0):
    entry = {"timestamp":datetime.now().isoformat(),"success":success,"post_id":post_id,"chars":chars,"error":error}
    log_file = Path("post_log.json")
    history = []
    if log_file.exists():
        try:
            with open(log_file) as f: history = json.load(f)
        except: pass
    history.append(entry)
    with open(log_file,"w") as f: json.dump(history[-60:], f, indent=2)

if __name__ == "__main__":
    token = os.environ["LINKEDIN_ACCESS_TOKEN"]
    person_id = os.environ["LINKEDIN_PERSON_ID"].replace("urn:li:person:","")

    with open("post.txt", encoding="utf-8") as f:
        text = f.read().strip()

    # LinkedIn max 3000 chars — smart trim
    if len(text) > 3000:
        cut = text[:2950].rfind('\n')
        text = text[:cut] + "\n\n#ArtificialIntelligence #AINews #MachineLearning #Innovation #TechTrends"

    print(f"📝 Post: {len(text)} chars")

    # Load images
    imgs = []
    if Path("images.json").exists():
        with open("images.json") as f:
            imgs = [i for i in json.load(f).get("images",[]) if Path(i).exists()]
    print(f"🖼 Images: {imgs}")

    resp = post(token, person_id, text, imgs)

    if resp.status_code in [200,201]:
        pid = resp.headers.get("X-RestLi-Id","unknown")
        print(f"\n✅ SUCCESS! LinkedIn post ID: {pid}")
        print(f"   View: https://www.linkedin.com/feed/")
        log(True, pid, chars=len(text))
    else:
        err = f"{resp.status_code}: {resp.text[:400]}"
        print(f"\n❌ FAILED: {err}")
        log(False, error=err, chars=len(text))
        exit(1)
