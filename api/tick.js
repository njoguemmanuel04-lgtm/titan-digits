export const config={runtime:'nodejs'};
import WebSocket from 'ws';
export default async function handler(req,res){
res.setHeader('Access-Control-Allow-Origin','*');
res.setHeader('Access-Control-Allow-Methods','POST,OPTIONS');
res.setHeader('Access-Control-Allow-Headers','Content-Type');
if(req.method==='OPTIONS') return res.status(200).end();
try{
const {token,buy_params}=req.body||JSON.parse(req.body||'{}');
if(!token||!buy_params) return res.status(400).json({error:'token and buy_params required'});
const ws=new WebSocket('wss://api.derivws.com/trading/v1/options/ws/public');
const result=await new Promise((resolve,reject)=>{
const t=setTimeout(()=>{try{ws.close()}catch{};reject(new Error('trade timeout'));},15000);
ws.on('open',()=>{ws.send(JSON.stringify({authorize:token}));});
ws.on('message',(d)=>{try{
const m=JSON.parse(d.toString());
if(m.error){clearTimeout(t);resolve({error:m.error.message});ws.close();return;}
if(m.msg_type==='authorize'){ws.send(JSON.stringify(buy_params));}
if(m.msg_type==='buy'){clearTimeout(t);resolve(m);ws.close();}
}catch{}});
ws.on('error',(e)=>{clearTimeout(t);reject(e);});
});
res.status(200).json(result);
}catch(e){res.status(500).json({error:e.message});}
}
