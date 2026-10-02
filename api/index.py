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
<title>TITAN V22 DIGITS</title><script src="https://cdn.tailwindcss.com"></script>
<style>body{background:#070b18;color:#e2e8f0;font-family:Arial}.card{background:#0f172a;border:1px solid #1e293b;border-radius:14px}.inp{background:#000;color:#fff;border:1px solid #334155;border-radius:8px;padding:10px;width:100%}.btn{border-radius:10px;font-weight:900;padding:12px}.log{background:#020617;border:1px solid #1e293b;border-radius:10px;padding:8px;height:130px;overflow:auto;font-size:11px}
.digit-box{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:18px;border:1px solid #334155}
.digit-last{font-size:52px;font-weight:900;text-align:center;line-height:1}
</style>
</head><body class="p-2 max-w-md mx-auto">
<div class="text-center py-1"><div class="text-2xl font-black text-green-400">🔥 TITAN V22</div><div class="text-[9px]">DIGITS VISION + SAVED TOKEN ✅</div></div>

<div class="card p-3">
<div id="status" class="p-2 rounded bg-black border text-xs">Loading saved...</div>
<input id="pat" type="password" class="inp mt-2" placeholder="pat_...">
<div class="flex items-center gap-2 mt-1"><input type="checkbox" id="remember" checked><label class="text-[10px]">Remember token</label><button onclick="localStorage.clear();location.reload()" class="ml-auto text-[10px] text-red-400">CLEAR</button></div>
<button onclick="loadAccounts()" id="btn1" class="btn w-full mt-2 bg-blue-500 text-black text-sm">🔍 LOAD ACCOUNTS</button>
<select id="accSelect" class="inp hidden mt-2" style="border:2px solid #22c55e"></select>
<button onclick="connectSelected()" id="btn2" class="btn w-full mt-2 bg-green-500 text-black hidden text-sm">🔌 CONNECT SELECTED</button>

<!-- DIGITS VISION -->
<div class="card p-2 mt-3 bg-[#020617]">
<div class="flex justify-between items-center">
<div><div class="text-[10px] text-gray-400">LAST DIGIT</div><div id="lastDigitBig" class="digit-last text-green-400">-</div><div id="price" class="text-[10px] text-center">R_10: -</div></div>
<div class="text-right"><div class="text-[10px]">STATS (Last 100)</div><div id="evenPct" class="text-xs">Even: 0% | Odd: 0%</div><div id="overUnder" class="text-xs">Over 4: 0% | Under 4: 0%</div><div id="digitCount" class="text-[9px] text-gray-400 mt-1"></div></div>
</div>
<div id="digitsHistory" class="flex gap-1 mt-2 flex-wrap"></div>
</div>

<div class="grid grid-cols-2 gap-2 mt-2">
<div><label class="text-[10px]">Market</label><select id="market" class="inp" onchange="changeMarket()"><option>R_10</option><option>R_25</option><option>R_50</option><option>R_75</option><option>R_100</option><option>R_10 - 1s</option></select></div>
<div><label class="text-[10px]">Type</label><select id="ctype" class="inp"><option value="DIGITOVER">Over</option><option value="DIGITUNDER">Under</option><option value="DIGITMATCH">Matches</option><option value="DIGITDIFF">Differs</option><option value="DIGITEVEN">Even</option><option value="DIGITODD">Odd</option></select></div>
</div>
<div class="grid grid-cols-3 gap-2 mt-2">
<div><label class="text-[10px]">Digit (0-9)</label><input id="digit" type="number" class="inp text-center font-bold" value="5"></div>
<div><label class="text-[10px]">Stake $</label><input id="stake" type="number" class="inp" value="1" step="0.1"></div>
<div><label class="text-[10px]">Marti x</label><input id="marti" type="number" class="inp" value="2.1" step="0.1"></div>
</div>
<div class="grid grid-cols-2 gap-2 mt-3">
<button onclick="startBot()" id="startBtn" class="btn bg-green-500 text-black">▶️ START BOT</button>
<button onclick="stopBot()" class="btn bg-red-500 text-white">⏹️ STOP</button>
</div>
<div id="bal" class="mt-2 text-sm font-bold">Balance: -</div>
<div class="grid grid-cols-4 text-[10px] text-center mt-1"><div>P: <span id="profit" class="font-bold">$0</span></div><div>W: <span id="wins">0</span></div><div>L: <span id="loss">0</span></div><div>Next: $<span id="nextStake">1</span></div></div>
<div id="log" class="log mt-2">Ready</div>
</div>

<script>
let ws=null, allAccs=[], currentPat="", autoRunning=false, curStake=1, profit=0, wins=0, losses=0, digitHistory=[], digitCounts=Array(10).fill(0);

function log(m){let l=document.getElementById("log"); l.innerHTML=`${new Date().toLocaleTimeString()} ${m}<br>`+l.innerHTML;}
function saveToken(p){ if(document.getElementById("remember").checked) localStorage.setItem("titan_pat",p); }
function loadSaved(){ let s=localStorage.getItem("titan_pat"); if(s){ document.getElementById("pat").value=s; document.getElementById("status").innerText=`✅ SAVED ${s.slice(0,8)}...`; setTimeout(()=>loadAccounts(),400);} else document.getElementById("status").innerText="OFFLINE - Paste PAT";}

async function loadAccounts(){
 let pat=document.getElementById("pat").value.trim(); if(!pat.startsWith("pat_")){alert("pat_ required");return;}
 currentPat=pat; saveToken(pat); document.getElementById("btn1").innerText="⏳...";
 let r=await fetch("/api/deriv-auth",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pat})});
 let j=await r.json(); if(j.error){log("❌ "+j.error);return;}
 allAccs=j.accounts; let sel=document.getElementById("accSelect"); sel.innerHTML=""; sel.classList.remove("hidden");
 allAccs.forEach(a=>{
   let o=document.createElement("option"); o.value=a.account_id;
   let isDemo = parseFloat(a.balance)==10000 || a.group=="demo" || a.account_id.includes("DOT");
   let label = isDemo? `DEMO ${a.account_id} $${a.balance}` : `REAL ${a.account_id} $${a.balance}`;
   o.text=label; sel.appendChild(o);
 });
 let last=localStorage.getItem("titan_acc"); if(last) sel.value=last;
 document.getElementById("btn2").classList.remove("hidden"); document.getElementById("status").innerText=`FOUND ${allAccs.length} ACCOUNTS (Saved ✅)`; log(`✅ Found ${allAccs.length}`); document.getElementById("btn1").innerText="🔄 RELOAD";
}

