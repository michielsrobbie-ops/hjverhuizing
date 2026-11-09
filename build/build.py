#!/usr/bin/env python3
"""Bouwt de statische site van HJ Verhuizing.

Inhoud komt uit content.json (geëxporteerd uit de oude WordPress/Elementor-site)
en uit de ruwe artikel-HTML in raw/. Draai:  python3 build/build.py
Uitvoer: site/  (dit is precies wat er op de hosting komt)
"""
import json, re, html, os, datetime, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "data"))
from diensten_extra import EXTRA
try:
    from lokaal import LOKAAL
except ImportError:
    LOKAAL = {}

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DATA = ROOT / "build" / "data"
C = json.load(open(DATA / "content.json"))
IMG = json.load(open(ROOT / "build" / "images.json"))
TODAY = datetime.date.today().isoformat()
VERSION = "20261105e"  # ophogen bij elke wijziging aan css/js (cache)

# ------------------------------------------------------------------ bedrijfsgegevens
BASE = "https://hjverhuizing.nl"
NAME = "HJ Verhuizing"
PHONE = "+31648577705"
PHONE_SHOW = "06 48 57 77 05"
EMAIL = "info@hjverhuizing.nl"
STREET, ZIP, CITY = "Kerkstraat 40", "8051 GN", "Hattem"
HOURS = "Ma t/m za: 9:00 - 20:00"
WA = "https://wa.me/31648577705?text=" + "Hallo%20team%20van%20HJ%20Verhuizing%2C%20ik%20zoek%20een%20vakkundig%20verhuisbedrijf.%20Kunt%20u%20contact%20met%20mij%20opnemen%3F"
WA_NA = "https://wa.me/31648577705?text=" + "Hallo%2C%20ik%20heb%20zojuist%20een%20aanvraag%20gedaan%20via%20de%20website.%20Hierbij%20alvast%20wat%20extra%20informatie%3A%20"
# Google-tags die op de huidige site draaien (Site Kit, MonsterInsights, PixelYourSite)
# AW-8464378947 is weggehaald: dat was het klantnummer van het Ads-account (846-437-8947), geen tag-ID
GTAGS = ["GT-MK4HJNPV", "G-W2LXQPG225", "AW-16718229948"]

SERVICES = [  # slug, menunaam, korte omschrijving (van de huidige homepage), icoon, pagina-id
    ("particuliere-verhuizing", "Particuliere verhuizing", "Zorgeloos overstappen naar uw nieuwe thuis met onze vakkundige en persoonlijke aanpak.", "home", "1577"),
    ("bedrijfsverhuizing", "Zakelijke verhuizing", "Efficiënte kantoorverhuizingen met een strakke planning om downtime te minimaliseren.", "office", "1583"),
    ("spoedverhuizing", "Spoedverhuizing", "Directe hulp en snelle actie in de regio Zwolle voor urgente verhuisbehoeften.", "clock", "1595"),
    ("seniorenverhuizing", "Seniorenverhuizing", "Een verhuizing met extra aandacht, geduld en volledige ontzorging van begin tot eind.", "heart", "1600"),
    ("ontruiming", "Ontruiming", "Discreet en vakkundig bezemschoon opleveren van woningen en bedrijfspanden.", "broom", "2131"),
    ("verhuisbenodigdheden", "Verhuisbenodigdheden", "Hoogwaardige dozen en materialen om uw inboedel veilig en onbeschadigd te vervoeren.", "box", "2140"),
    ("in-en-uitpak-service", "In- en uitpakservice", "Bespaar tijd en voorkom schade; onze professionals pakken alles zorgvuldig voor u in.", "pack", "1613"),
    ("demontage-service", "(De)montageservice", "Wij demonteren en monteren uw meubels vakkundig, zodat u direct kunt gaan wonen.", "tool", "1624"),
]
CITIES = [("elburg", "Elburg", "1784"), ("hattem", "Hattem", "1744"), ("heerde", "Heerde", "1776"), ("kampen", "Kampen", "1763"),
          ("oldebroek", "Oldebroek", "1771"), ("wapenveld", "Wapenveld", "1789"), ("wezep", "Wezep", "1755"), ("zalk", "Zalk", "1794"), ("zwolle", "Zwolle", "1735")]

# ---- alle plaatsen (oud: Elementor-pagina's, nieuw: build/data/plaatsen_*.py)
import importlib.util, glob as _glob, math
NIEUW = {}; COORD = {}
for _f in sorted(_glob.glob(str(Path(__file__).resolve().parent / "data" / "plaatsen_*.py"))):
    _spec = importlib.util.spec_from_file_location(Path(_f).stem, _f); _m = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_m)
    NIEUW.update(getattr(_m, "PLAATSEN", {})); COORD.update(getattr(_m, "COORD_BESTAAND", {}))
OUD_REGIO = {"zwolle": "Regio Zwolle", "kampen": "Regio Zwolle", "zalk": "Regio Zwolle", "hattem": "Veluwe", "heerde": "Veluwe",
             "wapenveld": "Veluwe", "oldebroek": "Noord-Veluwe", "wezep": "Noord-Veluwe", "elburg": "Noord-Veluwe"}
PLACES = [{"slug": s_, "naam": n_, "regio": OUD_REGIO[s_], "coord": COORD.get(s_)} for s_, n_, _ in CITIES] + \
         [{"slug": k, "naam": v["naam"], "regio": v["regio"], "coord": tuple(v["coord"])} for k, v in NIEUW.items()]
PLACES.sort(key=lambda x: x["naam"])
REGIO_ORDER = ["Regio Zwolle", "Veluwe", "Noord-Veluwe", "Salland", "Kop van Overijssel"]
TOP = ["zwolle", "kampen", "hattem", "elburg", "wezep", "heerde", "oldebroek", "apeldoorn", "deventer", "meppel"]
HOME_C = COORD.get("hattem")

def km(a, b):
    if not a or not b: return 999
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))

def nearest(slug, n=8):
    me = next(p for p in PLACES if p["slug"] == slug)
    return sorted((p for p in PLACES if p["slug"] != slug), key=lambda p: km(me["coord"], p["coord"]))[:n]

def place_link(p): return f'/verhuisbedrijf-{p["slug"]}/'

PROMISE = [  # de vier beloftes van de huidige site
    ("tool", "Vakkundige montage", "Wij demonteren en monteren uw meubels met uiterste zorg en precisie."),
    ("shield", "Veilig en verzekerd", "Uw kostbare inboedel is tijdens het hele transport volledig verzekerd."),
    ("calendar", "Planning op maat", "Ook in het weekend of op korte termijn staan wij voor u klaar."),
    ("check", "Compleet ontzorgd", "Van inpakservice tot verhuislift: wij regelen alles van A tot Z."),
]
PROMISE_TITLE = "Uw partner voor particulier en zakelijk verhuizen in regio Zwolle"
PROMISE_TEXT = ("Verhuizen is meer dan alleen spullen sjouwen; het is een nieuwe start voor u of uw onderneming. Wij bieden een persoonlijke aanpak die rust brengt in de chaos, "
                "of het nu gaat om een appartement in de binnenstad of een compleet kantoorpand. Als lokaal team kennen we de regio Zwolle, Kampen en de Noord-Veluwe op ons duimpje, "
                "waardoor we snel en efficiënt kunnen schakelen. Bij HJ Verhuizing staan zorgvuldigheid, snelheid en een transparante service altijd centraal.")
REVIEWS = [
    ("Uitstekende verhuisservice!", "Ik ben ontzettend blij dat ik dit verhuisbedrijf heb ingehuurd. Ze hebben alles voor mij overgenomen en de verhuizing verliep vlekkeloos. Zonder hun hulp had ik niet geweten hoe ik het moest doen. Hun professionaliteit en efficiëntie hebben de stress van verhuizen volledig weggenomen. Absoluut een aanrader!", "Gislaine van Leeuwaarde"),
    ("", "Mijn kantoor door de jongens zakelijk laten verhuizen. Top werk dank je mannen.", "Chris Breunis"),
    ("", "Goede communicatie en duidelijke afspraken. Alles netjes verhuisd zonder enige schade. Bedankt voor de service 💪", "Robin Magendans"),
]

# Algemene vragen: antwoorden letterlijk van de plaatspagina's, zonder plaatsnaam.
FAQ_GENERAL = {
 "kosten": ("Wat kost een verhuizing?", "<p>De prijs voor een verhuizing is altijd maatwerk. Factoren zoals de omvang van uw inboedel, de bereikbaarheid van de woning en extra wensen zoals (de)montage bepalen het tarief. Bij HJ Verhuizing werken we met eerlijke, transparante prijzen en krijgt u altijd een vrijblijvende offerte vooraf. Zo weet u precies waar u aan toe bent, zonder verrassingen achteraf. Lees ook <a href=\"/wat-kost-een-verhuizing/\">waar de prijs van een verhuizing van afhangt</a>.</p>"),
 "vooraf": ("Hoe ver van tevoren moet ik mijn verhuizing aanvragen?", "<p>Omdat steeds meer mensen kiezen voor onze vakkundige aanpak, loopt onze planning vaak snel vol. We raden daarom aan om zo vroeg mogelijk contact met ons op te nemen voor uw gewenste verhuisdatum. Heeft u echter een spoedverhuizing? Schroom dan niet om ons direct te bellen op <a href=\"tel:+31648577705\">06-48577705</a>. We kijken altijd vakkundig hoe we in onze planning kunnen schuiven om u toch zo snel mogelijk te helpen.</p>"),
 "verzekerd": ("Is mijn inboedel verzekerd tijdens de verhuizing?", "<p>Absoluut. Hoewel wij door onze bouwkundige achtergrond en uiterst voorzichtige werkwijze vrijwel altijd schadevrij werken, is uw kostbare inboedel tijdens het transport en de verhuizing volledig verzekerd. Wij behandelen uw eigendommen met de grootste zorg, alsof ze van onszelf zijn.</p>"),
 "lift": ("Beschikken jullie over een verhuislift?", "<p>Ja, wij zetten een moderne verhuislift in voor woningen met nauwe trappunten, appartementen of zware objecten die niet via de trap naar boven kunnen. Dit bespaart veel tijd en minimaliseert het risico op schade aan uw muren en meubilair. Onze verhuizers zijn vakkundig getraind om de lift veilig te bedienen. Lees ook <a href=\"/verhuislift-nodig/\">wanneer een verhuislift loont</a>.</p>"),
 "montage": ("Kunnen jullie ook meubels (de)monteren?", "<p>Dat is onze specialiteit. Dankzij onze ervaring in de bouwsector hebben wij diepgaand bouwkundig inzicht. Wij demonteren complexe meubelstukken vakkundig en zetten ze in uw nieuwe woning weer stevig in elkaar.</p>"),
 "meehelpen": ("Kan ik ook zelf meehelpen?", "<p>Bij HJ Verhuizing zijn we flexibel. Als u de kosten wilt drukken door zelf in te pakken of mee te helpen met sjouwen, is dat in overleg altijd mogelijk. Wij zorgen voor de vakkundige begeleiding en het veilige transport.</p>"),
 "checklist": ("Heeft HJ Verhuizing ook een handige verhuischecklist?", "<p>Zeker! Een vakkundige voorbereiding is het halve werk. Naast onze persoonlijke begeleiding kunt u <a href=\"/verhuischecklist/\">onze verhuischecklist</a> gebruiken. Zo weet u zeker dat u niks over het hoofd ziet voor, tijdens en na uw verhuizing.</p>"),
}
SERVICE_FAQ = {
 "particuliere-verhuizing": ["kosten", "vooraf", "verzekerd", "meehelpen"],
 "bedrijfsverhuizing": ["kosten", "verzekerd", "montage"],
 "spoedverhuizing": ["vooraf", "kosten", "verzekerd"],
 "seniorenverhuizing": ["kosten", "verzekerd", "meehelpen"],
 "in-en-uitpak-service": ["meehelpen", "kosten", "verzekerd"],
 "demontage-service": ["montage", "verzekerd", "kosten"],
 "ontruiming": ["kosten"],
 "verhuisbenodigdheden": ["meehelpen"],
}

