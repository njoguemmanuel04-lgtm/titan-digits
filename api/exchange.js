export default async function handler(req,res){
  const {code} = req.query;
  if(!code) return res.status(400).json({error:'no_code'});
  // Deriv OAuth token exchange
  try{
    const r = await fetch('https://oauth.deriv.com/oauth2/token',{
      method:'POST',
      headers:{'Content-Type':'application/x-www-form-urlencoded'},
      body: new URLSearchParams({
        app_id: '34xM40w3JyILr0iqbYGhh',
        code: code,
        grant_type: 'authorization_code'
      })
    });
    const data = await r.json();
    return res.json(data);
  }catch(e){
    return res.status(500).json({error:e.message});
  }
}
