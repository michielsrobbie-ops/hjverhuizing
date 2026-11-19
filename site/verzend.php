<?php
/**
 * HJ Verhuizing - verwerkt alle formulieren van de site en mailt de aanvraag door.
 *
 * Spambeveiliging zonder captcha:
 *  1. honeypot: het verborgen veld "website" moet leeg zijn
 *  2. tijdscheck: wie binnen 3 seconden na het laden verstuurt, is een bot
 *  3. linkfilter: berichten met meer dan 3 links worden niet doorgestuurd
 *  4. herkomst: de aanvraag moet vanaf hjverhuizing.nl zelf komen (Origin/Referer)
 *  5. limiet: hoogstens 3 aanvragen per uur per IP-adres
 *  6. blokkadelijst: IP-adressen in $BLOKKEER_IP worden altijd geweigerd
 *  7. verdachtscore: nep-postcode 1234 AB, 1234 in het telefoonnummer, browser zonder Nederlands;
 *     2 punten of meer = geblokkeerd, 1 punt = doorgestuurd met "[Verdacht]" in het onderwerp
 * Bots krijgen gewoon de bedankpagina te zien, zodat ze niet merken dat ze zijn tegengehouden.
 * Elke poging (ook de geblokkeerde) komt met IP, browser en reden in het logbestand
 * ../hj-formulier.log (buiten public_html, dus niet via de site op te vragen).
 */

date_default_timezone_set('Europe/Amsterdam');

// ---------------------------------------------------------------- instellingen
$AAN  = 'info@hjverhuizing.nl';                 // hier komen de aanvragen binnen (staat gekoppeld met Gmail)
$BCC  = [];                                     // eventueel extra ontvangers
$INFO = 'info@hjverhuizing.nl';                 // afzender van de automatische bevestiging aan de klant
$BEVESTIGING = true;                            // false = geen automatische bevestiging sturen
$MAX_BEVESTIGINGEN_PER_UUR = 3;                 // per IP-adres, tegen misbruik
$AFZENDER   = 'info@hjverhuizing.nl';           // bestaand mailadres op het eigen domein (Hostinger eist dat)
$BEDANKT    = '/bedankt/';
$MIN_SECONDEN = 3;
$MAX_AANVRAGEN_PER_UUR = 3;                     // per IP-adres
$BLOKKEER_IP = [                                // exacte adressen of een begin zoals '185.220.'
    '31.171.130.48',                            // nepaanvraag 13 nov 2026 (VPN, F.N.S. Holdings, Londen)
    '66.56.86.7',                               // nepaanvraag 15 nov 2026 (VPN, Datacamp, Bratislava)
];
$LOG = dirname(__DIR__) . '/hj-formulier.log';  // naast public_html

