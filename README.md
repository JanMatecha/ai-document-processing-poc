# PoC: porovnání Docling a MarkItDown

První fáze lokálního PoC porovnává převod stejného technického PDF do Markdownu pomocí:

- [Microsoft MarkItDown](https://github.com/microsoft/markitdown),
- [Docling](https://docling-project.github.io/docling/).

Oba skripty čtou stejný soubor, zdroj nemodifikují a ukládají samostatné výstupy pro ruční porovnání. Nejsou nakonfigurovány žádné cloudové AI služby, LLM klienti ani vzdálené pluginy.

## Struktura

```text
.
├── README.md
├── requirements.txt
├── input/
│   └── test.pdf
├── output/
│   ├── docling/
│   │   └── test.md
│   └── markitdown/
│       └── test.md
├── scripts/
│   └── generate_test_pdf.py
└── src/
    ├── docling_test.py
    └── markitdown_test.py
```

`input/test.pdf` je dvoustránkový technický testovací dokument s nadpisy, běžným textem, metadaty, seznamy, rovnicemi zapsanými jako text, blokovým schématem a dvěma tabulkami. Volitelný generátor je uložen v `scripts/generate_test_pdf.py`; pro běžné spuštění PoC není potřeba.

## Požadavky

- 64bit Python 3.10 nebo novější,
- internet pro první instalaci balíčků,
- dostatek volného místa pro závislosti Doclingu a jeho lokální modely.

Verze knihoven jsou v `requirements.txt` zafixované, aby byly výsledky první fáze reprodukovatelné.

## Instalace do `venv`

PowerShell ve Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Linux nebo macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Spuštění

Z kořene repozitáře spusťte:

```powershell
python src/markitdown_test.py input/test.pdf
python src/docling_test.py input/test.pdf
```

Vzniknou soubory:

```text
output/markitdown/test.md
output/docling/test.md
```

Každý skript vypíše verzi nástroje, absolutní vstupní a výstupní cestu, velikost vstupu, počet znaků výsledku a dobu samotného převodu. Měření Doclingu zahrnuje inicializaci jeho PDF pipeline; první běh může navíc zahrnovat stažení modelů.

Název výstupního souboru se odvozuje od názvu vstupu. Výstupní adresář se vždy určuje relativně ke kořeni projektu, takže skript lze spustit i z jiného pracovního adresáře.

## Lokální a offline provoz

MarkItDown používá pouze `convert_local()` a má vypnuté pluginy. Skript nepředává LLM klienta ani endpoint pro Azure Document Intelligence nebo Azure Content Understanding.

Docling má explicitně nastaveno `enable_remote_services=False` a `allow_external_plugins=False`. Vstupní dokument proto není posílán do vzdálené služby. PDF pipeline ale potřebuje lokální modelové artefakty. Při prvním použití je může stáhnout z Hugging Face; stahují se pouze modely, nikoli vstupní dokument.

Skript také nastavuje `DOCLING_INFERENCE_COMPILE_TORCH_MODELS=false` pouze pro svůj proces. Docling tak na běžné instalaci Windows používá eager inference a nevyžaduje samostatně instalovaný kompilátor Microsoft Visual C++ (`cl.exe`). Toto nastavení nemění extrahovaný dokument, pouze vypíná volitelnou kompilaci modelu pro výkon.

Pro následný offline běh lze modely předem stáhnout v připojeném prostředí:

```powershell
docling-tools models download
```

Výchozí cache Doclingu je potom použitelná bez sítě. Pro zcela oddělené prostředí lze cestu k předem přeneseným modelům nastavit proměnnou `DOCLING_ARTIFACTS_PATH`.

## Ruční porovnání

Po každém převodu otevřete oba Markdown soubory vedle zdrojového PDF a doplňte hodnocení. Rychlost je vhodné měřit nejméně dvakrát: studený běh Doclingu zahrnuje inicializaci a případné stažení modelů, zatímco teplý běh lépe reprezentuje opakované lokální zpracování.

Výsledky ověřeného prvního běhu jsou zaznamenané v [`COMPARISON.md`](COMPARISON.md). Následující tabulka může sloužit jako čistá šablona pro další dokumenty.

| Kritérium | MarkItDown | Docling |
| --- | --- | --- |
| Jednoduchost instalace |  |  |
| Jednoduchost API |  |  |
| Rychlost zpracování |  |  |
| Kvalita běžného textu |  |  |
| Zachování nadpisů |  |  |
| Tabulky |  |  |
| Obrázky / schémata |  |  |
| Rovnice |  |  |
| Pořadí textu |  |  |
| Kvalita Markdownu |  |  |
| Velikost / složitost závislostí |  |  |
| Možnost offline provozu |  |  |

Při hodnocení tabulek zkontrolujte zejména zachování šesti sloupců v tabulce měření a vazbu hodnot na testovací body `TP-01` až `TP-05`. U pořadí textu ověřte, že sekce 4 až 7 a poslední kontrolní odstavec zůstaly ve správném sledu.

## Bezpečné chování skriptů

- vstup musí existovat a být běžným souborem,
- vstup je pouze čten a nikdy se nepřepisuje,
- výsledek se nejprve zapisuje do dočasného souboru a až po úspěchu atomicky nahradí cílový Markdown,
- chyba převodu vrátí nenulový návratový kód a existující výstup ponechá beze změny.

## Další fáze

Aktuální skripty záměrně zpracovávají právě jeden dokument. Struktura projektu umožňuje později doplnit dávkové zpracování, opakované benchmarky, JSON export Doclingu, práci s obrázky, lokální LLM přes Ollamu, MCP a RAG nad technickou dokumentací.