# Titels en meta-omschrijvingen (Rank Math-waarden, opgeschoond waar ze kapot of leeg waren)
SEO = {
 "home": ("Verhuisbedrijf Zwolle en omgeving | HJ Verhuizing uit Hattem", "Verhuisbedrijf in Zwolle, Kampen en de Veluwe. Eigen verhuislift, (de)montage en inpakservice, schadevrij en ook in het weekend. Binnen 24 uur reactie."),
 "over-ons": ("Over ons | Uw verhuizer in regio Zwolle | HJ Verhuizing", "Maak kennis met HJ Verhuizing: twee gedreven ondernemers met een vakkundig team in regio Zwolle, Kampen en de Noord-Veluwe. Persoonlijk, snel en flexibel."),
 "diensten": ("Verhuisdiensten: particulier, zakelijk & spoed | HJ Verhuizing", "Alle verhuisdiensten van HJ Verhuizing: particuliere en zakelijke verhuizingen, spoed, senioren, ontruiming, inpakservice, (de)montage en verhuismaterialen."),
 "contact": ("Contact & offerte aanvragen | HJ Verhuizing", "Neem contact op met HJ Verhuizing voor een vrijblijvende offerte op maat. Bel 06 48 57 77 05, mail info@hjverhuizing.nl of vul het formulier in."),
 "kennisbank": ("Kennisbank: tips voor uw verhuizing | HJ Verhuizing", "Praktische uitleg over verhuizen: een verhuischecklist, wanneer een verhuislift loont en waar u op let bij internationaal verhuizen."),
 "particuliere-verhuizing": ("Particuliere verhuizing: vakkundige hulp | HJ Verhuizing", "Kies voor de vakkundige service van HJ Verhuizing. Wij regelen uw particuliere verhuizing van A tot Z, zorgeloos en betaalbaar. Vraag een gratis offerte aan."),
 "bedrijfsverhuizing": ("Bedrijfsverhuizing zonder downtime | HJ Verhuizing", "Bedrijfsverhuizing? HJ Verhuizing regelt uw zakelijke verhuizing met een strakke planning, minimale downtime en uiterste zorg voor uw inventaris."),
 "spoedverhuizing": ("Spoedverhuizing nodig? Direct vakkundige hulp | HJ Verhuizing", "Spoedverhuizing nodig? HJ Verhuizing staat direct voor u klaar voor een vakkundige verhuizing op korte termijn, ook binnen 24 uur. Bel ons direct."),
 "seniorenverhuizing": ("Seniorenverhuizing met geduld en zorg | HJ Verhuizing", "Seniorenverhuizing? HJ Verhuizing ontzorgt u volledig, met een vast aanspreekpunt en een planning op uw tempo. Vraag een vrijblijvende offerte aan."),
 "in-en-uitpak-service": ("Inpakservice bij uw verhuizing | HJ Verhuizing", "Inpakservice nodig? Laat uw inboedel vakkundig in- en uitpakken door HJ Verhuizing. Gelabeld per kamer en met de juiste materialen voor breekbare spullen."),
 "demontage-service": ("(De)montageservice voor meubels | HJ Verhuizing", "Meubels laten demonteren en monteren bij uw verhuizing? Dankzij onze bouwkundige achtergrond staat alles weer stevig en kaarsrecht in uw nieuwe woning."),
 "ontruiming": ("Woningontruiming, bezemschoon opgeleverd | HJ Verhuizing", "Woningontruiming of bedrijfspand ontruimen? HJ Verhuizing zorgt voor een respectvolle en discrete ontruiming met bezemschone oplevering."),
 "verhuisbenodigdheden": ("Verhuisdozen en verhuisdekens huren | HJ Verhuizing", "Verhuisbenodigdheden nodig? Huur stevige verhuisdozen en verhuisdekens bij HJ Verhuizing en krijg noppenfolie, tape en hoekbeschermers erbij."),
 "verhuisbedrijf-zwolle": ("Verhuizen in Zwolle: milieuzone en parkeren | HJ Verhuizing", "Gaat u verhuizen in Zwolle? Lees wat u regelt rond de zero-emissiezone, pollers en parkeren in de binnenstad, en hoe HJ Verhuizing uit Hattem u helpt."),
 "verhuisbedrijf-hattem": ("Verhuisbedrijf Hattem | Het verhuisbedrijf uit Hattem zelf", "HJ Verhuizing is gevestigd in Hattem en kent de Hanzestad als geen ander. Eigen verhuislift, (de)montage en inpakservice, ook in het weekend."),
 "verhuisbedrijf-wezep": ("Verhuisbedrijf Wezep | Vakkundig en dichtbij | HJ Verhuizing", "Verhuizen in Wezep? HJ Verhuizing uit Hattem is binnen tien minuten bij u: eigen verhuislift, (de)montage en inpakservice, ook in het weekend."),
 "verhuisbedrijf-kampen": ("Verhuisbedrijf Kampen | Vakkundig en dichtbij | HJ Verhuizing", "Verhuizen in Kampen of IJsselmuiden? HJ Verhuizing uit Hattem zit om de hoek: eigen verhuislift, (de)montage en inpakservice, ook in het weekend."),
 "verhuisbedrijf-oldebroek": ("Verhuisbedrijf Oldebroek | Vakkundig, dichtbij | HJ Verhuizing", "Verhuizen in Oldebroek? HJ Verhuizing uit Hattem is zo bij u: eigen verhuislift, (de)montage en inpakservice, schadevrij en ook in het weekend."),
 "verhuisbedrijf-heerde": ("Verhuisbedrijf Heerde | Vakkundig en dichtbij | HJ Verhuizing", "Verhuizen in Heerde of Wapenveld? HJ Verhuizing uit Hattem zit vlakbij: eigen verhuislift, (de)montage en inpakservice, ook in het weekend."),
 "verhuisbedrijf-elburg": ("Verhuisbedrijf Elburg | Schadevrij, dichtbij | HJ Verhuizing", "Verhuizen in Elburg? HJ Verhuizing uit Hattem verhuist u schadevrij: eigen verhuislift, (de)montage en inpakservice, ook in het weekend."),
 "verhuisbedrijf-wapenveld": ("Verhuisbedrijf Wapenveld: vakkundige hulp | HJ Verhuizing", "Verhuisbedrijf Wapenveld? Kies voor de vakkundige service van HJ Verhuizing. Wij regelen uw verhuizing op de Veluwe zorgeloos en snel. Vraag uw offerte aan."),
 "verhuisbedrijf-zalk": ("Verhuisbedrijf Zalk: vakkundige hulp | HJ Verhuizing", "Verhuisbedrijf Zalk? Kies voor de vakkundige service van HJ Verhuizing. Wij regelen uw verhuizing in de IJsseldelta zorgeloos en snel. Vraag uw offerte aan."),
 "internationaal-verhuizen": ("Internationaal verhuizen vanuit Nederland | HJ Verhuizing", "Internationale verhuizing vanuit Zwolle? Van Duitsland tot België regelt HJ Verhuizing uw transport over de grens vakkundig. Vraag een offerte aan."),
 "verhuislift-nodig": ("Verhuislift nodig? Wanneer het loont | HJ Verhuizing", "Wanneer heeft u een verhuislift nodig, wat is er op straat en aan de gevel voor nodig en is zelf huren slim? HJ Verhuizing legt het uit."),
 "wat-kost-een-verhuizing": ("Wat kost een verhuizing? De prijs uitgelegd | HJ Verhuizing", "Wat kost een verhuizing? Lees welke zes factoren de prijs bepalen, hoe een offerte op maat tot stand komt en hoe u zelf bespaart op uw verhuizing."),
 "verhuischecklist": ("Verhuischecklist: alles op volgorde | HJ Verhuizing", "Verhuizen zonder stress? Deze verhuischecklist zet alles op volgorde, van acht weken vooraf tot de sleuteloverdracht. Vink af wat u geregeld heeft."),
 "privacybeleid": ("Privacybeleid | HJ Verhuizing", "Lees hoe HJ Verhuizing omgaat met uw persoonsgegevens: welke gegevens we verzamelen, waarom, hoe lang we ze bewaren en wat uw rechten zijn."),
 "cookie-policy-eu": ("Cookiebeleid | HJ Verhuizing", "Welke cookies gebruikt hjverhuizing.nl en waarvoor? Lees ons cookiebeleid en pas uw keuze op elk moment aan."),
}
POSTS = [  # slug, id, datum, laatst gewijzigd, afbeelding, korte intro
    ("wat-kost-een-verhuizing", "kosten", "2026-10-31", "2026-10-31", "stel-lege-woning", "Waar hangt de prijs van een verhuizing van af, hoe komt een offerte tot stand en hoe bespaart u kosten?"),
    ("verhuischecklist", "3028", "2026-10-09", "2026-10-09", "dozen-nieuwe-woning", "Een verhuischecklist die alles op volgorde zet, van acht weken vooraf tot de sleuteloverdracht."),
    ("verhuislift-nodig", "3022", "2026-10-09", "2026-10-09", "verhuiswagen-vol", "Wanneer heeft u een verhuislift nodig, wat is er op straat en aan de gevel voor nodig en is zelf huren slim?"),
    ("internationaal-verhuizen", "2912", "2026-06-13", "2026-10-09", "verhuiswagen-laden", "Verhuizen naar Duitsland, België of verder? Waar u op let bij een verhuizing over de grens."),
]

