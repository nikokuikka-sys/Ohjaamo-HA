"""
Ohjaamo-silta Home Assistantille.

🔴 TOIMII ILMAN PILVIPALVELUA.
Tama lisaosa ei kayta Nabu Casaa, porttiohjausta eika VPN:aa. Home Assistant lahettaa
valitsemasi entiteettien tilat Ohjaamoon saannollisin valein — yhteys avataan aina
KOTOA ULOSPAIN, joten kotiverkkoon ei avata mitaan.

Asennus ja kaytto: katso OHJE-HOME-ASSISTANT.md
"""
import asyncio
import logging

import voluptuous as vol
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import area_registry, entity_registry
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta

from .const import (
    DOMAIN, CONF_PALVELIN, CONF_TUNNUS, CONF_ENTITEETIT, CONF_VALI,
    OLETUS_PALVELIN, OLETUS_VALI,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]

# 🔴 TYHJA VALINTA = LAHETA KAIKKI (KOSKI 24.7.2026).
#
# Nikon diagnostiikkatiedostossa oli `"entiteetit": []` ja `"entiteetteja": 0`. Yhteys
# toimi, mutta mitaan ei lahetetty — ja kayttajalle se nayttaa TASMALLEEN samalta kuin
# rikkinainen yhteys.
#
# Syy on suunnitteluvirhe: pyysimme kayttajaa valitsemaan entiteetit ENNEN kuin han on
# nahnyt niita Ohjaamossa. Han ei voi tietaa mita valita.
#
# Nyt tyhja valinta tarkoittaa "laheta kaikki mika on jarkevaa". Kayttaja valitsee
# Ohjaamossa mitka pitaa nakyvissa — siella han nakee ne.
# 🔴 ERAKOKO: lahetys pilkotaan. Ohjaamon palvelin hyvaksyy 256 kt, ja 250 entiteettia
# attribuutteineen on arviolta 96 kt — mutta Teslan kaltainen integraatio voi tuoda satoja
# entiteetteja pitkine attribuutteineen, jolloin raja ylittyy.
#
# Ylitys palauttaisi 413:n, eika kayttajalle nakyisi mitaan: lukemat vain eivat
# paivittyisi. Se on sama hiljainen epaonnistuminen jota vastaan koko tama integraatio
# on rakennettu. Pilkkominen poistaa koko riskin riippumatta laitemaarasta.
ERAKOKO = 80

