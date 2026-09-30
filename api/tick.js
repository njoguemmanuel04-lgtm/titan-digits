import WebSocket from 'ws';

export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', '*');
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache, no-transform');
  res.setHeader('Connection', 'keep-alive');

  const deriv = new WebSocket('wss://ws.derivws.com/websockets/v3?app_id=1089');

  deriv.on('open', () => {
    deriv.send(JSON.stringify({ ticks: 'R_100' }));
  });

  deriv.on('message', (data) => {
    res.write(`data: ${data}\n\n`);
  });

  deriv.on('error', (e) => {
    res.write(`data: ${JSON.stringify({error: 'deriv_error'})}\n\n`);
  });

  req.on('close', () => {
    try { deriv.close(); } catch {}
    try { res.end(); } catch {}
  });
}
