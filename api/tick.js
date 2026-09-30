export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  
  let body = req.body;
  if (!body || typeof body === 'string') {
    try {
      const text = await new Promise((resolve) => {
        let data = '';
        req.on('data', chunk => data += chunk);
        req.on('end', () => resolve(data));
      });
      body = text ? JSON.parse(text) : { ticks: 'R_100' };
    } catch {
      body = { ticks: 'R_100' };
    }
  }
  if (!body.ticks && !body.authorize) body = { ticks: 'R_100' };

  try {
    const r = await fetch('https://ws.derivws.com/websockets/v3?app_id=1089', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await r.json();
    return res.status(200).json(data);
  } catch (e) {
    return res.status(200).json({ error: e.message, body });
  }
}
