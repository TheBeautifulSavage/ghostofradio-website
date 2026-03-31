#!/usr/bin/env python3
"""
Fix dates for batch 5 shows:
- philip-marlowe → OTRR_Philip_Marlowe_Singles
- x-minus-one → OTRR_X_Minus_One_Singles
- inner-sanctum → inner-sanctum-mysteries-radio-show-1941-episodes, inner-sanctum_202108
- bob-hope → The_Bob_Hope_Program
- broadway-beat → OTRR_Broadway_Is_My_Beat_Singles
- green-hornet → GreenHornet
- our-miss-brooks → OTRR_Our_Miss_Brooks_Singles
- cisco-kid → TheCiscoKid
- cbs-mystery → cbsrmt-1975_2023
"""
import os
import re
import json
import urllib.request
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/Users/mac1/Projects/ghostofradio")

def slugify(text):
    text = str(text).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

def get_archive_metadata(identifier, retries=3):
    url = f"https://archive.org/metadata/{identifier}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "GhostOfRadio/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            result = {}
            for f in data.get("files", []):
                name = f.get("name", "")
                if name.lower().endswith(".mp3"):
                    date = f.get("date", "") or f.get("year", "")
                    title = f.get("title", "") or name
                    result[name] = {"date": date, "title": title}
            print(f"  Fetched {identifier}: {len(result)} MP3s")
            return result
        except Exception as e:
            print(f"  Error fetching {identifier} (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(5)
    return {}

def parse_date(date_str):
    """Parse a date string and return (display_str, iso_str) or (None, None)"""
    if not date_str:
        return None, None
    # Skip if just a year
    if re.match(r'^\d{4}$', date_str.strip()):
        return None, None
    # Try common formats
    formats = [
        ("%Y-%m-%d", "%B %d, %Y", "%Y-%m-%d"),
        ("%Y-%m-%dT%H:%M:%S", "%B %d, %Y", "%Y-%m-%d"),
        ("%Y/%m/%d", "%B %d, %Y", "%Y-%m-%d"),
    ]
    for fmt, disp_fmt, iso_fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip()[:10], fmt[:len(date_str.strip()[:10])])
            # Verify it's a real date
            if dt.year < 1920 or dt.year > 1990:
                continue
            display = dt.strftime(disp_fmt)
            # Remove leading zero from day
            display = re.sub(r' 0(\d),', r' \1,', display)
            iso = dt.strftime(iso_fmt)
            return display, iso
        except:
            pass
    # Try YYYY-MM-DD more carefully
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', date_str.strip())
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1920 <= y <= 1990 and 1 <= mo <= 12 and 1 <= d <= 31:
            try:
                dt = datetime(y, mo, d)
                display = dt.strftime("%B %d, %Y")
                display = re.sub(r' 0(\d),', r' \1,', display)
                return display, f"{y:04d}-{mo:02d}-{d:02d}"
            except:
                pass
    return None, None

def build_slug_map(metadata):
    """Build a map from slugified stem to (display_date, iso_date, original_name)"""
    result = {}
    for mp3_name, info in metadata.items():
        stem = Path(mp3_name).stem
        slug = slugify(stem)
        date_str = info["date"]
        display, iso = parse_date(date_str)
        if display and iso:
            result[slug] = (display, iso, mp3_name)
        # Also try the original stem without slugifying
        result[stem.lower()] = (display, iso, mp3_name) if (display and iso) else result.get(stem.lower())
    # Remove None values
    return {k: v for k, v in result.items() if v and v[0]}

def get_html_files(show_dir):
    """Get all non-index HTML files in a show directory"""
    show_path = BASE_DIR / show_dir
    files = []
    for f in sorted(show_path.glob("*.html")):
        if f.name != "index.html":
            files.append(f)
    return files

