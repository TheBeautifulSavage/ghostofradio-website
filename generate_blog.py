#!/usr/bin/env python3
import anthropic, json, time
from pathlib import Path

with open('/Users/mac1/.openclaw/agents/main/agent/auth-profiles.json') as f:
    d = json.load(f)
key = d['profiles']['anthropic:default']['key']
client = anthropic.Anthropic(api_key=key)

BLOG_DIR = Path('/Users/mac1/Projects/ghostofradio/blog')
BLOG_DIR.mkdir(exist_ok=True)

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{TITLE} | Ghost of Radio</title>
  <meta name="description" content="{DESCRIPTION}">
  <link rel="canonical" href="https://ghostofradio.com/blog/{SLUG}.html">
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
    {CONTENT}
  </div>
  <footer class="site-footer"><div class="container"><p>&copy; 2025 Ghost of Radio · <a href="/shows.html">All Shows</a> · <a href="/blog/">Blog</a></p></div></footer>
  <script src="/js/main.js"></script>
</body>
</html>'''

POSTS = [
    {
        "slug": "best-old-time-radio-shows",
        "title": "The Best Old Time Radio Shows of the Golden Age",
        "keyword": "best old time radio shows",
        "description": "Discover the best old time radio shows from the Golden Age of Radio. From detective dramas to comedy classics, explore the shows that defined American broadcasting.",
    },
    {
        "slug": "johnny-dollar-complete-guide",
        "title": "Yours Truly Johnny Dollar: The Complete Episode Guide",
        "keyword": "Yours Truly Johnny Dollar episodes",
        "description": "The definitive guide to Yours Truly Johnny Dollar episodes — the expense-account detective who solved impossible cases across America's airwaves from 1949 to 1962.",
    },
    {
        "slug": "sam-spade-radio-show-guide",
        "title": "The Adventures of Sam Spade Radio Show: A Complete Guide",
        "keyword": "Sam Spade radio show",
        "description": "Explore the Sam Spade radio show, starring Howard Duff as Dashiell Hammett's iconic detective. The full story of one of radio's greatest private eye dramas.",
    },
    {
        "slug": "the-shadow-radio-history",
        "title": "The Shadow Radio Show: Who Knows What Evil Lurks in the Hearts of Men?",
        "keyword": "The Shadow radio show",
        "description": "The complete history of The Shadow radio show — from pulp magazine origins to Orson Welles and beyond. Discover why this classic crime drama still captivates listeners.",
    },
    {
        "slug": "dragnet-radio-show-history",
        "title": "Dragnet Radio Show: Jack Webb and the Birth of Police Procedural Drama",
        "keyword": "Dragnet radio show Jack Webb",
        "description": "The story of Dragnet on radio — how Jack Webb created the most realistic police procedural in broadcasting history. Just the facts about radio's greatest cop show.",
    },
    {
        "slug": "suspense-radio-show-episodes",
        "title": "Suspense: CBS Radio's Greatest Thriller Anthology",
        "keyword": "Suspense radio show CBS",
        "description": "Explore the Suspense radio show on CBS — 945 episodes of edge-of-your-seat drama featuring Hollywood's biggest stars. The definitive guide to radio's greatest thriller series.",
    },
    {
        "slug": "golden-age-of-radio-history",
        "title": "The Golden Age of Radio: America's First Mass Media Revolution",
        "keyword": "golden age of radio",
        "description": "The complete history of the golden age of radio — from the 1920s to the 1950s. How radio transformed American culture, entertainment, and news forever.",
    },
    {
        "slug": "best-radio-detective-shows",
        "title": "The Best Radio Detective Shows Ever Made",
        "keyword": "best radio detective shows",
        "description": "The definitive ranking of the best radio detective shows from the Golden Age — Johnny Dollar, Sam Spade, Philip Marlowe, and more. Classic crime drama at its finest.",
    },
    {
        "slug": "lone-ranger-radio-show",
        "title": "The Lone Ranger Radio Show: Hi-Yo Silver and the Birth of a Legend",
        "keyword": "Lone Ranger radio show",
        "description": "The complete history of The Lone Ranger radio show — from its 1933 debut to its lasting cultural impact. How a masked Texas Ranger became an American icon.",
    },
    {
        "slug": "gunsmoke-radio-show-history",
        "title": "Gunsmoke Radio Show: Matt Dillon and the Original Western Drama",
        "keyword": "Gunsmoke radio show Matt Dillon",
        "description": "The full story of the Gunsmoke radio show and Marshal Matt Dillon — the adult Western that revolutionized radio drama before conquering television.",
    },
    {
        "slug": "fibber-mcgee-molly-guide",
        "title": "Fibber McGee and Molly: The Radio Show That Made America Laugh",
        "keyword": "Fibber McGee and Molly radio",
        "description": "The complete guide to Fibber McGee and Molly — the beloved radio comedy that ran for 24 years and gave us one of broadcasting's most enduring gags.",
    },
    {
        "slug": "orson-welles-mercury-theatre",
        "title": "Orson Welles and the Mercury Theatre: The War of the Worlds Broadcast",
        "keyword": "Orson Welles radio show War of Worlds",
        "description": "The complete story of Orson Welles' Mercury Theatre on the Air and the legendary War of the Worlds broadcast that panicked a nation on Halloween 1938.",
    },
    {
        "slug": "jack-benny-radio-show",
        "title": "The Jack Benny Radio Show: America's Most Beloved Comic",
        "keyword": "Jack Benny radio show",
        "description": "Explore The Jack Benny radio show — the comedy that dominated American radio for two decades and created the template for modern sitcoms. The Jack Benny Program complete guide.",
    },
    {
        "slug": "inner-sanctum-mysteries-guide",
        "title": "Inner Sanctum Mysteries: Radio's Creaking Door to Terror",
        "keyword": "Inner Sanctum Mysteries radio",
        "description": "The complete guide to Inner Sanctum Mysteries radio — the chilling anthology horror series known for its creaking door intro and macabre stories that haunted listeners.",
    },
    {
        "slug": "x-minus-one-sci-fi-radio",
        "title": "X Minus One: The Greatest Science Fiction Radio Show Ever Made",
        "keyword": "X Minus One science fiction radio",
        "description": "X Minus One science fiction radio — the NBC anthology that brought Asimov, Bradbury, and Heinlein to life. The definitive guide to radio's greatest sci-fi series.",
    },
    {
        "slug": "burns-allen-radio-show",
        "title": "The Burns and Allen Radio Show: George and Gracie's Comic Genius",
        "keyword": "Burns and Allen radio show",
        "description": "The complete history of the Burns and Allen radio show — how George Burns and Gracie Allen revolutionized comedy broadcasting with their unique brand of wit.",
    },
    {
        "slug": "old-time-radio-history",
        "title": "Old Time Radio History: How Broadcasting Changed America",
        "keyword": "old time radio history",
        "description": "The complete story of old time radio history — from Marconi's experiments to the fall of network radio. How the golden age of broadcasting shaped American culture.",
    },
    {
        "slug": "radio-drama-golden-age",
        "title": "Radio Drama in the 1940s: The Art Form That Captivated a Nation",
        "keyword": "radio drama 1940s",
        "description": "Radio drama in the 1940s was America's most popular entertainment. Explore how writers, directors, and actors created vivid worlds using only sound — and why it still matters.",
    },
    {
        "slug": "free-old-time-radio-streaming",
        "title": "Free Old Time Radio Online: Where to Stream Classic Shows",
        "keyword": "free old time radio online",
        "description": "Discover the best places to listen to free old time radio online. Stream thousands of classic episodes from the Golden Age of Radio — no subscription required.",
    },
    {
        "slug": "classic-radio-shows-list",
        "title": "The Ultimate Classic Radio Shows List: 50+ Shows You Should Know",
        "keyword": "classic radio shows list",
        "description": "The definitive classic radio shows list — 50+ essential programs from the Golden Age of Radio. Comedies, dramas, westerns, mysteries, and sci-fi you need to hear.",
    },
]

def generate_blog_post(title, keyword, slug):
    print(f"  Generating: {title}...")
    msg = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2000,
        messages=[{"role":"user","content":f"""Write a compelling, SEO-optimized blog post for a classic old time radio website.

Title: {title}
Target keyword: {keyword}
Site: ghostofradio.com

Requirements:
- 600-900 words
- Include the target keyword naturally 4-6 times
- Include headings (H2, H3)
- Engaging, historically accurate
- End with CTA to explore ghostofradio.com
- Link to relevant show pages like /johnny-dollar/, /sam-spade/, /shadow/, /dragnet/, /suspense/, /gunsmoke/, /loneranger/, /fibber-mcgee/, /mercury-theatre/, /jack-benny/, /inner-sanctum/, /x-minus-one/, /burns-allen/ etc. where relevant

Return ONLY the HTML body content (no html/head/body tags), starting with <h1>"""}]
    )
    return msg.content[0].text

results = []
for post in POSTS:
    try:
        content = generate_blog_post(post['title'], post['keyword'], post['slug'])
        html = HTML_TEMPLATE.format(
            TITLE=post['title'],
            DESCRIPTION=post['description'],
            SLUG=post['slug'],
            CONTENT=content
        )
        filepath = BLOG_DIR / f"{post['slug']}.html"
        filepath.write_text(html, encoding='utf-8')
        results.append({"slug": post['slug'], "title": post['title'], "description": post['description'], "status": "ok"})
        print(f"  ✓ Saved: {post['slug']}.html")
        time.sleep(0.5)  # small delay to avoid rate limits
    except Exception as e:
        print(f"  ✗ Error on {post['slug']}: {e}")
        results.append({"slug": post['slug'], "title": post['title'], "description": post['description'], "status": "error"})

# Create blog index page
print("\nCreating blog index...")

INDEX_CARDS = ""
for r in results:
    if r['status'] == 'ok':
        INDEX_CARDS += f'''    <article class="blog-card">
      <h2><a href="/blog/{r['slug']}.html">{r['title']}</a></h2>
      <p>{r['description']}</p>
    </article>\n'''

INDEX_HTML = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Old Time Radio Blog | Ghost of Radio</title>
  <meta name="description" content="The Ghost of Radio blog — your guide to classic old time radio shows, golden age history, and the greatest broadcasts ever made.">
  <link rel="canonical" href="https://ghostofradio.com/blog/">
  <link href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/style.css">
  <style>
    .blog-index{{max-width:800px;margin:0 auto;padding:2rem 1rem;}}
    .blog-index h1{{font-family:'Special Elite',cursive;color:#c9a84c;font-size:2.5rem;margin-bottom:.5rem;text-align:center;}}
    .blog-index .subtitle{{color:#888;text-align:center;margin-bottom:3rem;font-style:italic;}}
    .blog-card{{border-bottom:1px solid #2a2a2a;padding:1.5rem 0;}}
    .blog-card:last-child{{border-bottom:none;}}
    .blog-card h2{{font-family:'Special Elite',cursive;font-size:1.3rem;margin-bottom:.5rem;}}
    .blog-card h2 a{{color:#e8e0d0;text-decoration:none;}}
    .blog-card h2 a:hover{{color:#c9a84c;}}
    .blog-card p{{color:#888;line-height:1.7;margin:0;}}
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
  <div class="blog-index">
    <h1>Old Time Radio Blog</h1>
    <p class="subtitle">Guides, history, and deep dives into the Golden Age of Radio</p>
{INDEX_CARDS}
  </div>
  <footer class="site-footer"><div class="container"><p>&copy; 2025 Ghost of Radio · <a href="/shows.html">All Shows</a> · <a href="/blog/">Blog</a></p></div></footer>
  <script src="/js/main.js"></script>
</body>
</html>'''

(BLOG_DIR / 'index.html').write_text(INDEX_HTML, encoding='utf-8')
print("✓ Blog index created")

ok_count = sum(1 for r in results if r['status'] == 'ok')
print(f"\nDone! Created {ok_count}/20 blog posts + index page")
