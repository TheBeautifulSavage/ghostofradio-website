"""
Rebuild shows.html — searchable, genre filter buttons, show card images.
"""
from pathlib import Path
import subprocess

SITE = Path("/Users/mac1/Projects/ghostofradio")

SHOWS = [
    # Detective / Noir
    {"slug": "johnny-dollar",      "name": "Yours Truly, Johnny Dollar",       "years": "1949–1962", "network": "CBS",              "genre": "Detective"},
    {"slug": "sam-spade",          "name": "Sam Spade, Private Detective",      "years": "1946–1951", "network": "NBC / CBS",         "genre": "Detective"},
    {"slug": "philip-marlowe",     "name": "Philip Marlowe",                    "years": "1947–1951", "network": "NBC / CBS",         "genre": "Detective"},
    {"slug": "richard-diamond",    "name": "Richard Diamond",                   "years": "1949–1953", "network": "NBC / CBS",         "genre": "Detective"},
    {"slug": "broadway-beat",      "name": "Broadway Is My Beat",               "years": "1949–1954", "network": "CBS",               "genre": "Detective"},
    {"slug": "nightbeat",          "name": "Nightbeat",                         "years": "1950–1952", "network": "NBC",               "genre": "Detective"},
    {"slug": "let-george-do-it",   "name": "Let George Do It",                  "years": "1946–1954", "network": "Mutual",            "genre": "Detective"},
    {"slug": "the-falcon",         "name": "The Falcon",                        "years": "1943–1954", "network": "NBC / Mutual",      "genre": "Detective"},
    {"slug": "rogues-gallery",     "name": "Rogue's Gallery",                   "years": "1945–1951", "network": "NBC / Mutual",      "genre": "Detective"},
    {"slug": "dragnet",            "name": "Dragnet",                           "years": "1949–1957", "network": "NBC",               "genre": "Detective"},
    # Mystery / Thriller / Horror
    {"slug": "shadow",             "name": "The Shadow",                        "years": "1937–1954", "network": "Mutual",            "genre": "Mystery"},
    {"slug": "suspense",           "name": "Suspense",                          "years": "1942–1962", "network": "CBS",               "genre": "Mystery"},
    {"slug": "inner-sanctum",      "name": "Inner Sanctum Mysteries",           "years": "1941–1952", "network": "NBC / CBS",         "genre": "Mystery"},
    {"slug": "lights-out",         "name": "Lights Out",                        "years": "1934–1947", "network": "NBC / CBS",         "genre": "Mystery"},
    {"slug": "quiet-please",       "name": "Quiet Please",                      "years": "1947–1949", "network": "Mutual",            "genre": "Mystery"},
    {"slug": "mysterious-traveler","name": "The Mysterious Traveler",            "years": "1943–1953", "network": "Mutual",            "genre": "Mystery"},
    {"slug": "the-clock",          "name": "The Clock",                         "years": "1946–1948", "network": "NBC",               "genre": "Mystery"},
    {"slug": "cbs-mystery",        "name": "CBS Radio Mystery Theater",         "years": "1974–1982", "network": "CBS",               "genre": "Mystery"},
    {"slug": "whistler",           "name": "The Whistler",                      "years": "1942–1955", "network": "CBS",               "genre": "Mystery"},
    {"slug": "crime-classics",     "name": "Crime Classics",                    "years": "1953–1954", "network": "CBS",               "genre": "Mystery"},
    {"slug": "sherlock",           "name": "Sherlock Holmes",                   "years": "1930–1955", "network": "Various",           "genre": "Mystery"},
    # Western / Adventure
    {"slug": "loneranger",         "name": "The Lone Ranger",                   "years": "1933–1954", "network": "ABC",               "genre": "Western"},
    {"slug": "gunsmoke",           "name": "Gunsmoke",                          "years": "1952–1961", "network": "CBS",               "genre": "Western"},
    {"slug": "cisco-kid",          "name": "The Cisco Kid",                     "years": "1942–1956", "network": "Mutual",            "genre": "Western"},
    {"slug": "challenge-yukon",    "name": "Challenge of the Yukon",            "years": "1938–1955", "network": "ABC / Mutual",      "genre": "Western"},
    {"slug": "fort-laramie",       "name": "Fort Laramie",                      "years": "1956",      "network": "CBS",               "genre": "Western"},
    {"slug": "have-gun",           "name": "Have Gun Will Travel",              "years": "1958–1960", "network": "CBS",               "genre": "Western"},
    {"slug": "escape",             "name": "Escape",                            "years": "1947–1954", "network": "CBS",               "genre": "Adventure"},
    {"slug": "bold-venture",       "name": "Bold Venture",                      "years": "1951–1952", "network": "Syndicated",        "genre": "Adventure"},
    {"slug": "green-hornet",       "name": "The Green Hornet",                  "years": "1936–1952", "network": "NBC / ABC",         "genre": "Adventure"},
    {"slug": "dangerous-assignment","name":"Dangerous Assignment",               "years": "1949–1953", "network": "NBC",               "genre": "Adventure"},
    {"slug": "box-13",             "name": "Box 13",                            "years": "1948–1949", "network": "Syndicated",        "genre": "Adventure"},
    {"slug": "the-saint",          "name": "The Saint",                         "years": "1945–1951", "network": "NBC / CBS",         "genre": "Adventure"},
    # Sci-Fi
    {"slug": "dimension-x",        "name": "Dimension X",                       "years": "1950–1951", "network": "NBC",               "genre": "Sci-Fi"},
    {"slug": "x-minus-one",        "name": "X Minus One",                       "years": "1955–1958", "network": "NBC",               "genre": "Sci-Fi"},
    # Comedy
    {"slug": "fibber-mcgee",       "name": "Fibber McGee & Molly",              "years": "1935–1959", "network": "NBC",               "genre": "Comedy"},
    {"slug": "burns-allen",        "name": "The Burns and Allen Show",          "years": "1932–1950", "network": "CBS / NBC",         "genre": "Comedy"},
    {"slug": "bob-hope",           "name": "The Bob Hope Show",                 "years": "1938–1955", "network": "NBC",               "genre": "Comedy"},
    {"slug": "amos-andy",          "name": "Amos 'n' Andy",                     "years": "1928–1955", "network": "NBC / CBS",         "genre": "Comedy"},
    {"slug": "our-miss-brooks",    "name": "Our Miss Brooks",                   "years": "1948–1957", "network": "CBS",               "genre": "Comedy"},
    {"slug": "great-gildersleeve", "name": "The Great Gildersleeve",            "years": "1941–1957", "network": "NBC",               "genre": "Comedy"},
    {"slug": "red-skelton",        "name": "The Red Skelton Show",              "years": "1941–1953", "network": "NBC / CBS",         "genre": "Comedy"},
    {"slug": "ozzie-harriet",      "name": "The Adventures of Ozzie & Harriet", "years": "1944–1954", "network": "CBS / NBC",         "genre": "Comedy"},
    {"slug": "my-favorite-husband","name": "My Favorite Husband",               "years": "1948–1951", "network": "CBS",               "genre": "Comedy"},
    {"slug": "duffys-tavern",      "name": "Duffy's Tavern",                    "years": "1941–1951", "network": "CBS / NBC",         "genre": "Comedy"},
    # Drama
    {"slug": "lux-radio-theatre",  "name": "Lux Radio Theatre",                "years": "1934–1955", "network": "CBS / NBC",         "genre": "Drama"},
    {"slug": "mercury-theatre",    "name": "Mercury Theatre on the Air",        "years": "1938",      "network": "CBS",               "genre": "Drama"},
    {"slug": "stars-over-hollywood","name":"Stars Over Hollywood",              "years": "1941–1953", "network": "CBS",               "genre": "Drama"},
    {"slug": "railroad-hour",      "name": "The Railroad Hour",                 "years": "1948–1954", "network": "ABC",               "genre": "Drama"},
    {"slug": "death-valley-days",  "name": "Death Valley Days",                 "years": "1930–1945", "network": "NBC / CBS",         "genre": "Drama"},
]