def is_vague_date(html_content, show_dir):
    """Check if the page has a vague/era date that needs updating"""
    # For x-minus-one style: episode-meta-value with era range in Air Date
    if re.search(r'episode-meta-label.*?Air Date.*?episode-meta-value.*?(\d{4})[–-]\d{4}', html_content, re.DOTALL):
        return True
    if re.search(r'<span class="episode-meta-value">NBC\s*·\s*\d{4}[–-]\d{4}</span>', html_content):
        return True
    if re.search(r'<span class="episode-meta-value">CBS\s*·\s*\d{4}[–-]\d{4}</span>', html_content):
        return True
    # For episode__network style with era range
    if re.search(r'episode__network.*?\d{4}s\b', html_content, re.DOTALL):
        return True
    # Empty datePublished
    if '"datePublished":""' in html_content:
        return True
    return False

def has_good_date(html_content):
    """Check if the page already has a specific date"""
    # Already has specific date in datePublished
    m = re.search(r'"datePublished":"(\d{4}-\d{2}-\d{2})"', html_content)
    if m:
        return True
    # Has episode-meta-value with specific date (not era range)
    m = re.search(r'Air Date.*?episode-meta-value[^>]*>([^<]+)</span>', html_content, re.DOTALL)
    if m:
        val = m.group(1).strip()
        # If it's a real date (not era range or network label)
        if re.search(r'\d{4}', val) and not re.search(r'\d{4}[–-]\d{4}', val) and not re.search(r'[A-Z]{2,}', val):
            return True
    return False

def update_xminusone_style(html_content, display_date, iso_date):
    """Update HTML with episode-meta-value Air Date and empty datePublished"""
    # Update datePublished
    html_content = re.sub(
        r'"datePublished":""',
        f'"datePublished":"{iso_date}"',
        html_content
    )
    # Update Air Date in episode-meta-value (the one right after "Air Date" label)
    # Pattern: Air Date label followed by value span
    html_content = re.sub(
        r'(<span class="episode-meta-label">Air Date</span><span class="episode-meta-value">)([^<]*)(</span>)',
        rf'\g<1>{display_date}\3',
        html_content
    )
    return html_content

def update_episode_network_style(html_content, network, display_date):
    """Update episode__network span that has a vague date like '1940s'"""
    # Replace just the date part (after the · ) in the network span
    html_content = re.sub(
        r'(<span class="episode__network">[^·]*·\s*)([^<]*)(</span>)',
        rf'\g<1>{display_date}\3',
        html_content
    )
    return html_content

