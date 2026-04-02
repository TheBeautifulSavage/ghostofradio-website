#!/usr/bin/env python3
"""Generate per-show RSS podcast feeds for Ghost of Radio top 20 shows."""

import os
import re
import glob
from datetime import datetime
from xml.sax.saxutils import escape

SITE_ROOT = "/Users/mac1/Projects/ghostofradio"
BASE_URL = "https://ghostofradio.com"
RSS_DIR = os.path.join(SITE_ROOT, "rss")
BUILD_DATE = "Thu, 02 Apr 2026 07:00:00 +0000"

SHOWS = [
    "shadow",
    "suspense",
    "gunsmoke",
    "dragnet",
    "loneranger",
    "johnny-dollar",
    "jack-benny",
    "fibber-mcgee",
    "great-gildersleeve",
    "escape",
    "x-minus-one",
    "lux-radio-theatre",
    "inner-sanctum",
    "have-gun",
    "burns-allen",
    "bob-hope",
    "our-miss-brooks",
    "philip-marlowe",
    "richard-diamond",
    "whistler",
]

SHOW_NAMES = {
    "shadow": "The Shadow",
    "suspense": "Suspense",
    "gunsmoke": "Gunsmoke",
    "dragnet": "Dragnet",
    "loneranger": "The Lone Ranger",
    "johnny-dollar": "Yours Truly, Johnny Dollar",
    "jack-benny": "The Jack Benny Program",
    "fibber-mcgee": "Fibber McGee and Molly",
    "great-gildersleeve": "The Great Gildersleeve",
    "escape": "Escape",
    "x-minus-one": "X Minus One",
    "lux-radio-theatre": "Lux Radio Theatre",
    "inner-sanctum": "Inner Sanctum Mysteries",
    "have-gun": "Have Gun Will Travel",
    "burns-allen": "The Burns and Allen Show",
    "bob-hope": "The Bob Hope Show",
    "our-miss-brooks": "Our Miss Brooks",
    "philip-marlowe": "Philip Marlowe",
    "richard-diamond": "Richard Diamond, Private Detective",
    "whistler": "The Whistler",
}


def parse_html(content):
    """Extract episode data from HTML content."""
    data = {}

    # Title
    m = re.search(r'<title>(.*?)</title>', content, re.DOTALL)
    if m:
        title = m.group(1).strip()
        # Strip "— Ghost of Radio" suffix
        title = re.sub(r'\s*[—–-]+\s*Ghost of Radio\s*$', '', title).strip()
        data['title'] = title

    # Meta description
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.DOTALL | re.IGNORECASE)
    if m:
        data['description'] = m.group(1).strip()

    # Canonical URL
    m = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\'](.*?)["\']', content, re.DOTALL | re.IGNORECASE)
    if m:
        data['link'] = m.group(1).strip()

    # Audio source
    m = re.search(r'<source\s+src=["\'](.*?)["\']', content, re.DOTALL | re.IGNORECASE)
    if m:
        data['audio_url'] = m.group(1).strip()

    # Date from episode__network span
    m = re.search(r'class=["\']episode__network["\'][^>]*>(.*?)</span>', content, re.DOTALL | re.IGNORECASE)
    if m:
        network_text = m.group(1).strip()
        # Extract 4-digit year
        year_m = re.search(r'\b(\d{4})\b', network_text)
        if year_m:
            data['year'] = int(year_m.group(1))
        data['network_text'] = network_text

    return data


def parse_date_from_filename(filename):
    """Try to extract date from filename like 1937-09-26-..."""
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', os.path.basename(filename))
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


def format_rfc2822(dt):
    """Format a datetime as RFC 2822."""
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return f"{days[dt.weekday()]}, {dt.day:02d} {months[dt.month-1]} {dt.year} 12:00:00 +0000"


