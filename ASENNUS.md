# Käyttöönotto — latauksen jälkeen

<!-- SIIRTYMA:ALKU -->
## 🔴 PÄIVITÄTKÖ OHJAAMOSTA? Lue tämä ensin

Tämä integraatio oli ennen **Ohjaamo**. Versiossa **2.0.0** nimi vaihtui Klevra
Homeksi, ja **kaikkien kuuden sensorin entiteettitunnus muuttui.**

**Automaatiosi lakkaavat toimimaan hiljaa** — laukaisin ei vain koskaan laukea, eikä
Home Assistant ilmoita siitä. Korjaa ne tällä listalla ennen päivitystä:

| Vanha (Ohjaamo) | Uusi (Klevra Home) |
|---|---|
| `sensor.ohjaamo_porssihinta` | `sensor.klevra_porssihinta` |
| `sensor.ohjaamo_sahkon_kokonaishinta` | `sensor.klevra_sahkon_kokonaishinta` |
| `sensor.ohjaamo_halvin_tunti_tanaan` | `sensor.klevra_halvin_tunti_tanaan` |
| `sensor.ohjaamo_liittyman_kuormitus` | `sensor.klevra_liittyman_kuormitus` |
| `sensor.ohjaamo_paasulake` | `sensor.klevra_paasulake` |
| `sensor.ohjaamo_kuormanhallinta_rajoittaa` | `sensor.klevra_kuormanhallinta_rajoittaa` |

Vain etuliite muuttuu: `ohjaamo_` → `klevra_`.

### Poista vanha ENNEN kuin asennat uuden

🔴 **Järjestys ei ole vapaa.** HACS ei poista vanhaa kansiota, koska se laskee
asennuspolun uudesta nimestä. Jos et poista vanhaa, levylle jää **kaksi
integraatiota, jotka lähettävät rinnakkain.**

1. Asetukset → Laitteet ja palvelut → **Ohjaamo** → ⋮ → **Poista**
2. HACS → **Ohjaamo** → ⋮ → **Poista**
3. Tarkista levyltä, että `/config/custom_components/ohjaamo` on poissa. Jos ei,
   poista se käsin (File editor / Studio Code Server / Samba).
4. Käynnistä Home Assistant uudelleen.
5. Jatka alla olevasta vaiheesta 1.
6. Lopuksi: Asetukset → Laitteet ja palvelut → **Entiteetit**, suodata `ohjaamo` ja
   poista jäljelle jääneet kuusi *ei saatavilla* -sensoria. Ne eivät katoa itsestään.

### Palvelinosoite on nyt pakollinen

Vanha oletusosoite ei enää vastaa, joten lukittua oletusarvoa ei ole. Kenttä on
täytetty valmiiksi **ehdotuksella**, jonka voit kirjoittaa yli. **Ota palvelinosoite
Klevra Homesta** samasta näkymästä kuin siltatunnus. Jos annat väärän osoitteen,
dialogi kertoo sen heti.

🔴 **Osoite vaihtuu vielä kertaalleen**, kun Klevra Homelle rekisteröidään uusi
domain. Se ei vaadi uudelleenasennusta eikä rikko automaatioita: päivität osoitteen
kohdasta **Asetukset → Laitteet ja palvelut → Klevra Home → Määritä**, ja muutos
otetaan käyttöön heti. Entiteettitunnukset eivät muutu silloin.
<!-- SIIRTYMA:LOPPU -->

---

Olet ladannut Klevra Homen HACSista. **Nyt se on levyllä muttei vielä käytössä.**
Tämä ohje vie loppuun.

Kokonaisaika noin **5 minuuttia**.

---

## Vaihe 1 — Käynnistä Home Assistant uudelleen

🔴 **Tämä on pakollinen.** HACS kopioi tiedostot, mutta Home Assistant lataa
integraatiot vain käynnistyessään. Ilman uudelleenkäynnistystä Klevra Homea **ei löydy
haussa**, ja se on yleisin syy siihen että käyttöönotto jää tähän.

**Asetukset → Järjestelmä → Käynnistä uudelleen → Käynnistä Home Assistant uudelleen**

Odota että sivu latautuu takaisin (30–60 s).

---

## Vaihe 2 — Hae tunnus ja palvelinosoite Klevra Homesta

Avaa Klevra Home toisessa välilehdessä tai puhelimessa:

**Valikko → Laitteet ja anturit → Home Assistant**

Näet kolmivaiheisen ohjeen. Sieltä löytyvät **siltatunnus** ja **palvelinosoite** —
paina **Kopioi** molemmista.

🔴 **Tunnus on salasana.** Se antaa oikeuden kirjoittaa kohteesi tietoja. Älä lähetä sitä
sähköpostissa äläkä kuvakaappauksessa. Jos se vuotaa, voit perua sen samasta näkymästä —
vanha lakkaa toimimasta heti.

---

## Vaihe 3 — Lisää integraatio

Home Assistantissa:

**Asetukset → Laitteet ja palvelut → + Lisää integraatio**

