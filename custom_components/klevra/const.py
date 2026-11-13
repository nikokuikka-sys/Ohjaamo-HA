"""Klevra Home -sillan vakiot."""

DOMAIN = "klevra"

# Nakyva nimi. 🔴 EI sama kuin LAITENIMI alla — ks. LAITENIMI:n perustelu.
TUOTENIMI = "Klevra Home"

# 🔴 LAITENIMI RATKAISEE ENTITEETTITUNNUKSEN. Mitattu 13.11.2026 ajamalla
# integraatio Home Assistant 2026.2.3:a vasten:
#
#   device_info["name"] = "Ohjaamo"      -> sensor.ohjaamo_porssihinta
#   device_info["name"] = "Klevra Home"  -> sensor.klevra_home_porssihinta
#   device_info["name"] = "Klevra"       -> sensor.klevra_porssihinta
#
# Tunnus EI tule DOMAINista vaan tasta nimesta: `_attr_has_entity_name = True`
# panee HA:n muodostamaan tunnuksen muodossa <laitenimi> <entiteetin nimi>.
#
# Siksi laitenimi on "Klevra" eika "Klevra Home": Nikon valitsemat tunnukset ovat
# `sensor.klevra_*`. Jos tama vaihdetaan "Klevra Homeksi", JOKAINEN kuusi tunnusta
# muuttuu uudelleen ja automaatiot hajoavat toisen kerran.
LAITENIMI = "Klevra"

VALMISTAJA = "Owella Software"

# 🔴 HA TYONTAA tiedot Klevra Homeen, ei toisin pain.
#
# Syy on verkkorakenne eika mieltymys: Klevra Home ajaa pilvessa, Home Assistant kotona
# NAT:in takana. Pilvesta EI voi avata yhteytta kotiin ilman porttiohjausta, VPN:aa tai
# valityspalvelua — ja juuri niita halutaan valttaa.
#
# Ulospain avattu yhteys toimii aina ja on turvallisempi: kotiverkkoon ei avata mitaan.
CONF_PALVELIN = "palvelin"
CONF_TUNNUS = "tunnus"
CONF_ENTITEETIT = "entiteetit"
CONF_VALI = "vali"

OLETUS_VALI = 60  # sekuntia

# ─────────────────────────────────────────────────────────────────────────────
# 🔴 PALVELIMEN SOPIMUS — NAMA EIVAT OLE NIMENVAIHDON ALAISIA.
#
# Polku ja otsake ovat PALVELIMEN omistamia, eivat taman integraation. Ne sanovat
# yha "ohjaamo", koska palvelin odottaa niita siina asussa. Palvelin on toisessa
# repossa; jos ne nimetaan tassa yksin, integraatio saa 404:n eika mikaan toimi.
#
# 🔴 ALA "SIISTI" NAITA. Mitattu 13.11.2026: nimenvaihto rikkoo entiteettitunnukset
# tarkoituksella, mutta naiden rikkominen rikkoisi yhteyden — eri vika, ei haluttu.
# Ne vaihdetaan VASTA kun palvelin on vaihdettu samalla kertaa.
#
# 🔴 JOS INTEGRAATIO LAKKAA TOIMIMAAN, KATSO ENSIN TAHAN — SYY ON TODENNAKOISESTI
# PALVELINPAASSA EIKA TASSA KOODISSA. Mitattu 13.11.2026 palvelimen lahteesta:
# siltapaa elaa `src/ohjaamo/`-hakemistossa (`reitit.js`: `/silta/tila`,
# `/silta/havainnot`, tunnistus otsakkeella `X-Ohjaamo-Silta`; `silta.js`).
# Se hakemisto on osa Ohjaamoa, joka on nyt POISTUMASSA ja jonka Klevra Home
# korvaa. Kun se puretaan, nama polut katoavat tai nimetaan uudelleen.
# Sama vikaluokka on jo nahty: ohjaamo.io vastasi 503 suspend-by-user.
#
# test/test_sopimus.py vartioi naiden ARVOT ajamalla lahetyksen ja lukemalla
# osoitteen ja otsakkeen — ei etsimalla merkkijonoa.
POLKU_HAVAINNOT = "/api/ohjaamo/silta/havainnot"
POLKU_TILA = "/api/ohjaamo/silta/tila"
OTSAKE_TUNNUS = "X-Ohjaamo-Silta"

# 🔴 PALVELINOSOITE: EHDOTUS, EI LUKITTUA OLETUSTA.
#
# Vanha oletus oli `https://ohjaamo.io`. Mitattu 13.11.2026: se vastaa
# HTTP 503, `x-render-routing: suspend-by-user` — palvelu on suljettu. Kuollut
# oletusarvo olisi juuri sita hiljaista puolitoimivuutta jota vastaan tama
# integraatio on rakennettu: kayttaja painaisi Laheta ja ihmettelisi virhetta.
#
# Siksi kentta on PAKOLLINEN ja tama arvo annetaan vain `suggested_value`na:
# se nakyy kentassa valmiiksi kirjoitettuna, mutta kayttaja voi pyyhkia sen yli
# eika sita tallenneta hanen puolestaan.
#
# 🔴 TAMA OSOITE VAIHTUU — SE ON JO TIEDOSSA. Nikon paatos 13.11.2026:
# "laskuposti.com, joka tullaan vaihtamaan kun rekisteroidaan uusi domain."
# Siksi osoitetta EI saa kovakoodata mihinkaan mista sita ei voi vaihtaa ilman
# uutta versiota: se on muokattavissa asennuksen jalkeen asetusnakymasta
# (KlevraOptionsFlow). Domainin vaihto on varma tuleva tapahtuma, ei reunatapaus.
EHDOTUS_PALVELIN = "https://laskuposti.com"
