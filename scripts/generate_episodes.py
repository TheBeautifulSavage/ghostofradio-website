#!/usr/bin/env python3
"""
Ghost of Radio — Bulk Episode Generator
Uses Ollama (local, zero API cost) to generate historical context posts for OTR episodes.
"""

import os
import re
import json
import shutil
import subprocess
import time
from pathlib import Path
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────
OLLAMA_MODEL = "qwen2.5:14b"
SITE_ROOT = Path("/Users/mac1/Projects/ghostofradio")
AUDIO_OUTPUT = SITE_ROOT / "audio"
BLOG_OUTPUT = SITE_ROOT / "blog"
COMMIT_EVERY = 10  # commit to git every N episodes
START_FROM = 1     # skip first N episodes (for resuming)

# ── Show Definitions ─────────────────────────────────────────────────────────
SHOWS = [
    {
        "id": "shadow",
        "name": "The Shadow",
        "slug": "shadow",
        "network": "Mutual Broadcasting System",
        "years": "1937–1954",
        "description": "The classic crime drama starring Lamont Cranston, who has learned the power to cloud men's minds so they cannot see him.",
        "intro_voice": "Who knows what evil lurks in the hearts of men? The Shadow knows!",
        "mp3_dir": "/Users/mac1/OTR_Library/The_Shadow",
        "blog_subdir": "shadow",
    },
    {
        "id": "sherlock",
        "name": "The New Adventures of Sherlock Holmes",
        "slug": "sherlock",
        "network": "NBC / ABC",
        "years": "1939–1950",
        "description": "Basil Rathbone and Nigel Bruce star as Holmes and Watson in radio's most beloved detective series.",
        "intro_voice": "Elementary, my dear Watson.",
        "mp3_dir": "/Users/mac1/OTR_Library/Sherlock_Holmes",
        "blog_subdir": "sherlock",
    },
    {
        "id": "whistler",
        "name": "The Whistler",
        "slug": "whistler",
        "network": "CBS",
        "years": "1942–1955",
        "description": "A mysterious narrator who knows your innermost thoughts — and the strange twists of fate that await ordinary people who make desperate choices.",
        "intro_voice": "I am the Whistler, and I know many things, for I walk by night.",
        "mp3_dir": "/Users/mac1/OTR_Library/Old_Time_Radio_Show/OTRR_Whistler_Singles",
        "blog_subdir": "whistler",
    },
    {
        "id": "cbs-mystery",
        "name": "CBS Radio Mystery Theater",
        "slug": "cbs-mystery",
        "network": "CBS",
        "years": "1974–1982",
        "description": "E.G. Marshall hosts over 1,000 tales of mystery and suspense — the last great original radio drama anthology.",
        "intro_voice": "Come in. Welcome. I'm E.G. Marshall, your host for the CBS Radio Mystery Theater.",
        "mp3_dir": "/Users/mac1/OTR_Library/Old_Time_Radio_Show/CBS Radio Mystery cbsrmt-1975_2023",
        "blog_subdir": "cbs-mystery",
    },
    {
        "id": "sounds-of-darkness",
        "name": "Sounds of Darkness",
        "slug": "sounds-of-darkness",
        "network": "Syndicated",
        "years": "1969–1971",
        "description": "Anthology series of crime, mystery, and suspense from the twilight years of American radio drama.",
        "intro_voice": "From the shadows, a tale is told...",
        "mp3_dir": "/Users/mac1/OTR_Library/Old_Time_Radio_Show/sounds-of-darkness-sa-71-03-16-098-a-friend-of-uncle-sam_202102",
        "blog_subdir": "sounds-of-darkness",
    },
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text

def parse_episode_filename(filename, show):
    """Extract date and title from common OTR filename formats."""
    name = Path(filename).stem
    
    # Shadow format: "1937-09-26 - Death House Rescue"
    m = re.match(r"(\d{4}-\d{2}-\d{2})\s*[-–]\s*(.+)", name)
    if m:
        try:
            date = datetime.strptime(m.group(1), "%Y-%m-%d")
            return date, m.group(2).strip()
        except: pass

    # Whistler format: "Whistler_44-10-02_ep124_Not_If_I_Kill_You_First"
    m = re.match(r"[Ww]histler_(\d{2}-\d{2}-\d{2})_ep(\d+)_(.+)", name)
    if m:
        try:
            date = datetime.strptime("19" + m.group(1), "%Y-%m-%d")
            title = m.group(3).replace("_", " ").strip()
            ep_num = int(m.group(2))
            return date, title, ep_num
        except: pass

    # CBS format: "750101_194_The_Deadly_Pearls"
    m = re.match(r"(\d{6})_(\d+)_(.+)", name)
    if m:
        try:
            datestr = m.group(1)
            yy = int(datestr[:2])
            year = 1900 + yy if yy >= 70 else 2000 + yy
            date = datetime.strptime(str(year) + datestr[2:], "%Y%m%d")
            title = m.group(3).replace("_", " ").replace("-", " ").strip()
            ep_num = int(m.group(2))
            return date, title, ep_num
        except: pass

    # Sherlock format: "440515 The New Adventures of Sherlock Holmes - The Adventure..."
    m = re.match(r"(\d{6})\s*(?:The New Adventures of Sherlock Holmes\s*-\s*)?(.+)", name, re.IGNORECASE)
    if m:
        try:
            datestr = m.group(1)
            yy = int(datestr[:2])
            year = 1900 + yy if yy >= 30 else 2000 + yy
            date = datetime.strptime(str(year) + datestr[2:], "%Y%m%d")
            title = m.group(2).strip()
            return date, title
        except: pass

    # Sounds of Darkness: "Sounds Of Darkness - SA 70-01-20 (038) Tick-Tock Death"
    m = re.match(r"Sounds [Oo]f Darkness\s*-\s*SA\s+(\d{2}-\d{2}-\d{2})\s+\((\d+)\)\s+(.+)", name)
    if m:
        try:
            date = datetime.strptime("19" + m.group(1), "%Y-%m-%d")
            title = m.group(3).strip()
            ep_num = int(m.group(2))
            return date, title, ep_num
        except: pass

    # Fallback: just use filename as title
    return None, name

def ollama_generate(prompt, model=OLLAMA_MODEL):
    """Call Ollama locally — zero API cost."""
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=180
    )
    return result.stdout.strip()

