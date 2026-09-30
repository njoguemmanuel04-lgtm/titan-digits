import WebSocket from 'ws';
export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin','*');
  try {
    const ws = new WebSocket('wss://ws.derivws.com/websockets/v3?app_id=1089');
    const tick = await new Promise((resolve, reject) => {
      const t = setTimeout(()=>reject('timeout'),4000);
      ws.on('open',()=>{ ws.send(JSON.stringify({ticks:"R_100"})); });
      ws.on('message',(d)=>{
        const m=JSON.parse(d.toString());
        if(m.tick){ clearTimeout(t); resolve(m.tick); ws.close(); }
      });
      ws.on('error',reject);
    });
    res.status(200).json({quote:tick.quote, epoch:tick.epoch});
  } catch(e){ res.status(500).json({error:e.toString()}); }
}
