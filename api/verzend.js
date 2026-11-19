/**
 * HJ Verhuizing - verwerkt alle formulieren van de site en mailt de aanvraag door.
 * Vercel-versie van het oude verzend.php (Hostinger). Zelfde werking, zelfde controles.
 *
 * Spambeveiliging zonder captcha:
 *  1. honeypot: het verborgen veld "website" moet leeg zijn
 *  2. tijdscheck: wie binnen 3 seconden na het laden verstuurt, is een bot
 *  3. linkfilter: berichten met meer dan 3 links worden niet doorgestuurd
 *  4. herkomst: de aanvraag moet vanaf hjverhuizing.nl zelf komen (Origin/Referer)
 *  5. limiet: hoogstens 3 (geldige) aanvragen per uur per IP-adres (per draaiende functie-instantie)
 *  6. blokkadelijst: IP-adressen in BLOKKEER_IP worden altijd geweigerd
 *  7. verdachtscore: nep-postcode 1234 AB, 1234 in het telefoonnummer, browser zonder Nederlands;
 *     2 punten of meer = geblokkeerd, 1 punt = doorgestuurd met "[Verdacht]" in het onderwerp
 * Bots krijgen gewoon de bedankpagina te zien, zodat ze niet merken dat ze zijn tegengehouden.
 * Elke poging (ook de geblokkeerde) komt met IP, browser en reden in de Vercel-logs ([formulier] ...).
 *
 * Mail gaat via SMTP (Hostinger, mailbox info@hjverhuizing.nl):
 *   SMTP_HOST (standaard smtp.hostinger.com), SMTP_PORT (465), SMTP_USER, SMTP_PASS
 * of, als RESEND_API_KEY is gezet, via Resend (domein hjverhuizing.nl moet daar geverifieerd zijn).
 * Zonder een van beide: aanvraag wordt gelogd en de bezoeker ziet de foutmelding "bel ons".
 */

const nodemailer = require('nodemailer');

const AAN = process.env.MAIL_AAN || 'info@hjverhuizing.nl';      // hier komen de aanvragen binnen
const INFO = 'info@hjverhuizing.nl';                              // afzender van de automatische bevestiging
const AFZENDER = process.env.SMTP_USER || INFO;                   // bestaand mailadres op het eigen domein
const BEVESTIGING = process.env.BEVESTIGING !== '0';
const MAX_BEVESTIGINGEN_PER_UUR = 3;
const MAX_AANVRAGEN_PER_UUR = 3;
const MIN_SECONDEN = 3;
const BEDANKT = '/bedankt/';
const BLOKKEER_IP = [
  '31.171.130.48',  // nepaanvraag 13 nov 2026 (VPN, F.N.S. Holdings, Londen)
  '66.56.86.7',     // nepaanvraag 15 nov 2026 (VPN, Datacamp, Bratislava)
  ...String(process.env.BLOKKEER_IP || '').split(',').map((s) => s.trim()).filter(Boolean),
];

// ---------------------------------------------------------------- helpers
const tellers = new Map(); // soort+ip -> tijdstippen (leeft zolang de functie-instantie leeft)
function teller(soort, ip, max) {
  const sleutel = soort + ':' + ip;
  const nu = Date.now();
  const lijst = (tellers.get(sleutel) || []).filter((t) => t > nu - 3600 * 1000);
  if (lijst.length >= max) { tellers.set(sleutel, lijst); return false; }
  lijst.push(nu); tellers.set(sleutel, lijst);
  return true;
}

