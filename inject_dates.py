#!/usr/bin/env python3
"""
inject_dates.py - Fetch archive.org metadata and inject air dates into HTML episode pages.
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

# Show configs: (show_dir, archive_identifiers, show_era_label, network)
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
    text = re.sub(r"['\u2019\u2018\u201c\u201d]", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text


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
        if name.lower().endswith(".mp3"):
            date = f.get("date", "") or f.get("year", "")
            title = f.get("title", "") or f.get("name", "")
            result[name] = {"date": date, "title": title}
    print(f"  Got {len(result)} MP3 entries from {identifier}")
    return result


def parse_date(date_str):
    """Parse a date string into (iso_date, human_date) or (None, None)."""
    if not date_str:
        return None, None

    date_str = date_str.strip()

    # Try various formats
    formats = [
        ("%Y-%m-%d", True),
        ("%Y/%m/%d", True),
        ("%m/%d/%Y", True),
        ("%B %d, %Y", True),
        ("%b %d, %Y", True),
        ("%d %B %Y", True),
        ("%Y-%m", False),  # partial date - year+month only
    ]

    for fmt, is_full in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if is_full:
                iso = dt.strftime("%Y-%m-%d")
                human = dt.strftime("%B %-d, %Y")
                return iso, human
        except ValueError:
            continue

    # Just a 4-digit year - not specific enough
    if re.match(r"^\d{4}$", date_str):
        return None, None

    return None, None


def build_slug_map(metadata):
    """Build a mapping from slug -> (date, title) from archive metadata."""
    slug_map = {}
    for filename, info in metadata.items():
        stem = os.path.splitext(filename)[0]
        # Remove path separators if present
        stem = stem.replace("/", "_").replace("\\", "_")
        # Get just the base name
        stem = os.path.basename(stem)
        slug = slugify(stem)
        date = info.get("date", "")
        title = info.get("title", "")
        iso, human = parse_date(date)
        if iso:
            slug_map[slug] = {"iso": iso, "human": human, "title": title, "filename": filename}
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

    # 2. Update Air Date meta value (replace era like "NBC · 1949–1957")
    # Pattern: Air Date label followed by the era value
    air_date_pattern = r'(<span class="episode-meta-label">Air Date</span><span class="episode-meta-value">)[^<]*(</span>)'
    content = re.sub(
        air_date_pattern,
        lambda m: m.group(1) + human_date + m.group(2),
        content
    )

    # 3. Update the era box content if it contains just the era range
    # e.g., "NBC · 1949–1957" → "NBC · March 5, 1953"
    # Only replace if current content is the generic era label
    era_escaped = re.escape(era_label)
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
        subprocess.run(
            ["git", "commit", "-m", f"fix: archive.org dates for {show_name} — batch {batch_num}"],
            cwd=SITE_ROOT, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "push", "origin", "HEAD:main"],
            cwd=SITE_ROOT, check=True, capture_output=True
        )
        print(f"  ✓ Committed and pushed batch {batch_num} for {show_name}")
    except subprocess.CalledProcessError as e:
        print(f"  WARNING: git operation failed: {e}")


def process_show(show_config):
    show_dir = show_config["dir"]
    identifiers = show_config["identifiers"]
    era_label = show_config["era"]
    network = show_config["network"]
    show_path = os.path.join(SITE_ROOT, show_dir)

    if not os.path.isdir(show_path):
        print(f"  SKIP: directory not found: {show_path}")
        return

    print(f"\n{'='*60}")
    print(f"Processing: {show_dir}")
    print(f"{'='*60}")

    # Fetch metadata from all identifiers
    all_metadata = {}
    for ident in identifiers:
        meta = get_archive_metadata(ident)
        all_metadata.update(meta)
        time.sleep(1)  # polite delay

    # Build slug map
    slug_map = build_slug_map(all_metadata)
    print(f"  Slug map has {len(slug_map)} entries with real dates")

    if not slug_map:
        print(f"  No dated entries found, skipping {show_dir}")
        return

    # Get all HTML files without dates in slug (files that don't match YYYY-MM-DD or similar)
    all_html = glob.glob(os.path.join(show_path, "*.html"))
    
    # Filter to only files WITHOUT dates in filename
    no_date_files = []
    for f in all_html:
        basename = os.path.basename(f)
        # Skip if filename already has date (e.g., dragnet-54-02-16-ep235-big-sucker.html)
        if re.search(r'\d{2}-\d{2}-\d{2}', basename):
            continue
        no_date_files.append(f)

    print(f"  Found {len(no_date_files)} files without dates in slug (out of {len(all_html)} total)")

    updated = 0
    skipped = 0
    batch = 1
    batch_updates = 0

    for filepath in sorted(no_date_files):
        basename = os.path.basename(filepath)
        slug = os.path.splitext(basename)[0]

        # Try direct slug match
        match = slug_map.get(slug)

        # If no direct match, try partial matching
        if not match:
            # Try to find a slug_map key that contains this slug
            for key, val in slug_map.items():
                if slug in key or key.endswith(slug):
                    match = val
                    break

        if not match:
            skipped += 1
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

    print(f"\n  Summary for {show_dir}: {updated} updated, {skipped} skipped/no-match")
    return updated


def main():
    # Default: process all shows, or pass show names as args
    target_shows = sys.argv[1:] if len(sys.argv) > 1 else None

    total_updated = 0
    for show in SHOWS:
        if target_shows and show["dir"] not in target_shows:
            continue
        count = process_show(show)
        if count:
            total_updated += count
        time.sleep(2)  # polite delay between shows

    print(f"\n{'='*60}")
    print(f"TOTAL UPDATED: {total_updated} pages")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
