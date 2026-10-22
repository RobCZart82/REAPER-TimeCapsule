# REAPER Time Capsule — egységes fejlesztési és kiadási terv

Frissítve: **2026-10-14**. Ellenőrzött main a 1.0.0 kiadáskor: `c495a66b9059f561951ef09fdd880a6bbdb64309`.
Ez az egyetlen végrehajtási terv. A [release readiness](RELEASE_READINESS.md)
a megvalósított garanciák technikai háttéranyaga; a
[korábbi audit](AUDIT_REVIEW_2026-10-11.md) történeti bizonyíték, nem párhuzamos feladatlista.
A korábbi audit chatben TC-014-nél csonkolódott; TC-014–024 azonosítása a repository
auditkövetése alapján történt. Az eredeti teljes audit elfogadási feltételeivel való
egyezés annak elérhetőségekor külön ellenőrzendő.

## Legutóbbi stabil kiadás — v1.0.0 — 2026-10-14

A [REAPER Time Capsule 1.0.0 stabil kiadás](https://github.com/RobCZart82/REAPER-TimeCapsule/releases/tag/v1.0.0) 2026-10-14-én megjelent; a v1.0.0 tag a c495a66b9059f561951ef09fdd880a6bbdb64309 main commitra mutat. A release ID 412475413; a PR #77 squash merge-ként került a main ágba. A release nem előzetes kiadás, és a GitHub Latest címkével jelöli.

- PR #77 végső ellenőrzései PASS: [Tests run 38531184489](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38531184489) és [Desktop builds run 38531184451](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38531184451); a Windows/macOS forrásteszt, csomagolás és bundled self-test sikeres.
- Nyolc release-asset van: két aláíratlan app ZIP, két pontos forrásarchívum, platformonkénti build-manifest, kiadási megjegyzés és összevont SHA256SUMS.txt. A checksums fájl mind a másik hét assethez egyező SHA-256 értéket tartalmaz.
- App csomagok: Windows x64 SHA-256 abd02dc625fe78ccc3807b83e09ff5cafe7a51f7de01044d48452be23c6caf5d; macOS Apple Silicon SHA-256 f74b5356602fd71a4598be8a429fba6c50c2b9de7717ee01b959f9c4ecfb3e6b. Mindkét build-manifest 1.0.0 verziót, c495a66 commitot és sikeres szintetikus self-testet rögzít.
- Windows 11 x64 Intel valós profilú Restore-próba egy korábbi, funkcionálisan azonos 1.0.0 jelöltbuilddel PASS: 7 035 hordozható fájl visszaállítva, 32 felülvizsgálatra elkülönítve, 0 legacy kihagyás, 0 inspection omission. A ZIP CRC- és mind a 7 067 manifest SHA-256 ellenőrzése PASS.
- A felhasználó macOS-en is sikeres GUI-folyamatot jelentett; külön macOS jelentés/archívum nem érkezett a darabszámok és hash-ek független ellenőrzésére. A pontos végleges release fájlok telepítését külön nem tesztelték.

A csomagok aláíratlanok; a felhasználó elfogadta az aláíratlan stabil publikálást. Tisztagépes telepítés/első indítás, FAT/exFAT és hálózati kötet-validálás NOT RUN, a kiadási megjegyzés ezt jelzi. A #3 MIDI toolbar/runtime és #4 aktív konfiguráció-apply/rollback külön, 1.0.0 scope-on kívüli mérföldkő. Plugintelepítést vagy teljes REAPER runtime-integrációt nem ígérünk.

## Történeti jelöltellenőrzések és auditkövetés

- Korábbi publikált verzió: [v0.9.0-beta.2](https://github.com/RobCZart82/REAPER-TimeCapsule/releases/tag/v0.9.0-beta.2); a fejlesztések azóta a v1.0.0 stabil kiadásban jelentek meg.
- A PR #73 (`e4e25c8`) javítása beolvadt a main ágba; issue [#3](https://github.com/RobCZart82/REAPER-TimeCapsule/issues/3) és [#4](https://github.com/RobCZart82/REAPER-TimeCapsule/issues/4) nyitott.
- A PR #73 [`Tests` run 38516327510](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38516327510) és [`Desktop beta builds` run 38516327518](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38516327518) PASS; a Windows és macOS build, valamint a tesztmátrix sikeres. A Windows futás tartalmazza a >259 karakteres végső helyreállított fájlra vonatkozó szintetikus backup→restore regressziót.
- Windows 11 x64 gépen a PR #70 régi buildjén a Restore korábban FAIL volt; a PR #73 Windows Actions-buildjével végzett ismételt, valós REAPER-profilos próba **PASS**. A mentett Restore-jelentés: 7 035 visszaállított, 32 review alá elkülönített, 0 kihagyott legacy cache, 0 inspection omission. A File policies ablak és a privát JSON-export is PASS: 7 035 keep, 32 review, 12 regenerate, 2 exclude; 0 inspection omission. A felhasználó minden gombot és funkciót működőnek jelzett. A korábbi konkrét Scan / Preview, MIDI Audit, ReaPack Audit, Backup, Verify és az új Restore/File policies eredmények ezt alátámasztják.
- macOS kézi smoke-test (felhasználói jelentés, 2026-10-14): a felhasználó szerint a Windows-próbán végigvett műveletek — Scan / Preview, MIDI Audit, ReaPack Audit, Backup, Verify, Restore, File policies és privát JSON-export — mind sikeresek voltak a PR #73 [macOS Actions-artefaktumával](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38516327518/artifacts/11872227935) (artifact ID `11872227935`, PR-head `c7e216dc668aced2578fff66d2c61fe6f64b5eed`, SHA-256 `87a783f52da62dd996de35522cb01e1f96a7a723804782870942a8be7904a5a2`). macOS-verziót a felhasználó nem adott meg; külön macOS JSON-jelentés vagy archívum-integritási eredmény nem érkezett, ezért a Windows számlálói nem vonatkoznak erre a próbára.
- Helyi PR #73 fájlrendszerteszt a sandbox `WinError 5` korlátozása miatt **NOT RUN**. A PR Windows/macOS/Linux CI-tesztjei PASS; ezek a CI-eredmények a változás ellenőrzései.
- A célzott, valós profilon végzett Windows GUI smoke-test PASS. Tisztagépes telepítés, izolált REAPER-runtime, illetve valódi FAT/exFAT/hálózati kötet tesztje továbbra is **NOT RUN**.
- A PR #77 (`release/1.0.0-candidate`) 1.0.0-s jelöltcsomagjával Windows 11 x64 Intel gépen végzett felhasználói Restore-próba PASS (PR-head `a96d263bb4d45964a89f758159a4f582c47479cd`, Windows Actions-artefaktum SHA-256 `36185397c6226467c03ec23bf165735a9d07ab0390388a6fbcae144a250a9d55`). A felhasználói `restore.json` 7 035 visszaállított hordozható fájlt, 32 review alá elkülönített fájlt, 0 legacy kihagyást és 0 inspection omissiont mutatott. A mellékelt `Test100.zip` CRC-ellenőrzése PASS; a schema-2 manifest mind a 7 067 fájljának SHA-256 értéke egyezett. A jelentés és a privát archívum nem került a repository-ba. Ez valós profilú célzott próba, nem tisztagépes telepítési vagy fájlrendszer-validálási bizonyíték.
- macOS-en a felhasználó a legfrissebb 1.0.0 jelöltcsomaggal azonosan sikeres eredményt jelentett a Windows Restore-próbához képest; tesztelt csomag: [Actions-artefaktum 11874633631](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38524793323/artifacts/11874633631), SHA-256 `87f8215c95d8f8ecd5704600f54e97514fc62c9cc01989251ba6b01e0486eb40`. Külön macOS JSON/ZIP nem érkezett, ezért ez felhasználói smoke-test jelentés; a darabszámok és archívumhash-ek ezen a platformon nincsenek külön ellenőrizve.
- A felhasználó 2026-10-14-én a következő verziónak az **1.0.0 stabil** változatot választotta. A `release/1.0.0-candidate` PR csak belső verziómetaadatot és kiadási tervet módosít; ez nem publikálás vagy készre nyilvánítás. A PR #77 `42ef450cb9b217ba01906ac4187696a72f1faf9b` jelölt-revízióján a [`Tests` run 38525955324](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38525955324) és [`Desktop beta builds` run 38525955034](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38525955034) PASS; a Windows és macOS csomagolt self-test sikeres. Artefaktumok: Windows ID `11875553124`, SHA-256 `30b8ca1eab589a76eabcc318200cb58d8a142b3a9706f5eec00166895ff5aca3`; macOS ID `11875736934`, SHA-256 `03c488fbb064bd13fb25f33707aa39680b6434ca8949fa6e77270173f3bae968`. A tiszta gépes próbák, valós fájlrendszer-kör, végleges kiadási megjegyzések/README és az aláírás/notarizálás vagy aláíratlan stabil csomag elfogadása még kiadási kapu. A nyitott #3/#4 funkciók nincsenek az 1.0.0 ígéretei közé sorolva.
- A `1.0.0` kiadásjelölt About ablaka a felhasználói képernyőképen `VERSION 1.0.0 · BETA` jelölést mutat. A jelölt még nem stabil kiadás; a végleges 1.0.0 csomagnál a hard-coded `BETA` feliratot el kell távolítani, majd új builden ellenőrizni. A jelölt Windows-csomag továbbra is unsigned.

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
| [#63](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/63) | Main-SHA-hoz kötött roadmap-evidencia és dokumentációfrissítési szabály | README-k és terv egyeztetve |
| [#64](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/64) | Szigorú UTF-8 config-preview provenancia | Tesztelt preview; általános encoding-felismerés továbbra sincs |
| [#65](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/65) | Hibás ReaPack override partial státusza és növekvő INI-olvasáskorlát | 226 helyi teszt; két PR CI-folyamat PASS |
| [#66](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/66) | Read-only inspection-limit összegzés CLI-ben és GUI-ban | 229 helyi teszt; kézi GUI továbbra NOT RUN |
| [#67](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/67) | ReaScript függőségfeloldás Custom Actionökben | 232 helyi teszt; REAPER runtime továbbra NOT RUN |
| [#68](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/68) | Kis-/nagybetűs scriptútvonal-eltérés felülvizsgálatra jelölése | 234 helyi teszt; pontos fájlnévegyezés szükséges |
| [#69](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/69) | Release readiness és roadmap frissítése `5fa9738` mainhez | Dokumentációs PR; PR CI és merge utáni main CI PASS |
| [#70](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/70) | Windows >260 karakteres forrásútvonal-mentés és OneDrive-/lokalizált Asztal alapérték | Merge: `c1763a8`; PR CI Tests 6/6 és Desktop builds 2/2 PASS; kézi Windows 11 x64 smoke-test: Scan/Preview, MIDI Audit, ReaPack Audit és Backup PASS; Verify UI PASS; az akkori build Restore-ja FAIL volt |
| [#73](https://github.com/RobCZart82/REAPER-TimeCapsule/pull/73) | Windows extended-length útvonalú restore staging és 259 karakter feletti célútvonalak támogatása | Merge: `e4e25c8`; Tests run 38516327510 és Desktop beta builds run 38516327518 PASS; Windowsos szintetikus regresszió PASS; PR #73 Windows Actions-buildjén valós profil Restore PASS: 7 035 restored / 32 review / 0 legacy-skipped / 0 omission; a `teszt2-zip.zip` CRC és mind a 7 067 SHA-256 PASS; File policies és privát JSON-export PASS (7 035 keep / 32 review / 12 regenerate / 2 exclude); a PR #73 macOS Actions-artefaktumával felhasználói smoke-test: minden felsorolt művelet PASS (macOS verzió külön nincs rögzítve) |

Ezeket ne nyissuk újra reprodukció nélkül. Az összes egyszerű ciklus felsorolása,
általános encoding-felismerés és teljes build-reprodukálhatóság nincs megvalósítva.

## Legutóbbi repository-felülvizsgálat

A 2026-10-12-i felülvizsgálat a main kódját, CLI/GUI belépési pontokat,
archiválást/restore-t, auditokat, migrációt/staginget, build/CI konfigurációt és
dokumentációs állapotot vizsgálta. A változtatás előtti macOS suite: **220 teszt OK**;
a config-provenance változtatás utáni suite: **222 teszt OK**.
A config-preview külön forrás/cél kódolási provenanciát ad (szigorú UTF-8,
BOM, bájtszám, fallback nélkül); hibás UTF-8/UTF-16/legacy bemenet továbbra leállítja
a preview-t és staginget. Ez nem általános encoding-felismerés. Kézi tisztagépes és
REAPER-runtime elfogadás ettől még NOT RUN. A szintetikus tesztek privát profilt nem használnak.

A 2026-10-13-i felülvizsgálatkor nincs új main-változás a PR #64 után, nincs
nyitott PR; #3/#4 továbbra nyitott. A main Tests és Desktop builds PASS.
A helyi kiinduló suite **222 teszt OK**. Reprodukált új hibamód: explicit hibás
ReaPack auto-install override érvényes öröklésként jelent meg. Javítás után a
rekord kihagyott, a profil partial és titokmentes számlálófigyelmeztetést ad;
a felismert részleges repository-formátum leltára nem keres URL-t elutasított mezőkben;
a hárommezős legacy rekord és 0/1/2 továbbra támogatott. A profilolvasó és URL-fallback
méretellenőrzés után növekvő INI olvasása is korlátozott lett. Szintetikus
regressziókkal a helyi suite **226 teszt OK**. Ez nem runtime vagy tisztagépes elfogadás.

A következő fejlesztés a 4. lépés GUI/CLI limitösszegzése: a csak tájékoztató
`inspection-limits` parancs és az Inspection limits… GUI-gomb a tényleges kód-
konstansokból mutatja a limiteket, profilolvasás/beállításváltoztatás nélkül.
Kiinduló main: PR #65, mindkét CI PASS. Helyi suite: **229 teszt OK**;
a CLI headless/olvasásmentes működése, a konstansok követése és a GUI-jelentés
megőrzése tesztelt. Kézi GUI/tisztagépes elfogadás továbbra NOT RUN.

A következő MIDI-regresszió igazolta: a támogatott ReaScript ID-k menühivatkozásként
feloldódtak, Custom Action függőségként viszont unverified státuszt kaptak.
A javítás mindkét támogatott RS-formát azonos action sectionben keres, hiányzó
vagy más sectionben lévő regisztrációt missing-dependencies státusszal jelent.
Hibás RS és SWS token továbbra unverified; scriptfuttatás/runtime nincs.
A javítás előtti negatív kontroll hibázott, utána **232 helyi teszt OK**.
Ez a 4. lépés regisztrációformáinak célzott bővítése, nem #3 runtime-teljesítés.

A scriptútvonalak új negatív kontrollja kimutatta, hogy case-only eltérés is
biztosan mentett fájlként jelent meg. A javítás pontos egyezést kér, eltérő
kis-/nagybetűt `case-mismatch-requires-review` script-issue-ként jelez;
relatív Scripts-bázis és Windows elválasztó továbbra támogatott.
Helyi suite: **234 teszt OK**. Platformfüggő runtime-feloldás nincs igazolva.

## 2026-10-14-i release-előkészítési pillanatkép és PR #73 utófrissítés

A felhasználói Windows 11 x64 képernyőképen a Scripts alatti fájlútvonal 263 karakteres volt;
a beta.2 `Scan / Preview` művelete `WinError 3`-mal leállt. A PR #70 megoldotta a Windows
extended-length útvonalas forrásbejárást és mentésolvasást; a Windows known-folder API
a OneDrive-ra átirányított, magyar nevű Asztal-mappát állítja be alapértelmezett
visszaállítási célként. A PR Windows/macOS/Ubuntu CI és csomagolt alkalmazás-ellenőrzése PASS.
Kézi Windows-teszt (2026-10-14): Windows 11 x64, a tényleges REAPER settings mappán; a felhasználó a PR #70 kódját tartalmazó [desktop-beta-windows-latest Actions-artefaktumot](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38513240558/artifacts/11870727714) futtatta (artifact ID `11870727714`, build commit `0a23f23e25fefd6d0e6dc6e95241ed1e5fd8a32f`, letöltött Actions-artefaktum SHA-256 `5a8719d4e91272da6db3ccbe0d8748243751368ecac83ca2230011dd50318b5b`; ez az artefaktum-zip digestje). Lépések: Scan / Preview, MIDI Audit, ReaPack Audit, Backup a `testing-zip.zip` fájlba, majd Verify és a teljes JSON-jelentés mentése. Mindegyik művelet sikeresen lefutott. A Verify-jelentés mentett/tárolt leltára egyaránt 7 035 keep és 32 review; policy-változás és inspection omission nincs, 12 regenerate és 2 exclude elem kihagyottként szerepel. A Backup ZIP-tartalmának ellenőrzése: `zipfile.testzip()` hibát nem talált, a schema 2 / beta.2 manifest 7 067 bejegyzésének SHA-256 mind egyezett, váratlan ZIP-tétel nem volt, a korábban problémás hosszú útvonalú Lua-fájl jelen volt. Várt és tényleges eredmény: az öt UI-művelet befejeződik, a manifest és az archivált fájlhash-ek egyeznek; **PASS**. Ez célzott, felhasználói gépen végzett smoke-test és archive-integritás ellenőrzés, nem tisztagépes vagy teljes release-elfogadás. A PR #70 régi teszt-buildjén a Restore UI a rövid, 49 karakteres célmappa ellenére FAIL-lel állt le: `Recovery path exceeds conservative filesystem capacity`. A ZIP leghosszabb relatív útvonala 254 karakter; 13 végső és 85 ideiglenes staging-útvonal haladta meg a régi 259 karakteres preflight-korlátot (max. 311, illetve 344 karakter). A PR #73 ezt a korlátot javítja: az extended-length staging és a 255 karakteres komponenskorlát mellett 32 760 UTF-16 egységig engedett teljes útvonal CI-ben tesztelt. A felhasználó megerősítette, hogy a PR #73 friss Windows Actions-buildjét futtatta. Restore után a képernyőkép `Complete report saved` állapotot, a mentett JSON pedig `restored_portable=7035`, `isolated_for_review=32`, `legacy_cache_skipped=0`, `inspection_omissions=[]` értékeket mutat. A `teszt2-zip.zip` archívum CRC-ellenőrzése PASS; a schema-2 manifest 7 067 fájljának mindegyik SHA-256 értéke egyezett, hiányzó vagy hash-eltérő fájl nélkül. Ez a régi beta.2 Restore FAIL utáni célzott kézi újrateszt **PASS**; a publikált beta.2 kiadás változatlan.

- macOS kézi smoke-test (felhasználói jelentés, 2026-10-14): a felhasználó szerint a Windows-próbán végigvett műveletek — Scan / Preview, MIDI Audit, ReaPack Audit, Backup, Verify, Restore, File policies és privát JSON-export — mind sikeresek voltak a PR #73 [macOS Actions-artefaktumával](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38516327518/artifacts/11872227935) (artifact ID `11872227935`, PR-head `c7e216dc668aced2578fff66d2c61fe6f64b5eed`, SHA-256 `87a783f52da62dd996de35522cb01e1f96a7a723804782870942a8be7904a5a2`). macOS-verziót a felhasználó nem adott meg; külön macOS JSON-jelentés vagy archívum-integritási eredmény nem érkezett, ezért a Windows számlálói nem vonatkoznak erre a próbára.

A PR #73 merge-commitja az ellenőrzött main `e4e25c82daec1316364669c312fddbdb370e0c9c`. A PR #73 ellenőrzései: Tests run 38516327510 és Desktop beta builds run 38516327518; mindkettő sikeres. A csomagolt CI-artefaktum nem publikált vagy tisztagépen elfogadott release-csomag. A célzott, felhasználói gépen végzett GUI-próbák PASS; a tisztagépes telepítés, izolált REAPER-runtime és valódi FAT/exFAT/hálózati kötet teszt továbbra sincs rögzítve.



A kiadott legfrissebb verzió továbbra is v0.9.0-beta.2. A `pyproject.toml`
verziója `0.9.0b2`, a felhasználói útmutatók és README-k is a beta.2
felületet írják le; egy új release verzió, release notes, guide/PDF-egyeztetés és
candidate-tag még nincs elkészítve. Kézi GUI/clean-machine, isolated REAPER-runtime
és valódi FAT/exFAT/hálózati kötet tesztek nincsenek rögzítve. Ezért a main CI
zöldsége önmagában nem teszi publikálhatóvá a következő release-t.

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
| 3 | **Fájlrendszer-validálás — nyitott** (TC-008/015/017/020) | A PR #73 szintetikus Windows CI-regressziója és a felhasználó PR #73 builddel végzett valós archívumos Restore-újratesztje (>259 karakteres restore-útvonal, PASS) elkészült. Továbbra is vizsgálandó a valódi FAT/exFAT és kiválasztott hálózati kötet, ENOSPC/jogosultsági hiba/megszakítás; nincs csendes kihagyás/felülírás, unsupported eset leáll. A nem validált köteteket a kiadási támogatási körből ki kell zárni vagy korlátként egyértelműen jelölni. |
| 4 | **Célzott fejlesztés — részben kész** (TC-007/013/016/018, külső #8/#15/#16/#19) | MIDI-gráf, MIDI/ReaPack encoding-diagnosztika és config encoding-provenance kész. Következő: regisztrációformák és hibás/olvashatatlan bemenetek; GUI/CLI limitösszegzés kész. Nagy registry benchmark után döntsünk SQL-optimalizálásról; read-only/deadline/cancel megmarad. Csak reprodukált hibára algoritmusjavítás. |
| 5 | **1.0.0 dokumentáció és kiadás — kész; következő kiadásnál ismétlendő** (TC-016/022/024) | v1.0.0 2026-10-14-én publikálva. EN/HU README, About, release notes, GPL/runtime notice, platformmanifestek és 7 asset checksum egyeztetve. Upstream licencek rögzítése külön reprodukálhatósági feladat. |
| 6 | **Következő kiadás fennmaradó validálása — nyitott** | A v1.0.0 CI és csomagolt self-test PASS; célzott Windows valósprofil-teszt PASS, macOS GUI-teszt felhasználói jelentése PASS. Tisztagépes telepítés/első indítás, valódi FAT/exFAT/hálózati kötet, jogosultsági/ENOSPC/megszakítási kör továbbra NOT RUN. Következő kiadás előtt ezekhez kézi bizonyíték vagy támogatási korlátozás szükséges. |
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
| TC-017 | Részben | Windows extended-length forrásbejárás, backup és restore staging; PR #73 szintetikus CI-regresszióval igazolja a >259 karakteres végső restore-útvonalat. A felhasználó PR #73 builddel végzett valós profil/archive Restore-újratesztje PASS. Szokatlan fájlrendszer/alias-validálás és valódi FAT/exFAT/hálózati kötet teszt még nyitott. |
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
| #16 | Részben hasznos kódolási kockázat | Érvényes UTF-8 először sikeresen dekódolódik; cp1252 csak UnicodeDecodeError után jön. Nem változtat archivált bájtokat, de sérült/nem támogatott encoding félreértelmezett leltárt adhat. PR #59: MIDI-dekódolási figyelmeztetés; PR #60: ReaPack cp1252 fallback notes és partial státusz; UTF-8/BOM/legacy/sérült bájt fixture-ek. Config-migráció szigorú UTF-8 provenanciája kész; általános encoding-felismerés külön nyitott. |
| #17 | Cáfolt None-kezelési hiány | Mind az action-, mind a menüolvasó hívó `contents is not None` ellenőrzést használ. Olvashatatlan bemenet jelentett probléma, nem bizonyított AttributeError. |
| #18 | Nem igazolt Linux-default bug | A fix `~/.config/REAPER` alapútvonal létezik a kódban, de a jelentés nem igazol alternatív REAPER-konvenciót. Későbbi opt-in felderítéshez hivatalos/eldobható REAPER-bizonyíték, portable/XDG eset és explicit felhasználói forrásválasztás kell. |
| #19 | Dokumentációban már megoldott, GUI/CLI javítható | `RESOURCE_BUDGETS.md` tartalmazza a 200000 rekord / 200001 ZIP-member / 8 GiB / 32 GiB / 16 MiB / 64 MiB limiteket. Egységes felhasználói limitösszegzés még hasznos. |


## Kiadás utáni ikoncsere — 2026-10-22

A felhasználó új Reaper-Floppy ikoncsomagja lecseréli az alkalmazás ICO/ICNS,
Tk ablakikon és About floppy PNG erőforrásait; az SVG-forrás is frissül.
Az About elrendezése, GYR-logója, szignója és szövege változatlan.
Ez main-fejlesztés és tesztbuild, nem új publikált release. A Finder/Dock/Explorer
megjelenés és ikoncache kézi ellenőrzése a friss csomaggal még szükséges.
