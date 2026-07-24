# Ohjaamo — Home Assistant -integraatio

Yhdistä Home Assistant **Ohjaamoon** ilman pilvipalvelua.
Ei Nabu Casaa, ei porttiohjausta, ei VPN:ää.

---

## Miten tämä toimii

Home Assistant on kotonasi, reitittimen takana. Ohjaamo on internetissä.

**Ohjaamo ei voi soittaa kotiisi** — se vaatisi porttiohjauksen tai VPN:n, ja molemmat
avaavat kotiverkkoosi reiän.

Siksi suunta on käännetty: **Home Assistant lähettää tiedot ulospäin**, samoin kuin
selain avaa sivun. Kotiverkkoosi ei avata mitään.

```
   KOTI                          INTERNET
 ┌─────────────────┐           ┌──────────────┐
 │ Home Assistant  │  ──────▶  │   Ohjaamo    │
 └─────────────────┘  60 s     └──────────────┘
   ei avattuja portteja
```

---

## Asennus

### 1. Lisää tietovarasto HACSiin
**HACS → Integraatiot → ⋮ → Mukautetut tietovarastot**

| | |
|---|---|
| Tietovarasto | `https://github.com/nikokuikka-sys/Ohjaamo-HA` |
| Luokka | Integration |

### 2. Asenna
Etsi **Ohjaamo** → **Lataa** → käynnistä Home Assistant uudelleen.

### 3. Yhdistä

👉 **Yksityiskohtainen ohje latauksen jälkeen: [ASENNUS.md](ASENNUS.md)**

**Asetukset → Laitteet ja palvelut → Lisää integraatio → Ohjaamo**

1. Liitä **siltatunnus** (Ohjaamo → Laitteet → Home Assistant → Näytä tunnus)
2. Valitse **entiteetit** listalta
3. Aseta **lähetysväli** (oletus 60 s)

Tunnus testataan heti — väärä tunnus näkyy tässä eikä vasta tunnin päästä.

---

## Mitä lähetetään

Vain valitsemasi entiteetit: **tila, yksikkö, nimi ja laji**. Ei salasanoja, ei muita
laitteita, ei mitään mitä et ole listannut.

Voit muuttaa valintaa milloin tahansa samasta näkymästä.

---

## Mitä tämä EI tee

**Ei ohjaa Home Assistantin laitteita Ohjaamosta.** Suunta on yksi: HA lähettää, Ohjaamo
lukee. Ohjaus vaatisi yhteyden pilvestä kotiin — juuri sen jonka halusimme välttää.

Laitteiden ohjaus Ohjaamossa tapahtuu suoraan valmistajan pilven kautta (Shelly, Sensibo)
tai releen avulla.

---

## Vianetsintä

Katso **Asetukset → Järjestelmä → Lokit** ja etsi sana `Ohjaamo`.

| Lokirivi | Merkitys |
|---|---|
| `Ohjaamo-silta kaynnistetty: N entiteettia` | toimii |
| `entiteettia sensor.x ei ole olemassa` | entiteetti poistettu tai nimetty uudelleen |
| `tunnus ei kelvannut` | hae uusi tunnus Ohjaamosta |
| `aikakatkaisu` | verkko-ongelma; yrittää itse uudelleen |

Yksityiskohtainen ohje: [OHJE-HOME-ASSISTANT.md](OHJE-HOME-ASSISTANT.md)

---

## Tietoturva

| | |
|---|---|
| Yhteys | HTTPS, aina kotoa ulospäin |
| Tunnistus | kohdekohtainen tunnus, peruttavissa milloin tahansa |
| Kotiverkko | ei avattuja portteja |
| Peruminen | Ohjaamo → Home Assistant → Peru tunnus |

---

## Vaatimukset

Home Assistant **2024.4.0** tai uudempi.

---

Tehnyt [Owella Software](https://ohjaamo.io) · Owella Software
