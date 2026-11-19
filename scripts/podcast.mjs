// Pulls every LEDG Podcast episode from Substack into podcast.json (run hourly by GitHub Actions).
// Substack blocks browsers on other sites from reading its feed, so the app reads this saved copy instead.
// Uses Substack's archive (all episodes); falls back to the RSS feed (latest ~10) if the archive is unavailable.
import { readFileSync, writeFileSync, existsSync, rmSync } from "node:fs";
const BASE = "https://theledgpodcast.substack.com";
const PODCAST_FEED = "https://api.substack.com/feed/podcast/10631863.rss"; // the feed Apple/Spotify-style apps read
const UA = { "user-agent": "LEDG-app podcast sync (github.com/shakyjacks/ledg)" };

async function fromArchive() {
  const out = [];
  for (let offset = 0; offset < 2000; offset += 50) {
    const r = await fetch(`${BASE}/api/v1/archive?sort=new&offset=${offset}&limit=50`, { headers: UA });
    if (!r.ok) throw new Error("archive HTTP " + r.status + " " + (await r.text()).slice(0, 120).replace(/\s+/g, " "));
    const j = await r.json(); const page = Array.isArray(j) ? j : (j.posts || []);
    if (!Array.isArray(page) || !page.length) break;
    for (const p of page) {
      if (!p.podcast_url) continue;
      out.push({
        title: p.title,
        date: p.post_date,
        audio: p.podcast_url,
        duration: p.podcast_duration ? Math.round(p.podcast_duration) : null,
        desc: p.subtitle || p.description || "",
        link: p.canonical_url || `${BASE}/p/${p.slug}`,
      });
    }
    if (page.length < 50) break;
  }
  return out;
}

async function fromRss(url = `${BASE}/feed`) {
  const rr = await fetch(url, { headers: UA });
  const xml = await rr.text();
  if (!rr.ok) throw new Error("rss HTTP " + rr.status + " " + xml.slice(0, 120).replace(/\s+/g, " "));
  const tag = (s, t) => { const m = s.match(new RegExp(`<${t}[^>]*>([\\s\\S]*?)</${t}>`)); return m ? m[1].replace(/^<!\[CDATA\[|\]\]>$/g, "").trim() : ""; };
  return [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)].map(([, it]) => ({
    title: tag(it, "title"),
    date: new Date(tag(it, "pubDate")).toISOString(),
    audio: (it.match(/<enclosure[^>]*url="([^"]+)"/) || [])[1],
    duration: (d => !d ? null : d.includes(":") ? d.split(":").reduce((a, x) => a * 60 + +x, 0) : Math.round(+d) || null)(tag(it, "itunes:duration")),
    desc: tag(it, "description").replace(/<[^>]+>/g, "").replace(/\s*This is a public episode\.[\s\S]*$/, "").trim().slice(0, 300),
    link: tag(it, "link"),
  })).filter(e => e.audio);
}

const status = { at: new Date().toISOString(), podcastFeed: null, archive: null, rss: null };
let episodes = [];
try { episodes = await fromRss(PODCAST_FEED); status.podcastFeed = `ok ${episodes.length}`; } catch (e) { status.podcastFeed = String(e.message || e); }
if (!episodes.length) try { episodes = await fromArchive(); status.archive = `ok ${episodes.length}`; if (!episodes.length) throw new Error("empty archive"); }
catch (e) {
  status.archive = String(e.message || e);
  console.warn("archive failed, using RSS:", status.archive);
  try { episodes = await fromRss(); status.rss = `ok ${episodes.length}`; } catch (e2) { status.rss = String(e2.message || e2); }
}
if (!episodes.length) {
  console.error("no episodes found; leaving podcast.json unchanged", status);
  writeFileSync("podcast-status.json", JSON.stringify(status, null, 1));
  process.exit(0);
}
rmSync("podcast-status.json", { force: true }); // clear an old failure note
episodes.sort((a, b) => new Date(b.date) - new Date(a.date));

const next = { show: { title: "The LEDG Podcast", link: BASE }, episodes };
const prev = existsSync("podcast.json") ? JSON.parse(readFileSync("podcast.json", "utf8")) : null;
if (prev && JSON.stringify({ show: prev.show, episodes: prev.episodes }) === JSON.stringify(next)) {
  console.log(`no change (${episodes.length} episodes)`);
} else {
  writeFileSync("podcast.json", JSON.stringify({ ...next, updated: new Date().toISOString() }, null, 1));
  console.log(`saved ${episodes.length} episodes`);
}
