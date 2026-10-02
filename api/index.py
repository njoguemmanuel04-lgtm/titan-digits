import os, requests
from flask import Flask, request, Response, jsonify
app=Flask(__name__)
DERIV_REST="https://api.derivws.com"
DERIV_APP_ID=os.environ.get("DERIV_APP_ID","34xM40w3JyILr0iqbYGhhM")

@app.route("/api/deriv-auth", methods=["POST","OPTIONS"])
def d_auth():
    if request.method=="OPTIONS": return Response("",200,headers={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"*","Access-Control-Allow-Methods":"POST, OPTIONS"})
    try:
        pat=request.get_json(force=True,silent=True).get("pat","").strip()
        h={"Authorization":f"Bearer {pat}","Deriv-App-ID":DERIV_APP_ID,"Accept":"application/json"}
        r=requests.get(f"{DERIV_REST}/trading/v1/options/accounts",headers=h,timeout=20)
        return jsonify({"ok":True,"accounts":r.json().get("data",[])})
    except Exception as e: return jsonify({"error":str(e)}),500

@app.route("/api/deriv-otp", methods=["POST","OPTIONS"])
def d_otp():
    if request.method=="OPTIONS": return Response("",200,headers={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"*","Access-Control-Allow-Methods":"POST, OPTIONS"})
    try:
        b=request.get_json(force=True); h={"Authorization":f"Bearer {b.get('pat','')}","Deriv-App-ID":DERIV_APP_ID,"Accept":"application/json"}
        r=requests.post(f"{DERIV_REST}/trading/v1/options/accounts/{b.get('account_id')}/otp",headers=h,timeout=20)
        return jsonify({"ok":True,"ws_url":r.json().get("data",{}).get("url")})
    except Exception as e: return jsonify({"error":str(e)}),500

