# hjverhuizing-website

Statische site voor HJ Verhuizing (hjverhuizing.nl), herbouwd vanuit de WordPress/Elementor-backup van 28 okt 2026.
Zelfde look, URL's en teksten, zonder WordPress en plugins.

## Structuur
- `site/` - wat er op de hosting komt (inhoud van `public_html`)
- `build/build.py` - genereert alle pagina's in `site/` vanuit `build/data/`
- `build/images.py` - zet originele uploads om naar WebP (alleen opnieuw nodig bij nieuwe foto's)
- `build/data/content.json` - teksten van alle pagina's, geëxporteerd uit Elementor
- `build/data/raw/` - de kennisbankartikelen
- `docs/open-punten.md` - wat nog nagelopen moet worden

## Aanpassen
1. Tekst, titels, diensten of plaatsen wijzigen in `build/build.py` of `build/data/`
2. `python3 build/build.py`
3. Bij wijzigingen in CSS of JS: `VERSION` in `build/build.py` ophogen (cache)

## Lokaal bekijken
`cd site && php -S localhost:8000` (met PHP werkt ook het formulier; zonder: `python3 -m http.server`)

## Live zetten (Hostinger)
De site staat sinds 5 nov 2026 live en deployt automatisch:
1. Wijzigen, `python3 build/build.py`, committen en pushen naar `main`.
2. De GitHub Action (`.github/workflows/live.yml`) zet de inhoud van `site/` op de branch `live`.
3. Hostinger (hPanel > Geavanceerd > GIT, automatische implementatie) zet de branch `live` in `public_html`.

Handmatig opnieuw uitrollen: hPanel > Geavanceerd > GIT > Herimplementeren.
De oude WordPress-bestanden staan in `wp-oud/` naast `public_html` (terugzetten = inhoud terug verplaatsen).
