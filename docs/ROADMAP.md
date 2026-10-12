# REAPER Time Capsule development roadmap

This page describes current `main` capabilities and the ordered work required
before the first stable `1.0.0` release. It is a development plan, not a release
announcement. Status was checked against GitHub on 2026-10-12: `main` is the default
branch, there are no open pull requests, and issues #3 and #4 remain open. The last
published version recorded by this project is `0.9.0-beta.2`; newer fixes on `main`
still need validation in fresh packaged applications. No `1.0.0` release is ready
or published.

## Current capabilities

- Scan a REAPER resource folder, explain file policies, create and verify a
  checksummed capsule, and restore into a new folder without replacing an existing
  destination.
- Report traversal errors, links, reparse points and unsupported names rather than
  silently following or dropping them. Native-name capsule mode is an explicit
  alternative; portable recovery isolates nonportable resources and records their
  mapping.
- Build ReaPack 1.x profile and installed-package reports from recognized
  `reapack.ini` and SQLite formats. Repository order/enabled states and global
  options are inspected read-only; old registry/cache state is not activated.
- Run static MIDI menu and Custom Action checks for duplicate IDs, dependency
  cycles, unresolved references, script paths and unverified numeric/extension
  commands. The audit does not install or execute anything.
- Compare `reaper.ini` files read-only using an exact two-preference allowlist;
  unknown and machine-specific state stays review/excluded. An opt-in staging ZIP
  can carry only selected approved preference data and reverse values. Verification
  is read-only; no command applies this data to REAPER.
- Compare packed themes with an explicitly supplied factory reference without
  copying or deleting anything.
- Run long operations in a background worker. Large GUI output is shortened in a
  display-only copy and rendered in bounded chunks; full scan policy rows remain in
  File policies and CLI report output is complete.
- Build unsigned macOS and Windows beta packages. Linux is source-only. GPL-3.0-only
  and bilingual user documentation have been selected/prepared.

See [the current audit status](AUDIT_REVIEW_2026-10-11.md), [release readiness](RELEASE_READINESS.md)
and the linked issue for each remaining area.

## Összefésült audit és végrehajtási sorrend (2026-10-12)

Az alábbi kiegészítés a TC-001–TC-024 korábbi auditot és a felhasználó által
2026-10-12-én átadott, 19 állításból álló külső jelentést egyesíti a meglévő
1.0.0-tervvel. Ellenőrzött alap: `f188765572e150a50e4c2a1680bd34caa30e8d25`.
A külső jelentés nem ad vizsgált commitot vagy működő reprodukciót; súlyosságait
nem vesszük át automatikusan. A lent jelzett vizsgálatok nem bizonyított hibák.
Az eredeti jelentés személyes csatolmányának elérési útját nem tesszük közzé.

Ez a ROADMAP az egyetlen végrehajtási terv; az
[AUDIT_REVIEW_2026-10-11.md](AUDIT_REVIEW_2026-10-11.md) történeti státuszforrás.
A korábbi chatből elérhető audit TC-014 közben csonkolódott; TC-014–TC-024
azonosításához a repository auditkövetését használtuk. Az eredeti teljes
dokumentum minden elfogadási feltételével való egyezés külön ellenőrzendő,
ha a teljes dokumentum elérhetővé válik.

### Prioritások és elfogadási feltételek

