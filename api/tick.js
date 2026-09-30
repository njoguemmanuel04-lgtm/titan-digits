export const config = { runtime: 'nodejs' };
import WebSocket from 'ws';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin','*');
  res.setHeader('Cache-Control','no-store');
  if(req.method==='OPTIONS') return res.status(200).end();
  try{
    const ws = new WebSocket('wss://ws.derivws.com/websockets/v3?app_id=1089');
    const data = await new Promise((resolve, reject)=>{
      const timeout = setTimeout(()=>{ try{ws.close()}catch{}; reject(new Error('timeout')); }, 8000);
      ws.on('open',()=>{ ws.send(JSON.stringify({ticks:'R_100'})); });
      ws.on('message',(msg)=>{
        try{
          const m = JSON.parse(msg.toString());
          if(m.msg_type==='tick'){
            clearTimeout(timeout);
            resolve({quote:m.tick.quote, symbol:m.tick.symbol});
            ws.close();
          }
        }catch{}
      });
      ws.on('error',(e)=>{ clearTimeout(timeout); reject(e); });
    });
    res.status(200).json(data);
  }catch(e){
    res.status(500).json({error:e.message});
  }
}
