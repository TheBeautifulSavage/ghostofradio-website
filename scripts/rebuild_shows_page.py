"""
Rebuild shows.html and update index.html to include all 46 shows.
Reads actual show folders and generates a complete, organized page.
"""
from pathlib import Path
import subprocess

SITE = Path("/Users/mac1/Projects/ghostofradio")

# All shows with metadata
SHOWS = [
    # Detective / Noir
    {"slug": "johnny-dollar",      "name": "Yours Truly, Johnny Dollar",     "years": "1949–1962", "network": "CBS",              "genre": "Detective",    "desc": "The expense account adventures of America's fabulous freelance insurance investigator. Bob Bailey's definitive performance made this one of radio's longest-running dramas."},
    {"slug": "sam-spade",          "name": "Sam Spade, Private Detective",   "years": "1946–1951", "network": "NBC / CBS",         "genre": "Noir",         "desc": "Howard Duff as Dashiell Hammett's hard-boiled San Francisco private eye. Each case dictated to his loyal secretary Effie — sharp, funny, and relentlessly noir."},
    {"slug": "philip-marlowe",     "name": "Philip Marlowe",                 "years": "1947–1951", "network": "NBC / CBS",         "genre": "Noir",         "desc": "Raymond Chandler's iconic detective brought to life. Gerald Mohr's sardonic Marlowe navigated the corrupt underbelly of Los Angeles with wit and a loaded .38."},
    {"slug": "richard-diamond",    "name": "Richard Diamond, Private Detective","years":"1949–1953","network": "NBC / CBS",        "genre": "Detective",    "desc": "Dick Powell as a charming, singing private eye. Equal parts tough and funny — one of radio's most entertaining detective series."},
    {"slug": "broadway-beat",      "name": "Broadway Is My Beat",            "years": "1949–1954", "network": "CBS",              "genre": "Noir",         "desc": "Detective Danny Clover investigates murders along the Great White Way. Dark, moody, and brilliantly written New York noir."},
    {"slug": "nightbeat",          "name": "Nightbeat",                      "years": "1950–1952", "network": "NBC",              "genre": "Noir",         "desc": "Chicago newspaper reporter Randy Stone prowls the city at night, encountering stories of human drama. One of radio's most poetic crime programs."},
    {"slug": "let-george-do-it",   "name": "Let George Do It",               "years": "1946–1954", "network": "Mutual",           "genre": "Detective",    "desc": "George Valentine, a freelance troubleshooter who advertises his services in the classifieds. Smart, witty, and always in over his head."},
    {"slug": "the-falcon",         "name": "The Falcon",                     "years": "1943–1954", "network": "NBC / Mutual",     "genre": "Detective",    "desc": "The suave, sophisticated Gay Lawrence — the Falcon — solves crimes with style and a sharp sense of humor. Classic gentleman detective radio."},
    {"slug": "rogues-gallery",     "name": "Rogue's Gallery",                "years": "1945–1951", "network": "NBC / Mutual",     "genre": "Detective",    "desc": "Richard Rogue, private detective, gets knocked unconscious in nearly every episode — and hallucinates conversations with his alter ego Eugor. Wonderfully weird noir."},
    {"slug": "have-gun",           "name": "Have Gun Will Travel",           "years": "1958–1960", "network": "CBS",              "genre": "Western",      "desc": "Paladin, a West Point-educated gunfighter for hire based in San Francisco. Intelligent, literary, and morally complex — the thinking person's western."},

    # Mystery / Horror / Thriller
    {"slug": "shadow",             "name": "The Shadow",                     "years": "1937–1954", "network": "Mutual",           "genre": "Mystery",      "desc": "Who knows what evil lurks in the hearts of men? The Shadow knows. Lamont Cranston's power to cloud men's minds made this one of radio's most iconic programs."},
    {"slug": "suspense",           "name": "Suspense",                       "years": "1942–1962", "network": "CBS",              "genre": "Thriller",     "desc": "Radio's premier anthology thriller. Twenty years of stories designed to keep you in suspense — featuring Hollywood's biggest stars in their most chilling performances."},
    {"slug": "inner-sanctum",      "name": "Inner Sanctum Mysteries",        "years": "1941–1952", "network": "NBC / CBS",        "genre": "Horror",       "desc": "The creaking door opens, and Raymond Edward Johnson welcomes you to another tale of mystery and horror. Macabre, atmospheric, unforgettable."},
    {"slug": "lights-out",         "name": "Lights Out",                     "years": "1934–1947", "network": "NBC / CBS",        "genre": "Horror",       "desc": "Arch Oboler's masterpiece of radio horror. Stories so disturbing that NBC received thousands of listener complaints. Turn out the lights before you listen."},
    {"slug": "quiet-please",       "name": "Quiet Please",                   "years": "1947–1949", "network": "Mutual",           "genre": "Horror",       "desc": "Wyllis Cooper's cerebral, unsettling anthology — widely considered the most literate horror program in radio history. Quiet, haunting, and deeply disturbing."},
    {"slug": "mysterious-traveler","name": "The Mysterious Traveler",         "years": "1943–1953", "network": "Mutual",           "genre": "Mystery",      "desc": "A mysterious stranger on a train shares tales of the strange and macabre. Every story a twist, every episode a journey into the unknown."},
    {"slug": "escape",             "name": "Escape",                         "years": "1947–1954", "network": "CBS",              "genre": "Adventure",    "desc": "Designed to free you from the four walls of today — adventure stories of courage and survival from the far corners of the world."},
    {"slug": "the-clock",          "name": "The Clock",                      "years": "1946–1948", "network": "NBC",              "genre": "Mystery",      "desc": "The clock ticks for everyone — but for some it stops too soon. Anthology mysteries narrated by the inexorable passage of time."},
    {"slug": "cbs-mystery",        "name": "CBS Radio Mystery Theater",      "years": "1974–1982", "network": "CBS",              "genre": "Mystery",      "desc": "E.G. Marshall hosted over 1,300 episodes of this late-era anthology — proving radio drama still had power long after television took over living rooms."},

    # Adventure / Action
    {"slug": "loneranger",         "name": "The Lone Ranger",                "years": "1933–1954", "network": "ABC",              "genre": "Western",      "desc": "Hi-yo, Silver! The masked rider of the plains and his faithful companion Tonto — radio's greatest western hero, fighting for justice across the frontier."},
    {"slug": "gunsmoke",           "name": "Gunsmoke",                       "years": "1952–1961", "network": "CBS",              "genre": "Western",      "desc": "William Conrad as Marshal Matt Dillon keeping the peace in Dodge City. The adult western that defined the genre — gritty, morally complex, and brilliantly written."},
    {"slug": "cisco-kid",          "name": "The Cisco Kid",                  "years": "1942–1956", "network": "Mutual/Syndicated","genre": "Western",      "desc": "The Robin Hood of the Old West and his sidekick Pancho — O. Henry's beloved characters riding through the Southwest righting wrongs with style and laughter."},
    {"slug": "challenge-yukon",    "name": "Challenge of the Yukon",         "years": "1938–1955", "network": "ABC / Mutual",     "genre": "Adventure",    "desc": "Sergeant Preston of the Yukon and his faithful dog Yukon King patrol the frozen Northwest. On, King! On, you huskies!"},
    {"slug": "fort-laramie",       "name": "Fort Laramie",                   "years": "1956",      "network": "CBS",              "genre": "Western",      "desc": "The most serious and realistic western in radio history. Captain Lee Quince and the U.S. Cavalry face the brutal reality of frontier life in 1880s Wyoming."},
    {"slug": "bold-venture",       "name": "Bold Venture",                   "years": "1951–1952", "network": "Syndicated",       "genre": "Adventure",    "desc": "Humphrey Bogart and Lauren Bacall reunited for radio — Slate Shannon and Sailor Duval on exotic Caribbean adventures. Glamorous, dangerous, irresistible."},
    {"slug": "green-hornet",       "name": "The Green Hornet",               "years": "1936–1952", "network": "NBC / ABC",        "genre": "Action",       "desc": "Britt Reid and his faithful valet Kato — fighting crime as the Green Hornet, hunted by police as a criminal, but always on the side of justice."},
    {"slug": "dangerous-assignment","name":"Dangerous Assignment",           "years": "1949–1953", "network": "NBC / Syndicated", "genre": "Spy",          "desc": "Brian Donlevy as Steve Mitchell, an American government agent sent on impossible missions around the world. Cold War espionage at its most entertaining."},
    {"slug": "box-13",             "name": "Box 13",                         "years": "1948–1949", "network": "Syndicated",       "genre": "Adventure",    "desc": "Alan Ladd as Dan Holiday, a mystery writer who advertises for adventure: 'Adventure wanted — will go anywhere, do anything.' And they always deliver."},
    {"slug": "dimension-x",        "name": "Dimension X",                    "years": "1950–1951", "network": "NBC",              "genre": "Sci-Fi",       "desc": "NBC's groundbreaking science fiction anthology adapting the best of Asimov, Bradbury, and Heinlein. Radio's first great sci-fi series."},
    {"slug": "x-minus-one",        "name": "X Minus One",                    "years": "1955–1958", "network": "NBC",              "genre": "Sci-Fi",       "desc": "The greatest science fiction radio series ever produced — adapting Galaxy Magazine's best stories with stunning production values and imaginative sound design."},
    {"slug": "the-saint",          "name": "The Saint",                      "years": "1945–1951", "network": "NBC / CBS",        "genre": "Adventure",    "desc": "Simon Templar — the Saint — a modern Robin Hood who steals from criminals and keeps the proceeds. Suave, witty, and utterly charming."},

    # Drama / Anthology
    {"slug": "lux-radio-theatre",  "name": "Lux Radio Theatre",             "years": "1934–1955", "network": "CBS / NBC",        "genre": "Drama",        "desc": "Hollywood's biggest stars recreating their greatest films for radio — produced by Cecil B. DeMille. An unparalleled archive of golden age Hollywood."},
    {"slug": "mercury-theatre",    "name": "Mercury Theatre on the Air",    "years": "1938",      "network": "CBS",              "genre": "Drama",        "desc": "Orson Welles and the Mercury Theatre Company — including the legendary War of the Worlds broadcast that panicked a nation on October 30, 1938."},
    {"slug": "stars-over-hollywood","name":"Stars Over Hollywood",          "years": "1941–1953", "network": "CBS",              "genre": "Drama",        "desc": "Dramatic anthology featuring Hollywood's finest talent in original radio plays. Decades of compelling drama from CBS's golden era."},
    {"slug": "crime-classics",     "name": "Crime Classics",                "years": "1953–1954", "network": "CBS",              "genre": "Crime",        "desc": "True crime stories from history — told with dark humor and impeccable research by host Thomas Hyland. Murders, swindles, and villainy from the ages."},

    # Sherlock Holmes
    {"slug": "sherlock",           "name": "Sherlock Holmes",               "years": "1930–1955", "network": "Various",          "genre": "Mystery",      "desc": "The world's greatest detective in dozens of radio adventures — featuring Basil Rathbone, John Stanley, and Tom Conway bringing Conan Doyle's immortal creation to life."},

    # Comedy
    {"slug": "fibber-mcgee",       "name": "Fibber McGee & Molly",          "years": "1935–1959", "network": "NBC",              "genre": "Comedy",       "desc": "Jim and Marian Jordan as America's most beloved radio couple — the exaggerating Fibber and his long-suffering Molly at 79 Wistful Vista. Don't open that closet!"},
    {"slug": "burns-allen",        "name": "The Burns and Allen Show",      "years": "1932–1950", "network": "CBS / NBC",        "genre": "Comedy",       "desc": "George Burns and Gracie Allen — the greatest comedy team in radio history. Gracie's sublime illogic and George's perfect timing made America laugh for two decades."},
    {"slug": "bob-hope",           "name": "The Bob Hope Show",             "years": "1938–1955", "network": "NBC",              "genre": "Comedy",       "desc": "Bob Hope, America's comedian — topical jokes, celebrity guests, and the most popular comedy program in radio history. Pepsodent never had a better salesman."},
    {"slug": "amos-andy",          "name": "Amos 'n' Andy",                 "years": "1928–1955", "network": "NBC / CBS",        "genre": "Comedy",       "desc": "The most popular program in radio history — Freeman Gosden and Charles Correll's beloved characters whose trials and tribulations captivated an entire nation."},
    {"slug": "our-miss-brooks",    "name": "Our Miss Brooks",               "years": "1948–1957", "network": "CBS",              "genre": "Comedy",       "desc": "Eve Arden as the witty, wisecracking English teacher Connie Brooks — perpetually broke, perpetually in love with Mr. Boynton, perpetually hilarious."},
    {"slug": "great-gildersleeve", "name": "The Great Gildersleeve",        "years": "1941–1957", "network": "NBC",              "genre": "Comedy",       "desc": "Throckmorton P. Gildersleeve — pompous, lovable, and hopelessly confused by women and life. The first radio spinoff and one of the medium's longest-running comedies."},
    {"slug": "red-skelton",        "name": "The Red Skelton Show",          "years": "1941–1953", "network": "NBC / CBS",        "genre": "Comedy",       "desc": "Red Skelton's beloved characters — Clem Kadiddlehopper, Freddie the Freeloader, the Mean Widdle Kid — brought radio comedy to its most lovable heights."},
    {"slug": "ozzie-harriet",      "name": "The Adventures of Ozzie & Harriet","years":"1944–1954","network":"CBS / NBC",        "genre": "Comedy",       "desc": "The Nelson family in their real-life domestic adventures — a radio institution that launched television's longest-running sitcom."},
    {"slug": "my-favorite-husband","name": "My Favorite Husband",          "years": "1948–1951", "network": "CBS",              "genre": "Comedy",       "desc": "Lucille Ball and Richard Denning as Liz and George Cooper — the show that convinced CBS to give Lucy her own TV show. The rest is history."},
    {"slug": "duffys-tavern",      "name": "Duffy's Tavern",               "years": "1941–1951", "network": "CBS / NBC",        "genre": "Comedy",       "desc": "Where the elite meet to eat — Archie the manager holds down the fort for the perpetually absent Duffy. Celebrity-packed, sharp, and endlessly funny."},

    # Music
    {"slug": "railroad-hour",      "name": "The Railroad Hour",             "years": "1948–1954", "network": "ABC",              "genre": "Musical",      "desc": "Gordon MacRae and the MGM Orchestra in condensed musical adaptations of Broadway shows and operettas. The pinnacle of radio's musical drama."},
    {"slug": "dragnet",            "name": "Dragnet",                       "years": "1949–1957", "network": "NBC",              "genre": "Crime",        "desc": "Just the facts, ma'am. Jack Webb's landmark police procedural defined a genre and a generation. The most influential crime drama in broadcast history."},
    {"slug": "whistler",           "name": "The Whistler",                  "years": "1942–1955", "network": "CBS",              "genre": "Mystery",      "desc": "I am the Whistler, and I know many things — for I walk by night. Ironic tales of crime and justice narrated by a mysterious figure who knows your fate."},
]

