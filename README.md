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
1. Maak in hPanel eerst een volledige backup van de huidige site.
2. Verplaats de WordPress-bestanden in `public_html` naar een map buiten `public_html` (bijv. `wp-oud`), of verwijder ze na de backup.
3. Upload de inhoud van `site/` naar `public_html` (inclusief het verborgen bestand `.htaccess`).
4. Zet in hPanel de LiteSpeed Cache uit of leeg hem.
5. Test: homepage, een dienstpagina, een plaatspagina, een oude afbeeldings-URL (moet doorsturen), en verstuur één testformulier.
6. Search Console: dien `https://hjverhuizing.nl/sitemap.xml` in.
