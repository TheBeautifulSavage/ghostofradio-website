#!/usr/bin/env python3
"""
fix_dates_batch3.py - Fix empty datePublished and Air Date meta values for:
  - loneranger (17 episode pages with dates in filenames)
  - lux-radio-theatre (1 page with date in filename)

Strategy: Extract dates directly from HTML filenames since the archive.org
OTRR format embeds dates (YY-MM-DD) in filenames.
"""

import os
import re
import glob
import subprocess
from datetime import datetime

SITE_ROOT = "/Users/mac1/Projects/ghostofradio"


def extract_date_from_filename(basename):
    """Extract date from patterns like theloneranger38-06-150840povertyinthreeconers.html"""
    # Match YY-MM-DD pattern
    m = re.search(r'(\d{2})-(\d{2})-(\d{2})', basename)
    if m:
        yy, mm, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
        year = yy + 1900  # All OTR dates are 1930-1960s
        mon, day = mm, dd
        if 1 <= mon <= 12 and 1 <= day <= 31:
            try:
                dt = datetime(year, mon, day)
                iso = dt.strftime("%Y-%m-%d")
                human = dt.strftime("%B %-d, %Y")
                return iso, human
            except ValueError:
                pass
    # Also try YYYY-MM-DD pattern (for lux filenames like luxradiotheatre1940-02-26...)
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', basename)
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            iso = dt.strftime("%Y-%m-%d")
            human = dt.strftime("%B %-d, %Y")
            return iso, human
        except ValueError:
            pass
    return None, None


def update_html_file(filepath, iso_date, human_date, era_labels_to_replace):
    """
    Update HTML:
    1. Fill empty datePublished in JSON-LD
    2. Replace Air Date meta value with exact date
    Returns True if file was modified.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # 1. Fill empty datePublished
    content = re.sub(
        r'"datePublished":""',
        f'"datePublished":"{iso_date}"',
        content
    )

    # 2. Replace Air Date meta value (whatever it currently shows → exact date)
    # Pattern: Air Date label followed by meta-value span
    air_date_pattern = r'(<span class="episode-meta-label">Air Date</span>\s*<span class="episode-meta-value">)[^<]*(</span>)'
    content = re.sub(
        air_date_pattern,
        lambda m: m.group(1) + human_date + m.group(2),
        content,
        flags=re.DOTALL
    )

    # 3. Also replace any of the known era label spans
    for label in era_labels_to_replace:
        content = content.replace(
            f'<span class="episode-meta-value">{label}</span>',
            f'<span class="episode-meta-value">{human_date}</span>'
        )

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def git_commit(show_name, batch_num, file_count):
    """Commit and push current changes."""
    try:
        subprocess.run(["git", "add", "-A"], cwd=SITE_ROOT, check=True, capture_output=True)
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=SITE_ROOT, capture_output=True, text=True
        )
        if not result.stdout.strip():
            print(f"  No changes to commit for {show_name} batch {batch_num}")
            return
        subprocess.run(
            ["git", "commit", "-m", f"fix: exact dates {show_name} batch {batch_num} ({file_count} files)"],
            cwd=SITE_ROOT, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "push", "origin", "HEAD:main"],
            cwd=SITE_ROOT, check=True, capture_output=True
        )
        print(f"  ✓ Committed and pushed batch {batch_num} for {show_name} ({file_count} files)")
    except subprocess.CalledProcessError as e:
        print(f"  WARNING: git operation failed: {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"  stderr: {e.stderr}")


def process_show(show_dir, era_labels, skip_patterns=None):
    """Process all HTML files in a show directory."""
    show_path = os.path.join(SITE_ROOT, show_dir)
    if not os.path.isdir(show_path):
        print(f"SKIP: {show_path} not found")
        return 0

    print(f"\n{'='*60}")
    print(f"Processing: {show_dir}")
    print(f"{'='*60}")

    # Find files with empty datePublished
    all_html = glob.glob(os.path.join(show_path, "*.html"))
    targets = []
    for f in all_html:
        b = os.path.basename(f)
        if b == "index.html":
            continue
        # Skip patterns (e.g., special pages without episode dates)
        if skip_patterns and any(p in b for p in skip_patterns):
            print(f"  SKIP (special): {b}")
            continue
        with open(f, encoding="utf-8") as fh:
            content = fh.read()
        if '"datePublished":""' in content:
            targets.append(f)

    print(f"  Found {len(targets)} files with empty datePublished")

    updated = 0
    no_date = []
    batch_updates = 0
    batch_num = 1

    for filepath in sorted(targets):
        basename = os.path.basename(filepath)
        iso_date, human_date = extract_date_from_filename(basename)

        if not iso_date:
            no_date.append(basename)
            continue

        if update_html_file(filepath, iso_date, human_date, era_labels):
            updated += 1
            batch_updates += 1
            print(f"  ✓ {basename} → {human_date}")
        else:
            print(f"  ~ {basename} already had {iso_date}")

        if batch_updates >= 200:
            git_commit(show_dir, batch_num, batch_updates)
            batch_num += 1
            batch_updates = 0

    # Final commit
    if batch_updates > 0:
        git_commit(show_dir, batch_num, batch_updates)

    if no_date:
        print(f"\n  Files without extractable dates ({len(no_date)}):")
        for f in no_date:
            print(f"    {f}")

    print(f"\n  Summary: {updated} updated, {len(no_date)} skipped (no date in filename)")
    return updated


def main():
    total = 0

    # --- LONERANGER ---
    total += process_show(
        show_dir="loneranger",
        era_labels=["Classic Radio", "ABC · 1940s", "1930s–1950s"],
        skip_patterns=[
            "the-lone-ranger-00-",
            "the-lone-ranger-01-",
            "the-lone-ranger-02-",
            "the-lone-ranger-03-",
            "the-lone-ranger-04-",
        ]
    )

    # --- LUX RADIO THEATRE ---
    total += process_show(
        show_dir="lux-radio-theatre",
        era_labels=["CBS/NBC · 1934–1955", "CBS · 1936–1955"],
    )

    print(f"\n{'='*60}")
    print(f"GRAND TOTAL: {total} pages updated")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
