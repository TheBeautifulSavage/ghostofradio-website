#!/usr/bin/env python3
"""
Ghost of Radio — Archive.org Mass Downloader + Episode Generator
Downloads every major OTR show from archive.org, then generates pages with Ollama.
Zero API cost. Runs forever until complete.
"""

import os
import re
import json
import time
import shutil
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

SITE_ROOT = Path("/Users/mac1/Projects/ghostofradio")
OTR_LIB = Path("/Users/mac1/OTR_Library")
DOWNLOAD_DIR = OTR_LIB / "Downloads"
BLOG_OUTPUT = SITE_ROOT
AUDIO_OUTPUT = SITE_ROOT / "audio"
LOG_DIR = SITE_ROOT / "scripts/logs"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL_OVERRIDE", "llama3.2:3b")

LOG_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── The Master Show List ──────────────────────────────────────────────────────
# Every major OTR show, with archive.org identifiers
ALL_SHOWS = [
    # === DRAMA / MYSTERY / THRILLER ===
    {"id": "suspense", "name": "Suspense", "slug": "suspense",
     "network": "CBS", "years": "1942–1962",
     "archive_ids": ["suspense_otr", "SUSPENSE"],
     "description": "Radio's outstanding theater of thrills. Over 900 episodes of suspense, crime, and horror starring Hollywood's biggest names.",
     "intro_voice": "And now, Suspense!"},

    {"id": "escape", "name": "Escape", "slug": "escape",
     "network": "CBS", "years": "1947–1954",
     "archive_ids": ["OTRR_Escape_Singles"],
     "description": "Designed to free you from the four walls of today — adventure and escape from the mundane into the exotic.",
     "intro_voice": "Tired of the everyday routine? Ever dream of a life of romantic adventure?"},

    {"id": "inner-sanctum", "name": "Inner Sanctum Mysteries", "slug": "inner-sanctum",
     "network": "NBC / CBS / ABC", "years": "1941–1952",
     "archive_ids": ["InnerSanctumMysteries", "inner_sanctum_otr"],
     "description": "The creaking door that opened onto tales of mystery and horror, hosted by Raymond Edward Johnson.",
     "intro_voice": "Good evening, friends of the inner sanctum..."},

    {"id": "dragnet", "name": "Dragnet", "slug": "dragnet",
     "network": "NBC", "years": "1949–1957",
     "archive_ids": ["Dragnet_OTR", "dragnet_radio"],
     "description": "The story you are about to hear is true. The semi-documentary crime drama that defined a generation.",
     "intro_voice": "The story you are about to hear is true. Only the names have been changed to protect the innocent."},

    {"id": "gunsmoke", "name": "Gunsmoke", "slug": "gunsmoke",
     "network": "CBS", "years": "1952–1961",
     "archive_ids": ["OTRR_Gunsmoke_Singles"],
     "description": "The adult western that brought the frontier to life. William Conrad as Matt Dillon, marshal of Dodge City.",
     "intro_voice": "Around Dodge City and in the territory out west, there's just one way to handle the killers and the spoilers, and that's with a U.S. Marshal and the smell of gunsmoke."},

    {"id": "x-minus-one", "name": "X Minus One", "slug": "x-minus-one",
     "network": "NBC", "years": "1955–1958",
     "archive_ids": ["OTRR_X_Minus_One_Singles"],
     "description": "Dramatizations of the finest science fiction from Galaxy, Astounding, and other magazines. The pinnacle of sci-fi radio.",
     "intro_voice": "Countdown for blastoff... X minus five, four, three, two, X minus one — Fire!"},

    {"id": "dimension-x", "name": "Dimension X", "slug": "dimension-x",
     "network": "NBC", "years": "1950–1951",
     "archive_ids": ["DimensionX", "dimension_x_otr"],
     "description": "Adventures in time and space told in terms of tomorrow. The forerunner to X Minus One.",
     "intro_voice": "Adventures in time and space, told in terms of tomorrow."},

    {"id": "lights-out", "name": "Lights Out", "slug": "lights-out",
     "network": "NBC / CBS", "years": "1934–1947",
     "archive_ids": ["LightsOut_OTR", "lights_out_radio"],
     "description": "Everybody out — it's lights out time. The original horror radio anthology.",
     "intro_voice": "It... is... later... than you... think."},

    {"id": "hermit-cave", "name": "The Hermit's Cave", "slug": "hermits-cave",
     "network": "Syndicated", "years": "1930s–1940s",
     "archive_ids": ["HermitsCave", "hermits_cave_otr"],
     "description": "Tales of the weird and the supernatural told by the mysterious Hermit from his cave.",
     "intro_voice": "Oooooh, spooks! Ha ha ha ha ha!"},

    {"id": "mysterious-traveler", "name": "The Mysterious Traveler", "slug": "mysterious-traveler",
     "network": "Mutual", "years": "1943–1952",
     "archive_ids": ["MysteriousTraveler", "mysterious_traveler_otr"],
     "description": "Tales of mystery and the macabre from a stranger met on a train.",
     "intro_voice": "This is the Mysterious Traveler, inviting you to join me on another journey into the strange and terrifying."},

    {"id": "two-thousand-plus", "name": "2000 Plus", "slug": "2000-plus",
     "network": "Mutual", "years": "1950–1952",
     "archive_ids": ["2000Plus", "twothousandplus"],
     "description": "Science fiction radio drama set in a technological future.",
     "intro_voice": "Two thousand plus — stories of the future."},

    {"id": "crime-classics", "name": "Crime Classics", "slug": "crime-classics",
     "network": "CBS", "years": "1953–1954",
     "archive_ids": ["CrimeClassics", "crime_classics_otr"],
     "description": "True crime stories from history, meticulously dramatized by host Thomas Hyland.",
     "intro_voice": "Crime Classics — the story of a crime."},

    {"id": "broadway-is-my-beat", "name": "Broadway Is My Beat", "slug": "broadway-is-my-beat",
     "network": "CBS", "years": "1949–1954",
     "archive_ids": ["BroadwayIsMyBeat", "broadway_is_my_beat_otr"],
     "description": "Detective Danny Clover walks the Great White Way solving murders in the city that never sleeps.",
     "intro_voice": "Broadway is my beat, from Times Square to Columbus Circle — the gaudiest, the most violent, the loneliest mile in the world."},

    {"id": "yours-truly-johnny-dollar", "name": "Yours Truly, Johnny Dollar", "slug": "johnny-dollar",
     "network": "CBS", "years": "1949–1962",
     "archive_ids": ["YoursTrulyJohnnyDollar", "johnny_dollar_otr"],
     "mp3_dir": str(OTR_LIB / "Johnny_Dollar"),
     "description": "America's fabulous freelance insurance investigator — the man with the action-packed expense account.",
     "intro_voice": "Yours truly, Johnny Dollar!"},

    {"id": "philip-marlowe", "name": "The Adventures of Philip Marlowe", "slug": "philip-marlowe",
     "network": "NBC / CBS", "years": "1947–1951",
     "archive_ids": ["OTRR_Philip_Marlowe_Singles"],
     "description": "Raymond Chandler's hard-boiled Los Angeles private detective in full radio glory.",
     "intro_voice": "Philip Marlowe, private detective."},

    {"id": "casey-crime-photographer", "name": "Casey, Crime Photographer", "slug": "casey-crime-photographer",
     "network": "CBS", "years": "1943–1955",
     "archive_ids": ["CaseyCrimePhotographer", "casey_crime_photographer"],
     "description": "Flashgun Casey, star photographer for The Morning Express, who can't stay out of trouble.",
     "intro_voice": "Casey, crime photographer!"},

    {"id": "richard-diamond", "name": "Richard Diamond, Private Detective", "slug": "richard-diamond",
     "network": "NBC / CBS", "years": "1949–1952",
     "archive_ids": ["RichardDiamond", "richard_diamond_otr"],
     "description": "Dick Powell as a wisecracking Manhattan private eye with a knack for singing and a flair for danger.",
     "intro_voice": "Richard Diamond, private detective."},

    {"id": "sam-spade", "name": "The Adventures of Sam Spade", "slug": "sam-spade",
     "network": "ABC / CBS", "years": "1946–1951",
     "archive_ids": ["SamSpade_OTR", "sam_spade_otr"],
     "mp3_dir": str(OTR_LIB / "Sam_Spade"),
     "description": "Dashiell Hammett's hard-boiled San Francisco detective — Howard Duff in the role of a lifetime.",
     "intro_voice": "The Adventures of Sam Spade, detective."},

    # === SCIENCE FICTION ===
    {"id": "the-witch-doctor", "name": "Witch's Tale", "slug": "witchs-tale",
     "network": "Syndicated", "years": "1931–1938",
     "archive_ids": ["WitchsTale", "witches_tale_otr"],
     "description": "One of the earliest horror anthology series, told by Old Nancy the Witch and her cat Satan.",
     "intro_voice": "Hee hee hee hee! 'Tis I, Old Nancy the Witch of Salem..."},

    {"id": "planet-man", "name": "Buck Rogers", "slug": "buck-rogers",
     "network": "CBS / Mutual", "years": "1932–1947",
     "archive_ids": ["BuckRogers_OTR", "buck_rogers_radio"],
     "description": "The original science fiction space hero — Buck Rogers in the 25th century.",
     "intro_voice": "Buck Rogers in the 25th century!"},

    # === COMEDY ===
    {"id": "jack-benny", "name": "The Jack Benny Program", "slug": "jack-benny",
     "network": "NBC / CBS", "years": "1932–1955",
     "archive_ids": ["JackBenny", "jack_benny_otr"],
     "description": "The most celebrated comedy program in radio history. Jack Benny's masterclass in timing and character.",
     "intro_voice": "The Jack Benny Program!"},

    {"id": "bob-hope", "name": "The Bob Hope Show", "slug": "bob-hope",
     "network": "NBC", "years": "1935–1956",
     "archive_ids": ["BobHope_OTR", "bob_hope_radio"],
     "description": "America's comedian entertains the troops and the nation with wit, guests, and gags.",
     "intro_voice": "This is Bob Hope saying..."},

    {"id": "fibber-mcgee", "name": "Fibber McGee and Molly", "slug": "fibber-mcgee",
     "network": "NBC", "years": "1935–1959",
     "archive_ids": ["FibberMcGeeAndMolly", "fibber_mcgee_otr"],
     "description": "The loveable braggart and his patient wife in the most beloved domestic comedy of radio's golden age.",
     "intro_voice": "Fibber McGee and Molly!"},

    {"id": "burns-allen", "name": "The Burns and Allen Show", "slug": "burns-and-allen",
     "network": "CBS / NBC", "years": "1932–1950",
     "archive_ids": ["BurnsAndAllen", "burns_allen_otr"],
     "description": "George Burns and Gracie Allen — the perfectly mismatched couple whose comedy chemistry was pure gold.",
     "intro_voice": "The Burns and Allen Show!"},

    {"id": "fred-allen", "name": "The Fred Allen Show", "slug": "fred-allen",
     "network": "NBC / CBS", "years": "1932–1949",
     "archive_ids": ["FredAllen_OTR", "fred_allen_radio"],
     "description": "Fred Allen's razor-sharp wit and satirical commentary on American life.",
     "intro_voice": "Fred Allen!"},

    {"id": "great-gildersleeve", "name": "The Great Gildersleeve", "slug": "great-gildersleeve",
     "network": "NBC", "years": "1941–1957",
     "archive_ids": ["GreatGildersleeve", "great_gildersleeve_otr"],
     "description": "The pompous but loveable Throckmorton P. Gildersleeve, water commissioner of Summerfield.",
     "intro_voice": "The Great Gildersleeve!"},

    # === WESTERNS ===
    {"id": "lone-ranger", "name": "The Lone Ranger", "slug": "lone-ranger",
     "network": "Mutual / NBC", "years": "1933–1954",
     "archive_ids": ["LoneRanger_OTR", "lone_ranger_radio"],
     "description": "Hi-yo, Silver! The masked rider of the plains and his faithful companion Tonto.",
     "intro_voice": "A fiery horse with the speed of light, a cloud of dust and a hearty Hi-Yo Silver — the Lone Ranger!"},

    {"id": "red-ryder", "name": "Red Ryder", "slug": "red-ryder",
     "network": "Mutual / NBC", "years": "1942–1951",
     "archive_ids": ["RedRyder_OTR", "red_ryder_radio"],
     "description": "The Robin Hood of the West and Little Beaver in adventures across the frontier.",
     "intro_voice": "Red Ryder!"},

    {"id": "death-valley-days", "name": "Death Valley Days", "slug": "death-valley-days",
     "network": "NBC / CBS", "years": "1930–1945",
     "archive_ids": ["DeathValleyDays_OTR", "death_valley_days_radio"],
     "description": "True tales from the American West, sponsored by Twenty Mule Team Borax.",
     "intro_voice": "Death Valley Days!"},

    # === ADVENTURE ===
    {"id": "green-hornet", "name": "The Green Hornet", "slug": "green-hornet",
     "network": "Mutual / NBC", "years": "1936–1952",
     "archive_ids": ["GreenHornet_OTR", "green_hornet_radio"],
     "description": "Britt Reid, publisher by day, masked crime-fighter by night, with his loyal valet Kato.",
     "intro_voice": "The Green Hornet!"},

    {"id": "captain-midnight", "name": "Captain Midnight", "slug": "captain-midnight",
     "network": "Mutual", "years": "1938–1949",
     "archive_ids": ["CaptainMidnight_OTR", "captain_midnight_radio"],
     "description": "America's ace of the airways — Captain Midnight and the Secret Squadron.",
     "intro_voice": "Captain Midnight!"},

    {"id": "sky-king", "name": "Sky King", "slug": "sky-king",
     "network": "ABC / NBC / CBS", "years": "1946–1954",
     "archive_ids": ["SkyKing_OTR", "sky_king_radio"],
     "description": "Kirby King, Arizona rancher and pilot, fighting crime from the air.",
     "intro_voice": "Sky King!"},

    # === DRAMA / ANTHOLOGY ===
    {"id": "lux-radio-theatre", "name": "Lux Radio Theatre", "slug": "lux-radio-theatre",
     "network": "NBC / CBS", "years": "1934–1955",
     "archive_ids": ["LuxRadioTheatre", "lux_radio_theatre_otr"],
     "description": "Hollywood's biggest stars recreating their greatest films on radio. Over 900 broadcasts.",
     "intro_voice": "Lux presents Hollywood!"},

    {"id": "screen-guild-theater", "name": "Screen Guild Theater", "slug": "screen-guild-theater",
     "network": "CBS", "years": "1939–1952",
     "archive_ids": ["ScreenGuildTheater", "screen_guild_theater_otr"],
     "description": "Major motion pictures adapted for radio, with proceeds going to the Motion Picture Relief Fund.",
     "intro_voice": "The Screen Guild Theater!"},

    {"id": "stars-over-hollywood", "name": "Stars Over Hollywood", "slug": "stars-over-hollywood",
     "network": "CBS", "years": "1941–1954",
     "archive_ids": ["StarsOverHollywood", "stars_over_hollywood_otr"],
     "description": "Original radio dramas featuring Hollywood talent in stories written for the medium.",
     "intro_voice": "Stars Over Hollywood!"},

    {"id": "theater-five", "name": "Theater Five", "slug": "theater-five",
     "network": "ABC", "years": "1964–1965",
     "archive_ids": ["TheaterFive", "theater_five_otr"],
     "description": "One of the last great radio drama anthology series from the twilight of the golden age.",
     "intro_voice": "Theater Five."},

    # === TRUE CRIME / DOCUMENTARY ===
    {"id": "gang-busters", "name": "Gang Busters", "slug": "gang-busters",
     "network": "NBC / CBS / ABC / Mutual", "years": "1935–1957",
     "archive_ids": ["GangBusters_OTR", "gang_busters_radio"],
     "description": "True crime stories dramatized with the cooperation of law enforcement. Come in shooting!",
     "intro_voice": "Calling all Americans to war on the underworld!"},

    {"id": "fbi-in-peace-and-war", "name": "The FBI in Peace and War", "slug": "fbi-in-peace-and-war",
     "network": "CBS", "years": "1944–1958",
     "archive_ids": ["FBIInPeaceAndWar", "fbi_in_peace_and_war"],
     "description": "Based on the book by Frederick L. Collins — the real work of J. Edgar Hoover's FBI.",
     "intro_voice": "The FBI in peace and war!"},

    # === CHILDREN'S / FAMILY ===
    {"id": "lets-pretend", "name": "Let's Pretend", "slug": "lets-pretend",
     "network": "CBS", "years": "1934–1954",
     "archive_ids": ["LetsPretend_OTR", "lets_pretend_radio"],
     "description": "Children's fairy tale adaptations that enchanted a generation of young listeners.",
     "intro_voice": "Let's pretend!"},

    # === QUIZ / VARIETY ===
    {"id": "information-please", "name": "Information Please", "slug": "information-please",
     "network": "NBC", "years": "1938–1951",
     "archive_ids": ["InformationPlease", "information_please_otr"],
     "description": "The panel quiz show that made being smart fashionable. Listeners stumped the experts for cash.",
     "intro_voice": "Information Please!"},

    # === WAR / PATRIOTIC ===
    {"id": "command-performance", "name": "Command Performance", "slug": "command-performance",
     "network": "Armed Forces Radio", "years": "1942–1949",
     "archive_ids": ["CommandPerformance", "command_performance_otr"],
     "description": "The biggest names in entertainment performing for the troops overseas. Pure American morale.",
     "intro_voice": "Command Performance — the request program of the Armed Forces Radio Service."},

    {"id": "mail-call", "name": "Mail Call", "slug": "mail-call",
     "network": "Armed Forces Radio", "years": "1942–1945",
     "archive_ids": ["MailCall_OTR", "mail_call_radio"],
     "description": "Hollywood stars entertaining American servicemen and women around the world.",
     "intro_voice": "Mail Call!"},
]

