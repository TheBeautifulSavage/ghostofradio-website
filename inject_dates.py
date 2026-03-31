#!/usr/bin/env python3
"""
inject_dates.py - Fetch archive.org metadata and inject air dates into HTML episode pages.
Dates are extracted from archive.org filenames (e.g., Dragnet_49-06-10_002_Big_38.mp3)
and the 'album' field (e.g., "06/10/49, episode 2").
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

# Show configs
SHOWS = [
    {
        "dir": "dragnet",
        "identifiers": ["Dragnet_OTR", "OTRR_Dragnet_Singles"],
        "era": "NBC · 1949–1957",
        "network": "NBC",
    },
    {
        "dir": "escape",
        "identifiers": ["OTRR_Escape_Singles"],
        "era": "CBS · 1947–1954",
        "network": "CBS",
    },
    {
        "dir": "gunsmoke",
        "identifiers": ["OTRR_Gunsmoke_Singles"],
        "era": "CBS · 1952–1961",
        "network": "CBS",
    },
    {
        "dir": "whistler",
        "identifiers": ["OTRR_Whistler_Singles"],
        "era": "CBS · 1942–1955",
        "network": "CBS",
    },
    {
        "dir": "lux-radio-theatre",
        "identifiers": ["LuxRadioTheatre"],
        "era": "CBS · 1936–1955",
        "network": "CBS",
    },
    {
        "dir": "philip-marlowe",
        "identifiers": ["OTRR_Philip_Marlowe_Singles"],
        "era": "CBS · 1947–1951",
        "network": "CBS",
    },
    {
        "dir": "suspense",
        "identifiers": ["OTRR_Suspense_Singles"],
        "era": "CBS · 1942–1962",
        "network": "CBS",
    },
    {
        "dir": "x-minus-one",
        "identifiers": ["OTRR_X_Minus_One_Singles"],
        "era": "NBC · 1955–1958",
        "network": "NBC",
    },
    {
        "dir": "inner-sanctum",
        "identifiers": ["inner-sanctum-mysteries-radio-show-1941-episodes"],
        "era": "NBC · 1941–1952",
        "network": "NBC",
    },
]


def slugify(text):
    """Convert text to URL slug."""
    text = text.lower()
    # Remove apostrophes and quotes
    text = re.sub(r"['\u2019\u2018\u201c\u201d`]", "", text)
    # Replace non-alphanumeric with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text


def extract_date_from_filename(filename):
    """
    Extract date from filename patterns like:
    - Dragnet_49-06-10_002_Big_38.mp3  → 1949-06-10
    - Escape_47-07-07_001_...mp3 → 1947-07-07
    - Gunsmoke_52-04-26_001_...mp3 → 1952-04-26
    Returns (iso_date, human_date) or (None, None)
    """
    stem = os.path.splitext(os.path.basename(filename))[0]
    
    # Pattern: ShowName_YY-MM-DD_NNN_Title or ShowName_YYYY-MM-DD_...
    # Match 2-digit or 4-digit year
    m = re.search(r'[_\s](\d{2})-(\d{2})-(\d{2})[_\s]', stem)
    if m:
        yy, mm, dd = m.group(1), m.group(2), m.group(3)
        # Convert 2-digit year to 4-digit
        year = int(yy)
        if year >= 0 and year <= 70:
            year += 1900
        elif year > 70:
            year += 1900
        # Validate month and day
        mon, day = int(mm), int(dd)
        if 1 <= mon <= 12 and 1 <= day <= 31:
            try:
                dt = datetime(year, mon, day)
                iso = dt.strftime("%Y-%m-%d")
                human = dt.strftime("%B %-d, %Y")
                return iso, human
            except ValueError:
                pass

    # Pattern: YYYY-MM-DD anywhere in filename
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', stem)
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            iso = dt.strftime("%Y-%m-%d")
            human = dt.strftime("%B %-d, %Y")
            return iso, human
        except ValueError:
            pass

    return None, None


def extract_date_from_album(album):
    """
    Extract date from album field like "06/10/49, episode 2"
    """
    if not album:
        return None, None
    
    # Pattern: MM/DD/YY or MM/DD/YYYY
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', album)
    if m:
        mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if len(m.group(3)) == 2:
            year = yy + 1900 if yy >= 0 else yy + 2000
        else:
            year = yy
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            try:
                dt = datetime(year, mm, dd)
                iso = dt.strftime("%Y-%m-%d")
                human = dt.strftime("%B %-d, %Y")
                return iso, human
            except ValueError:
                pass

    return None, None


def extract_title_from_filename(filename):
    """
    Extract the episode title portion from archive filename.
    E.g., "Dragnet_49-06-10_002_Big_38.mp3" → "Big 38"
    "OTRR_Dragnet_49-06-10_002_Big_38.mp3" → "Big 38"
    """
    stem = os.path.splitext(os.path.basename(filename))[0]
    
    # Remove leading show prefix (up to and including the episode number after date)
    # Pattern: anything up to YY-MM-DD_NNN_ or YY-MM-DD_
    result = re.sub(r'^.*?\d{2}-\d{2}-\d{2}[_\s]+(?:\d+[_\s]+)?', '', stem)
    
    if not result:
        # Try YYYY-MM-DD pattern
        result = re.sub(r'^.*?\d{4}-\d{2}-\d{2}[_\s]+(?:\d+[_\s]+)?', '', stem)
    
    if not result:
        result = stem
    
    return result.replace("_", " ").strip()


def get_archive_metadata(identifier):
    """Fetch metadata from archive.org for a given identifier."""
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
        
        album = f.get("album", "")
        title = f.get("title", "") or ""
        
        # Extract date: first try filename, then album field
        iso, human = extract_date_from_filename(name)
        if not iso:
            iso, human = extract_date_from_album(album)
        
        if iso:
            # Get title for matching
            if not title:
                title = extract_title_from_filename(name)
            result[name] = {"iso": iso, "human": human, "title": title}

    print(f"  Got {len(result)} MP3 entries with dates from {identifier}")
    return result


def build_slug_map(metadata):
    """Build a mapping from slug -> (date, title) from archive metadata."""
    slug_map = {}
    for filename, info in metadata.items():
        iso = info.get("iso", "")
        human = info.get("human", "")
        title = info.get("title", "")
        
        if not iso:
            continue

        # Slug from the title
        title_slug = slugify(title) if title else ""
        
        # Slug from the filename title portion
        fname_title = extract_title_from_filename(filename)
        fname_slug = slugify(fname_title) if fname_title else ""
        
        # Also try slugifying the full stem
        stem = os.path.splitext(os.path.basename(filename))[0]
        # Remove show prefix and date/episode number
        clean_stem = re.sub(r'^[^_]+_\d{2}-\d{2}-\d{2}[_\s]+(?:\d+[_\s]+)?', '', stem)
        stem_slug = slugify(clean_stem) if clean_stem else ""
        
        entry = {"iso": iso, "human": human, "title": title, "filename": filename}
        
        for slug in [title_slug, fname_slug, stem_slug]:
            if slug and slug not in slug_map:
                slug_map[slug] = entry
            elif slug and slug in slug_map:
                # Keep if same date or if existing has no date
                pass

    return slug_map


def update_html(filepath, iso_date, human_date, era_label, network):
    """Update an HTML file with the given date information."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # 1. Update datePublished in JSON-LD (only if empty)
    content = re.sub(
        r'"datePublished":""',
        f'"datePublished":"{iso_date}"',
        content
    )

    # 2. Update Air Date meta value
    air_date_pattern = r'(<span class="episode-meta-label">Air Date</span><span class="episode-meta-value">)[^<]*(</span>)'
    content = re.sub(
        air_date_pattern,
        lambda m: m.group(1) + human_date + m.group(2),
        content
    )

    # 3. Replace generic era label with specific date in meta value spans
    # This handles the Air Date row if it has the era label
    content = content.replace(
        f'<span class="episode-meta-value">{era_label}</span>',
        f'<span class="episode-meta-value">{human_date}</span>'
    )

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
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
            ["git", "commit", "-m", f"fix: archive.org dates for {show_name} — batch {batch_num} ({file_count} files)"],
            cwd=SITE_ROOT, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "push", "origin", "HEAD:main"],
            cwd=SITE_ROOT, check=True, capture_output=True
        )
        print(f"  ✓ Committed and pushed batch {batch_num} for {show_name} ({file_count} files)")
    except subprocess.CalledProcessError as e:
        print(f"  WARNING: git operation failed: {e}")
        print(f"  stderr: {e.stderr}")


