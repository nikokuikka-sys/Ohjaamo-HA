# Klevra Home — Home Assistant -integraatio

Yhdistä Home Assistant **Klevra Homeen** ilman pilvipalvelua.
Ei Nabu Casaa, ei porttiohjausta, ei VPN:ää.

---

<!-- SIIRTYMA:ALKU -->
## 🔴 LUE TÄMÄ ENSIN — tämä versio rikkoo automaatiosi

Tämä integraatio oli ennen **Ohjaamo**. Nimi vaihdettiin paikallaan versiossa
**2.0.0**: sama integraatio, uusi nimi. Siksi **jokainen entiteettitunnus muuttui.**

**Jokainen automaatio, komentosarja, näkymä ja mittaustaulu, joka nojaa vanhoihin
tunnuksiin, lakkaa toimimasta — ja lakkaa hiljaa.** Home Assistant ei ilmoita siitä:
laukaisin ei vain koskaan laukea. Käy nämä kuusi läpi ennen kuin päivität.

### Vanha → uusi entiteettitunnus

Nämä ovat kaikki kuusi. Tee etsi-ja-korvaa tällä listalla.

| Vanha (Ohjaamo) | Uusi (Klevra Home) |
|---|---|
| `sensor.ohjaamo_porssihinta` | `sensor.klevra_porssihinta` |
| `sensor.ohjaamo_sahkon_kokonaishinta` | `sensor.klevra_sahkon_kokonaishinta` |
| `sensor.ohjaamo_halvin_tunti_tanaan` | `sensor.klevra_halvin_tunti_tanaan` |
| `sensor.ohjaamo_liittyman_kuormitus` | `sensor.klevra_liittyman_kuormitus` |
| `sensor.ohjaamo_paasulake` | `sensor.klevra_paasulake` |
| `sensor.ohjaamo_kuormanhallinta_rajoittaa` | `sensor.klevra_kuormanhallinta_rajoittaa` |

Vain etuliite muuttuu: `ohjaamo_` → `klevra_`. Loppuosat ovat tarkoituksella samat,
jotta korvaus on mekaaninen.

🔴 **Yhteensopivuuskerrosta vanhoille tunnuksille ei ole, eikä se ole unohdus.**
Se jättäisi kaksi totuutta elämään rinnakkain ja tekisi siirtymästä näkymättömän.
Katkos, jonka näet, on parempi kuin puolitoimivuus, jota et näe.

### Mitä sinun on tehtävä

Järjestys ei ole vapaa. **Vanha poistetaan ENNEN uuden asennusta**, koska HACS
ei poista vanhaa kansiota itse — muuten levylle jää kaksi integraatiota lähettämään
rinnakkain.

1. **Korjaa automaatiot** yllä olevalla taulukolla. Tee tämä ensin, niin ne toimivat
   heti kun uusi on asennettu.
2. **Poista vanha integraatio Home Assistantista:**
   Asetukset → Laitteet ja palvelut → **Ohjaamo** → ⋮ → **Poista**
3. **Poista vanha HACSista:** HACS → **Ohjaamo** → ⋮ → **Poista**
4. **Tarkista levyltä**, että kansio `/config/custom_components/ohjaamo` on poissa.
   Jos se on vielä siellä, poista se käsin (File editor / Studio Code Server / Samba).
   🔴 Tätä kohtaa ei voi ohittaa: HACS laskee asennuspolun uudesta nimestä eikä
   kosketa vanhaan kansioon.
5. **Käynnistä Home Assistant uudelleen.**
6. **Asenna Klevra Home** — ohje alla. Tarvitset **palvelinosoitteen** ja
   **siltatunnuksen** Klevra Homesta.
7. **Siivoa jäljet:** Asetukset → Laitteet ja palvelut → Entiteetit. Suodata sanalla
   `ohjaamo`. Kuusi vanhaa sensoria jää rekisteriin tilaan *ei saatavilla* — poista ne.
   Ne eivät katoa itsestään eivätkä estä uusia, mutta ne sotkevat haun.

Yksityiskohtainen käyttöönotto: **[ASENNUS.md](ASENNUS.md)**
<!-- SIIRTYMA:LOPPU -->

---

## Miten tämä toimii

Home Assistant on kotonasi, reitittimen takana. Klevra Home on internetissä.

**Palvelin ei voi soittaa kotiisi** — se vaatisi porttiohjauksen tai VPN:n, ja molemmat
avaavat kotiverkkoosi reiän.

Siksi suunta on käännetty: **Home Assistant lähettää tiedot ulospäin**, samoin kuin
selain avaa sivun. Kotiverkkoosi ei avata mitään.

