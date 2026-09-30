export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  let body = { ticks: 'R_100' };
  try {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const txt = Buffer.concat(chunks).toString();
    if (txt) body = JSON.parse(txt);
  } catch {}

  try {
    const { WebSocket } = await import('ws');
    const ws = new WebSocket('wss://ws.derivws.com/websockets/v3?app_id=1089');
    
    const data = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => { try{ws.close()}catch{}; reject(new Error('timeout')); }, 8000);
      ws.on('open', () => ws.send(JSON.stringify(body)));
      ws.on('message', (msg) => {
        clearTimeout(timer);
        try{ws.close()}catch{}
        resolve(JSON.parse(msg.toString()));
      });
      ws.on('error', (e) => { clearTimeout(timer); reject(e); });
    });

    return res.status(200).json(data);
  } catch (e) {
    return res.status(200).json({ error: e.message });
  }
}