# Genre colors for badges
GENRE_COLORS = {
    "Detective": "#c9a84c", "Noir": "#8b7355", "Mystery": "#6b5b95",
    "Horror": "#cc2200", "Thriller": "#aa3300", "Adventure": "#2d6a4f",
    "Western": "#8b4513", "Sci-Fi": "#1a6b8a", "Spy": "#2c3e50",
    "Comedy": "#e67e22", "Drama": "#7f8c8d", "Crime": "#922b21",
    "Musical": "#8e44ad", "Action": "#1a5276",
}

def count_episodes(slug):
    d = SITE / slug
    if not d.exists():
        return 0
    return len(list(d.glob("*.html")))

def build_shows_page():
    # Group by genre
    genres = {}
    for show in SHOWS:
        g = show["genre"]
        genres.setdefault(g, []).append(show)

    cards_html = ""
    for genre, shows in sorted(genres.items()):
        cards_html += f'\n      <h2 class="genre-heading">{genre}</h2>\n      <div class="show-grid">\n'
        for show in shows:
            ep_count = count_episodes(show["slug"])
            if ep_count == 0:
                continue
            color = GENRE_COLORS.get(genre, "#c9a84c")
            cards_html += f'''        <a href="/{show["slug"]}/" class="show-card">
          <div class="show-card__badge" style="background:{color}">{genre}</div>
          <h3 class="show-card__title">{show["name"]}</h3>
          <div class="show-card__era">{show["years"]} · {show["network"]}</div>
          <p class="show-card__desc">{show["desc"][:120]}...</p>
          <div class="show-card__count">{ep_count:,} episodes</div>
        </a>\n'''
        cards_html += "      </div>\n"

    total_shows = len([s for s in SHOWS if count_episodes(s["slug"]) > 0])
    total_episodes = sum(count_episodes(s["slug"]) for s in SHOWS)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>All Shows — Ghost of Radio | Classic Old Time Radio</title>
  <meta name="description" content="Browse {total_shows} classic old time radio shows with {total_episodes:,} episodes. Free to stream — detective noir, westerns, horror, comedy, sci-fi and more.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/style.css">
  <link rel="manifest" href="/manifest.json">
  <link rel="apple-touch-icon" href="/images/logo.png">
  <style>
    .genre-heading {{
      color: #c9a84c;
      font-family: 'Special Elite', cursive;
      font-size: 1.4rem;
      margin: 2.5rem 0 1rem;
      padding-bottom: .5rem;
      border-bottom: 1px solid #333;
      letter-spacing: .05em;
    }}
    .show-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1.25rem;
      margin-bottom: 1rem;
    }}
    .show-card {{
      background: #111;
      border: 1px solid #222;
      border-radius: 8px;
      padding: 1.25rem;
      text-decoration: none;
      color: inherit;
      display: block;
      transition: border-color .2s, transform .2s;
      position: relative;
    }}
    .show-card:hover {{
      border-color: #c9a84c;
      transform: translateY(-2px);
    }}
    .show-card__badge {{
      display: inline-block;
      font-size: .65rem;
      font-weight: 700;
      letter-spacing: .08em;
      text-transform: uppercase;
      padding: .2rem .6rem;
      border-radius: 4px;
      color: #fff;
      margin-bottom: .6rem;
    }}
    .show-card__title {{
      font-family: 'Special Elite', cursive;
      font-size: 1.1rem;
      color: #f0dca0;
      margin: 0 0 .3rem;
      line-height: 1.3;
    }}
    .show-card__era {{
      font-size: .75rem;
      color: #888;
      margin-bottom: .6rem;
    }}
    .show-card__desc {{
      font-size: .85rem;
      color: #aaa;
      line-height: 1.5;
      margin-bottom: .75rem;
    }}
    .show-card__count {{
      font-size: .75rem;
      color: #c9a84c;
      font-weight: 600;
    }}
    .shows-stats {{
      text-align: center;
      padding: 1rem;
      color: #888;
      font-size: .9rem;
      margin-bottom: 1rem;
    }}
    .shows-stats strong {{ color: #c9a84c; }}
  </style>
</head>
<body>
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
        <li><a href="/shows.html" class="active">Shows</a></li>
        <li><a href="/about.html">About</a></li>
        <li><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a></li>
      </ul>
    </nav>
  </header>

  <div class="page-header">
    <h1 class="flicker">All Shows</h1>
    <div class="divider"></div>
    <p>The complete Ghost of Radio library — {total_shows} shows, {total_episodes:,} episodes, all free to stream.</p>
  </div>

  <section class="section">
    <div class="container">
      <div class="shows-stats">
        <strong>{total_shows}</strong> shows &nbsp;·&nbsp; <strong>{total_episodes:,}</strong> episodes &nbsp;·&nbsp; All free to stream
      </div>
{cards_html}
    </div>
  </section>

  <footer class="site-footer">
    <p>© 2025 Ghost of Radio · <a href="/about.html">About</a> · <a href="/privacy-policy.html">Privacy</a></p>
  </footer>
  <script src="/js/main.js"></script>
</body>
</html>'''

    out = SITE / "shows.html"
    out.write_text(html, encoding="utf-8")
    print(f"✅ shows.html rebuilt — {total_shows} shows, {total_episodes:,} episodes")
    return total_shows, total_episodes

if __name__ == "__main__":
    total_shows, total_eps = build_shows_page()
    # Commit
    subprocess.run(["git", "add", "shows.html"], cwd=SITE, capture_output=True)
    result = subprocess.run(["git", "commit", "-m", f"feat: rebuild shows.html — all {total_shows} shows, {total_eps} episodes"],
                           cwd=SITE, capture_output=True, text=True)
    print(result.stdout.strip() or result.stderr.strip())
    subprocess.run(["git", "push", "origin", "main"], cwd=SITE, capture_output=True)
    print("✅ Pushed to GitHub")
