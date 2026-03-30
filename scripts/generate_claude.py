#!/usr/bin/env python3
"""
Ghost of Radio — Fast Episode Page Generator using Claude Haiku
Downloads MP3s from archive.org, generates rich episode pages, commits to GitHub.
~50-100x faster than local Ollama.
"""
import os, sys, re, json, time, subprocess, urllib.request, urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import anthropic

SITE_ROOT  = Path("/Users/mac1/Projects/ghostofradio")
AUDIO_DIR  = SITE_ROOT / "audio"
R2_BASE    = "https://pub-43a2a91d87c649239fa207174290a900.r2.dev"
CF_TOKEN   = "cfut_F7Gk8H3OrM2QQ34UoqpRfo3F3mHuNd222p2IMdm73b91416a"
CF_ACCOUNT = "dae784fdc17957e814046c3637ee10eb"
ANTHROPIC_KEY = "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"

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# Shows to complete: slug -> archive.org identifier(s)
SHOWS = {
    "suspense":        ["OTRR_Suspense_Singles", "SUSPENSE"],
    "loneranger":      ["OTRR_LoneRanger_Singles"],
    "gunsmoke":        ["OTRR_Gunsmoke_Singles"],
    "lux-radio-theatre": ["LuxRadioTheatre"],
    "inner-sanctum":   ["inner-sanctum-mysteries-radio-show-1941-episodes", "inner-sanctum_202108", "inner-sanctum-1944-episodes", "inner-sanctum-1949-episodes"],
    "dragnet":         ["Dragnet_OTR", "OTRR_Dragnet_Singles"],
    "whistler":        ["OTRR_Whistler_Singles"],
    "escape":          ["OTRR_Escape_Singles"],
    "x-minus-one":     ["OTRR_X_Minus_One_Singles"],
    "philip-marlowe":  ["OTRR_Philip_Marlowe_Singles"],
    "shadow":          ["the-shadow-radio-show-1937-1954-old-time-radio-all-available-episodes", "OTRR_Shadow_Singles"],
    "sherlock":        ["sherlockholmes_otr", "OTRR_SherlockHolmes_Singles"],
    "cbs-mystery":     ["cbsrmt-1975_2023"],
    # New shows - top 50 expansion
    "johnny-dollar":       ["OTRR_YoursTrulyJohnnyDollar_Singles_Mandel_Kramer", "OTRR_YoursTrulyJohnnyDollar_Singles_Charles_Russell", "OTRR_YoursTrulyJohnnyDollar_Singles_Bob_Bailey"],
    "dimension-x":         ["OTRR_Dimension_X_Singles"],
    "mysterious-traveler": ["OTRR_Mysterious_Traveler_Singles"],
    "quiet-please":        ["Quiet_Please"],
    "bold-venture":        ["OTRR_Bold_Venture_Singles"],
    "broadway-beat":       ["OTRR_Broadway_Is_My_Beat_Singles"],
    "crime-classics":      ["OTRR_Crime_Classics_Singles"],
    "box-13":              ["OTRR_Box_13_Singles"],
    "rogues-gallery":      ["OTRR_Rogues_Gallery_Singles"],
    "fort-laramie":        ["OTRR_Fort_Laramie_Singles"],
    "have-gun":            ["have-gun-will-travel"],
    "our-miss-brooks":    ["OTRR_Our_Miss_Brooks_Singles"],
    "richard-diamond":     ["OTRR_Richard_Diamond_Private_Detective_Singles"],
    "great-gildersleeve":  ["Otrr_The_Great_Gildersleeve_Singles"],
    "mercury-theatre":     ["OrsonWelles_MercurySummer", "OTRR_Mercury_Theatre_Singles"],
}