# ------------------------------------------------------------------ iconen (lijnstijl, 24x24)
ICON = {
 "home": '<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 9.5V20h13V9.5"/><path d="M10 20v-5.5h4V20"/>',
 "office": '<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M8 7h2M14 7h2M8 11h2M14 11h2M8 15h2M14 15h2M11 21v-3h2v3"/>',
 "clock": '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2.5M9.5 2.5h5M12 2.5V5"/>',
 "heart": '<path d="M12 20s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7a4.3 4.3 0 0 1 7.5 2.8C19.5 15.4 12 20 12 20Z"/>',
 "broom": '<path d="M14.5 3.5 10 12"/><path d="M6 12h8l2 9H4l2-9Z"/><path d="M8 16.5v4.5M12 16.5v4.5"/>',
 "box": '<path d="M3.5 7.5 12 3l8.5 4.5v9L12 21l-8.5-4.5v-9Z"/><path d="m3.5 7.5 8.5 4.5 8.5-4.5M12 12v9"/>',
 "pack": '<path d="M4 9h16v11H4z"/><path d="M4 9l2-5h12l2 5M9.5 13h5"/>',
 "tool": '<path d="M14.5 6.5a4 4 0 0 0 5 5L12 19a2.1 2.1 0 0 1-3-3l7.5-7.5"/><path d="M14.5 6.5 17 4l3 3-2.5 2.5"/>',
 "shield": '<path d="M12 3 4.5 6v6c0 4.5 3.2 7.8 7.5 9 4.3-1.2 7.5-4.5 7.5-9V6L12 3Z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
 "calendar": '<rect x="3.5" y="5" width="17" height="15.5" rx="1.5"/><path d="M3.5 10h17M8 3v4M16 3v4M8 14h2M14 14h2M8 17h2"/>',
 "check": '<circle cx="12" cy="12" r="8.5"/><path d="m8 12.3 2.7 2.7 5.3-5.5"/>',
 "phone": '<path d="M5 3.5h3.5l1.5 4.5-2.2 1.4a11 11 0 0 0 6.8 6.8l1.4-2.2 4.5 1.5V19a1.5 1.5 0 0 1-1.6 1.5A16.5 16.5 0 0 1 3.5 5.1 1.5 1.5 0 0 1 5 3.5Z"/>',
 "mail": '<rect x="3" y="5" width="18" height="14" rx="1.5"/><path d="m3.5 6 8.5 7 8.5-7"/>',
 "pin": '<path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.3"/>',
 "time": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
 "people": '<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.6"/><path d="M15.5 14.2A5 5 0 0 1 21 19"/>',
 "bolt": '<path d="M13 3 5 13.5h6L10 21l8-10.5h-6L13 3Z"/>',
 "chev": '<path d="m6 9 6 6 6-6"/>',
 "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
 "close": '<path d="M6 6l12 12M18 6 6 18"/>',
}
def icon(name, cls=""):
    return f'<svg{(" class=" + chr(34) + cls + chr(34)) if cls else ""} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON[name]}</svg>'
STAR = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9L12 3Z"/></svg>'
WA_SVG = '<svg viewBox="0 0 32 32" fill="currentColor" aria-hidden="true"><path d="M16 3a13 13 0 0 0-11.2 19.6L3 29l6.6-1.7A13 13 0 1 0 16 3Zm0 23.6a10.6 10.6 0 0 1-5.4-1.5l-.4-.2-3.9 1 1-3.8-.2-.4A10.6 10.6 0 1 1 16 26.6Zm5.8-7.9c-.3-.2-1.9-.9-2.2-1s-.5-.2-.7.2-.8 1-1 1.2-.4.2-.7.1a8.7 8.7 0 0 1-4.3-3.8c-.3-.6.3-.5 1-1.7.1-.2 0-.4 0-.5l-1-2.4c-.3-.6-.5-.5-.7-.5h-.6a1.2 1.2 0 0 0-.9.4 3.7 3.7 0 0 0-1.1 2.7 6.4 6.4 0 0 0 1.3 3.4 14.7 14.7 0 0 0 5.7 5c2.1.9 2.9 1 4 .8a3.4 3.4 0 0 0 2.2-1.6 2.8 2.8 0 0 0 .2-1.6c-.1-.2-.3-.3-.6-.4Z"/></svg>'

# ------------------------------------------------------------------ helpers
esc = lambda s: html.escape(s or "", quote=True)

def img(name, sizes="100vw", cls="", eager=False, alt=None, w=None):
    m = IMG[name]; ws = m["widths"]
    srcset = ", ".join(f"/img/{name}-{x}.webp {x}w" for x in ws)
    default = [x for x in ws if x >= 800] or ws
    W = default[0]; H = round(W * m["ratio"])
    a = esc(m["alt"] if alt is None else alt)
    attrs = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return f'<img src="/img/{name}-{W}.webp" srcset="{srcset}" sizes="{sizes}" width="{W}" height="{H}" alt="{a}"{(" class=" + chr(34) + cls + chr(34)) if cls else ""} {attrs}>'

def local(u):
    """Absolute interne links relatief maken."""
    return (u or "").replace("https://hjverhuizing.nl", "").replace("http://hjverhuizing.nl", "") or "/"

def clean_html(h):
    h = local(h) if h else h
    h = re.sub(r'href="https?://hjverhuizing\.nl', 'href="', h or "")
    h = h.replace('href="/home/"', 'href="/"').replace('href="/home"', 'href="/"')
    h = h.replace("<br><br>", "</p><p>").replace("\n", " ")
    h = re.sub(r"<p>\s*</p>", "", h)
    h = re.sub(r"\s{2,}", " ", h)
    # 'Kop tekst' in alinea's met vetgedrukte kop: zet een dubbele punt / regel
    return h.strip()

def tidy_title(t):
    t = t.replace("SpoedVerhuizing", "Spoedverhuizing").replace("SeniorenVerhuizing", "Seniorenverhuizing")
    return t

def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>"

ORG_ID = BASE + "/#organisatie"
def org_schema():
    return {
        "@type": "MovingCompany", "@id": ORG_ID, "name": NAME, "url": BASE + "/",
        "logo": BASE + "/img/logo-512.png", "image": BASE + "/img/og-team-laadt-verhuiswagen.jpg",
        "telephone": PHONE, "email": EMAIL,
        "address": {"@type": "PostalAddress", "streetAddress": STREET, "postalCode": ZIP, "addressLocality": CITY, "addressCountry": "NL"},
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], "opens": "09:00", "closes": "20:00"}],
        "areaServed": [{"@type": "City", "name": p["naam"]} for p in PLACES],
        "knowsAbout": [s[1] for s in SERVICES],
    }

def crumbs_schema(items):
    return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + u} for i, (n, u) in enumerate(items)]}

def faq_schema(items):
    return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a).strip()}} for q, a in items]}

# ------------------------------------------------------------------ vaste onderdelen
def nav(current):
    def li(href, label):
        cur = ' aria-current="page"' if current == href else ""
        return f'<li><a href="{href}"{cur}>{label}</a></li>'
    sub_s = "".join(li(f"/diensten/{s}/", n) for s, n, *_ in SERVICES)
    top = [p for t in TOP for p in PLACES if p["slug"] == t]
    sub_c = li("/werkgebied/", f"Hele werkgebied ({len(PLACES)} plaatsen)") + "".join(li(place_link(p), f"Verhuisbedrijf {p['naam']}") for p in top)
    dienst_cur = ' aria-current="page"' if current == "/diensten/" else ""
    return f'''<nav class="nav" id="nav" aria-label="Hoofdmenu"><ul>
{li("/", "Home")}
<li class="has-sub"><button class="sub-toggle" type="button" aria-expanded="false">Diensten {icon("chev")}</button><ul class="sub"><li><a href="/diensten/"{dienst_cur}>Alle diensten</a></li>{sub_s}</ul></li>
<li class="has-sub"><button class="sub-toggle" type="button" aria-expanded="false">Werkgebied {icon("chev")}</button><ul class="sub">{sub_c}</ul></li>
{li("/over-ons/", "Over ons")}
{li("/kennisbank/", "Kennisbank")}
{li("/contact/", "Contact")}
</ul></nav>'''

def header(current):
    return f'''<a class="skip" href="#main">Naar de inhoud</a>
<header class="site-header"><div class="wrap">
<a class="logo" href="/" aria-label="HJ Verhuizing, naar de homepage"><img src="/img/logo-128.webp" width="{round(IMG['_logo']['w']*128/IMG['_logo']['h'])}" height="128" alt="HJ Verhuizing"></a>
{nav(current)}
<div class="header-cta"><a class="btn btn--offerte" href="/contact/">Offerte aanvragen</a><a class="btn btn--navy" href="tel:{PHONE}" data-track="bellen" aria-label="Bel ons: {PHONE_SHOW}">{icon("phone")}<span>Bel ons</span></a></div>
<button class="menu-toggle" type="button" aria-controls="nav" aria-expanded="false"><span class="sr-only">Menu</span>{icon("menu")}</button>
</div></header>'''

def footer():
    dl = "".join(f'<li><a href="/diensten/{s}/">{n}</a></li>' for s, n, *_ in SERVICES)
    cl = "".join(f'<li><a href="{place_link(p)}">{p["naam"]}</a></li>' for t in TOP for p in PLACES if p["slug"] == t) + f'<li><a href="/werkgebied/">Alle {len(PLACES)} plaatsen</a></li>'
    return f'''<footer class="site-footer">
<div class="wrap cols">
<div><img class="foot-logo" src="/img/logo-128.webp" width="{round(IMG['_logo']['w']*128/IMG['_logo']['h'])}" height="128" alt="HJ Verhuizing" loading="lazy">
<address><a href="mailto:{EMAIL}">{EMAIL}</a><br><a href="tel:{PHONE}" data-track="bellen">{PHONE_SHOW}</a><br>{STREET}<br>{ZIP} {CITY}<br>{HOURS}</address></div>
<div><h2>Navigatie</h2><ul><li><a href="/">Home</a></li><li><a href="/over-ons/">Over ons</a></li><li><a href="/diensten/">Diensten</a></li><li><a href="/kennisbank/">Kennisbank</a></li><li><a href="/contact/">Contact</a></li></ul></div>
<div><h2>Diensten</h2><ul>{dl}</ul></div>
<div><h2>Verhuisbedrijf in de regio</h2><ul>{cl}</ul></div>
</div>
<div class="bottom"><div class="wrap"><p style="margin:0">© {datetime.date.today().year} HJ Verhuizing. Alle rechten voorbehouden. Website gemaakt door <a class="maxx" href="https://maxxmarketing.eu" rel="noopener">Maxx Marketing</a></p>
<nav aria-label="Juridisch"><a href="/cookie-policy-eu/">Cookiebeleid</a><a href="/privacybeleid/">Privacybeleid</a><button type="button" data-consent-open>Cookie-instellingen</button></nav></div></div>
</footer>
<a class="float-wa" href="{WA}" target="_blank" rel="noopener" data-track="whatsapp" aria-label="Stuur ons een WhatsApp-bericht">{WA_SVG}</a>
<div class="mbar"><a class="btn btn--navy" href="tel:{PHONE}" data-track="bellen">{icon("phone")}Bel direct</a><a class="btn" href="/contact/#offerte" data-offerte>Gratis offerte</a></div>
<div class="consent" id="consent" role="dialog" aria-labelledby="consent-title" hidden>
<h2 id="consent-title">Cookies op deze website</h2>
<p>Wij gebruiken cookies om te meten hoe de site gebruikt wordt en om onze advertenties te verbeteren. Dat doen we alleen als u akkoord gaat. <a href="/cookie-policy-eu/">Meer over cookies</a></p>
<div class="btn-row"><button class="btn btn--light" type="button" data-consent="denied">Alleen noodzakelijk</button><button class="btn" type="button" data-consent="granted">Akkoord</button></div>
</div>'''

