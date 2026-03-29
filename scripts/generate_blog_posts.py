#!/usr/bin/env python3
"""
Ghost of Radio — Shadow Episode Blog Post Generator

Generates individual blog post pages and an index page for Shadow episodes.
Uses the Anthropic Claude API (claude-3-5-haiku-20241022) for content generation.

Usage:
    python scripts/generate_blog_posts.py --dry-run   # Placeholder content (no API calls)
    python scripts/generate_blog_posts.py --live       # Real API calls (requires ANTHROPIC_API_KEY)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Only import anthropic when needed (--live mode)
anthropic = None


def slugify(title):
    """Convert a title to a URL-friendly slug."""
    slug = title.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug.strip('-')


def format_date(date_str):
    """Format YYYY-MM-DD to a readable date."""
    from datetime import datetime
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    return dt.strftime('%B %d, %Y')


def generate_placeholder_content(episode):
    """Generate placeholder blog post content for --dry-run mode."""
    title = episode['title']
    date = format_date(episode['date'])
    desc = episode['description']

    return f"""<p><em>The radio crackles to life, and through the static, a chilling voice emerges...</em></p>

<p>First aired on {date}, "{title}" stands as one of the most gripping episodes in the early run of The Shadow. {desc}</p>

<p>From the very first moments of this episode, listeners are plunged into a world of darkness and suspense. The atmosphere is thick with tension as Lamont Cranston — that wealthy young man-about-town who secretly fights crime as The Shadow — finds himself drawn into a mystery that tests even his extraordinary abilities.</p>

<p>What makes this episode particularly memorable is the way it builds suspense through masterful sound design and voice acting. The creaking doors, the distant footsteps, the ominous music — every element works together to create a sense of dread that only old time radio can deliver. You can almost feel the fog rolling in as The Shadow stalks through the shadows of 1930s New York.</p>

<p>The standout moment comes in the third act, when The Shadow confronts the villain in a scene that showcases everything great about this series. His iconic laugh echoes through the darkness as he declares, "The weed of crime bears bitter fruit!" — a line that sent shivers down the spines of millions of listeners gathered around their radios on that {date} evening.</p>

<p>Orson Welles and the cast deliver performances that remind us why The Shadow remained on the air for nearly two decades. The chemistry between Cranston and Margo Lane adds warmth to even the darkest storylines, and this episode is no exception.</p>

<p>Whether you're a longtime fan of old time radio or discovering The Shadow for the first time, "{title}" is essential listening. It captures everything that made this show a cultural phenomenon — the mystery, the atmosphere, the unforgettable characters, and that delicious blend of terror and triumph.</p>

<h3>Listen Now</h3>

<p>Experience "{title}" and more classic Shadow episodes on the <a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">Ghost of Radio YouTube channel</a>. Subscribe so you never miss a broadcast from the golden age of radio. You can also find us on <a href="https://open.spotify.com" target="_blank" rel="noopener">Spotify</a> for listening on the go.</p>

<p><em>"Who knows what evil lurks in the hearts of men? The Shadow knows!"</em></p>"""


def generate_live_content(episode, client):
    """Generate blog post content using the Anthropic Claude API."""
    title = episode['title']
    date = format_date(episode['date'])
    desc = episode['description']

    prompt = f"""Write a thrilling 400-500 word blog post / episode guide for the old time radio episode:

Title: "{title}" from The Shadow
Air Date: {date}
Description: {desc}