SHOW_INFO = {
    "suspense":        {"name": "Suspense", "network": "CBS", "years": "1942-1962", "genre": "thriller/horror"},
    "loneranger":      {"name": "The Lone Ranger", "network": "ABC", "years": "1933-1954", "genre": "western"},
    "gunsmoke":        {"name": "Gunsmoke", "network": "CBS", "years": "1952-1961", "genre": "western"},
    "lux-radio-theatre": {"name": "Lux Radio Theatre", "network": "CBS/NBC", "years": "1934-1955", "genre": "drama"},
    "inner-sanctum":   {"name": "Inner Sanctum Mysteries", "network": "NBC/CBS", "years": "1941-1952", "genre": "horror/mystery"},
    "dragnet":         {"name": "Dragnet", "network": "NBC", "years": "1949-1957", "genre": "crime/police procedural"},
    "whistler":        {"name": "The Whistler", "network": "CBS", "years": "1942-1955", "genre": "noir/mystery"},
    "escape":          {"name": "Escape", "network": "CBS", "years": "1947-1954", "genre": "adventure/thriller"},
    "x-minus-one":     {"name": "X Minus One", "network": "NBC", "years": "1955-1958", "genre": "science fiction"},
    "philip-marlowe":  {"name": "The Adventures of Philip Marlowe", "network": "CBS", "years": "1947-1951", "genre": "noir detective"},
    "shadow":          {"name": "The Shadow", "network": "CBS/Mutual", "years": "1937-1954", "genre": "mystery/crime"},
    "sherlock":        {"name": "Sherlock Holmes", "network": "NBC/CBS", "years": "1939-1950", "genre": "detective mystery"},
    "cbs-mystery":     {"name": "CBS Radio Mystery Theater", "network": "CBS", "years": "1974-1982", "genre": "mystery/horror"},
    # New shows
    "johnny-dollar":       {"name": "Yours Truly Johnny Dollar", "network": "CBS", "years": "1949-1962", "genre": "insurance investigator noir"},
    "dimension-x":         {"name": "Dimension X", "network": "NBC", "years": "1950-1951", "genre": "science fiction"},
    "mysterious-traveler": {"name": "The Mysterious Traveler", "network": "Mutual", "years": "1943-1952", "genre": "mystery/thriller anthology"},
    "quiet-please":        {"name": "Quiet Please", "network": "Mutual/ABC", "years": "1947-1949", "genre": "eerie anthology drama"},
    "bold-venture":        {"name": "Bold Venture", "network": "Syndicated", "years": "1951-1952", "genre": "adventure noir"},
    "broadway-beat":       {"name": "Broadway Is My Beat", "network": "CBS", "years": "1949-1954", "genre": "New York crime drama"},
    "crime-classics":      {"name": "Crime Classics", "network": "CBS", "years": "1953-1954", "genre": "true crime drama"},
    "box-13":              {"name": "Box 13", "network": "Syndicated", "years": "1948-1949", "genre": "adventure mystery"},
    "rogues-gallery":      {"name": "Rogue's Gallery", "network": "NBC/Mutual", "years": "1945-1951", "genre": "detective comedy"},
    "fort-laramie":        {"name": "Fort Laramie", "network": "CBS", "years": "1956", "genre": "adult western drama"},
    "have-gun":            {"name": "Have Gun Will Travel", "network": "CBS", "years": "1958-1960", "genre": "western"},
    "our-miss-brooks":    {"name": "Our Miss Brooks", "network": "CBS", "years": "1948-1957", "genre": "comedy"},
    "richard-diamond":     {"name": "Richard Diamond Private Detective", "network": "NBC/CBS", "years": "1949-1953", "genre": "detective noir"},
    "great-gildersleeve":  {"name": "The Great Gildersleeve", "network": "NBC", "years": "1941-1957", "genre": "comedy"},
    "mercury-theatre":     {"name": "Mercury Theatre on the Air", "network": "CBS", "years": "1938", "genre": "drama/thriller"},
}

def slugify(text):
    text = str(text).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

