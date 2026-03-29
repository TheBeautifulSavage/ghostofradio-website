#!/usr/bin/env python3
"""
Ghost of Radio — Master OTRR Downloader + Page Generator
Downloads ALL 237 OTRR-verified collections from archive.org.
Verifies MP3 integrity, generates episode pages with Ollama (zero API cost).
"""

import os, re, json, time, shutil, subprocess, urllib.request, urllib.parse
import hashlib, fcntl
from pathlib import Path
from datetime import datetime

SITE_ROOT = Path("/Users/mac1/Projects/ghostofradio")
OTR_LIB = Path("/Users/mac1/OTR_Library")
DOWNLOAD_DIR = OTR_LIB / "OTRR_Downloads"
BLOG_OUTPUT = SITE_ROOT / "blog"
AUDIO_OUTPUT = SITE_ROOT / "audio"
LOG_DIR = SITE_ROOT / "scripts/logs"
STATE_FILE = OTR_LIB / "otrr_state.json"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL_OVERRIDE", "llama3.2:3b")
DISK_LIMIT_GB = 200  # stop downloading if disk usage exceeds this

LOG_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

# ── State tracking (resume support) ─────────────────────────────────────────

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"completed_shows": [], "completed_episodes": {}, "failed_shows": []}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

# ── Disk usage check ─────────────────────────────────────────────────────────

def disk_gb_used(path):
    result = subprocess.run(["du", "-sg", str(path)], capture_output=True, text=True)
    try: return int(result.stdout.split()[0])
    except: return 0

# ── Archive.org API ──────────────────────────────────────────────────────────

