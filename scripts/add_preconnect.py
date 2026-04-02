#!/usr/bin/env python3
"""Add <link rel="preconnect" href="https://archive.org" crossorigin> to episode pages
that reference archive.org but don't already have the preconnect hint."""

import os
import re
import sys

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRECONNECT_TAG = '<link rel="preconnect" href="https://archive.org" crossorigin>'
SKIP_DIRS = {'stories', 'node_modules', '.git', 'scripts', 'css', 'js', 'audio', 'images', 'rss', 'downloads', 'research', 'blog', '2000-plus'}

added = 0
skipped_already = 0
skipped_no_archive = 0
errors = 0

html_files = []
for root, dirs, files in os.walk(SITE_ROOT):
    # Prune skip dirs
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
    for fname in files:
        if fname.endswith('.html'):
            html_files.append(os.path.join(root, fname))

print(f"Scanning {len(html_files)} HTML files...")

for fpath in html_files:
    try:
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Skip if no archive.org reference
        if 'archive.org' not in content:
            skipped_no_archive += 1
            continue
        
        # Skip if already has preconnect for archive.org
        if 'preconnect' in content and 'archive.org' in content:
            # Check if preconnect specifically points to archive.org
            if re.search(r'rel=["\']preconnect["\'][^>]*href=["\']https://archive\.org', content) or \
               re.search(r'href=["\']https://archive\.org["\'][^>]*rel=["\']preconnect', content):
                skipped_already += 1
                continue
        
        # Insert preconnect after <head> tag or after charset meta
        # Try to insert after the last existing <link rel="preconnect"> if any
        # Otherwise insert after <head>
        new_content = None
        
        # Strategy: insert before </head> but after existing preconnects/metas
        # Best: insert right after <meta charset=...> line
        charset_match = re.search(r'(<meta\s+charset=[^>]+>)', content, re.IGNORECASE)
        if charset_match:
            insert_pos = charset_match.end()
            new_content = content[:insert_pos] + '\n  ' + PRECONNECT_TAG + content[insert_pos:]
        else:
            # Fall back: insert right after <head>
            head_match = re.search(r'(<head[^>]*>)', content, re.IGNORECASE)
            if head_match:
                insert_pos = head_match.end()
                new_content = content[:insert_pos] + '\n  ' + PRECONNECT_TAG + content[insert_pos:]
        
        if new_content is None:
            print(f"  WARN: Could not find insertion point in {fpath}", file=sys.stderr)
            errors += 1
            continue
        
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        added += 1
        
    except Exception as e:
        print(f"  ERROR: {fpath}: {e}", file=sys.stderr)
        errors += 1

print(f"\nDone!")
print(f"  Pages updated (preconnect added): {added}")
print(f"  Skipped (already had preconnect): {skipped_already}")
print(f"  Skipped (no archive.org ref):     {skipped_no_archive}")
print(f"  Errors:                           {errors}")
