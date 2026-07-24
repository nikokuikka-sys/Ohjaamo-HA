# Käyttöönotto — latauksen jälkeen

Olet ladannut Ohjaamon HACSista. **Nyt se on levyllä muttei vielä käytössä.**
Tämä ohje vie loppuun.

Kokonaisaika noin **5 minuuttia**.

---

## Vaihe 1 — Käynnistä Home Assistant uudelleen

🔴 **Tämä on pakollinen.** HACS kopioi tiedostot, mutta Home Assistant lataa
integraatiot vain käynnistyessään. Ilman uudelleenkäynnistystä Ohjaamoa **ei löydy
haussa**, ja se on yleisin syy siihen että käyttöönotto jää tähän.

**Asetukset → Järjestelmä → Käynnistä uudelleen → Käynnistä Home Assistant uudelleen**

Odota että sivu latautuu takaisin (30–60 s).

---

## Vaihe 2 — Hae tunnus Ohjaamosta

Avaa Ohjaamo (ohjaamo.io) toisessa välilehdessä tai puhelimessa:

**Valikko → Laitteet ja anturit → Home Assistant**

Näet kolmivaiheisen ohjeen. Kohdasta 2 löytyy **siltatunnus** — paina **Kopioi**.

Tunnus näyttää tältä:
```
ohj_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

🔴 **Tunnus on salasana.** Se antaa oikeuden kirjoittaa kohteesi tietoja. Älä lähetä sitä
sähköpostissa äläkä kuvakaappauksessa. Jos se vuotaa, voit perua sen samasta näkymästä —
vanha lakkaa toimimasta heti.

---

## Vaihe 3 — Lisää integraatio

Home Assistantissa:

**Asetukset → Laitteet ja palvelut → + Lisää integraatio**

Kirjoita hakuun **Ohjaamo** ja valitse se.

> **Jos Ohjaamo ei löydy haussa:**
> Uudelleenkäynnistys jäi tekemättä (vaihe 1), tai HACS-lataus ei mennyt läpi.
> Tarkista HACS → Integraatiot → näkyykö Ohjaamo ladattuna.

---

## Vaihe 4 — Liitä tunnus

Dialogi kysyy kaksi asiaa:

| Kenttä | Mitä siihen |
|---|---|
| **Siltatunnus** | liitä kopioimasi `ohj_...` |
| **Palvelin** | jätä oletukseksi `https://ohjaamo.io` |

Paina **Lähetä**.

🔴 **Tunnus testataan heti.** Jos se on väärä tai epätäydellinen, näet virheen tässä
etkä vasta tunnin päästä ihmetellessäsi miksi mitään ei näy. Yleisin virhe on että
kopiointi jäi vajaaksi — kopioi tunnus uudelleen kokonaan.

---

## Vaihe 5 — Valitse mitä lähetetään

Toinen dialogi kysyy **entiteetit**.

Kirjoita hakukenttään esimerkiksi `varaaja` ja valitse listalta ne jotka haluat Ohjaamoon:

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

### Ohjaamossa
**Laitteet → Home Assistant → Tarkista yhteys**

Näet joko *"Yhteys toimii — 4 mittausta, 4 uutta anturia"* tai kehotuksen tarkistaa
asennus.

### Home Assistantissa
**Asetukset → Järjestelmä → Lokit**, etsi sana `Ohjaamo`:

| Lokirivi | Merkitys |
|---|---|
| `Ohjaamo-silta kaynnistetty: 4 entiteettia` | ✅ toimii |
| `entiteettia sensor.x ei ole olemassa` | entiteetti poistettu tai nimetty uudelleen |
| `tunnus ei kelvannut` | hae uusi tunnus Ohjaamosta |
| `aikakatkaisu` | verkko-ongelma, yrittää itse uudelleen |

---

## Muutokset jälkikäteen

**Asetukset → Laitteet ja palvelut → Ohjaamo → Määritä**

Voit lisätä tai poistaa entiteettejä ja muuttaa lähetysväliä. Asetukset latautuvat
uudelleen automaattisesti — **ei uudelleenkäynnistystä**.

---

## Viimeinen vaihe Ohjaamossa: yhdistä kytkin ja lämpötila

Jos laitteesi **ohjaus ja mittaus ovat eri laitteissa** — esimerkiksi varaaja Shelly-releen
takana ja lämpötila Home Assistantista — ne näkyvät aluksi kahtena erillisenä.

Yhdistä ne:

**Avaa kytkin → Asetukset → Lämpötila-anturi → Liitä** → valitse Home Assistantin tuoma
lämpötila.

Sen jälkeen kortti näyttää **molemmat**: päälle/pois ja lämpötilan. Ja pörssiohjaus voi
ottaa lämpötilan huomioon ennen kuin katkaisee virran.

---

## Poistaminen

**Asetukset → Laitteet ja palvelut → Ohjaamo → ⋮ → Poista**

Lähetys lakkaa heti. Ohjaamoon jo tulleet mittaukset säilyvät; voit poistaa anturit
Ohjaamon puolelta erikseen.

Halutessasi peru myös tunnus: **Ohjaamo → Home Assistant → Peru tunnus**.