def head(title, desc, path, og_img="team-laadt-verhuiswagen", schema=None, noindex=False, preload=None, extra=""):
    canonical = BASE + path
    g = "".join(f"gtag('config','{t}');" for t in GTAGS)
    robots = '<meta name="robots" content="noindex, follow">' if noindex else '<meta name="robots" content="index, follow, max-image-preview:large">'
    pre = f'<link rel="preload" as="image" href="/img/{preload}-1200.webp" imagesrcset="{", ".join(f"/img/{preload}-{x}.webp {x}w" for x in IMG[preload]["widths"])}" imagesizes="100vw" fetchpriority="high">' if preload else ""
    graph = {"@context": "https://schema.org", "@graph": [org_schema(), {"@type": "WebSite", "@id": BASE + "/#website", "url": BASE + "/", "name": NAME, "publisher": {"@id": ORG_ID}, "inLanguage": "nl-NL"}] + (schema or [])}
    return f'''<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="google-site-verification" content="s4vVQVV3n0cSMQYwHKbhDIfkVoGnxXrPpo7ZTuNKd9o">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{robots}
<link rel="canonical" href="{canonical}">
<meta property="og:locale" content="nl_NL">
<meta property="og:type" content="{"article" if extra == "article" else "website"}">
<meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE}/img/og-{og_img}.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#072C50">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preload" href="/fonts/heebo-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/pt-sans-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
{pre}
<link rel="stylesheet" href="/css/style.css?v={VERSION}">
<script>
window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}
var c=null;try{{c=localStorage.getItem('hj_consent');}}catch(e){{}}
gtag('consent','default',{{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied',wait_for_update:500}});
if(c==='granted'){{gtag('consent','update',{{ad_storage:'granted',ad_user_data:'granted',ad_personalization:'granted',analytics_storage:'granted'}});}}
gtag('js',new Date());{g}
</script>
<script async src="https://www.googletagmanager.com/gtag/js?id={GTAGS[0]}"></script>
{ld(graph)}
</head>'''

def page(title, desc, path, body, current=None, **kw):
    return head(title, desc, path, **kw) + f'''
<body>
{header(current or path)}
<main id="main">
{body}
</main>
{footer()}
<script src="/js/main.js?v={VERSION}" defer></script>
</body>
</html>
'''

# ------------------------------------------------------------------ formulieren
def form(kind, page_path, button, title=None):
    """kind: quick (home), offerte (dienst/plaats), contact."""
    f = []
    def fld(name, label, typ="text", req=True, full=False, ac=None, extra=""):
        r = " required" if req else ""
        opt = "" if req else ' <span class="opt">(optioneel)</span>'
        a = f' autocomplete="{ac}"' if ac else ""
        inp = f'<textarea id="{kind}-{name}" name="{name}" rows="4"{r}{extra}></textarea>' if typ == "textarea" else f'<input id="{kind}-{name}" name="{name}" type="{typ}"{a}{r}{extra}>'
        f.append(f'<div class="field{" field--full" if full else ""}"><label for="{kind}-{name}">{label}{opt}</label>{inp}</div>')
    if kind == "quick":
        fld("naam", "Naam", ac="name"); fld("postcode", "Postcode", ac="postal-code", extra=' inputmode="text" maxlength="7"')
        fld("telefoon", "Telefoon", "tel", ac="tel"); fld("email", "E-mail", "email", ac="email")
    elif kind == "offerte":
        fld("naam", "Naam", ac="name", full=True); fld("telefoon", "Telefoon", "tel", ac="tel", full=True); fld("email", "E-mail", "email", ac="email", full=True)
        fld("bericht", "Wat wilt u laten verhuizen?", "textarea", req=False, full=True)
    else:
        fld("naam", "Naam", ac="name"); fld("telefoon", "Telefoon", "tel", ac="tel")
        fld("email", "E-mail", "email", ac="email", full=True)
        fld("onderwerp", "Onderwerp", req=False); fld("bedrijf", "Bedrijf", req=False, ac="organization")
        fld("bericht", "Bericht", "textarea", req=False, full=True)
    hidden = (f'<input type="hidden" name="formulier" value="{kind}"><input type="hidden" name="pagina" value="{page_path}">'
              '<input type="hidden" name="ts" value="">'
              '<div class="hp" aria-hidden="true"><label for="' + kind + '-website">Website</label><input id="' + kind + '-website" name="website" type="text" tabindex="-1" autocomplete="off"></div>')
    btn = f'<button class="btn" type="submit">{button}</button>'
    note = '<p class="form-note">We gebruiken uw gegevens alleen om contact met u op te nemen over uw verhuizing. <a href="/privacybeleid/">Privacybeleid</a></p>' if kind != "quick" else ""
    status = '<p class="form-status" role="alert"></p>'
    order = "".join(f) + hidden + (btn + note if kind != "quick" else btn) + status
    return f'<form class="form-grid hj-form" action="/verzend.php" method="post" accept-charset="utf-8">{order}</form>'

# ------------------------------------------------------------------ secties
def eyebrow(t): return f'<p class="eyebrow">{t}</p>'

def promise_section(mist=True):
    items = "".join(f'<li><span class="ico">{icon(i)}</span><h3>{t}</h3><p>{d}</p></li>' for i, t, d in PROMISE)
    return f'''<section class="section{" section--mist" if mist else ""}" aria-labelledby="belofte"><div class="wrap">
<div class="promise-head"><div>{eyebrow("Onze belofte")}<h2 id="belofte">{PROMISE_TITLE}</h2></div><p>{PROMISE_TEXT}</p></div>
<ul class="promise">{items}</ul></div></section>'''

def services_list(current=None):
    out = []
    for s, n, d, i, _ in SERVICES:
        if s == current: continue
        out.append(f'<li class="service"><a href="/diensten/{s}/"><span class="ico">{icon(i)}</span><span><h3>{n}</h3><p>{d}</p></span></a></li>')
    return f'<ul class="services">{"".join(out)}</ul>'

def reviews_section(mist=False, img_name=None):
    cards = []
    for t, q, n in REVIEWS:
        tt = f"<b>{t}</b>" if t else ""
        cards.append(f'<li><figure class="review"><blockquote>{tt}“{q}”</blockquote><figcaption>{n}</figcaption></figure></li>')
    return f'''<section class="section{" section--mist" if mist else ""}" aria-labelledby="reviews"><div class="wrap">
<div class="section-head">{eyebrow("Ervaringen")}<h2 id="reviews">Wat onze klanten zeggen</h2></div>
<ul class="reviews">{"".join(cards)}</ul></div></section>'''

def cta_band(img_name="stel-tussen-verhuisdozen", title="Klaar voor een zorgeloze verhuizing?"):
    return f'''<section class="band" aria-labelledby="cta-band"><div class="band__media">{img(img_name)}</div><div class="wrap">
<h2 id="cta-band">{title}</h2>
<p>Neem vandaag nog contact op. Wij komen graag vrijblijvend langs om uw situatie te bekijken en een scherpe offerte op maat te maken.</p>
<div class="btn-row"><a class="btn" href="/contact/">Gratis offerte</a><a class="btn btn--ghost" href="tel:{PHONE}" data-track="bellen">{icon("phone")}Bel direct</a></div>
</div></section>'''

def spoed_band():
    return f'''<section class="spoed" aria-labelledby="spoed"><div class="wrap">
<div class="spoed__text"><h2 id="spoed">Spoedverhuizing?</h2><p>Neem contact met ons op en wij staan direct voor u klaar!</p>
<div class="btn-row"><a class="btn" href="tel:{PHONE}" data-track="bellen">{icon("phone")}Bel direct</a><a class="btn btn--ghost" href="/diensten/spoedverhuizing/">Over spoedverhuizingen</a></div></div>
<img src="/img/verhuizer-uitgesneden-704.webp" width="704" height="901" alt="" loading="lazy">
</div></section>'''

