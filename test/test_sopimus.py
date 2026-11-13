"""
Sopimustestit: mitataan TAKUU ajamalla, ei merkkijonon esiintymista.

🔴 MIKSI NAMA OVAT ERI TIEDOSTOSSA KUIN NIMIVARTIJA. Nimivartija lukee lahdetta ja
voi kertoa vain, mita koodissa on kirjoitettuna. Nama testit NOSTAVAT Home Assistantin,
asentavat integraation ja lukevat mita HA oikeasti teki: mitka entiteettitunnukset
syntyivat ja mihin osoitteeseen lahetys meni. Vain tama jalkimmainen on takuu.

Ei verkkoa: istunto on valennos. Ei oikeaa Home Assistantia, ei oikeita laitteita.
"""
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

import custom_components.klevra  # noqa: F401  (sidonta patsattavaksi)
import custom_components.klevra.sensor  # noqa: F401
from custom_components.klevra.const import (
    CONF_ENTITEETIT, CONF_PALVELIN, CONF_TUNNUS, CONF_VALI, DOMAIN,
)

# 🔴 TAMA LISTA ON SE LUPAUS, JONKA README ANTAA NIKON AUTOMAATIOILLE.
# Jos tama muuttuu, hanen automaationsa hajoavat. Siksi se on tassa kirjaimellisesti
# eika muodostettuna koodista — muodostettu odotusarvo muuttuisi vian mukana.
ODOTETUT_TUNNUKSET = {
    "sensor.klevra_porssihinta",
    "sensor.klevra_sahkon_kokonaishinta",
    "sensor.klevra_halvin_tunti_tanaan",
    "sensor.klevra_liittyman_kuormitus",
    "sensor.klevra_paasulake",
    "sensor.klevra_kuormanhallinta_rajoittaa",
}

# 🔴 Palvelimen sopimus. Nama OVAT vanhassa asussa tarkoituksella: polku ja otsake
# ovat palvelimen omistamia, ja niiden palvelinpaa elaa poistuvassa
# `src/ohjaamo/`-moduulissa. Jos tama testi kaatuu siihen, etta koodi on nimennyt
# ne uudelleen, kyse ei ole siistimisesta vaan rikkoutuneesta yhteydesta.
ODOTETTU_POLKU_POST = "/api/ohjaamo/silta/havainnot"
ODOTETTU_POLKU_GET = "/api/ohjaamo/silta/tila"
ODOTETTU_OTSAKE = "X-Ohjaamo-Silta"

PALVELINTILA = {
    "porssi_snt": 7.5, "kokonaishinta_snt": 11.2, "halvin_snt": 3.1,
    "kuormitus_pros": 42, "paasulake_a": 25,
    "kuormanhallinta_kaytossa": True, "rajoittaa": False, "rajoitus_syy": None,
    "hinnat": [1, 2, 3], "halvin_alkaa": "2026-11-13T02:00:00",
}


class ValeVastaus:
    def __init__(self, status=200, data=None):
        self.status = status
        self._data = data or {}

    async def json(self):
        return self._data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class ValeIstunto:
    """Valeistunto. Kirjaa jokaisen kutsun, ei avaa verkkoyhteytta."""

    def __init__(self):
        self.postit: list[tuple[str, dict]] = []
        self.getit: list[tuple[str, dict]] = []

    def post(self, url, **kw):
        self.postit.append((url, kw))
        return ValeVastaus(200, {"komennot": []})

    def get(self, url, **kw):
        self.getit.append((url, kw))
        return ValeVastaus(200, PALVELINTILA)


# 🔴 KOLME KOHTAA, EI YKSI. Molemmat moduulit tekevat `from ... import
# async_get_clientsession`, joten sidonta tapahtuu moduulin latauksessa. Pelkka
# apumoduulin patsaaminen EI riita, jos moduuli on jo ladattu — mitattu: testi
# avasi oikean DNS-kyselyn (`aiodns.error.DNSError`) ja asennus kaatui.
PATSIT = (
    "homeassistant.helpers.aiohttp_client.async_get_clientsession",
    "custom_components.klevra.async_get_clientsession",
    "custom_components.klevra.sensor.async_get_clientsession",
)


class _Patsit:
    """Patsaa kaikki kolme sidontaa yhtaaikaa."""

    def __init__(self, istunto):
        self._patsit = [patch(p, return_value=istunto) for p in PATSIT]

    def __enter__(self):
        for p in self._patsit:
            p.start()
        return self

    def __exit__(self, *a):
        for p in self._patsit:
            p.stop()
        return False


@pytest.fixture
def istunto():
    return ValeIstunto()


async def _asenna(hass, istunto, palvelin="https://eka.invalid"):
    entry = MockConfigEntry(
        domain=DOMAIN, title="Klevra Home",
        data={CONF_TUNNUS: "testitunnus", CONF_PALVELIN: palvelin, CONF_ENTITEETIT: []},
    )
    entry.add_to_hass(hass)
    with _Patsit(istunto):
        ok = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, ok


async def test_kuusi_sensoria_oikeilla_tunnuksilla(hass, istunto):
    """🔴 TAKUU: tasan kuusi sensoria, tasan nama tunnukset."""
    entry, ok = await _asenna(hass, istunto)
    assert ok, "integraatio ei noussut"
    assert entry.state is ConfigEntryState.LOADED

    tunnukset = set(hass.states.async_entity_ids("sensor"))
    assert tunnukset == ODOTETUT_TUNNUKSET, (
        "entiteettitunnukset eivat vastaa READMEn siirtymataulukkoa.\n"
        f"  puuttuu: {sorted(ODOTETUT_TUNNUKSET - tunnukset)}\n"
        f"  ylimaarainen: {sorted(tunnukset - ODOTETUT_TUNNUKSET)}"
    )
    # Jokaisella on lukema, ei pelkka olemassaolo.
    for t in tunnukset:
        assert hass.states.get(t).state not in (None, "", "unknown", "unavailable"), t


