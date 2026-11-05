# Briefing: nieuwe plaatspagina's voor hjverhuizing.nl

HJ Verhuizing is een verhuisbedrijf met thuisbasis in Hattem (Gelderland). De site heeft plaatspagina's
(`/verhuisbedrijf-<plaats>/`) die moeten ranken op "verhuisbedrijf <plaats>". Elke pagina moet echt
anders zijn dan de andere: Google filtert pagina's weg die alleen de plaatsnaam verwisselen.
Voorbeelden van hoe het moet: `/home/claude/hj/build/data/lokaal.py` (lees die eerst, vooral "elburg" en "zwolle").

## Harde regels
1. **Niets verzinnen.** Elk feit over een plaats komt uit een bron die je zelf hebt geopend, liefst de
   gemeentesite. Zet elke bron in `bronnen`. Wat je niet vindt, laat je weg.
2. **Over HJ Verhuizing mag je alleen deze dingen zeggen** (ze komen van hun eigen site):
   thuisbasis in Hattem; vakkundig team; ruim 250 verhuizingen; persoonlijk contact met de verhuizers zelf;
   (de)montage van meubels dankzij een achtergrond in de bouw; een eigen verhuislift; inpak- en uitpakservice;
   ontruiming met bezemschone oplevering; seniorenverhuizing met vast aanspreekpunt; spoedverhuizing (soms
   binnen 24 uur); verhuisdozen en dekens huren; ook in het weekend en op korte termijn; vrijblijvend langskomen
   en een offerte op maat zonder verrassingen achteraf (geen vaste prijzen, altijd maatwerk); inboedel verzekerd;
   ook internationaal. Niets anders: geen jaartallen, geen aantallen klanten in die plaats, geen "wij hebben al
   veel verhuizingen in X gedaan", geen opslag als dienst, geen prijzen.
3. **Toon:** gewoon, direct Nederlands, u-vorm, zoals een vakman praat. Geen marketingclichés
   ("ontzorgen" mag één keer per pagina, niet vaker), geen emoji, zo min mogelijk gedachtestreepjes (—).
   Leest als origineel Nederlands, niet als vertaald.
4. **Uniek per pagina:** begin elke intro anders, gebruik per plaats eigen invalshoeken (binnenstad, nieuwbouw,
   dorp/boerderijen, water/dijken, vakantieparken, studenten, wijken), andere vragen in de FAQ.
5. Plaatsen in dezelfde gemeente delen regels (afval, melding). Schrijf die dan in andere woorden en leg per kern
   een eigen nadruk (bijv. de kern zelf, de nieuwbouw daar, het karakter), zodat de pagina's niet op elkaar lijken.

## Wat je per plaats onderzoekt (met bron-URL)
- Verhuiswagen of verhuislift op straat: parkeren (betaald/blauwe zone/gratis), laad- en lostijden, venstertijden,
  voetgangersgebied, pollers, ontheffing of melding voor een object/verhuislift/container op de weg (termijn, kosten).
- Milieuzone/zero-emissiezone als die er is.
- Afval: wie haalt op, hoe grof vuil laten ophalen of wegbrengen (adres milieustraat).
- Verhuizing doorgeven (gemeente, DigiD, termijn als vermeld).
- Karakter: wijken/kernen, beschermd stadsgezicht, nieuwbouwwijken in aanbouw (met naam en aantal woningen als de bron het noemt).
- Coördinaten (lat, lon) van het centrum, bijvoorbeeld van Wikipedia.

## Uitvoer
Schrijf een Python-bestand (het pad staat in je opdracht) met precies deze vorm:

```python
PLAATSEN = {}
PLAATSEN["epe"] = {               # slug, kleine letters, koppeltekens: wordt /verhuisbedrijf-epe/
  "naam": "Epe",
  "gemeente": "Epe",
  "regio": "Veluwe",              # een van: "Regio Zwolle", "Veluwe", "Salland", "Kop van Overijssel", "Noord-Veluwe"
  "coord": (52.3475, 5.9861),     # centrum, met bron in bronnen
  "title": "Verhuisbedrijf Epe: ... | HJ Verhuizing",   # max 60 tekens
  "desc": "...",                  # meta description, 120-155 tekens, met "verhuisbedrijf Epe" erin
  "h1": "Verhuisbedrijf Epe ...", # begint met "Verhuisbedrijf <naam>"
  "lead": "...",                  # 1-2 zinnen onder de H1
  "intro_html": "<p>...</p>",     # 120-200 woorden: waarom HJ voor een verhuizing in deze plaats, aan de hand van het karakter van de plaats; alleen toegestane HJ-feiten
  "h2": "...",                    # kop van het lokale blok
  "html": "<p>..</p><h3>..</h3><p>..</p>",  # 220-380 woorden lokale feiten in gewone taal, met <h3>-tussenkoppen, interne links mogen naar /verhuislift-nodig/, /diensten/ontruiming/, /diensten/demontage-service/, /verhuischecklist/, /wat-kost-een-verhuizing/
  "faq": [("vraag?", "<p>antwoord</p>"), ...],  # 3-4 vragen die alleen voor deze plaats kloppen
  "bronnen": [("Gemeente Epe: parkeren", "https://..."), ...],
}
```
Gebruik `\"` of enkele quotes binnen strings correct, zodat het bestand met `python3 -c "import ast; ast.parse(open(PAD).read())"` foutloos parseert. Controleer dat aan het eind en laat het bestand importeerbaar achter.

Rapporteer kort: welke plaatsen je hebt gedaan, wat je per plaats niet kon vinden, en twijfelgevallen.