KAIKKI_DOMAINIT = (
    "sensor", "binary_sensor", "switch", "light", "climate",
    "water_heater", "number", "select", "fan", "cover",
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_TUNNUS): cv.string,
                vol.Optional(CONF_PALVELIN, default=OLETUS_PALVELIN): cv.string,
                vol.Required(CONF_ENTITEETIT): vol.All(cv.ensure_list, [cv.entity_id]),
                vol.Optional(CONF_VALI, default=OLETUS_VALI): vol.All(
                    vol.Coerce(int), vol.Range(min=15, max=3600)
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Kaynnista silta."""
    asetukset = config.get(DOMAIN)
    if not asetukset:
        return True

    await _kaynnista(
        hass,
        palvelin=asetukset[CONF_PALVELIN],
        tunnus=asetukset[CONF_TUNNUS],
        entiteetit=asetukset[CONF_ENTITEETIT],
        vali=asetukset[CONF_VALI],
    )
    return True


async def _kaynnista(hass, *, palvelin, tunnus, entiteetit, vali):
    """Yhteinen kaynnistys YAML- ja dialogipolulle."""
    palvelin = palvelin.rstrip("/")
    istunto = async_get_clientsession(hass)

    async def laheta(_nyt=None):
        """Kerää valitut entiteetit ja lahetä ne Ohjaamoon."""
        # Tyhja lista -> kaikki tuetut entiteetit.
        lahetettavat = entiteetit or [
            e for e in hass.states.async_entity_ids()
            if e.split(".")[0] in KAIKKI_DOMAINIT
        ]

        havainnot = []
        for eid in lahetettavat:
            tila = hass.states.get(eid)
            attr = tila.attributes if tila else {}
            if tila is None:
                # 🔴 Puuttuva entiteetti kerrotaan, ei ohiteta hiljaa: kirjoitusvirhe
                # asetuksissa nayttaisi muuten silta etta anturi on rikki.
                _LOGGER.warning("Ohjaamo: entiteettia %s ei ole olemassa", eid)
                continue
            havainnot.append(
                {
                    "entiteetti": eid,
                    "tila": tila.state,
                    "yksikko": attr.get("unit_of_measurement"),
                    "nimi": attr.get("friendly_name") or eid,
                    "laji": attr.get("device_class"),
                    "muutettu": tila.last_updated.isoformat(),
                    # 🔴 Huone ja laitetunnus mukaan (VUORIn ehdotus): ne poistavat
                    # kaksi kasityota Ohjaamon paassa — huoneen asettamisen erikseen
                    # jokaiselle anturille, ja anturien ryhmittelyn laitteiksi.
                    "huone": _alueen_nimi(hass, eid),
                    "laite_id": _laitteen_id(hass, eid),
                    # 🔴 KYVYT — tama on se mika poistaa laitekohtaisen koodauksen.
                    #
                    # Home Assistantilla on jo yleinen malli: `domain` kertoo laitetyypin
                    # (water_heater, climate, switch), `supported_features` on bittimaski
                    # joka kertoo MITA LAITE OSAA, ja attribuutit kertovat rajat
                    # (min_temp, max_temp) ja vaihtoehdot (operation_list).
                    #
                    # Kun lahetamme naman sellaisenaan, Ohjaamo osaa rakentaa ohjauksen
                    # MILLE TAHANSA laitteelle jota HA tukee — myos sellaiselle jota ei
                    # ollut olemassa kun tama koodi kirjoitettiin. Uusi laite ei vaadi
                    # riviakaan uutta koodia kummassakaan paassa.
                    "domain": eid.split(".")[0],
                    "kyvyt": attr.get("supported_features"),
                    # Kaikki attribuutit paitsi kuvat ja pitkat listat: niista tulee
                    # rajat, tilat ja vaihtoehdot ilman etta niita tarvitsee luetella.
                    "attribuutit": {
                        k: v for k, v in attr.items()
                        # 🔴 Rajat tiukennettu: 250 merkkia riittaa rajoihin ja
                        # vaihtoehtoihin. Teslan sijaintihistoria tai kameran
                        # kuvalista veisi kilotavuja kertomatta mitaan hyodyllista.
                        if k not in ("entity_picture", "icon", "attribution",
                                     "supported_features", "friendly_name")
                        and len(str(v)) <= 250
                    },
                }
            )

        if not havainnot:
            return

        # Pilkotaan eriin. Komennot tulevat vastauksessa, joten ne kasitellaan joka erasta.
        for alku in range(0, len(havainnot), ERAKOKO):
            era = havainnot[alku:alku + ERAKOKO]
            await _laheta_era(hass, istunto, palvelin, tunnus, era, vali,
                              osa=(alku // ERAKOKO) + 1,
                              osia=(len(havainnot) + ERAKOKO - 1) // ERAKOKO)

    async def _laheta_era(hass, istunto, palvelin, tunnus, havainnot, vali, osa, osia):
        try:
            async with istunto.post(
                f"{palvelin}/api/ohjaamo/silta/havainnot",
                json={"havainnot": havainnot},
                headers={"X-Ohjaamo-Silta": tunnus},
                timeout=30,
            ) as vastaus:
                if vastaus.status == 401:
                    _LOGGER.error(
                        "Ohjaamo: tunnus ei kelvannut. Tarkista silta-tunnus Ohjaamon "
                        "laiteasetuksista."
                    )
                elif vastaus.status == 413:
                    # 🔴 Kerrotaan tasmallisesti mita tehda. Pelkka "413" ei auta ketaan.
                    _LOGGER.error(
                        "Ohjaamo: lahetys oli liian iso (era %s/%s, %s entiteettia). "
                        "Valitse asetuksista vain tarvitsemasi entiteetit.",
                        osa, osia, len(havainnot),
                    )
                elif vastaus.status >= 400:
                    _LOGGER.error("Ohjaamo: palvelin vastasi %s (era %s/%s)", vastaus.status, osa, osia)
                else:
                    _LOGGER.debug("Ohjaamo: era %s/%s, %s havaintoa", osa, osia, len(havainnot))
                    # 🔴 KOMENNOT SAMASTA VASTAUKSESTA. Nain ohjaus toimii ilman etta
                    # kotiverkkoon avataan mitaan: HA kysyy komennot samalla kutsulla
                    # jolla se lahettaa havainnot. Ohjaamo ei koskaan avaa yhteytta
                    # kotiin — se on koko "ilman pilvipalvelua" -lupauksen ydin.
                    try:
                        data = await vastaus.json()
                    except Exception:  # noqa: BLE001
                        data = {}
                    for komento in (data.get("komennot") or []):
                        await _aja_komento(hass, komento)
        except asyncio.TimeoutError:
            _LOGGER.warning("Ohjaamo: aikakatkaisu — yritetaan uudelleen %s s kuluttua", vali)
        except Exception as virhe:  # noqa: BLE001
            # 🔴 Silta ei saa koskaan kaataa Home Assistantia. Virhe kirjataan ja
            # seuraava kierros yrittaa uudelleen.
            _LOGGER.warning("Ohjaamo: lahetys epaonnistui: %s", virhe)

    async_track_time_interval(hass, laheta, timedelta(seconds=vali))
    hass.async_create_task(laheta())

    _LOGGER.info(
        "Ohjaamo-silta kaynnistetty: %s, valitys %s s, palvelin %s",
        f"{len(entiteetit)} valittua entiteettia" if entiteetit else "KAIKKI tuetut entiteetit",
        vali, palvelin,
    )
    return True

async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """
    Kaynnista silta asetusdialogin kautta.

    🔴 Sama laheytyslogiikka kuin YAML-polussa, mutta asetukset tulevat
    config_entrysta. Molemmat polut tuetaan: YAML toimii yha niille jotka ovat sen jo
    ottaneet kayttoon, eika kenenkaan asennus hajoa paivityksessa.
    """
    asetukset = {**entry.data, **entry.options}

    # 🔴 VUORIn loydos 24.7.2026: ilman tata HA merkitsee integraation epaonnistuneeksi
    # jos palvelin ei satu vastaamaan asennushetkella — EIKA YRITA UUDELLEEN. Kayttaja
    # joutuu poistamaan ja lisaamaan sen kasin, eika mikaan kerro miksi.
    #
    # ConfigEntryNotReady kertoo HA:lle etta kyse on TILAPAISESTA ongelmasta: se yrittaa
    # automaattisesti kasvavin valein. ConfigEntryAuthFailed taas nayttaa kayttajalle
    # "Uudelleentunnistaudu"-napin sen sijaan etta integraatio olisi vain rikki.
    virhe = await _testaa(hass, asetukset)
    if virhe == "tunnus_ei_kelpaa":
        raise ConfigEntryAuthFailed("Ohjaamon tunnus ei kelpaa")
    if virhe:
        raise ConfigEntryNotReady(f"Ohjaamoon ei saada yhteytta: {virhe}")

    await _kaynnista(
        hass,
        palvelin=asetukset.get(CONF_PALVELIN, OLETUS_PALVELIN),
        tunnus=asetukset[CONF_TUNNUS],
        entiteetit=asetukset[CONF_ENTITEETIT],
        vali=int(asetukset.get(CONF_VALI, OLETUS_VALI)),
    )
    # Sensorit: porssihinta ja kuormitus HA:n puolelle, jotta kayttaja voi kirjoittaa
    # omat automaationsa ilman etta hanen tarvitsee vaihtaa sovellusta.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_paivitettiin))
    return True


async def _paivitettiin(hass: HomeAssistant, entry) -> None:
    """Asetukset muuttuivat -> lataa uudelleen."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Poisto onnistuu aina; ajastin katoaa uudelleenlatauksessa."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _testaa(hass, asetukset) -> str | None:
    """Kokeile yhteytta. Palauttaa virhekoodin tai None."""
    istunto = async_get_clientsession(hass)
    palvelin = str(asetukset.get(CONF_PALVELIN, OLETUS_PALVELIN)).rstrip("/")
    try:
        async with istunto.post(
            f"{palvelin}/api/ohjaamo/silta/havainnot",
            json={"havainnot": [{"entiteetti": "test.yhteys", "tila": "0", "nimi": "Yhteystesti"}]},
            headers={"X-Ohjaamo-Silta": asetukset[CONF_TUNNUS]},
            timeout=15,
        ) as vastaus:
            if vastaus.status == 401:
                return "tunnus_ei_kelpaa"
            if vastaus.status >= 400:
                return f"palvelin vastasi {vastaus.status}"
            return None
    except Exception as e:  # noqa: BLE001
        return str(e)[:120]


def _alueen_nimi(hass, entity_id: str) -> str | None:
    """
    🔴 HA:n ALUE = OHJAAMON HUONE (VUORIn ehdotus).

    Ilman tata kayttajan pitaa asettaa huone erikseen jokaiselle anturille. Nikon
    tilissa on 54 laitetta, joten se on 54 muokkausta kasin. Home Assistantissa alue on
    jo asetettu — otetaan se mukana, niin huoneet ovat valmiina ensimmaisesta hetkesta.
    """
    try:
        ent = entity_registry.async_get(hass)
        alueet = area_registry.async_get(hass)
        merkinta = ent.async_get(entity_id)
        if not merkinta:
            return None
        alue_id = merkinta.area_id
        if not alue_id and merkinta.device_id:
            from homeassistant.helpers import device_registry
            laitteet = device_registry.async_get(hass)
            laite = laitteet.async_get(merkinta.device_id)
            alue_id = laite.area_id if laite else None
        if not alue_id:
            return None
        alue = alueet.async_get_area(alue_id)
        return alue.name if alue else None
    except Exception:  # noqa: BLE001
        return None


def _laitteen_id(hass, entity_id: str) -> str | None:
    """Mihin fyysiseen laitteeseen entiteetti kuuluu. Ohjaamo ryhmittaa sen mukaan."""
    try:
        ent = entity_registry.async_get(hass)
        merkinta = ent.async_get(entity_id)
        return merkinta.device_id if merkinta else None
    except Exception:  # noqa: BLE001
        return None


async def _aja_komento(hass, komento) -> None:
    """
    Aja Ohjaamosta tullut komento Home Assistantin palveluna.

    🔴 Palvelu ja kentat tulevat HA:n OMASTA mallista (esim. water_heater.set_temperature),
    joten uusi laitetyyppi toimii ilman muutoksia tahan. Emme tulkitse komentoa emmeka
    muunna sita — valitamme sen sellaisenaan.
    """
    try:
        palvelu = str(komento.get("palvelu") or "")
        entiteetti = str(komento.get("entiteetti") or "")
        if "." not in palvelu or not entiteetti:
            _LOGGER.warning("Ohjaamo: virheellinen komento ohitettu: %s", komento)
            return
        domain, toiminto = palvelu.split(".", 1)
        tiedot = dict(komento.get("tiedot") or {})
        tiedot["entity_id"] = entiteetti
        await hass.services.async_call(domain, toiminto, tiedot, blocking=False)
        _LOGGER.info("Ohjaamo: ajettiin %s -> %s", palvelu, entiteetti)
    except Exception as virhe:  # noqa: BLE001
        # Yhden komennon vika ei saa estaa muita eika kaataa lahetysta.
        _LOGGER.warning("Ohjaamo: komento epaonnistui (%s): %s", komento.get("palvelu"), virhe)
