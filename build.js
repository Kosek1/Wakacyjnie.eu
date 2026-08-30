#!/usr/bin/env node
/**
 * Uruchamiany automatycznie przez Netlify przy każdym wdrożeniu (patrz
 * netlify.toml -> build.command). Przegląda wszystkie pliki w artykuly/,
 * wyciąga z każdego z nich blok <script type="application/json" id="article-meta">
 * (wstawiany przez generate_article.py) i na tej podstawie buduje
 * data/articles.json — plik, który strona główna pobiera i renderuje jako
 * karty w sekcji Newsy.
 *
 * Dzięki temu dodanie nowego artykułu wymaga wgrania do repozytorium TYLKO
 * jednego pliku (nowej strony w artykuly/) — nie trzeba już ręcznie
 * edytować ani uploadować data/articles.json.
 *
 * Ten sam przebieg buduje też sitemap.xml (strony statyczne + wszystkie
 * artykuły + wszystkie poradniki, jeśli katalog poradniki/ istnieje) —
 * z tego samego powodu: żeby nowa strona/artykuł/poradnik trafiał do
 * mapy strony automatycznie, bez ręcznej edycji.
 *
 * Ten skrypt nie ma żadnych zależności zewnętrznych (czysty Node.js),
 * więc Netlify nie musi nic instalować, żeby go uruchomić.
 */
const fs = require("fs");
const path = require("path");

const ROOT = __dirname;
const ARTICLES_DIR = path.join(ROOT, "artykuly");
const GUIDES_DIR = path.join(ROOT, "poradniki");
const OUTPUT_FILE = path.join(ROOT, "data", "articles.json");
const SITEMAP_FILE = path.join(ROOT, "sitemap.xml");
const SITE_URL = "https://ogarnijwakacje.pl";

// Statyczne podstrony, które nie mają własnych metadanych do wyciągnięcia —
// dopisz tu nową pozycję, jeśli w repo pojawi się kolejna samodzielna strona.
const STATIC_PAGES = [
  { path: "", priority: "1.0", changefreq: "daily" }, // strona główna
  { path: "newsy.html", priority: "0.8", changefreq: "daily" },
  { path: "miejsca.html", priority: "0.7", changefreq: "weekly" },
  { path: "ciekawostki.html", priority: "0.6", changefreq: "weekly" },
  { path: "poradniki.html", priority: "0.7", changefreq: "weekly" },
  { path: "poznaj-aplikacje.html", priority: "0.6", changefreq: "monthly" },
  { path: "polityka-prywatnosci.html", priority: "0.2", changefreq: "yearly" },
  { path: "regulamin.html", priority: "0.2", changefreq: "yearly" },
];

function readMeta(filePath) {
  const html = fs.readFileSync(filePath, "utf-8");
  const match = html.match(
    /<script type="application\/json" id="article-meta">([\s\S]*?)<\/script>/
  );
  if (!match) {
    console.warn(`  ! pominięto ${path.basename(filePath)} — brak bloku #article-meta`);
    return null;
  }
  try {
    return JSON.parse(match[1]);
  } catch (err) {
    console.warn(`  ! pominięto ${path.basename(filePath)} — niepoprawny JSON w #article-meta:`, err.message);
    return null;
  }
}

function collectArticles() {
  if (!fs.existsSync(ARTICLES_DIR)) return [];
  const files = fs
    .readdirSync(ARTICLES_DIR)
    .filter((f) => f.endsWith(".html"))
    .sort();
  console.log(`Znaleziono ${files.length} plik(ów) w artykuly/, wyciągam metadane...`);
  const articles = [];
  for (const file of files) {
    const meta = readMeta(path.join(ARTICLES_DIR, file));
    if (meta) articles.push(meta);
  }
  return articles;
}

function collectGuideUrls() {
  if (!fs.existsSync(GUIDES_DIR)) return [];
  return fs
    .readdirSync(GUIDES_DIR)
    .filter((f) => f.endsWith(".html"))
    .sort()
    .map((f) => `poradniki/${f}`);
}

function writeArticlesJson(articles) {
  articles.sort((a, b) => new Date(b.date) - new Date(a.date));
  fs.mkdirSync(path.dirname(OUTPUT_FILE), { recursive: true });
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(articles, null, 2) + "\n", "utf-8");
  console.log(`Zapisano ${articles.length} artykuł(ów) do ${path.relative(ROOT, OUTPUT_FILE)}.`);
}

function xmlEscape(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function writeSitemap(articles, guideUrls) {
  const today = new Date().toISOString().slice(0, 10);
  const urls = [];

  for (const page of STATIC_PAGES) {
    urls.push({
      loc: `${SITE_URL}/${page.path}`,
      lastmod: today,
      changefreq: page.changefreq,
      priority: page.priority,
    });
  }

  for (const a of articles) {
    urls.push({
      loc: `${SITE_URL}/${a.url}`,
      lastmod: a.date || today,
      changefreq: "monthly",
      priority: "0.6",
    });
  }

  for (const url of guideUrls) {
    urls.push({
      loc: `${SITE_URL}/${url}`,
      lastmod: today,
      changefreq: "monthly",
      priority: "0.6",
    });
  }

  const body = urls
    .map(
      (u) =>
        `  <url>\n    <loc>${xmlEscape(u.loc)}</loc>\n    <lastmod>${u.lastmod}</lastmod>\n    <changefreq>${u.changefreq}</changefreq>\n    <priority>${u.priority}</priority>\n  </url>`
    )
    .join("\n");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</urlset>\n`;

  fs.writeFileSync(SITEMAP_FILE, xml, "utf-8");
  console.log(`Zapisano sitemap.xml z ${urls.length} adresami URL.`);
}

function main() {
  const articles = collectArticles();
  const guideUrls = collectGuideUrls();
  writeArticlesJson(articles);
  writeSitemap(articles, guideUrls);
}

main();
