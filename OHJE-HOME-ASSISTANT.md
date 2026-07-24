# Ohjaamo + Home Assistant — asennusohje

**Ilman pilvipalvelua.** Ei Nabu Casaa, ei porttiohjausta, ei VPN:ää.

---

## Miksi tämä toimii ilman pilveä

Home Assistant on kotonasi, reitittimen takana. Ohjaamo on internetissä.

🔴 **Ohjaamo ei voi soittaa kotiisi** — se vaatisi porttiohjauksen tai VPN:n, ja
molemmat avaavat kotiverkkoosi reiän.

Siksi suunta on käännetty: **Home Assistant lähettää tiedot ulospäin.**

```
   KOTI                          INTERNET
 ┌─────────────────┐           ┌──────────────┐
 │ Home Assistant  │  ──────▶  │   Ohjaamo    │
 │ + Midea-varaaja │  lähettää │              │
 └─────────────────┘   60 s    └──────────────┘
      ei avattuja portteja
```

Ulospäin avattu yhteys toimii aina — samoin kuin selain avaa sivun. **Kotiverkkoosi ei
avata mitään.**

---

# OSA 1 — Ohjaamon puoli (2 min)

### 1.1 Hae siltatunnus
Ohjaamo → **Valikko → Laitteet ja anturit → Home Assistant → Näytä tunnus**

Saat tunnuksen joka alkaa `ohj_`. Se on **kohdekohtainen**: jokaisella kohteella on oma,
eikä yksi tunnus paljasta muita.

🔴 **Tunnus on salasana.** Älä lähetä sitä sähköpostissa äläkä kuvakaappauksessa. Jos se
vuotaa, peru se samasta näkymästä — vanha lakkaa toimimasta heti.

---

# OSA 2 — Home Assistantin puoli

Valitse **A** (suositeltu) tai **B**.

---

## A. Ohjattu asennus HACSin kautta ⭐ 3 min, ei tiedostoja

### A.1 Lisää Ohjaamo HACSiin
HA → **HACS → Integraatiot → ⋮ (oikea yläkulma) → Mukautetut tietovarastot**

```
Tietovarasto:  https://github.com/nikokuikka-sys/ohjaamo-ha
Luokka:        Integration
```
→ **Lisää**

### A.2 Asenna
Etsi HACSista **Ohjaamo** → **Lataa** → käynnistä HA uudelleen.

### A.3 Yhdistä — kaikki dialogissa
**Asetukset → Laitteet ja palvelut → Lisää integraatio → Ohjaamo**

1. **Liitä siltatunnus** (osasta 1). 🔴 Tunnus **testataan heti**: jos se on väärä,
   näet sen tässä etkä vasta tunnin päästä ihmetellessäsi miksi mitään ei näy.
2. **Valitse entiteetit listalta.** Et kirjoita nimiä käsin — `sensor.varaaja_current_temperature`
   on pitkä ja virhealtis, ja kirjoitusvirhe oli yleisin syy siihen ettei tieto tullut perille.
3. **Aseta lähetysväli** (oletus 60 s).

**Valmis.** Ei tiedostoja, ei YAML:ia, ei uudelleenkäynnistystä.

🔴 Voit **muuttaa entiteettivalintaa myöhemmin** samasta näkymästä — asetukset latautuvat
uudelleen automaattisesti.

---

## B. Käsin — jos et käytä HACSia

# OSA 2B — Käsiasennus (10 min)

### 2.1 Lataa ja pura tiedosto
Lataa `ohjaamo-ha-silta.zip` ja pura se.

### 2.2 Kopioi kansio Home Assistantiin
Kopioi `custom_components/ohjaamo` HA:n konfiguraatiokansioon:

```
/config/
  configuration.yaml
  custom_components/
    ohjaamo/          ← tähän
      __init__.py
      const.py
      manifest.json
```

**Miten kopioit** riippuu asennuksestasi:
| Asennus | Tapa |
|---|---|
| **HAOS / Supervised** | Lisäosa **File editor** tai **Samba share** |
| **Container / Core** | `scp` tai suoraan levylle |
| **Kaikki** | Lisäosa **Studio Code Server** on helpoin |

### 2.3 Selvitä mitkä entiteetit haluat lähettää
HA:ssa: **Kehittäjän työkalut → Tilat**. Etsi varaajasi.