async function connectSelected(){
 let accId=document.getElementById("accSelect").value; localStorage.setItem("titan_acc",accId);
 let r=await fetch("/api/deriv-otp",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pat:currentPat, account_id:accId})});
 let j=await r.json(); if(j.error){alert(j.error);return;}
 ws=new WebSocket(j.ws_url);
 ws.onopen=()=>{document.getElementById("status").innerText=`🟢 ${accId} CONNECTED`; digitHistory=[]; digitCounts=Array(10).fill(0); ws.send(JSON.stringify({ticks:document.getElementById("market").value, subscribe:1})); ws.send(JSON.stringify({balance:1, subscribe:1})); log("🟢 Connected - Watching digits"); document.getElementById("btn2").innerText="✅ CONNECTED";};
 ws.onmessage=(e)=>{let d=JSON.parse(e.data); if(d.tick){ let price=d.tick.quote; document.getElementById("price").innerText=`${d.tick.symbol}: ${price}`; let lastD=parseInt(String(price).slice(-1)); updateDigits(lastD); } if(d.balance){document.getElementById("bal").innerText=`$${d.balance.balance} - ${document.getElementById("accSelect").value}`;} if(d.proposal && autoRunning){ ws.send(JSON.stringify({buy:d.proposal.id, price:curStake})); } if(d.proposal_open_contract && d.proposal_open_contract.is_sold){ let pl=parseFloat(d.proposal_open_contract.profit); profit+=pl; if(pl>0){wins++; curStake=parseFloat(document.getElementById("stake").value);} else {losses++; curStake=(curStake*parseFloat(document.getElementById("marti").value)).toFixed(2);} document.getElementById("profit").innerText=`$${profit.toFixed(2)}`; document.getElementById("wins").innerText=wins; document.getElementById("loss").innerText=losses; document.getElementById("nextStake").innerText=curStake; log(`${pl>0?"✅ WIN":"❌ LOSS"} $${pl} D:${digitHistory[0]||"-"} Next $${curStake}`); if(autoRunning) setTimeout(()=>placeTrade(),1100);} if(d.error) log("❌ "+d.error.message); };
}

function updateDigits(d){
 document.getElementById("lastDigitBig").innerText=d;
 digitHistory.unshift(d); if(digitHistory.length>40) digitHistory.pop();
 digitCounts[d]++;
 let total=digitHistory.length; let evens=digitHistory.filter(x=>x%2==0).length; let over4=digitHistory.filter(x=>x>4).length;
 document.getElementById("evenPct").innerText=`Even: ${total?Math.round(evens/total*100):0}% | Odd: ${total?100-Math.round(evens/total*100):0}%`;
 document.getElementById("overUnder").innerText=`Over 4: ${total?Math.round(over4/total*100):0}% | Under: ${total?100-Math.round(over4/total*100):0}%`;
 document.getElementById("digitCount").innerText=digitCounts.map((c,i)=>`${i}:${c}`).join(" ");
 let h=document.getElementById("digitsHistory"); h.innerHTML="";
 digitHistory.slice(0,20).forEach((dig,idx)=>{
   let col = dig%2==0? "#22c55e" : "#eab308";
   if(idx==0) col="#22c55e"; // last
   let isWin = false;
   h.innerHTML+=`<div class="digit-box" style="background:${idx==0?'#22c55e': '#111827'};color:${idx==0?'#000':col};${idx==0?'transform:scale(1.15)':''}">${dig}</div>`;
 });
}

function placeTrade(){ if(!ws||ws.readyState!=1) return; let c=document.getElementById("ctype").value, dig=parseInt(document.getElementById("digit").value), mkt=document.getElementById("market").value; let p={proposal:1, amount:curStake, basis:"stake", contract_type:c, currency:"USD", duration:1, duration_unit:"t", symbol:mkt}; if(["DIGITOVER","DIGITUNDER","DIGITMATCH","DIGITDIFF"].includes(c)) p.barrier=dig; log(`➡️ ${c} ${dig} $${curStake} D:${digitHistory[0]}`); ws.send(JSON.stringify(p));}
function startBot(){ if(!ws){alert("Connect");return;} autoRunning=true; curStake=parseFloat(document.getElementById("stake").value); document.getElementById("startBtn").innerText="🤖 RUNNING"; log("▶️ STARTED"); placeTrade(); }
function stopBot(){ autoRunning=false; document.getElementById("startBtn").innerText="▶️ START BOT"; log("⏹️ STOPPED"); }
function changeMarket(){ if(ws){ ws.send(JSON.stringify({forget_all:"ticks"})); ws.send(JSON.stringify({ticks:document.getElementById("market").value, subscribe:1})); digitHistory=[]; document.getElementById("digitsHistory").innerHTML=""; log(`📈 Switched to ${document.getElementById("market").value}`);} }

window.onload=loadSaved;
</script></body></html>
""", mimetype="text/html")

if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