Requirements:
- Hook the reader in the very first sentence — make it dramatic and atmospheric
- Summarize the plot dramatically WITHOUT giving away full spoilers
- Highlight the best/most memorable moment of the episode
- Write in an engaging, atmospheric style that captures the noir feel of 1930s radio
- End with a call-to-action to listen on the Ghost of Radio YouTube channel and on Spotify
- Output ONLY the HTML body content (use <p>, <h3>, <em>, <a> tags as needed)
- Do NOT include the episode title as a heading (it's already on the page)
- Include a link to https://www.youtube.com/@GhostOfRadio for YouTube
- Make the reader FEEL like they're sitting by the radio in 1937/1938
- Reference "The Shadow" show elements: Lamont Cranston, Margo Lane, the famous laugh, "The weed of crime bears bitter fruit"
- Keep it between 400-500 words"""

    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


def build_episode_page(episode, content, slug):
    """Build a full HTML page for an episode blog post."""
    title = episode['title']
    date = format_date(episode['date'])
    date_iso = episode['date']
    desc = episode['description']
    page_title = f"{title} | The Shadow | Ghost of Radio"
    canonical = f"https://ghostofradio.com/blog/shadow/{slug}.html"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <meta name="description" content="{desc}">
  <meta property="og:title" content="{page_title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="Ghost of Radio">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{page_title}">
  <meta name="twitter:description" content="{desc}">
  <link rel="canonical" href="{canonical}">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#0a0a0a">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="/images/logo.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/style.css">
</head>
<body>

  <!-- Header -->
  <header class="site-header">
    <nav class="nav">
      <a href="/index.html" class="nav__logo">
        <span class="nav__logo-icon"><img src="/images/logo.png" alt="Ghost of Radio" class="nav__logo-img"></span> Ghost of Radio
      </a>
      <button class="nav__toggle" aria-label="Toggle navigation" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
      <ul class="nav__links">
        <li><a href="/index.html">Home</a></li>
        <li><a href="/shows.html">Shows</a></li>
        <li><a href="/about.html">About</a></li>
        <li><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a></li>
      </ul>
    </nav>
  </header>

  <!-- Page Header -->
  <div class="page-header">
    <h1 class="flicker">{title}</h1>
    <div class="divider"></div>
    <p>The Shadow &middot; Originally aired {date}</p>
  </div>

  <!-- Blog Content -->
  <section class="section">
    <div class="container">
      <article class="about-content fade-in">
        <time datetime="{date_iso}" style="font-family: var(--font-heading); color: var(--text-muted); font-size: 0.85rem; letter-spacing: 0.15em; text-transform: uppercase;">{date}</time>

        {content}

        <div class="divider" style="margin: 3rem auto;"></div>

        <p style="text-align: center;">
          <a href="/blog/shadow/index.html" class="btn">All Shadow Episodes</a>
          <a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener" class="btn btn--filled" style="margin-left: 0.5rem;">&#9654; Watch on YouTube</a>
        </p>
      </article>
    </div>
  </section>

  <!-- Footer -->
  <footer class="site-footer">
    <div class="footer__inner">
      <div class="footer__brand">
        <div class="footer__brand-name"><img src="/images/logo.png" alt="Ghost of Radio" class="footer__logo-img"> Ghost of Radio</div>
        <p>Where vintage broadcasts return from the dead. Bringing the golden age of radio to a new generation on YouTube.</p>
        <div class="social-links">
          <a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">&#9654; YouTube</a>
          <a href="https://www.facebook.com/profile.php?id=61575492482642" target="_blank" rel="noopener">&#9403; Facebook</a>
        </div>
      </div>
      <div class="footer__links">
        <div class="footer__col">
          <h4>Navigate</h4>
          <ul>
            <li><a href="/index.html">Home</a></li>
            <li><a href="/shows.html">Shows</a></li>
            <li><a href="/about.html">About</a></li>
          </ul>
        </div>
        <div class="footer__col">
          <h4>Legal</h4>
          <ul>
            <li><a href="/privacy-policy.html">Privacy Policy</a></li>
            <li><a href="mailto:admin@ghostofradio.com">Contact</a></li>
          </ul>
        </div>
      </div>
    </div>
    <div class="footer__bottom">
      <p>&copy; <span class="current-year">2026</span> Ghost of Radio. All rights reserved. Classic radio programs are in the public domain.</p>
    </div>
  </footer>

  <script src="/js/main.js"></script>
</body>
</html>"""


def build_index_page(episodes, slugs):
    """Build the Shadow episode listing page."""
    episode_cards = []
    for episode, slug in zip(episodes, slugs):
        title = episode['title']
        date = format_date(episode['date'])
        desc = episode['description']
        episode_cards.append(f"""
        <a href="/blog/shadow/{slug}.html" class="blog-episode-card fade-in" style="display: block; padding: 1.5rem; border: 1px solid var(--border); background: var(--bg-card); margin-bottom: 1rem; text-decoration: none; transition: all 0.3s ease;">
          <div style="font-family: var(--font-heading); font-size: 0.8rem; color: var(--text-muted); letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 0.3rem;">{date}</div>
          <h3 style="font-size: 1.3rem; margin-bottom: 0.5rem;">{title}</h3>
          <p style="color: var(--text-dim); font-size: 0.95rem; margin: 0;">{desc}</p>
        </a>""")

    cards_html = '\n'.join(episode_cards)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Shadow Episode Guide | Ghost of Radio</title>
  <meta name="description" content="Complete episode guide for The Shadow old time radio show. Read about every classic episode featuring Lamont Cranston and Margo Lane.">
  <meta property="og:title" content="The Shadow Episode Guide | Ghost of Radio">
  <meta property="og:description" content="Complete episode guide for The Shadow old time radio show.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://ghostofradio.com/blog/shadow/index.html">
  <meta property="og:site_name" content="Ghost of Radio">
  <link rel="canonical" href="https://ghostofradio.com/blog/shadow/index.html">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#0a0a0a">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="/images/logo.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/style.css">
  <style>
    .blog-episode-card:hover {{
      border-color: var(--accent-dim) !important;
      transform: translateX(6px);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), 0 0 15px rgba(201, 168, 76, 0.1);
    }}
  </style>
