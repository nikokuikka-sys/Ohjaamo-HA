#!/usr/bin/env python3
"""
Vartija: vanhaa nimea ei ole jaanyt sinne minne se ei kuulu.

🔴 TAMA VARTIJA EI ETSI MERKKIJONOA TIEDOSTOSTA. Sellainen vartija mittaa tekstia,
osuu omaan kommenttiinsa ja hälyttää siirtymaohjeesta, joka on kirjoitettu
tarkoituksella. Tama vartija jasentaa:

  * PYTHON-KOODI jasennetaan `ast`:lla. Tunnisteet (nimet, attribuutit, funktiot,
    luokat) eivat saa sisaltaa vanhaa nimea. Merkkijonoista tarkistetaan kaikki
    PAITSI kolme sopimusvakiota, joiden arvot KUULUU olla vanhassa asussa.
    Kommentit ohitetaan: ne selittavat siirtymaa.
  * JSON tarkistetaan arvo arvolta. Repon osoite on sallittu — reposta ei
    nimetty uudelleen.
  * DOKUMENTEISTA tarkistetaan rivi riviltä, ja vanha nimi on sallittu VAIN
    `<!-- SIIRTYMA:ALKU -->` ... `<!-- SIIRTYMA:LOPPU -->` -lohkon sisalla.
    Siellä se on ohje, ei jaanne.

Aja: python3 test/nimivartija.py
Sabotoi: aja `--sabotaasi` — se syottaa jokaiselle tarkistukselle sen vian jota se
etsii ja vaatii osuman. Vartija jota ei ole sabotoitu on vain vaite.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

JUURI = Path(__file__).resolve().parent.parent
VANHA = "ohjaamo"

# 🔴 Sopimusvakiot: naiden ARVOT kuuluu olla vanhassa asussa, koska ne ovat
# palvelimen omistamia. Ks. custom_components/klevra/const.py.
# Naiden arvoja ei vartioi tama tiedosto vaan test_sopimus.py, joka AJAA lahetyksen.
SOPIMUSVAKIOT = {"POLKU_HAVAINNOT", "POLKU_TILA", "OTSAKE_TUNNUS"}

# Repon osoite GitHubissa. Reposta ei nimetty uudelleen, joten osoite on oikein.
SALLITUT_OSOITTEET = (
    "github.com/nikokuikka-sys/ohjaamo-ha",
    "github.com/nikokuikka-sys/Ohjaamo-HA",
)

# 🔴 KAYTTAJALLE NAKYVAT SIIRTYMAMAININNAT — tasmalliset polut, ei kuvioita.
#
# Nama tekstit kertovat kayttajalle, ettei vanha osoite enaa toimi. Ne ovat ohje,
# eivat jaanne, eika niita voi merkita kommentilla koska JSON ei tunne kommentteja.
# Siksi ne luetellaan tassa polku polulta: uusi esiintyma MISSA TAHANSA muualla
# kaataa vartijan yha. Lavea kuvio ("salli kaikki virheteksit") avaisi reian.
SALLITUT_JSON_POLUT = {
    ".config.step.user.data_description.palvelin":
        "kertoo kayttajalle, ettei vanha osoite ole enaa oletus",
    ".config.error.vaara_osoite":
        "404-virhe: kertoo ettei vanha osoite enaa vastaa",
    ".options.error.vaara_osoite":
        "sama virhe asetusnakymassa",
}

ALKU = "<!-- SIIRTYMA:ALKU -->"
LOPPU = "<!-- SIIRTYMA:LOPPU -->"


def _on_sallittu_osoite(teksti: str) -> bool:
    return any(o.lower() in teksti.lower() for o in SALLITUT_OSOITTEET)


def tarkista_python(lahde: str, nimi: str) -> list[str]:
    """Tunnisteet ja merkkijonot. Kommentit ohitetaan (ast ei nae niita)."""
    virheet: list[str] = []
    puu = ast.parse(lahde, filename=nimi)

    # Merkkijonot, jotka saavat sisaltaa vanhan nimen:
    #  1) sopimusvakioiden arvot (palvelimen omistamat polut ja otsake)
    #  2) dokumenttimerkkijonot — ne selittavat siirtyman, kuten kommentit.
    #     🔴 TAMA EI OLE REIKA: docstring ei nay kayttajalle eika kulje verkkoon.
    #     Lokiviesti, virheteksti ja osoite ovat yha kiellettyja.
    sallitut_solmut: set[int] = set()
    for solmu in ast.walk(puu):
        if isinstance(solmu, ast.Assign):
            kohteet = {t.id for t in solmu.targets if isinstance(t, ast.Name)}
            if kohteet & SOPIMUSVAKIOT:
                for ali in ast.walk(solmu.value):
                    sallitut_solmut.add(id(ali))
        if isinstance(solmu, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef)):
            runko = getattr(solmu, "body", None) or []
            if (runko and isinstance(runko[0], ast.Expr)
                    and isinstance(runko[0].value, ast.Constant)
                    and isinstance(runko[0].value.value, str)):
                sallitut_solmut.add(id(runko[0].value))

    for solmu in ast.walk(puu):
        rivi = getattr(solmu, "lineno", "?")

        # 1) Tunnisteet: nimet, attribuutit, funktiot, luokat, argumentit.
        tunniste = None
        if isinstance(solmu, ast.Name):
            tunniste = solmu.id
        elif isinstance(solmu, ast.Attribute):
            tunniste = solmu.attr
        elif isinstance(solmu, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            tunniste = solmu.name
        elif isinstance(solmu, ast.arg):
            tunniste = solmu.arg
        elif isinstance(solmu, ast.alias):
            tunniste = f"{solmu.name} {solmu.asname or ''}"
        if tunniste and VANHA in tunniste.lower():
            virheet.append(f"{nimi}:{rivi}: tunniste sisaltaa vanhan nimen: {tunniste!r}")

        # 2) Merkkijonot.
        if isinstance(solmu, ast.Constant) and isinstance(solmu.value, str):
            if id(solmu) in sallitut_solmut:
                continue
            if VANHA in solmu.value.lower() and not _on_sallittu_osoite(solmu.value):
                lyhyt = solmu.value if len(solmu.value) <= 70 else solmu.value[:70] + "…"
                virheet.append(f"{nimi}:{rivi}: merkkijono sisaltaa vanhan nimen: {lyhyt!r}")

    return virheet


def tarkista_json(teksti: str, nimi: str) -> list[str]:
    virheet: list[str] = []

    def kay(arvo, polku: str) -> None:
        if isinstance(arvo, dict):
            for k, v in arvo.items():
                if VANHA in str(k).lower():
                    virheet.append(f"{nimi}: avain sisaltaa vanhan nimen: {polku}.{k}")
                kay(v, f"{polku}.{k}")
        elif isinstance(arvo, list):
            for i, v in enumerate(arvo):
                kay(v, f"{polku}[{i}]")
        elif isinstance(arvo, str):
            if polku in SALLITUT_JSON_POLUT:
                return
            if VANHA in arvo.lower() and not _on_sallittu_osoite(arvo):
                virheet.append(f"{nimi}: arvo sisaltaa vanhan nimen: {polku} = {arvo!r}")

    kay(json.loads(teksti), "")
    return virheet


def tarkista_dokumentti(teksti: str, nimi: str) -> list[str]:
    """Vanha nimi sallitaan vain siirtymalohkossa tai repon osoitteessa."""
    virheet: list[str] = []
    lohkossa = False
    nahty_lohko = False
    for n, rivi in enumerate(teksti.splitlines(), 1):
        if ALKU in rivi:
            lohkossa, nahty_lohko = True, True
            continue
        if LOPPU in rivi:
            lohkossa = False
            continue
        if lohkossa:
            continue
        if VANHA in rivi.lower() and not _on_sallittu_osoite(rivi):
            virheet.append(f"{nimi}:{n}: vanha nimi siirtymalohkon ULKOPUOLELLA: {rivi.strip()!r}")
    if lohkossa:
        virheet.append(f"{nimi}: {ALKU} ilman {LOPPU}:a")
    if not nahty_lohko:
        virheet.append(f"{nimi}: siirtymalohko puuttuu kokonaan — ei mainintaa nimenvaihdosta")
    return virheet


def kaikki_tiedostot() -> list[Path]:
    tiedostot = []
    for p in sorted(JUURI.rglob("*")):
        if not p.is_file():
            continue
        # Ohitetaan omat ja tyokalujen hakemistot: niiden sisalto ei ole tata repoa.
        if any(osa in ("__pycache__", ".git", ".pytest_cache", ".ruff_cache")
               for osa in p.parts):
            continue
        if p.suffix in (".py", ".json", ".md"):
            tiedostot.append(p)
    return tiedostot


def aja() -> list[str]:
    virheet: list[str] = []
    for p in kaikki_tiedostot():
        nimi = str(p.relative_to(JUURI))
        if nimi.startswith("test/"):
            # Testit nimeavat vanhat tunnukset tarkoituksella (siirtymataulukko).
            continue
        teksti = p.read_text(encoding="utf-8")
        if p.suffix == ".py":
            virheet += tarkista_python(teksti, nimi)
        elif p.suffix == ".json":
            virheet += tarkista_json(teksti, nimi)
        elif p.suffix == ".md":
            virheet += tarkista_dokumentti(teksti, nimi)
        if VANHA in p.name.lower():
            virheet.append(f"{nimi}: TIEDOSTONIMI sisaltaa vanhan nimen")
    for d in JUURI.joinpath("custom_components").iterdir():
        if d.is_dir() and VANHA in d.name.lower():
            virheet.append(f"custom_components/{d.name}: KANSIONIMI sisaltaa vanhan nimen")
    return virheet


# ─────────────────────────────────────────────────────────────────────────────
# SABOTAASI: syota jokaiselle tarkistukselle se vika jota se etsii.
# 🔴 Vartija, jota ei ole sabotoitu, on vaite.

SABOTAASIT = [
    ("python: tunniste", tarkista_python,
     "class OhjaamoSensori:\n    pass\n"),
    ("python: attribuutti", tarkista_python,
     "x = jotain.ohjaamo_tila\n"),
    ("python: merkkijono", tarkista_python,
     'LOGI = "Ohjaamo: kaynnistetty"\n'),
    ("python: vaara vakio sallittuna", tarkista_python,
     'JOKU_MUU = "/api/ohjaamo/silta/havainnot"\n'),
    ("json: arvo", tarkista_json,
     '{"name": "Ohjaamo"}\n'),
    ("json: avain", tarkista_json,
     '{"ohjaamo": 1}\n'),
    # 🔴 Sallittu polku ei saa laventua: sama teksti VAARASSA polussa osuu yha.
    ("json: sallittu teksti vaarassa polussa", tarkista_json,
     '{"config": {"error": {"muu_virhe": "vanha ohjaamo.io ei enaa toimi"}}}\n'),
    # 🔴 Docstring-poikkeus ei saa laventua tavallisiin merkkijonoihin.
    ("python: docstringin jalkeen tavallinen merkkijono", tarkista_python,
     '"""Moduulin docstring: ennen Ohjaamo."""\nVIESTI = "Ohjaamo kaynnistyi"\n'),
    ("dokumentti: lohkon ulkopuolella", tarkista_dokumentti,
     f"{ALKU}\nvanha: sensor.ohjaamo_porssihinta\n{LOPPU}\n\nAsenna Ohjaamo nyt.\n"),
    ("dokumentti: lohko puuttuu", tarkista_dokumentti,
     "# Klevra Home\n\nAsenna se.\n"),
]

VASTASABOTAASIT = [
    ("python: puhdas", tarkista_python,
     'class KlevraSensori:\n    pass\nPOLKU_TILA = "/api/ohjaamo/silta/tila"\n'
     'OTSAKE_TUNNUS = "X-Ohjaamo-Silta"\n'),
    ("python: docstring saa selittaa siirtyman", tarkista_python,
     '"""Klevra Home. Ennen tama oli Ohjaamo; tunnukset muuttuivat."""\n'
     'VIESTI = "Klevra kaynnistyi"\n'),
    ("json: puhdas", tarkista_json,
     '{"name": "Klevra Home",'
     ' "documentation": "https://github.com/nikokuikka-sys/Ohjaamo-HA/blob/main/ASENNUS.md"}\n'),
    ("json: sallittu polku", tarkista_json,
     '{"config": {"error": {"vaara_osoite": "vanha ohjaamo.io ei enaa toimi"}}}\n'),
    ("dokumentti: puhdas", tarkista_dokumentti,
     f"# Klevra Home\n{ALKU}\nvanha sensor.ohjaamo_porssihinta -> uusi\n{LOPPU}\nAsenna.\n"),
]


def sabotoi() -> int:
    paha = 0
    print("SABOTAASI — jokaisen pitaa OSUA:")
    for nimi, tarkistus, lahde in SABOTAASIT:
        osumat = tarkistus(lahde, "<sabotaasi>")
        if osumat:
            print(f"  ✅ osui   {nimi}: {osumat[0]}")
        else:
            print(f"  🔴 EI OSUNUT  {nimi} — vartija ei nae tata vikaa")
            paha += 1
    print("\nVASTASABOTAASI — jokaisen pitaa olla VIHREA:")
    for nimi, tarkistus, lahde in VASTASABOTAASIT:
        osumat = tarkistus(lahde, "<vastasabotaasi>")
        if osumat:
            print(f"  🔴 VAARA HALYTYS  {nimi}: {osumat[0]}")
            paha += 1
        else:
            print(f"  ✅ vihrea  {nimi}")
    return paha


if __name__ == "__main__":
    if "--sabotaasi" in sys.argv:
        sys.exit(1 if sabotoi() else 0)
    loydot = aja()
    if loydot:
        print(f"🔴 NIMIVARTIJA: {len(loydot)} loytoa")
        for v in loydot:
            print(f"  {v}")
        sys.exit(1)
    maara = len([p for p in kaikki_tiedostot() if not str(p.relative_to(JUURI)).startswith("test/")])
    print(f"✅ NIMIVARTIJA: {maara} tiedostoa tarkistettu, vanhaa nimea ei jaanyt")
