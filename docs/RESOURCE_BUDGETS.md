# Resource budgets / Erőforráskorlátok

## English

Backup and restore check conservative free-space estimates before staging. Backup accounts for uncompressed selected bytes, compression expansion, ZIP metadata, a manifest allowance, and private parser copies; the temporary filesystem is checked separately. Restore accounts for selected bytes, per-file filesystem allocation and a report allowance. A 16 MiB margin is retained. These checks are estimates, not reservations: other processes, filesystem quotas, sparse/compressed files and remote-volume behaviour can still cause write failures. Existing error/cancellation cleanup remains active.

Before Python loads a ZIP index, a bounded footer reader validates single-volume ZIP/ZIP64 metadata: at most 200001 members and a 64 MiB central directory. Ordinary comments and compressible files are allowed; compression ratio alone does not indicate malicious data. Prefix/self-extracting archives, appended trailing data, multi-volume archives and oversized ZIP64 footer extensions are unsupported. Existing manifest (16 MiB), payload (32 GiB total / 8 GiB each), checksums and member-type boundaries remain mandatory. Generated manifests and restore reports also have a 16 MiB bound. Source scanning stops rather than silently omitting files beyond its 200000-record budget. These fixed limits are not yet user-configurable; arbitrary process memory/CPU exhaustion is not claimed to be eliminated.

Handled failures remove unpublished staging. After a crash or forced process termination, inspect the relevant backup destination, restore parent or system temporary directory:

```
python -m reaper_timecapsule staging-residues /path/to/parent
```

This read-only command lists matching names, entry type, timestamp and entry size. It does not read file contents, follow links, recursively measure directories or remove anything. Matching names do not prove ownership, abandonment or that another process is inactive. Review manually after confirming no operation is running. Private parser remnants may contain configuration data; store backups and reports privately.

## Magyar

A mentés és visszaállítás még az előkészítés előtt konzervatív szabadhely-becslést ellenőriz. A mentés a kiválasztott tömörítetlen bájtokkal, tömörítési növekménnyel, ZIP-metaadatokkal, jegyzéktartalékkal és az elemzők privát másolataival számol; a rendszer ideiglenes fájlrendszerét külön ellenőrzi. A visszaállítás a kiválasztott bájtokkal, fájlonkénti fájlrendszer-foglalással és jelentéstartalékkal számol. További 16 MiB tartalék marad. Ezek becslések, nem helyfoglalások: más folyamatok, kvóták, ritka/tömörített fájlok és távoli kötetek miatt továbbra is előfordulhat írási hiba. A meglévő hiba- és megszakításkori takarítás továbbra is működik.

Mielőtt Python betöltené a ZIP-jegyzéket, korlátozott végrekord-olvasó ellenőrzi az egykötetes ZIP/ZIP64-metaadatokat: legfeljebb 200001 bejegyzés és 64 MiB központi jegyzék engedélyezett. A szokásos megjegyzések és jól tömöríthető fájlok megengedettek; a tömörítési arány önmagában nem jelenti, hogy az adat rosszindulatú. Az előtagos/önkicsomagoló, utólag hozzáfűzött adatú és többkötetes archívumok, illetve túlméretes ZIP64-végrekord-kiterjesztések nem támogatottak. A meglévő jegyzékhatár (16 MiB), adathatár (összesen 32 GiB / fájlonként 8 GiB), ellenőrzőösszeg és bejegyzéstípus-korlát kötelező marad. A létrehozott jegyzék és visszaállítási jelentés is legfeljebb 16 MiB lehet. A forrásvizsgálat 200000 rekord felett leáll, nem hagy ki csendben fájlokat. Ezek a rögzített korlátok még nem állíthatók a felhasználó által; nem állítjuk, hogy minden memória- vagy CPU-kimerítés kizárt.

A kezelt hibák eltávolítják a nem közzétett előkészítést. Összeomlás vagy kényszerített folyamatleállítás után a mentési célmappában, a visszaállítás szülőmappájában vagy a rendszer ideiglenes mappájában kereshetők maradványok:

```
python -m reaper_timecapsule staging-residues /path/to/parent
```

A csak olvasó parancs az illeszkedő neveket, bejegyzéstípust, időbélyeget és bejegyzésméretet listázza. Nem olvas fájltartalmat, nem követ hivatkozást, nem méri rekurzívan a mappát és nem töröl. Az illeszkedő név nem bizonyít tulajdonjogot, elhagyott állapotot vagy másik folyamat inaktivitását. Kézzel vizsgáld meg, miután ellenőrizted, hogy nincs folyamatban művelet. A privát elemzőmásolatok konfigurációs adatokat tartalmazhatnak; a mentéseket és jelentéseket privát helyen tárold.