GENRE_COLORS = {
    "Detective": "#c9a84c", "Mystery": "#7b2d8b", "Horror": "#cc2200",
    "Western": "#8b4513",   "Adventure": "#2d6a4f", "Sci-Fi": "#1a6b8a",
    "Comedy": "#e67e22",    "Drama": "#5d6d7e",
}

def count_episodes(slug):
    d = SITE / slug
    return len(list(d.glob("*.html"))) if d.exists() else 0

def has_image(slug):
    return (SITE / "images" / f"{slug}.jpg").exists()

def build():
    shows_data = []
    for s in SHOWS:
        ep = count_episodes(s["slug"])
        if ep == 0:
            continue
        img = f"/images/{s['slug']}.jpg" if has_image(s["slug"]) else "/images/hero.jpg"
        shows_data.append({**s, "episodes": ep, "img": img})

    total_eps = sum(s["episodes"] for s in shows_data)
    genres = sorted(set(s["genre"] for s in shows_data))

    # Build show cards JS data for search
    js_data = ",\n".join([
        f'{{slug:"{s["slug"]}",name:"{s["name"]}",genre:"{s["genre"]}",years:"{s["years"]}",eps:{s["episodes"]}}}'
        for s in shows_data
    ])

    # Build all show cards HTML (hidden by default, shown via JS)
    cards = ""
    for s in shows_data:
        color = GENRE_COLORS.get(s["genre"], "#c9a84c")
        cards += f'''<a href="/{s["slug"]}/" class="show-card" data-genre="{s["genre"]}" data-name="{s["name"].lower()}">
          <div class="show-card__img" style="background-image:url('{s["img"]}')">
            <span class="show-card__badge" style="background:{color}">{s["genre"]}</span>
          </div>
          <div class="show-card__body">
            <h3 class="show-card__title">{s["name"]}</h3>
            <div class="show-card__era">{s["years"]} · {s["network"]}</div>
            <div class="show-card__count">{s["episodes"]:,} episodes</div>
          </div>
        </a>\n'''

    genre_btns = '<button class="genre-btn active" data-genre="all">All Shows</button>\n'
    for g in genres:
        color = GENRE_COLORS.get(g, "#c9a84c")
        genre_btns += f'<button class="genre-btn" data-genre="{g}" style="--gc:{color}">{g}</button>\n'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>All Shows — Ghost of Radio | Classic Old Time Radio</title>
  <meta name="description" content="Browse {len(shows_data)} classic old time radio shows with {total_eps:,} free episodes. Search by genre — detective noir, westerns, horror, comedy, sci-fi and more.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/style.css">
  <link rel="manifest" href="/manifest.json">
  <link rel="apple-touch-icon" href="/images/logo.png">
  <style>
    .shows-toolbar {{
      display:flex; flex-wrap:wrap; gap:.75rem; align-items:center;
      margin-bottom:1.5rem; padding:1rem; background:#111; border-radius:8px;
      border:1px solid #222;
    }}
    .search-box {{
      flex:1; min-width:200px;
      background:#0a0a0a; border:1px solid #333; border-radius:6px;
      padding:.6rem 1rem; color:#f0dca0; font-size:.95rem;
      font-family:'Crimson Text',serif;
    }}
    .search-box::placeholder {{ color:#555; }}
    .search-box:focus {{ outline:none; border-color:#c9a84c; }}
    .genre-filters {{ display:flex; flex-wrap:wrap; gap:.5rem; }}
    .genre-btn {{
      background:#1a1a1a; border:1px solid #333; border-radius:20px;
      padding:.35rem .9rem; color:#888; font-size:.8rem; cursor:pointer;
      transition:all .2s; letter-spacing:.04em; text-transform:uppercase;
    }}
    .genre-btn:hover, .genre-btn.active {{
      background:var(--gc, #c9a84c); border-color:var(--gc, #c9a84c);
      color:#0a0a0a; font-weight:700;
    }}
    .genre-btn[data-genre="all"].active {{ background:#c9a84c; border-color:#c9a84c; color:#0a0a0a; }}
    .shows-count {{ color:#888; font-size:.85rem; margin-bottom:1rem; }}
    .shows-count span {{ color:#c9a84c; font-weight:700; }}
    .shows-grid {{
      display:grid;
      grid-template-columns:repeat(auto-fill,minmax(240px,1fr));
      gap:1.25rem;
    }}
    .show-card {{
      background:#111; border:1px solid #222; border-radius:8px;
      text-decoration:none; color:inherit; display:block;
      transition:border-color .2s, transform .2s; overflow:hidden;
    }}
    .show-card:hover {{ border-color:#c9a84c; transform:translateY(-3px); }}
    .show-card.hidden {{ display:none; }}
    .show-card__img {{
      height:150px; background-size:cover; background-position:center;
      position:relative;
    }}
    .show-card__badge {{
      position:absolute; top:.6rem; left:.6rem;
      font-size:.6rem; font-weight:700; letter-spacing:.08em;
      text-transform:uppercase; padding:.2rem .6rem; border-radius:4px; color:#fff;
    }}
    .show-card__body {{ padding:.9rem; }}
    .show-card__title {{
      font-family:'Special Elite',cursive; font-size:1rem;
      color:#f0dca0; margin:0 0 .3rem; line-height:1.3;
    }}
    .show-card__era {{ font-size:.72rem; color:#777; margin-bottom:.4rem; }}
    .show-card__count {{ font-size:.75rem; color:#c9a84c; font-weight:600; }}
    .no-results {{ text-align:center; color:#666; padding:3rem; font-size:1.1rem; display:none; }}
  </style>
</head>
<body>
  <header class="site-header">
    <nav class="nav">
      <a href="/index.html" class="nav__logo">
        <span class="nav__logo-icon"><img src="/images/logo.png" alt="Ghost of Radio" class="nav__logo-img"></span> Ghost of Radio
      </a>
      <button class="nav__toggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
      <ul class="nav__links">
        <li><a href="/index.html">Home</a></li>
        <li><a href="/shows.html" class="active">Shows</a></li>
        <li><a href="/about.html">About</a></li>
        <li><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a></li>
      </ul>
    </nav>
  </header>

  <div class="page-header">
    <h1 class="flicker">All Shows</h1>
    <div class="divider"></div>
    <p>{len(shows_data)} classic radio shows · {total_eps:,} episodes · All free to stream</p>
  </div>

  <section class="section">
    <div class="container">

      <div class="shows-toolbar">
        <input type="text" class="search-box" id="showSearch" placeholder="Search shows..." autocomplete="off">
        <div class="genre-filters">
          {genre_btns}
        </div>
      </div>

      <div class="shows-count">Showing <span id="showCount">{len(shows_data)}</span> shows</div>

      <div class="shows-grid" id="showsGrid">
        {cards}
      </div>
      <div class="no-results" id="noResults">No shows found. Try a different search.</div>

    </div>
  </section>

  <footer class="site-footer">
    <p>© 2025 Ghost of Radio · <a href="/about.html">About</a> · <a href="/privacy-policy.html">Privacy</a></p>
  </footer>

  <script src="/js/main.js"></script>
  <script>
    const cards = document.querySelectorAll('.show-card');
    const searchBox = document.getElementById('showSearch');
    const genreBtns = document.querySelectorAll('.genre-btn');
    const showCount = document.getElementById('showCount');
    const noResults = document.getElementById('noResults');
    let activeGenre = 'all';

    function filterShows() {{
      const q = searchBox.value.toLowerCase().trim();
      let visible = 0;
      cards.forEach(card => {{
        const name = card.dataset.name;
        const genre = card.dataset.genre;
        const matchSearch = !q || name.includes(q);
        const matchGenre = activeGenre === 'all' || genre === activeGenre;
        if (matchSearch && matchGenre) {{
          card.classList.remove('hidden');
          visible++;
        }} else {{
          card.classList.add('hidden');
        }}
      }});
      showCount.textContent = visible;
      noResults.style.display = visible === 0 ? 'block' : 'none';
    }}

    searchBox.addEventListener('input', filterShows);

    genreBtns.forEach(btn => {{
      btn.addEventListener('click', () => {{
        genreBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeGenre = btn.dataset.genre;
        filterShows();
      }});
    }});
  </script>
</body>
</html>'''

    out = SITE / "shows.html"
    out.write_text(html, encoding="utf-8")
    print(f"✅ shows.html rebuilt — {len(shows_data)} shows, {total_eps:,} episodes")
    return len(shows_data)

if __name__ == "__main__":
    n = build()
    subprocess.run(["git", "add", "shows.html"], cwd=SITE, capture_output=True)
    r = subprocess.run(["git", "commit", "-m", f"feat: shows page — search + genre filters + images ({n} shows)"],
                       cwd=SITE, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=SITE, capture_output=True)
    print("✅ Pushed")
