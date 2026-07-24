"""
Ohjaamon sensorit Home Assistantiin.

🔴 VUORIn periaate 24.7.2026: *"emme yrita korvata HA:n automaatioita vaan tarjoamme
tiedon jolla kayttaja kirjoittaa omansa."*

Ilman naita HA-kayttaja joutuu vaihtamaan sovellusta nahdakseen porssihinnan. Naiden
kanssa han voi kirjoittaa oman automaationsa:

    automation:
      - alias: "Pesukone vain halvalla"
        trigger:
          - platform: numeric_state
            entity_id: sensor.ohjaamo_kokonaishinta
            below: 8

🔴 YKSI KUTSU, EI KUUTTA. Minuutin valein kuusi kutsua kymmenelta kayttajalta olisi
3 600 kutsua tunnissa; yksi kutsu tekee siita 600. Kaikki sensorit jakavat saman haun.
"""
from datetime import timedelta
import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import CONF_PALVELIN, CONF_TUNNUS, DOMAIN, OLETUS_PALVELIN

_LOGGER = logging.getLogger(__name__)

# Sensorit: (avain, nimi, yksikko, laji, kuvake)
SENSORIT = [
    ("porssi_snt", "Pörssihinta", "snt/kWh", None, "mdi:transmission-tower"),
    ("kokonaishinta_snt", "Sähkön kokonaishinta", "snt/kWh", None, "mdi:cash"),
    ("halvin_snt", "Halvin tunti tänään", "snt/kWh", None, "mdi:arrow-down-bold"),
    ("kuormitus_pros", "Liittymän kuormitus", "%", None, "mdi:gauge"),
    ("paasulake_a", "Pääsulake", "A", SensorDeviceClass.CURRENT, "mdi:fuse"),
]


async def async_setup_entry(hass, entry, lisaa_entiteetit):
    """Luo sensorit."""
    asetukset = {**entry.data, **entry.options}
    palvelin = str(asetukset.get(CONF_PALVELIN, OLETUS_PALVELIN)).rstrip("/")
    tunnus = asetukset[CONF_TUNNUS]
    istunto = async_get_clientsession(hass)

    async def hae():
        async with istunto.get(
            f"{palvelin}/api/ohjaamo/silta/tila",
            headers={"X-Ohjaamo-Silta": tunnus},
            timeout=20,
        ) as vastaus:
            if vastaus.status != 200:
                raise RuntimeError(f"Ohjaamo vastasi {vastaus.status}")
            return await vastaus.json()

    koordinaattori = DataUpdateCoordinator(
        hass, _LOGGER, name="Ohjaamo", update_method=hae,
        update_interval=timedelta(minutes=5),
    )
    await koordinaattori.async_config_entry_first_refresh()

    lisaa_entiteetit(
        [OhjaamoSensori(koordinaattori, entry, *s) for s in SENSORIT]
        + [OhjaamoRajoitus(koordinaattori, entry)]
    )


class OhjaamoSensori(CoordinatorEntity, SensorEntity):
    """Yksi lukema Ohjaamosta."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, koordinaattori, entry, avain, nimi, yksikko, laji, kuvake):
        super().__init__(koordinaattori)
        self._avain = avain
        self._attr_name = nimi
        self._attr_native_unit_of_measurement = yksikko
        self._attr_device_class = laji
        self._attr_icon = kuvake
        self._attr_unique_id = f"{entry.entry_id}_{avain}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Ohjaamo",
            "manufacturer": "Owella Software",
        }

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get(self._avain)

    @property
    def extra_state_attributes(self):
        """
        🔴 Hintakayra attribuuttina vain porssihinnalle.
        Se on iso lista, ja sen toistaminen jokaisessa sensorissa turvottaisi HA:n
        tilatietokannan turhaan.
        """
        if self._avain != "porssi_snt":
            return None
        d = self.coordinator.data or {}
        return {"hinnat": d.get("hinnat"), "halvin_alkaa": d.get("halvin_alkaa")}


class OhjaamoRajoitus(CoordinatorEntity, SensorEntity):
    """
    Rajoittaako kuormanhallinta juuri nyt?

    🔴 Tama on oma sensorinsa eika attribuutti, koska sen varaan kirjoitetaan
    automaatioita: "jos Ohjaamo rajoittaa, ala kaynnista saunaa".
    """

    _attr_has_entity_name = True
    _attr_name = "Kuormanhallinta rajoittaa"
    _attr_icon = "mdi:speedometer-slow"

    def __init__(self, koordinaattori, entry):
        super().__init__(koordinaattori)
        self._attr_unique_id = f"{entry.entry_id}_rajoittaa"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Ohjaamo",
            "manufacturer": "Owella Software",
        }

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        if not d.get("kuormanhallinta_kaytossa"):
            return "ei käytössä"
        return "rajoittaa" if d.get("rajoittaa") else "ei rajoita"

    @property
    def extra_state_attributes(self):
        d = self.coordinator.data or {}
        return {"syy": d.get("rajoitus_syy"), "kuormitus_pros": d.get("kuormitus_pros")}