function enkel(v) { return String(v || '').replace(/[\r\n]+/g, ' ').trim(); }   // geen header-injectie
function veldUit(body, naam, max = 2000) {
  let v = body[naam];
  if (Array.isArray(v)) v = v[0];
  v = String(v == null ? '' : v).replace(/\r\n|\r/g, '\n').trim();
  v = v.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
  return v.slice(0, max);
}
function emailOk(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v) && v.length <= 200; }
function telefoonOk(v) {
  v = v.trim(); let d = v.replace(/\D/g, '');
  if (d.startsWith('0031')) d = '0' + d.slice(4);
  else if (d.startsWith('31') && v[0] === '+') d = '0' + d.slice(2);
  if (d !== '' && d[0] === '0') return d.length === 10;
  return v[0] === '+' && d.length >= 8 && d.length <= 15;
}
function datumNl() {
  const d = new Date();
  const f = new Intl.DateTimeFormat('nl-NL', { timeZone: 'Europe/Amsterdam', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  return f.format(d).replace(',', '');
}

async function leesBody(req) {
  if (req.body && typeof req.body === 'object') return req.body;
  if (typeof req.body === 'string') return Object.fromEntries(new URLSearchParams(req.body));
  const delen = [];
  for await (const d of req) delen.push(d);
  return Object.fromEntries(new URLSearchParams(Buffer.concat(delen).toString('utf8')));
}

// ---------------------------------------------------------------- mail
function mailIngesteld() { return !!(process.env.RESEND_API_KEY || process.env.SMTP_PASS || process.env.MAIL_DRYRUN); }

async function stuur({ to, from, replyTo, subject, text, headers }) {
  if (process.env.RESEND_API_KEY) {
    const r = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + process.env.RESEND_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ from, to: [to], reply_to: replyTo, subject, text, headers }),
    });
    if (!r.ok) throw new Error('resend ' + r.status + ' ' + (await r.text()).slice(0, 200));
    return;
  }
  const transport = process.env.MAIL_DRYRUN
    ? nodemailer.createTransport({ jsonTransport: true })
    : nodemailer.createTransport({
        host: process.env.SMTP_HOST || 'smtp.hostinger.com',
        port: Number(process.env.SMTP_PORT || 465),
        secure: Number(process.env.SMTP_PORT || 465) === 465,
        auth: { user: process.env.SMTP_USER || INFO, pass: process.env.SMTP_PASS },
        connectionTimeout: 8000, greetingTimeout: 8000, socketTimeout: 12000,
      });
  const info = await transport.sendMail({ to, from, replyTo, subject, text, headers });
  if (process.env.MAIL_DRYRUN) console.log('[formulier] dryrun-mail', info.message);
}

