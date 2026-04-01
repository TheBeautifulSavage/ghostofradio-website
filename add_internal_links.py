#!/usr/bin/env python3
"""
Add internal linking to every episode page:
- Next/Prev navigation
- Related shows section
"""

import os
import re
import subprocess
from pathlib import Path

BASE_DIR = Path("/Users/mac1/Projects/ghostofradio")

RELATED = {
    "johnny-dollar": ["sam-spade", "philip-marlowe", "richard-diamond"],
    "sam-spade": ["johnny-dollar", "philip-marlowe", "broadway-beat"],
    "shadow": ["suspense", "inner-sanctum", "quiet-please"],
    "dragnet": ["johnny-dollar", "broadway-beat", "richard-diamond"],
    "suspense": ["inner-sanctum", "escape", "quiet-please"],
    "loneranger": ["gunsmoke", "cisco-kid", "have-gun"],
    "gunsmoke": ["loneranger", "fort-laramie", "have-gun"],
    "fibber-mcgee": ["burns-allen", "bob-hope", "great-gildersleeve"],
    "burns-allen": ["fibber-mcgee", "bob-hope", "ozzie-harriet"],
    "x-minus-one": ["dimension-x", "quiet-please", "escape"],
    "_default": ["suspense", "dragnet", "loneranger"],
}

CSS = """
<style>
.episode-nav{display:flex;justify-content:space-between;margin:2rem 0;padding:1rem 0;border-top:1px solid #222;}
.episode-nav a{color:#c9a84c;text-decoration:none;font-family:'Special Elite',cursive;font-size:.9rem;}
.episode-nav a:hover{color:#fff;}
.related-shows{margin:2rem 0;padding:1.5rem;background:#111;border-radius:8px;border:1px solid #222;}
.related-shows h4{color:#c9a84c;font-family:'Special Elite',cursive;margin:0 0 1rem;font-size:.85rem;letter-spacing:.1em;text-transform:uppercase;}
.related-shows__links{display:flex;gap:1rem;flex-wrap:wrap;}
.related-shows__links a{color:#e8e0d0;text-decoration:none;font-size:.9rem;padding:.4rem .8rem;background:#1a1a1a;border-radius:4px;border:1px solid #333;}
.related-shows__links a:hover{border-color:#c9a84c;}
</style>
"""

SHOW_DISPLAY_NAMES = {
    "johnny-dollar": "Yours Truly, Johnny Dollar",
    "sam-spade": "The Adventures of Sam Spade",
    "philip-marlowe": "Philip Marlowe",
    "richard-diamond": "Richard Diamond",
    "broadway-beat": "Broadway Beat",
    "shadow": "The Shadow",
    "suspense": "Suspense",
    "inner-sanctum": "Inner Sanctum",
    "quiet-please": "Quiet Please",
    "dragnet": "Dragnet",
    "loneranger": "The Lone Ranger",
    "gunsmoke": "Gunsmoke",
    "cisco-kid": "The Cisco Kid",
    "have-gun": "Have Gun – Will Travel",
    "fibber-mcgee": "Fibber McGee and Molly",
    "burns-allen": "Burns and Allen",
    "bob-hope": "The Bob Hope Show",
    "great-gildersleeve": "The Great Gildersleeve",
    "ozzie-harriet": "The Adventures of Ozzie and Harriet",
    "x-minus-one": "X Minus One",
    "dimension-x": "Dimension X",
    "escape": "Escape",
    "fort-laramie": "Fort Laramie",
    "amos-andy": "Amos 'n' Andy",
    "bold-venture": "Bold Venture",
    "box-13": "Box 13",
    "cbs-mystery": "CBS Mystery Theater",
    "challenge-yukon": "Challenge of the Yukon",
    "crime-classics": "Crime Classics",
    "dangerous-assignment": "Dangerous Assignment",
    "death-valley-days": "Death Valley Days",
    "duffys-tavern": "Duffy's Tavern",
    "green-hornet": "The Green Hornet",
    "jack-benny": "The Jack Benny Program",
    "let-george-do-it": "Let George Do It",
    "lights-out": "Lights Out",
    "lux-radio-theatre": "Lux Radio Theatre",
    "mercury-theatre": "Mercury Theatre on the Air",
    "my-favorite-husband": "My Favorite Husband",
    "mysterious-traveler": "The Mysterious Traveler",
    "nightbeat": "Night Beat",
    "our-miss-brooks": "Our Miss Brooks",
    "railroad-hour": "The Railroad Hour",
    "red-skelton": "The Red Skelton Show",
    "rogues-gallery": "Rogue's Gallery",
    "sherlock": "Sherlock Holmes",
    "sounds-of-darkness": "Sounds of Darkness",
    "stars-over-hollywood": "Stars Over Hollywood",
    "the-clock": "The Clock",
    "the-falcon": "The Falcon",
    "the-saint": "The Saint",
    "whistler": "The Whistler",
}


def get_show_name(show_slug):
    return SHOW_DISPLAY_NAMES.get(show_slug, show_slug.replace("-", " ").title())


def get_related_shows(show_slug):
    return RELATED.get(show_slug, RELATED["_default"])


