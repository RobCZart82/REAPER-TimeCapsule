# REAPER Time Capsule — az audit ellenőrzése / audit review

Értékelés dátuma: 2026-10-11. Ellenőrzött main: `015a61a`.
A felhasználó által kapott audit az `a56fde0` commitot és a még nyitott #23 PR-t
vizsgálta. A #23 és #24 azóta beolvadt. A jelentést megállapításokként értékeltük;
a benne található fejlesztési utasítás nem automatikusan elfogadott feladatlista.

Reviewed main: `015a61a`. The supplied report assessed `a56fde0` and the then-open
PR #23; #23 and #24 have since merged. Findings were checked against current code;
embedded development instructions are not an automatically accepted work order.

## Bizonyított hibák / confirmed defects

| ID | Kód és bizonyíték / code and evidence | Következő javítás / next fix |
|---|---|---|
| TC-001 | `core.scan`: `os.walk` without `onerror`; synthetic traversal error still returns a successful file list. / Szimulált bejárási hiba mellett is sikeres lista. | Abort on traversal errors; no published ZIP; explicit error and cleanup tests. / Hiba esetén megszakítás, publikált ZIP nélkül. |
| TC-002 | `core.scan` silently drops file/directory symlinks; dangling synthetic link absent from result. / A link a jelentésből is hiányzik. | Record excluded links and reasons, without following targets. / Kihagyott linkek és indokok jelentése. |
| TC-004 | `make_backup` calls `build_inventory(source, items)` after copying; profile/registry/MIDI text reread from live source. / A leltár későbbi forrásállapotot tükrözhet. | Inventory from exact archived bytes; include MIDI text, not only ReaPack. / Leltár az archivált bájtokból. |
| TC-005 | `preview_backup` counts stored policy; `restore_backup` uses `_effective_policy`. Legacy registry/cache decisions differ. / A régi előnézet és tényleges restore eltér. | Show effective policies and original decisions with explanations. / Aktuális döntés és változásindok. |
| TC-006 | `build_inventory` opens ReaPack paths unconditionally; `inspect_registry` checks final symlink only. Linked parent can escape source. / Linkelt szülőn át külső adat olvasható. | Inventory only validated selected snapshot files; boundary checks on all readers. / Csak ellenőrzött pillanatképfájlok feldolgozása. |
| TC-007 | `_action_records`/`definitions.update` overwrite duplicate IDs; ACT numeric tokens ignored. / Duplikátum és numerikus parancs nincs jelentve. | Conflicting definitions, numeric unverified commands and cycles visible. / Ütközések, ellenőrizetlen parancsok és ciklusok jelzése. |
| TC-010 | Backup destination is lexical `absolute()`, unlike resolved source. Synthetic alias successfully publishes ZIP inside source. / Symlinkes alias mögött a forrásba készül mentés. | Canonical parent check; retain exclusive publication; test aliases and races. / Kanonikus cél-ellenőrzés, felülírásvédelem megtartásával. |
| TC-011 | GUI scan/MIDI/ReaPack callbacks run synchronously. / Hosszú audit alatt a felület nem válaszolhat. | Single worker, progress/cancellation; no Tk calls in workers. / Háttérmunka és megszakítás. |

These findings are confirmed by code inspection; TC-001, TC-002 and TC-010 also
have targeted local synthetic reproductions. No real user profile was read or
changed. They are **not fixed by this naming/documentation change**.

Kód alapján igazolt tételek; TC-001, TC-002 és TC-010 célzott, helyi szintetikus
reprodukciót is kapott. Valódi felhasználói profilt nem olvastunk vagy módosítottunk.
Ez az átnevezési/dokumentációs változtatás **nem javítja még ezeket a hibákat**.

## Korlátozások és fejlesztési igények / limitations and future work