```
   KOTI                          INTERNET
 ┌─────────────────┐           ┌──────────────┐
 │ Home Assistant  │  ──────▶  │ Klevra Home  │
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

Jos tietovarasto on jo lisätty, tätä kohtaa ei tarvitse tehdä uudelleen — repon
osoite ei muuttunut.

### 2. Asenna
Etsi **Klevra Home** → **Lataa** → käynnistä Home Assistant uudelleen.

🔴 **Jos HACS tarjoaa vain vanhoja versioita:** avaa versiovalikko ja valitse `main`,
tai pyydä uusi julkaisu. HACS lataa oletuksena viimeisimmän julkaisun, ja
nimenvaihto on julkaisematta siihen asti.

### 3. Yhdistä

👉 **Yksityiskohtainen ohje latauksen jälkeen: [ASENNUS.md](ASENNUS.md)**

**Asetukset → Laitteet ja palvelut → Lisää integraatio → Klevra Home**

1. Liitä **siltatunnus** ja **palvelinosoite** (Klevra Home → Laitteet → Home Assistant)
2. Valitse **entiteetit** listalta
3. Aseta **lähetysväli** (oletus 60 s)

Tunnus ja osoite testataan heti — väärä näkyy tässä eikä vasta tunnin päästä.

🔴 **Palvelinosoite on pakollinen kenttä, ja siinä on ehdotus — ei lukittua
oletusta.** Se on tarkoituksellista: lukittu oletus osoittaisi vanhaan osoitteeseen,
joka ei enää vastaa, ja virhe näyttäisi tunnuksen viaksi. Ota osoite Klevra Homesta ja
kirjoita ehdotuksen yli.

Osoite **vaihtuu vielä**, kun uusi domain rekisteröidään. Silloin riittää
**Klevra Home → Määritä** — ei uudelleenasennusta, eivätkä entiteettitunnukset muutu.

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
| `sensor.klevra_porssihinta` | pörssihinta nyt, attribuuttina koko vuorokauden käyrä |
| `sensor.klevra_sahkon_kokonaishinta` | siirto ja marginaali mukana |
| `sensor.klevra_halvin_tunti_tanaan` | halvin tunti |
| `sensor.klevra_liittyman_kuormitus` | paljonko liittymästä on käytössä |
| `sensor.klevra_paasulake` | pääsulakkeen koko |
| `sensor.klevra_kuormanhallinta_rajoittaa` | rajoittaako juuri nyt |

**Kirjoita omat automaatiosi niiden varaan:**

```yaml
automation:
  - alias: "Pesukone vain halvalla"
    trigger:
      - platform: numeric_state
        entity_id: sensor.klevra_sahkon_kokonaishinta
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
        entity_id: sensor.klevra_kuormanhallinta_rajoittaa
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

Katso **Asetukset → Järjestelmä → Lokit** ja etsi sana `Klevra`.

| Lokirivi | Merkitys |
|---|---|
| `Klevra Home-silta kaynnistetty: N entiteettia` | toimii |
| `entiteettia sensor.x ei ole olemassa` | entiteetti poistettu tai nimetty uudelleen |
| `tunnus ei kelvannut` | hae uusi tunnus Klevra Homesta |
| `palvelin ei tunne osoitetta` | väärä palvelinosoite, tai siltarajapinta on siirtynyt |
| `aikakatkaisu` | verkko-ongelma; yrittää itse uudelleen |

Yksityiskohtainen ohje: [OHJE-HOME-ASSISTANT.md](OHJE-HOME-ASSISTANT.md)

---

## Tietoturva

| | |
|---|---|
| Yhteys | HTTPS, aina kotoa ulospäin |
| Tunnistus | kohdekohtainen tunnus, peruttavissa milloin tahansa |
| Kotiverkko | ei avattuja portteja |
| Peruminen | Klevra Home → Home Assistant → Peru tunnus |

---

## Vaatimukset

Home Assistant **2024.4.0** tai uudempi.

---

## Kehittäjälle

```bash
python3 test/aja.py          # kaikki tarkistukset
```

Ajaa kolme asiaa: jokainen Python-tiedosto kääntyy, integraatio nousee oikeaa Home
Assistantia vasten ja tuottaa tasan kuusi `sensor.klevra_*`-tunnusta, ja vanhaa nimeä
ei ole jäänyt koodiin. Tarkistus lukee **koodia**, ei kommentteja eikä tämän
dokumentin siirtymäohjetta, jossa vanha nimi esiintyy tarkoituksella.

---

Tehnyt Owella Software
