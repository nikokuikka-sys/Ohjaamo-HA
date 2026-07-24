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
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta

from .const import (
    DOMAIN, CONF_PALVELIN, CONF_TUNNUS, CONF_ENTITEETIT, CONF_VALI,
    OLETUS_PALVELIN, OLETUS_VALI,
)

_LOGGER = logging.getLogger(__name__)

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
        havainnot = []
        for eid in entiteetit:
            tila = hass.states.get(eid)
            if tila is None:
                # 🔴 Puuttuva entiteetti kerrotaan, ei ohiteta hiljaa: kirjoitusvirhe
                # asetuksissa nayttaisi muuten silta etta anturi on rikki.
                _LOGGER.warning("Ohjaamo: entiteettia %s ei ole olemassa", eid)
                continue
            havainnot.append(
                {
                    "entiteetti": eid,
                    "tila": tila.state,
                    "yksikko": tila.attributes.get("unit_of_measurement"),
                    "nimi": tila.attributes.get("friendly_name") or eid,
                    "laji": tila.attributes.get("device_class"),
                    "muutettu": tila.last_updated.isoformat(),
                }
            )

        if not havainnot:
            return

        try:
            async with istunto.post(
                f"{palvelin}/api/ohjaamo/silta/havainnot",
                json={"havainnot": havainnot},
                headers={"X-Ohjaamo-Silta": tunnus},
                timeout=20,
            ) as vastaus:
                if vastaus.status == 401:
                    _LOGGER.error(
                        "Ohjaamo: tunnus ei kelvannut. Tarkista silta-tunnus Ohjaamon "
                        "laiteasetuksista."
                    )
                elif vastaus.status >= 400:
                    _LOGGER.error("Ohjaamo: palvelin vastasi %s", vastaus.status)
                else:
                    _LOGGER.debug("Ohjaamo: lahetetty %s havaintoa", len(havainnot))
        except asyncio.TimeoutError:
            _LOGGER.warning("Ohjaamo: aikakatkaisu — yritetaan uudelleen %s s kuluttua", vali)
        except Exception as virhe:  # noqa: BLE001
            # 🔴 Silta ei saa koskaan kaataa Home Assistantia. Virhe kirjataan ja
            # seuraava kierros yrittaa uudelleen.
            _LOGGER.warning("Ohjaamo: lahetys epaonnistui: %s", virhe)

    async_track_time_interval(hass, laheta, timedelta(seconds=vali))
    hass.async_create_task(laheta())

    _LOGGER.info(
        "Ohjaamo-silta kaynnistetty: %s entiteettia, valitys %s s, palvelin %s",
        len(entiteetit), vali, palvelin,
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
    await _kaynnista(
        hass,
        palvelin=asetukset.get(CONF_PALVELIN, OLETUS_PALVELIN),
        tunnus=asetukset[CONF_TUNNUS],
        entiteetit=asetukset[CONF_ENTITEETIT],
        vali=int(asetukset.get(CONF_VALI, OLETUS_VALI)),
    )
    entry.async_on_unload(entry.add_update_listener(_paivitettiin))
    return True


async def _paivitettiin(hass: HomeAssistant, entry) -> None:
    """Asetukset muuttuivat -> lataa uudelleen."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Poisto onnistuu aina; ajastin katoaa uudelleenlatauksessa."""
    return True
