"""
Diagnostiikkatiedot Home Assistantin laitesivulta.

🔴 VUORIn ehdotus 24.7.2026: ilman tata vianetsinta on arvailua. Kayttaja voi ladata
tiedoston ja lahettaa sen tukeen, jolloin nakyy tasan mita on asetettu ja mita
lahetetaan — ei sita mita han muistaa asettaneensa.

🔴 TUNNUS SALATAAN. Tiedosto paatyy sahkopostiin ja tukijarjestelmiin, joten siina ei
saa olla salasanaa. Sama saanto kuin Ohjaamon tapahtumalokissa.
"""
from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_TUNNUS

SALATTAVAT = {CONF_TUNNUS, "tunnus", "token", "api_key", "password"}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry) -> dict:
    """Kokoa diagnostiikka."""
    asetukset = {**entry.data, **entry.options}
    entiteetit = asetukset.get("entiteetit") or []

    tilat = []
    for eid in entiteetit:
        tila = hass.states.get(eid)
        tilat.append(
            {
                "entiteetti": eid,
                # 🔴 Kerrotaan LOYTYIKO entiteetti. Puuttuva entiteetti on yleisin syy
                # siihen ettei tieto tule perille, ja se nakyy tassa heti.
                "loytyy": tila is not None,
                "tila": tila.state if tila else None,
                "yksikko": tila.attributes.get("unit_of_measurement") if tila else None,
                "laji": tila.attributes.get("device_class") if tila else None,
            }
        )

    return async_redact_data(
        {
            "asetukset": asetukset,
            "entiteetteja": len(entiteetit),
            "loytymatta": sum(1 for t in tilat if not t["loytyy"]),
            "tilat": tilat,
            "ha_versio": getattr(hass.config, "version", None),
        },
        SALATTAVAT,
    )
