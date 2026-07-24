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

## Sensorit Home Assistantissa

Integraatio luo kuusi sensoria, joten **et joudu vaihtamaan sovellusta** nähdäksesi
pörssihinnan:

| Sensori | Kertoo |
|---|---|
| `sensor.ohjaamo_porssihinta` | pörssihinta nyt, attribuuttina koko vuorokauden käyrä |
| `sensor.ohjaamo_sahkon_kokonaishinta` | siirto ja marginaali mukana |
| `sensor.ohjaamo_halvin_tunti_tanaan` | halvin tunti |
| `sensor.ohjaamo_liittyman_kuormitus` | paljonko liittymästä on käytössä |
| `sensor.ohjaamo_paasulake` | pääsulakkeen koko |
| `sensor.ohjaamo_kuormanhallinta_rajoittaa` | rajoittaako juuri nyt |

**Kirjoita omat automaatiosi niiden varaan:**

```yaml
automation:
  - alias: "Pesukone vain halvalla"
    trigger:
      - platform: numeric_state
        entity_id: sensor.ohjaamo_sahkon_kokonaishinta
        below: 8
    action:
      - service: switch.turn_on
        target: { entity_id: switch.pesukone }
```

```yaml
automation:
  - alias: "Älä käynnistä saunaa jos liittymä on täynnä"
    condition:
      - condition: state
        entity_id: sensor.ohjaamo_kuormanhallinta_rajoittaa
        state: "ei rajoita"
```

🔴 Emme yritä korvata Home Assistantin automaatioita — **annamme tiedon jolla kirjoitat
omasi.**

---

## Mitä tämä EI tee

**Ei avaa mitään kotiverkkoosi.** Ohjaus toimii silti: Home Assistant **kysyy komennot**
samalla kutsulla jolla se lähettää tiedot. Komento lähtee seuraavalla kierroksella,
oletuksena minuutin sisällä.

🔴 Se on hyväksyttävä viive varaajalle ja lämmitykselle — ne ovat hitaita laitteita.
Valokatkaisijalle se olisi liikaa, ja niitä kannattaa ohjata suoraan Home Assistantissa.

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
