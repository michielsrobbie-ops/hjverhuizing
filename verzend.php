<?php
/**
 * HJ Verhuizing - verwerkt alle formulieren van de site en mailt de aanvraag door.
 *
 * Spambeveiliging zonder captcha:
 *  1. honeypot: het verborgen veld "website" moet leeg zijn
 *  2. tijdscheck: wie binnen 3 seconden na het laden verstuurt, is een bot
 *  3. linkfilter: berichten met meer dan 3 links worden niet doorgestuurd
 * Bots krijgen gewoon de bedankpagina te zien, zodat ze niet merken dat ze zijn tegengehouden.
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

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { header('Location: /', true, 302); exit; }

// ---------------------------------------------------------------- spamcontroles
$honeypot = veld('website', 200);
$ts = (int) veld('ts', 20);
$nu = (int) round(microtime(true) * 1000);

if ($honeypot !== '') { terug($BEDANKT); }                                        // bot
if ($ts > 0 && ($nu - $ts) < $MIN_SECONDEN * 1000) { terug($BEDANKT); }            // te snel
// ts ontbreekt (javascript uit): toegestaan, de honeypot vangt de meeste bots al af

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

if (preg_match_all('#https?://|www\.#i', $bericht) > 3) { terug($BEDANKT); }       // linkspam

if ($telefoon === '' || !filter_var($email, FILTER_VALIDATE_EMAIL) || ($formulier !== 'quick' && $naam === '')) {
    terug(null, 'velden');
}

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
$tekst .= "\n--\nVerzonden op " . date('d-m-Y H:i') . " vanaf IP " . ($_SERVER['REMOTE_ADDR'] ?? '?') . "\n";

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
if (!$ok) { terug(null, 'mail'); }

// ---------------------------------------------------------------- automatische bevestiging aan de klant
// Bewust zonder de ingevulde tekst van de klant: zo kan het formulier niet misbruikt worden om
// willekeurige berichten naar andermans adres te sturen. Plus een limiet per IP-adres.
function mag_bevestigen($ip, $max) {
    $f = sys_get_temp_dir() . '/hj_bevestiging_' . md5($ip);
    $nu = time(); $lijst = [];
    if (is_file($f)) { $lijst = array_filter(array_map('intval', explode(',', (string) @file_get_contents($f))), fn($t) => $t > $nu - 3600); }
    if (count($lijst) >= $max) return false;
    $lijst[] = $nu; @file_put_contents($f, implode(',', $lijst));
    return true;
}
if ($BEVESTIGING && mag_bevestigen($_SERVER['REMOTE_ADDR'] ?? '', $MAX_BEVESTIGINGEN_PER_UUR)) {
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
