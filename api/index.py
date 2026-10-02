import os, requests
from flask import Flask, request, Response, jsonify
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN","")
DERIV_APP_ID = os.environ.get("DERIV_APP_ID","34xM40w3JyILr0iqbYGhh")
app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
DERIV_REST = "https://api.derivws.com"

@app.route("/api/deriv-auth", methods=["POST","OPTIONS"])
def deriv_auth():
    if request.method=="OPTIONS":
        return Response("", status=200, headers={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"*","Access-Control-Allow-Methods":"POST, OPTIONS"})
    try:
        body = request.get_json(force=True, silent=True) or {}
        pat = str(body.get("pat","")).strip()
        if not pat.startswith("pat_"): return jsonify({"error":"pat_ required"}),400
        headers = {"Authorization": f"Bearer {pat}", "Deriv-App-ID": DERIV_APP_ID, "Accept":"application/json"}
        r = requests.get(f"{DERIV_REST}/trading/v1/options/accounts", headers=headers, timeout=20)
        if r.status_code!=200:
            try: err=r.json()
            except: err=r.text[:400]
            return jsonify({"error": f"accounts {r.status_code}: {err}"}),400
        accs = r.json().get("data",[])
        if not accs: return jsonify({"error":"No accounts"}),400
        # Return ALL accounts - don't auto-pick
        return jsonify({"ok":True,"accounts":accs})
    except Exception as e:
        return jsonify({"error": str(e)}),500

@app.route("/api/deriv-otp", methods=["POST","OPTIONS"])
def deriv_otp():
    if request.method=="OPTIONS":
        return Response("", status=200, headers={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"*","Access-Control-Allow-Methods":"POST, OPTIONS"})
    try:
        body = request.get_json(force=True) or {}
        pat = body.get("pat","")
        account_id = body.get("account_id","")
        headers = {"Authorization": f"Bearer {pat}", "Deriv-App-ID": DERIV_APP_ID, "Accept":"application/json"}
        r = requests.post(f"{DERIV_REST}/trading/v1/options/accounts/{account_id}/otp", headers=headers, timeout=20)
        if r.status_code!=200:
            try: err=r.json()
            except: err=r.text[:400]
            return jsonify({"error": f"OTP {r.status_code}: {err}"}),400
        ws_url = r.json().get("data",{}).get("url")
        return jsonify({"ok":True,"ws_url":ws_url})
    except Exception as e:
        return jsonify({"error": str(e)}),500

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
<title>TITAN V19 - ALL ACCOUNTS</title><script src="https://cdn.tailwindcss.com"></script>
<style>body{background:#070b18;color:#e2e8f0;font-family:Arial}.card{background:#0d1324;border:1px solid #1e293b;border-radius:14px}input,select{background:#000;color:#fff;border:2px solid #22c55e;border-radius:8px;padding:12px;width:100%;margin-top:8px}.log{background:#020617;border:1px solid #1e293b;border-radius:10px;padding:12px;min-height:120px;max-height:220px;overflow:auto;font-size:11px}</style>
</head><body class="p-3 max-w-md mx-auto">
<div class="text-center py-3"><div class="text-2xl font-black text-green-400">🔥 TITAN V19</div><div class="text-[10px]">App: 34xM40w3JyILr0iqbYGhh - ALL ACCOUNTS</div></div>
<div class="card p-4">
<div id="status" class="p-2 rounded bg-black border text-xs">OFFLINE - Paste PAT</div>
<input id="pat" type="password" placeholder="Paste pat_...">
<button onclick="loadAccounts()" id="btn1" class="w-full mt-2 bg-blue-500 text-black font-black py-3 rounded-xl">🔍 LOAD MY ACCOUNTS</button>
<select id="accSelect" class="hidden"></select>
<button onclick="connectSelected()" id="btn2" class="w-full mt-2 bg-green-500 text-black font-black py-4 rounded-xl hidden">🔌 CONNECT SELECTED</button>
<div id="bal" class="mt-2 text-sm font-bold">Balance: -</div>
<div id="price" class="text-green-400 font-bold text-center text-lg">R_10: -</div>
<div id="log" class="log mt-2">Paste PAT and click LOAD</div>
</div>
<script>
let allAccs=[], currentPat="";
async function loadAccounts(){
 let pat=document.getElementById("pat").value.trim();
 if(!pat.startsWith("pat_")){alert("pat_ required");return;}
 currentPat=pat;
 document.getElementById("btn1").innerText="⏳ LOADING...";
 document.getElementById("log").innerHTML="🔍 Loading all accounts...<br>";
 try{
  let r=await fetch("/api/deriv-auth",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pat})});
  let j=await r.json();
  if(j.error){document.getElementById("log").innerHTML="❌ "+j.error; alert(j.error); return;}
  allAccs=j.accounts;
  let sel=document.getElementById("accSelect"); sel.innerHTML=""; sel.classList.remove("hidden");
  allAccs.forEach((a,i)=>{
    let opt=document.createElement("option"); opt.value=a.account_id;
    let type=a.group=="demo"?"DEMO":a.group=="real"?"REAL":"";
    opt.text=`${type} - ${a.account_id} - $${a.balance} ${a.currency} - ${a.type||""}`;
    sel.appendChild(opt);
  });
  document.getElementById("btn2").classList.remove("hidden");
  document.getElementById("status").innerText=`✅ FOUND ${allAccs.length} ACCOUNTS`;
  document.getElementById("log").innerHTML=`✅ Found ${allAccs.length} accounts. Select one and CONNECT<br>`+document.getElementById("log").innerHTML;
  document.getElementById("btn1").innerText="🔄 RELOAD";
 }catch(e){alert(e.message);}
}
async function connectSelected(){
 let accId=document.getElementById("accSelect").value;
 let acc=allAccs.find(a=>a.account_id==accId);
 document.getElementById("log").innerHTML=`🔐 Getting OTP for ${accId}...<br>`+document.getElementById("log").innerHTML;
 document.getElementById("btn2").innerText="⏳ CONNECTING...";
 try{
  let r=await fetch("/api/deriv-otp",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pat:currentPat, account_id:accId})});
  let j=await r.json(); if(j.error){alert(j.error); return;}
  document.getElementById("bal").innerText=`$${acc.balance} ${acc.currency} - ${acc.account_id} (${acc.group})`;
  document.getElementById("log").innerHTML=`✅ OTP ok for ${accId}<br>`+document.getElementById("log").innerHTML;
  let ws=new WebSocket(j.ws_url);
  ws.onopen=()=>{document.getElementById("status").innerText=`🟢 CONNECTED TO ${accId}`; document.getElementById("status").style.color="#22c55e"; ws.send(JSON.stringify({ticks:"R_10",subscribe:1})); document.getElementById("btn2").innerText="✅ CONNECTED";};
  ws.onmessage=(e)=>{let d=JSON.parse(e.data); if(d.tick){document.getElementById("price").innerText=`R_10: ${d.tick.quote}`;}};
 }catch(e){alert(e.message);}
}
</script></body></html>
""", mimetype="text/html")

if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