def generate_episode_content(show, episode_title, air_date, episode_number=None):
    """Generate article content using local Ollama."""
    date_str = air_date.strftime("%B %d, %Y") if air_date else "Unknown date"
    year = air_date.year if air_date else "Unknown"
    
    prompt = f"""You are a skilled cultural historian and radio drama expert writing for ghostofradio.com.

Write a rich, engaging blog post about this old time radio episode. Write it like serious cultural journalism — evocative, historically grounded, deeply informative.

Show: {show['name']}
Episode: {episode_title}
Air Date: {date_str}
Network: {show['network']}

Write EXACTLY in this format with these EXACT section headers:

EPISODE_SUMMARY:
Write 2-3 paragraphs describing the episode plot, the drama, the characters. Be vivid and engaging. Make the reader WANT to listen.

HISTORICAL_CONTEXT:
Write 3-4 paragraphs about what was happening in America and the world when this episode aired in {year}. What was in the news? What was the political climate? The economy? What were ordinary Americans worried about? What made this kind of radio drama resonate with audiences at this exact moment in history? Be specific — name real events, real tensions, real cultural touchstones of the era.

WHY_IT_MATTERS:
Write 1-2 paragraphs about what makes this episode worth listening to today. What craft, performance, or storytelling technique stands out? What does it reveal about radio drama as an art form?

Keep the total response under 700 words. Write in a confident, literary voice. No bullet points. No markdown headers beyond the ones specified. Pure flowing prose."""

    response = ollama_generate(prompt)
    return parse_ollama_response(response)

