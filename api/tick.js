export const config = { runtime: 'nodejs' };
import WebSocket from 'ws';
export default async function handler(req,res){
res.setHeader('Access-Control-Allow-Origin','*');
res.setHeader('Cache-Control','no-store');
if(req.method==='OPTIONS') return res.status(200).end();
const urls=[
'wss://ws.binaryws.com/websockets/v3?app_id=1089',
'wss://ws.derivws.com/websockets/v3?app_id=1089',
'wss://ws.deriv.com/websockets/v3?app_id=1089'
];
for(let url of urls){
try{
const ws=new WebSocket(url);
const data=await new Promise((resolve,reject)=>{
const to=setTimeout(()=>{try{ws.close()}catch{};reject(new Error('timeout'));},7000);
ws.on('open',()=>{ws.send(JSON.stringify({ticks:'R_100'}));});
ws.on('message',(m)=>{try{
const j=JSON.parse(m.toString());
if(j.msg_type==='tick'){clearTimeout(to);resolve({quote:j.tick.quote});ws.close();}
}catch{}});
ws.on('error',(e)=>{clearTimeout(to);reject(e);});
});
return res.status(200).json(data);
}catch(e){ continue; }
}
res.status(500).json({error:'All WS urls failed 520 - retrying with HTTPS fallback'});
}
