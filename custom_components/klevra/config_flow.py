"""
Klevra Homen asetusdialogi Home Assistantissa.

🔴 Miksi tama on olemassa: ilman config_flow'ta kayttajan pitaa muokata
`configuration.yaml`-tiedostoa kasin ja kaynnistaa HA uudelleen. Se on kolme kohtaa
joissa voi epaonnistua (tiedoston loytaminen, sisennys, uudelleenkaynnistys) — ja YAML:n
sisennysvirhe kaataa koko Home Assistantin, ei vain tata integraatiota.

Taman kanssa asennus on: Asetukset -> Laitteet -> Lisaa integraatio -> Klevra Home ->
liita tunnus ja palvelinosoite -> valitse entiteetit. Ei tiedostoja, ei
uudelleenkaynnistysta.
"""
import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN, TUOTENIMI, CONF_PALVELIN, CONF_TUNNUS, CONF_ENTITEETIT, CONF_VALI,
    OLETUS_VALI, EHDOTUS_PALVELIN, POLKU_HAVAINNOT, OTSAKE_TUNNUS,
)

_LOGGER = logging.getLogger(__name__)


async def _testaa_tunnus(hass, palvelin: str, tunnus: str) -> str | None:
    """
    Kokeile tunnusta ja osoitetta ENNEN tallennusta.

    🔴 Vaara tunnus huomataan tassa eika vasta tunnin paasta kun kayttaja ihmettelee
    miksi mitaan ei nay. Palauttaa virhekoodin tai None jos kaikki hyvin.
    """
    istunto = async_get_clientsession(hass)
    try:
        async with istunto.post(
            # 🔴 Polku ja otsake: palvelimen sopimus, ks. const.py.
            f"{palvelin.rstrip('/')}{POLKU_HAVAINNOT}",
            json={"havainnot": [{"entiteetti": "test.yhteys", "tila": "0", "nimi": "Yhteystesti"}]},
            headers={OTSAKE_TUNNUS: tunnus},
            timeout=15,
        ) as vastaus:
            if vastaus.status == 401:
                return "tunnus_ei_kelpaa"
            # 🔴 404 erikseen: se ei ole tunnuksen eika verkon vika vaan vaara osoite
            # — tai siltarajapinta on siirtynyt palvelimella. Ks. const.py.
            if vastaus.status == 404:
                return "vaara_osoite"
            if vastaus.status >= 500:
                return "palvelinvirhe"
            if vastaus.status >= 400:
                return "yhteysvirhe"
            return None
    except Exception as virhe:  # noqa: BLE001
        _LOGGER.debug("%s: yhteystesti epaonnistui: %s", TUOTENIMI, virhe)
        return "ei_yhteytta"


class KlevraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Ohjattu asennus."""

    VERSION = 1

    def __init__(self) -> None:
        self._tiedot: dict = {}

    @staticmethod
    @callback
    def async_get_options_flow(entry) -> "KlevraOptionsFlow":
        """
        🔴 ILMAN TATA "MAARITA"-NAPPIA EI OLE.

        Mitattu 13.11.2026: integraatiossa ei ollut options flow'ta lainkaan, vaikka
        ASENNUS.md lupasi etta entiteettivalintaa voi muuttaa jalkikateen. Ilman sita
        PALVELINOSOITTEEN vaihtaminen vaatii integraation poiston ja uudelleenasennuksen
        — ja osoitteen vaihtuminen on jo tiedossa (uusi domain rekisteroidaan).
        """
        return KlevraOptionsFlow()

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
                    # 🔴 PAKOLLINEN, EHDOTUS EI OLETUS. Vanha oletus
                    # `https://ohjaamo.io` on suljettu (mitattu 13.11.2026: 503,
                    # suspend-by-user). Kuollut oletusarvo tuottaisi virheen jonka
                    # syyta kayttaja ei voi arvata. `suggested_value` kirjoittaa
                    # osoitteen kenttaan valmiiksi mutta ei tallenna sita hanen
                    # puolestaan — ja se on vaihdettavissa myos jalkikateen.
                    vol.Required(
                        CONF_PALVELIN,
                        description={"suggested_value": EHDOTUS_PALVELIN},
                    ): str,
                }
            ),
            errors=virheet,
            description_placeholders={
                "ohje": "Klevra Home → Laitteet → Home Assistant",
            },
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
            return self.async_create_entry(title=TUOTENIMI, data=self._tiedot)

        return self.async_show_form(
            step_id="entiteetit",
            data_schema=vol.Schema(
                {
                    # 🔴 VALINNAINEN. Tyhja = laheta kaikki. Kayttaja ei voi tietaa mita
                    # valita ennen kuin han on nahnyt laitteet sovelluksessa — ja tyhja
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


class KlevraOptionsFlow(config_entries.OptionsFlow):
    """
    Asetusten muuttaminen asennuksen jalkeen — ilman poistoa ja uudelleenasennusta.

    🔴 TAMAN OLEMASSAOLO ON SE, MIKA TEKEE DOMAININ VAIHDOSTA YHDEN KENTAN MUUTOKSEN.
    Palvelinosoite vaihtuu kun uusi domain rekisteroidaan (Nikon paatos 13.11.2026).
    Ilman tata se vaatisi integraation poiston, jolloin entiteetit katoaisivat ja
    automaatiot hajoaisivat kolmannen kerran.

    🔴 Osoite ja tunnus TESTATAAN ennen tallennusta, samoin kuin asennuksessa: vaara
    osoite nakyy tassa eika vasta siina etta lukemat lakkaavat hiljaa paivittymasta.
    """

    async def async_step_init(self, user_input=None):
        """Yksi nakyma: palvelin, tunnus, entiteetit, valitys."""
        entry = self.config_entry
        nyt = {**entry.data, **entry.options}
        virheet: dict[str, str] = {}

        if user_input is not None:
            virhe = await _testaa_tunnus(
                self.hass, user_input[CONF_PALVELIN], user_input[CONF_TUNNUS]
            )
            if virhe:
                virheet["base"] = virhe
            else:
                # 🔴 Kaikki neljä kenttaa tallennetaan optionsiin. `async_setup_entry`
                # lukee `{**entry.data, **entry.options}`, joten options voittaa
                # alkuperaisen asennuksen arvot — eika `data`a tarvitse kirjoittaa.
                return self.async_create_entry(title="", data=dict(user_input))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PALVELIN,
                        description={
                            "suggested_value": nyt.get(CONF_PALVELIN) or EHDOTUS_PALVELIN
                        },
                    ): str,
                    vol.Required(
                        CONF_TUNNUS,
                        description={"suggested_value": nyt.get(CONF_TUNNUS)},
                    ): str,
                    vol.Optional(
                        CONF_ENTITEETIT,
                        description={"suggested_value": nyt.get(CONF_ENTITEETIT) or []},
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(multiple=True)
                    ),
                    vol.Optional(
                        CONF_VALI,
                        description={
                            "suggested_value": nyt.get(CONF_VALI) or OLETUS_VALI
                        },
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=15, max=3600, step=15,
                                                      unit_of_measurement="s")
                    ),
                }
            ),
            errors=virheet,
        )