// ---------------------------------------------------------------- de aanvraag
module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') { res.statusCode = 302; res.setHeader('Location', '/'); return res.end(); }

  const body = await leesBody(req);
  const veld = (naam, max) => veldUit(body, naam, max);
  const kop = (naam) => enkel(req.headers[naam] || '');
  const ip = enkel(String(req.headers['x-forwarded-for'] || '').split(',')[0] || req.headers['x-real-ip'] || (req.socket && req.socket.remoteAddress) || '?');

  const pagina = veld('pagina', 200);
  const terug = (pad, fout) => {
    const ref = /^\/[a-z0-9/_-]*$/i.test(pagina) ? pagina : '/contact/';
    res.statusCode = 303;
    res.setHeader('Location', fout ? ref + '?fout=' + fout + '#offerte' : pad);
    res.end();
  };
  const log = (status) => console.log('[formulier]', [status, ip, enkel(veld('formulier', 30)), enkel(veld('naam', 120)), enkel(veld('email', 200)),
    enkel(veld('telefoon', 40)), kop('referer'), kop('user-agent')].map((s) => String(s).replace(/\t/g, ' ')).join('\t'));
  const blokkeer = (status) => { log(status); terug(BEDANKT); };   // bot: stil naar de bedankpagina

  // spamcontroles
  const honeypot = veld('website', 200);
  const ts = parseInt(veld('ts', 20), 10) || 0;
  const nu = Date.now();
  if (BLOKKEER_IP.some((b) => b && ip.startsWith(b))) return blokkeer('geblokkeerd-ip');
  if (honeypot !== '') return blokkeer('honeypot');
  if (ts <= 0) return blokkeer('geen-tijdstempel');
  if (nu - ts < MIN_SECONDEN * 1000) return blokkeer('te-snel');
  if (nu - ts > 86400 * 1000) return blokkeer('tijdstempel-oud');
  const herkomst = kop('origin') || kop('referer');
  if (herkomst !== '' && !/^https?:\/\/(www\.)?hjverhuizing\.nl(\/|$)/i.test(herkomst) && !/^https?:\/\/[a-z0-9-]+\.vercel\.app(\/|$)/i.test(herkomst) && !/^https?:\/\/localhost(:\d+)?(\/|$)/i.test(herkomst)) return blokkeer('andere-site');

  // velden
  const formulier = enkel(veld('formulier', 30));
  const naam = enkel(veld('naam', 120));
  const telefoon = enkel(veld('telefoon', 40));
  const email = enkel(veld('email', 200));
  const postcode = enkel(veld('postcode', 10)).toUpperCase();
  const onderwerp = enkel(veld('onderwerp', 150));
  const bedrijf = enkel(veld('bedrijf', 150));
  const bericht = veld('bericht', 5000);

  if ((bericht.match(/https?:\/\/|www\./gi) || []).length > 3) return blokkeer('linkspam');
  if (telefoon === '' || !emailOk(email) || (formulier !== 'quick' && naam === '')) return terug(null, 'velden');
  if (!telefoonOk(telefoon)) { log('telefoon-ongeldig'); return terug(null, 'telefoon'); }

  // mail
  const soort = { quick: 'Prijsopgave (homepage)', offerte: 'Offerteaanvraag', contact: 'Contactformulier' }[formulier] || 'Formulier';
  let onderwerpMail = 'Nieuwe aanvraag via hjverhuizing.nl: ' + (naam !== '' ? naam : email);
  const regels = [['Soort', soort], ['Naam', naam], ['Telefoon', telefoon], ['E-mail', email], ['Postcode', postcode], ['Bedrijf', bedrijf], ['Onderwerp', onderwerp], ['Pagina', 'https://hjverhuizing.nl' + pagina]];
  let tekst = '';
  for (const [k, v] of regels) if (v !== '') tekst += (k + ':').padEnd(11) + v + '\n';
  if (bericht !== '') tekst += '\nBericht:\n' + bericht + '\n';

  // verdachtscore: de nepaanvragen van nov 2026 hadden postcode "1234 AB", een 06-nummer met 1234 erin en kwamen via een VPN
  let score = 0; const redenen = [];
  const cijfers = telefoon.replace(/\D/g, '');
  if (/^1234\s?AB$/.test(postcode)) { score += 2; redenen.push('postcode 1234 AB'); }
  if (cijfers.includes('1234')) { score += 1; redenen.push('1234 in telefoonnummer'); }
  if (!/nl/i.test(kop('accept-language'))) { score += 1; redenen.push('browser zonder Nederlands'); }
  if (herkomst === '' || kop('user-agent') === '') { score += 1; redenen.push('herkomst of browser ontbreekt'); }
  if (/https?:\/\/|www\./i.test(naam + telefoon + postcode)) { score += 2; redenen.push('link in naam/telefoon/postcode'); }
  if (score >= 2) return blokkeer('nep-score-' + score);
  // limiet per IP pas hier: een typefout in het nummer telt niet mee, een echte aanvraag wel
  if (!teller('aanvraag', ip, MAX_AANVRAGEN_PER_UUR)) return blokkeer('limiet');
  const verdacht = score > 0;
  if (verdacht) onderwerpMail = '[Verdacht] ' + onderwerpMail;
  tekst += '\n--\nVerzonden op ' + datumNl() + ' vanaf IP ' + ip
    + '\nBrowser:   ' + (kop('user-agent') || '(leeg)')
    + '\nTaal:      ' + (kop('accept-language') || '(leeg)')
    + '\nHerkomst:  ' + (herkomst || '(leeg)')
    + (verdacht ? '\nVerdacht:  ' + redenen.join(', ') : '')
    + '\nWie is dit IP: https://ipinfo.io/' + ip + '\n';

  if (!mailIngesteld()) { log('mail-niet-ingesteld'); return terug(null, 'mail'); }
  try {
    await stuur({
      to: AAN, from: 'HJ Verhuizing website <' + AFZENDER + '>',
      replyTo: (naam !== '' ? '"' + naam.replace(/"/g, '') + '" ' : '') + '<' + email + '>',
      subject: onderwerpMail, text: tekst, headers: { 'X-Mailer': 'hjverhuizing.nl' },
    });
  } catch (e) {
    console.error('[formulier] mail mislukt:', e && e.message);
    log('mail-mislukt');
    return terug(null, 'mail');
  }
  log(verdacht ? 'verdacht' : 'ok');

  // automatische bevestiging aan de klant: bewust zonder de ingevulde tekst, zodat het formulier
  // niet misbruikt kan worden om willekeurige berichten naar andermans adres te sturen
  if (BEVESTIGING && teller('bevestiging', ip, MAX_BEVESTIGINGEN_PER_UUR)) {
    const voornaam = /^[\p{L} .'-]{2,60}$/u.test(naam) ? naam : '';
    const aanhef = voornaam !== '' ? 'Beste ' + voornaam + ',' : 'Goedendag,';
    const berichtKlant = aanhef + '\n\n'
      + 'Bedankt voor uw aanvraag bij HJ Verhuizing. We hebben hem goed ontvangen en nemen binnen 24 uur contact met u op om uw verhuizing door te nemen.\n\n'
      + 'Heeft u haast of wilt u alvast iets doorgeven? Bel ons op 06 48 57 77 05, stuur een WhatsApp-bericht naar hetzelfde nummer, of antwoord gewoon op deze e-mail.\n\n'
      + 'Met vriendelijke groet,\n\nHJ Verhuizing\n06 48 57 77 05\ninfo@hjverhuizing.nl\nhttps://hjverhuizing.nl\n';
    try {
      await stuur({ to: email, from: 'HJ Verhuizing <' + INFO + '>', replyTo: 'HJ Verhuizing <' + INFO + '>',
        subject: 'We hebben uw aanvraag ontvangen | HJ Verhuizing', text: berichtKlant,
        headers: { 'Auto-Submitted': 'auto-replied', 'X-Mailer': 'hjverhuizing.nl' } });
    } catch (e) { console.error('[formulier] bevestiging mislukt:', e && e.message); }
  }
  return terug(BEDANKT);
};
