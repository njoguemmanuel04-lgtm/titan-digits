export const config = { runtime: 'nodejs' };

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache, no-transform');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');
  
  res.write(`data: ${JSON.stringify({log:"CONNECTING TO DERIV..."})}\n\n`);

  try {
    const { default: WebSocket } = await import('ws');
    const deriv = new WebSocket('wss://ws.binaryws.com/websockets/v3?app_id=1089');

    deriv.on('open', () => {
      console.log('DERIV OPEN');
      deriv.send(JSON.stringify({ ticks: 'R_100' }));
      res.write(`data: ${JSON.stringify({log:"DERIV CONNECTED, WAITING TICKS..."})}\n\n`);
    });

    deriv.on('message', (data) => {
      // forward raw Deriv message
      res.write(`data: ${data}\n\n`);
    });

    deriv.on('error', (e) => {
      console.log('DERIV ERROR', e);
      res.write(`data: ${JSON.stringify({error: 'DERIV_WS_ERROR', msg: e.message})}\n\n`);
    });

    deriv.on('close', () => {
      res.write(`data: ${JSON.stringify({error: 'DERIV_CLOSED'})}\n\n`);
    });

    req.on('close', () => {
      try { deriv.close(); } catch {}
      res.end();
    });

    // keep alive ping every 15s
    const keepAlive = setInterval(()=>{ res.write(`:keepalive\n\n`); }, 15000);
    deriv.on('close', ()=> clearInterval(keepAlive));

  } catch (err) {
    console.log('IMPORT ERROR', err);
    res.write(`data: ${JSON.stringify({error: 'WS_LIB_MISSING', msg: err.message})}\n\n`);
  }
}
