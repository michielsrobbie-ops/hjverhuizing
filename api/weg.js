/* Oude WordPress-adressen (wp-admin, wp-content, wp-json ...) bestaan niet meer.
   410 Gone, zodat Google ze definitief uit de index haalt (vercel.json stuurt ze hierheen). */
module.exports = (req, res) => {
  res.statusCode = 410;
  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.setHeader('Cache-Control', 'public, max-age=86400');
  res.end('Deze pagina bestaat niet meer. Ga naar https://hjverhuizing.nl/\n');
};
