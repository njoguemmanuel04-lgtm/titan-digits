export const config={runtime:'nodejs'};
import WebSocket from 'ws';
export default async function handler(req,res){
 res.setHeader('Access-Control-Allow-Origin','*');
 res.setHeader('Access-Control-Allow-Methods','POST,OPTIONS');
 res.setHeader('Access-Control-Allow-Headers','Content-Type');
 if(req.method==='OPTIONS') return res.status(200).end();
 try{
  const body=typeof req.body==='string'?JSON.parse(req.body):req.body;
  const {token,buy_params}=body;
  if(!token||!buy_params) return res.status(400).json({error:'missing token'});
  const urls=['wss://ws.binaryws.com/websockets/v3?app_id=1089','wss://ws.derivws.com/websockets/v3?app_id=1089'];
  let result=null;
  for(let url of urls){
   try{
    const ws=new WebSocket(url,{headers:{Origin:'https://deriv.com'}});
    result=await new Promise((resolve,reject)=>{
      const t=setTimeout(()=>{try{ws.close()}catch{};reject(new Error('timeout'));},10000);
      ws.on('open',()=>ws.send(JSON.stringify({authorize:token})));
      ws.on('message',(d)=>{try{
        const m=JSON.parse(d.toString());
        if(m.error){clearTimeout(t);resolve({error:m.error});ws.close();}
        if(m.msg_type==='authorize') ws.send(JSON.stringify({buy:1,price:10,parameters:buy_params}));
        if(m.msg_type==='buy'){clearTimeout(t);resolve(m);ws.close();}
      }catch{}});
      ws.on('error',(e)=>{clearTimeout(t);reject(e);});
    });
    break;
   }catch(e){continue;}
  }
  res.status(200).json(result||{error:'all WS failed'});
 }catch(e){res.status(500).json({error:e.message});}
}