def get_show_description(slug):
    """Get description from show's index.html."""
    index_path = os.path.join(SITE_ROOT, slug, "index.html")
    if not os.path.exists(index_path):
        return f"Classic old time radio episodes from {SHOW_NAMES.get(slug, slug)}. Free streaming on Ghost of Radio."
    with open(index_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return f"Classic old time radio episodes from {SHOW_NAMES.get(slug, slug)}. Free streaming on Ghost of Radio."


def get_episodes(slug):
    """Get all episodes for a show."""
    show_dir = os.path.join(SITE_ROOT, slug)
    if not os.path.exists(show_dir):
        print(f"  WARNING: Directory not found: {show_dir}")
        return []

    html_files = glob.glob(os.path.join(show_dir, "*.html"))
    # Skip index.html
    html_files = [f for f in html_files if os.path.basename(f) != 'index.html']

    episodes = []
    for filepath in html_files:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        data = parse_html(content)

        if not data.get('title') or not data.get('audio_url'):
            continue

        # Get date - try filename first, then fall back to year
        dt = parse_date_from_filename(filepath)
        if dt is None:
            year = data.get('year', 1940)
            dt = datetime(year, 1, 1)

        data['dt'] = dt
        data['filepath'] = filepath
        episodes.append(data)

    # Sort by date descending
    episodes.sort(key=lambda e: e['dt'], reverse=True)
    return episodes[:300]


def generate_feed(slug, episodes):
    """Generate RSS XML for a show."""
    show_name = SHOW_NAMES.get(slug, slug.replace('-', ' ').title())
    description = get_show_description(slug)
    feed_title = f"{show_name} | Ghost of Radio"
    feed_link = f"{BASE_URL}/{slug}/"
    image_url = f"{BASE_URL}/images/{slug}.jpg"
    
    # Check if image exists, else use logo
    img_path = os.path.join(SITE_ROOT, "images", f"{slug}.jpg")
    if not os.path.exists(img_path):
        image_url = f"{BASE_URL}/images/logo.png"

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">',
        '<channel>',
        f'  <title>{escape(feed_title)}</title>',
        f'  <link>{escape(feed_link)}</link>',
        f'  <description>{escape(description)}</description>',
        '  <language>en-us</language>',
        '  <copyright>Public Domain</copyright>',
        '  <itunes:author>Ghost of Radio</itunes:author>',
        '  <itunes:category text="Society &amp; Culture">',
        '    <itunes:category text="History"/>',
        '  </itunes:category>',
        f'  <itunes:image href="{image_url}"/>',
        '  <itunes:explicit>false</itunes:explicit>',
        '  <image>',
        f'    <url>{image_url}</url>',
        f'    <title>{escape(feed_title)}</title>',
        f'    <link>{escape(feed_link)}</link>',
        '  </image>',
        f'  <lastBuildDate>{BUILD_DATE}</lastBuildDate>',
    ]

    for ep in episodes:
        title = ep.get('title', '')
        link = ep.get('link', '')
        audio_url = ep.get('audio_url', '')
        desc = ep.get('description', f"Classic old time radio episode from {show_name}. Free streaming on Ghost of Radio.")
        pub_date = format_rfc2822(ep['dt'])
        
        if not link or not audio_url:
            continue

        lines.extend([
            '  <item>',
            f'    <title><![CDATA[{title}]]></title>',
            f'    <link>{escape(link)}</link>',
            f'    <guid>{escape(link)}</guid>',
            f'    <description><![CDATA[{desc}]]></description>',
            f'    <pubDate>{pub_date}</pubDate>',
            f'    <category>{escape(show_name)}</category>',
            f'    <enclosure url="{escape(audio_url)}" length="0" type="audio/mpeg"/>',
            '    <itunes:explicit>false</itunes:explicit>',
            '  </item>',
        ])

    lines.extend([
        '</channel>',
        '</rss>',
    ])

    return '\n'.join(lines)


def generate_global_feed(all_episodes_by_show):
    """Generate the main feed.xml with all episodes from all shows."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">',
        '<channel>',
        '  <title>Ghost of Radio — Classic Old Time Radio</title>',
        '  <link>https://ghostofradio.com</link>',
        '  <description>Free classic old time radio streaming. 14,000+ episodes from the golden age of radio — The Shadow, Sam Spade, Dragnet, Suspense, Lone Ranger and 50+ more shows.</description>',
        '  <language>en-us</language>',
        '  <copyright>Public Domain</copyright>',
        '  <itunes:author>Ghost of Radio</itunes:author>',
        '  <itunes:category text="Society &amp; Culture">',
        '    <itunes:category text="History"/>',
        '  </itunes:category>',
        '  <itunes:image href="https://ghostofradio.com/images/logo.png"/>',
        '  <itunes:explicit>false</itunes:explicit>',
        '  <image>',
        '    <url>https://ghostofradio.com/images/logo.png</url>',
        '    <title>Ghost of Radio</title>',
        '    <link>https://ghostofradio.com</link>',
        '  </image>',
        f'  <lastBuildDate>{BUILD_DATE}</lastBuildDate>',
    ]

    # Merge all episodes across shows, sort by date desc, take top 500
    all_eps = []
    for slug, episodes in all_episodes_by_show.items():
        show_name = SHOW_NAMES.get(slug, slug.replace('-', ' ').title())
        for ep in episodes:
            ep_copy = dict(ep)
            ep_copy['show_name'] = show_name
            all_eps.append(ep_copy)

    all_eps.sort(key=lambda e: e['dt'], reverse=True)
    all_eps = all_eps[:500]

    for ep in all_eps:
        title = ep.get('title', '')
        link = ep.get('link', '')
        audio_url = ep.get('audio_url', '')
        desc = ep.get('description', '')
        pub_date = format_rfc2822(ep['dt'])
        show_name = ep.get('show_name', '')

        if not link or not audio_url:
            continue

        lines.extend([
            '  <item>',
            f'    <title><![CDATA[{title}]]></title>',
            f'    <link>{escape(link)}</link>',
            f'    <guid>{escape(link)}</guid>',
            f'    <description><![CDATA[{desc}]]></description>',
            f'    <pubDate>{pub_date}</pubDate>',
            f'    <category>{escape(show_name)}</category>',
            f'    <enclosure url="{escape(audio_url)}" length="0" type="audio/mpeg"/>',
            '    <itunes:explicit>false</itunes:explicit>',
            '  </item>',
        ])

    lines.extend([
        '</channel>',
        '</rss>',
    ])

    return '\n'.join(lines)


def generate_index_html(shows_data):
    """Generate rss/index.html listing all feeds."""
    rows = ""
    for slug, (show_name, ep_count) in shows_data.items():
        feed_url = f"{BASE_URL}/rss/{slug}.xml"
        show_url = f"{BASE_URL}/{slug}/"
        rows += f"""    <tr>
      <td><a href="{show_url}">{show_name}</a></td>
      <td>{ep_count} episodes</td>
      <td><a href="{feed_url}">RSS Feed</a></td>
    </tr>\n"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RSS Podcast Feeds | Ghost of Radio</title>
  <meta name="description" content="Subscribe to classic old time radio podcast feeds from Ghost of Radio. Individual RSS feeds for every major show.">
  <link rel="canonical" href="https://ghostofradio.com/rss/">
  <link rel="stylesheet" href="/css/style.css">
