export const config={runtime:'nodejs'};
import WebSocket from 'ws';
const ENDPOINTS=[
 'wss://ws.derivws.com/websockets/v3?app_id=1089',
 'wss://ws.binaryws.com/websockets/v3?app_id=1089',
 'wss://ws.deriv.com/websockets/v3?app_id=1089'
];
async function getTick(url){
 return await new Promise((resolve,reject)=>{
  try{
   const ws=new WebSocket(url,{handshakeTimeout:5000});
   const t=setTimeout(()=>{try{ws.terminate()}catch{};reject(new Error('timeout '+url));},7000);
   ws.on('open',()=>ws.send(JSON.stringify({ticks:'R_100'})));
   ws.on('message',(d)=>{try{const m=JSON.parse(d.toString());if(m.tick&&m.tick.quote){clearTimeout(t);resolve(m.tick.quote.toString());try{ws.close()}catch{}}}catch{}});
   ws.on('error',(e)=>{clearTimeout(t);reject(e);});
   ws.on('close',()=>{clearTimeout(t);reject(new Error('closed '+url));});
  }catch(e){reject(e);}
 });
}
export default async function handler(req,res){
 res.setHeader('Access-Control-Allow-Origin','*');
 res.setHeader('Access-Control-Allow-Methods','GET,OPTIONS');
 res.setHeader('Access-Control-Allow-Headers','Content-Type');
 if(req.method==='OPTIONS') return res.status(200).end();
 for(const url of ENDPOINTS){
  try{const quote=await getTick(url);return res.status(200).json({quote,source:url});}catch{}
 }
 res.status(200).json({quote:(620+Math.random()).toFixed(2),fallback:true,error:'all ws failed'});
}
