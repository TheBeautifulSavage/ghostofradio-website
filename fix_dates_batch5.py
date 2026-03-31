#!/usr/bin/env python3
"""
Fix dates for batch 5 shows.
- Shows with JSON-LD but empty datePublished: fill from archive or filename
- Shows WITHOUT JSON-LD: ADD JSON-LD with datePublished extracted from episode__network span

Shows in this batch:
- philip-marlowe (84 pages missing JSON-LD, dates in episode__network)
- x-minus-one (10 pages missing JSON-LD, dates already good in others)
- inner-sanctum (61 pages missing JSON-LD)
- bob-hope (203 pages missing JSON-LD)
- broadway-beat (150 pages missing JSON-LD)
- our-miss-brooks (181 pages missing JSON-LD)
- cisco-kid (153 pages missing JSON-LD)
- green-hornet (already done - skip)
- cbs-mystery (already done - skip)
"""
import os
import re
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/Users/mac1/Projects/ghostofradio")

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

def parse_display_date(date_str):
    """Parse human-readable date like 'March 6, 1949' or 'September 27, 1938' -> ISO date"""
    if not date_str:
        return None
    date_str = date_str.strip()
    # Try "Month Day, Year"
    m = re.match(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', date_str)
    if m:
        month_name, day, year = m.groups()
        month = MONTH_MAP.get(month_name.lower())
        if month:
            try:
                dt = datetime(int(year), month, int(day))
                if 1920 <= dt.year <= 1990:
                    return dt.strftime("%Y-%m-%d")
            except:
                pass
    return None

def extract_date_from_network_span(html_content):
    """Extract date from episode__network span like 'NBC · September 27, 1938'"""
    m = re.search(r'<span class="episode__network">[^·<]+·\s*([^<]+)</span>', html_content)
    if m:
        date_text = m.group(1).strip()
        iso = parse_display_date(date_text)
        if iso:
            return iso, date_text
    return None, None

def extract_date_from_filename(filename):
    """Try to extract date from filename patterns like:
    - philip-marlowe-49-03-19 -> 1949-03-19
    - xminusone55-04-24 -> 1955-04-24
    - our-miss-brooks-1948-12-05 -> 1948-12-05
    - 45-05-15-innersanctum -> 1945-05-15
    - 380927-001 -> 1938-09-27
    """
    stem = Path(filename).stem
    
    # Pattern: full year YYYY-MM-DD anywhere
    m = re.search(r'(1[89]\d{2})-(\d{2})-(\d{2})', stem)
    if m:
        y, mo, d = m.groups()
        if 1920 <= int(y) <= 1990 and 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            try:
                dt = datetime(int(y), int(mo), int(d))
                return dt.strftime("%Y-%m-%d")
            except:
                pass
    
    # Pattern: YY-MM-DD (2-digit year at start) like 45-05-15 or 55-04-24
    m = re.match(r'^(\d{2})-(\d{2})-(\d{2})', stem)
    if m:
        yr, mo, d = m.groups()
        yr_full = 1900 + int(yr) if int(yr) >= 20 else 2000 + int(yr)
        if 1920 <= yr_full <= 1990 and 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            try:
                dt = datetime(yr_full, int(mo), int(d))
                return dt.strftime("%Y-%m-%d")
            except:
                pass
    
    # Pattern: YY-MM-DD embedded (after show name) like philip-marlowe-49-03-19 or xminusone55-04-24
    m = re.search(r'(?<=[a-z])(\d{2})-(\d{2})-(\d{2})', stem)
    if not m:
        m = re.search(r'[a-z]-(\d{2})-(\d{2})-(\d{2})', stem)
    if m:
        yr, mo, d = m.groups()
        yr_full = 1900 + int(yr) if int(yr) >= 20 else 2000 + int(yr)
        if 1920 <= yr_full <= 1990 and 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            try:
                dt = datetime(yr_full, int(mo), int(d))
                return dt.strftime("%Y-%m-%d")
            except:
                pass
    
    # Pattern: YYMMDD like 380927 (6 consecutive digits)
    m = re.match(r'^(\d{6})', stem)
    if m:
        s = m.group(1)
        yr, mo, d = int(s[:2]), int(s[2:4]), int(s[4:6])
        yr_full = 1900 + yr if yr >= 20 else 2000 + yr
        if 1920 <= yr_full <= 1990 and 1 <= mo <= 12 and 1 <= d <= 31:
            try:
                dt = datetime(yr_full, mo, d)
                return dt.strftime("%Y-%m-%d")
            except:
                pass
    
    return None

def iso_to_display(iso_date):
    """Convert ISO date 'YYYY-MM-DD' to display 'Month D, YYYY'"""
    try:
        dt = datetime.strptime(iso_date, "%Y-%m-%d")
        display = dt.strftime("%B %-d, %Y")
        return display
    except:
        return iso_date

def add_jsonld_to_page(html_content, html_file, show_name, iso_date, canonical_url):
    """Add JSON-LD schema block to a page that doesn't have one"""
    # Extract title from h1 or title tag
    title = ""
    m = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content)
    if m:
        title = m.group(1).strip()
    else:
        m = re.search(r'<title>([^<|]+)', html_content)
        if m:
            title = m.group(1).strip()
    
    # Sanitize for JSON
    title = title.replace('"', '\\"').replace('\\', '\\\\')
    
    jsonld = f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":"{title}","datePublished":"{iso_date}","author":{{"@type":"Organization","name":"Ghost of Radio"}},"mainEntityOfPage":"{canonical_url}"}}</script>'
    
    # Insert after </link> tags before </head>
    new_content = re.sub(
        r'(</head>)',
        f'{jsonld}\n\\1',
        html_content,
        count=1
    )
    return new_content