Tyypilliset Midea-vesivaraajan entiteetit:
```
sensor.varaaja_current_temperature     nykyinen veden lämpötila
sensor.varaaja_target_temperature      tavoitelämpötila
water_heater.varaaja                   tila (päällä / pois / tila)
sensor.varaaja_power                   teho
```
🔴 **Nimet vaihtelevat.** Kopioi ne täsmälleen kuten HA näyttää — kirjoitusvirhe on
yleisin syy siihen ettei tieto tule perille. Lisäosa **varoittaa lokissa** jos entiteettiä
ei ole, joten virhe ei jää huomaamatta.

### 2.4 Lisää asetukset

🔴 **Tämä vaihe jää pois jos käytit tapaa A** — dialogi hoitaa sen.

Avaa `/config/configuration.yaml` ja lisää loppuun:

```yaml
ohjaamo:
  tunnus: "ohj_TÄHÄN_TUNNUS_OHJAAMOSTA"
  entiteetit:
    - sensor.varaaja_current_temperature
    - sensor.varaaja_target_temperature
    - water_heater.varaaja
    - sensor.varaaja_power
    # Voit lisätä mitä tahansa muitakin:
    - sensor.olohuone_lampotila
  vali: 60          # sekuntia, 15–3600
```

### 2.5 Käynnistä uudelleen
**Asetukset → Järjestelmä → Käynnistä uudelleen**

### 2.6 Tarkista että se toimii
**Asetukset → Järjestelmä → Lokit**, etsi sana `Ohjaamo`:

| Lokirivi | Merkitys |
|---|---|
| `Ohjaamo-silta kaynnistetty: 4 entiteettia` | ✅ toimii |
| `entiteettia sensor.x ei ole olemassa` | kirjoitusvirhe kohdassa 2.3 |
| `tunnus ei kelvannut` | väärä tunnus, hae uudelleen |
| `aikakatkaisu` | verkko-ongelma, yrittää itse uudelleen |

---

# OSA 3 — Varmista Ohjaamosta

Minuutin kuluttua: **Laitteet ja anturit**. Varaajan pitäisi näkyä lukemineen.

### 3.1 Yhdistä kytkin ja lämpötila
Varaajasi on **Shelly-kytkimen takana**, joten ohjaus tulee Shellyltä ja lämpötila HA:sta.
Ne ovat aluksi kaksi eri laitetta.

Yhdistä ne: **avaa Shelly-kytkin → Asetukset → Lämpötila-anturi → Liitä** ja valitse HA:n
tuoma lämpötila.

Sen jälkeen kortti näyttää **molemmat**: päälle/pois ja lämpötilan.

### 3.2 Pörssiohjaus
**Avaa laite → Asetukset → Pörssiohjaus**.

🔴 Varaaja on **paras mahdollinen pörssiohjattava**: 200 litraa vettä on lämpövarasto
joka kestää tuntien katkon huomaamatta.

---

## Vianetsintä

**Ei mitään lokissa** → kansio on väärässä paikassa. Sen on oltava
`/config/custom_components/ohjaamo/`, ei `/config/ohjaamo/`.

**"Integration error: ohjaamo"** → `manifest.json` puuttuu tai kansio on väärin nimetty.

**Lukemat eivät päivity** → tarkista `vali`. Alle 15 s ei kelpaa; se kuormittaisi turhaan.

**Lämpötila näkyy mutta ohjaus ei toimi** → ohjaus tulee Shellyltä, ei HA:sta. Tarkista
että Shelly-kytkin on liitetty samaan kohteeseen.

---

## Mitä tämä lisäosa EI tee

- **Ei ohjaa HA:n laitteita Ohjaamosta.** Suunta on yksi: HA lähettää, Ohjaamo lukee.
  Ohjaus vaatisi yhteyden pilvestä kotiin — juuri sen jonka halusimme välttää.
  Varaajan ohjaus tulee **Shelly-kytkimen kautta**, ja se toimii jo.
- **Ei lähetä mitään mitä et ole listannut.** Vain `entiteetit`-listan rivit lähtevät.
- **Ei tallenna salasanoja.** Vain tilat, yksiköt ja nimet.

---

## Tietoturva

| | |
|---|---|
| Yhteys | HTTPS, aina kotoa ulospäin |
| Tunnistus | kohdekohtainen tunnus, peruttavissa milloin tahansa |
| Kotiverkko | **ei avattuja portteja** |
| Data | vain listaamasi entiteetit |
| Peruminen | Ohjaamo → Home Assistant → **Peru tunnus** |