def parse_ollama_response(response):
    """Parse the structured response from Ollama."""
    sections = {"summary": "", "historical": "", "why": ""}
    
    parts = re.split(r"(EPISODE_SUMMARY:|HISTORICAL_CONTEXT:|WHY_IT_MATTERS:)", response)
    
    for i, part in enumerate(parts):
        if part == "EPISODE_SUMMARY:" and i+1 < len(parts):
            sections["summary"] = parts[i+1].strip()
        elif part == "HISTORICAL_CONTEXT:" and i+1 < len(parts):
            sections["historical"] = parts[i+1].strip()
        elif part == "WHY_IT_MATTERS:" and i+1 < len(parts):
            sections["why"] = parts[i+1].strip()
    
    # Fallback: if parsing fails, use whole response as summary
    if not any(sections.values()):
        sections["summary"] = response
    
    return sections

def paragraphize(text):
    """Convert plain text to HTML paragraphs."""
    if not text:
        return ""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "".join(f"<p>{p}</p>\n" for p in paras)

def build_html(show, episode_title, air_date, episode_number, mp3_web_path, mp3_filename, content, prev_ep=None, next_ep=None):
    """Build the full HTML page."""
    date_str = air_date.strftime("%B %d, %Y") if air_date else "Unknown"
    date_iso = air_date.strftime("%Y-%m-%d") if air_date else ""
    year = air_date.year if air_date else ""
    ep_label = f"Episode {episode_number}" if episode_number else ""
    slug = slugify(episode_title)
    
    title_tag = f"{episode_title} | {show['name']} | {date_str} | Ghost of Radio"
    meta_desc = f"Listen to '{episode_title}' from {show['name']}. {date_str}. Stream free on Ghost of Radio — the ultimate old time radio archive."
    canonical = f"https://ghostofradio.com/blog/{show['blog_subdir']}/{slug}.html"

    prev_link = f'<a href="{prev_ep[0]}">&larr; {prev_ep[1]}</a>' if prev_ep else "<span></span>"
    next_link = f'<a href="{next_ep[0]}">{next_ep[1]} &rarr;</a>' if next_ep else "<span></span>"

    era_year_display = str(year) if year else ""
    
    summary_html = paragraphize(content.get("summary", ""))
    historical_html = paragraphize(content.get("historical", ""))
    why_html = paragraphize(content.get("why", ""))

    # Generate simple waveform heights
    import random
    random.seed(hash(episode_title))
    wave_heights = [random.randint(4, 32) for _ in range(56)]
    bars_js = str(wave_heights)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_tag}</title>
  <meta name="description" content="{meta_desc}">
  <meta property="og:title" content="{episode_title} | {show['name']} | {date_str}">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="Ghost of Radio">
  <meta name="twitter:card" content="summary">
  <link rel="canonical" href="{canonical}">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#0a0a0a">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{episode_title} — {show['name']} ({date_str})",
    "description": "{meta_desc}",
    "datePublished": "{date_iso}",
    "author": {{"@type": "Organization", "name": "Ghost of Radio"}},
    "publisher": {{"@type": "Organization", "name": "Ghost of Radio", "url": "https://ghostofradio.com"}},
    "mainEntityOfPage": "{canonical}"
  }}
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/style.css">
  <link rel="stylesheet" href="/css/radio-player.css">
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
        <li><a href="/shows.html">Shows</a></li>
        <li><a href="/blog/{show['blog_subdir']}/">Browse Episodes</a></li>
        <li><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a></li>
      </ul>
    </nav>
  </header>

  <div class="page-header">
    <div class="container">
      <div class="breadcrumb">
        <a href="/index.html">Home</a><span>›</span>
        <a href="/shows.html">Shows</a><span>›</span>
        <a href="/blog/{show['blog_subdir']}/">{show['name']}</a><span>›</span>
        {episode_title}
      </div>
    </div>
    <h1 class="flicker">{episode_title}</h1>
    <div class="divider"></div>
    <p>{show['name']} &nbsp;·&nbsp; {ep_label + " &nbsp;·&nbsp; " if ep_label else ""}{date_str}</p>
  </div>

  <section class="section">
    <div class="container">
      <article class="about-content fade-in">

        <div class="episode-meta-box">
          <div class="episode-meta-item">
            <span class="episode-meta-label">Air Date</span>
            <span class="episode-meta-value">{date_str}</span>
          </div>
          <div class="episode-meta-item">
            <span class="episode-meta-label">Show</span>
            <span class="episode-meta-value">{show['name']}</span>
          </div>
          <div class="episode-meta-item">
            <span class="episode-meta-label">Network</span>
            <span class="episode-meta-value">{show['network']}</span>
          </div>
          <div class="episode-meta-item">
            <span class="episode-meta-label">Era</span>
            <span class="episode-meta-value">{show['years']}</span>
          </div>
        </div>

        <!-- RADIO PLAYER -->
        <div class="radio-player" id="radioPlayer">
          <div class="radio-top">
            <div class="radio-grille"></div>
            <div class="radio-info">
              <div class="radio-show-name">{show['name']}{" · " + ep_label if ep_label else ""}</div>
              <div class="radio-episode-title">{episode_title}</div>
              <div class="radio-meta">{date_str} &nbsp;·&nbsp; {show['network']}</div>
            </div>
          </div>
          <div class="radio-body">
            <div class="radio-waveform" id="waveform" aria-hidden="true"></div>
            <div class="radio-controls">
              <button class="radio-play-btn" id="playBtn" aria-label="Play episode">
                <svg class="play-icon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                <svg class="pause-icon" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
              </button>
              <div class="radio-progress-wrap">
                <input type="range" class="radio-progress" id="progressBar" min="0" max="100" value="0" step="0.1" aria-label="Seek">
                <div class="radio-time">
                  <span id="currentTime">0:00</span>
                  <span id="duration">--:--</span>
                </div>
              </div>
              <div class="radio-volume-wrap">
                <svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/></svg>
                <input type="range" class="radio-volume" id="volumeBar" min="0" max="1" step="0.05" value="0.85" aria-label="Volume">
              </div>
            </div>
          </div>
          <div class="radio-footer">
            <span class="radio-broadcast" id="broadcastLabel">· GHOST OF RADIO ·</span>
            <a class="radio-download" href="{mp3_web_path}" download>⬇ Download MP3</a>
          </div>
          <audio id="episodeAudio" preload="none">
            <source src="{mp3_web_path}" type="audio/mpeg">
          </audio>
        </div>

        <h2>The Episode</h2>
        {summary_html}

        <div class="era-box">
          <div class="era-box-label">Historical Context</div>
          <h3>The World of {era_year_display}</h3>
          {historical_html}
        </div>

        <h2>Why Listen Today</h2>
        {why_html}

        <p><em>"{show['intro_voice']}"</em></p>

        <div class="divider" style="margin: 3rem auto;"></div>

        <div class="episode-nav">
          {prev_link}
          {next_link}
        </div>

        <div class="divider" style="margin: 3rem auto;"></div>

        <p style="text-align:center; font-family: var(--font-heading); font-size: 0.75rem; letter-spacing: 0.15em; color: #6b6355;">
          <a href="/blog/{show['blog_subdir']}/" style="color: #c9a84c; text-decoration: none;">← Browse All {show['name']} Episodes</a>
        </p>

      </article>
    </div>
  </section>

  <footer class="site-footer">
    <div class="container">
      <p>&copy; 2024 Ghost of Radio &mdash; Where Vintage Broadcasts Return from the Dead</p>
      <p><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a> &nbsp;&middot;&nbsp; <a href="/privacy-policy.html">Privacy Policy</a></p>
    </div>
  </footer>

  <script src="/js/main.js"></script>
  <script>
    const heights = {bars_js};
    const waveform = document.getElementById('waveform');
    heights.forEach(h => {{
      const bar = document.createElement('span');
      bar.style.height = h + 'px';
      waveform.appendChild(bar);
    }});
    const audio = document.getElementById('episodeAudio');
    const playBtn = document.getElementById('playBtn');
    const progressBar = document.getElementById('progressBar');
    const volumeBar = document.getElementById('volumeBar');
    const currentTimeEl = document.getElementById('currentTime');
    const durationEl = document.getElementById('duration');
    const broadcastLabel = document.getElementById('broadcastLabel');
    const bars = waveform.querySelectorAll('span');
    function formatTime(s) {{ if(isNaN(s)) return '--:--'; const m=Math.floor(s/60),sec=Math.floor(s%60); return m+':'+(sec<10?'0':'')+sec; }}
    let animFrame;
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
</html>"""

def get_mp3_files(mp3_dir):
    """Get sorted list of MP3 files from a directory."""
    d = Path(mp3_dir)
    if not d.exists():
        return []
    files = list(d.glob("*.mp3")) + list(d.glob("*.MP3"))
    return sorted(files)

def process_show(show, start_from=0):
    """Process all episodes for a show."""
    print(f"\n{'='*60}")
    print(f"Processing: {show['name']}")
    print(f"{'='*60}")
    
    mp3_files = get_mp3_files(show["mp3_dir"])
    print(f"Found {len(mp3_files)} episodes")
    
    blog_dir = BLOG_OUTPUT / show["blog_subdir"]
    blog_dir.mkdir(parents=True, exist_ok=True)
    
    audio_dir = AUDIO_OUTPUT / show["blog_subdir"]
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # Build episode list for navigation
    episodes = []
    for mp3 in mp3_files:
        result = parse_episode_filename(mp3.name, show)
        if len(result) == 3:
            date, title, ep_num = result
        else:
            date, title = result
            ep_num = None
        episodes.append({"file": mp3, "date": date, "title": title, "ep_num": ep_num, "slug": slugify(title)})
    
    committed = 0
    for i, ep in enumerate(episodes):
        if i < start_from:
            continue
        
        slug = ep["slug"]
        out_html = blog_dir / f"{slug}.html"
        
        if out_html.exists():
            print(f"  [{i+1}/{len(episodes)}] SKIP (exists): {ep['title']}")
            continue
        
        print(f"  [{i+1}/{len(episodes)}] Generating: {ep['title']} ({ep['date'].strftime('%Y-%m-%d') if ep['date'] else 'unknown date'})")
        
        # Copy MP3
        mp3_dest = audio_dir / f"{slug}.mp3"
        if not mp3_dest.exists():
            shutil.copy2(ep["file"], mp3_dest)
        mp3_web_path = f"/audio/{show['blog_subdir']}/{slug}.mp3"
        
        # Generate content with Ollama
        try:
            content = generate_episode_content(show, ep["title"], ep["date"], ep.get("ep_num"))
        except Exception as e:
            print(f"    ERROR generating content: {e}")
            content = {"summary": f"A classic episode of {show['name']}.", "historical": "", "why": "Essential listening for fans of old time radio."}
        
        # Navigation links
        prev_ep = None
        next_ep = None
        if i > 0:
            prev_slug = episodes[i-1]["slug"]
            prev_ep = (f"/blog/{show['blog_subdir']}/{prev_slug}.html", episodes[i-1]["title"])
        if i < len(episodes)-1:
            next_slug = episodes[i+1]["slug"]
            next_ep = (f"/blog/{show['blog_subdir']}/{next_slug}.html", episodes[i+1]["title"])
        
        # Build HTML
        html = build_html(show, ep["title"], ep["date"], ep.get("ep_num"), mp3_web_path, mp3_dest.name, content, prev_ep, next_ep)
        out_html.write_text(html, encoding="utf-8")
        print(f"    ✓ Written: {out_html.name}")
        
        committed += 1
        if committed % COMMIT_EVERY == 0:
            git_commit(f"feat: add {committed} {show['name']} episode posts")
    
    # Final commit for this show
    git_commit(f"feat: complete {show['name']} episode archive ({len(episodes)} episodes)")
    
    # Generate index page
    generate_show_index(show, episodes)

def generate_show_index(show, episodes):
    """Generate a browseable index page for all episodes of a show."""
    blog_dir = BLOG_OUTPUT / show["blog_subdir"]
    
    episode_cards = ""
    for ep in episodes:
        date_str = ep["date"].strftime("%B %d, %Y") if ep["date"] else "Unknown date"
        ep_label = f"Ep. {ep['ep_num']} · " if ep.get("ep_num") else ""
        episode_cards += f"""
        <a href="/blog/{show['blog_subdir']}/{ep['slug']}.html" class="episode-card">
          <div class="episode-card__date">{ep_label}{date_str}</div>
          <div class="episode-card__title">{ep['title']}</div>
          <div class="episode-card__listen">▶ Listen Free</div>
        </a>"""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{show['name']} — All Episodes | Ghost of Radio</title>
  <meta name="description" content="Browse and stream all {len(episodes)} episodes of {show['name']} free on Ghost of Radio. {show['description']}">
  <link rel="canonical" href="https://ghostofradio.com/blog/{show['blog_subdir']}/">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Special+Elite&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/style.css">
  <style>
    .episode-grid {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr)); gap:1rem; margin-top:2rem; }}
    .episode-card {{ background:#1a1a1a; border:1px solid #2a2010; border-radius:8px; padding:1.25rem; text-decoration:none; display:block; transition:border-color 0.2s, background 0.2s; }}
    .episode-card:hover {{ border-color:#c9a84c; background:#1f1c14; }}
    .episode-card__date {{ font-family:var(--font-heading); font-size:0.65rem; letter-spacing:0.15em; color:#6b6355; text-transform:uppercase; margin-bottom:0.4rem; }}
    .episode-card__title {{ font-family:var(--font-heading); color:#e8e0d0; font-size:0.95rem; line-height:1.3; margin-bottom:0.5rem; }}
    .episode-card__listen {{ font-family:var(--font-heading); font-size:0.65rem; color:#c9a84c; letter-spacing:0.1em; }}
    .show-search {{ width:100%; max-width:400px; background:#111; border:1px solid #3a2e1e; color:#e8e0d0; font-family:var(--font-heading); padding:0.6rem 1rem; border-radius:6px; font-size:0.85rem; margin-bottom:1.5rem; }}
    .show-search:focus {{ outline:none; border-color:#c9a84c; }}
  </style>
</head>
<body>
  <header class="site-header">
    <nav class="nav">
      <a href="/index.html" class="nav__logo"><span class="nav__logo-icon"><img src="/images/logo.png" alt="Ghost of Radio" class="nav__logo-img"></span> Ghost of Radio</a>
      <button class="nav__toggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
      <ul class="nav__links">
        <li><a href="/index.html">Home</a></li>
        <li><a href="/shows.html">Shows</a></li>
        <li><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a></li>
      </ul>
    </nav>
  </header>

  <div class="page-header">
    <h1 class="flicker">{show['name']}</h1>
    <div class="divider"></div>
    <p>{show['years']} &nbsp;·&nbsp; {show['network']} &nbsp;·&nbsp; {len(episodes)} Episodes</p>
  </div>

  <section class="section">
    <div class="container">
      <p class="fade-in" style="font-family:var(--font-body); color:var(--text-dim); font-size:1.1rem; line-height:1.8; max-width:680px; margin:0 auto 2rem;">
        {show['description']}
      </p>
      <input type="text" class="show-search" id="searchInput" placeholder="Search episodes..." oninput="filterEpisodes(this.value)">
      <div class="episode-grid" id="episodeGrid">
        {episode_cards}
      </div>
    </div>
  </section>

  <footer class="site-footer">
    <div class="container">
      <p>&copy; 2024 Ghost of Radio &mdash; Where Vintage Broadcasts Return from the Dead</p>
      <p><a href="https://www.youtube.com/@GhostOfRadio" target="_blank" rel="noopener">YouTube</a> &nbsp;&middot;&nbsp; <a href="/privacy-policy.html">Privacy Policy</a></p>
    </div>
  </footer>

  <script src="/js/main.js"></script>
  <script>
    function filterEpisodes(q) {{
      q = q.toLowerCase();
      document.querySelectorAll('.episode-card').forEach(card => {{
        card.style.display = card.textContent.toLowerCase().includes(q) ? '' : 'none';
      }});
    }}
  </script>
</body>
</html>"""
    
    (blog_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"  ✓ Index page written for {show['name']}")

