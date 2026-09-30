export const config = { runtime: 'nodejs' };

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache, no-transform');
  res.setHeader('Connection', 'keep-alive');
  
  const send = (obj) => {
    try{ res.write(`data: ${JSON.stringify(obj)}\n\n`); }catch{}
  };

  send({log:"V8.1 TRYING DERIV ENDPOINTS..."});

  // Try 3 different Deriv WS hosts
  const ENDPOINTS = [
    'wss://ws.derivws.com/websockets/v3?app_id=1089',
    'wss://ws.binaryws.com/websockets/v3?app_id=1089',
    'wss://ws.deriv.com/websockets/v3?app_id=1089'
  ];

  async function tryConnect(url){
    const { default: WebSocket } = await import('ws');
    return new Promise((resolve, reject)=>{
      const ws = new WebSocket(url, {
        headers: { 'User-Agent': 'Mozilla/5.0', 'Origin': 'https://app.deriv.com' }
      });
      ws.on('open', ()=>{
        send({log:"CONNECTED TO: "+url});
        ws.send(JSON.stringify({ticks:'R_100'}));
        ws.on('message', (d)=>{ res.write(`data: ${d}\n\n`); });
        resolve(ws);
      });
      ws.on('error', (e)=>{
        send({log:"FAILED: "+url+" - "+e.message});
        reject(e);
      });
      setTimeout(()=>reject(new Error('timeout '+url)), 5000);
    });
  }

  (async ()=>{
    for(let ep of ENDPOINTS){
      try{
        const ws = await tryConnect(ep);
        req.on('close', ()=>{ try{ws.close()}catch{}; res.end(); });
        return;
      }catch{}
    }
    send({error:"ALL_ENDPOINTS_FAILED", msg:"Vercel IP banned by Deriv - need to deploy to Render.com"});
    // Fallback: tell frontend to connect direct
    send({fallback:"direct"});
  })();
}
