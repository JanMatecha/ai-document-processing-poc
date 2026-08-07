# PoC: porovnání Docling a MarkItDown

Projekt prakticky porovnává lokální převod technických dokumentů do Markdownu pomocí [Microsoft MarkItDown](https://github.com/microsoft/markitdown) a [Docling](https://docling-project.github.io/docling/). Dokumenty se neposílají do cloudové AI ani do externí služby pro zpracování dokumentů.

PoC má dvě navazující fáze:

- **Fáze 1** zachovává původní minimální test nad syntetickým `input/test.pdf`. Ověřené výsledky a ruční zhodnocení jsou v [`COMPARISON.md`](COMPARISON.md).
- **Fáze 2** přidává reprodukovatelný benchmark veřejných reálných dokumentů ve formátech PDF, DOCX, PPTX a XLSX, včetně srovnání stejného obsahu v různých zdrojových formátech.

## Požadavky a instalace

- 64bit Python 3.10 nebo novější,
- internet pro instalaci balíčků a jednorázové stažení veřejného datasetu,
- dostatek místa pro závislosti Doclingu a jeho lokální modely.

PowerShell ve Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Pokud firemní Execution Policy blokuje `Activate.ps1`, není nutné ji měnit. Použijte interpreter virtuálního prostředí přímo:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\markitdown_test.py input\test.pdf
.\.venv\Scripts\python.exe src\docling_test.py input\test.pdf
```

Linux nebo macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Verze balíčků jsou zafixované v `requirements.txt`. MarkItDown je instalován s extras pro PDF, DOCX, PPTX a XLSX.

## Podporované vstupy

| Formát | MarkItDown | Docling | Testovací účel |
| --- | --- | --- | --- |
| PDF | ano | ano | běžný text, layout, tabulky, sken/OCR |
| DOCX | ano | ano | původní struktura dokumentu a tabulky |
| PPTX | ano | ano | snímky, textová pole a technická grafika |
| XLSX | ano | ano | listy, řádky, sloupce a metadata |

Benchmark případný nepodporovaný formát nebo chybu jednoho konvertoru zaznamená do výsledků a pokračuje dalšími kombinacemi.

## Fáze 1: syntetický PDF test

Z kořene repozitáře zůstávají funkční původní příkazy:

```powershell
python src/markitdown_test.py input/test.pdf
python src/docling_test.py input/test.pdf
```

Vytvoří nebo aktualizují pouze:

```text
output/markitdown/test.md
output/docling/test.md
```

`input/test.pdf` je dvoustránkový technický test s nadpisy, seznamy, tabulkami, rovnicemi zapsanými jako text a blokovým schématem. Volitelný generátor zdroje je v `scripts/generate_test_pdf.py`.

## Fáze 2: veřejný dataset

Dataset je deklarovaný v [`test_documents.yaml`](test_documents.yaml). Obsahuje:

| Obsah | Formáty | Kategorie | Oficiální zdroj |
| --- | --- | --- | --- |
| NASA Thermal Modeling and Analysis | PDF, PPTX | technická prezentace | [NASA NTRS](https://ntrs.nasa.gov/citations/20220017174) |
| NIST Handbook 133, Appendix A | PDF, DOCX | komplexní tabulky | [NIST](https://www.nist.gov/pml/owm/nist-handbook-133-current-edition) |
| NACA Aerodynamic Heating of Aircraft Components | PDF | historický sken/OCR | [NASA NTRS](https://ntrs.nasa.gov/citations/19930089131) |
| NIST Smart Manufacturing Metadata | XLSX | tabulková data | [NIST](https://www.nist.gov/ctl/smart-connected-systems-division/networked-control-systems-group/measurement-data-files) |

Každá položka definuje stabilní ID, URL, místní název, formát, kategorii, popis a očekávané vlastnosti. Pole `content_group` spojuje PDF/DOCX nebo PDF/PPTX varianty stejného obsahu pro cross-format report.

### Stažení vstupů

Stáhněte všechny chybějící veřejné dokumenty:

```powershell
python scripts/download_test_documents.py
```

Existující soubory skript standardně přeskočí. Opětovné stažení nebo výběr jednoho dokumentu:

```powershell
python scripts/download_test_documents.py --force
python scripts/download_test_documents.py --document nist_smart_manufacturing_metadata_xlsx
```

Dokumenty se ukládají do `input/public/`, jsou ignorované Gitem a skript nikdy nic neuploaduje. Před přesunem do cíle ověří neprázdný obsah a základní podpis PDF nebo Office ZIP kontejneru. Chyby vypíše v souhrnu a vrátí nenulový návratový kód.

### Spuštění benchmarku

Kompletní benchmark nad všemi lokálně dostupnými položkami:

```powershell
python scripts/run_benchmark.py
```

Užitečné dílčí varianty:

```powershell
python scripts/run_benchmark.py --document nist_smart_manufacturing_metadata_xlsx
python scripts/run_benchmark.py --tool markitdown
python scripts/run_benchmark.py --tool docling --repeat 3
python scripts/run_benchmark.py --document nasa_thermal_modeling_pdf --document nasa_thermal_modeling_pptx
```

`--document` a `--tool` lze opakovat. Dílčí běh nahrazuje pouze záznamy vybraných dvojic dokument–konvertor; nesouvisející výstupy a dřívější výsledky ponechá zachované.

## Výstupy

```text
input/
├── test.pdf
└── public/                         # stažené, Git je ignoruje
output/
├── markitdown/test.md              # Fáze 1
├── docling/test.md                 # Fáze 1
└── public/
    └── <document-id>/
        ├── markitdown.md
        └── docling.md
results/
├── benchmark.json                  # strojově čitelná metadata
└── BENCHMARK.md                    # přehled a cross-format tabulky
```

Každý záznam obsahuje dokument, formát, nástroj a jeho verzi, opakování, dobu konverze, velikost vstupu, délku Markdownu, základní počty nadpisů, tabulek a značek obrázků, stav a případnou chybu.

Tyto indikátory **neurčují sémantického vítěze**. Kvalitu je potřeba ručně posoudit proti zdroji, zejména pořadí textu, vazby buněk tabulek, rovnice, popisky obrázků, rozložení snímků a kvalitu OCR. Pro cross-format případy porovnejte také, zda původní DOCX/PPTX zachovává strukturu lépe než PDF export.

## Lokální a offline provoz

MarkItDown používá `convert_local()` s vypnutými pluginy. Není mu předán LLM klient ani cloudový endpoint.

Docling má pro PDF explicitně `enable_remote_services=False` a `allow_external_plugins=False`; Office formáty používají lokální backendy. Vstupní dokument tedy žádný z projektových skriptů neposílá ke vzdálenému zpracování.

PDF pipeline Doclingu potřebuje modelové artefakty a při prvním použití je může stáhnout. Stahují se modely, nikoli vstupní dokument. Pro následný offline běh je lze předem připravit:

```powershell
docling-tools models download
```

Na Windows projekt pro svůj proces nastavuje `DOCLING_INFERENCE_COMPILE_TORCH_MODELS=false`, takže není nutný volitelný lokální C++ kompilátor pro `torch.compile`.

Historický naskenovaný PDF je záměrně náročný případ. Docling používá svou lokální OCR pipeline; MarkItDown v tomto PoC nemá aktivovaný cloudový OCR ani LLM/plugin rozšíření, proto může ze skenu získat málo nebo žádný text.

## Bezpečné chování

- zdrojové dokumenty se pouze čtou a nikdy nemodifikují,
- Markdown se zapisuje přes dočasný soubor a cílový soubor se nahradí až po úspěšné konverzi,
- výstupy jsou oddělené podle dokumentu a nástroje,
- chybějící vstup nebo selhání převodu se zaznamená bez ukončení celého benchmarku,
- projekt nekonfiguruje LLM, cloudové OCR, embeddingy, vektorovou databázi ani vzdálenou document-processing službu.
