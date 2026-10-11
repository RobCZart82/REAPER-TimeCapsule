# Preference evidence catalog / Preferenciák bizonyítékkatalógusa

## English

The read-only catalog currently lists exactly two keys:

| INI identity | Candidate values | Evidence | Limit |
|---|---|---|---|
| `[reaper] tinttcp` | `0`, `1` | The official theme reference says a theme's `tinttcp` directive overrides the setting in `reaper.ini`; REAPER 5.0+ | A user theme may override the result; manual visual review remains required |
| `[reaper] peaksedges` | `0`, `1` | Same explicit official statement for `peaksedges` | Same theme-override and manual-review limit |

The [official reference](https://www.reaper.fm/sdk/walter/images.php) also documents names such as `tcp_folderindent`, `tcp_heights` and `transport_showborders` as theme `rtconfig.txt` directives. Similar wording is not evidence that those settings are `reaper.ini` keys, so they remain review-only. The code restricts candidates to exact identities and values and still requires caller-supplied, matching REAPER 5+ versions. A candidate is not automatically copied, even in the separate staging export.

Inspect the catalog with `python -m reaper_timecapsule config-catalog`; Configuration Preview embeds the same evidence. Unknown keys, machine/platform/audio devices, hardware, plugin caches, paths and secrets stay excluded or under review according to the diff policy. No active configuration writer exists. Version provenance supplied to the preview is user-provided and is not independently verified.

## Magyar

A csak olvasó katalógus jelenleg pontosan két kulcsot tartalmaz:

| INI-azonosító | Jelölt értékek | Bizonyíték | Korlát |
|---|---|---|---|
| `[reaper] tinttcp` | `0`, `1` | A hivatalos témahivatkozás szerint a téma `tinttcp` direktívája felülírja a `reaper.ini` beállítását; REAPER 5.0+ | A felhasználói téma felülírhatja az eredményt; kézi, vizuális ellenőrzés kell |
| `[reaper] peaksedges` | `0`, `1` | Ugyanilyen kifejezett hivatalos állítás a `peaksedges` kulcsra | Ugyanaz a témafelülírási és kézi ellenőrzési korlát |

A [hivatalos dokumentáció](https://www.reaper.fm/sdk/walter/images.php) a `tcp_folderindent`, `tcp_heights` és `transport_showborders` neveket is `rtconfig.txt` témadirektívaként dokumentálja. A hasonló elnevezés nem bizonyítja, hogy ezek `reaper.ini`-kulcsok, ezért felülvizsgálaton maradnak. A kód csak a pontos azonosítókat és értékeket fogadja el, és azonos, felhasználó által megadott REAPER 5+ verziót is megkövetel. A jelölt érték automatikusan akkor sem másolódik át, ha külön staging-export készül.

A katalógus a `python -m reaper_timecapsule config-catalog` paranccsal olvasható; a Config Preview ugyanazt a bizonyítékot tartalmazza. Az ismeretlen kulcsok, gép/platform/hangeszköz-beállítások, hardver, plugincache, útvonalak és titkok a diff szabályai szerint kizárva vagy felülvizsgálaton maradnak. Aktív konfigurációíró funkció nincs. Az előnézet verzióeredete a felhasználó által megadott adat, nincs függetlenül ellenőrizve.