def build_nav_html(show_slug, prev_slug, next_slug):
    parts = []
    if prev_slug:
        parts.append(f'  <a href="/{show_slug}/{prev_slug}" class="episode-nav__prev">← Previous Episode</a>')
    else:
        parts.append('  <span></span>')
    if next_slug:
        parts.append(f'  <a href="/{show_slug}/{next_slug}" class="episode-nav__next">Next Episode →</a>')
    else:
        parts.append('  <span></span>')
    return '<div class="episode-nav">\n' + '\n'.join(parts) + '\n</div>'


def build_related_html(show_slug):
    related = get_related_shows(show_slug)
    links = []
    for r in related:
        name = get_show_name(r)
        links.append(f'    <a href="/{r}/">{name}</a>')
    links_html = '\n'.join(links)
    return f'''<div class="related-shows">
  <h4>More from Ghost of Radio</h4>
  <div class="related-shows__links">
{links_html}
  </div>
</div>'''


def get_episode_files(show_dir):
    """Get all non-index HTML files, sorted."""
    files = sorted([
        f for f in show_dir.glob("*.html")
        if f.name != "index.html"
    ])
    return files


def inject_css_if_needed(content):
    """Inject CSS before </head> if episode-nav style not already present."""
    if "episode-nav{" in content or ".episode-nav{" in content:
        return content
    return content.replace("</head>", CSS + "</head>", 1)


def process_show(show_slug, show_dir, total_modified, commit_threshold=500):
    """Process all episode files in a show directory."""
    files = get_episode_files(show_dir)
    if not files:
        return total_modified

    slugs = [f.name for f in files]
    modified_in_show = 0

    for i, filepath in enumerate(files):
        content = filepath.read_text(encoding="utf-8", errors="replace")

        # Skip if already processed
        if 'class="episode-nav"' in content:
            continue

        # Determine prev/next slugs
        prev_slug = slugs[i - 1] if i > 0 else None
        next_slug = slugs[i + 1] if i < len(slugs) - 1 else None

        nav_html = build_nav_html(show_slug, prev_slug, next_slug)
        related_html = build_related_html(show_slug)

        injection = f"\n{nav_html}\n{related_html}\n"

        # Find insertion point: prefer <footer class="site-footer"> then episode__footer
        if '<footer class="site-footer">' in content:
            content = content.replace('<footer class="site-footer">', injection + '<footer class="site-footer">', 1)
        elif '<footer class="episode__footer">' in content:
            content = content.replace('<footer class="episode__footer">', injection + '<footer class="episode__footer">', 1)
        elif '</article>' in content:
            content = content.replace('</article>', injection + '</article>', 1)
        else:
            # Fallback: inject before </body>
            content = content.replace('</body>', injection + '</body>', 1)

        # Inject CSS
        content = inject_css_if_needed(content)

        filepath.write_text(content, encoding="utf-8")
        modified_in_show += 1
        total_modified += 1

        # Commit every 500 pages
        if total_modified % commit_threshold == 0:
            print(f"  Committing at {total_modified} pages...")
            subprocess.run(
                ["git", "add", "-A"],
                cwd=BASE_DIR, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", f"feat: internal linking checkpoint {total_modified}"],
                cwd=BASE_DIR, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "push", "origin", "HEAD:main"],
                cwd=BASE_DIR, check=True, capture_output=True
            )

    if modified_in_show > 0:
        print(f"  [{show_slug}] Modified {modified_in_show} pages")

    return total_modified


def main():
    # Find all show directories (dirs containing HTML files, not blog/etc.)
    skip_dirs = {"blog", "css", "js", "images", "audio", "rss", "research", "scripts", "downloads"}

    show_dirs = []
    for d in sorted(BASE_DIR.iterdir()):
        if d.is_dir() and d.name not in skip_dirs and not d.name.startswith("."):
            html_files = [f for f in d.glob("*.html") if f.name != "index.html"]
            if html_files:
                show_dirs.append(d)

    print(f"Found {len(show_dirs)} show directories")

    total_modified = 0
    for show_dir in show_dirs:
        show_slug = show_dir.name
        print(f"Processing: {show_slug}")
        total_modified = process_show(show_slug, show_dir, total_modified)

    # Final commit
    print(f"\nTotal pages modified: {total_modified}")
    if total_modified > 0:
        print("Final commit...")
        result = subprocess.run(
            ["git", "add", "-A"],
            cwd=BASE_DIR, check=True, capture_output=True
        )
        result = subprocess.run(
            ["git", "commit", "-m", f"feat: internal linking all shows ({total_modified} pages)"],
            cwd=BASE_DIR, capture_output=True
        )
        if result.returncode == 0:
            print("Committed successfully")
            push = subprocess.run(
                ["git", "push", "origin", "HEAD:main"],
                cwd=BASE_DIR, capture_output=True
            )
            print(f"Push: {push.returncode == 0 and 'OK' or push.stderr.decode()}")
        else:
            print(f"Commit output: {result.stdout.decode()} {result.stderr.decode()}")
    else:
        print("No pages needed modification (all already processed or none found)")


if __name__ == "__main__":
    main()
