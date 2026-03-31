#!/usr/bin/env python3
"""
inject_dates_batch4.py - Fetch archive.org metadata and inject air dates for batch 4 shows.
Shows: fibber-mcgee, burns-allen, great-gildersleeve, amos-andy
"""

import urllib.request
import json
import os
import re
import glob
import time
import subprocess
import sys
from datetime import datetime

SITE_ROOT = "/Users/mac1/Projects/ghostofradio"

SHOWS = [
    {
        "dir": "fibber-mcgee",
        "identifiers": ["BDP_FibberMcGee"],
        "network": "NBC",
    },
    {
        "dir": "burns-allen",
        "identifiers": ["BDP_BurnsAllen", "TheBurnsAndAllenShow062545-22650"],
        "network": "CBS/NBC",
    },
    {
        "dir": "great-gildersleeve",
        "identifiers": ["Otrr_The_Great_Gildersleeve_Singles"],
        "network": "NBC",
    },
    {
        "dir": "amos-andy",
        "identifiers": ["AmosNAndy"],
        "network": "NBC/CBS",
    },
]


def slugify(text):
    text = str(text).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def get_archive_metadata(identifier):
    url = f"https://archive.org/metadata/{identifier}"
    print(f"  Fetching metadata: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "GhostOfRadio/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
    except Exception as e:
        print(f"  ERROR fetching {identifier}: {e}")
        return {}

    result = {}
    for f in data.get("files", []):
        name = f.get("name", "")
        if not name.lower().endswith(".mp3"):
            continue
        date_str = f.get("date", "") or f.get("year", "")
        title = f.get("title", "") or ""
        result[name] = {"date": date_str, "title": title}

    print(f"  Got {len(result)} MP3 entries from {identifier}")
    return result


def parse_date(date_str):
    """Parse date string from archive.org, return (iso, human) or (None, None)."""
    if not date_str:
        return None, None

    date_str = date_str.strip()

    # Try full ISO date: YYYY-MM-DD
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date_str)
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return dt.strftime("%Y-%m-%d"), dt.strftime("%B %-d, %Y")
        except ValueError:
            pass

    # Try MM/DD/YYYY or MM/DD/YY
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})$', date_str)
    if m:
        mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        year = yy if yy > 99 else (1900 + yy)
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            try:
                dt = datetime(year, mm, dd)
                return dt.strftime("%Y-%m-%d"), dt.strftime("%B %-d, %Y")
            except ValueError:
                pass

    # Only year - not specific enough
    return None, None


def extract_date_from_filename(filename):
    """Extract date from MP3 filename patterns like Show_YY-MM-DD_title.mp3"""
    stem = os.path.splitext(os.path.basename(filename))[0]

    # Pattern: YY-MM-DD (2-digit year)
    m = re.search(r'[_\-\s](\d{2})-(\d{2})-(\d{2})[_\-\s]', stem)
    if m:
        yy, mm, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
        year = 1900 + yy
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            try:
                dt = datetime(year, mm, dd)
                return dt.strftime("%Y-%m-%d"), dt.strftime("%B %-d, %Y")
            except ValueError:
                pass

    # Pattern: YYYY-MM-DD
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', stem)
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return dt.strftime("%Y-%m-%d"), dt.strftime("%B %-d, %Y")
        except ValueError:
            pass

    return None, None


def build_slug_map(metadata):
    """Build slug -> date mapping from archive.org metadata."""
    slug_map = {}

    for filename, info in metadata.items():
        date_str = info.get("date", "")
        title = info.get("title", "")

        # Try archive metadata date first
        iso, human = parse_date(date_str)

        # Fallback: try extracting date from filename
        if not iso:
            iso, human = extract_date_from_filename(filename)

        if not iso:
            continue

        stem = os.path.splitext(os.path.basename(filename))[0]

        # Generate multiple slugs for matching
        candidates = []

        # From title
        if title:
            candidates.append(slugify(title))

        # From full stem
        candidates.append(slugify(stem))

        # Strip show prefix + date + episode number, get title portion
        # Pattern like: Show_YY-MM-DD_NNN_Title → Title
        title_part = re.sub(r'^.*?\d{2}-\d{2}-\d{2}[_\-\s]+(?:\d{1,3}[_\-\s]+)?', '', stem)
        if title_part and title_part != stem:
            candidates.append(slugify(title_part))

        entry = {"iso": iso, "human": human, "filename": filename}

        for slug in candidates:
            if slug and len(slug) > 3 and slug not in slug_map:
                slug_map[slug] = entry

    return slug_map


def get_current_date_from_html(filepath):
    """Extract the current network/date span from HTML."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'episode__network[^>]*>([^<]*)</span>', content)
    if m:
        return m.group(1).strip()
    return None


def update_html_date(filepath, iso_date, human_date, network):
    """Update HTML file with specific date."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Update episode__network span: replace era range with specific date
    # Pattern: NBC · April 16, 1935 or NBC · 1940s or NBC/CBS · 1940s
    content = re.sub(
        r'(<span class="episode__network">)([^<]*)(</span>)',
        lambda m: m.group(1) + f"{network} · {human_date}" + m.group(3),
        content
    )

    # Update datePublished in JSON-LD if empty
    content = re.sub(
        r'"datePublished":""',
        f'"datePublished":"{iso_date}"',
        content
    )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def git_commit(show_name, batch_num):
    """Commit and push current changes."""
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=SITE_ROOT, check=True, capture_output=True
        )
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=SITE_ROOT, capture_output=True, text=True
        )
        if not result.stdout.strip():
            print("  No changes to commit")
            return
        file_count = len(result.stdout.strip().split('\n'))
        subprocess.run(
            ["git", "commit", "-m",
             f"fix: exact dates {show_name} batch {batch_num} ({file_count} files)"],
            cwd=SITE_ROOT, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "push", "origin", "HEAD:main"],
            cwd=SITE_ROOT, check=True, capture_output=True
        )
        print(f"  ✓ Committed and pushed batch {batch_num} for {show_name} ({file_count} files)")
    except subprocess.CalledProcessError as e:
        print(f"  WARNING: git operation failed: {e}")
        if e.stderr:
            print(f"  stderr: {e.stderr.decode()}")