</head>
<body>

  <!-- Header -->
  <header class="site-header">
    <nav class="nav">
      <a href="/index.html" class="nav__logo">
        <span class="nav__logo-icon"><img src="/images/logo.png" alt="Ghost of Radio" class="nav__logo-img"></span> Ghost of Radio
      </a>
      <button class="nav__toggle" aria-label="Toggle navigation" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
      <ul class="nav__links">
        <li><a href="/index.html">Home</a></li>
        <li><a href="/shows.html">Shows</a></li>
        <li><a href="/about.html">About</a></li>
        <li><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a></li>
      </ul>
    </nav>
  </header>

  <!-- Page Header -->
  <div class="page-header">
    <h1 class="flicker">The Shadow</h1>
    <div class="divider"></div>
    <p>Episode guide &mdash; "Who knows what evil lurks in the hearts of men?"</p>
  </div>

  <!-- Episode Listing -->
  <section class="section">
    <div class="container">
      <div style="max-width: 800px; margin: 0 auto;">
        {cards_html}
      </div>

      <div class="text-center mt-2 fade-in">
        <a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener" class="btn btn--filled">&#9654; Listen on YouTube</a>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="site-footer">
    <div class="footer__inner">
      <div class="footer__brand">
        <div class="footer__brand-name"><img src="/images/logo.png" alt="Ghost of Radio" class="footer__logo-img"> Ghost of Radio</div>
        <p>Where vintage broadcasts return from the dead. Bringing the golden age of radio to a new generation on YouTube.</p>
        <div class="social-links">
          <a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">&#9654; YouTube</a>
          <a href="https://www.facebook.com/profile.php?id=61575492482642" target="_blank" rel="noopener">&#9403; Facebook</a>
        </div>
      </div>
      <div class="footer__links">
        <div class="footer__col">
          <h4>Navigate</h4>
          <ul>
            <li><a href="/index.html">Home</a></li>
            <li><a href="/shows.html">Shows</a></li>
            <li><a href="/about.html">About</a></li>
          </ul>
        </div>
        <div class="footer__col">
          <h4>Legal</h4>
          <ul>
            <li><a href="/privacy-policy.html">Privacy Policy</a></li>
            <li><a href="mailto:admin@ghostofradio.com">Contact</a></li>
          </ul>
        </div>
      </div>
    </div>
    <div class="footer__bottom">
      <p>&copy; <span class="current-year">2026</span> Ghost of Radio. All rights reserved. Classic radio programs are in the public domain.</p>
    </div>
  </footer>

  <script src="/js/main.js"></script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description='Generate Shadow episode blog posts')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true', help='Generate placeholder content (no API calls)')
    group.add_argument('--live', action='store_true', help='Use Claude API for content generation')
    args = parser.parse_args()

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    episodes_file = script_dir / 'shadow_episodes.json'
    output_dir = project_root / 'blog' / 'shadow'

    # Load episodes
    with open(episodes_file, 'r') as f:
        episodes = json.load(f)

    print(f"Loaded {len(episodes)} episodes from {episodes_file}")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set up API client if live mode
    client = None
    if args.live:
        global anthropic
        import anthropic as anthropic_module
        anthropic = anthropic_module

        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print("Error: ANTHROPIC_API_KEY environment variable is required for --live mode")
            sys.exit(1)

        client = anthropic.Anthropic(api_key=api_key)
        print("Using Claude API for content generation...")
    else:
        print("Dry run mode — generating placeholder content...")

    # Generate individual episode pages
    slugs = []
    for i, episode in enumerate(episodes):
        slug = slugify(episode['title'])
        slugs.append(slug)

        print(f"  [{i + 1}/{len(episodes)}] {episode['title']} -> {slug}.html")

        if args.live:
            content = generate_live_content(episode, client)
        else:
            content = generate_placeholder_content(episode)

        page_html = build_episode_page(episode, content, slug)

        output_file = output_dir / f"{slug}.html"
        with open(output_file, 'w') as f:
            f.write(page_html)

    # Generate index page
    print(f"  Generating index.html...")
    index_html = build_index_page(episodes, slugs)
    with open(output_dir / 'index.html', 'w') as f:
        f.write(index_html)

    print(f"\nDone! Generated {len(episodes)} episode pages + index in {output_dir}/")


if __name__ == '__main__':
    main()