# ── Archive.org Downloader ──────────────────────────────────────────────────

def get_archive_files(identifier):
    """Get list of MP3 files from an archive.org identifier."""
    try:
        url = f"https://archive.org/metadata/{identifier}"
        req = urllib.request.Request(url, headers={"User-Agent": "GhostOfRadio/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        
        files = data.get("files", [])
        mp3s = [f for f in files if f.get("name", "").lower().endswith(".mp3")]
        base_url = f"https://archive.org/download/{identifier}/"
        return [(f["name"], base_url + urllib.parse.quote(f["name"])) for f in mp3s]
    except Exception as e:
        return []

def download_show(show):
    """Download all MP3s for a show from archive.org."""
    show_dir = DOWNLOAD_DIR / show["slug"]
    show_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if already has local mp3_dir
    if show.get("mp3_dir") and Path(show["mp3_dir"]).exists():
        existing = list(Path(show["mp3_dir"]).glob("*.mp3"))
        if existing:
            print(f"  ✓ {show['name']}: using {len(existing)} local files")
            return show["mp3_dir"]
    
    # Try archive.org identifiers
    all_files = []
    for identifier in show.get("archive_ids", []):
        files = get_archive_files(identifier)
        if files:
            all_files = files
            print(f"  Found {len(files)} files in archive.org/{identifier}")
            break
    
    if not all_files:
        print(f"  ⚠️  No files found for {show['name']}")
        return None
    
    # Download with resume support
    downloaded = 0
    for filename, url in all_files[:200]:  # cap at 200 per show to manage disk
        dest = show_dir / filename
        if dest.exists() and dest.stat().st_size > 10000:
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "GhostOfRadio/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
                shutil.copyfileobj(r, f)
            downloaded += 1
            if downloaded % 10 == 0:
                print(f"    Downloaded {downloaded}/{len(all_files)} — {filename[:50]}")
        except Exception as e:
            pass  # skip failed downloads silently
    
    print(f"  ✓ {show['name']}: downloaded {downloaded} new files to {show_dir}")
    return str(show_dir)

# ── Reuse generation logic from generate_episodes.py ──────────────────────

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

def parse_filename(filename):
    name = Path(filename).stem
    patterns = [
        r"(\d{4}-\d{2}-\d{2})\s*[-–]\s*(.+)",
        r"(\d{6})\s*[-–]?\s*(.+)",
        r"[A-Za-z_]+_(\d{2}-\d{2}-\d{2})_ep(\d+)_(.+)",
        r"(\d{6})_(\d+)_(.+)",
    ]
    for pat in patterns:
        m = re.match(pat, name)
        if m:
            groups = m.groups()
            datestr = groups[0]
            title = groups[-1].replace("_", " ").strip()
            try:
                if len(datestr) == 10:
                    date = datetime.strptime(datestr, "%Y-%m-%d")
                elif len(datestr) == 6:
                    yy = int(datestr[:2])
                    year = 1900 + yy if yy >= 20 else 2000 + yy
                    date = datetime.strptime(str(year) + datestr[2:], "%Y%m%d")
                else:
                    date = None
                return date, title
            except:
                return None, title
    return None, name

def ollama_generate(prompt):
    result = subprocess.run(
        ["ollama", "run", OLLAMA_MODEL],
        input=prompt, capture_output=True, text=True, timeout=120
    )
    return result.stdout.strip()

def generate_content(show, title, date):
    year = date.year if date else "unknown year"
    date_str = date.strftime("%B %d, %Y") if date else "Unknown date"
    prompt = f"""You are a cultural historian writing for ghostofradio.com about old time radio.

Show: {show['name']} ({show['network']}, {show['years']})
Episode: {title}
Air Date: {date_str}

Write in this EXACT format:

EPISODE_SUMMARY:
2-3 vivid paragraphs about this episode. Describe the atmosphere, drama, characters. Make it compelling.

HISTORICAL_CONTEXT:
3 paragraphs about America/the world in {year}. Specific events, tensions, what people feared and hoped for. Why did radio drama resonate that year?

WHY_IT_MATTERS:
1-2 paragraphs on the craft — what makes this episode worth hearing today?

Under 600 words total. No bullet points. Pure prose."""
    
    response = ollama_generate(prompt)
    sections = {"summary": "", "historical": "", "why": ""}
    parts = re.split(r"(EPISODE_SUMMARY:|HISTORICAL_CONTEXT:|WHY_IT_MATTERS:)", response)
    for i, part in enumerate(parts):
        if "EPISODE_SUMMARY:" in part and i+1 < len(parts): sections["summary"] = parts[i+1].strip()
        elif "HISTORICAL_CONTEXT:" in part and i+1 < len(parts): sections["historical"] = parts[i+1].strip()
        elif "WHY_IT_MATTERS:" in part and i+1 < len(parts): sections["why"] = parts[i+1].strip()
    if not any(sections.values()): sections["summary"] = response
    return sections

def paras(text):
    if not text: return ""
    return "".join(f"<p>{p.strip()}</p>\n" for p in text.split("\n\n") if p.strip())

def build_page(show, title, date, ep_num, mp3_web, content, prev_ep=None, next_ep=None):
    date_str = date.strftime("%B %d, %Y") if date else "Unknown date"
    date_iso = date.strftime("%Y-%m-%d") if date else ""
    year = date.year if date else ""
    ep_label = f"Episode {ep_num} · " if ep_num else ""
    slug = slugify(title)
    canonical = f"https://ghostofradio.com/{show['slug']}/{slug}.html"
    import random; random.seed(hash(title))
    bars = str([random.randint(4, 32) for _ in range(56)])
    prev_html = f'<a href="{prev_ep[0]}">&larr; {prev_ep[1][:40]}</a>' if prev_ep else "<span></span>"
    next_html = f'<a href="{next_ep[0]}">{next_ep[1][:40]} &rarr;</a>' if next_ep else "<span></span>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | {show['name']} | {date_str} | Ghost of Radio</title>
<meta name="description" content="Listen free: '{title}' from {show['name']} ({date_str}). {show['description'][:120]}">
<meta property="og:title" content="{title} | {show['name']} | {date_str}">
<meta property="og:type" content="article">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="Ghost of Radio">
<link rel="canonical" href="{canonical}">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":"{title} — {show['name']} ({date_str})","datePublished":"{date_iso}","author":{{"@type":"Organization","name":"Ghost of Radio"}},"mainEntityOfPage":"{canonical}"}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
<link rel="stylesheet" href="/css/radio-player.css">
</head>
<body>
<header class="site-header"><nav class="nav">
<a href="/index.html" class="nav__logo"><span class="nav__logo-icon"><img src="/images/logo.png" alt="Ghost of Radio" class="nav__logo-img"></span> Ghost of Radio</a>
<button class="nav__toggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
<ul class="nav__links"><li><a href="/index.html">Home</a></li><li><a href="/shows.html">Shows</a></li><li><a href="/{show['slug']}/">Browse Episodes</a></li><li><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a></li></ul>
</nav></header>
<div class="page-header">
<div class="container"><div class="breadcrumb"><a href="/index.html">Home</a><span>›</span><a href="/shows.html">Shows</a><span>›</span><a href="/{show['slug']}/">{show['name']}</a><span>›</span>{title}</div></div>
<h1 class="flicker">{title}</h1><div class="divider"></div>
<p>{show['name']} &nbsp;·&nbsp; {ep_label}{date_str}</p>
</div>
<section class="section"><div class="container"><article class="about-content fade-in">
<div class="episode-meta-box">
<div class="episode-meta-item"><span class="episode-meta-label">Air Date</span><span class="episode-meta-value">{date_str}</span></div>
<div class="episode-meta-item"><span class="episode-meta-label">Show</span><span class="episode-meta-value">{show['name']}</span></div>
<div class="episode-meta-item"><span class="episode-meta-label">Network</span><span class="episode-meta-value">{show['network']}</span></div>
<div class="episode-meta-item"><span class="episode-meta-label">Era</span><span class="episode-meta-value">{show['years']}</span></div>
</div>
<div class="radio-player" id="radioPlayer">
<div class="radio-top"><div class="radio-grille"></div><div class="radio-info">
<div class="radio-show-name">{show['name']}</div>
<div class="radio-episode-title">{title}</div>
<div class="radio-meta">{date_str} &nbsp;·&nbsp; {show['network']}</div>
</div></div>
<div class="radio-body">
<div class="radio-waveform" id="waveform" aria-hidden="true"></div>
<div class="radio-controls">
<button class="radio-play-btn" id="playBtn" aria-label="Play episode">
<svg class="play-icon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
<svg class="pause-icon" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
</button>
<div class="radio-progress-wrap">
<input type="range" class="radio-progress" id="progressBar" min="0" max="100" value="0" step="0.1" aria-label="Seek">
<div class="radio-time"><span id="currentTime">0:00</span><span id="duration">--:--</span></div>
</div>
<div class="radio-volume-wrap">
<svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/></svg>
<input type="range" class="radio-volume" id="volumeBar" min="0" max="1" step="0.05" value="0.85" aria-label="Volume">
</div></div></div>
<div class="radio-footer">
<span class="radio-broadcast" id="broadcastLabel">· GHOST OF RADIO ·</span>
<a class="radio-download" href="{mp3_web}" download>⬇ Download MP3</a>
</div>
<audio id="episodeAudio" preload="none"><source src="{mp3_web}" type="audio/mpeg"></audio>
</div>
<h2>The Episode</h2>{paras(content.get('summary',''))}
<div class="era-box"><div class="era-box-label">Historical Context</div><h3>The World of {year}</h3>{paras(content.get('historical',''))}</div>
<h2>Why Listen Today</h2>{paras(content.get('why',''))}
<p><em>"{show['intro_voice']}"</em></p>
<div class="divider" style="margin:3rem auto;"></div>
<div class="episode-nav">{prev_html}{next_html}</div>
<div class="divider" style="margin:3rem auto;"></div>
<p style="text-align:center;font-family:var(--font-heading);font-size:0.75rem;letter-spacing:0.15em;color:#6b6355;">
<a href="/{show['slug']}/" style="color:#c9a84c;text-decoration:none;">← Browse All {show['name']} Episodes</a></p>
</article></div></section>
<footer class="site-footer"><div class="container">
<p>&copy; 2024 Ghost of Radio &mdash; Where Vintage Broadcasts Return from the Dead</p>
<p><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a> &nbsp;&middot;&nbsp; <a href="/privacy-policy.html">Privacy Policy</a></p>
</div></footer>
<script src="/js/main.js"></script>
<script>
const heights={bars};
const wf=document.getElementById('waveform');
heights.forEach(h=>{{const b=document.createElement('span');b.style.height=h+'px';wf.appendChild(b);}});
const audio=document.getElementById('episodeAudio'),playBtn=document.getElementById('playBtn'),pb=document.getElementById('progressBar'),vb=document.getElementById('volumeBar'),ct=document.getElementById('currentTime'),dur=document.getElementById('duration'),bl=document.getElementById('broadcastLabel'),bars2=wf.querySelectorAll('span');
function fmt(s){{if(isNaN(s))return'--:--';const m=Math.floor(s/60),sec=Math.floor(s%60);return m+':'+(sec<10?'0':'')+sec;}}
let af;function anim(){{const p=audio.duration?audio.currentTime/audio.duration:0;const ac=Math.floor(p*bars2.length);bars2.forEach((b,i)=>b.classList.toggle('active',i<ac));af=requestAnimationFrame(anim);}}
playBtn.addEventListener('click',()=>{{if(audio.paused){{audio.play();playBtn.classList.add('playing');bl.classList.add('live');bl.textContent='● ON AIR — GHOST OF RADIO';anim();}}else{{audio.pause();playBtn.classList.remove('playing');bl.classList.remove('live');bl.textContent='· GHOST OF RADIO ·';cancelAnimationFrame(af);}}}});
audio.addEventListener('timeupdate',()=>{{if(audio.duration)pb.value=(audio.currentTime/audio.duration)*100;ct.textContent=fmt(audio.currentTime);}});
audio.addEventListener('loadedmetadata',()=>{{dur.textContent=fmt(audio.duration);}});
audio.addEventListener('ended',()=>{{playBtn.classList.remove('playing');bl.classList.remove('live');bl.textContent='· GHOST OF RADIO ·';cancelAnimationFrame(af);pb.value=0;ct.textContent='0:00';}});
pb.addEventListener('input',()=>{{if(audio.duration)audio.currentTime=(pb.value/100)*audio.duration;}});
vb.addEventListener('input',()=>{{audio.volume=vb.value;}});
audio.volume=0.85;
</script>
</body></html>"""

def git_commit_safe(message):
    import fcntl
    lock = open(str(SITE_ROOT / ".git_commit_lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        subprocess.run(["git", "add", "-A"], cwd=SITE_ROOT, capture_output=True)
        r = subprocess.run(["git", "commit", "-m", message], cwd=SITE_ROOT, capture_output=True, text=True)
        if r.returncode == 0: print(f"  📦 {message}")
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=SITE_ROOT, capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=SITE_ROOT, capture_output=True)
    except Exception as e: print(f"  git err: {e}")
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN); lock.close()

def process_show(show):
    print(f"\n{'='*50}\n{show['name']}\n{'='*50}")
    
    # Get mp3 directory
    mp3_dir = show.get("mp3_dir")
    if not mp3_dir or not Path(mp3_dir).exists():
        mp3_dir = download_show(show)
    if not mp3_dir:
        print(f"  SKIP — no files"); return
    
    mp3_files = sorted(Path(mp3_dir).glob("*.mp3")) + sorted(Path(mp3_dir).glob("*.MP3"))
    if not mp3_files:
        print(f"  SKIP — empty"); return
    print(f"  {len(mp3_files)} episodes")
    
    blog_dir = BLOG_OUTPUT / show["slug"]
    audio_dir = AUDIO_OUTPUT / show["slug"]
    blog_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    episodes = []
    for f in mp3_files:
        date, title = parse_filename(f.name)
        episodes.append({"file": f, "date": date, "title": title, "slug": slugify(title)})
    
    committed = 0
    for i, ep in enumerate(episodes):
        out = blog_dir / f"{ep['slug']}.html"
        if out.exists(): continue
        
        print(f"  [{i+1}/{len(episodes)}] {ep['title'][:50]}")
        
        # Copy mp3
        dest_mp3 = audio_dir / f"{ep['slug']}.mp3"
        if not dest_mp3.exists():
            shutil.copy2(ep["file"], dest_mp3)
        mp3_web = f"/audio/{show['slug']}/{ep['slug']}.mp3"
        
        # Generate content
        try: content = generate_content(show, ep["title"], ep["date"])
        except: content = {"summary": f"A classic episode of {show['name']}.", "historical": "", "why": "Essential old time radio."}
        
        # Nav
        prev_ep = (f"/{show['slug']}/{episodes[i-1]['slug']}.html", episodes[i-1]['title']) if i > 0 else None
        next_ep = (f"/{show['slug']}/{episodes[i+1]['slug']}.html", episodes[i+1]['title']) if i < len(episodes)-1 else None
        
        html = build_page(show, ep["title"], ep["date"], None, mp3_web, content, prev_ep, next_ep)
        out.write_text(html, encoding="utf-8")
        
        committed += 1
        if committed % 10 == 0:
            git_commit_safe(f"feat: {show['name']} — {committed} episodes")
    
    # Index page
    cards = ""
    for ep in episodes:
        ds = ep["date"].strftime("%B %d, %Y") if ep["date"] else "Unknown"
        cards += f'<a href="/{show["slug"]}/{ep["slug"]}.html" class="episode-card"><div class="episode-card__date">{ds}</div><div class="episode-card__title">{ep["title"]}</div><div class="episode-card__listen">▶ Listen Free</div></a>\n'
    
    idx = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{show['name']} — All Episodes | Ghost of Radio</title>
<meta name="description" content="Stream all {len(episodes)} episodes of {show['name']} free. {show['description'][:150]}">
<link rel="canonical" href="https://ghostofradio.com/{show['slug']}/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
<style>.ep-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem;margin-top:2rem}}.episode-card{{background:#1a1a1a;border:1px solid #2a2010;border-radius:8px;padding:1.25rem;text-decoration:none;display:block;transition:border-color .2s,background .2s}}.episode-card:hover{{border-color:#c9a84c;background:#1f1c14}}.episode-card__date{{font-family:var(--font-heading);font-size:.65rem;letter-spacing:.15em;color:#6b6355;text-transform:uppercase;margin-bottom:.4rem}}.episode-card__title{{font-family:var(--font-heading);color:#e8e0d0;font-size:.95rem;line-height:1.3;margin-bottom:.5rem}}.episode-card__listen{{font-family:var(--font-heading);font-size:.65rem;color:#c9a84c;letter-spacing:.1em}}.srch{{width:100%;max-width:400px;background:#111;border:1px solid #3a2e1e;color:#e8e0d0;font-family:var(--font-heading);padding:.6rem 1rem;border-radius:6px;font-size:.85rem;margin-bottom:1.5rem}}.srch:focus{{outline:none;border-color:#c9a84c}}</style>
</head><body>
<header class="site-header"><nav class="nav"><a href="/index.html" class="nav__logo"><span class="nav__logo-icon"><img src="/images/logo.png" alt="Ghost of Radio" class="nav__logo-img"></span> Ghost of Radio</a>
<button class="nav__toggle" aria-label="Toggle" aria-expanded="false"><span></span><span></span><span></span></button>
<ul class="nav__links"><li><a href="/index.html">Home</a></li><li><a href="/shows.html">Shows</a></li><li><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a></li></ul></nav></header>
<div class="page-header"><h1 class="flicker">{show['name']}</h1><div class="divider"></div><p>{show['years']} &nbsp;·&nbsp; {show['network']} &nbsp;·&nbsp; {len(episodes)} Episodes</p></div>
<section class="section"><div class="container">
<p style="font-family:var(--font-body);color:var(--text-dim);font-size:1.1rem;line-height:1.8;max-width:680px;margin:0 auto 2rem;">{show['description']}</p>
<input type="text" class="srch" id="si" placeholder="Search episodes..." oninput="document.querySelectorAll('.episode-card').forEach(c=>c.style.display=c.textContent.toLowerCase().includes(this.value.toLowerCase())?'':'none')">
<div class="ep-grid">{cards}</div>
</div></section>
<footer class="site-footer"><div class="container"><p>&copy; 2024 Ghost of Radio</p><p><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a></p></div></footer>
<script src="/js/main.js"></script>
</body></html>"""
    (blog_dir / "index.html").write_text(idx, encoding="utf-8")
    git_commit_safe(f"feat: complete {show['name']} — {len(episodes)} episodes + index")
    print(f"  ✅ {show['name']} complete")

if __name__ == "__main__":
    import sys
    targets = sys.argv[1:] if len(sys.argv) > 1 else [s["id"] for s in ALL_SHOWS]
    shows = [s for s in ALL_SHOWS if s["id"] in targets]
    print(f"Ghost of Radio — Processing {len(shows)} shows with {OLLAMA_MODEL}")
    for show in shows:
        process_show(show)
    print("\n✅ All done!")
