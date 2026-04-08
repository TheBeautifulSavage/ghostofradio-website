# Ghost of Radio — Website Project State
_Last updated: 2026-04-08_

## Repo
- GitHub: https://github.com/TheBeautifulSavage/ghostofradio-website
- Local: `/Users/mac1/Projects/ghostofradio/`
- Deployed: GitHub Pages, ghostofradio.com (HTTPS enforced)

## Page Count
- ~21,560 HTML pages live (as of 2026-04-08)
- Episode pages + show index pages + blog + landing pages

## Site Generator
- Script: `scripts/generate_claude.py`
- Requires: `ANTHROPIC_KEY`, `CF_TOKEN`, `CF_ACCOUNT` env vars
- ANTHROPIC_KEY: from `/Users/mac1/.openclaw/agents/main/agent/auth-profiles.json`
- CF_TOKEN: `cfut_F7Gk8H3OrM2QQ34UoqpRfo3F3mHuNd222p2IMdm73b91416a`
- CF_ACCOUNT: `dae784fdc17957e814046c3637ee10eb`
- Cron: restarts every 2h via `check_writers.sh`

## HTML Structure
- JD episodes: `johnny-dollar/ytjd-YYYY-MM-DD-NNN-slug.html`
- Title tag format: `EPISODE TITLE | Ghost of Radio`

## SEO Completed (2026-04-02)
- AudioObject + og:image: 24,606 episode pages
- Twitter Cards: 24,371 episode pages
- RadioSeries schema: 111 show index pages
- Article schema: 43 blog pages
- Hreflang EN↔ES: 48 show index pages
- Internal links: 17,870 pages
- 20 per-show RSS feeds at /rss/SLUG.xml
- 13 new landing pages
- 5 Web Stories in /stories/

## R2 CDN (audio)
- Public: `https://pub-43a2a91d87c649239fa207174290a900.r2.dev/`
- CORS set via CF API — GET/HEAD from * — DO NOT REMOVE or audio breaks in browsers
