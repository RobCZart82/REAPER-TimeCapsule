# REAPER Time Capsule — egységes fejlesztési és kiadási terv

Frissítve: **2026-10-12**. Ellenőrzött main: `c4e266f91398b04f4ae64da698e54c44032bb1c7`.
Ez az egyetlen végrehajtási terv. A [release readiness](RELEASE_READINESS.md)
a megvalósított garanciák technikai háttéranyaga; a
[korábbi audit](AUDIT_REVIEW_2026-10-11.md) történeti bizonyíték, nem párhuzamos feladatlista.
A korábbi audit chatben TC-014-nél csonkolódott; TC-014–024 azonosítása a repository
auditkövetése alapján történt. Az eredeti teljes audit elfogadási feltételeivel való
egyezés annak elérhetőségekor külön ellenőrzendő.

## Ellenőrzött állapot

- Publikált verzió: [v0.9.0-beta.2](https://github.com/RobCZart82/REAPER-TimeCapsule/releases/tag/v0.9.0-beta.2).
  A későbbi main-javítások ettől még nem publikált release-ek.
- E tervmódosítás előtti pillanatképben nincs nyitott PR; issue [#3](https://github.com/RobCZart82/REAPER-TimeCapsule/issues/3)
  és [#4](https://github.com/RobCZart82/REAPER-TimeCapsule/issues/4) nyitott.
- Main [Tests 38231756996](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38231756996)
  és [Desktop builds 38231757016](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38231757016): PASS.
- Legutóbbi helyi Windows/Python 3.13 suite: **220 teszt OK, 13 skip**.
  Szintetikus adatok, dedikált munkamappa; sandboxon kívüli futás az ideiglenesútvonal-korlát miatt.
- Tisztagépes telepítés, kézi GUI, valódi FAT/exFAT/hálózati kötet és izolált REAPER:
  **nincs itt rögzített elfogadási bizonyíték (NOT RUN)**.
- Új béta vagy 1.0.0 nincs e dokumentummal kiadásra késznek nyilvánítva.

## Közelmúltban lezárt munka

| PR | Eredmény | Bizonyíték |
|---|---|---|
| [#55](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/55) | TC-audit és 19 külső állítás összevetése | Megőrzött státusztáblák lent |
| [#56](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/56) | Könyvtárlink/reparse rekordok scan-budget megkerülése javítva | `test_scan_budget.py`, 5 eset |
| [#57](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/57) | Átmeneti HTTP licenceletöltési retry és megszakadt válasz diagnosztika | `test_runtime_licenses.py`, 12 eset; nem tartalomhitelesítés |
| [#58](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/58) | MIDI-gráf ellenőrzése; visszaélszám pontosítása | `test_midi_graph.py`, 512 gráf, 3000 elemű lánc, részletkorlát |
| [#59](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/59) | MIDI hibás UTF-8 olvasás már figyelmeztet | `test_midi_encoding.py`; eredeti bájtok változatlanok |
| [#60](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/60) | ReaPack cp1252 fallback bizonytalanság jelzett, partial státusz | `test_reapack_encoding.py`; URL-titokszűrés megmarad |
| [#61](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/61) | Egyetlen fejlesztési terv és összehangolt kiadási feltételek | ROADMAP és RELEASE_READINESS |
| [#62](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/62) | Snapshot ZIP sor vessző előtti szóköze eltávolítva | Csak formázás; PR és main CI PASS |

Ezeket ne nyissuk újra reprodukció nélkül. Az összes egyszerű ciklus felsorolása,
általános encoding-felismerés és teljes build-reprodukálhatóság nincs megvalósítva.

## Kiadási határ

A következő korlátozott béta alapígérete: felmérés, ellenőrzött mentés és
visszaállítás **új külső mappába**, meglévő cél felülírása nélkül.
MIDI/ReaPack statikus, read-only audit; konfiguráció kétkulcsos preview és opt-in
külső staging. Az 1.0.0 végleges hatókörét a kiadásjelölt előtt rögzíteni kell.

A toolbar/runtime teljesség és aktív konfiguráció-apply nem feltétele egy ezekre
ígéretet nem tevő bétának. Issue #3/#4 ettől nem zárható le. Signing/notarization,
titkosítás, metaadatok teljes megőrzése, ReaPack 2.x/telepítés/szinkronizálás és
Linux desktop-csomag külön későbbi munka; Linux jelenleg source-only.

## Egyetlen végrehajtási sorrend

| Lépés | Munka / státusz | Elfogadási feltétel |
|---|---|---|
| 1 | **Következő kiadási kapu: csomagolt alapfolyamat — nyitott** (TC-001/003/004/005/006/010/021) | Friss Windows/macOS csomag, eldobható profil: backup → verify → új mappás restore; bájt/hash-egyezés. Üres kiválasztás, könyvtár, sérült ZIP, meglévő cél, megszakítás és takarítás, natív nevek. Platformonként PASS/FAIL/NOT RUN, csomag és commit azonosító. |
| 2 | **Következő kiadási kapu: kézi GUI — nyitott** (TC-011/021) | Scan, File policies, MIDI/ReaPack, Config Preview/staging, verify/restore, teljes export, fájlválasztók; nagy jelentések, görgetés, reagálás és macOS natív About. Tiszta támogatott környezetben kézi bizonyíték. |
| 3 | **Fájlrendszer-validálás — nyitott** (TC-008/015/017/020) | Valódi FAT/exFAT és kiválasztott hálózati kötet, hosszú útvonal, ENOSPC/jogosultsági hiba/megszakítás. Nincs csendes kihagyás/felülírás; unsupported eset leáll. A nem validált köteteket a kiadási támogatási körből ki kell zárni vagy korlátként egyértelműen jelölni. |
| 4 | **Célzott fejlesztés — részben kész** (TC-007/013/016/018, külső #8/#15/#16/#19) | MIDI-gráf és MIDI/ReaPack encoding-diagnosztika kész. Következő: regisztrációformák és hibás/olvashatatlan bemenetek; config encoding-provenance; GUI/CLI limitösszegzés. Nagy registry benchmark után döntsünk SQL-optimalizálásról; read-only/deadline/cancel megmarad. Csak reprodukált hibára algoritmusjavítás. |
| 5 | **Dokumentáció és kiadásjelölt — nyitott** (TC-016/022/024) | Verzióválasztás (új béta vagy 1.0.0), changelog/release notes, README EN/HU, PDF/képek és About egyezzen a csomaggal. GPL/runtime notice, csomagmanifest, ellenőrzőösszegek és unsigned státusz ellenőrzése; upstream licencek rögzítése külön reprodukálhatósági feladat. |
| 6 | **Végső kiadási kapu — nyitott** | A pontos candidate teljes CI-mátrixa és csomagolt self-test PASS; letölthető csomagok tisztagépes install/first-launch/backup/restore PASS. Main szabályok/required checks/force-push védelem ellenőrzése. Nincs ismert kritikus/magas hiba a vállalt folyamatokban, nincs privát adat a csomagban; publikálás külön döntés. |
| 7 | **Külön funkcionális mérföldkövek — nyitott** (TC-012/013/014) | #3: igazolt toolbar/icon formátum és izolált runtime próba. #4: explicit opt-in, teljes ellenőrzött rollback, target fingerprint/conflict, atomic apply/recovery és eldobhatóprofil-tesztek. ReaPack telepítés/elérhetőség külön specifikáció; audit nem állíthat működő telepítést. |

A 4. lépés fejlesztése folytatható a kézi/platformpróbák mellett. A nyitott
tétel csak bizonyítékkal lezárható; egy korlát dokumentálása nem funkciómegvalósítás.

## A dokumentáció frissítési szabálya

- Minden repository-munkában ellenőrizzük, érinti-e a változás a tervet, auditstátuszt,
  felhasználói viselkedést, korlátokat vagy kiadási feltételeket. Az érintett dokumentáció
  ugyanabban a PR-ben frissüljön; a csak formázási változás státuszát a következő
  tervfrissítéskor is elegendő rögzíteni.
- Új bizonyíték, lezárt mérföldkő, release, támogatottplatform-változás vagy kiadási
  döntés esetén frissítsük az érintett státuszokat és hivatkozásokat. Ne legyen
  külön párhuzamos feladatlista a release-dokumentumban.
- Az ellenőrzött main-SHA és a hozzá tartozó CI egy dátumozott pillanatkép,
  nem folyamatos élő állapot. Egy csak dokumentációt módosító merge miatt nem
  szükséges önmagát követő újabb dokumentációs PR; a következő érdemi felülvizsgálat
  rögzítse az akkori main-SHA-t. Új tesztet kizárólag tényleges futás alapján írjunk PASS-nak.
- A szabály a repository-n végzett munka része; önmagában nem indít időzített
  háttérfigyelést vagy automatikus publikálást.

## Munkaszabály és bizonyíték

- Minden új változás előtt aktuális main-SHA; kis, önálló PR, releváns regresszió,
  zöld kötelező CI és review-észrevételek rendezése. A jelen dokumentum nem merge/release engedély.
- Reprodukció és negatív kontroll alapján javítsunk; külső jelentés súlyosságát ne vegyük át automatikusan.
- Kézi tesztnapló: platform/OS, commit, csomag/hash, eldobható fixture, lépések,
  elvárt/tényleges eredmény, PASS/FAIL/NOT RUN. CI és kézi bizonyíték külön marad.
- Privát profil, licenc, capsule, workflow-bundle és személyes jelentés nem kerül a repository-ba.
  Runtime licencek a szükséges nyilvános harmadikfél-notice-ok, nem személyes REAPER-licenc.
- Nincs aktív profil felülírás, scriptfuttatás vagy bővítménytelepítés a statikus auditban.
  Checksums nem titkosítás/aláírás. Crash-durability és ellenséges path-swap nincs garantálva.

## Auditkövetés

Az alábbi táblák megőrzik a TC-001–024 és a felhasználótól kapott 19 állítás
azonosítóit. A külső jelentés nem adott vizsgált commitot/reprodukciót.
Feladatok végrehajtási sorrendje kizárólag a fenti hét lépés.

### TC-001–TC-024 státusz és hátralévő munka

A „javított” a konkrét eredeti hibamódot jelenti kód és célzott regresszió alapján,
nem minden profil/fájlrendszer általános tanúsítását. A státuszok a lent rögzített aktuális mainhez és a korábbi audit bizonyítékaihoz tartoznak.

| ID | Státusz | Bizonyíték / következő feladat |
|---|---|---|
| TC-001 | Javított | `scan()` onerror/lstat hibái leállítanak; `test_scan_reliability.py`. Megőrizni a publikálást tiltó regressziót. |
| TC-002 | Javított | Link/reparse/special elem jelentett, célja nem olvasott; `test_scan_reliability.py`. Linkcélok mentése továbbra sem automatikus. |
| TC-003 | Részben | `native_names=True`, schema 3, izolált névtérkép; `test_native_names.py`. Normál portable mód továbbra elutasít; script/menu útvonalak nem átírtak. |
| TC-004 | Javított | Ugyanazon archivált bájtfolyam parsermásolata; `test_snapshot_inventory.py`. Nem teljes tranzakciós profilpillanatkép. |
| TC-005 | Javított | Preview/restore közös effektív policy, eredeti döntés és indok; `test_legacy_reapack.py`. |
| TC-006 | Javított | Szülőkomponens- és kiválasztottfájl-ellenőrzés, sidecar-határ; `test_snapshot_inventory.py`. Ellenséges path-swap garancia nincs. |
| TC-007 | Javított | Duplikáció, numerikus unverified, hiány és ciklus; `test_midi_validation.py`. `test_midi_graph.py`: 512 gráf, mély lánc és ciklusrészletek; PR #58. További regisztrációformák a 4. lépésben. |
| TC-008 | Részben | ZIP-index/manifeszt/payload és szabadhely-preflight; `test_resource_budget.py`. A scan minden leltárrekordra közös keretet használ (PR #56). Konfigurálható budget és általános CPU/memória-korlát nincs. |
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
| #2 | Nem igazolt algoritmushiba | Iteratív, aktív/befejezett állapotú DFS van. Helyi, fájlírás nélküli próba mind az 512 háromcsúcsú irányított gráfnál egyezett a független tranzitív lezárással a ciklus létezéséről. PR #58 ezt tartós regresszióval, mély lánccal és részletkorláttal egészíti ki. A jelentés jelzi: DFS-visszaélszám, nem minden egyszerű ciklus felsorolása. |
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
| #14 | Javított stíluseltérés | PR #62 eltávolította a Snapshot ZIP sor vessző előtti szóközét; nem szintaktikai vagy funkcionális bug. |
| #15 | Hasznos diagnosztikai ötlet | A verifier felsorolt parser/ZIP kivételeket normalizál; I/O hibatípusokat nem nyel el általánosan. Opcionális fejlesztői hibakategória/debug ok vizsgálandó, privát tartalom kiszivárogtatása és felhasználói traceback nélkül. |
| #16 | Részben hasznos kódolási kockázat | Érvényes UTF-8 először sikeresen dekódolódik; cp1252 csak UnicodeDecodeError után jön. Nem változtat archivált bájtokat, de sérült/nem támogatott encoding félreértelmezett leltárt adhat. PR #59: MIDI-dekódolási figyelmeztetés; PR #60: ReaPack cp1252 fallback notes és partial státusz; UTF-8/BOM/legacy/sérült bájt fixture-ek. Config-migráció és általános encoding-felismerés külön nyitott. |
| #17 | Cáfolt None-kezelési hiány | Mind az action-, mind a menüolvasó hívó `contents is not None` ellenőrzést használ. Olvashatatlan bemenet jelentett probléma, nem bizonyított AttributeError. |
| #18 | Nem igazolt Linux-default bug | A fix `~/.config/REAPER` alapútvonal létezik a kódban, de a jelentés nem igazol alternatív REAPER-konvenciót. Későbbi opt-in felderítéshez hivatalos/eldobható REAPER-bizonyíték, portable/XDG eset és explicit felhasználói forrásválasztás kell. |
| #19 | Dokumentációban már megoldott, GUI/CLI javítható | `RESOURCE_BUDGETS.md` tartalmazza a 200000 rekord / 200001 ZIP-member / 8 GiB / 32 GiB / 16 MiB / 64 MiB limiteket. Egységes felhasználói limitösszegzés még hasznos. |