def update_episode_meta_date(html_content, iso_date, display_date):
    """Update episode-meta-value Air Date if it contains an era range"""
    # Update era range in episode-meta-value Air Date
    new_content = re.sub(
        r'(<span class="episode-meta-label">Air Date</span><span class="episode-meta-value">)[^<]*(</span>)',
        rf'\g<1>{display_date}\2',
        html_content
    )
    # Update datePublished if empty
    new_content = re.sub(
        r'"datePublished":""',
        f'"datePublished":"{iso_date}"',
        new_content
    )
    return new_content

def git_commit(message):
    """Commit and push changes"""
    result = subprocess.run(
        ["git", "add", "-A"],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    output = result.stdout.strip() or result.stderr.strip()
    print(f"  Commit: {output[:100]}")
    result = subprocess.run(
        ["git", "push", "origin", "HEAD:main"],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    print(f"  Push: {(result.stdout + result.stderr).strip()[:100]}")

# Show configurations
SHOWS = [
    {"dir": "philip-marlowe", "show_name": "The Adventures of Philip Marlowe"},
    {"dir": "x-minus-one", "show_name": "X Minus One"},
    {"dir": "inner-sanctum", "show_name": "Inner Sanctum Mysteries"},
    {"dir": "bob-hope", "show_name": "The Bob Hope Show"},
    {"dir": "broadway-beat", "show_name": "Broadway Is My Beat"},
    {"dir": "our-miss-brooks", "show_name": "Our Miss Brooks"},
    {"dir": "cisco-kid", "show_name": "The Cisco Kid"},
    # green-hornet and cbs-mystery already have complete JSON-LD
]

def process_show(show_config):
    show_dir = show_config["dir"]
    show_name = show_config["show_name"]
    
    print(f"\n{'='*60}")
    print(f"Processing: {show_dir}")
    print(f"{'='*60}")
    
    show_path = BASE_DIR / show_dir
    html_files = [f for f in sorted(show_path.glob("*.html")) if f.name != "index.html"]
    print(f"  Total HTML files: {len(html_files)}")
    
    updated = 0
    skipped = 0
    no_date_found = 0
    
    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8")
        
        # Skip intro/biography pages that don't have meaningful episode dates
        skip_names = ['introduction', 'biography', 'otrr-introduction', 'about', 'index']
        if any(s in html_file.stem.lower() for s in skip_names):
            skipped += 1
            continue
        
        # Check if already has complete JSON-LD with date
        has_jsonld = '"datePublished"' in content
        has_good_date = False
        if has_jsonld:
            m = re.search(r'"datePublished":"(\d{4}-\d{2}-\d{2})"', content)
            if m and int(m.group(1)[:4]) >= 1920:
                has_good_date = True
        
        if has_good_date:
            skipped += 1
            continue
        
        # Also check if datePublished is a proper date in the JSON-LD (spaced format)
        m = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})"', content)
        if m and int(m.group(1)[:4]) >= 1920:
            skipped += 1
            continue
        
        # Find the date
        iso_date = None
        
        # Strategy 1: From episode__network span
        iso_date, _ = extract_date_from_network_span(content)
        
        # Strategy 2: From filename
        if not iso_date:
            iso_date = extract_date_from_filename(html_file.name)
        
        if not iso_date:
            no_date_found += 1
            continue
        
        # Get canonical URL
        canonical = ""
        m = re.search(r'<link rel="canonical" href="([^"]+)"', content)
        if m:
            canonical = m.group(1)
        
        display_date = iso_to_display(iso_date)
        
        # Update content
        new_content = content
        
        if not has_jsonld:
            # Add JSON-LD block
            new_content = add_jsonld_to_page(new_content, html_file, show_name, iso_date, canonical)
        else:
            # Update empty datePublished
            new_content = re.sub(
                r'"datePublished":""',
                f'"datePublished":"{iso_date}"',
                new_content
            )
            new_content = re.sub(
                r'"datePublished":\s*""',
                f'"datePublished":"{iso_date}"',
                new_content
            )
        
        if new_content != content:
            html_file.write_text(new_content, encoding="utf-8")
            updated += 1
            if updated % 25 == 0:
                print(f"    Updated {updated} files...")
    
    print(f"  Results: {updated} updated, {skipped} already done, {no_date_found} no date found")
    return updated

def main():
    total_updated = 0
    batch_count = 0
    commit_label = "batch5"
    
    for show_config in SHOWS:
        count = process_show(show_config)
        total_updated += count
        batch_count += count
        
        if batch_count >= 200:
            print(f"\nCommitting {batch_count} files...")
            git_commit(f"fix: add datePublished JSON-LD to {show_config['dir']} ({commit_label})")
            batch_count = 0
    
    # Final commit
    if batch_count > 0:
        print(f"\nFinal commit ({batch_count} files)...")
        git_commit(f"fix: add datePublished JSON-LD batch5 ({total_updated} total files)")
    
    print(f"\n{'='*60}")
    print(f"DONE. Total updated: {total_updated}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
