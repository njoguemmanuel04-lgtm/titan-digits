import os, requests
from flask import Flask, request, Response, jsonify
import telebot
BOT_TOKEN=os.environ.get("BOT_TOKEN",""); DERIV_APP_ID=os.environ.get("DERIV_APP_ID","34xM40w3JyILr0iqbYGhh")
app=Flask(__name__); bot=telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
DERIV_REST="https://api.derivws.com"

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

@app.route('/telegram', methods=["POST"])
def tg():
    if bot:
        try: bot.process_new_updates([telebot.types.Update.de_json(request.get_json(force=True))])
        except: pass
    return jsonify({"ok":True})

@app.route('/', methods=["GET"])
def home():
    return Response("""
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TITAN V21 SAVED</title><script src="https://cdn.tailwindcss.com"></script>
<style>body{background:#070b18;color:#e2e8f0;font-family:Arial}.card{background:#0f172a;border:1px solid #1e293b;border-radius:14px}.inp{background:#000;color:#fff;border:1px solid #334155;border-radius:8px;padding:10px;width:100%}.btn{border-radius:10px;font-weight:900;padding:14px}.log{background:#020617;border:1px solid #1e293b;border-radius:10px;padding:10px;height:150px;overflow:auto;font-size:11px}</style>
</head><body class="p-2 max-w-md mx-auto">
<div class="text-center py-2"><div class="text-2xl font-black text-green-400">🔥 TITAN V21</div><div class="text-[9px]">App: 34xM40w3JyILr0iqbYGhh - SAVED TOKEN ✅</div></div>
<div class="card p-3">
<div id="status" class="p-2 rounded bg-black border text-xs">LOADING SAVED TOKEN...</div>
<input id="pat" type="password" class="inp mt-2" placeholder="Paste pat_...">
<div class="flex items-center gap-2 mt-2"><input type="checkbox" id="remember" checked><label class="text-xs">Remember token (save on this phone)</label><button onclick="clearToken()" class="ml-auto text-[10px] text-red-400">CLEAR</button></div>
<button onclick="loadAccounts()" id="btn1" class="btn w-full mt-2 bg-blue-500 text-black">🔍 LOAD MY ACCOUNTS</button>
<select id="accSelect" class="inp hidden mt-2" style="border:2px solid #22c55e"></select>
<button onclick="connectSelected()" id="btn2" class="btn w-full mt-2 bg-green-500 text-black hidden">🔌 CONNECT</button>

<div class="grid grid-cols-2 gap-2 mt-3">
<div><label class="text-[10px]">Market</label><select id="market" class="inp"><option>R_10</option><option>R_25</option><option>R_50</option><option>R_75</option><option>R_100</option></select></div>
<div><label class="text-[10px]">Type</label><select id="ctype" class="inp"><option value="DIGITOVER">Over</option><option value="DIGITUNDER">Under</option><option value="DIGITMATCH">Match</option><option value="DIGITDIFF">Differs</option><option value="DIGITEVEN">Even</option><option value="DIGITODD">Odd</option></select></div>
</div>
<div class="grid grid-cols-3 gap-2 mt-2">
<div><label class="text-[10px]">Digit</label><input id="digit" type="number" class="inp" value="5"></div>
<div><label class="text-[10px]">Stake $</label><input id="stake" type="number" class="inp" value="1" step="0.5"></div>
<div><label class="text-[10px]">Martingale</label><input id="marti" type="number" class="inp" value="2.1"></div>
</div>
<div class="grid grid-cols-2 gap-2 mt-3">
<button onclick="startBot()" id="startBtn" class="btn bg-green-500 text-black">▶️ START</button>
<button onclick="stopBot()" class="btn bg-red-500 text-white">⏹️ STOP</button>
</div>

<div id="bal" class="mt-2 text-sm font-bold">Balance: -</div>
<div id="price" class="text-green-400 font-bold text-center">R_10: -</div>
<div class="grid grid-cols-3 text-[10px] text-center"><div>P: <span id="profit">$0</span></div><div>W: <span id="wins">0</span></div><div>L: <span id="loss">0</span></div></div>
<div id="log" class="log mt-2">Checking saved token...</div>
</div>

<script>
let ws=null, allAccs=[], currentPat="", selectedAcc=null, autoRunning=false, curStake=1, profit=0, wins=0, losses=0, lastDigit=-1;

function log(m){let l=document.getElementById("log"); l.innerHTML=`${new Date().toLocaleTimeString()} ${m}<br>`+l.innerHTML;}
function saveToken(p){ if(document.getElementById("remember").checked){ localStorage.setItem("titan_pat",p); log("💾 Token saved"); } }
function clearToken(){ localStorage.removeItem("titan_pat"); document.getElementById("pat").value=""; log("🗑️ Token cleared"); alert("Cleared"); }
function loadSaved(){
 let saved=localStorage.getItem("titan_pat");
 if(saved){ document.getElementById("pat").value=saved; document.getElementById("status").innerText=`✅ SAVED TOKEN FOUND (${saved.slice(0,8)}...)`; log(`✅ Loaded saved token ${saved.slice(0,10)}...`); currentPat=saved; setTimeout(()=>loadAccounts(),500); }
 else { document.getElementById("status").innerText="OFFLINE - Paste PAT"; log("No saved token - Paste new"); }
}

async function loadAccounts(){
 let pat=document.getElementById("pat").value.trim(); if(!pat.startsWith("pat_")){alert("pat_ required");return;}
 currentPat=pat; saveToken(pat); document.getElementById("btn1").innerText="⏳...";
 try{
  let r=await fetch("/api/deriv-auth",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pat})});
  let j=await r.json(); if(j.error){log("❌ "+j.error);return;}
  allAccs=j.accounts; let sel=document.getElementById("accSelect"); sel.innerHTML=""; sel.classList.remove("hidden");
  allAccs.forEach(a=>{let o=document.createElement("option"); o.value=a.account_id; let t=a.group=="demo"?"DEMO":"REAL"; o.text=`${t} ${a.account_id} $${a.balance}`; sel.appendChild(o);});
  // restore last account
  let lastAcc=localStorage.getItem("titan_acc"); if(lastAcc) sel.value=lastAcc;
  document.getElementById("btn2").classList.remove("hidden"); document.getElementById("status").innerText=`FOUND ${allAccs.length} ACCOUNTS (Saved ✅)`; log(`✅ Found ${allAccs.length} - Token saved!`); document.getElementById("btn1").innerText="🔄 RELOAD";
 }catch(e){log("❌ "+e.message);}
}

async function connectSelected(){
 let accId=document.getElementById("accSelect").value; localStorage.setItem("titan_acc",accId); selectedAcc=allAccs.find(a=>a.account_id==accId);
 let r=await fetch("/api/deriv-otp",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pat:currentPat, account_id:accId})});
 let j=await r.json(); if(j.error){alert(j.error);return;}
 ws=new WebSocket(j.ws_url);
 ws.onopen=()=>{document.getElementById("status").innerText=`🟢 ${accId} CONNECTED (Saved)`; ws.send(JSON.stringify({ticks:document.getElementById("market").value, subscribe:1})); ws.send(JSON.stringify({balance:1, subscribe:1})); log("🟢 Connected"); document.getElementById("btn2").innerText="✅ CONNECTED";};
 ws.onmessage=(e)=>{let d=JSON.parse(e.data); if(d.tick){document.getElementById("price").innerText=`${d.tick.symbol}: ${d.tick.quote}`; lastDigit=parseInt(String(d.tick.quote).slice(-1));} if(d.balance){document.getElementById("bal").innerText=`$${d.balance.balance} - ${accId}`;} if(d.proposal){if(autoRunning) ws.send(JSON.stringify({buy:d.proposal.id, price:curStake}));} if(d.proposal_open_contract && d.proposal_open_contract.is_sold){ let pl=parseFloat(d.proposal_open_contract.profit); profit+=pl; if(pl>0){wins++; curStake=parseFloat(document.getElementById("stake").value);} else {losses++; curStake=(curStake*parseFloat(document.getElementById("marti").value)).toFixed(2);} document.getElementById("profit").innerText=`$${profit.toFixed(2)}`; document.getElementById("wins").innerText=wins; document.getElementById("loss").innerText=losses; log(`${pl>0?"✅ WIN":"❌ LOSS"} $${pl} Next $${curStake}`); if(autoRunning) setTimeout(()=>placeTrade(),1000);} };
}

function placeTrade(){ if(!ws||ws.readyState!=1) return; let ctype=document.getElementById("ctype").value, dig=parseInt(document.getElementById("digit").value), market=document.getElementById("market").value; let p={proposal:1, amount:curStake, basis:"stake", contract_type:ctype, currency:"USD", duration:1, duration_unit:"t", symbol:market}; if(["DIGITOVER","DIGITUNDER","DIGITMATCH","DIGITDIFF"].includes(ctype)) p.barrier=dig; log(`➡️ ${ctype} ${dig} $${curStake}`); ws.send(JSON.stringify(p));}
function startBot(){ if(!ws){alert("Connect first");return;} autoRunning=true; curStake=parseFloat(document.getElementById("stake").value); log("▶️ STARTED"); placeTrade(); }
function stopBot(){ autoRunning=false; log("⏹️ STOPPED"); }

window.onload=loadSaved;
</script></body></html>
""", mimetype="text/html")

if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
