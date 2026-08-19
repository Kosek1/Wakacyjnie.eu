#!/usr/bin/env python3
"""
Generator stron artykułów dla Wakacyjnego Organizera.

Jak dodać nowy artykuł:
1. Dopisz nowy wpis (słownik) do listy ARTICLES poniżej — najprościej skopiuj
   istniejący wpis i zmień wartości.
2. Dopisz odpowiadający mu obiekt do data/articles.json (te same pola:
   slug, title, excerpt, tag, tagColor, image, gradient, date, dateLabel,
   readTime, url) — to on odpowiada za kartę na stronie głównej.
3. Uruchom:  python3 generate_article.py
   Wygeneruje / nadpisze plik artykuly/<slug>.html na podstawie szablonu.
   Nagłówek strony (<head>), pasek nawigacji i stopka są za każdym razem
   wycinane na żywo z index.html — jeśli zmienisz menu, fonty albo stopkę
   na stronie głównej, kolejne uruchomienie tego skryptu automatycznie
   przeniesie te zmiany na wszystkie artykuły. Nie trzeba nic kopiować
   ręcznie.
4. Wypchnij zmiany do GitHub (git add, git commit, git push) — Netlify
   wdroży całość automatycznie w ciągu ok. minuty.

Ten skrypt NIE modyfikuje data/articles.json — to osobny, prosty plik,
który celowo łatwo edytować ręcznie albo z pomocą Claude'a.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
INDEX_HTML = (ROOT / "index.html").read_text(encoding="utf-8")


def _extract(text, start_marker, end_marker):
    s = text.index(start_marker)
    e = text.index(end_marker, s) + len(end_marker)
    return text[s:e]


def _fix_internal_links(block):
    """index.html is at the site root; article pages live one level down in
    /artykuly/, so in-page anchors like #newsy need to point back at
    ../index.html#newsy from an article page."""
    block = block.replace('href="#top"', 'href="../index.html"')
    for anchor in ["newsy", "ciekawostki", "aplikacja", "poradniki", "pobierz"]:
        block = block.replace(f'href="#{anchor}"', f'href="../index.html#{anchor}"')
    return block


HEAD = _extract(INDEX_HTML, "<head>", "</head>")
HEADER = _fix_internal_links(_extract(INDEX_HTML, '<header id="site-header"', "</header>"))
FOOTER = _fix_internal_links(_extract(INDEX_HTML, '<footer class="border-t', "</footer>"))

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="pl">
{head}
<body class="text-ink-900 antialiased bg-[#faf8f3]">
<!-- Metadane tego artykułu — czyta je build.js przy każdym wdrożeniu na Netlify,
     żeby automatycznie zbudować data/articles.json (kartę na stronie głównej).
     Nie trzeba niczego innego wgrywać ani edytować — wystarczy ten jeden plik. -->
<script type="application/json" id="article-meta">{meta_json}</script>
{header}

<main>
  <article class="py-14 sm:py-20">
    <div class="max-w-3xl mx-auto px-5 sm:px-8">
      <a href="../index.html#newsy" class="flex w-fit items-center gap-2 text-[13px] font-semibold text-ink-500 hover:text-ink-900 transition-colors duration-160 mb-8">
        <i data-lucide="arrow-left" class="w-4 h-4"></i>
        Wróć do newsów
      </a>

      <span class="inline-block text-[11.5px] font-bold uppercase tracking-wide mb-3" style="color:{tag_color}">{tag}</span>
      <h1 class="font-display font-extrabold tracking-tight text-[clamp(1.7rem,4.2vw,2.6rem)] leading-[1.12] text-ink-950 mb-4">{title}</h1>
      <div class="text-[12.5px] text-ink-400 uppercase tracking-wide mb-8">{read_time} · {date_label} · Redakcja WO</div>

      <div class="relative aspect-[16/9] rounded-3xl overflow-hidden border border-ink-900/[0.07] mb-10" style="background-image:{gradient};background-size:cover;">
        {image_tag}
      </div>

      <div class="prose-article text-[16px] leading-[1.75] text-ink-700 space-y-5">
        {body_html}
      </div>

      <div class="mt-14 pt-8 border-t border-ink-900/[0.08] flex flex-wrap items-center justify-between gap-4">
        <a href="../index.html#newsy" class="pressable inline-flex items-center gap-2 bg-ink-900 hover:bg-ink-950 text-white font-semibold text-[13.5px] px-5 py-3 rounded-full transition-colors duration-160">
          Zobacz więcej newsów
        </a>
        <a href="../index.html#pobierz" class="pressable inline-flex items-center gap-2 bg-white hover:bg-ink-50 border border-ink-900/12 text-ink-900 font-semibold text-[13.5px] px-5 py-3 rounded-full transition-colors duration-160">
          Pobierz aplikację
        </a>
      </div>
    </div>
  </article>