// ---------------------------------------------------------------- helpers
function veld($naam, $max = 2000) {
    $v = isset($_POST[$naam]) ? (string) $_POST[$naam] : '';
    $v = trim(str_replace(["\r\n", "\r"], "\n", $v));
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $v);
    return mb_substr($v, 0, $max);
}
function enkel($v) { return trim(preg_replace('/[\r\n]+/', ' ', $v)); }   // geen header-injectie
function terug($pad, $fout = null) {
    $ref = isset($_POST['pagina']) && preg_match('#^/[a-z0-9/_-]*$#i', $_POST['pagina']) ? $_POST['pagina'] : '/contact/';
    $doel = $fout ? $ref . '?fout=' . $fout . '#offerte' : $pad;
    header('Location: ' . $doel, true, 303);
    exit;
}
function ip() { return $_SERVER['REMOTE_ADDR'] ?? '?'; }
function kop($naam) { return enkel((string) ($_SERVER[$naam] ?? '')); }
function log_poging($status) {
    global $LOG;
    $r = [date('Y-m-d H:i:s'), $status, ip(), enkel(veld('formulier', 30)), enkel(veld('naam', 120)), enkel(veld('email', 200)),
          enkel(veld('telefoon', 40)), kop('HTTP_REFERER'), kop('HTTP_USER_AGENT')];
    @file_put_contents($LOG, implode("\t", str_replace("\t", ' ', $r)) . "\n", FILE_APPEND | LOCK_EX);
}
function blokkeer($status) { log_poging($status); terug($GLOBALS['BEDANKT']); }    // bot: stil naar de bedankpagina
function teller($soort, $max) {                                                    // pogingen per IP per uur
    $f = sys_get_temp_dir() . '/hj_' . $soort . '_' . md5(ip());
    $nu = time(); $lijst = [];
    if (is_file($f)) { $lijst = array_filter(array_map('intval', explode(',', (string) @file_get_contents($f))), fn($t) => $t > $nu - 3600); }
    if (count($lijst) >= $max) return false;
    $lijst[] = $nu; @file_put_contents($f, implode(',', $lijst));
    return true;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { header('Location: /', true, 302); exit; }

// ---------------------------------------------------------------- spamcontroles
$honeypot = veld('website', 200);
$ts = (int) veld('ts', 20);
$nu = (int) round(microtime(true) * 1000);

foreach ($BLOKKEER_IP as $b) { if ($b !== '' && strpos(ip(), $b) === 0) blokkeer('geblokkeerd-ip'); }
if ($honeypot !== '') blokkeer('honeypot');
if ($ts <= 0) blokkeer('geen-tijdstempel');                                        // formulier niet via de pagina (javascript) verstuurd
if (($nu - $ts) < $MIN_SECONDEN * 1000) blokkeer('te-snel');
if (($nu - $ts) > 86400 * 1000) blokkeer('tijdstempel-oud');                       // ouder dan een dag of hergebruikt
$herkomst = kop('HTTP_ORIGIN') ?: kop('HTTP_REFERER');
if ($herkomst !== '' && !preg_match('#^https?://(www\.)?hjverhuizing\.nl(/|$)#i', $herkomst)) blokkeer('andere-site');
if (!teller('aanvraag', $MAX_AANVRAGEN_PER_UUR)) blokkeer('limiet');

// ---------------------------------------------------------------- velden
$formulier = enkel(veld('formulier', 30));
$pagina    = enkel(veld('pagina', 200));
$naam      = enkel(veld('naam', 120));
$telefoon  = enkel(veld('telefoon', 40));
$email     = enkel(veld('email', 200));
$postcode  = strtoupper(enkel(veld('postcode', 10)));
$onderwerp = enkel(veld('onderwerp', 150));
$bedrijf   = enkel(veld('bedrijf', 150));
$bericht   = veld('bericht', 5000);

if (preg_match_all('#https?://|www\.#i', $bericht) > 3) blokkeer('linkspam');

if ($telefoon === '' || !filter_var($email, FILTER_VALIDATE_EMAIL) || ($formulier !== 'quick' && $naam === '')) {
    terug(null, 'velden');
}
// telefoonnummer: Nederlands = 10 cijfers met 0 vooraan, of +31/0031 en 9 cijfers; buitenlands = + en 8 tot 15 cijfers
function telefoon_ok($v) {
    $v = trim($v); $d = preg_replace('/\D/', '', $v);
    if (strpos($d, '0031') === 0) $d = '0' . substr($d, 4);
    elseif (strpos($d, '31') === 0 && $v[0] === '+') $d = '0' . substr($d, 2);
    if ($d !== '' && $d[0] === '0') return strlen($d) === 10;
    return $v[0] === '+' && strlen($d) >= 8 && strlen($d) <= 15;
}
if (!telefoon_ok($telefoon)) { log_poging('telefoon-ongeldig'); terug(null, 'telefoon'); }

// ---------------------------------------------------------------- mail
$soort = ['quick' => 'Prijsopgave (homepage)', 'offerte' => 'Offerteaanvraag', 'contact' => 'Contactformulier'][$formulier] ?? 'Formulier';
$onderwerpMail = 'Nieuwe aanvraag via hjverhuizing.nl: ' . ($naam !== '' ? $naam : $email);

$regels = [
    'Soort'      => $soort,
    'Naam'       => $naam,
    'Telefoon'   => $telefoon,
    'E-mail'     => $email,
    'Postcode'   => $postcode,
    'Bedrijf'    => $bedrijf,
    'Onderwerp'  => $onderwerp,
    'Pagina'     => 'https://hjverhuizing.nl' . $pagina,
];
$tekst = '';
foreach ($regels as $k => $v) { if ($v !== '') $tekst .= str_pad($k . ':', 11) . $v . "\n"; }
if ($bericht !== '') $tekst .= "\nBericht:\n" . $bericht . "\n";
// verdachtscore: de nepaanvragen van nov 2026 hadden postcode "1234 AB", een 06-nummer met 1234 erin en kwamen via een VPN
$score = 0; $redenen = [];
$cijfers = preg_replace('/\D/', '', $telefoon);
if (preg_match('/^1234\s?AB$/', $postcode))                   { $score += 2; $redenen[] = 'postcode 1234 AB'; }
if (strpos($cijfers, '1234') !== false)                        { $score += 1; $redenen[] = '1234 in telefoonnummer'; }
if (stripos(kop('HTTP_ACCEPT_LANGUAGE'), 'nl') === false)      { $score += 1; $redenen[] = 'browser zonder Nederlands'; }
if ($herkomst === '' || kop('HTTP_USER_AGENT') === '')         { $score += 1; $redenen[] = 'herkomst of browser ontbreekt'; }
if (preg_match('#https?://|www\.#i', $naam . $telefoon . $postcode)) { $score += 2; $redenen[] = 'link in naam/telefoon/postcode'; }
if ($score >= 2) blokkeer('nep-score-' . $score);
$verdacht = $score > 0;
if ($verdacht) $onderwerpMail = '[Verdacht] ' . $onderwerpMail;
$tekst .= "\n--\nVerzonden op " . date('d-m-Y H:i') . " vanaf IP " . ip()
        . "\nBrowser:   " . (kop('HTTP_USER_AGENT') ?: '(leeg)')
        . "\nTaal:      " . (kop('HTTP_ACCEPT_LANGUAGE') ?: '(leeg)')
        . "\nHerkomst:  " . ($herkomst ?: '(leeg)')
        . ($verdacht ? "\nVerdacht:  " . implode(', ', $redenen) : '')
        . "\nWie is dit IP: https://ipinfo.io/" . ip() . "\n";

$headers = [
    'From: HJ Verhuizing website <' . $AFZENDER . '>',
    'Reply-To: ' . ($naam !== '' ? '"' . str_replace('"', '', $naam) . '" ' : '') . '<' . $email . '>',
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: 8bit',
    'X-Mailer: hjverhuizing.nl',
];
$subject = '=?UTF-8?B?' . base64_encode($onderwerpMail) . '?=';

if ($BCC) { $headers[] = 'Bcc: ' . implode(', ', $BCC); }
$ok = mail($AAN, $subject, $tekst, implode("\r\n", $headers), '-f' . $AFZENDER);
if (!$ok) { log_poging('mail-mislukt'); terug(null, 'mail'); }
log_poging($verdacht ? 'verdacht' : 'ok');

// ---------------------------------------------------------------- automatische bevestiging aan de klant
// Bewust zonder de ingevulde tekst van de klant: zo kan het formulier niet misbruikt worden om
// willekeurige berichten naar andermans adres te sturen. Plus een limiet per IP-adres.
if ($BEVESTIGING && teller('bevestiging', $MAX_BEVESTIGINGEN_PER_UUR)) {
    $voornaam = preg_match('/^[\p{L} .\'-]{2,60}$/u', $naam) ? $naam : '';
    $aanhef = $voornaam !== '' ? 'Beste ' . $voornaam . ',' : 'Goedendag,';
    $bericht_klant = $aanhef . "\n\n"
        . "Bedankt voor uw aanvraag bij HJ Verhuizing. We hebben hem goed ontvangen en nemen binnen 24 uur contact met u op om uw verhuizing door te nemen.\n\n"
        . "Heeft u haast of wilt u alvast iets doorgeven? Bel ons op 06 48 57 77 05, stuur een WhatsApp-bericht naar hetzelfde nummer, of antwoord gewoon op deze e-mail.\n\n"
        . "Met vriendelijke groet,\n\n"
        . "HJ Verhuizing\n"
        . "06 48 57 77 05\n"
        . "info@hjverhuizing.nl\n"
        . "https://hjverhuizing.nl\n";
    $headers_klant = [
        'From: HJ Verhuizing <' . $INFO . '>',
        'Reply-To: HJ Verhuizing <' . $INFO . '>',
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: 8bit',
        'Auto-Submitted: auto-replied',
        'X-Mailer: hjverhuizing.nl',
    ];
    @mail($email, '=?UTF-8?B?' . base64_encode('We hebben uw aanvraag ontvangen | HJ Verhuizing') . '?=', $bericht_klant, implode("\r\n", $headers_klant), '-f' . $INFO);
}
terug($BEDANKT);
