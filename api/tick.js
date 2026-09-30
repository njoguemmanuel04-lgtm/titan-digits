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
  const endpoints=[
    'wss://ws.derivws.com/websockets/v3?app_id=1089',
    'wss://ws.binaryws.com/websockets/v3?app_id=1089',
    'wss://ws.deriv.com/websockets/v3?app_id=1089'
  ];
  for(const url of endpoints){
    try{
      const WS=(await import('ws')).default;
      const ws=new WS(url, { headers:{ Origin:'https://titan-digits.vercel.app' }});
      const d=await new Promise((ok,er)=>{
        const tm=setTimeout(()=>{try{ws.close()}catch{}; er(new Error('timeout '+url))},6000);
        ws.on('open',()=>ws.send(JSON.stringify(body)));
        ws.on('message',m=>{clearTimeout(tm); try{ws.close()}catch{}; ok(JSON.parse(m.toString()))});
        ws.on('error',e=>{clearTimeout(tm); er(e)});
      });
      return res.status(200).json(d);
    }catch(e){
      if(url===endpoints[endpoints.length-1]) return res.status(200).json({error:e.message, tried:endpoints});
      continue;
    }
  }
}
