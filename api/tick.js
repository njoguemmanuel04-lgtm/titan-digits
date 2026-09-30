export const config = { runtime: 'nodejs' };
import WebSocket from 'ws';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin','*');
  res.setHeader('Cache-Control','no-store');
  try {
    const ws = new WebSocket('wss://api.derivws.com/trading/v1/options/ws/public');
    const tick = await new Promise((resolve, reject) => {
      const t = setTimeout(()=>{ try{ws.close()}catch{}; reject(new Error('timeout')); }, 8000);
      ws.on('open',()=>{ ws.send(JSON.stringify({ ticks: "R_100" })); });
      ws.on('message',(d)=>{
        try{
          const m=JSON.parse(d.toString());
          if(m.tick){ clearTimeout(t); resolve(m.tick); ws.close(); }
        }catch{}
      });
      ws.on('error',(e)=>{ clearTimeout(t); reject(e); });
    });
    res.status(200).json({ quote: tick.quote, epoch: tick.epoch, symbol: tick.symbol });
  } catch(e) {
    res.status(500).json({ error: e.message || e.toString() });
  }
}
