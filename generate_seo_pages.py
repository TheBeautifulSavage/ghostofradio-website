#!/usr/bin/env python3
"""Generate 10 SEO landing pages for ghostofradio.com using Claude Haiku."""

import anthropic
import os
import time

import subprocess, json as _json
_raw = subprocess.check_output(["python3", "-c", "import json; d=json.load(open('/Users/mac1/.openclaw/agents/main/agent/auth-profiles.json')); print(d['profiles']['anthropic:default']['key'])"])
API_KEY = _raw.decode().strip()
SITE_ROOT = "/Users/mac1/Projects/ghostofradio"

client = anthropic.Anthropic(api_key=API_KEY)

PAGES = [
    {
        "slug": "best-old-time-radio-shows-1940s.html",
        "keyword": "best old time radio shows 1940s",
        "title": "Best Old Time Radio Shows of the 1940s | Ghost of Radio",
        "og_title": "Best Old Time Radio Shows of the 1940s",
        "description": "Discover the best old time radio shows of the 1940s — golden age classics from mystery and comedy to drama and adventure. Listen free at Ghost of Radio.",
        "prompt": """Write a rich, 650-700 word SEO article for the keyword "best old time radio shows 1940s". 
Tone: authoritative, warm, nostalgic — like a knowledgeable OTR fan wrote it.

The article must include:
- Natural use of the target keyword and variations
- Show recommendations with these exact HTML links embedded inline:
  - <a href="https://ghostofradio.com/shadow/">The Shadow</a>
  - <a href="https://ghostofradio.com/suspense/">Suspense</a>
  - <a href="https://ghostofradio.com/jack-benny/">The Jack Benny Program</a>
  - <a href="https://ghostofradio.com/fibber-mcgee/">Fibber McGee and Molly</a>
  - <a href="https://ghostofradio.com/gunsmoke/">Gunsmoke</a>
  - <a href="https://ghostofradio.com/burns-allen/">Burns and Allen</a>
  - <a href="https://ghostofradio.com/inner-sanctum/">Inner Sanctum Mysteries</a>
  - <a href="https://ghostofradio.com/johnny-dollar/">Yours Truly, Johnny Dollar</a>
- A call to action pointing to ghostofradio.com to listen to these shows
- Use <h2> and <h3> subheadings (no h1, that will be added separately)
- Output ONLY the article HTML body content (h2s, p tags, etc) — no full HTML document wrapper"""
    },
    {
        "slug": "old-time-radio-sleep.html",
        "keyword": "old time radio to sleep to",
        "title": "Old Time Radio to Sleep To: Best Shows for Bedtime Listening | Ghost of Radio",
        "og_title": "Old Time Radio to Sleep To: Best Shows for Bedtime Listening",
        "description": "Looking for old time radio to sleep to? Discover the most soothing radio dramas and classic shows perfect for relaxing and drifting off. Listen free at Ghost of Radio.",
        "prompt": """Write a rich, 650-700 word SEO article for the keywords "old time radio to sleep to" and "sleep radio drama".
Tone: authoritative, warm, nostalgic — like a knowledgeable OTR fan wrote it.

The article must include:
- Natural use of the target keywords and variations
- Show recommendations with these exact HTML links embedded inline:
  - <a href="https://ghostofradio.com/suspense/">Suspense</a>
  - <a href="https://ghostofradio.com/quiet-please/">Quiet Please</a>
  - <a href="https://ghostofradio.com/inner-sanctum/">Inner Sanctum Mysteries</a>
  - <a href="https://ghostofradio.com/jack-benny/">The Jack Benny Program</a>
  - <a href="https://ghostofradio.com/fibber-mcgee/">Fibber McGee and Molly</a>
  - <a href="https://ghostofradio.com/escape/">Escape</a>
  - <a href="https://ghostofradio.com/johnny-dollar/">Yours Truly, Johnny Dollar</a>
- A call to action pointing to ghostofradio.com for sleep listening
- Use <h2> and <h3> subheadings
- Output ONLY the article HTML body content (h2s, p tags, etc) — no full HTML document wrapper"""
    },
    {
        "slug": "free-radio-drama-mp3.html",
        "keyword": "free radio drama mp3 download",
        "title": "Free Radio Drama MP3: Classic Old Time Radio Shows | Ghost of Radio",
        "og_title": "Free Radio Drama MP3: Classic Old Time Radio Shows",
        "description": "Find free radio drama MP3s and classic old time radio shows online. Stream or download episodes from the golden age of radio at Ghost of Radio.",
        "prompt": """Write a rich, 650-700 word SEO article for the keyword "free radio drama mp3 download".
Tone: authoritative, warm, nostalgic — like a knowledgeable OTR fan wrote it.

The article must include:
- Natural use of the target keyword and variations
- Show recommendations with these exact HTML links embedded inline:
  - <a href="https://ghostofradio.com/shadow/">The Shadow</a>
  - <a href="https://ghostofradio.com/suspense/">Suspense</a>
  - <a href="https://ghostofradio.com/inner-sanctum/">Inner Sanctum Mysteries</a>
  - <a href="https://ghostofradio.com/jack-benny/">The Jack Benny Program</a>
  - <a href="https://ghostofradio.com/gunsmoke/">Gunsmoke</a>
  - <a href="https://ghostofradio.com/johnny-dollar/">Yours Truly, Johnny Dollar</a>
  - <a href="https://ghostofradio.com/sam-spade/">The Adventures of Sam Spade</a>
  - <a href="https://ghostofradio.com/x-minus-one/">X Minus One</a>
- A call to action pointing to ghostofradio.com to stream/listen for free
- Use <h2> and <h3> subheadings
- Output ONLY the article HTML body content (h2s, p tags, etc) — no full HTML document wrapper"""
    },
    {
        "slug": "old-time-radio-mystery.html",
        "keyword": "old time radio mystery shows",
        "title": "Old Time Radio Mystery Shows: The Best Classic Whodunits | Ghost of Radio",
        "og_title": "Old Time Radio Mystery Shows: The Best Classic Whodunits",
        "description": "Explore the best old time radio mystery shows — from The Shadow to Inner Sanctum. Classic whodunits and thrillers streaming free at Ghost of Radio.",
        "prompt": """Write a rich, 650-700 word SEO article for the keyword "old time radio mystery shows".
Tone: authoritative, warm, nostalgic — like a knowledgeable OTR fan wrote it.

The article must include:
- Natural use of the target keyword and variations
- Show recommendations with these exact HTML links embedded inline:
  - <a href="https://ghostofradio.com/shadow/">The Shadow</a>
  - <a href="https://ghostofradio.com/suspense/">Suspense</a>
  - <a href="https://ghostofradio.com/inner-sanctum/">Inner Sanctum Mysteries</a>
  - <a href="https://ghostofradio.com/mysterious-traveler/">The Mysterious Traveler</a>
  - <a href="https://ghostofradio.com/sam-spade/">The Adventures of Sam Spade</a>
  - <a href="https://ghostofradio.com/philip-marlowe/">Philip Marlowe</a>
  - <a href="https://ghostofradio.com/johnny-dollar/">Yours Truly, Johnny Dollar</a>
- A call to action pointing to ghostofradio.com
- Use <h2> and <h3> subheadings
- Output ONLY the article HTML body content (h2s, p tags, etc) — no full HTML document wrapper"""
    },
    {
        "slug": "vintage-radio-shows-online.html",
        "keyword": "vintage radio shows online free",
        "title": "Vintage Radio Shows Online Free: Stream Classic OTR | Ghost of Radio",
        "og_title": "Vintage Radio Shows Online Free: Stream Classic OTR",
        "description": "Stream vintage radio shows online free — classic OTR programs from the golden age of broadcasting. Thousands of episodes at Ghost of Radio.",
        "prompt": """Write a rich, 650-700 word SEO article for the keyword "vintage radio shows online free".
Tone: authoritative, warm, nostalgic — like a knowledgeable OTR fan wrote it.

The article must include:
- Natural use of the target keyword and variations
- Show recommendations with these exact HTML links embedded inline:
  - <a href="https://ghostofradio.com/shadow/">The Shadow</a>
  - <a href="https://ghostofradio.com/suspense/">Suspense</a>
  - <a href="https://ghostofradio.com/jack-benny/">The Jack Benny Program</a>
  - <a href="https://ghostofradio.com/gunsmoke/">Gunsmoke</a>
  - <a href="https://ghostofradio.com/fibber-mcgee/">Fibber McGee and Molly</a>
  - <a href="https://ghostofradio.com/x-minus-one/">X Minus One</a>
  - <a href="https://ghostofradio.com/burns-allen/">Burns and Allen</a>
  - <a href="https://ghostofradio.com/loneranger/">The Lone Ranger</a>
- A call to action pointing to ghostofradio.com
- Use <h2> and <h3> subheadings
- Output ONLY the article HTML body content (h2s, p tags, etc) — no full HTML document wrapper"""
    },
    {
        "slug": "old-time-radio-comedy.html",
        "keyword": "old time radio comedy shows",
        "title": "Old Time Radio Comedy Shows: Classic Laughs from the Golden Age | Ghost of Radio",
        "og_title": "Old Time Radio Comedy Shows: Classic Laughs from the Golden Age",
        "description": "Discover the best old time radio comedy shows — Jack Benny, Burns and Allen, Fibber McGee and more. Classic laughs streaming free at Ghost of Radio.",
        "prompt": """Write a rich, 650-700 word SEO article for the keyword "old time radio comedy shows".
Tone: authoritative, warm, nostalgic — like a knowledgeable OTR fan wrote it.

The article must include:
- Natural use of the target keyword and variations
- Show recommendations with these exact HTML links embedded inline:
  - <a href="https://ghostofradio.com/jack-benny/">The Jack Benny Program</a>
  - <a href="https://ghostofradio.com/burns-allen/">Burns and Allen</a>
  - <a href="https://ghostofradio.com/fibber-mcgee/">Fibber McGee and Molly</a>
  - <a href="https://ghostofradio.com/great-gildersleeve/">The Great Gildersleeve</a>
  - <a href="https://ghostofradio.com/gunsmoke/">Gunsmoke</a>
- A call to action pointing to ghostofradio.com
- Use <h2> and <h3> subheadings
- Output ONLY the article HTML body content (h2s, p tags, etc) — no full HTML document wrapper"""
    },
    {
        "slug": "classic-radio-detective-shows.html",
        "keyword": "classic radio detective shows",
        "title": "Classic Radio Detective Shows: Hard-Boiled Mysteries of the Golden Age | Ghost of Radio",
        "og_title": "Classic Radio Detective Shows: Hard-Boiled Mysteries of the Golden Age",
        "description": "Explore the best classic radio detective shows — Sam Spade, Philip Marlowe, Johnny Dollar and more. Stream golden age detective dramas free at Ghost of Radio.",
        "prompt": """Write a rich, 650-700 word SEO article for the keyword "classic radio detective shows".
Tone: authoritative, warm, nostalgic — like a knowledgeable OTR fan wrote it.

The article must include:
- Natural use of the target keyword and variations
- Show recommendations with these exact HTML links embedded inline:
  - <a href="https://ghostofradio.com/sam-spade/">The Adventures of Sam Spade</a>
  - <a href="https://ghostofradio.com/philip-marlowe/">Philip Marlowe</a>
  - <a href="https://ghostofradio.com/johnny-dollar/">Yours Truly, Johnny Dollar</a>
  - <a href="https://ghostofradio.com/richard-diamond/">Richard Diamond, Private Detective</a>
  - <a href="https://ghostofradio.com/shadow/">The Shadow</a>
  - <a href="https://ghostofradio.com/suspense/">Suspense</a>
- A call to action pointing to ghostofradio.com
- Use <h2> and <h3> subheadings
- Output ONLY the article HTML body content (h2s, p tags, etc) — no full HTML document wrapper"""
    },
    {
        "slug": "old-time-radio-western.html",
        "keyword": "old time radio western shows",
        "title": "Old Time Radio Western Shows: Cowboys, Outlaws & Frontier Justice | Ghost of Radio",
        "og_title": "Old Time Radio Western Shows: Cowboys, Outlaws & Frontier Justice",
        "description": "Ride the frontier with the best old time radio western shows — Gunsmoke, The Lone Ranger, Have Gun Will Travel and more. Stream free at Ghost of Radio.",
        "prompt": """Write a rich, 650-700 word SEO article for the keyword "old time radio western shows".
Tone: authoritative, warm, nostalgic — like a knowledgeable OTR fan wrote it.

The article must include:
- Natural use of the target keyword and variations
- Show recommendations with these exact HTML links embedded inline:
  - <a href="https://ghostofradio.com/gunsmoke/">Gunsmoke</a>
  - <a href="https://ghostofradio.com/loneranger/">The Lone Ranger</a>
  - <a href="https://ghostofradio.com/have-gun/">Have Gun Will Travel</a>
  - <a href="https://ghostofradio.com/fort-laramie/">Fort Laramie</a>
  - <a href="https://ghostofradio.com/suspense/">Suspense</a>
- A call to action pointing to ghostofradio.com
- Use <h2> and <h3> subheadings
- Output ONLY the article HTML body content (h2s, p tags, etc) — no full HTML document wrapper"""
    },
    {
        "slug": "old-time-radio-horror.html",
        "keyword": "old time radio horror shows",
        "title": "Old Time Radio Horror Shows: Classic Spine-Chillers | Ghost of Radio",
        "og_title": "Old Time Radio Horror Shows: Classic Spine-Chillers",
        "description": "Discover the best old time radio horror shows — Lights Out, Inner Sanctum, Quiet Please and more. Classic terror from the golden age, streaming free at Ghost of Radio.",
        "prompt": """Write a rich, 650-700 word SEO article for the keyword "old time radio horror shows".
Tone: authoritative, warm, nostalgic — like a knowledgeable OTR fan wrote it.

The article must include:
- Natural use of the target keyword and variations
- Show recommendations with these exact HTML links embedded inline:
  - <a href="https://ghostofradio.com/lights-out/">Lights Out</a>
  - <a href="https://ghostofradio.com/inner-sanctum/">Inner Sanctum Mysteries</a>
  - <a href="https://ghostofradio.com/quiet-please/">Quiet Please</a>
  - <a href="https://ghostofradio.com/escape/">Escape</a>
  - <a href="https://ghostofradio.com/suspense/">Suspense</a>
  - <a href="https://ghostofradio.com/mysterious-traveler/">The Mysterious Traveler</a>
- A call to action pointing to ghostofradio.com
- Use <h2> and <h3> subheadings
- Output ONLY the article HTML body content (h2s, p tags, etc) — no full HTML document wrapper"""
    },
    {
        "slug": "old-time-radio-christmas.html",
        "keyword": "old time radio christmas episodes",
        "title": "Old Time Radio Christmas Episodes: Classic Holiday Broadcasts | Ghost of Radio",
        "og_title": "Old Time Radio Christmas Episodes: Classic Holiday Broadcasts",
        "description": "Celebrate the season with classic old time radio Christmas episodes from Jack Benny, Fibber McGee, Gunsmoke and more. Stream holiday classics free at Ghost of Radio.",
        "prompt": """Write a rich, 650-700 word SEO article for the keyword "old time radio christmas episodes".
Tone: authoritative, warm, nostalgic, festive — like a knowledgeable OTR fan wrote it.

The article must include:
- Natural use of the target keyword and variations
- Show recommendations with these exact HTML links embedded inline:
  - <a href="https://ghostofradio.com/jack-benny/">The Jack Benny Program</a>
  - <a href="https://ghostofradio.com/fibber-mcgee/">Fibber McGee and Molly</a>
  - <a href="https://ghostofradio.com/burns-allen/">Burns and Allen</a>
  - <a href="https://ghostofradio.com/great-gildersleeve/">The Great Gildersleeve</a>
  - <a href="https://ghostofradio.com/gunsmoke/">Gunsmoke</a>
  - <a href="https://ghostofradio.com/suspense/">Suspense</a>
  - <a href="https://ghostofradio.com/loneranger/">The Lone Ranger</a>
- A call to action pointing to ghostofradio.com for holiday listening
- Use <h2> and <h3> subheadings
- Output ONLY the article HTML body content (h2s, p tags, etc) — no full HTML document wrapper"""
    },
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <meta property="og:title" content="{og_title}">
  <meta property="og:description" content="{description}">
  <meta property="og:image" content="https://ghostofradio.com/images/hero.jpg">
  <meta property="og:type" content="article">
  <meta property="og:url" content="https://ghostofradio.com/{slug}">
  <link rel="canonical" href="https://ghostofradio.com/{slug}">
  <link href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/style.css">
  <style>
    .blog-content{{max-width:720px;margin:0 auto;padding:2rem 1rem;}}
    .blog-content h1{{font-family:'Special Elite',cursive;color:#c9a84c;font-size:2rem;margin-bottom:1rem;}}
    .blog-content h2{{font-family:'Special Elite',cursive;color:#e8e0d0;font-size:1.4rem;margin:2rem 0 .75rem;}}
    .blog-content h3{{color:#c9a84c;font-size:1.1rem;margin:1.5rem 0 .5rem;}}
    .blog-content p{{color:#aaa;line-height:1.8;margin-bottom:1rem;}}
    .blog-content a{{color:#c9a84c;}}
    .blog-date{{color:#666;font-size:.85rem;margin-bottom:2rem;}}
    .blog-content ul{{color:#aaa;line-height:1.8;margin-bottom:1rem;padding-left:1.5rem;}}
    .blog-content li{{margin-bottom:.5rem;}}
  </style>
</head>
<body>
  <header class="site-header">
    <nav class="nav">
      <a href="/index.html" class="nav__logo"><span class="nav__logo-icon"><img src="/images/logo.png" alt="Ghost of Radio" class="nav__logo-img"></span> Ghost of Radio</a>
      <ul class="nav__links">
        <li><a href="/index.html">Home</a></li>
        <li><a href="/shows.html">Shows</a></li>
        <li><a href="/blog/">Blog</a></li>
      </ul>
    </nav>
  </header>
  <div class="blog-content">
    <p class="blog-date">Ghost of Radio · Old Time Radio Guide</p>
    <h1>{og_title}</h1>
    {article_body}
  </div>
  <footer class="site-footer"><div class="container"><p>&copy; 2025 Ghost of Radio · <a href="/shows.html">All Shows</a> · <a href="/blog/">Blog</a></p></div></footer>
  <script src="/js/main.js"></script>
</body>
</html>"""


def generate_article(page):
    """Call Claude Haiku to generate article body HTML."""
    print(f"  Generating: {page['slug']}...")
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": page["prompt"]
            }
        ]
    )
    return message.content[0].text


def build_page(page, article_body):
    """Render the full HTML page."""
    return HTML_TEMPLATE.format(
        title=page["title"],
        description=page["description"],
        og_title=page["og_title"],
        slug=page["slug"],
        article_body=article_body
    )


def main():
    created = []
    for page in PAGES:
        try:
            article_body = generate_article(page)
            html = build_page(page, article_body)
            output_path = os.path.join(SITE_ROOT, page["slug"])
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  ✅ Saved: {output_path}")
            created.append(page["slug"])
            # Small delay to be polite to the API
            time.sleep(1)
        except Exception as e:
            print(f"  ❌ Error for {page['slug']}: {e}")
    
    print(f"\nDone! Created {len(created)}/{len(PAGES)} pages.")
    for slug in created:
        print(f"  - /{slug}")


if __name__ == "__main__":
    main()
