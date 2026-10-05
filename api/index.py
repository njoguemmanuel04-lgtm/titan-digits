import os, json
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import BaseHTTPRequestHandler
API_BASE="https://api.derivws.com"
DERIV_APP_ID=os.environ.get("DERIV_APP_ID","")
def deriv_request(method,url,token):
 headers={"Authorization":"Bearer "+token,"Deriv-App-ID":DERIV_APP_ID,"Accept":"application/json","Content-Type":"application/json"}
 req=Request(url,method=method,headers=headers)
 try:
  with urlopen(req,timeout=20) as r: return r.status, json.loads(r.read().decode())
 except HTTPError as e:
  raw=e.read().decode("utf-8",errors="replace")
  try: data=json.loads(raw)
  except: data={"error":raw}
  return e.code,data
 except Exception as e: return 500,{"error":str(e)}
def error_message(d):
 if isinstance(d,dict):
  if d.get("error"): return str(d["error"])
  if isinstance(d.get("errors"),list) and d["errors"]:
   f=d["errors"][0];return f.get("message",f.get("code","Error")) if isinstance(f,dict) else str(f)
  if d.get("message"): return str(d["message"])
 return "Unknown error"
class handler(BaseHTTPRequestHandler):
 def send_json(self,s,d):
  b=json.dumps(d).encode();self.send_response(s);self.send_header("Content-Type","application/json");self.send_header("Cache-Control","no-store");self.send_header("Access-Control-Allow-Origin","*");self.send_header("Access-Control-Allow-Headers","Content-Type");self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS");self.end_headers();self.wfile.write(b)
 def do_OPTIONS(self):self.send_response(204);self.send_header("Access-Control-Allow-Origin","*");self.send_header("Access-Control-Allow-Headers","Content-Type");self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS");self.end_headers()
 def do_POST(self):
  if self.path!="/api/deriv-auth": self.send_json(404,{"ok":False,"error":"Not found"});return
  try:
   length=int(self.headers.get("Content-Length","0"));body=json.loads(self.rfile.read(length).decode());token=str(body.get("token","")).strip();mode=str(body.get("mode","demo")).lower()
   if not token: self.send_json(400,{"ok":False,"error":"Token required"});return
   if not DERIV_APP_ID: self.send_json(500,{"ok":False,"error":"APP_ID missing"});return
   st,acc_res=deriv_request("GET",API_BASE+"/trading/v1/options/accounts",token)
   if st!=200: self.send_json(st,{"ok":False,"error":error_message(acc_res),"stage":"accounts"});return
   accs=acc_res.get("data",[]);
   if isinstance(accs,dict): accs=[accs]
   matched=[a for a in accs if str(a.get("account_type","")).lower()==mode];acc=matched[0] if matched else accs[0]
   otp_url=f"{API_BASE}/trading/v1/options/accounts/{acc.get('account_id')}/otp";ost,otp_res=deriv_request("POST",otp_url,token)
   if ost not in (200,201): self.send_json(ost,{"ok":False,"error":error_message(otp_res),"stage":"otp"});return
   ws_url=otp_res.get("data",{}).get("url")
   if not ws_url: self.send_json(500,{"ok":False,"error":"No WS URL"});return
   self.send_json(200,{"ok":True,"account_id":acc.get("account_id"),"account_type":acc.get("account_type",""),"balance":acc.get("balance",0),"currency":acc.get("currency","USD"),"ws_url":ws_url})
  except Exception as e: self.send_json(500,{"ok":False,"error":str(e)})
 def do_GET(self):
  html="""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>TITAN V10.2 0.35 FIX</title><script src="https://cdn.tailwindcss.com"></script><style>body{background:#030804;color:#00ff66;font-family:monospace}.titan-card{background:#07120a;border:1px solid rgba(0,255,102,.25);border-radius:12px}.btn-green{background:linear-gradient(135deg,#00ff66,#00b347);color:#000;font-weight:900}</style></head><body class="p-3"><div class="max-w-md mx-auto space-y-3">
<div class="titan-card p-3"><div class="flex justify-between items-center mb-2"><div class="font-black text-lg text-emerald-400">🚀 TITAN V10.2 0.35 FIX</div><div class="text-right"><div class="text-xs text-emerald-500 font-bold" id="accountTypeDisplay">DEMO MODE</div><div class="text-sm font-black" id="balanceDisplay">Bal: $0.00</div></div></div>
<div class="flex gap-2"><select id="accountMode" class="bg-black border border-emerald-500/40 rounded-lg px-2 text-xs font-bold text-emerald-400"><option value="demo">DEMO</option><option value="real">REAL</option></select><input id="token" type="password" placeholder="Paste PAT..." class="w-full bg-black border border-emerald-500/40 rounded-lg px-3 py-2 text-xs"></div><button onclick="connectNow()" id="connectBtn" class="w-full btn-green py-2.5 rounded-lg text-sm mt-2">🔌 CONNECT TO DERIV</button></div>
<div class="titan-card p-3"><div class="flex justify-between text-xs mb-1"><span>MULTI MARKET 5x - EVEN/ODD + OVER/UNDER</span><span id="dotStatus">🔴 NOT CONNECTED</span></div><div id="marketStatus" class="grid grid-cols-5 gap-1 text-[9px] mb-2"></div><div class="text-center py-1"><div id="lastDigit" class="text-5xl font-black text-emerald-400">-</div><div id="tickInfo" class="text-xs">WAITING FOR TICKS</div></div></div>
<div class="titan-card p-3"><div class="flex justify-between text-xs font-bold"><span>SCANNER (0.35 READY)</span><span>WIN RATE: <b id="conf" class="text-yellow-400">0%</b></span></div><div id="scanDetails" class="text-[11px] mb-1">Collecting 30 ticks per market...</div><div id="bestMarket" class="text-sm font-bold text-yellow-400">🎯 Waiting for 85% bias...</div></div>
<div class="titan-card p-3 space-y-2"><div class="grid grid-cols-4 gap-2 text-center text-xs"><div><div class="text-[10px]">STAKE</div><input id="stake" value="0.35" step="0.01" min="0.35" class="w-full bg-black border border-emerald-500/30 rounded p-1.5 text-center font-bold"></div><div><div class="text-[10px]">MARTI</div><input id="martingale" value="2.0" step="0.1" class="w-full bg-black border border-emerald-500/30 rounded p-1.5 text-center font-bold"></div><div><div class="text-[10px]">TP</div><input id="tp" value="4" class="w-full bg-black border border-emerald-500/30 rounded p-1.5 text-center font-bold"></div><div><div class="text-[10px]">SL</div><input id="sl" value="6" class="w-full bg-black border border-emerald-500/30 rounded p-1.5 text-center font-bold text-red-400"></div></div>
<div class="grid grid-cols-2 gap-2 text-[10px]"><div><div>MAX MARTI STEPS</div><input id="maxSteps" value="3" class="w-full bg-black border border-red-500/30 rounded p-1.5 text-center font-bold"></div><div><div>BAL PROTECT %</div><input id="balanceProtect" value="40" class="w-full bg-black border border-yellow-500/30 rounded p-1.5 text-center font-bold text-yellow-400"></div></div>
<button onclick="startTrading()" id="fireBtn" class="w-full btn-green py-3 rounded-lg">🚀 SCAN & TRADE ALL MARKETS</button><div class="grid grid-cols-2 gap-2"><button onclick="stopTrading()" class="bg-red-600/80 text-white font-bold py-2 rounded-lg text-xs">⏹️ STOP</button><button onclick="clearLog()" class="bg-emerald-950/60 border border-emerald-500/30 font-bold py-2 rounded-lg text-xs">🧹 CLEAR</button></div></div>
<div class="titan-card p-3 text-xs"><div class="flex justify-between font-bold border-b border-emerald-500/20 pb-2 mb-2"><span>W: <b id="wins" class="text-emerald-400">0</b> L: <b id="loss" class="text-red-400">0</b> S: <b id="streak">0</b></span><span>P: <b id="profit" class="text-yellow-400">$0.00</b></span></div><div id="log" class="h-44 overflow-y-auto text-[11px] space-y-1"></div></div></div>
<script>
let markets=["R_10","R_25","R_50","R_75","R_100"];
let histories={}, ws=null,trading=false,dotConnected=false,awaitingResult=false,nextStake=0.35,profit=0,wins=0,losses=0,balance=0,pendingBuy=false,contractId=null,lossStreak=0;
markets.forEach(m=>{histories[m]=[];});
function initMarketStatus(){let el=document.getElementById("marketStatus");el.innerHTML="";markets.forEach(m=>{let d=document.createElement("div");d.id="ms_"+m;d.className="bg-black border border-emerald-500/20 rounded p-1 text-center";d.innerHTML=`<div class="font-bold">${m.replace("R_","R")}</div><div id="ms_${m}_ticks">0</div><div id="ms_${m}_sig" class="text-yellow-400">-</div>`;el.appendChild(d);});}
initMarketStatus();
function logM(m){let l=document.getElementById("log");l.innerHTML+=`<div>[${new Date().toLocaleTimeString()}] ${m}</div>`;l.scrollTop=l.scrollHeight;}
function playSound(win){try{let ctx=new (window.AudioContext||window.webkitAudioContext)();let o=ctx.createOscillator();let g=ctx.createGain();o.type="sine";o.frequency.value=win?880:220;g.gain.value=0.3;o.connect(g);g.connect(ctx.destination);o.start();setTimeout(()=>{o.stop();ctx.close();}, win?300:500);}catch(e){}}
function scanMarket(market){
 let history=histories[market];
 if(history.length<30) return null;
 let last=history[history.length-1];
 let r20=history.slice(-20);
 let evenCount=r20.filter(d=>d%2===0).length;
 let oddCount=20-evenCount;
 if(evenCount>=17){ return {marketSymbol:market,contract_type:"DIGITODD",barrier:null,conf:86,type:`${market} EVEN ${evenCount*5}% -> ODD`,priority:evenCount}; }
 if(oddCount>=17){ return {marketSymbol:market,contract_type:"DIGITEVEN",barrier:null,conf:86,type:`${market} ODD ${oddCount*5}% -> EVEN`,priority:oddCount}; }
 let over1=Math.round(r20.filter(d=>d>1).length/20*100);
 let under8=Math.round(r20.filter(d=>d<8).length/20*100);
 if((last===0||last===1)&&over1>=80){ return {marketSymbol:market,contract_type:"DIGITOVER",barrier:1,conf:85,type:`${market} OVER 1 Pullback Last=${last} ${over1}%`,priority:over1}; }
 if((last===8||last===9)&&under8>=80){ return {marketSymbol:market,contract_type:"DIGITUNDER",barrier:8,conf:85,type:`${market} UNDER 8 Pullback Last=${last} ${under8}%`,priority:under8}; }
 return null;
}
function findBestSignal(){
 let best=null;
 markets.forEach(m=>{
   let sig=scanMarket(m);
   let tickEl=document.getElementById(`ms_${m}_ticks`);
   if(tickEl) tickEl.innerText=histories[m].length;
   let sigEl=document.getElementById(`ms_${m}_sig`);
   if(sigEl) sigEl.innerText=sig?sig.contract_type.replace("DIGIT",""):"WAIT";
   if(sig && (!best || sig.conf>best.conf || (sig.conf===best.conf && sig.priority>best.priority))){
     best=sig;
   }
 });
 return best;
}
async function connectNow(){
 let token=document.getElementById("token").value.trim(), mode=document.getElementById("accountMode").value;
 if(!token){logM("❌ PASTE TOKEN");return;}if(ws)try{ws.close()}catch(e){}
 dotConnected=false;document.getElementById("connectBtn").innerText="⏳ CONNECTING...";
 try{
  let r=await fetch("/api/deriv-auth",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token,mode})});
  let data=await r.json(); if(!r.ok||!data.ok) throw new Error(data.error);
  logM(`✅ ${data.account_id} (${data.account_type}) Bal $${data.balance}`);document.getElementById("accountTypeDisplay").innerText=data.account_type.toUpperCase()+" MODE";document.getElementById("balanceDisplay").innerText=`Bal: $${parseFloat(data.balance).toFixed(2)}`;
  connectAuthenticatedWS(data.ws_url);localStorage.setItem("deriv_token",token);
 }catch(e){logM("❌ AUTH: "+e.message);document.getElementById("dotStatus").innerText="🔴 NOT CONNECTED";document.getElementById("connectBtn").innerText="🔌 CONNECT";}
}
function connectAuthenticatedWS(url){
 ws=new WebSocket(url);
 ws.onopen=()=>{dotConnected=true;document.getElementById("dotStatus").innerText="🟢 5 MARKETS CONNECTED";document.getElementById("connectBtn").innerText="✅ CONNECTED";ws.send(JSON.stringify({balance:1,subscribe:1}));
   markets.forEach(m=>{ws.send(JSON.stringify({ticks:m,subscribe:1}));});
   logM("📡 V10.2 0.35 FIX LIVE: R_10,R_25,R_50,R_75,R_100");
   setTimeout(()=>{if(!trading){logM("🤖 AUTO STARTING...");startTrading();}},1500);
 };
 ws.onmessage=(ev)=>{
  let data=JSON.parse(ev.data);
  if(data.error){logM(`❌ ERR: ${data.error.message||data.error.code}`);pendingBuy=false;awaitingResult=false;return;}
  if(data.msg_type==="balance"&&data.balance){balance=Number(data.balance.balance);document.getElementById("balanceDisplay").innerText=`Bal: $${balance.toFixed(2)}`;}
  if(data.msg_type==="tick"&&data.tick){
    let symbol=data.tick.symbol||data.echo_req?.ticks||"R_100";
    if(!histories[symbol]) symbol="R_100";
    let q=String(data.tick.quote),d=Number(q.slice(-1));
    histories[symbol].push(d); if(histories[symbol].length>100) histories[symbol].shift();
    document.getElementById("lastDigit").innerText=d; document.getElementById("tickInfo").innerText=`${symbol} LIVE ${q}`;
    let best=findBestSignal();
    if(best){
      document.getElementById("conf").innerText=best.conf+"%";
      document.getElementById("bestMarket").innerText=`🎯 ${best.type}`;
      document.getElementById("scanDetails").innerText=`Best: ${best.marketSymbol} ${best.contract_type} | 0.35 READY`;
      if(trading&&!awaitingResult&&!pendingBuy) doTrade(best);
    } else {
      document.getElementById("bestMarket").innerText="Scanning 5 markets... waiting 85% bias";
    }
  }
  if(data.msg_type==="proposal"&&data.proposal){ws.send(JSON.stringify({buy:data.proposal.id,price:Number(data.proposal.ask_price)}));}
  if(data.msg_type==="buy"&&data.buy){pendingBuy=false;contractId=data.buy.contract_id;awaitingResult=true;logM(`📈 BOUGHT #${contractId} $${pendingStake.toFixed(2)} ${data.buy.longcode||""}`);ws.send(JSON.stringify({proposal_open_contract:1,contract_id:contractId,subscribe:1}));}
  if(data.msg_type==="proposal_open_contract"&&data.proposal_open_contract){
   let c=data.proposal_open_contract;
   if(c.is_sold){let p=Number(c.profit||0);profit+=p;
    if(p>0){wins++;lossStreak=0;nextStake=Math.round(Number(document.getElementById("stake").value)*100)/100;logM(`✅ WIN +$${p.toFixed(2)} PROF $${profit.toFixed(2)}`);playSound(true);}
    else{losses++;lossStreak++;let maxS=Number(document.getElementById("maxSteps").value);let marti=Number(document.getElementById("martingale").value);nextStake=Math.round(nextStake*marti*100)/100;if(lossStreak>=maxS){stopTrading();logM(`🛑 MAX MARTI ${maxS} HIT STOP @ $${nextStake.toFixed(2)}`);}else logM(`❌ LOSS $${Math.abs(p).toFixed(2)} → Next $${nextStake.toFixed(2)} (${lossStreak}/${maxS})`);playSound(false);}
    document.getElementById("profit").innerText=`$${profit.toFixed(2)}`;document.getElementById("wins").innerText=wins;document.getElementById("loss").innerText=losses;document.getElementById("streak").innerText=lossStreak;
    let tp=Number(document.getElementById("tp").value), sl=Number(document.getElementById("sl").value);
    if(profit>=tp){stopTrading();logM(`🎯 TP $${tp} HIT`);}
    if(profit<=-sl){stopTrading();logM(`🛑 SL -$${sl}`);}
    awaitingResult=false;}
  }
 };
 ws.onclose=()=>{dotConnected=false;document.getElementById("dotStatus").innerText="🔴 CLOSED";document.getElementById("connectBtn").innerText="🔌 RECONNECT";};
}
let pendingStake=0;
function doTrade(best){
 if(!dotConnected||awaitingResult||pendingBuy) return;
 let base=Math.round(Number(document.getElementById("stake").value)*100)/100; if(nextStake<base) nextStake=base;
 nextStake=Math.round(nextStake*100)/100;
 let protect=Number(document.getElementById("balanceProtect").value||40);
 let maxAllowed=balance*(protect/100);
 if(nextStake>maxAllowed){
   logM(`⚠️ BAL PROTECT ${protect}%: $${nextStake.toFixed(2)} > $${maxAllowed.toFixed(2)} STOP`);
   stopTrading(); return;
 }
 if(nextStake>balance){
   logM(`⚠️ LOW BAL $${balance.toFixed(2)} < $${nextStake.toFixed(2)} STOP`);
   stopTrading(); return;
 }
 pendingStake=Math.round(nextStake*100)/100;
 logM(`🎯 ${best.type} @ $${pendingStake.toFixed(2)} ${best.marketSymbol} ${best.contract_type} ${best.barrier!==null?"Barrier "+best.barrier:""}`);
 let req={proposal:1,amount:pendingStake,basis:"stake",contract_type:best.contract_type,currency:"USD",duration:1,duration_unit:"t",underlying_symbol:best.marketSymbol};
 if(best.barrier!==null && best.barrier!==undefined) req.barrier=String(best.barrier);
 ws.send(JSON.stringify(req)); pendingBuy=true;
}
function startTrading(){if(!dotConnected){connectNow();return;}trading=true;lossStreak=0;profit=0;wins=0;losses=0;nextStake=Math.round(Number(document.getElementById("stake").value)*100)/100;document.getElementById("profit").innerText="$0.00";document.getElementById("wins").innerText="0";document.getElementById("loss").innerText="0";document.getElementById("streak").innerText="0";document.getElementById("fireBtn").innerText="✅ 0.35 FIX LIVE...";logM("🧠 V10.2 0.35 FIX STARTED");}
function stopTrading(){trading=false;pendingBuy=false;document.getElementById("fireBtn").innerText="🚀 SCAN & TRADE ALL MARKETS";logM("⏹️ STOPPED");}
function clearLog(){document.getElementById("log").innerHTML="";}
window.onload=()=>{let s=localStorage.getItem("deriv_token");if(s)document.getElementById("token").value=s;};
</script></body></html>"""
  self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Cache-Control","no-cache");self.end_headers();self.wfile.write(html.encode("utf-8"))
