import os, requests
from flask import Flask, request, Response, jsonify
app=Flask(__name__)
DERIV_REST="https://api.derivws.com"
DERIV_APP_ID=os.environ.get("DERIV_APP_ID","34xM40w3JyILr0iqbYGhhM")

@app.route("/api/deriv-auth", methods=["POST","OPTIONS"])
def deriv_auth():
    if request.method=="OPTIONS": return Response("",200,headers={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"*","Access-Control-Allow-Methods":"POST, OPTIONS"})
    try:
        pat=request.get_json(force=True,silent=True).get("pat","").strip()
        headers={"Authorization":f"Bearer {pat}","Deriv-App-ID":DERIV_APP_ID,"Accept":"application/json"}
        r=requests.get(f"{DERIV_REST}/trading/v1/options/accounts",headers=headers,timeout=20)
        return jsonify({"ok":True,"accounts":r.json().get("data",[])})
    except Exception as e: return jsonify({"error":str(e)}),500

@app.route("/api/deriv-otp", methods=["POST","OPTIONS"])
def deriv_otp():
    if request.method=="OPTIONS": return Response("",200,headers={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"*","Access-Control-Allow-Methods":"POST, OPTIONS"})
    try:
        b=request.get_json(force=True); headers={"Authorization":f"Bearer {b.get('pat','')}","Deriv-App-ID":DERIV_APP_ID,"Accept":"application/json"}
        r=requests.post(f"{DERIV_REST}/trading/v1/options/accounts/{b.get('account_id')}/otp",headers=headers,timeout=20)
        return jsonify({"ok":True,"ws_url":r.json().get("data",{}).get("url")})
    except Exception as e: return jsonify({"error":str(e)}),500

