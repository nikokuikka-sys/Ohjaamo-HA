#!/usr/bin/env python3
"""
Aja kaikki tarkistukset: python3 test/aja.py

Kolme vaihetta, ja jokainen kertoo mita se MITTASI:

  1. Kaantyminen — jokainen Python-tiedosto jasentyy (`py_compile`) ja jokainen
     JSON on validia.
  2. Nimivartija — vanhaa nimea ei ole jaanyt koodiin, teksteihin, JSONiin,
     tiedostonimiin eika dokumenttien siirtymalohkojen ulkopuolelle. Vartija
     sabotoidaan ensin: jos se ei nae omia vikojaan, se on vain vaite.
  3. Sopimustestit — integraatio NOSTETAAN oikeaa Home Assistantia vasten ja
     mitataan mita se teki: kuusi entiteettitunnusta, palvelimen polku ja otsake,
     ja osoitteen vaihto ilman uudelleenasennusta.

🔴 Vaihe 3 vaatii paketit `homeassistant` ja `pytest-homeassistant-custom-component`.
Jos ne puuttuvat, se OHITETAAN ja siita kerrotaan — ohitettua vaihetta ei lasketa
lapimenneeksi. Asennus: pip install homeassistant pytest-homeassistant-custom-component
"""
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path

JUURI = Path(__file__).resolve().parent.parent


def otsikko(teksti: str) -> None:
    print(f"\n{'─' * 70}\n{teksti}\n{'─' * 70}")


def vaihe1_kaantyminen() -> bool:
    otsikko("1/3  KAANTYMINEN")
    paha = 0
    pyt = sorted(JUURI.rglob("*.py"))
    pyt = [p for p in pyt if "__pycache__" not in p.parts]
    for p in pyt:
        try:
            py_compile.compile(str(p), doraise=True, cfile=None)
        except py_compile.PyCompileError as e:
            print(f"  🔴 {p.relative_to(JUURI)}: {e.msg.splitlines()[0]}")
            paha += 1
    jsonit = sorted(JUURI.rglob("*.json"))
    jsonit = [p for p in jsonit if "__pycache__" not in p.parts
              and ".pytest_cache" not in p.parts]
    for p in jsonit:
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  🔴 {p.relative_to(JUURI)}: {e}")
            paha += 1
    if paha:
        print(f"  🔴 {paha} virhetta")
        return False
    print(f"  ✅ {len(pyt)} Python-tiedostoa kaantyy, {len(jsonit)} JSON validia")
    return True


def vaihe2_nimivartija() -> bool:
    otsikko("2/3  NIMIVARTIJA (sabotoidaan ensin)")
    vartija = JUURI / "test" / "nimivartija.py"
    sab = subprocess.run([sys.executable, str(vartija), "--sabotaasi"],
                         capture_output=True, text=True)
    osui = sab.stdout.count("✅ osui")
    vihreat = sab.stdout.count("✅ vihrea")
    if sab.returncode != 0:
        print(sab.stdout)
        print("  🔴 vartija ei nae omia vikojaan — tuloksiin ei voi luottaa")
        return False
    print(f"  ✅ sabotaasi: {osui} vikaa havaittu, {vihreat} puhdasta tapausta vihreana")

    ajo = subprocess.run([sys.executable, str(vartija)], capture_output=True, text=True)
    print("  " + (ajo.stdout.strip().replace("\n", "\n  ") or "(ei tulostetta)"))
    return ajo.returncode == 0


def vaihe3_sopimustestit() -> bool | None:
    otsikko("3/3  SOPIMUSTESTIT (ajetaan Home Assistantia vasten)")
    try:
        import homeassistant  # noqa: F401
        import pytest_homeassistant_custom_component  # noqa: F401
    except ImportError as e:
        print(f"  ⚠️  OHITETTU — paketti puuttuu: {e.name}")
        print("     Nama testit ovat ainoa takuu entiteettitunnuksista ja")
        print("     palvelimen sopimuksesta. Ilman niita ne ovat vain vaite.")
        print("     pip install homeassistant pytest-homeassistant-custom-component")
        return None
    from homeassistant.const import __version__ as ha_versio
    print(f"  Home Assistant {ha_versio}")
    ajo = subprocess.run(
        [sys.executable, "-m", "pytest", "test/test_sopimus.py", "-q", "-p", "no:randomly"],
        cwd=str(JUURI),
    )
    return ajo.returncode == 0


if __name__ == "__main__":
    tulokset = {
        "kaantyminen": vaihe1_kaantyminen(),
        "nimivartija": vaihe2_nimivartija(),
        "sopimustestit": vaihe3_sopimustestit(),
    }
    otsikko("YHTEENVETO")
    paha = False
    for nimi, tulos in tulokset.items():
        if tulos is None:
            print(f"  ⚠️  {nimi}: OHITETTU (ei ajettu — ei siis lapimennyt)")
        elif tulos:
            print(f"  ✅ {nimi}")
        else:
            print(f"  🔴 {nimi}")
            paha = True
    sys.exit(1 if paha else 0)