def get_all_otrr_identifiers():
    """Fetch all OTRR singles collection identifiers from archive.org."""
    all_ids = []
    try:
        saved = OTR_LIB / "otrr_collections.json"
        if saved.exists():
            docs = json.loads(saved.read_text())
            all_ids = [d.get("identifier","") for d in docs if d.get("identifier")]
        
        # Also search for more pages
        for page in range(0, 3):
            url = f"https://archive.org/advancedsearch.php?q=identifier%3AOTRR_*_Singles&output=json&rows=100&start={page*100}&fl[]=identifier,title"
            req = urllib.request.Request(url, headers={"User-Agent": "GhostOfRadio/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
            docs = data.get("response", {}).get("docs", [])
            if not docs: break
            for doc in docs:
                ident = doc.get("identifier","")
                if ident and ident not in all_ids:
                    all_ids.append(ident)
    except Exception as e:
        log(f"Warning: could not fetch full list: {e}")
    
    return all_ids

def get_collection_files(identifier):
    """Get all MP3 files from an archive.org identifier with metadata."""
    try:
        url = f"https://archive.org/metadata/{identifier}"
        req = urllib.request.Request(url, headers={"User-Agent": "GhostOfRadio/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        
        metadata = data.get("metadata", {})
        files = data.get("files", [])
        
        mp3s = []
        for f in files:
            name = f.get("name", "")
            if not name.lower().endswith(".mp3"):
                continue
            size = int(f.get("size", 0))
            md5 = f.get("md5", "")
            if size < 50000:  # skip tiny files (probably corrupt)
                continue
            url_file = f"https://archive.org/download/{identifier}/{urllib.parse.quote(name)}"
            mp3s.append({"name": name, "url": url_file, "size": size, "md5": md5})
        
        show_title = metadata.get("title", identifier.replace("OTRR_","").replace("_Singles","").replace("_"," "))
        show_desc = metadata.get("description", "")[:300] if metadata.get("description") else ""
        
        return show_title, show_desc, mp3s
    except Exception as e:
        return identifier, "", []

def verify_mp3(path, expected_md5=None):
    """Verify MP3 file integrity."""
    if not path.exists() or path.stat().st_size < 50000:
        return False
    # Check magic bytes
    try:
        with open(path, "rb") as f:
            header = f.read(3)
        if header[:2] in [b'\xff\xfb', b'\xff\xf3', b'\xff\xf2', b'ID3']:
            return True
        if header[:3] == b'ID3':
            return True
    except:
        return False
    return False

def download_file(url, dest, expected_md5=None, retries=3):
    """Download with verification and retry."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "GhostOfRadio/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
                shutil.copyfileobj(r, f)
            if verify_mp3(dest, expected_md5):
                return True
            else:
                dest.unlink(missing_ok=True)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return False

# ── Show name → slug extraction ──────────────────────────────────────────────

def identifier_to_show_info(identifier, title):
    """Convert OTRR identifier to show slug and clean name."""
    # Strip OTRR_ prefix and _Singles suffix
    clean = identifier
    clean = re.sub(r'^OTRR_', '', clean)
    clean = re.sub(r'_Singles.*$', '', clean)
    clean = re.sub(r'_Season_\d+$', '', clean)
    slug = clean.lower().replace('_', '-')
    
    # Use title if it's cleaner
    if title and len(title) < 80:
        show_name = re.sub(r'\s*-\s*Single Episodes.*$', '', title, flags=re.IGNORECASE).strip()
    else:
        show_name = clean.replace('_', ' ')
    
    return slug, show_name

# ── Episode parsing ──────────────────────────────────────────────────────────

def slugify(text):
    text = str(text).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")[:80]

def parse_filename(filename, show_name=""):
    name = Path(filename).stem
    # Remove show name prefix if present
    if show_name:
        show_slug = slugify(show_name)[:20]
        name = re.sub(rf'^{re.escape(show_slug)}[_\-\s]*', '', name, flags=re.IGNORECASE)
    
    patterns = [
        (r'(\d{4}-\d{2}-\d{2})[_\s-]+(.+)', '%Y-%m-%d'),
        (r'(\d{2}-\d{2}-\d{2})[_\s]+ep\d+[_\s]+(.+)', None),
        (r'(\d{6})[_\s-]*ep\d+[_\s]+(.+)', None),
        (r'(\d{6})[_\s]+\d+[_\s]+(.+)', None),
        (r'(\d{6})[_\s-]+(.+)', None),
    ]
    
    for pat, fmt in patterns:
        m = re.match(pat, name, re.IGNORECASE)
        if m:
            datestr, title = m.group(1), m.group(2).replace('_',' ').replace('-',' ').strip()
            date = None
            try:
                if fmt:
                    date = datetime.strptime(datestr, fmt)
                elif len(datestr) == 6:
                    yy = int(datestr[:2])
                    year = 1900 + yy if yy >= 20 else 2000 + yy
                    date = datetime.strptime(str(year) + datestr[2:], "%Y%m%d")
                elif len(datestr) == 8:
                    yy = int(datestr[:2])
                    year = 1900 + yy if yy >= 20 else 2000 + yy
                    date = datetime.strptime(str(year) + datestr[2:], "%Y%m%d")
            except: pass
            return date, title
    
    # Fallback: whole filename as title
    clean = name.replace('_',' ').replace('-',' ').strip()
    return None, clean

# ── Ollama content generation ────────────────────────────────────────────────

def ollama_generate(prompt, timeout=90):
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip()
    except:
        return ""

def generate_content(show_name, show_desc, episode_title, date, network="Radio"):
    year = date.year if date else "the golden age of radio"
    date_str = date.strftime("%B %d, %Y") if date else "Unknown date"
    
    prompt = f"""Cultural historian writing for ghostofradio.com. Old time radio expert.

Show: {show_name}
Episode: {episode_title}  
Air Date: {date_str}
{f'About the show: {show_desc[:200]}' if show_desc else ''}

Write EXACTLY:

EPISODE_SUMMARY:
2 vivid paragraphs. Atmosphere, drama, what makes this episode compelling.

HISTORICAL_CONTEXT:
2 paragraphs. America in {year} — specific events, cultural mood, why radio mattered.

WHY_IT_MATTERS:
1 paragraph. The craft and why to listen today.

Max 450 words. Flowing prose only."""

    response = ollama_generate(prompt)
    sections = {"summary": "", "historical": "", "why": ""}
    parts = re.split(r"(EPISODE_SUMMARY:|HISTORICAL_CONTEXT:|WHY_IT_MATTERS:)", response)
    for i, part in enumerate(parts):
        if "EPISODE_SUMMARY:" in part and i+1 < len(parts): sections["summary"] = parts[i+1].strip()
        elif "HISTORICAL_CONTEXT:" in part and i+1 < len(parts): sections["historical"] = parts[i+1].strip()
        elif "WHY_IT_MATTERS:" in part and i+1 < len(parts): sections["why"] = parts[i+1].strip()
    if not any(sections.values()): sections["summary"] = response[:500] if response else f"A classic episode of {show_name}."
    return sections

# ── HTML generation ──────────────────────────────────────────────────────────

def paras(text):
    if not text: return "<p>A classic episode from the golden age of radio.</p>"
    return "".join(f"<p>{p.strip()}</p>\n" for p in text.split("\n\n") if p.strip())

def build_episode_page(show_slug, show_name, show_desc, episode_title, date, mp3_web, content, prev_ep=None, next_ep=None):
    date_str = date.strftime("%B %d, %Y") if date else "Classic Radio"
    date_iso = date.strftime("%Y-%m-%d") if date else ""
    year = date.year if date else ""
    canonical = f"https://ghostofradio.com/blog/{show_slug}/{slugify(episode_title)}.html"
    
    import random; random.seed(hash(episode_title + show_slug))
    bars = str([random.randint(4, 32) for _ in range(56)])
    
    prev_html = f'<a href="{prev_ep[0]}">&larr; {prev_ep[1][:35]}...</a>' if prev_ep else "<span></span>"
    next_html = f'<a href="{next_ep[0]}">{next_ep[1][:35]}... &rarr;</a>' if next_ep else "<span></span>"
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{episode_title} | {show_name} | {date_str} | Ghost of Radio</title>
<meta name="description" content="Stream free: '{episode_title}' — {show_name} ({date_str}). {show_desc[:120] if show_desc else 'Classic old time radio.'}">
<meta property="og:title" content="{episode_title} | {show_name} | Ghost of Radio">
<meta property="og:type" content="article">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="Ghost of Radio">
<link rel="canonical" href="{canonical}">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":"{episode_title} — {show_name} ({date_str})","datePublished":"{date_iso}","author":{{"@type":"Organization","name":"Ghost of Radio"}},"mainEntityOfPage":"{canonical}"}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
<link rel="stylesheet" href="/css/radio-player.css">
</head>
<body>
<header class="site-header"><nav class="nav">
<a href="/index.html" class="nav__logo"><span class="nav__logo-icon"><img src="/images/logo.png" alt="Ghost of Radio" class="nav__logo-img"></span> Ghost of Radio</a>
<button class="nav__toggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
<ul class="nav__links"><li><a href="/index.html">Home</a></li><li><a href="/shows.html">Shows</a></li><li><a href="/blog/{show_slug}/">Browse Episodes</a></li><li><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a></li></ul>
</nav></header>

<div class="page-header">
<div class="container"><div class="breadcrumb"><a href="/index.html">Home</a><span>›</span><a href="/shows.html">Shows</a><span>›</span><a href="/blog/{show_slug}/">{show_name}</a><span>›</span>{episode_title}</div></div>
<h1 class="flicker">{episode_title}</h1><div class="divider"></div>
<p>{show_name} &nbsp;·&nbsp; {date_str}</p>
</div>

<section class="section"><div class="container"><article class="about-content fade-in">

<div class="episode-meta-box">
<div class="episode-meta-item"><span class="episode-meta-label">Air Date</span><span class="episode-meta-value">{date_str}</span></div>
<div class="episode-meta-item"><span class="episode-meta-label">Show</span><span class="episode-meta-value">{show_name}</span></div>
</div>

<div class="radio-player">
<div class="radio-top"><div class="radio-grille"></div><div class="radio-info">
<div class="radio-show-name">{show_name}</div>
<div class="radio-episode-title">{episode_title}</div>
<div class="radio-meta">{date_str}</div>
</div></div>
<div class="radio-body">
<div class="radio-waveform" id="waveform" aria-hidden="true"></div>
<div class="radio-controls">
<button class="radio-play-btn" id="playBtn" aria-label="Play">
<svg class="play-icon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
<svg class="pause-icon" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
</button>
<div class="radio-progress-wrap">
<input type="range" class="radio-progress" id="progressBar" min="0" max="100" value="0" step="0.1">
<div class="radio-time"><span id="currentTime">0:00</span><span id="duration">--:--</span></div>
</div>
<div class="radio-volume-wrap">
<svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/></svg>
<input type="range" class="radio-volume" id="volumeBar" min="0" max="1" step="0.05" value="0.85">
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

<div class="divider" style="margin:3rem auto;"></div>
<div class="episode-nav">{prev_html}{next_html}</div>
<div class="divider" style="margin:3rem auto;"></div>
<p style="text-align:center;font-family:var(--font-heading);font-size:.75rem;letter-spacing:.15em;color:#6b6355;">
<a href="/blog/{show_slug}/" style="color:#c9a84c;text-decoration:none;">← All {show_name} Episodes</a></p>
</article></div></section>

<footer class="site-footer"><div class="container">
<p>&copy; 2024 Ghost of Radio — Where Vintage Broadcasts Return from the Dead</p>
<p><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a></p>
</div></footer>
<script src="/js/main.js"></script>
<script>
const heights={bars};
const wf=document.getElementById('waveform');
heights.forEach(h=>{{const b=document.createElement('span');b.style.height=h+'px';wf.appendChild(b);}});
const audio=document.getElementById('episodeAudio'),pb2=document.getElementById('playBtn'),pb=document.getElementById('progressBar'),vb=document.getElementById('volumeBar'),ct=document.getElementById('currentTime'),dur=document.getElementById('duration'),bl=document.getElementById('broadcastLabel'),brs=wf.querySelectorAll('span');
function fmt(s){{if(isNaN(s))return'--:--';return Math.floor(s/60)+':'+(Math.floor(s%60)<10?'0':'')+Math.floor(s%60);}}
let af;function anim(){{const p=audio.duration?audio.currentTime/audio.duration:0;brs.forEach((b,i)=>b.classList.toggle('active',i<Math.floor(p*brs.length)));af=requestAnimationFrame(anim);}}
pb2.addEventListener('click',()=>{{if(audio.paused){{audio.play();pb2.classList.add('playing');bl.classList.add('live');bl.textContent='● ON AIR — GHOST OF RADIO';anim();}}else{{audio.pause();pb2.classList.remove('playing');bl.classList.remove('live');bl.textContent='· GHOST OF RADIO ·';cancelAnimationFrame(af);}}}});
audio.addEventListener('timeupdate',()=>{{if(audio.duration)pb.value=(audio.currentTime/audio.duration)*100;ct.textContent=fmt(audio.currentTime);}});
audio.addEventListener('loadedmetadata',()=>{{dur.textContent=fmt(audio.duration);}});
audio.addEventListener('ended',()=>{{pb2.classList.remove('playing');bl.classList.remove('live');bl.textContent='· GHOST OF RADIO ·';cancelAnimationFrame(af);pb.value=0;ct.textContent='0:00';}});
pb.addEventListener('input',()=>{{if(audio.duration)audio.currentTime=(pb.value/100)*audio.duration;}});
vb.addEventListener('input',()=>{{audio.volume=vb.value;}});
audio.volume=.85;
</script>
</body></html>"""

def build_show_index(show_slug, show_name, show_desc, episodes):
    cards = ""
    for ep in episodes:
        ds = ep["date"].strftime("%B %d, %Y") if ep.get("date") else "Classic Radio"
        cards += f'<a href="/blog/{show_slug}/{ep["slug"]}.html" class="episode-card"><div class="episode-card__date">{ds}</div><div class="episode-card__title">{ep["title"]}</div><div class="episode-card__listen">▶ Listen Free</div></a>\n'
    
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{show_name} — All Episodes | Ghost of Radio</title>
<meta name="description" content="Stream all {len(episodes)} episodes of {show_name} free on Ghost of Radio. {show_desc[:150] if show_desc else 'Classic old time radio.'}">
<link rel="canonical" href="https://ghostofradio.com/blog/{show_slug}/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
<style>
.ep-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem;margin-top:2rem}}
.episode-card{{background:#1a1a1a;border:1px solid #2a2010;border-radius:8px;padding:1.25rem;text-decoration:none;display:block;transition:border-color .2s,background .2s}}
.episode-card:hover{{border-color:#c9a84c;background:#1f1c14}}
.episode-card__date{{font-family:var(--font-heading);font-size:.65rem;letter-spacing:.15em;color:#6b6355;text-transform:uppercase;margin-bottom:.4rem}}
.episode-card__title{{font-family:var(--font-heading);color:#e8e0d0;font-size:.95rem;line-height:1.3;margin-bottom:.5rem}}
.episode-card__listen{{font-family:var(--font-heading);font-size:.65rem;color:#c9a84c;letter-spacing:.1em}}
.srch{{width:100%;max-width:420px;background:#111;border:1px solid #3a2e1e;color:#e8e0d0;font-family:var(--font-heading);padding:.65rem 1rem;border-radius:6px;font-size:.85rem;margin-bottom:1.5rem}}
.srch:focus{{outline:none;border-color:#c9a84c}}
</style>
</head><body>
<header class="site-header"><nav class="nav">
<a href="/index.html" class="nav__logo"><span class="nav__logo-icon"><img src="/images/logo.png" alt="Ghost of Radio" class="nav__logo-img"></span> Ghost of Radio</a>
<button class="nav__toggle" aria-label="Toggle" aria-expanded="false"><span></span><span></span><span></span></button>
<ul class="nav__links"><li><a href="/index.html">Home</a></li><li><a href="/shows.html">Shows</a></li><li><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a></li></ul>
</nav></header>
<div class="page-header"><h1 class="flicker">{show_name}</h1><div class="divider"></div><p>{len(episodes)} Episodes — Stream Free</p></div>
<section class="section"><div class="container">
{f'<p style="font-family:var(--font-body);color:var(--text-dim);font-size:1.1rem;line-height:1.8;max-width:680px;margin:0 auto 2rem;">{show_desc}</p>' if show_desc else ''}
<input type="text" class="srch" placeholder="Search episodes..." oninput="document.querySelectorAll('.episode-card').forEach(c=>c.style.display=c.textContent.toLowerCase().includes(this.value.toLowerCase())?'':'none')">
<div class="ep-grid">{cards}</div>
</div></section>
<footer class="site-footer"><div class="container">
<p>&copy; 2024 Ghost of Radio — Where Vintage Broadcasts Return from the Dead</p>
<p><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a></p>
</div></footer>
<script src="/js/main.js"></script>
</body></html>"""

# ── Git ──────────────────────────────────────────────────────────────────────

def git_commit_safe(message):
    lock = open(str(SITE_ROOT / ".git_commit_lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        subprocess.run(["git", "add", "-A"], cwd=SITE_ROOT, capture_output=True)
        r = subprocess.run(["git", "commit", "-m", message], cwd=SITE_ROOT, capture_output=True, text=True)
        if r.returncode == 0: log(f"📦 {message}")
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=SITE_ROOT, capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=SITE_ROOT, capture_output=True)
    except Exception as e: log(f"git err: {e}")
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN); lock.close()

# ── Main processor ───────────────────────────────────────────────────────────

def process_collection(identifier, state):
    if identifier in state["completed_shows"]:
        log(f"SKIP (done): {identifier}")
        return
    
    log(f"\n{'='*50}")
    log(f"Processing: {identifier}")
    
    # Get file list
    show_title, show_desc, mp3_files = get_collection_files(identifier)
    if not mp3_files:
        log(f"  No MP3s found — skipping")
        state["failed_shows"].append(identifier)
        return
    
    log(f"  {show_title} — {len(mp3_files)} episodes")
    
    show_slug, show_name = identifier_to_show_info(identifier, show_title)
    
    # Directories
    dl_dir = DOWNLOAD_DIR / show_slug
    dl_dir.mkdir(parents=True, exist_ok=True)
    blog_dir = BLOG_OUTPUT / show_slug
    blog_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = AUDIO_OUTPUT / show_slug
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # Check disk space
    if disk_gb_used(DOWNLOAD_DIR) > DISK_LIMIT_GB:
        log(f"  ⚠️ Disk limit reached ({DISK_LIMIT_GB}GB). Skipping downloads, generating from existing.")
    
    # Build episode list
    episodes = []
    for f in mp3_files:
        date, title = parse_filename(f["name"], show_name)
        ep_slug = slugify(title)
        episodes.append({
            "name": f["name"], "url": f["url"], "size": f["size"],
            "md5": f.get("md5",""), "date": date, "title": title, "slug": ep_slug
        })
    episodes.sort(key=lambda e: e["date"] or datetime(1900,1,1))
    
    # Process each episode
    committed = 0
    ep_done = state["completed_episodes"].get(identifier, [])
    
    for i, ep in enumerate(episodes):
        if ep["slug"] in ep_done:
            continue
        
        # Download MP3
        dest_mp3 = audio_dir / f"{ep['slug']}.mp3"
        if not verify_mp3(dest_mp3):
            # Try local download dir first
            local = dl_dir / ep["name"]
            if verify_mp3(local):
                shutil.copy2(local, dest_mp3)
            else:
                # Download from archive.org
                if disk_gb_used(DOWNLOAD_DIR) < DISK_LIMIT_GB:
                    success = download_file(ep["url"], dest_mp3, ep.get("md5"))
                    if not success:
                        log(f"  ⚠️ Download failed: {ep['title'][:40]}")
                        continue
                else:
                    log(f"  SKIP (disk full): {ep['title'][:40]}")
                    continue
        
        mp3_web = f"/audio/{show_slug}/{ep['slug']}.mp3"
        
        # Check if page already exists
        out_html = blog_dir / f"{ep['slug']}.html"
        if out_html.exists():
            ep_done.append(ep["slug"])
            continue
        
        # Generate content
        log(f"  [{i+1}/{len(episodes)}] {ep['title'][:50]}")
        try:
            content = generate_content(show_name, show_desc, ep["title"], ep["date"])
        except Exception as e:
            content = {"summary": f"A classic episode of {show_name}.", "historical": "", "why": "Essential old time radio listening."}
        
        # Navigation
        prev_ep = (f"/blog/{show_slug}/{episodes[i-1]['slug']}.html", episodes[i-1]['title']) if i > 0 else None
        next_ep = (f"/blog/{show_slug}/{episodes[i+1]['slug']}.html", episodes[i+1]['title']) if i < len(episodes)-1 else None
        
        # Write HTML
        html = build_episode_page(show_slug, show_name, show_desc, ep["title"], ep["date"], mp3_web, content, prev_ep, next_ep)
        out_html.write_text(html, encoding="utf-8")
        
        ep_done.append(ep["slug"])
        committed += 1
        
        if committed % 10 == 0:
            state["completed_episodes"][identifier] = ep_done
            save_state(state)
            git_commit_safe(f"feat: {show_name} — {committed} episodes")
    
    # Write index page
    index_html = build_show_index(show_slug, show_name, show_desc, episodes)
    (blog_dir / "index.html").write_text(index_html, encoding="utf-8")
    
    state["completed_shows"].append(identifier)
    state["completed_episodes"][identifier] = ep_done
    save_state(state)
    git_commit_safe(f"feat: complete {show_name} ({len(episodes)} eps)")
    log(f"  ✅ {show_name} complete")

# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    log(f"Ghost of Radio — Master OTRR Downloader")
    log(f"Model: {OLLAMA_MODEL} | Disk limit: {DISK_LIMIT_GB}GB")
    
    state = load_state()
    log(f"Resuming: {len(state['completed_shows'])} shows done, {len(state['failed_shows'])} failed")
    
    # Get all identifiers
    if len(sys.argv) > 1:
        identifiers = sys.argv[1:]
    else:
        identifiers = get_all_otrr_identifiers()
        log(f"Found {len(identifiers)} OTRR collections")
    
    for identifier in identifiers:
        try:
            process_collection(identifier, state)
        except KeyboardInterrupt:
            log("Interrupted — saving state")
            save_state(state)
            break
        except Exception as e:
            log(f"ERROR on {identifier}: {e}")
            state["failed_shows"].append(identifier)
            save_state(state)
            continue
    
    log(f"\n✅ Complete. {len(state['completed_shows'])} shows processed.")
