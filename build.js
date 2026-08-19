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
 * Ten skrypt nie ma żadnych zależności zewnętrznych (czysty Node.js),
 * więc Netlify nie musi nic instalować, żeby go uruchomić.
 */
const fs = require("fs");
const path = require("path");

const ROOT = __dirname;
const ARTICLES_DIR = path.join(ROOT, "artykuly");
const OUTPUT_FILE = path.join(ROOT, "data", "articles.json");

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

function main() {
  if (!fs.existsSync(ARTICLES_DIR)) {
    console.warn("Brak folderu artykuly/ — nic do zrobienia.");
    fs.mkdirSync(path.dirname(OUTPUT_FILE), { recursive: true });
    fs.writeFileSync(OUTPUT_FILE, "[]\n", "utf-8");
    return;
  }

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

  articles.sort((a, b) => new Date(b.date) - new Date(a.date));

  fs.mkdirSync(path.dirname(OUTPUT_FILE), { recursive: true });
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(articles, null, 2) + "\n", "utf-8");

  console.log(`Zapisano ${articles.length} artykuł(ów) do ${path.relative(ROOT, OUTPUT_FILE)}.`);
}

main();