| Sorrend | Feladat / kapcsolódó tételek | Elfogadási feltétel |
|---|---|---|
| 1 — kiadási kapu | Az alábbi 2–3. lépés: kapszula és csomagolt GUI végponttól végpontig; TC-001/003/004/005/006/010/011/021. | Friss macOS/Windows csomag, eldobható profil: backup → verify → új mappás restore; bájt/hash egyezés, meglévő cél megőrzése, hibák és megszakítás takarítása, natív nevek, nagy jelentés/export és About. Platformonként PASS/FAIL/NOT RUN napló. |
| 2 — kiadási kapu | TC-008/015/017/020/021: tárhely-, fájlrendszer- és útvonalhatárok. | Valódi cserélhető és kiválasztott hálózati kötet tesztje; ENOSPC/jogosultsági hiba és megszakítás; a nem támogatott eset egyértelműen leáll. Nincs csendes kihagyás/felülírás. A becslés és crash-maradványok korlátai láthatók. |
| 3 — célzott ellenőrzés | MIDI-gráf szemantikája és további regisztrációformák; TC-007/013, új jelentés #2/#17. | Önhurok, különálló/átfedő ciklus, aciklikus keresztél, mély lánc, hibás/olvashatatlan bemenet. Független referencia ellenőrzi a ciklus létezését; a jelentés nem nevezi a DFS visszaéleinek számát az összes egyszerű ciklus számának. Csak reprodukált hibára készüljön algoritmusjavítás. |
| 4 — diagnosztika | Kódolási bizonytalanság, erőforráskorlátok és hibaüzenetek; TC-008/016/018, új #8/#15/#16/#19. | UTF-8/BOM/cp1252/hibás bájt tesztek; eredeti mentett bájtok változatlanok, bizonytalan dekódolás jelzett. CLI/GUI a limiteket és a túllépés okát megmutatja. Nagy registry benchmark alapján döntsünk SQL-optimalizálásról; read-only/deadline/megszakítás megmarad. |
| 5 — funkcionális határ | A lentebbi 4–6. lépés: issue #3/#4, TC-012/013/014. | Toolbar/icon csak igazolt formátummal; runtime csak eldobható REAPER-ben. ReaPack terv őrzi a sorrendet/verziót/pint, de nem állít telepítést vagy letöltés-ellenőrzést. Kétkulcsos konfiguráció-preview/staging marad; aktív apply külön rollback-terv nélkül tilos. |
| 6 — kiadási kapu | A lentebbi 7–10. lépés: TC-016/022/024, dokumentáció, CI és release candidate. | Kétnyelvű dokumentáció/útmutatók egyeznek a csomaggal; kötelező CI és kézi elfogadási tesztek zöldek; letölthető csomagok ellenőrzöttek. Új verzió és publikálás külön kiadási döntés. |
| 7 — későbbi fejlesztés | TC-009/019/023, Linux felderítés (#18), konfiguráció-apply, ReaPack 2.x/telepítés. | Külön specifikáció: titkosítás/hitelesítés, metaadatmegőrzés, signing/notarization és platformfelderítés. Nem feltétele az explicit korlátokkal kiadott béta működésének, nem jelölhető késznek dokumentáció alapján. |

### TC-001–TC-024 státusz és hátralévő munka

A „javított” a konkrét eredeti hibamódot jelenti kód és célzott regresszió alapján,
nem minden profil/fájlrendszer általános tanúsítását. A források és tesztek az
ellenőrzött alapcommithoz tartoznak.

| ID | Státusz | Bizonyíték / következő feladat |
|---|---|---|
| TC-001 | Javított | `scan()` onerror/lstat hibái leállítanak; `test_scan_reliability.py`. Megőrizni a publikálást tiltó regressziót. |
| TC-002 | Javított | Link/reparse/special elem jelentett, célja nem olvasott; `test_scan_reliability.py`. Linkcélok mentése továbbra sem automatikus. |
| TC-003 | Részben | `native_names=True`, schema 3, izolált névtérkép; `test_native_names.py`. Normál portable mód továbbra elutasít; script/menu útvonalak nem átírtak. |
| TC-004 | Javított | Ugyanazon archivált bájtfolyam parsermásolata; `test_snapshot_inventory.py`. Nem teljes tranzakciós profilpillanatkép. |
| TC-005 | Javított | Preview/restore közös effektív policy, eredeti döntés és indok; `test_legacy_reapack.py`. |
| TC-006 | Javított | Szülőkomponens- és kiválasztottfájl-ellenőrzés, sidecar-határ; `test_snapshot_inventory.py`. Ellenséges path-swap garancia nincs. |
| TC-007 | Javított | Duplikáció, numerikus unverified, hiány és ciklus; `test_midi_validation.py`. Gráfszemantika további ellenőrzése a 3. prioritás. |
| TC-008 | Részben | ZIP-index/manifeszt/payload és szabadhely-preflight; `test_resource_budget.py`. Konfigurálható budget és általános CPU/memória-korlát nincs. |
| TC-009 | Nyitott | Nincs integrált titkosítás/aláírás vagy teljes érzékenyadat-felismerés. Kapszulák és exportok privátak. |
| TC-010 | Javított | Feloldott/rögzített célszülő, kizárólagos publikálás; alias/race/no-overwrite tesztek. Bind-mount és minden ellenséges race nincs tanúsítva. |
| TC-011 | Javított | Háttérworker, korlátozott/darabolt GUI-preview, File policies és teljes export; `test_background.py`, `test_report_export.py`. Kézi nagyprofil-GUI teszt marad. |
| TC-012 | Nyitott | Bizonyítékkatalógus, de csak tinttcp/peaksedges; nincs aktív apply, teljes konfliktuskezelés/rollback. Issue #4. |
| TC-013 | Részben | Statikus gráf és recovery plan van; toolbar/icon és REAPER-runtime nincs. Issue #3. |
| TC-014 | Részben | `recovery_plan.py`: repositorysorrend, állapot, verzió/pin; `test_recovery_plan.py`. Elérhetőség, telepítés és szinkronizálás nincs. |
| TC-015 | Részben | Hard-link után natív no-replace rename; `test_file_publication.py`. Valódi FAT/exFAT/hálózati validálás hiányzik. |
| TC-016 | Részben | Verziózott jelentés, időpont, forrás, vizsgálati alap, teljes JSON-export már van. Hitelesített eredet/aláírás nincs. Az auditkövetés exportot jövőbeli feladatnak nevező mondata elavult. |
| TC-017 | Részben | Névtér és végleges/ideiglenes path-capacity preflight; Windows UTF-16 teszt. Szokatlan FS/alias és hosszúútvonal-kompatibilitás korlátozott. |
| TC-018 | Javított | SQLite read-only, méret/sor és 5 s query-budget, progress-handler; `test_audit_cancellation.py`. Ez nem általános OS I/O-deadline. |
| TC-019 | Nyitott | Timestamp/mode információ mentett, restore friss fájlalapértékeket használ; ACL/owner/xattr/Finder nincs megőrizve. |
| TC-020 | Részben | Helybecslés, kezelt hiba/interruption cleanup és read-only residue lista. Crash-durability és tranzakciós garancia nincs. |
| TC-021 | Részben | Szintetikus hibainjektálás/race/határtesztek és csomagolt self-test bővült. Valódi izolált REAPER és tisztagépes QA szükséges. |
| TC-022 | Részben | Actions commit-SHA és packager pin tesztelt; `test_workflow_pins.py`. A latest runner/OS toolchain változhat, bitazonos reprodukálhatóság nincs. |
| TC-023 | Nyitott, elfogadott béta-korlát | Unsigned csomagok; signing/notarization külön terjesztési fejlesztés. |
| TC-024 | Részben | GPL és kétnyelvű dokumentáció/útmutatók vannak. Következő csomaghoz képek, útmutatók és release notes újra egyeztetendők. |

### Az új 19 tételes jelentés ellenőrzése

| Új ID | Minősítés | Ellenőrzés és döntés |
|---|---|---|
| #1 | Cáfolt szintaktikai hiba | A `gui.py` 92. sorának lambda/tuple kifejezése szabályos; a zárójel és vessző közötti szóköz stílus. Korábbi CI compile és GUI-import sikeres. Nincs kritikus javítás. |
| #2 | Nem igazolt algoritmushiba | Iteratív, aktív/befejezett állapotú DFS van. Helyi, fájlírás nélküli próba mind az 512 háromcsúcsú irányított gráfnál egyezett a független tranzitív lezárással a ciklus létezéséről. Ez nem bizonyít minden gráfot vagy minden egyszerű ciklus felsorolását; a fenti 3. prioritás szerint bővítsük a lefedettséget. |
| #3 | Cáfolt archive-validációs rés | `_valid_path()` NULL-t tilt; `_validate_portable_paths()` kontrollokat/surrogate-okat is tilt a schema-2 verify előtt. A schema-3 eredeti név validátora ugyancsak tiltja őket. Teljes hívási útvonalat kell tesztelni, nem csak a segédfüggvényt. |
| #4 | Cáfolt; a javaslat gyengítené az opt-int | `opt_in is not True` szándékosan csak a valódi True-t fogadja el; 1 vagy truthy objektum nem felhasználói jóváhagyás. Megőrizni. |
| #5 | Cáfolt konkrét None/AttributeError állítás | Invalid globális booleanhoz note/partial státusz, invalid repository-enabled értékhez kihagyás és partial státusz tartozik. Nem történik None attribútumhívás. |
| #6 | Cáfolt kezelt-hiba cleanup hiány | TemporaryDirectory context manager, stream ExitStack és staging finally van; `test_inventory_failure_cleans_snapshot_and_unpublished_zip` lefedi. Process-crash külön TC-020 korlát; nem memóriaszivárgásként címkézzük. |
| #7 | Cáfolt az ellenőrzött mainen | A GUI-feltétel már `items` ÉS `portable_names_ready` jelenlétét ellenőrzi. A belső eredményszerződés további típusellenőrzése csak hibás eredményreprodukció esetén szükséges. |
| #8 | Mérendő optimalizálási ötlet | `sqlite_master` táblaneveinek materializálása csökkenthető célzott lekérdezéssel. Már van méret/deadline/megszakítás-védelem; nagy schema benchmark és változatlan unsupported-schema viselkedés kell, mielőtt hibának vagy prioritásos lassulásnak neveznénk. |
| #9 | Már dokumentált határ | A docstring és kimenet kimondja, hogy extension/runtime aktiválás nincs ellenőrizve. A toolbar/runtime hiány TC-013/issue #3 része. |
| #10 | Cáfolt traversal/OOB állítás | Fullmatch csak canonical `objects/[0-9]{6}.bin` nevet fogad el; a manifest/taglista létezést és egyediséget ellenőriz. Az ordinal nem listaindex, a hiányzó sorszám önmagában nem OOB. Nem kell indokolatlan szekvenciafeltétel. |
| #11 | Alacsony stílusötlet | A fájlazonosság-lambda kiemelése csak kapcsolódó karbantartáskor; nem változtatja a backup korrekt működését. |
| #12 | Cáfolt redundanciaállítás | Forrás konfigurációszülője, cél konfigurációszülője és alapértelmezett erőforrás három külön tiltott határ. Refaktor nem törölhet határellenőrzést. |
| #13 | Nem igazolt kommenthiba | A komment 32060-ra korlátozott piano-roll feldolgozást és más sectionök óvatosságát írja le, összhangban a kóddal. Bővítés issue #3-ban csak igazolt formátummal. |
| #14 | Valós, alacsony stíluseltérés | A 92. sor `)) ,` formázása későbbi kis takarítás; nem szintaktikai vagy funkcionális bug. |
| #15 | Hasznos diagnosztikai ötlet | A verifier felsorolt parser/ZIP kivételeket normalizál; I/O hibatípusokat nem nyel el általánosan. Opcionális fejlesztői hibakategória/debug ok vizsgálandó, privát tartalom kiszivárogtatása és felhasználói traceback nélkül. |
| #16 | Részben hasznos kódolási kockázat | Érvényes UTF-8 először sikeresen dekódolódik; cp1252 csak UnicodeDecodeError után jön. Nem változtat archivált bájtokat, de sérült/nem támogatott encoding félreértelmezett leltárt adhat. Kódolási provenance/figyelmeztetés és fixture-ek a 4. prioritásban. |
| #17 | Cáfolt None-kezelési hiány | Mind az action-, mind a menüolvasó hívó `contents is not None` ellenőrzést használ. Olvashatatlan bemenet jelentett probléma, nem bizonyított AttributeError. |
| #18 | Nem igazolt Linux-default bug | A fix `~/.config/REAPER` alapútvonal létezik a kódban, de a jelentés nem igazol alternatív REAPER-konvenciót. Későbbi opt-in felderítéshez hivatalos/eldobható REAPER-bizonyíték, portable/XDG eset és explicit felhasználói forrásválasztás kell. |
| #19 | Dokumentációban már megoldott, GUI/CLI javítható | `RESOURCE_BUDGETS.md` tartalmazza a 200000 rekord / 200001 ZIP-member / 8 GiB / 32 GiB / 16 MiB / 64 MiB limiteket. Egységes felhasználói limitösszegzés még hasznos. |

### Elvégzett javítás: a felmérési rekordkeret megkerülése (2026-10-12)

- Alap: `26451c9d59c01ea1edf167b6bae4701acc11bea0`; TC-008/TC-021, a
  fenti 2. prioritás erőforrás-határvizsgálata.
- Reprodukált hiba: a `MAX_FILES` ellenőrzés csak a fájlciklusban futott,
  a könyvtárként jelentett linkek/reparse pontok korlátlanul bővíthették a leltárt.
- Javítás: minden leltárrekord hozzáadásakor közös keretellenőrzés. Túllépéskor
  nincs részleges eredmény és a backup még a parserleltár/célmappa/staging előtt leáll.
  Linkcélok olvasása és az üres normál könyvtárak rekordként számolása nem szükséges.
- Regresszió: `tests/test_scan_budget.py`, öt szintetikus teszt.
  Javítás előtt három túllépési eset FAIL, két kontroll PASS;
  javítás után 5/5 PASS. A junction-esetek attribútumszimulációt használnak.
- Helyi Windows/Python 3.13 teljes suite: 197 teszt, OK, 13 skip.
  A sandbox ideiglenes útvonal-hozzáférési korlátja miatt a sikeres futás
  sandboxon kívül, kizárólag dedikált szintetikus munkamappában történt.
  Natív macOS/Linux, Python 3.10/3.12 és csomagolt GUI: a PR CI-je ellenőrizze.
- Valódi cserélhető/hálózati kötet és élő REAPER: NOT RUN. Üreskönyvtár-bejárás,
  általános CPU/memóriabudget és konfigurálható limitek továbbra nyitottak;
  TC-008 ettől részben javított marad.

### Ellenőrzési napló és munkaszabály

- Kód/teszt/docs olvasás az alapcommitról; az átadott külső jelentés
  állításai külön minősítve. A számozás nem új GitHub issue-szám.
- A helyi próba csak a mainből kiemelt `_action_cycles()` függvényt futtatta
  memóriában, szintetikus gráfokkal; nem a teljes alkalmazás tesztje.
- Az előző ellenőrzés alapcommithoz tartozó main CI-je:
  [Tests 38175204213](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38175204213)
  és [Desktop builds 38175204227](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38175204227)
  sikeres volt. Olvasott macOS 3.12 napló: 192 teszt OK; Windows 3.12:
  192 teszt OK, 2 skip. Ez nem a dokumentációmódosítás saját CI-eredménye.
- Teljes új helyi suite és valódi REAPER-integráció e tervfrissítésben:
  NOT RUN. A terv nem jelöl reprodukció nélkül új kritikus hibát.
- Implementáció előtt új main-SHA rögzítése, konkrét reprodukció és negatív
  kontroll; javítás külön kis PR-ben, célzott regresszióval és releváns CI-vel.
- A már javított TC-tételeket ne nyissuk újra bizonyíték nélkül. A privát profil,
  licenc, DMG, workflow-bundle és jelentés nem kerülhet a repository-ba.
- A terv frissítése nem kódjavítás, merge-, release- vagy publikálási engedély.

## Ordered work before `1.0.0`

### 1. Lock the first-release scope

- The 1.0.0 core promise is a safe workflow to scan, back up, verify and restore a
  capsule into a new folder without replacing an existing destination.
- MIDI and ReaPack functions are static/read-only audits. Configuration migration
  is a read-only preview with optional external staging. These features must report
  what they did and what they could not verify.
- Keep active `reaper.ini` editing, automatic ReaPack installation/synchronization,
  script execution, and claims of end-to-end MIDI workflow compatibility outside
  1.0.0 unless their separate safety and validation requirements are completed.

### 2. Re-check restore and archive safety

- Current `main` rejects an empty snapshot selection and a directory supplied as a
  snapshot before verification or restore. This addresses the reported
  `[Errno 21] Is a directory: '/'` case caused by starting Restore without a ZIP.
- Verify the behavior in the packaged GUI, not only through unit tests. Cover an
  empty selection, directory, corrupt archive, existing destination, cancellation,
  and a valid backup/verify/restore cycle.
- Include the priority-2 real-volume, free-space, cleanup and path-capacity matrix above.
- Compare the restored files with the manifest and hashes. Run only against
  synthetic fixtures or disposable profiles; do not add the user's capsule or
  configuration to the repository.

### 3. Acceptance-test the current packaged GUI

- Build fresh macOS and Windows applications from the reviewed `main` commit.
- Exercise Scan / Preview, MIDI Audit, ReaPack Audit, Config Preview, Backup,
  Verify, Restore, full-report export, all file choosers, and cancellation.
- Recheck the earlier “Unexpected source path” report, long-output scrolling and
  responsiveness, plus the macOS native About menu and displayed version.
- CI already has synthetic bundled-app checks for oversized output and macOS About
  hook behavior. A clean-machine visual/manual pass is still required.

### 4. Finish or explicitly bound the MIDI audit (#3)

- Validate graph cycle-detection semantics and unreadable-input handling using the
  independent fixtures specified in priority 3 above; do not replace DFS without a reproducer.
- Evaluate remaining ReaScript registration formats with synthetic fixtures and
  make sure summary counts stay complete when detailed findings are capped.
- Verify toolbar-to-icon parsing only if the saved file format and path rules are
  supported by reliable REAPER evidence. Otherwise keep the result explicitly
  `not-checked`.
- Keep numeric/external commands, runtime registration and action behavior marked
  unverified unless an isolated disposable REAPER test proves them. Never execute
  scripts or install extensions during a static audit.
- Close issue #3 only when its acceptance criteria are met or its remaining limits
  are clearly narrowed and documented for 1.0.0.

### 5. Preserve configuration-migration safety (#4)

- Keep the exact preference allowlist, hardware/platform/plugin/cache exclusions,
  unknown-value review, and explicit external staging behavior.
- Make clear that staged reverse values cover selected keys only; staging is not a
  complete destination backup or rollback snapshot.
- Do not add an apply-to-active-profile command for 1.0.0 without a separate design
  for explicit opt-in, complete verified external rollback, target fingerprint and
  conflict checks, atomic replacement, failure recovery, and disposable-profile
  tests. Keep issue #4 open while those criteria are incomplete.

### 6. Make report and ReaPack outcomes understandable

- Explain in the GUI and documentation which files are restored automatically and
  which are placed under `NeedsReview/`.
- State that the ReaPack database is review-only under current policy; its presence
  in a backup does not mean installed packages or registry state are activated.
- Evaluate uncertain text-decoding provenance, actionable validation categories,
  registry schema benchmark results and visible resource-limit summaries (priority 4).
- Confirm reports distinguish complete counts from capped detail lists, and clearly
  label checks that were not performed.

### 7. Refresh the English and Hungarian user documentation

- Keep both README languages equal in scope and detail, and update the illustrated
  PDF guides and screenshots to match the 1.0.0 interface.
- Explain the first-launch macOS flow for an unsigned application, including the
  operating-system approval prompts seen during testing. Distinguish those prompts
  from Time Capsule's normal operation and do not advise disabling platform
  protections.
- Document the standard backup, verify and new-folder restore flows, `NeedsReview/`,
  ReaPack review-only behavior, privacy of reports/capsules, and known limitations.
- Do not include personal paths, REAPER profiles, licenses, private reports, or DMGs.

### 8. Complete platform and CI checks

- Run the full Python test matrix and native macOS/Windows packaged-app self-tests
  on the release candidate. Fix all failures before merging or tagging.
- Protect `main` with pull-request-based changes and required green CI checks; block
  force-pushes and branch deletion. Review the repository rules before treating this
  gate as complete.
- Record supported platforms and filesystems accurately. Linux is source-only unless
  a desktop package and its acceptance tests are added; removable/network filesystem
  limitations must remain visible.
- Confirm GPL-3.0-only notices, app version/About text, icons, and artifact contents.

### 9. Prepare and validate a release candidate

- Bump the application version to `1.0.0`, update the changelog, release notes,
  download links and bilingual documentation together.
- Build from the reviewed `main` commit. Publish checksums for each downloadable
  artifact and state clearly whether it is signed/notarized; do not imply signing
  that has not occurred.
- Install and exercise the candidate on clean supported macOS and Windows systems,
  with a disposable REAPER profile. Verify the actual downloaded packages, not only
  CI artifacts or source tests.

### 10. Apply the release go/no-go gate

Publish `1.0.0` only when all of the following are true:

- Required CI and packaged-app self-tests pass.
- The clean-machine backup, verification and restore acceptance tests pass on every
  supported desktop platform.
- No known critical or high-severity defect remains in the promised workflows.
- The release notes and both language guides match the shipped behavior and state
  the remaining MIDI, ReaPack, migration, signing and filesystem limitations.
- The release artifacts contain no personal REAPER data, licenses, user bundles or
  private test reports.

## Post-1.0.0 candidates

- ReaPack 2.x support requires source-format verification and independent fixtures.
- Applying staged preferences or providing full migration rollback is a separate
  high-risk feature and remains out of scope until issue #4's acceptance criteria
  can be met.
- Broader toolbar/action runtime validation is separate from the static MIDI audit
  and must use disposable REAPER profiles.
- Signing/notarization and additional packaged platforms can be revisited as
  distribution improvements; current release metadata must describe actual status.

## Guarantees and limits

- No automatic overwrite of an active REAPER resource folder; restore targets a new
  location.
- No executing untrusted scripts, installing extensions, downloading ReaPack
  packages, or uploading personal REAPER profiles, license files or DMGs.
- Checksums are not encryption, signatures or proof of origin. Capsules can contain
  private configuration and filenames and should be stored accordingly.
- Filesystem capacity checks are estimates. Crash durability, every removable or
  network filesystem, complete metadata preservation and every customized REAPER
  environment are not guaranteed.
- Green synthetic CI is necessary but does not replace clean-machine or isolated
  real-REAPER acceptance testing.
