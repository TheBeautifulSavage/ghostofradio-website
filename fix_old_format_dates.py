#!/usr/bin/env python3
"""
fix_old_format_dates.py - Inject JSON-LD datePublished into old-format episode pages.

Old-format pages have dates in their filenames (e.g., dragnet-49-06-10-002-...)
and in the episode__network span (e.g., "NBC · June 10, 1949") but lack JSON-LD.

This script:
1. Finds old-format pages (those with episode__network span, no episode-meta-box)
2. Extracts date from filename OR episode__network span
3. Injects JSON-LD script into <head>
4. Commits every 200 pages
"""

import glob
import os
import re
import subprocess
from datetime import datetime

SITE_ROOT = "/Users/mac1/Projects/ghostofradio"

SHOWS = [
    {
        "dir": "dragnet",
        "show_name": "Dragnet",
        "era": "NBC · 1949–1957",
        "network": "NBC",
    },
    {
        "dir": "escape",
        "show_name": "Escape",
        "era": "CBS · 1947–1954",
        "network": "CBS",
    },
    {
        "dir": "gunsmoke",
        "show_name": "Gunsmoke",
        "era": "CBS · 1952–1961",
        "network": "CBS",
    },
]


def extract_date_from_filename(filename):
    """
    Extract date from filename patterns like:
    - dragnet-49-06-10-002-big-38.html → 1949-06-10
    - escape-48-01-28-025-three-good-witnesses.html → 1948-01-28
    - gunsmoke-52-04-26-001-billy-the-kid.html → 1952-04-26
    Returns (iso_date, human_date) or (None, None)
    """
    stem = os.path.splitext(os.path.basename(filename))[0]
    
    # Pattern: show-YY-MM-DD-NNN-... or show-YY-MM-DD-...
    m = re.search(r'-(\d{2})-(\d{2})-(\d{2})-', stem)
    if m:
        yy, mm, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
        # Convert 2-digit year - radio shows 1940s-1960s
        year = yy + 1900  # all OTR shows are 1900s
        # Validate month and day
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            try:
                dt = datetime(year, mm, dd)
                iso = dt.strftime("%Y-%m-%d")
                human = dt.strftime("%B %-d, %Y")
                return iso, human
            except ValueError:
                pass

    # Pattern: YYYY-MM-DD
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


def extract_date_from_network_span(content):
    """
    Extract date from episode__network span like "NBC · June 10, 1949"
    Returns (iso_date, human_date) or (None, None)
    """
    m = re.search(r'episode__network[^>]*>[^·]+·\s*([A-Z][a-z]+ \d+, \d{4})', content)
    if m:
        date_str = m.group(1).strip()
        try:
            dt = datetime.strptime(date_str, "%B %d, %Y")
            iso = dt.strftime("%Y-%m-%d")
            human = dt.strftime("%B %-d, %Y")
            return iso, human
        except ValueError:
            pass
    return None, None


def get_episode_title_from_page(content, filepath):
    """Extract episode title from h1 or title tag."""
    # Try h1
    m = re.search(r'<h1[^>]*class="episode__title"[^>]*>([^<]+)</h1>', content)
    if m:
        return m.group(1).strip()
    # Try title tag - take first part before " — "
    m = re.search(r'<title>([^<]+)</title>', content)
    if m:
        title = m.group(1).strip()
        # Remove " — Show | Ghost of Radio" part
        title = re.split(r'\s*[—–|]\s*', title)[0].strip()
        return title
    # Fall back to filename
    stem = os.path.splitext(os.path.basename(filepath))[0]
    return stem.replace('-', ' ').title()


def get_canonical_url(content, filepath, show_dir):
    """Get canonical URL from the page."""
    m = re.search(r'<link rel="canonical" href="([^"]+)"', content)
    if m:
        return m.group(1)
    # Build from filepath
    base = os.path.basename(filepath)
    return f"https://ghostofradio.com/{show_dir}/{base}"


