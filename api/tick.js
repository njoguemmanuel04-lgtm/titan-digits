export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  let body={ticks:'R_100'};
  try{
    const c=[]; for await(const k of req) c.push(k);
    const t=Buffer.concat(c).toString();
    if(t) body=JSON.parse(t);
  }catch{}
  try{
    const WS=(await import('ws')).default;
    const ws=new WS('wss://ws.derivws.com/websockets/v3?app_id=1089');
    const d=await new Promise((ok,er)=>{
      const tm=setTimeout(()=>{try{ws.close()}catch{}; er(new Error('timeout'))},8000);
      ws.on('open',()=>ws.send(JSON.stringify(body)));
      ws.on('message',m=>{clearTimeout(tm); try{ws.close()}catch{}; ok(JSON.parse(m.toString()))});
      ws.on('error',e=>{clearTimeout(tm); er(e)});
    });
    return res.status(200).json(d);
  }catch(e){ return res.status(200).json({error:e.message});}
}
