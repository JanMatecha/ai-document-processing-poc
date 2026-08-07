# Výsledky první fáze

Tento protokol zachycuje první praktický běh nad `input/test.pdf` dne 2026-08-07. Jde o jeden syntetický technický dokument, nikoli o obecný benchmark. Závěry je proto potřeba potvrdit na reprezentativních firemních dokumentech.

## Testovací prostředí

- Windows x64 (`10.0.26200.0`), 8 logických procesorů
- Python 3.10.4
- MarkItDown 0.1.7
- Docling 2.118.0, CPU, eager inference
- vstup: 2 strany A4, 7 126 B
- SHA-256 vstupu před i po převodech: `85F3E61E550AC54DE69CFEE82C16B1014B78718C0AD3EEC0B06A8E8B5BCE1621`

Časy níže jsou jeden závěrečný běh každého samostatného Python procesu po instalaci balíčků a stažení modelů. Nejde o statistický benchmark.

## Naměřené výsledky

| Kritérium | MarkItDown | Docling |
| --- | --- | --- |
| Jednoduchost instalace | Jedna závislost s formátovými extras; nevyžaduje ML modely. | Instalace funguje z `pip`, ale stahuje rozsáhlý ML stack a PDF modely. Na Windows bylo nutné vypnout volitelný `torch.compile`, jinak Docling 2.118.0 očekával `cl.exe`. Skript to řeší automaticky. |
| Jednoduchost API | Velmi jednoduché: `MarkItDown(...).convert_local(path).text_content`. | Základní API je krátké, ale bezpečné nastavení PDF pipeline a export vyžadují více objektů. |
| Rychlost zpracování | **0,167 s** | **8,744 s**, přibližně 52x pomalejší v tomto jediném CPU běhu. |
| Kvalita běžného textu | Zachoval veškerý běžný text i text poznámky, ale ponechal zalomení řádků z PDF a záhlaví/zápatí. | Běžné odstavce i text poznámky jsou čisté a bez pevných zalomení; textové popisky uvnitř schématu však chybějí. |
| Zachování nadpisů | Rozpoznal text nadpisů, ale nevytvořil žádné Markdown nadpisy (`#`). | Vytvořil 11 Markdown nadpisů; jejich pořadí na první straně však nebylo správné. |
| Tabulky | Zachoval hodnoty, ale záhlaví tabulky měření rozdělil do dvou tabulek a třísloupcovou tabulku kritérií rozšířil na šest sloupců. | Obě datové tabulky převedl správně, včetně všech pěti řádků `TP-01` až `TP-05` a správného počtu sloupců. |
| Obrázky / schémata | Textové popisky blokového schématu sloučil do řádku; nevytvořil odkaz ani značku obrázku. | Vložil `<!-- image -->`, ale text uvnitř schématu se ve výsledku neobjevil. |
| Rovnice | Zachoval rovnice jako prostý text, ale podtržítka nejsou escapovaná. | Zachoval rovnice jako text a podtržítka správně escapoval pro Markdown. Specializované rozpoznávání vzorců nebylo zapnuté. |
| Pořadí textu | Správné pořadí hlavních sekcí 1 až 7; přidává záhlaví a čísla stran. | Sekce „Key interfaces“ a „3. Control model“ se objevily před titulem a sekcemi 1 a 2. Druhá strana zůstala ve správném pořadí. |
| Kvalita Markdownu | 3 036 znaků; spíše prostý text s částečnými tabulkami. | 3 296 znaků; výrazně čistší struktura nadpisů, seznamů a tabulek, ale s chybějícími popisky schématu a chybou pořadí. |
| Velikost / složitost závislostí | Nízká až střední; pro PDF/DOCX/PPTX nepotřebuje PyTorch ani layout model. | Vysoká. Společné prostředí obou nástrojů má 123 distribucí a 1,37 GB; stažené Docling modely zabírají dalších přibližně 530 MB. |
| Možnost offline provozu | Ano po instalaci balíčků. Skript nepovoluje pluginy ani cloudové klienty. | Ano po instalaci balíčků a předstažení modelů. Vzdálené služby i externí pluginy jsou explicitně vypnuté. |

## Kontrolní zjištění

- Oba příkazy skončily s návratovým kódem `0` a vytvořily očekávané soubory.
- Zdrojový PDF soubor měl před převody i po nich shodný SHA-256 hash.
- Oba výstupy obsahují všech pět měřicích bodů a poslední kontrolní odstavec.
- Oba nástroje zachovaly text informačního bloku „Engineering note“.
- Docling zachoval obě tabulky výrazně lépe, ale nesplnil očekávané pořadí bloků na první straně.

## Předběžný závěr

Na tomto dokumentu není jeden nástroj vítězem ve všech kritériích:

- **MarkItDown je vhodnější pro rychlou, jednoduchou a obsahově konzervativní extrakci textu.** Je 52x rychlejší, zachoval popisky schématu i pořadí sekcí a má výrazně menší provozní režii. Výstup ale vyžaduje další úpravu, pokud jsou důležité nadpisy a tabulky.
- **Docling je vhodnější tam, kde jsou zásadní strukturovaný Markdown a tabulky.** Jeho výstup je podstatně lépe členěný, ale v tomto testu změnil pořadí části dokumentu a ztratil textové popisky uvnitř schématu. Vyšší kvalita struktury tedy automaticky neznamenala úplnější výsledek.

Pro technickou document-ingestion vrstvu zatím doporučení zní: **nevybírat pouze podle ukázkového Markdownu**. Druhá fáze by měla zopakovat test na reálných PDF s vícesloupcovou sazbou, tabulkami, schématy a rovnicemi a u Doclingu kontrolovat úplnost a pořadí. Pokud převažuje běžný text, začal bych MarkItDownem; pokud převažují tabulky a dokumentová struktura, pokračoval bych s Doclingem, ale s validační kontrolou výstupu.
