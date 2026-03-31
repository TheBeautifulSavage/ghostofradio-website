#!/usr/bin/env python3
"""
Fix episode pages that have dates in filenames but show year-only or era in HTML.
"""

import os
import re
import sys
from pathlib import Path

MONTHS = {
    '01': 'January', '02': 'February', '03': 'March', '04': 'April',
    '05': 'May', '06': 'June', '07': 'July', '08': 'August',
    '09': 'September', '10': 'October', '11': 'November', '12': 'December'
}

def extract_date_from_filename(filename):
    """
    Try to extract (year, month, day) from a filename.
    Returns (yyyy_str, mm_str, dd_str) or None.
    Priority: YYYY-MM-DD > YY-MM-DD > YYMMDD_
    """
    name = os.path.splitext(filename)[0]

    # Pattern 1: YYYY-MM-DD (4-digit year, 1900s or 2000s)
    m = re.search(r'(?<!\d)((?:19|20)\d{2})-(\d{2})-(\d{2})(?!\d)', name)
    if m:
        yyyy, mm, dd = m.group(1), m.group(2), m.group(3)
        if 1 <= int(mm) <= 12 and 1 <= int(dd) <= 31:
            return yyyy, mm, dd

    # Pattern 2: YY-MM-DD (2-digit year with dashes)
    # (?<!\d) ensures we don't match inside a 4-digit year
    m = re.search(r'(?<!\d)(\d{2})-(\d{2})-(\d{2})(?!\d)', name)
    if m:
        yy, mm, dd = m.group(1), m.group(2), m.group(3)
        yy_int, mm_int, dd_int = int(yy), int(mm), int(dd)
        if 1 <= mm_int <= 12 and 1 <= dd_int <= 31:
            # Old time radio: all YY >= 20 → 19xx, YY < 20 → 20xx
            # (shows ran 1920s-1980s)
            year = 1900 + yy_int if yy_int >= 20 else 2000 + yy_int
            return str(year), mm, dd

    # Pattern 3: YYMMDD followed by _ or - (compact 6-digit date)
    m = re.search(r'(?<!\d)(\d{2})(\d{2})(\d{2})[_\-]', name)
    if m:
        yy, mm, dd = m.group(1), m.group(2), m.group(3)
        yy_int, mm_int, dd_int = int(yy), int(mm), int(dd)
        if 1 <= mm_int <= 12 and 1 <= dd_int <= 31:
            year = 1900 + yy_int if yy_int >= 20 else 2000 + yy_int
            return str(year), mm, dd

    # Pattern 4: YYMMDD at end of name or word boundary (no following separator)
    m = re.search(r'(?<![a-zA-Z\d])(\d{2})(\d{2})(\d{2})(?=[a-z])', name)
    if m:
        yy, mm, dd = m.group(1), m.group(2), m.group(3)
        yy_int, mm_int, dd_int = int(yy), int(mm), int(dd)
        if 1 <= mm_int <= 12 and 1 <= dd_int <= 31:
            year = 1900 + yy_int if yy_int >= 20 else 2000 + yy_int
            return str(year), mm, dd

    return None


def format_date(yyyy, mm, dd):
    """Format as 'Month Day, Year'"""
    month_name = MONTHS.get(mm)
    if not month_name:
        return None
    return f"{month_name} {int(dd)}, {yyyy}"


def fix_html_file(filepath, yyyy, mm, dd):
    """Fix a single HTML file. Returns True if modified."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    original = content
    full_date = format_date(yyyy, mm, dd)
    if not full_date:
        return False

    iso_date = f"{yyyy}-{mm}-{dd}"

    # 1. Fix episode__network span — replace whatever date/era is there
    # Matches: <span class="episode__network">NETWORK · SOMETHING</span>
    def fix_network(m_obj):
        network_part = m_obj.group(1)
        return f'<span class="episode__network">{network_part} · {full_date}</span>'

    content = re.sub(
        r'<span class="episode__network">([^·<]+?) · [^<]+?</span>',
        fix_network,
        content
    )

    # 2. Fix datePublished in JSON-LD (empty or year-only)
    content = re.sub(
        r'"datePublished"\s*:\s*""',
        f'"datePublished":"{iso_date}"',
        content
    )
    content = re.sub(
        r'"datePublished"\s*:\s*"(?:\d{4}|)"',
        f'"datePublished":"{iso_date}"',
        content
    )

    # 3. Fix article:published_time meta tag
    content = re.sub(
        r'(<meta\s+property="article:published_time"\s+content=")[^"]*(")',
        rf'\g<1>{iso_date}\g<2>',
        content
    )

    # 4. Fix Air Date in episode-meta-item (if present)
    # Pattern: <span class="episode-meta-label">Air Date</span><span class="episode-meta-value">SOMETHING</span>
    content = re.sub(
        r'(Air Date</span>\s*<span[^>]*>)[^<]*(</span>)',
        rf'\g<1>{full_date}\g<2>',
        content
    )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    return False


def git_commit_push(base_dir, batch_num):
    msg = f"fix: inject exact air dates from slugs — batch {batch_num}"
    cmd = f'cd "{base_dir}" && git add -A && git commit -m "{msg}" && git push origin HEAD:main'
    ret = os.system(cmd)
    return ret


def main():
    base_dir = Path('/Users/mac1/Projects/ghostofradio')

    # Collect all non-index HTML files
    html_files = [
        f for f in sorted(base_dir.rglob('*.html'))
        if f.name != 'index.html'
    ]
    print(f"Found {len(html_files)} non-index HTML files", flush=True)

    fixed = 0
    skipped_no_date = 0
    skipped_no_change = 0
    batch_num = 0
    files_since_commit = 0
    BATCH_SIZE = 500

    for filepath in html_files:
        result = extract_date_from_filename(filepath.name)
        if result is None:
            skipped_no_date += 1
            continue

        yyyy, mm, dd = result
        changed = fix_html_file(filepath, yyyy, mm, dd)
        if changed:
            fixed += 1
            files_since_commit += 1
            if files_since_commit >= BATCH_SIZE:
                batch_num += 1
                print(f"  → Committing batch {batch_num} ({fixed} total fixed so far)...", flush=True)
                git_commit_push(base_dir, batch_num)
                files_since_commit = 0
        else:
            skipped_no_change += 1

    # Final commit for remaining
    if files_since_commit > 0:
        batch_num += 1
        print(f"  → Committing final batch {batch_num} ({fixed} total fixed)...", flush=True)
        git_commit_push(base_dir, batch_num)

    print(f"\n=== DONE ===")
    print(f"Fixed:              {fixed}")
    print(f"Skipped (no date):  {skipped_no_date}")
    print(f"Skipped (no change):{skipped_no_change}")
    print(f"Total batches committed: {batch_num}")


if __name__ == '__main__':
    main()
