"""Ohjaamo-sillan vakiot."""

DOMAIN = "ohjaamo"

# 🔴 HA TYONTAA tiedot Ohjaamoon, ei toisin pain.
#
# Syy on verkkorakenne eika mieltymys: Ohjaamo ajaa pilvessa, Home Assistant kotona
# NAT:in takana. Pilvesta EI voi avata yhteytta kotiin ilman porttiohjausta, VPN:aa tai
# valityspalvelua — ja juuri niita halutaan valttaa.
#
# Ulospain avattu yhteys toimii aina ja on turvallisempi: kotiverkkoon ei avata mitaan.
CONF_PALVELIN = "palvelin"
CONF_TUNNUS = "tunnus"
CONF_ENTITEETIT = "entiteetit"
CONF_VALI = "vali"

OLETUS_PALVELIN = "https://ohjaamo.io"
OLETUS_VALI = 60  # sekuntia