</head>
<body>
  <header style="padding:2rem;text-align:center;background:#111;border-bottom:1px solid #222;">
    <a href="/" style="color:#c9a84c;font-family:serif;font-size:1.8rem;text-decoration:none;">Ghost of Radio</a>
  </header>
  <main style="max-width:900px;margin:3rem auto;padding:0 1rem;">
    <h1 style="color:#c9a84c;font-family:serif;margin-bottom:.5rem;">Podcast RSS Feeds</h1>
    <p style="color:#aaa;margin-bottom:2rem;">Subscribe to your favorite classic radio shows in any podcast app. Copy the RSS feed URL and paste it into your app, or click the link to subscribe directly.</p>
    <p style="margin-bottom:2rem;"><strong><a href="{BASE_URL}/rss/feed.xml" style="color:#c9a84c;">All Shows Combined Feed</a></strong> — Every show in one feed</p>
    <table style="width:100%;border-collapse:collapse;background:#111;border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#1a1a0a;color:#c9a84c;font-family:serif;">
          <th style="text-align:left;padding:.75rem 1rem;border-bottom:1px solid #333;">Show</th>
          <th style="text-align:left;padding:.75rem 1rem;border-bottom:1px solid #333;">Episodes</th>
          <th style="text-align:left;padding:.75rem 1rem;border-bottom:1px solid #333;">RSS Feed</th>
        </tr>
      </thead>
      <tbody style="color:#e8e0d0;">
{rows}
      </tbody>
    </table>
  </main>
  <footer style="text-align:center;padding:2rem;color:#555;font-size:.85rem;">
    <p>&copy; Ghost of Radio — Public Domain Classic Radio</p>
  </footer>
</body>
</html>"""


def main():
    os.makedirs(RSS_DIR, exist_ok=True)

    total_feeds = 0
    total_episodes = 0
    all_episodes_by_show = {}
    shows_data = {}

    for slug in SHOWS:
        show_name = SHOW_NAMES.get(slug, slug.replace('-', ' ').title())
        print(f"Processing {show_name} ({slug})...")

        episodes = get_episodes(slug)
        ep_count = len(episodes)
        print(f"  Found {ep_count} episodes")

        if ep_count == 0:
            print(f"  Skipping (no episodes found)")
            continue

        xml = generate_feed(slug, episodes)
        output_path = os.path.join(RSS_DIR, f"{slug}.xml")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml)

        all_episodes_by_show[slug] = episodes
        shows_data[slug] = (show_name, ep_count)
        total_feeds += 1
        total_episodes += ep_count
        print(f"  Written: rss/{slug}.xml")

    # Update global feed
    print("\nUpdating global feed.xml...")
    global_xml = generate_global_feed(all_episodes_by_show)
    with open(os.path.join(RSS_DIR, "feed.xml"), 'w', encoding='utf-8') as f:
        f.write(global_xml)
    print("  Written: rss/feed.xml")

    # Generate index.html
    print("Generating rss/index.html...")
    index_html = generate_index_html(shows_data)
    with open(os.path.join(RSS_DIR, "index.html"), 'w', encoding='utf-8') as f:
        f.write(index_html)
    print("  Written: rss/index.html")

    print(f"\n✅ Done! {total_feeds} feeds created, {total_episodes} total episodes across all feeds.")
    return total_feeds, total_episodes


if __name__ == "__main__":
    main()