Kirjoita hakuun **Klevra** ja valitse **Klevra Home**.

> **Jos Klevra Home ei löydy haussa:**
> Uudelleenkäynnistys jäi tekemättä (vaihe 1), tai HACS-lataus ei mennyt läpi.
> Tarkista HACS → Integraatiot → näkyykö Klevra Home ladattuna. Tarkista myös, että
> ladattu versio on nimenvaihdon jälkeinen — HACS lataa oletuksena viimeisimmän
> julkaisun, ja vanha julkaisu asentaa vanhan nimen.

---

## Vaihe 4 — Liitä tunnus ja osoite

Dialogi kysyy kaksi asiaa:

| Kenttä | Mitä siihen |
|---|---|
| **Siltatunnus** | liitä kopioimasi tunnus kokonaisuudessaan |
| **Palvelinosoite** | liitä Klevra Homesta, muodossa `https://…` |

Paina **Lähetä**.

🔴 **Molemmat testataan heti.** Jos tunnus on väärä tai epätäydellinen tai osoite on
väärä, näet virheen tässä etkä vasta tunnin päästä ihmetellessäsi miksi mitään ei näy.
Yleisin virhe on että kopiointi jäi vajaaksi — kopioi uudelleen kokonaan.

---

## Vaihe 5 — Valitse mitä lähetetään

Toinen dialogi kysyy **entiteetit**.

Kirjoita hakukenttään esimerkiksi `varaaja` ja valitse listalta ne jotka haluat
lähettää:

```
sensor.varaaja_current_temperature    veden lämpötila
sensor.varaaja_target_temperature     tavoitelämpötila
water_heater.varaaja                  tila
sensor.varaaja_power                  teho
```

**Valitse listalta, älä kirjoita nimiä käsin.** Nimet ovat pitkiä ja virhealttiita, ja
kirjoitusvirhe on yleisin syy siihen ettei tieto tule perille.

Voit lisätä mitä tahansa muutakin — lämpötila-antureita, kytkimiä, mittareita.

**Lähetysväli**: oletus 60 s riittää lähes aina. Alle 15 s ei kelpaa.

Paina **Lähetä**. Valmis.

---

## Vaihe 6 — Varmista että tieto tulee perille

Odota **noin minuutti** ensimmäistä lähetystä.

### Klevra Homessa
**Laitteet → Home Assistant → Tarkista yhteys**

Näet joko *"Yhteys toimii — 4 mittausta, 4 uutta anturia"* tai kehotuksen tarkistaa
asennus.

### Home Assistantissa
**Asetukset → Järjestelmä → Lokit**, etsi sana `Klevra`:

| Lokirivi | Merkitys |
|---|---|
| `Klevra Home-silta kaynnistetty: 4 entiteettia` | ✅ toimii |
| `entiteettia sensor.x ei ole olemassa` | entiteetti poistettu tai nimetty uudelleen |
| `tunnus ei kelvannut` | hae uusi tunnus Klevra Homesta |
| `palvelin ei tunne osoitetta` | väärä palvelinosoite |
| `aikakatkaisu` | verkko-ongelma, yrittää itse uudelleen |

---

## Muutokset jälkikäteen

**Asetukset → Laitteet ja palvelut → Klevra Home → Määritä**

Voit muuttaa kaikkia neljää: **palvelinosoitteen**, **siltatunnuksen**, lähetettävät
entiteetit ja lähetysvälin. Osoite ja tunnus testataan ennen tallennusta. Asetukset
latautuvat uudelleen automaattisesti — **ei uudelleenkäynnistystä, ei
uudelleenasennusta, eivätkä entiteettitunnukset muutu.**

🔴 Tätä näkymää ei ollut aiemmin olemassa, vaikka ohje lupasi sen. Siksi
palvelinosoitteen vaihtaminen olisi vaatinut integraation poiston — ja poisto
hävittää entiteetit, eli automaatiot olisivat hajonneet uudelleen. Nyt vaihto on
yhden kentän muutos.

---

## Viimeinen vaihe sovelluksessa: yhdistä kytkin ja lämpötila

Jos laitteesi **ohjaus ja mittaus ovat eri laitteissa** — esimerkiksi varaaja Shelly-releen
takana ja lämpötila Home Assistantista — ne näkyvät aluksi kahtena erillisenä.

Yhdistä ne:

**Avaa kytkin → Asetukset → Lämpötila-anturi → Liitä** → valitse Home Assistantin tuoma
lämpötila.

Sen jälkeen kortti näyttää **molemmat**: päälle/pois ja lämpötilan. Ja pörssiohjaus voi
ottaa lämpötilan huomioon ennen kuin katkaisee virran.

---

## Poistaminen

**Asetukset → Laitteet ja palvelut → Klevra Home → ⋮ → Poista**

Lähetys lakkaa heti. Palvelimelle jo tulleet mittaukset säilyvät; voit poistaa anturit
sovelluksen puolelta erikseen.

Halutessasi peru myös tunnus: **Klevra Home → Home Assistant → Peru tunnus**.
