# Third-party runtime notices

Time Capsule source is GPL-3.0-only; see LICENSE. No Cockos REAPER executable,
license, proprietary plugin or workflow bundle is distributed by this project.

Standalone builds contain CPython (PSF license and included historical notices),
Tcl/Tk (their upstream license terms), and the PyInstaller bootloader (its GPL
exception/Apache notices). Exact upstream texts are included in runtime-licenses.
The build records interpreter and Tcl/Tk versions and includes additional upstream
notices for OpenSSL, zlib, libffi, bzip2, liblzma/xz and SQLite. Python's license text contains
additional notices for bundled standard-library code; platform/system library
licenses also apply. PyInstaller's build exception is documented at:
https://pyinstaller.org/en/stable/license.html

No warranty is provided. This project is not affiliated with Cockos.

## Visual identity

The application icon uses the REAPER symbol from [Cockos' website header](https://www.reaper.fm/v5img/logo.jpg)
on an original Time Capsule floppy drawing. REAPER marks remain with their owner;
this independent project is not endorsed by Cockos. Creator GYR marks and the
handwritten signature are supplied and authorized by the project owner and have
separate branding rights. See [asset notes](reaper_timecapsule/assets/README.md).

## Build-time notice collection / Build közbeni licencgyűjtés

The collector retries HTTP 429 and selected transient server failures (500, 502,
503, 504) up to four attempts. Exponential backoff and the server's Retry-After
seconds/date are bounded to 30 seconds per wait; requests have a 30-second timeout.
Each response must contain 100 bytes to 1 MiB. Exhausted retries, permanent HTTP
errors, other network errors and invalid response sizes stop the build with the
required notice filename. No required notice is skipped and TLS validation is not
disabled. SOURCES.txt records the requested upstream URLs; retries do not
authenticate content or make mutable upstream references reproducible.

A gyűjtő HTTP 429 és kiválasztott átmeneti szerverhibák (500, 502, 503, 504)
esetén legfeljebb négyszer próbálkozik. Az exponenciális várakozás és a szerver
Retry-After másodperc/dátum értéke várakozásonként legfeljebb 30 másodperc;
a kérés timeoutja 30 másodperc. A válasz 100 bájt és 1 MiB közötti lehet.
Kimerített próbák, végleges HTTP-hiba, más hálózati hiba vagy hibás válaszméret
esetén a build a szükséges licencfájl nevével leáll. Nem hagyunk ki kötelező
licencet és nem kapcsoljuk ki a TLS-ellenőrzést. A SOURCES.txt a kért upstream
URL-eket rögzíti; az újrapróbálás nem hitelesíti a tartalmat és nem teszi
reprodukálhatóvá a változó upstream hivatkozásokat.
