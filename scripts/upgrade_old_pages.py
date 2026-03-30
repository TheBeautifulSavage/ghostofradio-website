#!/usr/bin/env python3
"""
Upgrade old-format episode pages (no audio player) to new radio player format.
Pulls archive.org URL for each episode.
"""
import re, json, urllib.request, urllib.parse, subprocess
from pathlib import Path
from datetime import datetime

SITE_ROOT = Path("/Users/mac1/Projects/ghostofradio")

# Shadow archive.org identifier
SHADOW_ID = "the-shadow-radio-show-1937-1954-old-time-radio-all-available-episodes"

def get_archive_map(identifier):
    try:
        url = f"https://archive.org/metadata/{identifier}"
        req = urllib.request.Request(url, headers={"User-Agent": "GhostOfRadio/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        result = {}
        for f in data.get("files", []):
            name = f.get("name", "")
            if name.lower().endswith(".mp3"):
                enc = urllib.parse.quote(name)
                url_str = f"https://archive.org/download/{identifier}/{enc}"
                stem = Path(name).stem.lower()
                result[slugify(stem)] = url_str
        return result
    except Exception as e:
        print(f"  Error: {e}")
        return {}

def slugify(text):
    text = str(text).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

def find_url(page_slug, archive_map):
    # Direct match
    if page_slug in archive_map:
        return archive_map[page_slug]
    # Fuzzy: find best word overlap
    slug_words = set(page_slug.split('-'))
    best, best_score = None, 0
    for key, url in archive_map.items():
        common = len(slug_words & set(key.split('-')))
        if common > best_score and common >= max(1, len(slug_words) * 0.5):
            best_score = common
            best = url
    return best

RADIO_PLAYER_TEMPLATE = '''
        <!-- RADIO PLAYER -->
        <div class="radio-player" id="radioPlayer">
          <div class="radio-top">
            <div class="radio-grille"></div>
            <div class="radio-info">
              <div class="radio-show-name">{show_name}</div>
              <div class="radio-episode-title">{episode_title}</div>
              <div class="radio-meta">{date_str}</div>
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
            <a class="radio-download" href="{mp3_url}" download>⬇ Download MP3</a>
          </div>
          <audio id="episodeAudio" preload="none">
            <source src="{mp3_url}" type="audio/mpeg">
          </audio>
        </div>
        <script>
          (function(){{
            var heights=[{bars}];
            var wf=document.getElementById('waveform');
            heights.forEach(function(h){{var b=document.createElement('span');b.style.height=h+'px';wf.appendChild(b);}});
            var audio=document.getElementById('episodeAudio'),pb2=document.getElementById('playBtn'),pb=document.getElementById('progressBar'),vb=document.getElementById('volumeBar'),ct=document.getElementById('currentTime'),dur=document.getElementById('duration'),bl=document.getElementById('broadcastLabel'),brs=wf.querySelectorAll('span');
            function fmt(s){{if(isNaN(s))return'--:--';return Math.floor(s/60)+':'+(Math.floor(s%60)<10?'0':'')+Math.floor(s%60);}}
            var af;function anim(){{var p=audio.duration?audio.currentTime/audio.duration:0;brs.forEach(function(b,i){{b.classList.toggle('active',i<Math.floor(p*brs.length));}});af=requestAnimationFrame(anim);}}
            pb2.addEventListener('click',function(){{if(audio.paused){{audio.play();pb2.classList.add('playing');bl.classList.add('live');bl.textContent='● ON AIR — GHOST OF RADIO';anim();}}else{{audio.pause();pb2.classList.remove('playing');bl.classList.remove('live');bl.textContent='· GHOST OF RADIO ·';cancelAnimationFrame(af);}}}});
            audio.addEventListener('timeupdate',function(){{if(audio.duration)pb.value=(audio.currentTime/audio.duration)*100;ct.textContent=fmt(audio.currentTime);}});
            audio.addEventListener('loadedmetadata',function(){{dur.textContent=fmt(audio.duration);}});
            audio.addEventListener('ended',function(){{pb2.classList.remove('playing');bl.classList.remove('live');bl.textContent='· GHOST OF RADIO ·';cancelAnimationFrame(af);pb.value=0;ct.textContent='0:00';}});
            pb.addEventListener('input',function(){{if(audio.duration)audio.currentTime=(pb.value/100)*audio.duration;}});
            vb.addEventListener('input',function(){{audio.volume=vb.value;}});
            audio.volume=0.85;
          }})();
        </script>
'''

PLAYER_CSS = '''  <link rel="stylesheet" href="/css/radio-player.css">'''

def upgrade_page(html_path, archive_map, show_name="The Shadow"):
    content = html_path.read_text(encoding="utf-8")
    
    # Already upgraded?
    if "episodeAudio" in content:
        return False
    
    slug = html_path.stem
    mp3_url = find_url(slug, archive_map)
    if not mp3_url:
        print(f"  ⚠️  No audio found for: {slug}")
        mp3_url = f"https://archive.org/search.php?query={urllib.parse.quote(slug.replace('-',' '))}&mediatype=audio"
    
    # Extract episode title and date from page
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
    episode_title = title_match.group(1).strip() if title_match else slug.replace('-', ' ').title()
    
    date_match = re.search(r'Originally aired ([^<]+)<', content)
    date_str = date_match.group(1).strip() if date_match else ""
    
    import random
    random.seed(hash(slug))
    bars = ",".join(str(random.randint(4, 32)) for _ in range(56))
    
    player_html = RADIO_PLAYER_TEMPLATE.format(
        show_name=show_name,
        episode_title=episode_title,
        date_str=date_str,
        mp3_url=mp3_url,
        bars=bars
    )
    
    # Add radio-player.css link if missing
    if "radio-player.css" not in content:
        content = content.replace('<link rel="stylesheet" href="/css/style.css">', 
                                  '<link rel="stylesheet" href="/css/style.css">\n' + PLAYER_CSS)
    
    # Insert player after the <time> tag or after first <p> in article
    insert_after = re.search(r'(<time[^>]*>[^<]*</time>)', content)
    if insert_after:
        content = content.replace(insert_after.group(0), insert_after.group(0) + "\n" + player_html)
    else:
        # Insert after first <p> in article
        first_p = re.search(r'(<p><em>The radio crackles[^<]*</em></p>)', content)
        if first_p:
            content = content.replace(first_p.group(0), first_p.group(0) + "\n" + player_html)
    
    html_path.write_text(content, encoding="utf-8")
    print(f"  ✓ {slug}")
    return True

def main():
    print("Upgrading old-format pages to radio player...")
    
    # Load archive maps
    print("Loading archive.org metadata...")
    shadow_map = get_archive_map(SHADOW_ID)
    print(f"  Shadow: {len(shadow_map)} files")
    
    upgraded = 0
    
    # Process all shows
    show_map = {
        "shadow": (shadow_map, "The Shadow"),
    }
    
    for show_slug, (archive_map, show_name) in show_map.items():
        blog_dir = SITE_ROOT / "blog" / show_slug
        old_pages = [f for f in blog_dir.glob("*.html") 
                     if f.name != "index.html" and "episodeAudio" not in f.read_text()]
        print(f"\n{show_name}: {len(old_pages)} old pages to upgrade")
        for page in old_pages:
            if upgrade_page(page, archive_map, show_name):
                upgraded += 1
    
    print(f"\n✅ Upgraded {upgraded} pages")
    
    # Commit and push
    subprocess.run(["git", "add", "-A"], cwd=SITE_ROOT, capture_output=True)
    r = subprocess.run(["git", "commit", "-m", f"fix: upgrade {upgraded} old pages to radio player with archive.org audio"],
                      cwd=SITE_ROOT, capture_output=True, text=True)
    print(r.stdout[:100] if r.returncode == 0 else "Nothing new")
    subprocess.run(["git", "push", "origin", "main"], cwd=SITE_ROOT, timeout=30)
    print("Pushed!")

if __name__ == "__main__":
    main()