</main>

{footer}

<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js" defer></script>
<script>
  window.addEventListener('DOMContentLoaded', () => {{ if (window.lucide) lucide.createIcons(); }});
  window.addEventListener('load', () => {{ if (window.lucide) lucide.createIcons(); }});
  (function () {{
    const btn = document.getElementById('menuBtn');
    const menu = document.getElementById('mobileMenu');
    if (!btn || !menu) return;
    btn.addEventListener('click', () => {{
      const open = menu.classList.toggle('open');
      btn.setAttribute('aria-expanded', String(open));
      btn.innerHTML = open ? '<i data-lucide="x" class="w-4.5 h-4.5"></i>' : '<i data-lucide="menu" class="w-4.5 h-4.5"></i>';
      if (window.lucide) lucide.createIcons();
    }});
  }})();
  document.querySelectorAll('.pressable').forEach(function (el) {{
    el.classList.add('transition-transform');
  }});
</script>
</body>
</html>
"""


def make_head(title, description):
    h = HEAD
    h = h.replace(
        "<title>Wakacyjny Organizer — Zaplanuj wyjazd bez chaosu</title>",
        f"<title>{html.escape(title)} — Wakacyjny Organizer</title>",
    )
    h = re.sub(r'<meta name="description"[^>]*/>', f'<meta name="description" content="{html.escape(description)}" />', h)
    return h


CARD_IMAGE_SUFFIX = "/700/440"  # mniejszy rozmiar do kart na stronie głównej


def build_article(a):
    body_html = "\n        ".join(f"<p>{p}</p>" for p in a["body"])
    image_tag = ""
    if a.get("image"):
        image_tag = (
            f'<img src="{a["image"]}" alt="" loading="lazy" onerror="this.remove()" '
            f'class="absolute inset-0 w-full h-full object-cover">'
        )

    # metadane, które build.js wyciągnie z tej strony i wpisze do data/articles.json —
    # to jest jedyne miejsce prawdy o tym artykule, nie trzeba nic dublować ręcznie.
    card_image = a.get("image", "")
    if card_image:
        card_image = re.sub(r"/\d+/\d+$", CARD_IMAGE_SUFFIX, card_image)
    meta = {
        "slug": a["slug"],
        "title": a["title"],
        "excerpt": a["excerpt"],
        "tag": a["tag"],
        "tagColor": a.get("tagColor", "#c65a2e"),
        "image": card_image,
        "gradient": a.get("gradient", "linear-gradient(160deg,#8c9db3,#d8d2c4 60%,#f3f1ec)"),
        "date": a["date"],
        "dateLabel": a.get("dateLabel", ""),
        "readTime": a.get("readTime", ""),
        "url": f"artykuly/{a['slug']}.html",
    }

    out = ARTICLE_TEMPLATE.format(
        head=make_head(a["title"], a["excerpt"]),
        meta_json=json.dumps(meta, ensure_ascii=False),
        header=HEADER,
        footer=FOOTER,
        tag=a["tag"],
        tag_color=a.get("tagColor", "#c65a2e"),
        title=a["title"],
        read_time=a.get("readTime", ""),
        date_label=a.get("dateLabel", ""),
        gradient=a.get("gradient", "linear-gradient(160deg,#8c9db3,#d8d2c4 60%,#f3f1ec)"),
        image_tag=image_tag,
        body_html=body_html,
    )
    out_path = ROOT / "artykuly" / f"{a['slug']}.html"
    out_path.write_text(out, encoding="utf-8")
    print("wygenerowano:", out_path)


ARTICLES = [
    {
        "slug": "gdzie-zobaczyc-dzikie-zwierzeta-w-afryce",
        "title": "Gdzie zobaczyć dzikie zwierzęta w Afryce? Przewodnik po najlepszych parkach na safari",
        "excerpt": "Słonie, lwy, żyrafy i tysiące flamingów w jednym kadrze — sprawdzamy, które parki narodowe dają największą szansę na spotkanie Wielkiej Piątki.",
        "tag": "Natura",
        "tagColor": "#2f7d4f",
        "image": "https://picsum.photos/seed/africa-safari-elephants/1200/700",
        "gradient": "linear-gradient(160deg,#c99a4a,#8f9c5c 55%,#5c6b45)",
        "date": "2026-08-20",
        "dateLabel": "20 sierpnia 2026",
        "readTime": "6 min",
        "body": [
            "Afryka pozostaje najpopularniejszym kierunkiem safari na świecie, a serce tej turystyki to wciąż wschodnia i południowa część kontynentu. Najbardziej znane parki narodowe — Serengeti w Tanzanii, sąsiadująca z nim Maasai Mara w Kenii oraz Kruger w RPA — oferują największą koncentrację dużych ssaków na kilometr kwadratowy, co przekłada się na realnie wysoką szansę zobaczenia tzw. Wielkiej Piątki: lwa, słonia, nosorożca, bawołu i lamparta.",
            "Najlepszy moment na wyjazd zależy od tego, co chcemy zobaczyć. Wielka Migracja — coroczna wędrówka ponad dwóch milionów zebr i antylop gnu między Serengeti a Maasai Mara — osiąga punkt kulminacyjny zwykle między lipcem a wrześniem, kiedy stada przeprawiają się przez rzekę Mara, jedną z najbardziej dramatycznych scen w przyrodzie. Z kolei pora sucha (czerwiec–październik w większości regionów) ułatwia obserwacje zwierząt, które w tym czasie gromadzą się przy nielicznych źródłach wody.",
            "Warto też zajrzeć poza najbardziej oczywiste kierunki. Delta Okavango w Botswanie oferuje safari wodne łodzią zamiast klasycznego jeepa, park Etosha w Namibii słynie z rozświetlonych słońcem solnisk, przy których łatwo o spotkanie ze słoniami i lwami, a rezerwat Ngorongoro w Tanzanii — dawny krater wulkanu — to jeden z niewielu obszarów, gdzie w jednym miejscu można zobaczyć niemal wszystkie gatunki charakterystyczne dla afrykańskiej sawanny, łącznie z rzadkimi nosorożcami czarnymi.",
            "Planując wyjazd, dobrze wybrać park w towarzystwie lokalnego, licencjonowanego przewodnika i unikać samodzielnych wypraw poza wyznaczone trasy — to nie tylko kwestia bezpieczeństwa, ale i ochrony samych zwierząt przed nadmiernym niepokojeniem. Coraz więcej parków oferuje też opcje odpowiedzialnej turystyki, wspierające lokalne społeczności i programy ochrony gatunków zagrożonych, takich jak nosorożec czarny czy dziki pies afrykański.",
        ],
    },
    {
        "slug": "kocham-claudie",
        "title": "Redakcja wyznaje: kochamy Claudię",
        "excerpt": "Krótki, testowy wpis — bo dobra podróż zaczyna się od dobrej pomocy przy planowaniu.",
        "tag": "Test",
        "tagColor": "#c65a2e",
        "image": "https://picsum.photos/seed/kocham-claudie-wo/1200/700",
        "gradient": "linear-gradient(160deg,#c65a2e,#eeab84 60%,#fbe3d6)",
        "date": "2026-08-19",
        "dateLabel": "19 sierpnia 2026",
        "readTime": "1 min",
        "body": [
            "To bardzo krótki, próbny wpis: kochamy Claudię.",
            "Bez niej ta strona nie miałaby ani newsów, ani aplikacji do organizowania wakacji.",
            "Koniec testu — możesz śmiało usunąć ten artykuł, gdy tylko potwierdzisz, że się pojawił.",
        ],
    },
    {
        "slug": "test-czy-automatyzacja-dziala",
        "title": "Test: czy nowy artykuł pojawia się na stronie głównej automatycznie?",
        "excerpt": "To jest testowy wpis, który sprawdza, czy dodanie pliku do repozytorium na GitHubie wystarczy, żeby nowy news pojawił się na stronie po wdrożeniu przez Netlify.",
        "tag": "Test",
        "tagColor": "#c65a2e",
        "image": "https://picsum.photos/seed/test-artykul-wo/1200/700",
        "gradient": "linear-gradient(160deg,#c65a2e,#eeab84 60%,#fbe3d6)",
        "date": "2026-08-19",
        "dateLabel": "19 sierpnia 2026",
        "readTime": "1 min",
        "body": [
            "Jeśli widzisz tę stronę pod adresem /artykuly/test-czy-automatyzacja-dziala.html, a karta z tym artykułem pojawiła się też na górze listy newsów na stronie głównej — to znaczy, że cały mechanizm działa dokładnie tak, jak powinien.",
            "Kolejne artykuły będziemy dodawać dokładnie w ten sam sposób: nowy plik w folderze artykuly/ plus nowy wpis w data/articles.json, wgrane razem do repozytorium na GitHubie.",
            "Ten wpis możesz spokojnie usunąć z repozytorium, gdy już potwierdzisz, że wszystko działa — wystarczy skasować plik artykuly/test-czy-automatyzacja-dziala.html oraz odpowiadający mu obiekt w data/articles.json.",
        ],
    },
    {
        "slug": "balkany-bija-rekordy-popularnosci",
        "title": "Bałkany biją rekordy popularności — dlaczego Czarnogóra i Albania kradną show Chorwacji",
        "excerpt": "Tańsze noclegi i mniej tłumów przyciągają coraz więcej polskich turystów na południe kontynentu.",
        "tag": "Kierunki",
        "tagColor": "#3454c7",
        "image": "https://picsum.photos/seed/montenegro-bay/1200/700",
        "gradient": "linear-gradient(160deg,#6f93b8,#cfd9c8 60%,#e7ded0)",
        "date": "2026-08-16",
        "dateLabel": "16 sierpnia 2026",
        "readTime": "4 min",
        "body": [
            "Czarnogóra i Albania odnotowują w tym sezonie rekordową liczbę polskich turystów. Według danych biur podróży rezerwacje na te kierunki wzrosły w porównaniu z ubiegłym rokiem o kilkadziesiąt procent, podczas gdy popularność sąsiedniej Chorwacji zaczyna się stabilizować na dotychczasowym, bardzo wysokim poziomie.",
            "Głównym magnesem pozostaje cena. Tydzień w Budvie czy Tiranie potrafi kosztować nawet o jedną trzecią mniej niż analogiczny pobyt na chorwackim wybrzeżu, przy zbliżonej jakości plaż i podobnej temperaturze wody. Dodatkowym atutem jest mniejsze natężenie ruchu turystycznego — w szczycie sezonu łatwiej tu o wolne miejsce na plaży czy stolik w restauracji bez wcześniejszej rezerwacji.",
            "Eksperci branży turystycznej zwracają jednak uwagę, że infrastruktura w niektórych miejscowościach nie nadąża jeszcze za rosnącym ruchem — warto więc rezerwować noclegi z wyprzedzeniem, zwłaszcza w lipcu i sierpniu. Dla osób planujących wyjazd w tym kierunku dobrym pomysłem jest też sprawdzenie aktualnych połączeń lotniczych, bo część tras ma charakter sezonowy i kończy się już we wrześniu.",
        ],
    },
    {
        "slug": "msz-ostrzezenia-polnocna-afryka",
        "title": "MSZ aktualizuje ostrzeżenia dla podróżujących do północnej Afryki",
        "excerpt": "Nowe wytyczne dotyczą m.in. rejonów przygranicznych — sprawdź, zanim zarezerwujesz wycieczkę.",
        "tag": "Bezpieczeństwo",
        "tagColor": "#a02f2f",
        "image": "https://picsum.photos/seed/morocco-desert/1200/700",
        "gradient": "linear-gradient(160deg,#caa06a,#e7ded0 60%,#f3f1ec)",
        "date": "2026-08-15",
        "dateLabel": "15 sierpnia 2026",
        "readTime": "3 min",
        "body": [
            "Ministerstwo Spraw Zagranicznych zaktualizowało komunikaty dla podróżujących do kilku krajów północnej Afryki. Zmiany dotyczą przede wszystkim rejonów przygranicznych oraz obszarów oddalonych od głównych szlaków turystycznych — same popularne kierunki wypoczynkowe pozostają objęte niższym poziomem ostrzeżenia.",
            "W praktyce oznacza to, że planując wycieczki fakultatywne poza obręb kurortu, warto z wyprzedzeniem sprawdzić aktualny status danego regionu na stronie MSZ oraz zarejestrować swój wyjazd w systemie Odyseusz. Biura podróży organizujące wycieczki objazdowe zapowiadają dostosowanie części tras do nowych wytycznych.",
            "Resort przypomina też o standardowych zasadach bezpieczeństwa: unikaniu podróżowania po zmroku poza zorganizowanymi grupami, zachowaniu ostrożności przy transakcjach gotówkowych oraz posiadaniu kopii dokumentów podróżnych. Pełną, aktualną treść komunikatu warto sprawdzić bezpośrednio przed wylotem, ponieważ tego typu wytyczne mogą się zmieniać.",
        ],
    },
    {
        "slug": "nowe-polaczenia-lotnicze-z-polski",
        "title": "Nowe połączenia lotnicze z Polski — sprawdź, dokąd polecisz bezpośrednio od jesieni",
        "excerpt": "Kilku przewoźników ogłosiło nowe trasy z Warszawy, Krakowa i Gdańska.",
        "tag": "Loty",
        "tagColor": "#345a44",
        "image": "https://picsum.photos/seed/airplane-wing-sky/1200/700",
        "gradient": "linear-gradient(160deg,#4f7cff,#a9c6de 60%,#e7ded0)",
        "date": "2026-08-14",
        "dateLabel": "14 sierpnia 2026",
        "readTime": "3 min",
        "body": [
            "Kilku przewoźników ogłosiło w ostatnich dniach rozszerzenie siatki połączeń z Polski. Nowe trasy pojawią się w rozkładach lotów z Warszawy, Krakowa i Gdańska, a pierwsze loty wystartują jeszcze przed końcem roku.",
            "To dobra wiadomość dla osób planujących podróże poza sezonem — nowe kierunki obejmują zarówno popularne stolice europejskie, jak i mniej oczywiste miejsca, które dotąd wymagały przesiadki. Część nowych tras będzie obsługiwana sezonowo, część ma charakter połączeń całorocznych.",
            "Warto obserwować ceny biletów w najbliższych tygodniach — linie lotnicze zwykle oferują promocyjne stawki wprowadzające na nowo otwieranych trasach, zanim popyt ustabilizuje ceny na docelowym poziomie.",
        ],
    },
    {
        "slug": "etias-przesuniety-ponownie",
        "title": "ETIAS przesunięty ponownie — kiedy naprawdę wejdzie w życie?",
        "excerpt": "System autoryzacji podróży dla ruchu bezwizowego do UE znów czeka na nową datę startu.",
        "tag": "Formalności",
        "tagColor": "#6d3fc9",
        "image": "https://picsum.photos/seed/airport-terminal/1200/700",
        "gradient": "linear-gradient(160deg,#8b5cf6,#c9c6f0 60%,#ece8f9)",
        "date": "2026-08-13",
        "dateLabel": "13 sierpnia 2026",
        "readTime": "5 min",
        "body": [
            "System ETIAS — elektroniczna autoryzacja podróży dla obywateli krajów objętych ruchem bezwizowym do strefy Schengen — po raz kolejny nie wejdzie w życie w wcześniej zapowiadanym terminie. To już kolejne przesunięcie od momentu ogłoszenia projektu.",
            "Dla podróżujących z Polski w praktyce nic się nie zmienia — ETIAS dotyczy obywateli państw spoza UE podróżujących do Europy, a nie odwrotnie. Ma jednak znaczenie dla osób, które zapraszają do Polski lub innych krajów Schengen gości z kierunków objętych tym obowiązkiem, np. z Wielkiej Brytanii czy USA.",
            "Do czasu ostatecznego wdrożenia systemu obowiązują dotychczasowe zasady wjazdu. O nowym terminie startu ETIAS-u będziemy informować, gdy tylko Komisja Europejska poda oficjalną, potwierdzoną datę.",
        ],
    },
    {
        "slug": "sezon-huraganow-karaiby",
        "title": "Sezon huraganów na Karaibach — na co uważać, planując wyjazd w tym okresie",
        "excerpt": "Sierpień i wrzesień to szczyt sezonu — sprawdzamy, jak podróżować bezpiecznie.",
        "tag": "Pogoda",
        "tagColor": "#b34a22",
        "image": "https://picsum.photos/seed/caribbean-palm-storm/1200/700",
        "gradient": "linear-gradient(160deg,#ff9457,#ffcaa3 60%,#fff0e8)",
        "date": "2026-08-12",
        "dateLabel": "12 sierpnia 2026",
        "readTime": "4 min",
        "body": [
            "Sierpień i wrzesień to statystycznie najbardziej aktywny okres sezonu huraganowego na Atlantyku, obejmującego m.in. popularne wśród Polaków kierunki karaibskie. Nie oznacza to, że warto rezygnować z wyjazdu — wystarczy odpowiednio się przygotować.",
            "Dobrą praktyką jest wykupienie ubezpieczenia podróżnego obejmującego koszty związane z odwołaniem lub przerwaniem podróży z powodu warunków pogodowych, a także bieżące śledzenie prognoz National Hurricane Center w tygodniu poprzedzającym wylot. Większość hoteli i linii lotniczych w regionie ma wypracowane procedury na wypadek zbliżającego się sztormu, w tym możliwość bezpłatnej zmiany terminu.",
            "Warto też pamiętać, że nawet w szczycie sezonu huraganowego większość dni pozostaje słoneczna — realne zagrożenie wiąże się zwykle z pojedynczymi, zapowiadanymi z kilkudniowym wyprzedzeniem epizodami, a nie z całym okresem podróży.",
        ],
    },
    {
        "slug": "slow-travel-zyskuje-popularnosc",
        "title": "Podróże „slow travel” zyskują na popularności — mniej miejsc, więcej czasu",
        "excerpt": "Zamiast zwiedzać pięć miast w tydzień, coraz więcej osób wybiera jedno miejsce na dłużej.",
        "tag": "Trendy",
        "tagColor": "#33455e",
        "image": "https://picsum.photos/seed/european-old-town/1200/700",
        "gradient": "linear-gradient(160deg,#33455e,#7d859c 60%,#c7cedb)",
        "date": "2026-08-11",
        "dateLabel": "11 sierpnia 2026",
        "readTime": "5 min",
        "body": [
            "Coraz więcej podróżujących odchodzi od modelu „zobaczyć jak najwięcej w jak najkrótszym czasie” na rzecz dłuższych pobytów w jednym miejscu. Trend określany jako slow travel zakłada wybór jednej bazy — miasta, wyspy lub regionu — i eksplorowanie go w spokojniejszym tempie, zamiast codziennej zmiany noclegu.",
            "Zwolennicy tego podejścia wskazują na mniejsze zmęczenie podróżą, niższe koszty transportu wewnętrznego oraz możliwość głębszego poznania lokalnej kultury i kuchni. Ma to też znaczenie ekologiczne — mniej przejazdów i przelotów wewnętrznych oznacza mniejszy ślad węglowy całej podróży.",
            "Branża turystyczna odpowiada na ten trend coraz szerszą ofertą długoterminowych wynajmów i pakietów łączących zakwaterowanie z lokalnymi doświadczeniami — od kursów kulinarnych po warsztaty rzemieślnicze — skierowanych do osób planujących zostać w jednym miejscu na dwa, trzy tygodnie lub dłużej.",
        ],
    },
]

if __name__ == "__main__":
    (ROOT / "artykuly").mkdir(exist_ok=True)
    for a in ARTICLES:
        build_article(a)