def process_show(show_config):
    show_dir = show_config["dir"]
    identifiers = show_config["identifiers"]
    era_label = show_config["era"]
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

    # Build slug map
    slug_map = build_slug_map(all_metadata)
    print(f"  Slug map has {len(slug_map)} slug entries")

    if not slug_map:
        print(f"  No dated entries found, skipping {show_dir}")
        return 0

    # Debug: show sample slug entries
    sample = list(slug_map.items())[:5]
    print(f"  Sample slug entries:")
    for slug, info in sample:
        print(f"    '{slug}' → {info['human']} ({info['filename'][:50]}...)")

    # Get all HTML files without dates in filename
    all_html = glob.glob(os.path.join(show_path, "*.html"))
    
    no_date_files = []
    for f in all_html:
        basename = os.path.basename(f)
        # Skip if filename already has date (e.g., dragnet-54-02-16-ep235-big-sucker.html)
        if re.search(r'\d{2}-\d{2}-\d{2}', basename):
            continue
        no_date_files.append(f)

    print(f"  Found {len(no_date_files)} files without dates in slug (out of {len(all_html)} total)")

    # Debug: show sample site slugs
    sample_slugs = [os.path.splitext(os.path.basename(f))[0] for f in sorted(no_date_files)[:5]]
    print(f"  Sample site slugs: {sample_slugs}")

    updated = 0
    skipped = 0
    no_match = 0
    batch = 1
    batch_updates = 0

    for filepath in sorted(no_date_files):
        basename = os.path.basename(filepath)
        site_slug = os.path.splitext(basename)[0]

        # Try direct slug match
        match = slug_map.get(site_slug)

        # If no direct match, try substring matching
        if not match:
            # Try to find archive slug that ends with site_slug
            for arc_slug, val in slug_map.items():
                if arc_slug.endswith(site_slug) or arc_slug == site_slug:
                    match = val
                    break

        # Try prefix match (site slug might be shorter)
        if not match:
            for arc_slug, val in slug_map.items():
                if site_slug.startswith(arc_slug) or arc_slug.startswith(site_slug):
                    match = val
                    break

        if not match:
            no_match += 1
            continue

        iso = match["iso"]
        human = match["human"]

        if update_html(filepath, iso, human, era_label, network):
            updated += 1
            batch_updates += 1
            print(f"  ✓ {basename} → {human}")

            if batch_updates >= 200:
                git_commit(show_dir, batch)
                batch += 1
                batch_updates = 0
        else:
            skipped += 1

    # Final commit for remaining changes
    if batch_updates > 0:
        git_commit(show_dir, batch)

    print(f"\n  Summary for {show_dir}: {updated} updated, {skipped} already done, {no_match} no archive match")
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
