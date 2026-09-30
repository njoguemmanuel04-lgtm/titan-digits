export const config={runtime:'nodejs'};
import WebSocket from 'ws';
export default async function handler(req,res){
 res.setHeader('Access-Control-Allow-Origin','*');
 res.setHeader('Access-Control-Allow-Methods','GET,OPTIONS');
 res.setHeader('Access-Control-Allow-Headers','Content-Type');
 if(req.method==='OPTIONS') return res.status(200).end();
 try{
  const quote=await new Promise((resolve,reject)=>{
   const ws=new WebSocket('wss://ws.derivws.com/websockets/v3?app_id=1089');
   const t=setTimeout(()=>{try{ws.close()}catch{};reject(new Error('timeout'));},6000);
   ws.on('open',()=>ws.send(JSON.stringify({ticks:'R_100'})));
   ws.on('message',(d)=>{try{let m=JSON.parse(d.toString());if(m.tick&&m.tick.quote){clearTimeout(t);resolve(m.tick.quote.toString());ws.close();}}catch{}});
   ws.on('error',(e)=>{clearTimeout(t);reject(e);});
  });
  res.status(200).json({quote});
 }catch(e){
  res.status(200).json({quote:(620+Math.random()).toFixed(2),fallback:true});
 }
}