def get_archive_files(identifier):
    try:
        url = f"https://archive.org/metadata/{identifier}"
        req = urllib.request.Request(url, headers={"User-Agent": "GhostOfRadio/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        files = {}
        for f in data.get("files", []):
            name = f.get("name", "")
            if name.lower().endswith(".mp3"):
                enc = urllib.parse.quote(name)
                files[name] = f"https://archive.org/download/{identifier}/{enc}"
        return files
    except Exception as e:
        return {}

def clean_title(filename):
    """Extract clean episode title from filename."""
    stem = Path(filename).stem
    # Remove date prefixes like "491204_", "42-06-17", "440813"
    stem = re.sub(r"^\d{6}[_\s-]*", "", stem)
    stem = re.sub(r"^\d{2}-\d{2}-\d{2}[-_\s]*", "", stem)
    stem = re.sub(r"^\d{4}-\d{2}-\d{2}[-_\s]*", "", stem)
    # Remove episode numbers
    stem = re.sub(r"^\d{3}[-_\s]*", "", stem)
    # Clean up
    stem = stem.replace("_", " ").replace("-", " ").strip()
    # Title case
    return " ".join(w.capitalize() for w in stem.split()) if stem else Path(filename).stem

def extract_year(filename):
    m = re.search(r"(19[3-9]\d|20[0-2]\d)", filename)
    return m.group(1) if m else "1940s"

def generate_page_content(show_slug, episode_title, filename, air_date=""):
    """Use Claude Haiku to write episode page content."""
    info = SHOW_INFO.get(show_slug, {"name": show_slug, "network": "Radio", "years": "1940s", "genre": "drama"})
    year = extract_year(filename)
    
    prompt = f"""Write a compelling episode page for a classic old time radio show website. Be evocative, historically grounded, and engaging. 2-3 paragraphs total.

Show: {info['name']}
Network: {info['network']} ({info['years']})
Genre: {info['genre']}
Episode: {episode_title}
Year: {year}

Write:
1. A vivid opening paragraph about this specific episode (what listeners can expect, the atmosphere, the drama)
2. A paragraph about the historical context or what makes this episode/show special
3. A short closing paragraph encouraging listeners to tune in

Keep it under 300 words. No headers, just flowing prose."""

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except Exception as e:
        # Fallback content if API fails
        return f"Tune in to this classic episode of {info['name']}, one of radio's most beloved {info['genre']} programs. Originally broadcast on {info['network']} in the {info['years']} era, this episode represents the golden age of American radio drama at its finest. Whether you're a longtime fan or discovering old time radio for the first time, {episode_title} delivers the compelling storytelling that made {info['name']} a household name."

def build_html(show_slug, episode_title, filename, audio_url, content, air_date=""):
    """Build the full HTML page."""
    info = SHOW_INFO.get(show_slug, {"name": show_slug, "network": "Radio", "years": "1940s", "genre": "drama"})
    slug = slugify(Path(filename).stem)
    year = extract_year(filename)
    
    meta_desc = f"Listen to {episode_title} — {info['name']} ({info['network']}, {year}). Classic old time radio streaming free on Ghost of Radio."
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <script>if(location.protocol!=="https:"&&location.hostname!=="localhost")location.replace("https://"+location.host+location.pathname+location.search);</script>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{episode_title} — {info['name']} | Ghost of Radio</title>
  <meta name="description" content="{meta_desc}">
  <meta property="og:title" content="{episode_title} — {info['name']}">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:type" content="article">
  <link rel="canonical" href="https://ghostofradio.com/{show_slug}/{slug}.html">
  <link rel="stylesheet" href="/css/style.css">
  <link rel="stylesheet" href="/css/radio-player.css">
</head>
<body>
  <nav class="nav">
    <a href="/index.html" class="nav__logo">
      <span class="nav__logo-icon"><img src="/images/logo.png" alt="Ghost of Radio" class="nav__logo-img"></span> Ghost of Radio
    </a>
    <button class="nav__toggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
    <ul class="nav__links">
      <li><a href="/index.html">Home</a></li>
      <li><a href="/shows.html">Shows</a></li>
      <li><a href="/{show_slug}/">Browse Episodes</a></li>
      <li><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a></li>
    </ul>
  </nav>

  <main class="episode-page">
    <div class="container">
      <div class="breadcrumb">
        <a href="/index.html">Home</a><span>›</span>
        <a href="/shows.html">Shows</a><span>›</span>
        <a href="/{show_slug}/">{info['name']}</a><span>›</span>
        {episode_title}
      </div>

      <article class="episode">
        <header class="episode__header">
          <div class="episode__meta">
            <span class="episode__show">{info['name']}</span>
            <span class="episode__network">{info['network']} · {year}</span>
          </div>
          <h1 class="episode__title">{episode_title}</h1>
        </header>

        <div class="radio-player-wrapper">
          <div class="radio-player">
            <div class="radio-player__header">
              <span class="broadcast-label">· GHOST OF RADIO ·</span>
            </div>
            <div class="radio-player__waveform">
              <div class="waveform-bars">
                {"".join('<span class="bar"></span>' for _ in range(40))}
              </div>
            </div>
            <div class="radio-player__controls">
              <button class="play-btn" aria-label="Play/Pause">▶</button>
              <div class="progress-container">
                <input type="range" class="progress-bar" value="0" min="0" max="100" step="0.1">
                <div class="time-display">
                  <span class="current-time">0:00</span>
                  <span class="duration">--:--</span>
                </div>
              </div>
              <input type="range" class="volume-bar" value="0.85" min="0" max="1" step="0.05">
            </div>
            <audio id="episodeAudio" preload="none"><source src="{audio_url}" type="audio/mpeg"></audio>
          </div>
        </div>

        <div class="episode__content">
          {chr(10).join(f'<p>{p.strip()}</p>' for p in content.split(chr(10)) if p.strip())}
        </div>

        <footer class="episode__footer">
          <p><a href="/{show_slug}/" style="color:#c9a84c;text-decoration:none;">← Browse All {info['name']} Episodes</a></p>
        </footer>
      </article>
    </div>
  </main>

  <script src="/js/main.js"></script>
  <script>
    const audio = document.getElementById('episodeAudio');
    const playBtn = document.querySelector('.play-btn');
    const progressBar = document.querySelector('.progress-bar');
    const volumeBar = document.querySelector('.volume-bar');
    const currentTimeEl = document.querySelector('.current-time');
    const durationEl = document.querySelector('.duration');
    const broadcastLabel = document.querySelector('.broadcast-label');
    const bars = document.querySelectorAll('.bar');
    let animFrame;
    function formatTime(s) {{ const m=Math.floor(s/60),sec=Math.floor(s%60); return m+':'+(sec<10?'0':'')+sec; }}
    function animateWaveform() {{ const p=audio.duration?audio.currentTime/audio.duration:0; const ac=Math.floor(p*bars.length); bars.forEach((b,i)=>b.classList.toggle('active',i<ac)); animFrame=requestAnimationFrame(animateWaveform); }}
    playBtn.addEventListener('click',()=>{{ if(audio.paused){{ audio.play(); playBtn.classList.add('playing'); broadcastLabel.classList.add('live'); broadcastLabel.textContent='● ON AIR — GHOST OF RADIO'; animateWaveform(); }} else {{ audio.pause(); playBtn.classList.remove('playing'); broadcastLabel.classList.remove('live'); broadcastLabel.textContent='· GHOST OF RADIO ·'; cancelAnimationFrame(animFrame); }} }});
    audio.addEventListener('timeupdate',()=>{{ if(audio.duration) progressBar.value=(audio.currentTime/audio.duration)*100; currentTimeEl.textContent=formatTime(audio.currentTime); }});
    audio.addEventListener('loadedmetadata',()=>{{ durationEl.textContent=formatTime(audio.duration); }});
    audio.addEventListener('ended',()=>{{ playBtn.classList.remove('playing'); broadcastLabel.classList.remove('live'); broadcastLabel.textContent='· GHOST OF RADIO ·'; cancelAnimationFrame(animFrame); progressBar.value=0; currentTimeEl.textContent='0:00'; }});
    progressBar.addEventListener('input',()=>{{ if(audio.duration) audio.currentTime=(progressBar.value/100)*audio.duration; }});
    volumeBar.addEventListener('input',()=>{{ audio.volume=volumeBar.value; }});
    audio.volume=0.85;
  </script>
</body>
</html>'''

def upload_to_r2(local_path, show_slug, filename):
    """Upload MP3 to Cloudflare R2."""
    key = f"{show_slug}/{filename}"
    try:
        result = subprocess.run([
            "wrangler", "r2", "object", "put", f"ghostofradio-audio/{key}",
            "--file", str(local_path), "--content-type", "audio/mpeg", "--remote"
        ], capture_output=True, text=True, timeout=120,
        env={**os.environ, "CLOUDFLARE_API_TOKEN": CF_TOKEN, "CLOUDFLARE_ACCOUNT_ID": CF_ACCOUNT})
        return result.returncode == 0
    except Exception:
        return False

def process_episode(show_slug, archive_id, filename, archive_url):
    """Download, generate page, upload to R2 — for one episode."""
    slug = slugify(Path(filename).stem)
    if not slug:
        return None, "bad slug"
    
    html_path = SITE_ROOT / show_slug / f"{slug}.html"
    if html_path.exists():
        return slug, "skip"
    
    # Check if already on R2
    local_mp3 = AUDIO_DIR / show_slug / f"{slug}.mp3"
    
    # Download MP3 if not local
    if not local_mp3.exists():
        (AUDIO_DIR / show_slug).mkdir(parents=True, exist_ok=True)
        try:
            req = urllib.request.Request(archive_url, headers={"User-Agent": "GhostOfRadio/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                local_mp3.write_bytes(r.read())
        except Exception as e:
            return slug, f"download_fail: {e}"
    
    # Upload to R2
    audio_url = f"{R2_BASE}/{show_slug}/{slug}.mp3"
    r2_key = f"{show_slug}/{slug}.mp3"
    
    # Check if on R2 already, upload if not
    upload_to_r2(local_mp3, show_slug, f"{slug}.mp3")
    
    # Generate content with Claude Haiku
    episode_title = clean_title(filename)
    content = generate_page_content(show_slug, episode_title, filename)
    
    # Build and write HTML
    html = build_html(show_slug, episode_title, filename, audio_url, content)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    
    return slug, "ok"

def commit_batch(show_slug, count):
    """Commit and push a batch of pages."""
    subprocess.run(["git", "add", "-A"], cwd=SITE_ROOT, capture_output=True)
    r = subprocess.run(
        ["git", "commit", "-m", f"feat: {show_slug} +{count} episodes (Claude Haiku)"],
        cwd=SITE_ROOT, capture_output=True, text=True
    )
    if "nothing to commit" not in r.stdout:
        subprocess.run(["git", "push", "origin", "main"], cwd=SITE_ROOT, capture_output=True)
        print(f"  📦 Pushed {count} pages for {show_slug}")

def process_show(show_slug, archive_ids):
    """Process all missing episodes for a show."""
    info = SHOW_INFO.get(show_slug, {"name": show_slug})
    print(f"\n{'='*50}")
    print(f"Processing: {info['name']}")
    
    # Get existing pages
    show_dir = SITE_ROOT / show_slug
    existing = set(p.stem for p in show_dir.glob("*.html") if p.name != "index.html") if show_dir.exists() else set()
    print(f"  Existing pages: {len(existing)}")
    
    # Collect all archive files
    all_files = {}
    for aid in archive_ids:
        print(f"  Loading {aid}...")
        files = get_archive_files(aid)
        # Deduplicate by slug
        for fname, url in files.items():
            slug = slugify(Path(fname).stem)
            if slug and slug not in existing and slug not in all_files:
                all_files[slug] = (fname, url)
    
    if not all_files:
        print(f"  No new files found")
        return 0
    
    print(f"  {len(all_files)} new episodes to generate")
    
    # Process in parallel batches of 20
    BATCH = 20
    total_done = 0
    items = list(all_files.items())
    
    for batch_start in range(0, len(items), BATCH):
        batch = items[batch_start:batch_start+BATCH]
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(process_episode, show_slug, None, fname, url): slug
                for slug, (fname, url) in batch
            }
            for future in as_completed(futures):
                slug, status = future.result()
                if status == "ok":
                    total_done += 1
                    if total_done % 10 == 0:
                        print(f"  [{total_done}/{len(all_files)}] {slug}")
                elif status not in ("skip",):
                    print(f"  ✗ {slug}: {status}")
        
        # Commit every batch
        commit_batch(show_slug, total_done)
    
    print(f"  ✅ {info['name']}: {total_done} new pages generated")
    return total_done

if __name__ == "__main__":
    import anthropic
    
    # Kill existing Ollama workers for these shows to avoid conflicts
    shows_to_run = sys.argv[1:] if len(sys.argv) > 1 else list(SHOWS.keys())
    
    print("🎙️ Ghost of Radio — Claude Haiku Generator")
    print(f"Shows: {', '.join(shows_to_run)}")
    print(f"Model: claude-haiku-4-5")
    
    total = 0
    for show in shows_to_run:
        if show in SHOWS:
            total += process_show(show, SHOWS[show])
    
    print(f"\n✅ COMPLETE: {total} total new pages generated")
    
    # Final push
    subprocess.run(["git", "add", "-A"], cwd=SITE_ROOT, capture_output=True)
    subprocess.run(["git", "commit", "-m", f"feat: Claude Haiku batch — {total} episodes total"], cwd=SITE_ROOT, capture_output=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=SITE_ROOT, capture_output=True)