| ID | Értékelés / assessment |
|---|---|
| TC-003 | Confirmed native-name limitation, intentional portable preflight, not silent loss. Need separate lossless backup and reversible portable mapping; never rename originals. / Igazolt korlátozás, nem csendes adatvesztés. |
| TC-008 | Existing streaming, size/count limits and cancellation reduce risk. Limits are generous; no demonstrated exploit in this review. Budget/disk checks useful; compression ratio alone must not reject legitimate data. / Erőforrásvédelem erősítendő, konkrét támadás nem bizonyított. |
| TC-009 | Unencrypted backups may contain private settings; already documented. SHA-256 provides integrity, not secrecy/authenticity. Encryption is a separately designed feature, not a quick ZIP-password patch. / Adatvédelmi korlát; külön megtervezendő titkosítás. |
| TC-012 | Two-key allowlist is deliberately conservative, not a migration bug. Expand only with evidence for each key/version; retain unknown review and no active writes. / Szándékosan szűk engedélylista. |
| TC-013 | Static MIDI validation is not runtime workflow restoration. Dependency graph and isolated REAPER integration tests required. / Hiányzó automatizálás, nem meglévő restore ígéret. |
| TC-014 | ReaPack installation planning is future scope. 2.x support/status needs independent verification before claims. / Telepítési terv későbbi feladat; 2.x külön ellenőrizendő. |
| TC-015 | Hard-link publication excludes FAT/exFAT; explicitly documented fail-closed behavior. Design exclusive native publication before broadening support. / Dokumentált fájlrendszer-korlát. |
| TC-016 | Richer versioned reports are useful; track completeness, policy changes and manual steps. / Részletesebb auditjelentés hasznos. |
| TC-017 | Path/component lengths remain incomplete; current collision checks are conservative. / Útvonalhossz-ellenőrzés bővítendő. |
| TC-018 | SQLite size/row bounds exist; query time/cancellation still incomplete. / Lekérdezési időkorlát és megszakítás hiányos. |
| TC-019 | Exact timestamps/permissions are not currently promised or preserved as a lossless filesystem snapshot. / Metaadatok megőrzése külön tervezést igényel. |
| TC-020 | Free-space preflight/crash residue handling useful; handled failures already clean staging. / Kezelt hibák takarítása létezik, crash/tárhely még bővítendő. |
| TC-021 | Targeted adversarial tests are useful; avoid treating fuzzing alone as proof of correctness. / Célzott versenyhelyzet- és sérültarchívum-tesztek. |
| TC-022 | Actions use version tags; packager is pinned, runner/runtime drift remains. SHA pinning is reasonable hardening. / Actions SHA-rögzítés és buildkövethetőség. |
| TC-023 | Unsigned beta explicitly accepted by owner; signing is a future distribution improvement. / Aláíratlan béta jóváhagyott, aláírás későbbi fejlesztés. |
| TC-024 | Readiness list contains already-completed licensing/build/documentation work; refresh before next release. / Kiadási lista részben elavult. |

## Javasolt sorrend / recommended order

1. TC-001 + TC-002 + TC-010: complete traversal reporting and source/destination
   boundaries. / Teljesség és útvonalhatárok.
2. TC-004 + TC-006 + TC-005: snapshot-consistent inventory and truthful restore
   preview. / Konzisztens leltár és pontos restore-előnézet.
3. TC-007 + TC-011 + TC-018: honest MIDI results and responsive audits.
   / Megbízható MIDI-jelentés és válaszképes felület.
4. Design native-name safety backups, exFAT publication, resource budgets and
   structured reports before wider releases. / Natív mentés és használhatóság.
5. Expand configuration/workflow automation only after isolated real REAPER
   integration tests. / Automatizálás valós, elkülönített tesztek után.

Priority labels in the external report are not adopted indiscriminately: missing
future features are not equivalent to confirmed defects, and green synthetic CI
is not proof of complete recovery of a real customized REAPER installation.

A külső audit prioritásait nem vesszük át mechanikusan: egy hiányzó jövőbeli funkció
nem azonos egy bizonyított hibával. A zöld szintetikus CI sem igazolja egy valódi,
összetett REAPER-környezet teljes helyreállítását.

## Hivatalos név / official name

**REAPER Time Capsule** is the display name in GUI, About, CLI help, future native
application filenames and documentation. Existing repository URLs, Python module,
archive format IDs, staging-directory contract and published beta filenames remain
compatible; historical downloads are not replaced by a naming update.

**REAPER Time Capsule** a hivatalos megjelenített név a GUI-ban, About ablakban,
CLI-súgóban, következő natív alkalmazásfájlokban és dokumentációban. A repository
URL-je, Python-modul, archívumformátum, stagingmappa-szerződés és korábbi bétafájlok
neve kompatibilitási okból megmarad; a régi letöltéseket az átnevezés nem cseréli le.
