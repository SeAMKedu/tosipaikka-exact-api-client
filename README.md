![kuva](/images/tosipaikka_logot.png)

# TosiPaikka - EXACT API Client

Asiakasohjelma Exafore-sisätilapaikannusjärjestelmän EXACT API -ohjelmointirajapinnalle.

Ohjelma vastaanottaa järjestelmän palvelimelta kahden tyyppisiä *notification*-viestejä:
* *measurements*: ankkurien ja tunnisteen väliset etäisyysmittaukset
* *solution*: järjestelmän laskema tunnisteen sijainti

Kaikki vastaanotetut *notification*-viestit tallennetaan tiedostoon *exafore.log*.

## Exafore-sisätilapaikannusjärjestelmä

Exafore-sisätilapaikannusjärjestelmä käytää UWB:tä (Ultra-Wideband) eli ultralaajakaistaa järjestelmään kuuluvan tunnisteen paikantamiseen.

Lisätietoja Exaforesta ja ultralaajakaistasta:

[https://www.exafore.com/](https://www.exafore.com/)

[https://en.wikipedia.org/wiki/Ultra-wideband](https://en.wikipedia.org/wiki/Ultra-wideband)

Järjestelmä koostuu seuraavista komponenteista:
* EXL Gateway: Linux-tietokone, jolla EXL Server -palvelinohjelmaa ajetaan
* Tukiasemat, joista yksi on master-tukiasema
* Tunnisteet

![kuva](/images/toimintakaavio.png)

Master-tukiasema liitetään verkkokaapelilla EXL Gateway -tietokoneeseen. Muut tukiasemat kommunikoivat langattomasti.

EXACT API on ohjelmointirajapinta, jonka kautta ulkoinen asiakasohjelma voi kommunikoida järjestelmän kanssa. Kommunikointi tapahtuu SSL-pistokkeen avulla. Ohjelmointirajapinnalle lähetetyt ja sieltä vastaanotettavat viestit käyttävät JSON-formaattia.

# Sovelluksen ajaminen

Asenna tarvittavat Python-paketit komennolla
```
pip install -r requirements.txt
```

Käynnistä sitten sovellus komennolla
```
python app.py
```
Lopeta sovelluksen ajo painamalla Ctrl+c.

## Tekijätiedot

Hannu Hakalahti, Asiantuntija TKI, Seinäjoen ammattikorkeakoulu

## Hanketiedot

* Hankkeen nimi: Tosiaikaisen paikkadatan hyödyntäminen teollisuudessa (TosiPaikka)
* Rahoittaja: Etelä-Pohjanmaan liitto (EAKR)
* Aikataulu: 01.12.2021 - 31.08.2023
* Hankkeen kotisivut: [https://projektit.seamk.fi/alykkaat-teknologiat/tosipaikka/](https://projektit.seamk.fi/alykkaat-teknologiat/tosipaikka/)