@app.route('/', methods=["GET"])
def home():
    return Response("""
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TITAN V27 TRADES</title><script src="https://cdn.tailwindcss.com"></script>
<style>
body{background:#0b0f1f;color:#fff;font-family:system-ui;margin:0}
.big{font-size:110px;font-weight:900;color:#2df28b;line-height:1;text-align:center;margin-top:5px}
.grid-box{background:#1a203a;border-radius:10px;padding:10px 0;text-align:center;border:2px solid transparent}
.grid-box.hot{border-color:#2df28b;box-shadow:0 0 12px #2df28b88}
.grid-box.cold{opacity:0.4}
.inp{background:#171d35;border:1px solid #2a345c;border-radius:12px;padding:12px;color:#fff;width:100%;text-align:center}
.btn{border-radius:12px;font-weight:900;padding:12px;width:100%}
.log{background:#040712;border-radius:12px;padding:8px;height:240px;overflow:auto;color:#2df28b;font-family:monospace;font-size:11px;line-height:1.4}
</style>
</head><body class="p-3 max-w-[400px] mx-auto">

<div class="text-center font-black text-[15px] tracking-widest mt-1">TITAN DIGITS - FINAL FIX</div>
<div id="big" class="big">4</div>
<div id="tick" class="text-center text-[#2df28b] text-xs font-mono">TICK -- LAST:--</div>

<div id="grid" class="grid grid-cols-5 gap-2 mt-3"></div>

<div class="text-center text-[12px] font-mono mt-3">
History:<span id="hLen">0</span> | PREDICT:<span id="pred" class="text-[#2df28b] font-bold">0</span> | CONF:<span id="conf">0%</span>
</div>
<div class="flex justify-center gap-3 mt-1 text-[10px] font-mono">
<span class="text-[#2df28b]">🔥 HOT: <span id="hotTxt">-</span></span>
<span class="text-red-400">❄️ COLD: <span id="coldTxt">-</span></span>
</div>
<div id="status" class="text-center text-[10px] text-gray-400 mt-2">Loading saved token...</div>

<input id="pat" type="password" class="inp mt-2" placeholder="pat_...">
<button onclick="toggle()" class="btn mt-2 bg-[#2df28b] text-black text-sm">👁️ Show / Hide Token</button>

<div class="grid grid-cols-3 gap-2 mt-2">
<select id="ctype" class="inp text-xs"><option value="DIGITOVER">Over</option><option value="DIGITUNDER">Under</option><option value="DIGITMATCH">Match</option><option value="DIGITDIFF">Diff</option><option value="DIGITEVEN">Even</option><option value="DIGITODD">Odd</option></select>
<input id="digit" type="number" class="inp text-sm" value="5" placeholder="D">
<input id="stake" type="number" class="inp text-sm" value="1" step="0.1">
</div>

<button onclick="connect()" id="btnConn" class="btn mt-2 bg-[#1a203a] border text-white text-sm">🔍 LOAD & CONNECT</button>
<button onclick="startBot()" id="btnStart" class="btn mt-2 bg-[#2df28b] text-black">SAVE TOKEN & START TRADING</button>
<div class="grid grid-cols-2 gap-2 mt-2">
<button onclick="startBot()" class="btn bg-green-500 text-black text-xs py-2">▶️ START BOT</button>
<button onclick="stopBot()" class="btn bg-red-500 text-white text-xs py-2">⏹️ STOP</button>
</div>

<div id="bal" class="text-center text-xs font-mono mt-2">Balance: - | P:$0 W:0 L:0 Next:$1</div>
<div class="text-center text-[10px] text-gray-500">Token stored only in YOUR phone</div>

<div id="log" class="log mt-2">> FINAL V27 - Trades will show here<br></div>

<script>
let digitCounts=Array(10).fill(0), history=[], ws=null, currentPat="", auto=false, curStake=1, profit=0, wins=0, losses=0, lastPrice="0";
function log(m, col="#2df28b"){ let l=document.getElementById("log"); let c=col=="#2df28b"? "" : `style="color:${col}"`; l.innerHTML=`<div ${c}>> ${m}</div>`+l.innerHTML; }
function toggle(){ let p=document.getElementById("pat"); p.type=p.type=="password"?"text":"password"; }

function loadSaved(){ let s=localStorage.getItem("titan_pat"); if(s){ document.getElementById("pat").value=s; document.getElementById("status").innerText="✅ SAVED "+s.slice(0,10)+"..."; log("LOADED SAVED TOKEN - Memory ✅"); setTimeout(()=>connect(),800);} renderGrid(); }
function renderGrid(){
  let total=history.length||1;
  let sorted=[...Array(10).keys()].map(i=>({d:i,c:digitCounts[i],p:Math.round(digitCounts[i]/total*100)||0})).sort((a,b)=>b.c-a.c);
  document.getElementById("hotTxt").innerText=sorted.slice(0,3).map(h=>h.d).join(" ");
  document.getElementById("coldTxt").innerText=sorted.slice(-3).map(c=>c.d).join(" ");
  document.getElementById("hLen").innerText=history.length;
  document.getElementById("pred").innerText=sorted[0]?.d??"0";
  document.getElementById("conf").innerText=(sorted[0]?.p||0)+"%";
  let g=document.getElementById("grid"); g.innerHTML="";
  for(let i=0;i<10;i++){
    let pct=history.length?Math.round(digitCounts[i]/history.length*100):0;
    let isHot=sorted[0]?.d==i, isCold=sorted.slice(-3).some(c=>c.d==i);
    let cls=isHot?"grid-box hot":isCold?"grid-box cold":"grid-box";
    g.innerHTML+=`<div class="${cls}"><div class="text-lg font-black">${i}</div><div class="text-[10px] opacity-60">${pct}%</div></div>`;
  }
}

async function connect(){
  let pat=document.getElementById("pat").value.trim(); if(!pat.startsWith("pat_")){alert("pat_ required");return;}
  currentPat=pat; localStorage.setItem("titan_pat",pat); document.getElementById("btnConn").innerText="⏳...";
  let r=await fetch("/api/deriv-auth",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pat})});
  let j=await r.json(); if(j.error){log("❌ "+j.error,"#ef4444");return;}
  let acc=j.accounts.find(a=>a.account_id.includes("DOT"))||j.accounts[0];
  let r2=await fetch("/api/deriv-otp",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pat, account_id:acc.account_id})});
  let j2=await r2.json(); ws=new WebSocket(j2.ws_url);
  ws.onopen=()=>{ document.getElementById("status").innerText=`🟢 ${acc.account_id} CONNECTED`; log(`CONNECTED ${acc.account_id} $${acc.balance}`,"#22c55e"); ws.send(JSON.stringify({ticks:"R_10", subscribe:1})); ws.send(JSON.stringify({balance:1, subscribe:1})); document.getElementById("btnConn").innerText=`✅ ${acc.account_id}`; document.getElementById("btnStart").innerText="✅ CONNECTED - START BOT NOW"; };
  ws.onmessage=(e)=>{
    let d=JSON.parse(e.data);
    if(d.tick){ lastPrice=d.tick.quote; let last=parseInt(String(lastPrice).slice(-1)); document.getElementById("big").innerText=last; document.getElementById("tick").innerText=`TICK ${lastPrice} LAST:${last} via ${d.tick.symbol||'live'}`; history.unshift(last); if(history.length>100) history.pop(); digitCounts[last]++; renderGrid(); log(`TICK ${lastPrice} LAST:${last} | PRED:${document.getElementById("pred").innerText} ${document.getElementById("conf").innerText}`); }
    if(d.balance){ document.getElementById("bal").innerText=`Balance:$${d.balance.balance} | P:$${profit.toFixed(2)} W:${wins} L:${losses} Next:$${curStake}`; }
    if(d.proposal && auto){ log(`PROP id:${d.proposal.id} stake $${curStake}`,"#facc15"); ws.send(JSON.stringify({buy:d.proposal.id, price:curStake})); }
    if(d.proposal_open_contract && d.proposal_open_contract.is_sold){
      let pl=parseFloat(d.proposal_open_contract.profit); profit+=pl;
      if(pl>0){ wins++; curStake=parseFloat(document.getElementById("stake").value); log(`✅ WIN $${pl.toFixed(2)} D:${history[0]} Profit:$${profit.toFixed(2)}`,"#2df28b"); }
      else { losses++; curStake=(curStake*2.1).toFixed(2); log(`❌ LOSS $${pl.toFixed(2)} D:${history[0]} Next:$${curStake}`,"#ef4444"); }
      document.getElementById("bal").innerText=`Balance:$${d.proposal_open_contract.bid_price||'-'} | P:$${profit.toFixed(2)} W:${wins} L:${losses} Next:$${curStake}`;
      if(auto) setTimeout(()=>trade(),1200);
    }
    if(d.error){ log(`❌ ${d.error.message||JSON.stringify(d.error)}`,"#ef4444"); }
  };
}

function trade(){
  if(!ws||ws.readyState!=1){ log("❌ Not connected","#ef4444"); return; }
  let c=document.getElementById("ctype").value, dig=parseInt(document.getElementById("digit").value);
  let base={proposal:1, amount:parseFloat(curStake), basis:"stake", contract_type:c, currency:"USD", duration:1, duration_unit:"t", underlying_symbol:"R_10"};
  if(["DIGITOVER","DIGITUNDER","DIGITMATCH","DIGITDIFF"].includes(c)) base.barrier=dig;
  log(`➡️ TRADE ${c} ${c.includes("DIGIT")&&!["DIGITEVEN","DIGITODD"].includes(c)?dig:""} $${curStake} D:${history[0]||'-'}`,"#facc15");
  ws.send(JSON.stringify(base));
}
function startBot(){ auto=true; curStake=parseFloat(document.getElementById("stake").value); document.getElementById("btnStart").innerText="🤖 RUNNING"; log("▶️ BOT STARTED","#22c55e"); trade(); }
function stopBot(){ auto=false; document.getElementById("btnStart").innerText="▶️ STOPPED - START AGAIN"; log("⏹️ BOT STOPPED","#ef4444"); }
window.onload=loadSaved;
</script></body></html>
""", mimetype="text/html")
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
