#!/usr/bin/env python3
"""
Upload all local MP3s to Cloudflare R2, then rewrite HTML pages to use R2 URLs.
"""
import os, sys, re, boto3, subprocess
from pathlib import Path
from botocore.config import Config

CF_ACCOUNT = "dae784fdc17957e814046c3637ee10eb"
CF_TOKEN   = "cfut_F7Gk8H3OrM2QQ34UoqpRfo3F3mHuNd222p2IMdm73b91416a"
BUCKET     = "ghostofradio-audio"
PUBLIC_URL = "https://pub-43a2a91d87c649239fa207174290a900.r2.dev"

AUDIO_DIR  = Path("/Users/mac1/Projects/ghostofradio/audio")
SITE_ROOT  = Path("/Users/mac1/Projects/ghostofradio")

# R2 uses S3-compatible API
s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{CF_ACCOUNT}.r2.cloudflarestorage.com",
    aws_access_key_id=CF_TOKEN,
    aws_secret_access_key=CF_TOKEN,
    config=Config(signature_version="s3v4"),
    region_name="auto",
)

def get_existing_keys():
    """Get all keys already in the bucket."""
    existing = set()
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET):
        for obj in page.get("Contents", []):
            existing.add(obj["Key"])
    return existing

def upload_all():
    print("Scanning local audio files...")
    mp3s = list(AUDIO_DIR.rglob("*.mp3"))
    print(f"Found {len(mp3s)} MP3 files")

    print("Checking R2 for already-uploaded files...")
    try:
        existing = get_existing_keys()
        print(f"Already uploaded: {len(existing)}")
    except Exception as e:
        print(f"Warning: couldn't list bucket: {e}")
        existing = set()

    uploaded = 0
    skipped = 0
    failed = 0

    for i, mp3 in enumerate(sorted(mp3s)):
        # R2 key: show/filename.mp3
        rel = mp3.relative_to(AUDIO_DIR)
        key = str(rel)  # e.g. "sam-spade/chargogagog.mp3"

        if key in existing:
            skipped += 1
            continue

        try:
            s3.upload_file(
                str(mp3), BUCKET, key,
                ExtraArgs={"ContentType": "audio/mpeg", "CacheControl": "public, max-age=31536000"}
            )
            uploaded += 1
            if uploaded % 10 == 0 or uploaded == 1:
                print(f"  [{i+1}/{len(mp3s)}] ✓ {key}")
        except Exception as e:
            print(f"  [{i+1}] ✗ FAIL {key}: {e}")
            failed += 1

    print(f"\nUpload complete: {uploaded} uploaded, {skipped} skipped, {failed} failed")
    return uploaded + skipped

def rewrite_pages():
    """Replace archive.org and /audio/ paths with R2 URLs in all HTML pages."""
    print("\nRewriting HTML pages to use R2...")

    html_files = []
    for show_dir in AUDIO_DIR.iterdir():
        show = show_dir.name
        site_dir = SITE_ROOT / show
        if site_dir.exists():
            html_files.extend(site_dir.glob("*.html"))

    fixed = 0
    for html_path in html_files:
        if html_path.name == "index.html":
            continue
        content = html_path.read_text(encoding="utf-8")

        # Find current audio src
        src_match = re.search(r'<source src="([^"]+)" type="audio/mpeg">', content)
        dl_match  = re.search(r'href="([^"]+)" download', content)
        if not src_match:
            continue

        old_src = src_match.group(1)
        if PUBLIC_URL in old_src:
            continue  # already using R2

        # Determine show/filename from current path or archive.org URL
        # Try to extract show + filename from local /audio/ path
        local_match = re.search(r'/audio/([^/]+)/([^"]+\.mp3)', old_src)
        if local_match:
            show, fname = local_match.group(1), local_match.group(2)
        else:
            # Parse from archive.org URL — get filename
            fname = old_src.split("/")[-1].split("?")[0]
            # Infer show from page path
            show = html_path.parent.name

        # Check if file exists in R2 (by checking local audio dir)
        local_mp3 = AUDIO_DIR / show / fname
        # URL-decode fname for local check
        import urllib.parse
        decoded_fname = urllib.parse.unquote(fname)
        local_mp3_decoded = AUDIO_DIR / show / decoded_fname

        if local_mp3.exists() or local_mp3_decoded.exists():
            new_url = f"{PUBLIC_URL}/{show}/{fname}"
            new_content = content.replace(
                f'<source src="{old_src}" type="audio/mpeg">',
                f'<source src="{new_url}" type="audio/mpeg">'
            )
            if dl_match and old_src in dl_match.group(1):
                new_content = new_content.replace(
                    f'href="{old_src}" download',
                    f'href="{new_url}" download'
                )
            if new_content != content:
                html_path.write_text(new_content, encoding="utf-8")
                fixed += 1

    print(f"Rewrote {fixed} pages to use R2")
    return fixed

def commit_push():
    print("\nCommitting and pushing to GitHub...")
    subprocess.run(["git", "add", "-A"], cwd=SITE_ROOT, capture_output=True)
    r = subprocess.run(
        ["git", "commit", "-m", "feat: serve audio from Cloudflare R2 (direct hosting, no redirects)"],
        cwd=SITE_ROOT, capture_output=True, text=True
    )
    print(r.stdout[:200] if r.returncode == 0 else "Nothing new to commit")
    subprocess.run(["git", "push", "origin", "main"], cwd=SITE_ROOT)
    print("Pushed!")

if __name__ == "__main__":
    # Install boto3 if needed
    try:
        import boto3
    except ImportError:
        os.system("pip3 install boto3 --break-system-packages -q")
        import boto3

    upload_all()
    rewrite_pages()
    commit_push()