def git_commit(message):
    """Commit and push changes"""
    import subprocess
    result = subprocess.run(
        ["git", "add", "-A"],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    print(f"  Commit: {result.stdout.strip() or result.stderr.strip()}")
    result = subprocess.run(
        ["git", "push", "origin", "HEAD:main"],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    print(f"  Push: {result.stdout.strip() or result.stderr.strip()}")

SHOWS = [
    {
        "dir": "philip-marlowe",
        "identifiers": ["OTRR_Philip_Marlowe_Singles"],
        "style": "meta-box",
    },
    {
        "dir": "x-minus-one",
        "identifiers": ["OTRR_X_Minus_One_Singles"],
        "style": "meta-box",
    },
    {
        "dir": "inner-sanctum",
        "identifiers": ["inner-sanctum-mysteries-radio-show-1941-episodes", "inner-sanctum_202108"],
        "style": "episode-network",
    },
    {
        "dir": "bob-hope",
        "identifiers": ["The_Bob_Hope_Program"],
        "style": "episode-network",
    },
    {
        "dir": "broadway-beat",
        "identifiers": ["OTRR_Broadway_Is_My_Beat_Singles"],
        "style": "episode-network",
    },
    {
        "dir": "green-hornet",
        "identifiers": ["GreenHornet"],
        "style": "meta-box",
    },
    {
        "dir": "our-miss-brooks",
        "identifiers": ["OTRR_Our_Miss_Brooks_Singles"],
        "style": "episode-network",
    },
    {
        "dir": "cisco-kid",
        "identifiers": ["TheCiscoKid"],
        "style": "episode-network",
    },
    {
        "dir": "cbs-mystery",
        "identifiers": ["cbsrmt-1975_2023"],
        "style": "meta-box",
    },
]

def find_date_from_filename(html_file_name):
    """Try to extract date from filename like 'our-miss-brooks-1948-12-05-018-weighing-machine.html'"""
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', html_file_name)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1920 <= y <= 1990 and 1 <= mo <= 12 and 1 <= d <= 31:
            try:
                dt = datetime(y, mo, d)
                display = dt.strftime("%B %d, %Y")
                display = re.sub(r' 0(\d),', r' \1,', display)
                return display, f"{y:04d}-{mo:02d}-{d:02d}"
            except:
                pass
    return None, None

def process_show(show_config):
    show_dir = show_config["dir"]
    identifiers = show_config["identifiers"]
    style = show_config["style"]
    
    print(f"\n{'='*60}")
    print(f"Processing: {show_dir}")
    print(f"{'='*60}")
    
    # Fetch metadata from all identifiers
    all_metadata = {}
    for identifier in identifiers:
        print(f"  Fetching metadata: {identifier}")
        meta = get_archive_metadata(identifier)
        all_metadata.update(meta)
        time.sleep(1)  # Rate limit
    
    # Build slug map
    slug_map = build_slug_map(all_metadata)
    print(f"  Slug map: {len(slug_map)} entries with valid dates")
    
    # Process HTML files
    html_files = get_html_files(show_dir)
    print(f"  HTML files: {len(html_files)}")
    
    updated = 0
    skipped_good = 0
    skipped_no_match = 0
    
    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8")
        
        # Skip if already has good date (not vague)
        if has_good_date(content) and not is_vague_date(content, show_dir):
            skipped_good += 1
            continue
        
        # Determine if page needs updating
        needs_update = is_vague_date(content, show_dir)
        if not needs_update:
            skipped_good += 1
            continue
        
        # Try to match by slugified filename
        stem = html_file.stem
        slug = slugify(stem)
        
        # Try various matching strategies
        match = slug_map.get(slug)
        
        # Try partial matches
        if not match:
            for key, val in slug_map.items():
                # Sliding window - if the slug contains the key or vice versa
                if len(key) > 8 and (key in slug or slug in key):
                    match = val
                    break
        
        # For shows where filename has date, try filename as fallback
        display_date, iso_date = None, None
        if match:
            display_date, iso_date = match[0], match[1]
        else:
            # Try extracting from filename (works for some shows)
            display_date, iso_date = find_date_from_filename(html_file.name)
        
        if not display_date:
            skipped_no_match += 1
            continue
        
        # Update the HTML based on style
        new_content = content
        
        if style == "meta-box" or '"datePublished":""' in content:
            new_content = update_xminusone_style(new_content, display_date, iso_date)
        
        if style == "episode-network" or 'episode__network' in content:
            # Also update episode__network if it has a vague date
            if re.search(r'episode__network.*?(\d{4}s|\d{4}[–-]\d{4})', new_content, re.DOTALL):
                # Get network name
                m = re.search(r'<span class="episode__network">([^·<]+)', new_content)
                network = m.group(1).strip() if m else ""
                new_content = update_episode_network_style(new_content, network, display_date)
            # Also update datePublished if empty
            if '"datePublished":""' in new_content:
                new_content = re.sub(
                    r'"datePublished":""',
                    f'"datePublished":"{iso_date}"',
                    new_content
                )
        
        if new_content != content:
            html_file.write_text(new_content, encoding="utf-8")
            updated += 1
            if updated % 20 == 0:
                print(f"    Updated {updated} files so far...")
        else:
            skipped_no_match += 1
    
    print(f"  Results: {updated} updated, {skipped_good} already good, {skipped_no_match} no match")
    return updated

def main():
    total_updated = 0
    batch_count = 0
    
    for show_config in SHOWS:
        count = process_show(show_config)
        total_updated += count
        batch_count += count
        
        # Commit every 200 pages
        if batch_count >= 200:
            print(f"\nCommitting batch ({batch_count} files)...")
            git_commit(f"fix: exact dates batch5 ({batch_count} files updated)")
            batch_count = 0
        
        time.sleep(2)  # Pause between shows
    
    # Final commit
    if batch_count > 0:
        print(f"\nFinal commit ({batch_count} files)...")
        git_commit(f"fix: exact dates batch5 final ({batch_count} files)")
    
    print(f"\n{'='*60}")
    print(f"DONE. Total updated: {total_updated}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