def werkgebied_svg(highlight=None, compact=False):
    """Getekende kaart: alle plaatsen geprojecteerd op hun coördinaten, ringen op 10/20/30 km van Hattem."""
    pts = [p for p in PLACES if p["coord"]]
    if not pts or not HOME_C: return ""
    lat0 = math.radians(HOME_C[0]); kx = 111.32 * math.cos(lat0); ky = 110.57
    xy = {p["slug"]: ((p["coord"][1] - HOME_C[1]) * kx, (HOME_C[0] - p["coord"][0]) * ky) for p in pts}
    R = max(max(abs(x), abs(y)) for x, y in xy.values()) + 4
    W = 600; sc = W / (2 * R); cx = cy = W / 2
    P = lambda v: (cx + v[0] * sc, cy + v[1] * sc)
    out = [f'<svg class="map-svg" viewBox="0 0 {W} {W}" role="img" aria-label="Kaart van het werkgebied van HJ Verhuizing rond Hattem">',
           f'<rect width="{W}" height="{W}" rx="18" fill="#EEF2F5"/>']
    for r in (10, 20, 30):
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r*sc:.1f}" fill="none" stroke="#C9D3DD" stroke-dasharray="4 6"/>')
        out.append(f'<text x="{cx + r*sc*0.71 + 4:.1f}" y="{cy - r*sc*0.71 - 4:.1f}" class="ring">{r} km</text>')
    # labels plaatsen zonder overlap: probeer rechts, links, boven, onder
    placed = []  # (x0,y0,x1,y1) van punten en labels
    for p in pts:
        x, y = P(xy[p["slug"]]); placed.append((x - 7, y - 7, x + 7, y + 7))
    def free(b): return all(b[2] < q[0] or b[0] > q[2] or b[3] < q[1] or b[1] > q[3] for q in placed)
    order = sorted(pts, key=lambda p: (p["slug"] not in ("hattem", highlight), km(HOME_C, p["coord"])))
    labels = {}
    for p in order:
        x, y = P(xy[p["slug"]]); big = p["slug"] in ("hattem", highlight)
        w = len(p["naam"]) * (8.6 if big else 7.3); h = 15 if big else 13; rr = 10
        cands = [(x + rr, y + 4, "start"), (x - rr, y + 4, "end"), (x, y - rr - 2, "middle"), (x, y + rr + h - 2, "middle"),
                 (x + rr, y - rr + 2, "start"), (x - rr, y - rr + 2, "end"), (x + rr, y + rr + 6, "start"), (x - rr, y + rr + 6, "end")]
        for lx, ly, an in cands:
            x0 = lx if an == "start" else (lx - w if an == "end" else lx - w / 2)
            box = (x0 - 2, ly - h + 2, x0 + w + 2, ly + 3)
            if box[0] > 2 and box[2] < W - 2 and box[1] > 2 and box[3] < W - 2 and free(box):
                break
        placed.append(box); labels[p["slug"]] = (lx, ly, an)
    for p in sorted(pts, key=lambda p: p["slug"] in ("hattem", highlight)):
        x, y = P(xy[p["slug"]]); home = p["slug"] == "hattem"; hi = p["slug"] == highlight
        rr = 9 if home else (8 if hi else 5.5)
        fill = "#072C50" if home else ("#EC6E31" if hi else "#fff")
        stroke = "#EC6E31" if home else "#072C50"
        lx, ly, an = labels[p["slug"]]
        out.append(f'<a href="{place_link(p)}"><circle cx="{x:.1f}" cy="{y:.1f}" r="{rr}" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>'
                   f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{an}" class="lbl{" lbl--hi" if (hi or home) else ""}">{esc(p["naam"])}</text></a>')
    out.append("</svg>")
    return "".join(out)

def areas_section(mist=False, exclude=None, title="Verhuisbedrijf in uw regio"):
    groups = []
    for r in REGIO_ORDER:
        ps = sorted([p for p in PLACES if p["regio"] == r and p["slug"] != exclude], key=lambda p: km(HOME_C, p["coord"]))
        if ps:
            groups.append(f'<div class="area-group"><h3>{r}</h3><ul class="areas">' + "".join(f'<li><a href="{place_link(p)}">{icon("pin")}{p["naam"]}</a></li>' for p in ps) + "</ul></div>")
    return f'''<section class="section section--tight{" section--mist" if mist else ""}" aria-labelledby="werkgebied"><div class="wrap">
<div class="section-head">{eyebrow("Werkgebied")}<h2 id="werkgebied">{title}</h2>
<p>Vanuit Hattem werken wij in de wijde regio rondom Zwolle, Kampen, Salland en de Veluwe. Bekijk het <a href="/werkgebied/">hele werkgebied op de kaart</a>.</p></div>
<div class="area-groups">{"".join(groups)}</div></div></section>'''

def faq_section(items, title, intro=None, mist=False):
    det = "".join(f'<details><summary>{esc(q)}</summary><div class="answer">{a}</div></details>' for q, a in items)
    intro = f"<p>{intro}</p>" if intro else ""
    return f'''<section class="section{" section--mist" if mist else ""}" aria-labelledby="faq"><div class="wrap">
<div class="section-head">{eyebrow("Veelgestelde vragen")}<h2 id="faq">{title}</h2>{intro}</div>
<div class="faq">{det}</div></div></section>'''

def posts_section(mist=False):
    cards = []
    for slug, pid, d, mod, im, intro in POSTS:
        t = SEO[slug][0].split(" | ")[0]
        cards.append(f'<li><a class="post-card" href="/{slug}/">{img(im, "(max-width:900px) 100vw, 33vw")}<span class="post-card__body"><h3>{esc(post_title(slug))}</h3><p>{esc(intro)}</p><span class="more">Lees verder</span></span></a></li>')
    return f'''<section class="section{" section--mist" if mist else ""}" aria-labelledby="kennisbank"><div class="wrap">
<div class="section-head">{eyebrow("Kennisbank")}<h2 id="kennisbank">Goed voorbereid verhuizen</h2></div>
<ul class="posts">{"".join(cards)}</ul></div></section>'''

def contact_card():
    return f'''<div class="card"><h2 class="h3">Liever direct contact?</h2>
<ul class="contact-list">
<li><span class="ico">{icon("phone")}</span><span><a href="tel:{PHONE}" data-track="bellen">{PHONE_SHOW}</a><small>{HOURS}</small></span></li>
<li><span class="ico">{icon("mail")}</span><span><a href="mailto:{EMAIL}">{EMAIL}</a><small>Wij reageren binnen 24 uur</small></span></li>
<li><span class="ico">{WA_SVG}</span><span><a href="{WA}" target="_blank" rel="noopener" data-track="whatsapp">WhatsApp ons</a><small>Stuur gerust een foto van wat er mee moet</small></span></li>
</ul></div>'''

def map_block(q, label):
    src = "https://maps.google.com/maps?q=" + q.replace(" ", "+") + "&z=13&output=embed"
    return f'''<div class="map" data-map="{esc(src)}"><p class="map__note">De kaart komt van Google Maps en laadt pas als u erop klikt.</p><button class="btn btn--navy" type="button">{icon("pin")}Toon kaart van {esc(label)}</button></div>'''

def hero_page(title, lead, crumbs, bg, buttons=True, facts=True, meta=None):
    cl = "".join((f'<li><a href="{u}">{esc(n)}</a></li>' if i < len(crumbs) - 1 else f'<li aria-current="page">{esc(n)}</li>') for i, (n, u) in enumerate(crumbs))
    btns = f'<div class="btn-row"><a class="btn" href="#offerte">Gratis offerte</a><a class="btn btn--ghost" href="tel:{PHONE}" data-track="bellen">{icon("phone")}Bel {PHONE_SHOW}</a></div>' if buttons else ""
    fx = f'<ul class="hero__facts"><li>{icon("check")}Vrijblijvende offerte op maat</li><li>{icon("shield")}Inboedel verzekerd</li><li>{icon("calendar")}Ook in het weekend</li></ul>' if facts else ""
    lead_html = f'<p class="hero__lead">{lead}</p>' if lead else ""
    m = f'<p class="article-meta">{meta}</p>' if meta else ""
    return f'''<section class="hero hero--page"><div class="hero__media">{img(bg, eager=True, alt="")}</div><div class="wrap">
<nav aria-label="Kruimelpad"><ol class="crumbs">{cl}</ol></nav>
<h1>{esc(title)}</h1>{m}{lead_html}{btns}{fx}
</div></section>'''

# ------------------------------------------------------------------ inhoud uit Elementor
NAME_BY_URL = {}  # oude upload-url -> nieuwe afbeeldingnaam
for k, v in IMG.items():
    if not k.startswith("_"): NAME_BY_URL[v["src"]] = k
def img_name(url):
    if not url: return None
    return NAME_BY_URL.get(url.split("wp-content/uploads/")[-1])

SHARED_STOP = ("Klaar voor een zorgeloze verhuizing?", "Uw partner voor particulier", "Spoedverhuizing?")
def parse_detail(pid):
    """Haal de eigen inhoud uit een dienst- of plaatspagina."""
    B = C[pid]["blocks"]
    hs = [b for b in B if b["t"] == "h"]
    hero_title = hs[0]["text"]
    lead = next(b["html"] for b in B if b["t"] == "text")
    bg = img_name(next(b["bg"] for b in B if b["t"] == "section" and b.get("bg")))
    mapq = next((b["q"] for b in B if b["t"] == "map"), None)
    # hoofdinhoud: vanaf de eerste afbeelding na het formulier tot de gedeelde blokken
    i = next(i for i, b in enumerate(B) if b["t"] == "form")
    main_img = None; parts = []; stop = False; faq_title = None; faq_intro = None; faq = []
    for b in B[i + 1:]:
        if b["t"] == "h" and b["text"].startswith(SHARED_STOP): stop = True
        if b["t"] == "h" and b["text"].startswith("Veelgestelde vragen"):
            faq_title = b["text"]; stop = "faq"; continue
        if stop == "faq":
            if b["t"] == "text" and faq_intro is None: faq_intro = re.sub(r"</?p>", "", b["html"])
            if b["t"] == "faq": faq = [(x["q"], clean_html(x["a"])) for x in b["items"]]
            continue
        if stop: continue
        if b["t"] == "img" and not main_img: main_img = img_name(b["url"])
        elif b["t"] == "h": parts.append(("h", b["text"]))
        elif b["t"] == "text": parts.append(("text", clean_html(b["html"])))
        elif b["t"] == "box": parts.append(("box", b["title"], clean_html(b["html"])))
    return dict(title=hero_title, lead=re.sub(r"</?(p|strong)>", "", lead), bg=bg, map=mapq, img=main_img, parts=parts, faq_title=faq_title, faq_intro=faq_intro, faq=faq)

def fix_inline_heads(h):
    """'<p><strong>Kop</strong> tekst</p>' (kopje zonder leesteken) -> kopje + alinea."""
    return re.sub(r"<p><strong>([^<:]{3,60})</strong>\s+", r"<h3>\1</h3><p>", h)

def render_parts(parts):
    out = []
    for p in parts:
        if p[0] == "h": out.append(f"<h2>{esc(tidy_title(p[1]))}</h2>")
        elif p[0] == "text": out.append(fix_inline_heads(p[1]))
        else: out.append(f'<div class="callout"><h3>{esc(p[1])}</h3>{p[2] if p[2].startswith("<") else "<p>" + p[2] + "</p>"}</div>')
    return "\n".join(out)

def sidebar(path, links=None, title="Gratis offerte"):
    l = f'<div class="card"><h2 class="h3">{links[0]}</h2><ul class="mini-links">{links[1]}</ul></div>' if links else ""
    return f'''<aside class="aside" id="offerte" aria-label="Offerte aanvragen">
<div class="card card--form"><h2>{title}</h2><p class="lead">Vul uw gegevens in en wij nemen binnen 24 uur contact met u op voor een verhuizing op maat.</p>{form("offerte", path, "Offerte aanvragen")}</div>
{contact_card()}{l}</aside>'''

# ------------------------------------------------------------------ pagina's
pages = {}  # pad -> html
sitemap = []  # (pad, lastmod, prioriteit)

def add(path, html_, lastmod=TODAY, prio="0.7", index=True):
    # geen formulier op deze pagina: de offerteknop gaat dan naar het formulier op de contactpagina
    if 'id="offerte"' not in html_:
        html_ = html_.replace('href="#offerte"', 'href="/contact/#offerte"')
    pages[path] = html_
    if index: sitemap.append((path, lastmod, prio))

def post_title(slug):
    return {"wat-kost-een-verhuizing": "Wat kost een verhuizing? Hier hangt de prijs van af", "verhuischecklist": "Verhuischecklist: alles op volgorde", "verhuislift-nodig": "Verhuislift nodig? Wanneer het loont en waar u op let",
            "internationaal-verhuizen": "Internationaal verhuizen vanuit Nederland"}[slug]

# ---- home
def build_home():
    hero = f'''<section class="hero hero--home"><div class="hero__media">{img("kennismaking-voordeur", eager=True, alt="")}</div><div class="wrap">
<h1>Uw vakkundig <span class="hl">verhuisbedrijf<svg viewBox="0 0 300 20" preserveAspectRatio="none" aria-hidden="true"><path d="M4 14C60 5 170 3 296 9"/></svg></span> in Zwolle en omgeving</h1>
<p class="hero__lead">HJ Verhuizing: uw vakkundige partner voor particuliere en zakelijke verhuizingen. Regio Zwolle en Noord-Veluwe; wij regelen het zware werk met zorg en precisie.</p>
<div class="btn-row"><a class="btn" href="#prijsopgave">Gratis offerte aanvragen</a><a class="btn btn--ghost" href="tel:{PHONE}" data-track="bellen">{icon("phone")}Bel {PHONE_SHOW}</a></div>
</div></section>
<section class="quote-bar" aria-labelledby="prijsopgave"><div class="wrap"><div class="quote-bar__card">
<div><h2 id="prijsopgave">Ontvang een prijsopgave op maat</h2><p>Wij nemen binnen 24 uur contact met u op.</p></div>
{form("quick", "/", "Ja, ik wil een prijsopgave")}
</div></div></section>'''
    who = f'''<section class="section" aria-labelledby="wie"><div class="wrap split">
<div class="photo-stat">{img("verhuizers-voordeur", "(max-width:900px) 100vw, 50vw")}<div class="stat-badge"><b>250+</b><span>verhuizingen</span></div></div>
<div>{eyebrow("Wie zijn wij?")}<h2 id="wie">De gezichten achter HJ Verhuizing</h2>
<p>Bij HJ Verhuizing staan wij, twee gedreven ondernemers, klaar om uw verhuizing soepel te laten verlopen. Met een sterke focus op persoonlijke service bieden wij snelle, flexibele en efficiënte oplossingen in de regio Zwolle en omstreken. Wij denken niet alleen met u mee, maar steken ook echt de handen uit de mouwen om uw inboedel veilig naar de nieuwe plek te brengen.</p>
<ul class="points"><li class="point"><span class="ico">{icon("people")}</span><div><h3>Persoonlijk en betrokken</h3><p>Geen groot anoniem bedrijf, maar direct contact met de verhuizers die het werk uitvoeren.</p></div></li>
<li class="point"><span class="ico">{icon("bolt")}</span><div><h3>Snel en flexibel</h3><p>Wij passen ons aan uw planning aan en zorgen voor een zorgeloze verhuisdag zonder verrassingen.</p></div></li></ul>
<a class="btn btn--navy" href="/over-ons/">Over ons</a></div>
</div></section>'''
    diensten = f'''<section class="section" aria-labelledby="diensten"><div class="wrap services-split">
{img("team-laadt-verhuiswagen", "(max-width:900px) 100vw, 40vw")}
<div><div class="section-head">{eyebrow("Wat wij doen")}<h2 id="diensten">Onze diensten</h2></div>{services_list()}
<p style="margin-top:28px"><a class="btn btn--navy" href="/diensten/">Bekijk alle diensten</a></p></div>
</div></section>'''
    steps = [("Contact", "Bel, WhatsApp of vul het formulier in. Wij nemen binnen 24 uur contact met u op."),
             ("Vrijblijvend langs", "Wij komen graag vrijblijvend langs om uw situatie te bekijken: de omvang van de inboedel, de bereikbaarheid en uw wensen."),
             ("Offerte op maat", "U krijgt een heldere offerte zonder verrassingen achteraf. Geen standaardtarief, maar een prijs die past bij uw verhuizing."),
             ("De verhuisdag", "Ons team pakt, demonteert, vervoert en monteert volgens de planning die we vooraf met u hebben besproken.")]
    werkwijze = f'''<section class="section section--tight" aria-labelledby="werkwijze"><div class="wrap">
<div class="section-head">{eyebrow("Werkwijze")}<h2 id="werkwijze">Zo verloopt uw verhuizing</h2></div>
<ol class="steps">{"".join(f'<li><h3>{t}</h3><p>{d}</p></li>' for t, d in steps)}</ol></div></section>'''
    faq = [FAQ_GENERAL[k] for k in ("kosten", "vooraf", "verzekerd", "lift", "montage", "meehelpen", "checklist")]
    body = hero + who + werkwijze + promise_section() + diensten + cta_band("verhuiswagen-vol") + reviews_section(mist=False) + areas_section(mist=True) + faq_section(faq, "Veelgestelde vragen over verhuizen") + posts_section(mist=True) + spoed_band()
    t, d = SEO["home"]
    add("/", page(t, d, "/", body, preload="kennismaking-voordeur", schema=[{"@type": "WebPage", "@id": BASE + "/#webpage", "url": BASE + "/", "name": t, "isPartOf": {"@id": BASE + "/#website"}, "about": {"@id": ORG_ID}}, faq_schema(faq)]), prio="1.0")

# ---- dienstpagina's
def build_service(slug, name, short, ico, pid):
    D = parse_detail(pid)
    path = f"/diensten/{slug}/"
    crumbs = [("Home", "/"), ("Diensten", "/diensten/"), (name, path)]
    links = ("Andere diensten", "".join(f'<li><a href="/diensten/{s}/"{" aria-current=page" if s == slug else ""}>{n}</a></li>' for s, n, *_ in SERVICES))
    article = f'''<section class="section"><div class="wrap page-grid">
<article class="prose">{img(D["img"], "(max-width:1000px) 100vw, 60vw", cls="article-img")}{render_parts(D["parts"])}
<h2>{EXTRA[slug]["h2"]}</h2>{EXTRA[slug]["html"]}</article>
{sidebar(path, links)}
</div></section>'''
    faq = EXTRA[slug]["faq"]  # eigen vragen per dienst, geen kopie van de algemene FAQ
    body = hero_page(tidy_title(D["title"]), D["lead"], crumbs, D["bg"]) + article + promise_section()
    if faq: body += faq_section(faq, f"Vragen over {name.lower() if not name.startswith('(') else name}")
    body += cta_band("verhuiswagen-laden-3") + areas_section(mist=True)
    t, d = SEO[slug]
    sch = [crumbs_schema(crumbs), {"@type": "Service", "name": name, "serviceType": name, "description": d, "provider": {"@id": ORG_ID}, "areaServed": [p["naam"] for p in PLACES], "url": BASE + path}]
    if faq: sch.append(faq_schema(faq))
    add(path, page(t, d, path, body, current="/diensten/", og_img=D["img"], preload=D["bg"], schema=sch), prio="0.8")

# ---- plaatspagina's
def local_html(L, city):
    if not L:
        return f'<h2 id="lokaal">Verhuizen in en rond {city}</h2><p>Wij werken dagelijks in de wijde regio rondom Zwolle, Kampen en de Veluwe. Bel ons gerust op <a href="tel:{PHONE}" data-track="bellen">{PHONE_SHOW}</a> om de mogelijkheden voor uw verhuizing in {city} te bespreken.</p>'
    src = "".join(f'<li><a href="{u}" rel="nofollow noopener" target="_blank">{esc(n)}</a></li>' for n, u in L.get("bronnen", []))
    src = f'<details class="sources"><summary>Bronnen</summary><ul>{src}</ul></details>' if src else ""
    return f'<h2 id="lokaal">{L["h2"]}</h2>{L["html"]}{src}'

def build_city(slug, city, pid):
    D = parse_detail(pid)
    path = f"/verhuisbedrijf-{slug}/"
    crumbs = [("Home", "/"), (f"Verhuisbedrijf {city}", path)]
    links = ("Ook actief in de buurt", "".join(f'<li><a href="{place_link(p)}">Verhuisbedrijf {p["naam"]}</a></li>' for p in nearest(slug)))
    mp = f'<figure class="map-fig">{werkgebied_svg(slug)}<figcaption>{city} in ons werkgebied rond Hattem. <a href="/werkgebied/">Bekijk alle plaatsen</a></figcaption></figure>'
    L = LOKAAL.get(slug)
    article = f'''<section class="section"><div class="wrap page-grid">
<article class="prose">{img(D["img"], "(max-width:1000px) 100vw, 60vw", cls="article-img")}{'<p>Zoekt u een <a href="/">verhuisbedrijf voor Zwolle en omgeving</a>? HJ Verhuizing uit Hattem verhuist dagelijks in Zwolle. Op deze pagina leest u wat er in Zwolle zelf komt kijken bij een verhuizing: de zero-emissiezone, de pollers en het parkeren in de binnenstad.</p>' if slug == "zwolle" else ''}{render_parts(D["parts"])}
<p class="also">Ook voor {city}: {", ".join(f'<a href="/diensten/{s}/">{n.lower() if not n.startswith("(") else n}</a>' for s, n, *_ in SERVICES)}.</p></article>
{sidebar(path, links)}
</div></section>
<section class="section section--tight section--mist" aria-labelledby="lokaal"><div class="wrap split split--top"><div class="prose">{eyebrow("Lokaal")}{local_html(L, city)}</div>{mp}</div></section>'''
    L = LOKAAL.get(slug)
    if L:
        # lokale vragen + twee algemene; de oude, per plaats gekopieerde FAQ vervalt
        faq = L["faq"] + [(q.replace("?", f" in {city}?", 1) if q.startswith("Wat kost") else q, a) for q, a in (FAQ_GENERAL["kosten"], FAQ_GENERAL["verzekerd"])]
    else:
        faq = D["faq"]
        faq = [(q, FAQ_GENERAL["checklist"][1] if "checklist" in q.lower() else a) for q, a in faq]
    h1 = "Verhuizen in Zwolle: lokale kennis van HJ Verhuizing" if slug == "zwolle" else tidy_title(D["title"])
    body = hero_page(h1, D["lead"], crumbs, D["bg"]) + article
    if faq: body += faq_section(faq, D["faq_title"], re.sub(r"06-48577705", f'<a href="tel:{PHONE}" data-track="bellen">06-48577705</a>', D["faq_intro"] or ""), mist=True)
    body += reviews_section() + cta_band("verhuiswagen-dozen")
    t, d = SEO[f"verhuisbedrijf-{slug}"]
    sch = [crumbs_schema(crumbs), {"@type": "Service", "name": f"Verhuisbedrijf {city}", "serviceType": "Verhuizen", "provider": {"@id": ORG_ID}, "areaServed": {"@type": "City", "name": city}, "url": BASE + path}]
    if faq: sch.append(faq_schema(faq))
    add(path, page(t, d, path, body, og_img=D["img"], preload=D["bg"], schema=sch), prio="0.8")

IMG_ROT = ["verhuiswagen-laden-2", "steekwagen-dozen", "verhuizer-draagt-doos", "kast-dragen", "verhuiswagen-laden-4", "meubel-dragen",
           "verhuizer-verhuisdoos-binnen", "spiegel-dragen", "team-laadt-verhuiswagen", "verhuiswagen-vol", "verhuizer-steekwagen-woonkamer", "verhuiswagen-dozen"]
def build_new_city(i, slug, P):
    path = f"/verhuisbedrijf-{slug}/"; city = P["naam"]
    crumbs = [("Home", "/"), ("Werkgebied", "/werkgebied/"), (f"Verhuisbedrijf {city}", path)]
    links = ("Ook actief in de buurt", "".join(f'<li><a href="{place_link(p)}">Verhuisbedrijf {p["naam"]}</a></li>' for p in nearest(slug)))
    bg = IMG_ROT[i % len(IMG_ROT)]; art = IMG_ROT[(i + 5) % len(IMG_ROT)]
    d_km = km(HOME_C, P["coord"])
    src = "".join(f'<li><a href="{u}" rel="nofollow noopener" target="_blank">{esc(n)}</a></li>' for n, u in P.get("bronnen", []))
    mp = f'<figure class="map-fig">{werkgebied_svg(slug)}<figcaption>{city} ligt hemelsbreed zo\'n {round(d_km)} km van onze thuisbasis in Hattem. <a href="/werkgebied/">Bekijk alle plaatsen</a></figcaption></figure>'
    article = f'''<section class="section"><div class="wrap page-grid">
<article class="prose">{img(art, "(max-width:1000px) 100vw, 60vw", cls="article-img")}{P["intro_html"]}
<p class="also">Ook voor {city}: {", ".join(f'<a href="/diensten/{s}/">{n.lower() if not n.startswith("(") else n}</a>' for s, n, *_ in SERVICES)}.</p></article>
{sidebar(path, links)}
</div></section>
<section class="section section--tight section--mist" aria-labelledby="lokaal"><div class="wrap split split--top"><div class="prose">{eyebrow("Lokaal")}<h2 id="lokaal">{P["h2"]}</h2>{P["html"]}<details class="sources"><summary>Bronnen</summary><ul>{src}</ul></details></div>{mp}</div></section>'''
    faq = P["faq"] + [(FAQ_GENERAL["kosten"][0].replace("?", f" in {city}?"), FAQ_GENERAL["kosten"][1]), FAQ_GENERAL["verzekerd"]]
    body = hero_page(P["h1"], P["lead"], crumbs, bg) + article + faq_section(faq, f"Veelgestelde vragen over verhuizen in {city}", mist=False) + reviews_section(mist=True) + cta_band("verhuiswagen-dozen")
    sch = [crumbs_schema(crumbs), {"@type": "Service", "name": f"Verhuisbedrijf {city}", "serviceType": "Verhuizen", "provider": {"@id": ORG_ID}, "areaServed": {"@type": "City", "name": city}, "url": BASE + path}, faq_schema(faq)]
    add(path, page(P["title"], P["desc"], path, body, current="/werkgebied/", og_img=art, preload=bg, schema=sch), prio="0.7")

def dist_label(p):
    return "thuisbasis" if p["slug"] == "hattem" else f"ca. {round(km(HOME_C, p['coord']))} km"

def build_werkgebied():
    path = "/werkgebied/"; crumbs = [("Home", "/"), ("Werkgebied", path)]
    rows = []
    for r in REGIO_ORDER:
        ps = [p for p in PLACES if p["regio"] == r]
        if not ps: continue
        rows.append(f'<div class="area-group"><h2 class="h3">{r}</h2><ul class="area-list">' + "".join(
            f'<li><a href="{place_link(p)}"><span>Verhuisbedrijf {p["naam"]}</span><small>{dist_label(p)}</small></a></li>' for p in sorted(ps, key=lambda p: km(HOME_C, p["coord"]))) + "</ul></div>")
    body = hero_page("Ons werkgebied", f"Vanuit Hattem verhuizen wij in {len(PLACES)} plaatsen in de regio Zwolle, Salland, de Kop van Overijssel en de Veluwe. Staat uw plaats er niet bij? Bel ons gerust.", crumbs, "verhuiswagen-vol", facts=False) + f'''
<section class="section"><div class="wrap split split--top">
<figure class="map-fig map-fig--big">{werkgebied_svg()}<figcaption>Afstanden hemelsbreed vanaf Hattem. Klik op een plaats voor de lokale informatie.</figcaption></figure>
<div class="area-cols">{"".join(rows)}</div>
</div></section>''' + promise_section() + cta_band()
    sch = [crumbs_schema(crumbs), {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": BASE + place_link(p), "name": f"Verhuisbedrijf {p['naam']}"} for i, p in enumerate(PLACES)]}]
    add(path, page("Werkgebied: verhuisbedrijf regio Zwolle en Veluwe | HJ Verhuizing", f"HJ Verhuizing verhuist vanuit Hattem in {len(PLACES)} plaatsen: van Zwolle, Kampen en Meppel tot Apeldoorn, Deventer en Harderwijk. Bekijk het werkgebied.", path, body, preload="verhuiswagen-vol", schema=sch), prio="0.8")

# ---- diensten (overzicht)
def build_diensten():
    path = "/diensten/"; crumbs = [("Home", "/"), ("Diensten", path)]
    intro = f'''<section class="section"><div class="wrap split">
<div>{eyebrow("Onze werkwijze")}<h2>Vakkundige verhuizing met een persoonlijke aanpak</h2>
<p>HJ Verhuizing staat voor kwaliteit en betrouwbaarheid. Ons team van ervaren verhuizers begrijpt dat uw inboedel meer is dan alleen spullen; het zijn uw herinneringen. Wij werken dagelijks in de wijde regio rondom Zwolle, Kampen en de Veluwe, maar verzorgen ook met plezier verhuizingen in plaatsen als Meppel, Nunspeet en Raalte. Of u nu lokaal verhuist of naar de andere kant van het land, ons team regelt het zware werk met de grootste zorg.</p>
<a class="btn btn--navy" href="/contact/">Gratis offerte aanvragen</a></div>
<div class="photo-stat">{img("verhuizers-voordeur", "(max-width:900px) 100vw, 50vw")}</div></div></section>
<section class="section section--mist" aria-labelledby="alle"><div class="wrap services-split">
{img("verhuizer-met-doos-staand", "(max-width:900px) 100vw, 40vw")}
<div><div class="section-head"><h2 id="alle">Onze diensten</h2><p>Staat uw gewenste dienst er niet tussen? Neem gerust contact met ons op voor de mogelijkheden.</p></div>{services_list()}</div></div></section>'''
    faq = []
    body = hero_page("Diensten", "Van een particuliere verhuizing tot een complete kantoorverhuizing: wij regelen het zware werk met zorg en precisie.", crumbs, "verhuisdozen-dragen", facts=False) + intro + promise_section(mist=False) + cta_band() + reviews_section()
    t, d = SEO["diensten"]
    add(path, page(t, d, path, body, preload="verhuisdozen-dragen", schema=[crumbs_schema(crumbs), {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{BASE}/diensten/{s[0]}/", "name": s[1]} for i, s in enumerate(SERVICES)]}]), prio="0.9")

# ---- over ons
def build_over():
    path = "/over-ons/"; crumbs = [("Home", "/"), ("Over ons", path)]
    gallery = "".join(f'<li>{img(n, "(max-width:900px) 50vw, 25vw")}</li>' for n in ("kast-dragen", "spiegel-dragen", "verhuizer-steekwagen-woonkamer", "meubel-dragen"))
    body = hero_page("Over ons", "HJ Verhuizing is gegroeid van lokale start naar een professionele organisatie met een vakkundig team.", crumbs, "verhuizer-steekwagen-woonkamer", buttons=False, facts=False) + f'''
<section class="section"><div class="wrap split">
<div class="photo-stat">{img("meubel-dragen", "(max-width:900px) 100vw, 50vw")}<div class="stat-badge"><b>250+</b><span>verhuizingen</span></div></div>
<div>{eyebrow("HJ Verhuizing")}<h2>Uw vakkundige partner in de regio</h2>
<p>HJ Verhuizing is gegroeid van lokale start naar een professionele organisatie met een vakkundig team. Wij ontzorgen klanten door de hele provincie Overijssel en de omliggende regio's. Terwijl de regie en kwaliteit bij de oprichters liggen, zorgt ons team op locatie voor een zorgeloze en vlekkeloze uitvoering van uw verhuisdag.</p>
<p>Dankzij onze achtergrond in de bouw kunnen wij ook complexe (de)montageklussen direct voor u oplossen.</p>
<ul class="points"><li class="point"><span class="ico">{icon("people")}</span><div><h3>Persoonlijk en betrokken</h3><p>Geen groot anoniem bedrijf, maar direct contact met de verhuizers die het werk uitvoeren.</p></div></li>
<li class="point"><span class="ico">{icon("bolt")}</span><div><h3>Snel en flexibel</h3><p>Wij passen ons aan uw planning aan en zorgen voor een zorgeloze verhuisdag zonder verrassingen.</p></div></li></ul>
<a class="btn btn--navy" href="/contact/">Contact</a></div></div></section>
<section class="section section--tight" aria-labelledby="aan-het-werk"><div class="wrap"><div class="section-head"><h2 id="aan-het-werk">Ons team aan het werk</h2></div>
<ul class="gallery">{gallery}</ul></div></section>
<section class="section section--mist" aria-labelledby="wat"><div class="wrap"><div class="section-head"><h2 id="wat">Diensten</h2><p>Staat uw gewenste dienst er niet tussen? Neem gerust contact met ons op voor de mogelijkheden.</p></div>{services_list()}</div></section>
''' + promise_section(mist=False) + reviews_section(mist=True) + spoed_band()
    t, d = SEO["over-ons"]
    add(path, page(t, d, path, body, og_img="verhuizers-voordeur", preload="verhuizer-steekwagen-woonkamer", schema=[crumbs_schema(crumbs), {"@type": "AboutPage", "url": BASE + path, "name": t, "about": {"@id": ORG_ID}}]), prio="0.6")

# ---- contact
def build_contact():
    path = "/contact/"; crumbs = [("Home", "/"), ("Contact", path)]
    body = hero_page("Contact", "Zoekt u een specifieke verhuisservice op maat? Wij denken graag met u mee voor een oplossing die bij u past.", crumbs, "verhuisdozen-dragen", buttons=False, facts=False) + f'''
<section class="section"><div class="wrap page-grid">
<div><h2 id="offerte">Klaar voor een zorgeloze verhuisdag?</h2>
<p>Ons vakkundige team staat voor u klaar. Vul uw gegevens in en wij nemen binnen 24 uur contact met u op voor een verhuizing op maat.</p>
{form("contact", path, "Offerte aanvragen")}</div>
<aside class="aside" aria-label="Contactgegevens">
<div class="card"><h2 class="h3">Neem contact op</h2><ul class="contact-list">
<li><span class="ico">{icon("phone")}</span><span><a href="tel:{PHONE}" data-track="bellen">{PHONE_SHOW}</a><small>Bellen of WhatsApp</small></span></li>
<li><span class="ico">{icon("mail")}</span><span><a href="mailto:{EMAIL}">{EMAIL}</a></span></li>
<li><span class="ico">{icon("pin")}</span><span>{STREET}<br>{ZIP} {CITY}</span></li>
<li><span class="ico">{icon("time")}</span><span>{HOURS}</span></li>
</ul></div>
{map_block(STREET + ", " + ZIP + " " + CITY, "Hattem")}
</aside></div></section>''' + spoed_band()
    t, d = SEO["contact"]
    add(path, page(t, d, path, body, preload="verhuisdozen-dragen", schema=[crumbs_schema(crumbs), {"@type": "ContactPage", "url": BASE + path, "name": t, "about": {"@id": ORG_ID}}]), prio="0.8")

# ---- kennisbank + artikelen
RAW = ROOT / "build" / "data" / "raw"
def article_html(slug, pid):
    h = open(RAW / f"{pid}.html").read()
    h = re.sub(r"<!--\s*/?wp:[^>]*-->", "", h)
    if slug == "internationaal-verhuizen":
        # Elementor-uitvoer: alleen de artikeltekst houden
        h = h.split("</h2>", 1)[1].split("<h2>Klaar voor een zorgeloze")[0]
        h = re.sub(r"<img[^>]*>", "", h)
        h = re.sub(r'\sdata-path-to-node="[^"]*"', "", h)
        h = re.sub(r"</?(div|span|section)[^>]*>", "", h)
        h = re.sub(r'\s(class|style|id|data-[a-z-]+)="[^"]*"', "", h)
        h = re.sub(r"\s{2,}", " ", h).replace("> <", "><")
        h = fix_inline_heads(h)
        h = h.replace("<h2>Waarom internationaal", img("verhuiswagen-laden", "(max-width:900px) 100vw, 760px", cls="article-img") + "<h2>Waarom internationaal", 1)
    h = re.sub(r'href="https?://hjverhuizing\.nl', 'href="', h)
    if "<style>" in h:
        # handgemaakte artikelen: WordPress had de class-attributen weggefilterd; de eigen
        # opmaak zit nu in style.css (.post-body). Oude <style> eruit, knoppen herstellen.
        h = re.sub(r"<style>.*?</style>", "", h, flags=re.S)
        h = re.sub(r'(<a href="/contact/">[^<]+</a>)(<a href="tel:[^"]+">[^<]+</a>)',
                   r'<p class="btn-row"><a class="btn" href="/contact/">Offerte aanvragen</a><a class="btn btn--navy" href="tel:+31648577705" data-track="bellen">Bel 06 48 57 77 05</a></p>', h)
        h = re.sub(r"<details>", '<details class="post-faq">', h)
        h = re.sub(r"<p>", '<p class="lead">', h, count=1)
    return h.strip()

def faq_from_details(h):
    out = []
    for m in re.finditer(r"<details[^>]*>\s*<summary[^>]*>(.*?)</summary>(.*?)</details>", h, re.S):
        q = re.sub(r"<[^>]+>", "", m.group(1)).strip(); a = m.group(2).strip()
        if q: out.append((q, a))
    return out

def build_posts():
    for slug, pid, date, mod, im, intro in POSTS:
        path = f"/{slug}/"; title = post_title(slug)
        crumbs = [("Home", "/"), ("Kennisbank", "/kennisbank/"), (title, path)]
        art = article_html(slug, pid)
        nice = datetime.date.fromisoformat(mod).strftime("%-d %B %Y")
        for en, nl in (("January", "januari"), ("February", "februari"), ("March", "maart"), ("April", "april"), ("May", "mei"), ("June", "juni"), ("July", "juli"), ("August", "augustus"), ("September", "september"), ("October", "oktober"), ("November", "november"), ("December", "december")):
            nice = nice.replace(en, nl)
        others = "".join(f'<li><a href="/{s}/">{post_title(s)}</a></li>' for s, *_ in POSTS if s != slug)
        body = hero_page(title, None, crumbs, im, buttons=False, facts=False, meta=f'Bijgewerkt op <time datetime="{mod}">{nice}</time>') + f'''
<section class="section"><div class="wrap page-grid">
<article class="post-body prose">{art}</article>
{sidebar(path, ("Meer in de kennisbank", others))}
</div></section>''' + cta_band()
        t, d = SEO[slug]
        sch = [crumbs_schema(crumbs), {"@type": "BlogPosting", "headline": title, "description": d, "datePublished": date, "dateModified": mod, "image": f"{BASE}/img/og-{im}.jpg", "author": {"@id": ORG_ID}, "publisher": {"@id": ORG_ID}, "mainEntityOfPage": BASE + path, "inLanguage": "nl-NL"}]
        fq = faq_from_details(art)
        if fq: sch.append(faq_schema(fq))
        add(path, page(t, d, path, body, current="/kennisbank/", og_img=im, preload=im, schema=sch, extra="article"), lastmod=mod, prio="0.6")
    path = "/kennisbank/"; crumbs = [("Home", "/"), ("Kennisbank", path)]
    body = hero_page("Kennisbank", "Praktische uitleg om uw verhuizing goed voor te bereiden.", crumbs, "hj-verhuizing-shirt", buttons=False, facts=False) + posts_section().replace('<section class="section"', '<section class="section" id="artikelen"', 1) + spoed_band()
    t, d = SEO["kennisbank"]
    add(path, page(t, d, path, body, preload="hj-verhuizing-shirt", schema=[crumbs_schema(crumbs), {"@type": "CollectionPage", "url": BASE + path, "name": t}]), prio="0.6")

# ---- bedankt, juridisch, 404
def build_misc():
    path = "/bedankt/"
    body = hero_page("Bedankt!", "Wij nemen zo snel mogelijk contact met u op.", [("Home", "/"), ("Bedankt", path)], "verhuizer-met-doos", buttons=False, facts=False) + f'''
<section class="section"><div class="wrap split split--top">
<div class="prose"><h2>Hoe gaat het nu verder?</h2>
<p>We hebben uw aanvraag goed ontvangen en nemen binnen 24 uur contact met u op om uw verhuizing door te nemen. U krijgt ook een bevestiging per e-mail.</p>
<p>Wilt u alvast iets doorgeven, zoals de gewenste verhuisdatum of foto's van de inboedel? Stuur ons een WhatsApp-bericht of bel ons.</p>
<div class="btn-row" style="margin-bottom:2.2em"><a class="btn" href="{WA_NA}" target="_blank" rel="noopener" data-track="whatsapp">Stuur een WhatsApp-bericht</a><a class="btn btn--navy" href="tel:{PHONE}" data-track="bellen">{icon("phone")}Bel {PHONE_SHOW}</a></div>
<h2>Onze waarden</h2><p>Lees hieronder nog onze kernwaarden, zodat u weet dat u in goede handen bent.</p>
<h3>Ervaring en expertise</h3><p>Met jarenlange ervaring in de verhuisbranche beschikken we over de expertise om elke verhuizing aan te pakken. Ons team van professionals is goed opgeleid en toegewijd aan het leveren van hoogwaardige service.</p>
<h3>Maatwerk</h3><p>We begrijpen dat elke verhuizing uniek is. Daarom bieden we maatwerkoplossingen die aansluiten bij uw specifieke behoeften en budget. Of het nu gaat om een kleine verhuizing binnen dezelfde stad of een grootschalige internationale verhuizing, we hebben de middelen en flexibiliteit om aan uw eisen te voldoen.</p>
<h3>Betrouwbaarheid</h3><p>Bij HJ Verhuizing kunt u rekenen op betrouwbaarheid en punctualiteit. We komen onze afspraken na en streven ernaar om uw waardevolle bezittingen veilig en op tijd op de plaats van bestemming te krijgen.</p>
<h3>Klantgerichte service</h3><p>Uw tevredenheid staat bij ons centraal. Ons vriendelijke en professionele team staat klaar om al uw vragen te beantwoorden en u te begeleiden door het gehele verhuisproces.</p></div>
<div>{contact_card()}</div></div></section>'''
    add(path, page("Bedankt voor uw aanvraag | HJ Verhuizing", "Bedankt voor uw aanvraag. HJ Verhuizing neemt zo snel mogelijk contact met u op.", path, body, noindex=True, preload="verhuizer-met-doos"), index=False)

    # privacybeleid (bestaande tekst, bijgewerkt voor de nieuwe site)
    pv = open(ROOT / "build" / "data" / "privacybeleid.html").read()
    path = "/privacybeleid/"; crumbs = [("Home", "/"), ("Privacybeleid", path)]
    body = hero_page("Privacybeleid", None, crumbs, "verhuisdozen-dragen", buttons=False, facts=False) + f'<section class="section"><div class="wrap legal prose">{pv}</div></section>'
    t, d = SEO["privacybeleid"]
    add(path, page(t, d, path, body, preload="verhuisdozen-dragen", schema=[crumbs_schema(crumbs)]), prio="0.2")

    ck = open(ROOT / "build" / "data" / "cookiebeleid.html").read()
    path = "/cookie-policy-eu/"; crumbs = [("Home", "/"), ("Cookiebeleid", path)]
    body = hero_page("Cookiebeleid", None, crumbs, "verhuisdozen-dragen", buttons=False, facts=False) + f'<section class="section"><div class="wrap legal prose">{ck}</div></section>'
    t, d = SEO["cookie-policy-eu"]
    add(path, page(t, d, path, body, preload="verhuisdozen-dragen", schema=[crumbs_schema(crumbs)]), prio="0.2")

    body = f'''<section class="section notfound"><div class="wrap">
<p class="big">404</p><h1>Even de weg kwijt?</h1>
<p>Waarschijnlijk hebben we deze pagina in de verkeerde verhuisdoos gestopt. Of hij staat nog achterin de verhuiswagen. Kan gebeuren.<br>Geen stress, we helpen u weer op weg naar de juiste kamer:</p>
<div class="btn-row"><a class="btn" href="/">Home</a><a class="btn btn--navy" href="/diensten/">Diensten</a><a class="btn btn--navy" href="/contact/">Contact</a><a class="btn btn--navy" href="tel:{PHONE}">{icon("phone")}Bel ons</a></div>
</div></section>'''
    pages["/404.html"] = page("Pagina niet gevonden | HJ Verhuizing", "Deze pagina bestaat niet (meer).", "/404.html", body, noindex=True)

# ------------------------------------------------------------------ bouwen
build_home(); build_diensten(); build_over(); build_contact()
for s in SERVICES: build_service(*s)
for c in CITIES: build_city(*c)
for i, (k, v) in enumerate(sorted(NIEUW.items())): build_new_city(i, k, v)
build_werkgebied()
build_posts(); build_misc()

for path, h in pages.items():
    out = SITE / (path.lstrip("/") if path.endswith(".html") else path.lstrip("/") + "index.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(h)

sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for p, lm, pr in sorted(sitemap, key=lambda x: (-float(x[2]), x[0])):
    sm.append(f"<url><loc>{BASE}{p}</loc><lastmod>{lm}</lastmod><priority>{pr}</priority></url>")
sm.append("</urlset>")
(SITE / "sitemap.xml").write_text("\n".join(sm) + "\n")
(SITE / "robots.txt").write_text(f"User-agent: *\nDisallow: /verzend.php\nDisallow: /bedankt/\n\nSitemap: {BASE}/sitemap.xml\n")
(SITE / "site.webmanifest").write_text(json.dumps({"name": NAME, "short_name": "HJ Verhuizing", "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}], "theme_color": "#072C50", "background_color": "#ffffff", "display": "browser"}))
print(f"{len(pages)} pagina's gebouwd, {len(sitemap)} in sitemap")
