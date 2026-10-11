# Native filename capsules / Natív fájlnevek

## English

Portable schema-2 backup remains the default and refuses nonportable names before creating an archive. Native-name backup is an explicit alternative for names such as `presets/au-discodsp: OB-Xd-builtin.ini` on macOS:

```
python -m reaper_timecapsule backup capsule.zip --source /path/to/REAPER --native-names
python -m reaper_timecapsule verify capsule.zip
python -m reaper_timecapsule restore capsule.zip /new/recovery-folder
```

The GUI offers an explicit native-name retry only after a portable backup reports incompatible filenames. Declining creates no archive. Schema 3 stores payloads as canonical `objects/000000.bin` ZIP members; original relative names remain manifest data. Checksums, current restore policies, link exclusion, licence/credential exclusions and no-overwrite publication still apply. Native mode preserves **selected keep/review resources**, not excluded licences or regenerated caches. No original file is renamed. Older builds cannot read schema 3.

Original-name restore requires the source platform and a conservative collision-free namespace. Files still go into a **new staging folder**, under `REAPER/` or `NeedsReview/`; the live resource folder is never modified. Windows does not receive names containing colons, reserved names or other incompatible characters.

For another platform, or case/Unicode collisions, explicitly recover under portable object names:

```
python -m reaper_timecapsule restore capsule.zip /new/recovery-folder --portable-names
```

All recovered files are isolated under `NeedsReview/RecoveredResources/`. `RESTORE_REPORT.json` pairs each original name with its actual recovered path, checksum and effective policy. The bytes and original spelling are recoverable; scripts and menus may still reference original paths and are **not automatically rewritten or activated**. This option is currently available through the CLI. The report is private local data and may contain personal filenames. Backslashes, NUL, empty/dot/traversal components and control/surrogate characters are unsupported; an unsupported name fails rather than silently dropping a file. This is a resource migration capsule, not a disk image or a transactionally consistent live REAPER snapshot.

## Magyar

A hordozható, 2-es sémájú mentés marad az alapértelmezés: a nem hordozható neveket még az archívum elkészítése előtt elutasítja. A natív fájlneves mentés külön választható lehetőség például a macOS alatt előforduló `presets/au-discodsp: OB-Xd-builtin.ini` névhez:

```
python -m reaper_timecapsule backup capsule.zip --source /path/to/REAPER --native-names
python -m reaper_timecapsule verify capsule.zip
python -m reaper_timecapsule restore capsule.zip /new/recovery-folder
```

A GUI csak az inkompatibilis fájlnevek miatti hordozható mentési hiba után ajánlja fel a külön jóváhagyandó natív újrapróbálást. Elutasításkor nem készül archívum. A 3-as séma a tartalmat szabályos `objects/000000.bin` ZIP-bejegyzésekben tárolja; az eredeti relatív nevek a jegyzék adatai maradnak. Az ellenőrzőösszegek, az aktuális visszaállítási szabályok, a hivatkozások és licencek/hitelesítő adatok kizárása, valamint a felülírás nélküli közzététel továbbra is érvényes. A natív mód a **kiválasztott keep/review erőforrásokat** őrzi meg, nem a kizárt licenceket vagy újragenerálandó gyorsítótárakat. Az eredeti fájlok nem kapnak új nevet. A régi alkalmazásverziók nem olvassák a 3-as sémát.

Az eredeti nevű visszaállítás azonos forrásplatformot és konzervatív, ütközésmentes névteret követel. A fájlok továbbra is **új előkészítő mappába**, a `REAPER/` vagy `NeedsReview/` alá kerülnek; a valódi resource mappát nem módosítjuk. Windowsra nem kerülnek kettőspontos, fenntartott vagy egyéb inkompatibilis nevek.

Más platformhoz vagy kis-/nagybetűs, illetve Unicode-ütközés esetén külön kérhető a hordozható objektumneves kinyerés:

```
python -m reaper_timecapsule restore capsule.zip /new/recovery-folder --portable-names
```

Minden kinyert fájl a `NeedsReview/RecoveredResources/` alatt marad elkülönítve. A `RESTORE_REPORT.json` az eredeti nevekhez rendeli a tényleges kinyerési útvonalat, az ellenőrzőösszeget és az aktuális szabályt. A fájlbájtok és az eredeti névírás visszanyerhetők; a scriptek és menük továbbra is hivatkozhatnak eredeti útvonalakra, ezeket **nem írjuk át és nem aktiváljuk automatikusan**. Ez a lehetőség jelenleg parancssorból érhető el. A jelentés helyi magánadat, személyes fájlneveket is tartalmazhat. A fordított perjel, NUL, üres/pont/szülőmappa-komponens, illetve vezérlő- vagy surrogate-karakter nem támogatott; az ilyen név hibát okoz, nem csendes kihagyást. Ez erőforrás-költöztetési kapszula, nem lemezkép vagy az élő REAPER tranzakciósan konzisztens pillanatképe.