def inject_jsonld(content, iso_date, show_name, era, canonical_url, filepath):
    """Inject JSON-LD script into head if not already present."""
    if 'application/ld+json' in content:
        # Already has JSON-LD - skip
        return content, False
    
    title = get_episode_title_from_page(content, filepath)
    
    jsonld = (
        f'<script type="application/ld+json">'
        f'{{"@context":"https://schema.org","@type":"Article",'
        f'"headline":"{title} — {show_name} ({era})",'
        f'"datePublished":"{iso_date}",'
        f'"author":{{"@type":"Organization","name":"Ghost of Radio"}},'
        f'"mainEntityOfPage":"{canonical_url}"}}'
        f'</script>'
    )
    
    # Inject before </head>
    if '</head>' in content:
        content = content.replace('</head>', jsonld + '\n</head>', 1)
        return content, True
    
    # Fallback: inject after last <link> or <meta> tag in head
    # Find </title> or last meta tag and inject after
    m = re.search(r'(<link rel="stylesheet"[^>]*>\n?)', content)
    if m:
        insert_pos = content.rfind('<link rel="stylesheet"')
        end_pos = content.find('>', insert_pos) + 1
        content = content[:end_pos] + '\n' + jsonld + content[end_pos:]
        return content, True
    
    return content, False


def git_commit(show_name, batch_num, file_count):
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
            print(f"  No changes to commit (batch {batch_num})")
            return
        actual_count = len(result.stdout.strip().split('\n'))
        subprocess.run(
            ["git", "commit", "-m", 
             f"fix: exact dates {show_name} batch {batch_num} ({actual_count} files)"],
            cwd=SITE_ROOT, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "push", "origin", "HEAD:main"],
            cwd=SITE_ROOT, check=True, capture_output=True
        )
        print(f"  ✓ Committed and pushed batch {batch_num} for {show_name} ({actual_count} files)")
    except subprocess.CalledProcessError as e:
        print(f"  WARNING: git operation failed: {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"  stderr: {e.stderr}")


def process_show(show_config):
    show_dir = show_config["dir"]
    show_name = show_config["show_name"]
    era = show_config["era"]
    network = show_config["network"]
    show_path = os.path.join(SITE_ROOT, show_dir)

    if not os.path.isdir(show_path):
        print(f"  SKIP: directory not found: {show_path}")
        return 0

    print(f"\n{'='*60}")
    print(f"Processing: {show_dir}")
    print(f"{'='*60}")

    # Find old-format pages (no episode-meta-box, has episode__network)
    all_html = sorted(glob.glob(os.path.join(show_path, "*.html")))
    
    old_format_pages = []
    for f in all_html:
        if 'index' in os.path.basename(f):
            continue
        with open(f, encoding='utf-8') as fh:
            content = fh.read()
        # Old format: has episode__network but no episode-meta-box
        if 'episode__network' in content and 'episode-meta-box' not in content:
            if 'application/ld+json' not in content:
                old_format_pages.append(f)
    
    print(f"  Found {len(old_format_pages)} old-format pages needing JSON-LD injection")

    updated = 0
    skipped = 0
    no_date = 0
    batch = 1
    batch_updates = 0

    for filepath in old_format_pages:
        basename = os.path.basename(filepath)
        
        # Try to get date from filename first (most reliable)
        iso_date, human_date = extract_date_from_filename(basename)
        
        # Fallback: try episode__network span
        if not iso_date:
            with open(filepath, encoding='utf-8') as f:
                content = f.read()
            iso_date, human_date = extract_date_from_network_span(content)
        
        if not iso_date:
            no_date += 1
            print(f"  SKIP (no date): {basename}")
            continue
        
        # Read content and inject
        with open(filepath, encoding='utf-8') as f:
            content = f.read()
        
        canonical_url = get_canonical_url(content, filepath, show_dir)
        new_content, changed = inject_jsonld(content, iso_date, show_name, era, canonical_url, filepath)
        
        if changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            updated += 1
            batch_updates += 1
            print(f"  ✓ {basename} → {human_date}")
            
            if batch_updates >= 200:
                git_commit(show_name, batch, batch_updates)
                batch += 1
                batch_updates = 0
        else:
            skipped += 1

    # Final commit
    if batch_updates > 0:
        git_commit(show_name, batch, batch_updates)

    print(f"\n  Summary for {show_dir}: {updated} updated, {skipped} already done, {no_date} no date found")
    return updated


def main():
    import sys
    target_shows = sys.argv[1:] if len(sys.argv) > 1 else None

    total_updated = 0
    for show in SHOWS:
        if target_shows and show["dir"] not in target_shows:
            continue
        count = process_show(show)
        total_updated += count

    print(f"\n{'='*60}")
    print(f"TOTAL UPDATED: {total_updated} pages")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