@app.route('/', methods=["GET"])
def home():
    return Response("""
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TITAN V28 SCANNER</title><script src="https://cdn.tailwindcss.com"></script>
<style>
body{background:#0b0f1f;color:#fff;font-family:system-ui;margin:0}
.big{font-size:100px;font-weight:900;color:#2df28b;text-align:center;line-height:1}
.box{background:#1a203a;border-radius:10px;padding:10px 0;text-align:center;border:2px solid transparent}
.box.hot{border-color:#2df28b;box-shadow:0 0 12px #2df28b88}
.box.cold{opacity:0.4}
.inp{background:#171d35;border:1px solid #2a345c;border-radius:12px;padding:12px;color:#fff;width:100%;text-align:center}
.btn{border-radius:12px;font-weight:900;padding:14px;width:100%}
.log{background:#040712;border-radius:12px;padding:8px;height:300px;overflow:auto;color:#2df28b;font-family:monospace;font-size:11px}
.scan-card{background:#131a2e;border:1px solid #2df28b44;border-radius:10px;padding:8px;margin-top:6px;font-size:11px}
</style>
</head><body class="p-3 max-w-[400px] mx-auto">
<div class="text-center font-black text-[13px] tracking-widest mt-1">TITAN V28 SMART SCANNER</div>
<div id="big" class="big">8</div>
<div id="tick" class="text-center text-[#2df28b] text-xs font-mono">TICK -- via R_10</div>
<div id="grid" class="grid grid-cols-5 gap-2 mt-2"></div>
<div class="text-center text-[11px] font-mono mt-2">History:<span id="hLen">0</span> | PREDICT:<span id="pred" class="text-[#2df28b]">-</span> | CONF:<span id="conf">0%</span></div>
<div class="flex justify-center gap-3 text-[10px] font-mono"><span class="text-[#2df28b]">🔥 HOT:<span id="hotTxt">-</span></span><span class="text-red-400">❄️ COLD:<span id="coldTxt">-</span></span></div>

<div id="scanner" class="scan-card">
<div class="font-bold text-[#2df28b] text-[11px]">🧠 SCANNER STATUS: <span id="scanStatus">IDLE</span></div>
<div id="scanDetails" class="text-[10px] mt-1 text-gray-300">Waiting for 20 ticks to scan...</div>
<div id="bestMarket" class="mt-1 font-black text-xs"></div>
</div>

<div id="status" class="text-center text-[10px] text-gray-400 mt-2">Loading saved token...</div>
<input id="pat" type="password" class="inp mt-2" placeholder="pat_...">
<button onclick="toggle()" class="btn mt-2 bg-[#2df28b] text-black text-xs">👁️ Show / Hide Token</button>
<div class="grid grid-cols-2 gap-2 mt-2">
<input id="stake" type="number" class="inp text-sm" value="1" step="0.1" placeholder="Stake">
<input id="marti" type="number" class="inp text-sm" value="2.1" step="0.1" placeholder="Marti">
</div>

<button onclick="connect()" id="btnConn" class="btn mt-2 bg-[#1a203a] border text-white text-xs">🔍 LOAD & CONNECT</button>
<button onclick="smartRun()" id="btnSmart" class="btn mt-2 bg-gradient-to-r from-[#2df28b] to-[#00d4ff] text-black text-[13px]">🧠 ONE BUTTON SMART SCAN & RUN</button>
<div class="grid grid-cols-2 gap-2 mt-2">
<button onclick="stopBot()" class="btn bg-red-500 text-white text-xs py-2">⏹️ STOP</button>
<button onclick="document.getElementById('log').innerHTML=''" class="btn bg-[#1a203a] text-white text-xs py-2">🧹 CLEAR LOG</button>
</div>
<div id="bal" class="text-center text-xs font-mono mt-2">Balance:- | P:$0 W:0 L:0 | Next:$1 | HOLDING</div>
<div id="log" class="log mt-2">> V28 SMART SCANNER LOADED<br>> Will scan Even/Odd, Over/Under, Match/Diff, Touch/NoTouch<br></div>

<script>
let counts=Array(10).fill(0), history=[], ws=null, currentPat="", auto=false, curStake=1, profit=0, wins=0, losses=0, scanInterval=null;

function log(m,c="#2df28b"){ let l=document.getElementById("log"); l.innerHTML=`<div style="color:${c}">> ${m}</div>`+l.innerHTML; }
function toggle(){ let p=document.getElementById("pat"); p.type=p.type=="password"?"text":"password"; }
function loadSaved(){ let s=localStorage.getItem("titan_pat"); if(s){ document.getElementById("pat").value=s; document.getElementById("status").innerText="✅ SAVED "+s.slice(0,10)+"..."; setTimeout(()=>connect(),800);} render(); }
function render(){
  let total=history.length||1;
  let sorted=[...Array(10).keys()].map(i=>({d:i,c:counts[i],p:Math.round(counts[i]/total*100)||0})).sort((a,b)=>b.c-a.c);
  document.getElementById("hotTxt").innerText=sorted.slice(0,3).map(h=>h.d).join(" ");
  document.getElementById("coldTxt").innerText=sorted.slice(-3).map(c=>c.d).join(" ");
  document.getElementById("hLen").innerText=history.length;
  document.getElementById("pred").innerText=sorted[0]?.d??"-";
  document.getElementById("conf").innerText=(sorted[0]?.p||0)+"%";
  let g=document.getElementById("grid"); g.innerHTML="";
  for(let i=0;i<10;i++){
    let pct=history.length?Math.round(counts[i]/history.length*100):0;
    let isHot=sorted[0]?.d==i, isCold=sorted.slice(-3).some(c=>c.d==i);
    let cls=isHot?"box hot":isCold?"box cold":"box";
    g.innerHTML+=`<div class="${cls}"><div class="text-lg font-black">${i}</div><div class="text-[10px] opacity-60">${pct}%</div></div>`;
  }
  if(history.length>=5) runScanner(); // auto scan each tick
}

// CORE SMART SCANNER LOGIC
function runScanner(){
  if(history.length<20){ document.getElementById("scanStatus").innerText=`COLLECTING ${history.length}/20`; return; }
  let total=history.length;
  let even=history.filter(d=>d%2==0).length, odd=total-even;
  let evenPct=Math.round(even/total*100), oddPct=100-evenPct;
  let over4=history.filter(d=>d>4).length, under4=total-over4;
  let overPct=Math.round(over4/total*100), underPct=100-overPct;
  let over2=history.filter(d=>d>2).length, over7=history.filter(d=>d>7).length;
  let sorted=[...Array(10).keys()].map(i=>({d:i,c:counts[i],p:Math.round(counts[i]/total*100)})).sort((a,b)=>b.c-a.c);
  let top=sorted[0], second=sorted[1];

  let opportunities=[];
  // Even/Odd
  if(evenPct>=65) opportunities.push({market:"DIGITEVEN", conf:evenPct, reason:`Even ${evenPct}% (${even}/${total})`, barrier:null, type:"Even/Odd"});
  if(oddPct>=65) opportunities.push({market:"DIGITODD", conf:oddPct, reason:`Odd ${oddPct}% (${odd}/${total})`, barrier:null, type:"Even/Odd"});
  // Over/Under 4
  if(overPct>=65) opportunities.push({market:"DIGITOVER", barrier:4, conf:overPct, reason:`Over 4 ${overPct}%`, type:"Over/Under"});
  if(underPct>=65) opportunities.push({market:"DIGITUNDER", barrier:4, conf:underPct, reason:`Under 4 ${underPct}%`, type:"Over/Under"});
  // Over/Under 2 (safer)
  let over2Pct=Math.round(over2/total*100);
  if(over2Pct>=75) opportunities.push({market:"DIGITOVER", barrier:2, conf:over2Pct, reason:`Over 2 ${over2Pct}% VERY STRONG`, type:"Over/Under"});
  // Match/Diff - if one digit dominates
  if(top.p>=28) opportunities.push({market:"DIGITMATCH", barrier:top.d, conf:top.p+20, reason:`Digit ${top.d} HOT ${top.p}% - MATCH`, type:"Matches/Differs"});
  if(top.p<=5 && sorted[9].p<=5) opportunities.push({market:"DIGITDIFF", barrier:sorted[9].d, conf:70, reason:`Digit ${sorted[9].d} COLD - DIFFERS`, type:"Matches/Differs"});
  // Touch/NoTouch logic (using hot prediction)
  if(top.p>=35) opportunities.push({market:"DIGITMATCH", barrier:top.d, conf:top.p+10, reason:`Touch ${top.d} high prob`, type:"Touch/NoTouch"});

  opportunities.sort((a,b)=>b.conf-a.conf);
  let best=opportunities[0];

  let details=`Even:${evenPct}% Odd:${oddPct}% | Over4:${overPct}% Under4:${underPct}% | Top:${top.d} ${top.p}%`;
  document.getElementById("scanDetails").innerText=details;

  if(best && best.conf>=60){
    document.getElementById("scanStatus").innerText="✅ FAVOURABLE FOUND";
    document.getElementById("scanStatus").style.color="#2df28b";
    document.getElementById("bestMarket").innerHTML=`🎯 <span class="text-[#2df28b]">${best.type}</span> → ${best.market} ${best.barrier!==null?best.barrier:''} (${best.conf}%)<br><span class="text-[10px] text-gray-400">${best.reason}</span>`;
    document.getElementById("bestMarket").dataset.trade=JSON.stringify(best);
    return best;
  }else{
    document.getElementById("scanStatus").innerText="⏸️ HOLDING - No edge";
    document.getElementById("scanStatus").style.color="#f59e0b";
    document.getElementById("bestMarket").innerText="HOLD - Waiting for 60%+ edge (scanning...)";
    document.getElementById("bestMarket").dataset.trade="";
    return null;
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
  ws.onopen=()=>{ document.getElementById("status").innerText=`🟢 ${acc.account_id} CONNECTED`; log(`CONNECTED ${acc.account_id} $${acc.balance}`,"#22c55e"); ws.send(JSON.stringify({ticks:"R_10", subscribe:1})); ws.send(JSON.stringify({balance:1, subscribe:1})); document.getElementById("btnConn").innerText=`✅ ${acc.account_id}`; };
  ws.onmessage=(e)=>{
    let d=JSON.parse(e.data);
    if(d.tick){ let last=parseInt(String(d.tick.quote).slice(-1)); document.getElementById("big").innerText=last; document.getElementById("tick").innerText=`TICK ${d.tick.quote} LAST:${last} via R_10`; history.unshift(last); if(history.length>100) history.pop(); counts[last]++; render(); if(auto) log(`TICK ${d.tick.quote} LAST:${last} | SCAN:${document.getElementById("scanStatus").innerText}`); else log(`TICK ${d.tick.quote} LAST:${last} | PRED:${document.getElementById("pred").innerText} ${document.getElementById("conf").innerText}`); }
    if(d.balance){ document.getElementById("bal").innerText=`Bal:$${d.balance.balance} | P:$${profit.toFixed(2)} W:${wins} L:${losses} Next:$${curStake} | ${auto?"AUTO":"HOLD"}`; }
    if(d.proposal && auto){ log(`PROP ${d.proposal.id} $${curStake} waiting buy`,"#facc15"); ws.send(JSON.stringify({buy:d.proposal.id, price:curStake})); }
    if(d.proposal_open_contract && d.proposal_open_contract.is_sold){
      let pl=parseFloat(d.proposal_open_contract.profit); profit+=pl;
      if(pl>0){ wins++; curStake=parseFloat(document.getElementById("stake").value); log(`✅ WIN $${pl.toFixed(2)} P:$${profit.toFixed(2)}`,"#2df28b"); }
      else { losses++; curStake=(curStake*parseFloat(document.getElementById("marti").value)).toFixed(2); log(`❌ LOSS $${pl.toFixed(2)} Next:$${curStake}`,"#ef4444"); }
      if(auto) setTimeout(()=>smartTrade(),2500);
    }
    if(d.error){ log(`❌ ${d.error.message}`,"#ef4444"); }
  };
}

function smartTrade(){
  let best=runScanner();
  if(!best){ log("⏸️ HOLD - No 60%+ edge found, waiting...","#f59e0b"); document.getElementById("bal").innerText=`Bal:- | P:$${profit.toFixed(2)} W:${wins} L:${losses} Next:$${curStake} | ⏸️ HOLDING`; if(auto) setTimeout(()=>smartTrade(),3000); return; }
  let base={proposal:1, amount:parseFloat(curStake), basis:"stake", contract_type:best.market, currency:"USD", duration:1, duration_unit:"t", underlying_symbol:"R_10"};
  if(best.barrier!==null) base.barrier=best.barrier;
  log(`🎯 SMART TRADE → ${best.type}: ${best.market} ${best.barrier??''} $${curStake} CONF:${best.conf}% | ${best.reason}`,"#00d4ff");
  ws.send(JSON.stringify(base));
}

function smartRun(){
  if(!ws){ alert("Connect first"); return; }
  auto=true; curStake=parseFloat(document.getElementById("stake").value);
  document.getElementById("btnSmart").innerText="🧠 SCANNING & TRADING...";
  log("🧠 SMART SCANNER STARTED - Scanning Even/Odd, Over/Under, Match/Diff, Touch/NoTouch","#00d4ff");
  smartTrade();
  // auto re-scan every 5 sec
  if(scanInterval) clearInterval(scanInterval);
  scanInterval=setInterval(()=>{ if(auto) runScanner(); },5000);
}
function stopBot(){ auto=false; if(scanInterval) clearInterval(scanInterval); document.getElementById("btnSmart").innerText="🧠 ONE BUTTON SMART SCAN & RUN"; log("⏹️ STOPPED","#ef4444"); document.getElementById("scanStatus").innerText="STOPPED"; }
window.onload=loadSaved;
</script></body></html>
""", mimetype="text/html")
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