def extract_date_from_html_filename(filename):
    """Extract date from HTML filename pattern like show-YY-MM-DD-title.html"""
    stem = os.path.splitext(os.path.basename(filename))[0]

    # Standard pattern: show-name-YY-MM-DD-title (date after show prefix)
    # Try matching YY-MM-DD as standalone segments (surrounded by separators or end)
    # Be careful with numbers that are part of titles like "2ndcourtship", "1877nickel"

    # Strategy: look for pattern where after the show prefix, we have YY-MM-DD
    # Pattern: two-digit year between 28 and 59 (OTR era), then month, then day
    m = re.search(r'-(\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])(?:-|$)', stem)
    if m:
        yy, mm, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
        year = 1900 + yy
        if 1928 <= year <= 1959:
            try:
                dt = datetime(year, mm, dd)
                return dt.strftime("%Y-%m-%d"), dt.strftime("%B %-d, %Y")
            except ValueError:
                pass

    # Try 4-digit year
    m = re.search(r'-(19\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])(?:-|$)', stem)
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return dt.strftime("%Y-%m-%d"), dt.strftime("%B %-d, %Y")
        except ValueError:
            pass

    return None, None


def process_show(show_config):
    show_dir = show_config["dir"]
    identifiers = show_config["identifiers"]
    network = show_config["network"]
    show_path = os.path.join(SITE_ROOT, show_dir)

    if not os.path.isdir(show_path):
        print(f"  SKIP: directory not found: {show_path}")
        return 0

    print(f"\n{'='*60}")
    print(f"Processing: {show_dir}")
    print(f"{'='*60}")

    # Fetch metadata from all identifiers
    all_metadata = {}
    for ident in identifiers:
        meta = get_archive_metadata(ident)
        all_metadata.update(meta)
        time.sleep(1)

    # Build slug map from archive metadata
    slug_map = build_slug_map(all_metadata)
    print(f"  Slug map has {len(slug_map)} entries")

    # Sample slug entries
    sample = list(slug_map.items())[:5]
    print(f"  Sample slugs:")
    for slug, info in sample:
        print(f"    '{slug}' → {info['human']}")

    # Get all HTML episode files
    all_html = sorted(glob.glob(os.path.join(show_path, "*.html")))
    episode_files = [f for f in all_html if os.path.basename(f) != "index.html"]

    print(f"  Total episode files: {len(episode_files)}")

    updated = 0
    skipped = 0
    already_done = 0
    batch = 1
    batch_updates = 0

    months_list = ['January','February','March','April','May','June','July','August',
                   'September','October','November','December']

    for filepath in episode_files:
        basename = os.path.basename(filepath)

        # Get current date in HTML
        current_date = get_current_date_from_html(filepath)
        if current_date:
            has_month = any(mo in current_date for mo in months_list)
            if has_month:
                already_done += 1
                continue

        # Try to extract date from HTML filename
        iso, human = extract_date_from_html_filename(basename)

        if iso:
            # We have a date from the filename - update the HTML
            if update_html_date(filepath, iso, human, network):
                updated += 1
                batch_updates += 1
                print(f"  ✓ [filename] {basename} → {human}")
                if batch_updates >= 200:
                    git_commit(show_dir, batch)
                    batch += 1
                    batch_updates = 0
            else:
                skipped += 1
            continue

        # Try to match via archive.org slug map
        site_slug = os.path.splitext(basename)[0]
        match = None

        # Direct match
        match = slug_map.get(site_slug)

        # Try various slug fragments
        if not match:
            # Extract just the title portion after date
            title_part = re.sub(r'^.*?-\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])-?', '', site_slug)
            if title_part and title_part != site_slug:
                match = slug_map.get(title_part)

        if not match:
            # Try substring matching
            for arc_slug, val in slug_map.items():
                if len(arc_slug) >= 5:
                    if arc_slug in site_slug or site_slug in arc_slug:
                        match = val
                        break

        if not match:
            print(f"  ? No match: {basename}")
            continue

        iso = match["iso"]
        human = match["human"]

        if update_html_date(filepath, iso, human, network):
            updated += 1
            batch_updates += 1
            print(f"  ✓ [archive] {basename} → {human}")
            if batch_updates >= 200:
                git_commit(show_dir, batch)
                batch += 1
                batch_updates = 0
        else:
            skipped += 1

    # Final commit
    if batch_updates > 0:
        git_commit(show_dir, batch)

    print(f"\n  Summary for {show_dir}:")
    print(f"    Already done: {already_done}")
    print(f"    Updated: {updated}")
    print(f"    Skipped (no change): {skipped}")

    return updated


def main():
    target_shows = sys.argv[1:] if len(sys.argv) > 1 else None
    total_updated = 0

    for show in SHOWS:
        if target_shows and show["dir"] not in target_shows:
            continue
        count = process_show(show)
        total_updated += count
        time.sleep(2)

    print(f"\n{'='*60}")
    print(f"TOTAL UPDATED: {total_updated} pages")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