async def test_vanhaa_tunnusta_ei_synny(hass, istunto):
    """🔴 Yhteensopivuuskerrosta EI ole, eika sita saa vahingossa syntya."""
    await _asenna(hass, istunto)
    rek = er.async_get(hass)
    vanhat = [e.entity_id for e in rek.entities.values() if "ohjaamo" in e.entity_id]
    assert not vanhat, f"vanhoja tunnuksia syntyi: {vanhat}"


async def test_palvelimen_sopimus_sailyi(hass, istunto):
    """🔴 TAKUU: polku ja otsake mitataan AJAMALLA, ei lukemalla lahdetta."""
    await _asenna(hass, istunto, palvelin="https://eka.invalid")

    assert istunto.postit, "lahetysta ei tapahtunut lainkaan"
    url, kw = istunto.postit[0]
    assert url == f"https://eka.invalid{ODOTETTU_POLKU_POST}", url
    assert ODOTETTU_OTSAKE in (kw.get("headers") or {}), kw.get("headers")
    assert kw["headers"][ODOTETTU_OTSAKE] == "testitunnus"

    assert istunto.getit, "tilaa ei haettu lainkaan"
    assert istunto.getit[0][0] == f"https://eka.invalid{ODOTETTU_POLKU_GET}"
    assert ODOTETTU_OTSAKE in (istunto.getit[0][1].get("headers") or {})


async def test_palvelinosoite_vaihtuu_ilman_uudelleenasennusta(hass, istunto):
    """
    🔴 TAKUU: osoite vaihtuu asetusnakymasta, EIKA integraatiota tarvitse poistaa.

    Tama ei ole reunatapaus: Niko kertoi 13.11.2026, etta osoite vaihtuu kun uusi
    domain rekisteroidaan. Mitataan, etta vaihdon jalkeen lahetys menee UUTEEN
    osoitteeseen ja entry on sama (entry_id ennallaan, entiteetit eivat kadonneet).
    """
    entry, ok = await _asenna(hass, istunto, palvelin="https://eka.invalid")
    assert ok
    alkup_entry_id = entry.entry_id
    assert all(u.startswith("https://eka.invalid") for u, _ in istunto.postit)

    # Asetusnakyma auki ja osoite vaihdetaan.
    with _Patsit(istunto):
        virta = await hass.config_entries.options.async_init(entry.entry_id)
        assert virta["step_id"] == "init", virta
        tulos = await hass.config_entries.options.async_configure(
            virta["flow_id"],
            user_input={
                CONF_PALVELIN: "https://toka.invalid",
                CONF_TUNNUS: "testitunnus",
                CONF_ENTITEETIT: [],
                CONF_VALI: 60,
            },
        )
        await hass.async_block_till_done()

    assert tulos["type"] == "create_entry", tulos
    assert entry.options[CONF_PALVELIN] == "https://toka.invalid"

    # Sama entry, ei poistoa — ja entiteetit ovat yha paikallaan.
    assert entry.entry_id == alkup_entry_id
    assert entry.state is ConfigEntryState.LOADED
    assert set(hass.states.async_entity_ids("sensor")) == ODOTETUT_TUNNUKSET

    # 🔴 Ja ennen kaikkea: lahetys menee UUTEEN osoitteeseen.
    uudet = [u for u, _ in istunto.postit if u.startswith("https://toka.invalid")]
    assert uudet, (
        "osoite vaihtui asetuksissa mutta lahetys menee yha vanhaan — "
        f"kutsutut osoitteet: {[u for u, _ in istunto.postit]}"
    )


async def test_asetusnakyma_on_olemassa(hass, istunto):
    """
    🔴 Ilman tata "Maarita"-nappia ei ole, ja osoitteen vaihto vaatisi poiston.

    Mitattu 13.11.2026: options flow PUUTTUI kokonaan, vaikka ohje lupasi etta
    valintoja voi muuttaa jalkikateen.
    """
    from homeassistant.config_entries import HANDLERS
    kasittelija = HANDLERS.get(DOMAIN)
    assert kasittelija is not None, "config flow -kasittelijaa ei rekisteroity"
    assert kasittelija.async_supports_options_flow(
        MockConfigEntry(domain=DOMAIN, data={})
    ), "integraatiolla ei ole asetusnakymaa"


async def test_puuttuva_integraatio_ei_lataudu(hass):
    """
    Kirjattu mittaus: vanha tallennettu entry, jonka kansio on poissa levylta.

    Nain kayttaytyy Nikon vanha `ohjaamo`-entry nimenvaihdon jalkeen:
    se EI katoa itsestaan, vaan jaa listaan tilaan NOT_LOADED. Siksi README kehottaa
    poistamaan sen kasin.
    """
    entry = MockConfigEntry(
        domain="poistunut_integraatio", title="Vanha",
        data={CONF_TUNNUS: "x", CONF_PALVELIN: "https://eka.invalid", CONF_ENTITEETIT: []},
    )
    entry.add_to_hass(hass)
    ok = await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert ok is False
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert entry in hass.config_entries.async_entries()

    # ...mutta poistaminen onnistuu, vaikka integraatiota ei ole levylla.
    tulos = await hass.config_entries.async_remove(entry.entry_id)
    assert tulos == {"require_restart": False}
