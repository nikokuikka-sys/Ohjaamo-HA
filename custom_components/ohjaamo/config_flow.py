"""
Ohjaamon asetusdialogi Home Assistantissa.

🔴 Miksi tama on olemassa: ilman config_flow'ta kayttajan pitaa muokata
`configuration.yaml`-tiedostoa kasin ja kaynnistaa HA uudelleen. Se on kolme kohtaa
joissa voi epaonnistua (tiedoston loytaminen, sisennys, uudelleenkaynnistys) — ja YAML:n
sisennysvirhe kaataa koko Home Assistantin, ei vain tata lisaosaa.

Taman kanssa asennus on: Asetukset -> Laitteet -> Lisaa integraatio -> Ohjaamo ->
liita tunnus -> valitse entiteetit. Ei tiedostoja, ei uudelleenkaynnistysta.
"""
import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN, CONF_PALVELIN, CONF_TUNNUS, CONF_ENTITEETIT, CONF_VALI,
    OLETUS_PALVELIN, OLETUS_VALI,
)

_LOGGER = logging.getLogger(__name__)


async def _testaa_tunnus(hass, palvelin: str, tunnus: str) -> str | None:
    """
    Kokeile tunnusta ENNEN tallennusta.

    🔴 Vaara tunnus huomataan tassa eika vasta tunnin paasta kun kayttaja ihmettelee
    miksi mitaan ei nay. Palauttaa virhekoodin tai None jos kaikki hyvin.
    """
    istunto = async_get_clientsession(hass)
    try:
        async with istunto.post(
            f"{palvelin.rstrip('/')}/api/ohjaamo/silta/havainnot",
            json={"havainnot": [{"entiteetti": "test.yhteys", "tila": "0", "nimi": "Yhteystesti"}]},
            headers={"X-Ohjaamo-Silta": tunnus},
            timeout=15,
        ) as vastaus:
            if vastaus.status == 401:
                return "tunnus_ei_kelpaa"
            if vastaus.status >= 500:
                return "palvelinvirhe"
            if vastaus.status >= 400:
                return "yhteysvirhe"
            return None
    except Exception as virhe:  # noqa: BLE001
        _LOGGER.debug("Ohjaamo: yhteystesti epaonnistui: %s", virhe)
        return "ei_yhteytta"


class OhjaamoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Ohjattu asennus."""

    VERSION = 1

    def __init__(self) -> None:
        self._tiedot: dict = {}

    async def async_step_user(self, user_input=None):
        """Vaihe 1: tunnus ja palvelin."""
        virheet: dict[str, str] = {}

        if user_input is not None:
            virhe = await _testaa_tunnus(
                self.hass, user_input[CONF_PALVELIN], user_input[CONF_TUNNUS]
            )
            if virhe:
                virheet["base"] = virhe
            else:
                self._tiedot = dict(user_input)
                return await self.async_step_entiteetit()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TUNNUS): str,
                    vol.Optional(CONF_PALVELIN, default=OLETUS_PALVELIN): str,
                }
            ),
            errors=virheet,
            description_placeholders={"ohje": "Ohjaamo → Laitteet → Home Assistant"},
        )

    async def async_step_entiteetit(self, user_input=None):
        """
        Vaihe 2: mitka entiteetit lahetetaan.

        🔴 Kayttaja VALITSEE listalta eika kirjoita nimia kasin. Entiteettien nimet ovat
        pitkia ja virhealttiita (`sensor.varaaja_current_temperature`), ja kirjoitusvirhe
        oli yleisin syy siihen ettei tieto tullut perille.
        """
        if user_input is not None:
            self._tiedot.update(user_input)
            return self.async_create_entry(title="Ohjaamo", data=self._tiedot)

        return self.async_show_form(
            step_id="entiteetit",
            data_schema=vol.Schema(
                {
                    # 🔴 VALINNAINEN. Tyhja = laheta kaikki. Kayttaja ei voi tietaa mita
                    # valita ennen kuin han on nahnyt laitteet Ohjaamossa — ja tyhja
                    # valinta johti siihen ettei mitaan lahetetty, mika nayttaa
                    # tasmalleen samalta kuin rikkinainen yhteys.
                    vol.Optional(CONF_ENTITEETIT, default=[]): selector.EntitySelector(
                        selector.EntitySelectorConfig(multiple=True)
                    ),
                    vol.Optional(CONF_VALI, default=OLETUS_VALI): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=15, max=3600, step=15,
                                                      unit_of_measurement="s")
                    ),
                }
            ),
        )
