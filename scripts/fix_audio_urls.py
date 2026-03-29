#!/usr/bin/env python3
"""
Update all episode HTML pages to stream MP3s directly from archive.org.
No local storage needed. Free CDN. Permanent public domain hosting.
"""
import os, re, json, urllib.request, urllib.parse
from pathlib import Path

SITE_ROOT = Path("/Users/mac1/Projects/ghostofradio")
OTR_LIB = Path("/Users/mac1/OTR_Library")

# Map show slug -> archive.org identifiers (in order of preference)
SHOW_ARCHIVE_MAP = {
    "shadow": [
        "the-shadow-radio-show-1937-1954-old-time-radio-all-available-episodes",
        "OTRR_Shadow_Singles",
    ],
    "whistler": ["OTRR_Whistler_Singles"],
    "sherlock": [
        "sherlockholmes_otr",
        "OTRR_SherlockHolmes_Singles",
    ],
    "cbs-mystery": [
        "cbsrmt-1975_2023",
        "cbs-murder-mystery-season-1-cbsrmt-1974_2023",
    ],
    "sam-spade": ["sam-spade", "OTRR_SamSpade_Singles"],
    "suspense": [
        "OTRR_Suspense_Singles_By_Year_1946",
        "OTRR_Suspense_Singles_By_Year_1949",
        "OTRR_Suspense_Singles_By_Year_1953",
        "SUSPENSE",
    ],
    "jack-benny": ["OTRR_Jack_Benny_Singles"],
    "loneranger": ["OTRR_LoneRanger_Singles"],
    "sounds-of-darkness": ["sounds-of-darkness-sa-71-03-16-098-a-friend-of-uncle-sam_202102"],
    "dragnet": ["Dragnet_OTR", "OTRR_Dragnet_Singles"],
    "x-minus-one": ["OTRR_X_Minus_One_Singles"],
    "mysterious-traveler": ["OTRR_Mysterious_Traveler_Singles"],
    "philip-marlowe": ["OTRR_PMarlowe_Singles"],
    "falcon": ["OTRR_Falcon_Singles"],
    "dark-fantasy": ["OTRR_Dark_Fantasy_Singles"],
}

def get_archive_files(identifier):
    """Get name->URL mapping for all MP3s in an archive.org collection."""
    try:
        url = f"https://archive.org/metadata/{identifier}"
        req = urllib.request.Request(url, headers={"User-Agent": "GhostOfRadio/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        files = {}
        for f in data.get("files", []):
            name = f.get("name", "")
            if name.lower().endswith(".mp3"):
                enc = urllib.parse.quote(name)
                url = f"https://archive.org/download/{identifier}/{enc}"
                files[name] = url
                # Also index by stem for fuzzy matching
                stem = Path(name).stem.lower()
                files[stem] = url
        return files
    except:
        return {}

def slugify(text):
    text = str(text).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

def find_archive_url(filename_slug, archive_files):
    """Find best match for a slug in archive files."""
    # Direct slug match
    for key, url in archive_files.items():
        key_slug = slugify(Path(key).stem)
        if key_slug == filename_slug or key_slug.endswith(filename_slug) or filename_slug.endswith(key_slug):
            return url
    
    # Fuzzy: find longest common substring
    best_url = None
    best_score = 0
    slug_words = set(filename_slug.replace('-', ' ').split())
    for key, url in archive_files.items():
        if not key.endswith('.mp3'):
            continue
        key_words = set(slugify(Path(key).stem).replace('-', ' ').split())
        common = len(slug_words & key_words)
        if common > best_score and common >= max(1, len(slug_words) * 0.5):
            best_score = common
            best_url = url
    return best_url

def fix_show(show_slug, identifiers):
    """Update all HTML pages for a show to use archive.org URLs."""
    blog_dir = SITE_ROOT / "blog" / show_slug
    if not blog_dir.exists():
        return 0
    
    html_files = list(blog_dir.glob("*.html"))
    if not html_files:
        return 0
    
    # Load archive files
    print(f"\n  Loading archive.org for {show_slug}...")
    archive_files = {}
    for identifier in identifiers:
        files = get_archive_files(identifier)
        if files:
            archive_files.update(files)
            print(f"    ✓ {identifier}: {len(files)//2} files")
    
    if not archive_files:
        print(f"    ⚠️ No archive files found for {show_slug}")
        return 0
    
    fixed = 0
    unfixed = 0
    for html_path in sorted(html_files):
        if html_path.name == "index.html":
            continue
        
        content = html_path.read_text(encoding="utf-8")
        
        # Find current audio src
        old_src_match = re.search(r'<source src="([^"]+)" type="audio/mpeg">', content)
        if not old_src_match:
            continue
        
        old_src = old_src_match.group(1)
        
        # Already using archive.org?
        if "archive.org" in old_src:
            fixed += 1
            continue
        
        # Get slug from current path
        ep_slug = Path(old_src).stem
        
        # Find matching archive URL
        new_url = find_archive_url(ep_slug, archive_files)
        
        if new_url:
            new_content = content.replace(
                f'<source src="{old_src}" type="audio/mpeg">',
                f'<source src="{new_url}" type="audio/mpeg">'
            ).replace(
                f'href="{old_src}" download',
                f'href="{new_url}" download'
            )
            html_path.write_text(new_content, encoding="utf-8")
            fixed += 1
        else:
            unfixed += 1
    
    print(f"    Fixed: {fixed} | Unfixed: {unfixed}")
    return fixed

def main():
    print("Ghost of Radio — Fixing audio URLs to use archive.org directly")
    total = 0
    for show_slug, identifiers in SHOW_ARCHIVE_MAP.items():
        total += fix_show(show_slug, identifiers)
    print(f"\n✅ Total pages updated: {total}")
    
    # Commit
    import subprocess
    subprocess.run(["git", "add", "-A"], cwd=SITE_ROOT, capture_output=True)
    r = subprocess.run(["git", "commit", "-m", "fix: stream audio from archive.org directly (no local storage)"], 
                      cwd=SITE_ROOT, capture_output=True, text=True)
    print(r.stdout[:200] if r.returncode == 0 else "Nothing to commit")
    subprocess.run(["git", "push", "origin", "main"], cwd=SITE_ROOT)
    print("Pushed!")

if __name__ == "__main__":
    main()