def git_commit(message):
    """Commit current changes to git."""
    try:
        subprocess.run(["git", "add", "-A"], cwd=SITE_ROOT, capture_output=True)
        result = subprocess.run(["git", "commit", "-m", message], cwd=SITE_ROOT, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  📦 Committed: {message}")
        subprocess.run(["git", "push", "origin", "main"], cwd=SITE_ROOT, capture_output=True)
    except Exception as e:
        print(f"  Git error: {e}")

def generate_radio_player_css():
    """Write the shared radio player CSS file."""
    css = """/* Ghost of Radio — Radio Player Component */
.radio-player { background:#0d0a06; border:2px solid #3a2e1e; border-radius:12px; padding:0; margin:2.5rem 0; overflow:hidden; box-shadow:0 8px 40px rgba(0,0,0,0.7), inset 0 1px 0 rgba(201,168,76,0.15); font-family:var(--font-heading); position:relative; }
.radio-player::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,transparent,#c9a84c,#e8c96a,#c9a84c,transparent); }
.radio-top { background:linear-gradient(180deg,#1a1208 0%,#0d0a06 100%); padding:1.5rem 1.5rem 1rem; border-bottom:1px solid #2a2010; display:flex; align-items:center; gap:1rem; }
.radio-grille { width:56px; height:56px; flex-shrink:0; background:#0a0704; border:2px solid #3a2e1e; border-radius:50%; display:grid; place-items:center; position:relative; box-shadow:inset 0 2px 8px rgba(0,0,0,0.8); }
.radio-grille::after { content:''; width:24px; height:24px; border-radius:50%; background:radial-gradient(circle,#c9a84c 0%,#7a5c20 60%,#3a2e1e 100%); box-shadow:0 0 12px rgba(201,168,76,0.4); }
.radio-info { flex:1; min-width:0; }
.radio-show-name { font-family:var(--font-heading); color:#c9a84c; font-size:0.65rem; letter-spacing:0.2em; text-transform:uppercase; margin-bottom:0.2rem; opacity:0.8; }
.radio-episode-title { font-family:var(--font-heading); color:#e8e0d0; font-size:1rem; line-height:1.2; margin-bottom:0.25rem; }
.radio-meta { color:#6b6355; font-size:0.75rem; font-family:var(--font-heading); letter-spacing:0.1em; }
.radio-body { padding:1.25rem 1.5rem 1.5rem; }
.radio-waveform { height:36px; margin-bottom:1rem; display:flex; align-items:center; gap:2px; overflow:hidden; }
.radio-waveform span { display:block; width:3px; border-radius:2px; background:#3a2e1e; flex-shrink:0; transition:background 0.2s; }
.radio-waveform span.active { background:#c9a84c; }
.radio-controls { display:flex; align-items:center; gap:1rem; margin-bottom:1rem; }
.radio-play-btn { width:44px; height:44px; border-radius:50%; background:linear-gradient(135deg,#c9a84c,#a8893e); border:none; cursor:pointer; display:flex; align-items:center; justify-content:center; flex-shrink:0; box-shadow:0 2px 12px rgba(201,168,76,0.3); transition:transform 0.1s,box-shadow 0.2s; }
.radio-play-btn:hover { transform:scale(1.05); box-shadow:0 4px 20px rgba(201,168,76,0.5); }
.radio-play-btn:active { transform:scale(0.97); }
.radio-play-btn svg { width:18px; height:18px; fill:#0a0704; margin-left:2px; }
.radio-play-btn.playing .play-icon { display:none; }
.radio-play-btn.playing .pause-icon { display:block; }
.radio-play-btn .pause-icon { display:none; margin-left:0; }
.radio-progress-wrap { flex:1; }
.radio-progress { width:100%; -webkit-appearance:none; appearance:none; height:4px; background:#2a2010; border-radius:2px; outline:none; cursor:pointer; margin-bottom:0.4rem; }
.radio-progress::-webkit-slider-thumb { -webkit-appearance:none; width:14px; height:14px; border-radius:50%; background:#c9a84c; cursor:pointer; box-shadow:0 0 6px rgba(201,168,76,0.5); }
.radio-time { display:flex; justify-content:space-between; font-family:var(--font-heading); font-size:0.65rem; color:#6b6355; letter-spacing:0.1em; }
.radio-volume-wrap { display:flex; align-items:center; gap:0.5rem; flex-shrink:0; }
.radio-volume-wrap svg { width:14px; height:14px; fill:#6b6355; }
.radio-volume { width:70px; -webkit-appearance:none; appearance:none; height:3px; background:#2a2010; border-radius:2px; outline:none; cursor:pointer; }
.radio-volume::-webkit-slider-thumb { -webkit-appearance:none; width:10px; height:10px; border-radius:50%; background:#c9a84c; cursor:pointer; }
.radio-footer { background:#080604; border-top:1px solid #1a1408; padding:0.6rem 1.5rem; display:flex; align-items:center; justify-content:space-between; }
.radio-broadcast { font-family:var(--font-heading); font-size:0.6rem; letter-spacing:0.2em; color:#3a2e1e; text-transform:uppercase; }
.radio-broadcast.live { color:#c9a84c; animation:pulse-text 2s infinite; }
@keyframes pulse-text { 0%,100%{opacity:1} 50%{opacity:0.4} }
.radio-download { font-family:var(--font-heading); font-size:0.65rem; color:#6b6355; text-decoration:none; letter-spacing:0.1em; border:1px solid #2a2010; padding:0.25rem 0.75rem; border-radius:3px; transition:color 0.2s,border-color 0.2s; }
.radio-download:hover { color:#c9a84c; border-color:#c9a84c; }
.episode-meta-box { background:#111008; border:1px solid #2a2010; border-left:3px solid #c9a84c; border-radius:6px; padding:1.25rem 1.5rem; margin:2rem 0; display:grid; grid-template-columns:1fr 1fr; gap:0.75rem 2rem; }
@media (max-width:600px) { .episode-meta-box { grid-template-columns:1fr; } }
.episode-meta-item { display:flex; flex-direction:column; gap:0.2rem; }
.episode-meta-label { font-family:var(--font-heading); font-size:0.6rem; letter-spacing:0.2em; color:#6b6355; text-transform:uppercase; }
.episode-meta-value { font-family:var(--font-body); color:#e8e0d0; font-size:0.95rem; }
.era-box { background:linear-gradient(135deg,#0d0b08 0%,#100e09 100%); border:1px solid #2a2010; border-radius:8px; padding:1.75rem; margin:2.5rem 0; position:relative; overflow:hidden; }
.era-box-label { font-family:var(--font-heading); font-size:0.6rem; letter-spacing:0.25em; color:#c9a84c; text-transform:uppercase; margin-bottom:1rem; }
.era-box h3 { font-family:var(--font-heading); color:#e8e0d0; font-size:1.1rem; margin-bottom:0.75rem; }
.era-box p { font-family:var(--font-body); color:#a89e8c; font-size:1rem; line-height:1.75; margin-bottom:0.75rem; }
.era-box p:last-child { margin-bottom:0; }
.breadcrumb { padding:1rem 0 0; font-family:var(--font-heading); font-size:0.7rem; letter-spacing:0.1em; color:#6b6355; }
.breadcrumb a { color:#6b6355; text-decoration:none; }
.breadcrumb a:hover { color:#c9a84c; }
.breadcrumb span { margin:0 0.5rem; }
.episode-nav { display:flex; justify-content:space-between; gap:1rem; margin-top:3rem; padding-top:2rem; border-top:1px solid #2a2010; }
.episode-nav a { font-family:var(--font-heading); font-size:0.75rem; letter-spacing:0.1em; color:#6b6355; text-decoration:none; border:1px solid #2a2010; padding:0.6rem 1rem; border-radius:4px; transition:color 0.2s,border-color 0.2s; }
.episode-nav a:hover { color:#c9a84c; border-color:#c9a84c; }
"""
    css_dir = SITE_ROOT / "css"
    css_dir.mkdir(exist_ok=True)
    (css_dir / "radio-player.css").write_text(css)
    print("✓ radio-player.css written")

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    print("Ghost of Radio — Bulk Episode Generator")
    print(f"Model: {OLLAMA_MODEL} (local, zero API cost)")
    print()
    
    # Write shared CSS
    generate_radio_player_css()
    
    # Which shows to process (pass show IDs as args, or process all)
    target_shows = sys.argv[1:] if len(sys.argv) > 1 else [s["id"] for s in SHOWS]
    
    for show in SHOWS:
        if show["id"] in target_shows:
            process_show(show, start_from=START_FROM)
    
    print("\n✅ All done! Push to GitHub Pages when ready.")
    print("Run: cd /Users/mac1/Projects/ghostofradio && git push origin main")
