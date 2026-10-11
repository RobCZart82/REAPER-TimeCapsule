# Recovery planning / Helyreállítási terv

## English

```
python -m reaper_timecapsule recovery-plan capsule.zip
```

The command verifies the entire capsule before producing a versioned, read-only MIDI/ReaPack plan. It preserves saved repository order, enabled/disabled states, global options, package versions and pins as **review evidence**, not installation instructions to execute blindly. Missing/unsupported/truncated inventories and unresolved MIDI findings become blockers. Legacy inventories require a fresh audit of staged resources.

The plan separates staged file recovery, script registration review, native/numbered command verification, isolated ReaPack repository review and package availability checks. It never downloads, synchronizes, executes scripts, imports a registry or writes a REAPER resource directory. Hash verification confirms capsule integrity, not publisher identity. Package availability and runtime MIDI behaviour remain unverified.

Before any future automation, use a disposable REAPER installation with synthetic configuration and scripts, independent of the live resource folder. Test action registration, menu commands, missing extensions, pinned-package availability, disabled repositories, native-file recovery and rollback there. This release does **not** claim that those real REAPER integration tests have been performed. The plan records this gate explicitly. Keep its output private because it includes repository/package metadata.

## Magyar

```
python -m reaper_timecapsule recovery-plan capsule.zip
```

A parancs a teljes kapszulát ellenőrzi, mielőtt verziózott, csak olvasó MIDI/ReaPack-tervet ad. A mentett repository-sorrendet, engedélyezett/letiltott állapotokat, globális beállításokat, csomagverziókat és rögzítéseket **ellenőrzési bizonyítékként** őrzi meg, nem vakon végrehajtandó telepítési utasításként. A hiányzó/nem támogatott/csonkolt leltár és a megoldatlan MIDI-megállapítás akadályként jelenik meg. A régi leltárhoz az előkészített erőforrások friss auditja kell.

A terv külön kezeli az előkészítő fájlkinyerést, a scriptregisztráció áttekintését, a natív/számozott parancsok ellenőrzését, az elkülönített ReaPack-repositoryk vizsgálatát és a csomagelérhetőség ellenőrzését. Nem tölt le, nem szinkronizál, nem futtat scriptet, nem importál registryt és nem ír REAPER resource mappába. A hash-ellenőrzés a kapszula sértetlenségét igazolja, nem a közzétevő személyazonosságát. A csomagelérhetőség és a futás közbeni MIDI-viselkedés nincs igazolva.

Későbbi automatizálás előtt külön, eldobható REAPER-telepítés szükséges szintetikus konfigurációval és scriptekkel, az élő resource mappától függetlenül. Ott kell tesztelni a műveletregisztrációt, menüparancsokat, hiányzó bővítményeket, rögzített csomagok elérhetőségét, letiltott repositorykat, natív fájlkinyerést és visszagörgetést. Ez a változtatás **nem állítja**, hogy ezek a valódi REAPER-integrációs tesztek már megtörténtek. A terv külön rögzíti ezt a feltételt. A kimenetet tartsd privátan, mert repository-/csomagmetaadatokat tartalmaz.
