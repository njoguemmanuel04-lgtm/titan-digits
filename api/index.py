import os, requests
from flask import Flask, request, Response, jsonify
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN","")
DERIV_APP_ID = os.environ.get("DERIV_APP_ID","34xM40w3JyILr0iqbYGhh")
app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
DERIV_REST = "https://api.derivws.com" # FIXED - was api.deriv.com

@app.route("/api/deriv-auth", methods=["POST","OPTIONS"])
def deriv_auth():
    if request.method=="OPTIONS":
        return Response("", status=200, headers={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"*","Access-Control-Allow-Methods":"POST, OPTIONS"})
    try:
        body = request.get_json(force=True, silent=True) or {}
        pat = str(body.get("pat","")).strip()
        if not pat: return jsonify({"error":"Paste pat_ token"}), 400
        if not pat.startswith("pat_"): return jsonify({"error":"Must start with pat_"}), 400

        headers = {"Authorization": f"Bearer {pat}", "Deriv-App-ID": DERIV_APP_ID, "Accept":"application/json"}

        # 1. GET accounts from correct host
        r = requests.get(f"{DERIV_REST}/trading/v1/options/accounts", headers=headers, timeout=20)
        if r.status_code!=200:
            # Return what Deriv actually said
            try: err = r.json()
            except: err = r.text[:400]
            return jsonify({"error": f"Deriv accounts failed {r.status_code}: {err}"}), 400

        accs = r.json().get("data",[])
        if not accs: return jsonify({"error":"No options accounts found for this PAT - create PAT with Trade scope for Titan v7"}),400
        real = [a for a in accs if a.get("group")=="real"]
        chosen = real[0] if real else accs[0]

        # 2. OTP
        r2 = requests.post(f"{DERIV_REST}/trading/v1/options/accounts/{chosen['account_id']}/otp", headers=headers, timeout=20)
        if r2.status_code!=200:
            try: err = r2.json()
            except: err = r2.text[:400]
            return jsonify({"error": f"OTP failed {r2.status_code}: {err}"}),400

        ws_url = r2.json().get("data",{}).get("url")
        if not ws_url: return jsonify({"error":"No ws_url"}),400
        return jsonify({"ok":True,"ws_url":ws_url,"account":chosen})
    except Exception as e:
        return jsonify({"error": f"Server exception: {str(e)}"}),500

@app.route('/telegram', methods=["POST"])
def tg():
    if bot:
        try: bot.process_new_updates([telebot.types.Update.de_json(request.get_json(force=True))])
        except: pass
    return jsonify({"ok":True})

@app.route('/', methods=["GET"])
def home():
    return Response("""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TITAN V18 - 34xM40w3</title><script src="https://cdn.tailwindcss.com"></script><style>body{background:#070b18;color:#e2e8f0;font-family:Arial}.card{background:#0d1324;border:1px solid #1e293b;border-radius:14px}input{background:#000;color:#fff;border:2px solid #22c55e;border-radius:8px;padding:12px;width:100%}.log{background:#020617;border:1px solid #1e293b;border-radius:10px;padding:12px;min-height:120px;max-height:220px;overflow:auto;font-size:11px}</style></head><body class="p-3 max-w-md mx-auto"><div class="text-center py-3"><div class="text-2xl font-black text-green-400">🔥 TITAN V18</div><div class="text-[10px]">App: 34xM40w3JyILr0iqbYGhh ✅ FIXED HOST</div></div><div class="card p-4"><div id="status" class="p-2 rounded bg-black border text-xs">OFFLINE - Waiting PAT</div><div class="mt-3"><input id="pat" type="password" placeholder="Paste pat_... here"><button onclick="connectPAT()" id="btn" class="w-full mt-3 bg-green-500 text-black font-black py-4 rounded-xl">🔌 CONNECT REAL MAX</button></div><div id="bal" class="mt-2 text-sm">Balance: $0</div><div id="price" class="text-green-400 font-bold text-center">-</div><div id="log" class="log mt-2">Ready. Host fixed to api.derivws.com ✅</div></div><script>
async function connectPAT(){
 let pat=document.getElementById("pat").value.trim();
 if(!pat.startsWith("pat_")){alert("pat_ required");return;}
 document.getElementById("btn").innerText="⏳ CONNECTING...";
 let log=document.getElementById("log");
 log.innerHTML="🔐 Starting PAT auth with 34xM40w3...<br>"+log.innerHTML;
 try{
  let r=await fetch("/api/deriv-auth",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({pat})});
  let text=await r.text(); let j; try{j=JSON.parse(text);}catch(e){ log.innerHTML="❌ Server returned non-JSON: "+text.slice(0,200)+"<br>"+log.innerHTML; alert("Server error: "+text.slice(0,200)); return;}
  if(j.error){ log.innerHTML="❌ "+j.error+"<br>"+log.innerHTML; alert(j.error); document.getElementById("btn").innerText="❌ "+j.error.slice(0,30); return;}
  document.getElementById("bal").innerText="$"+j.account.balance+" "+j.account.currency+" - "+j.account.account_id;
  log.innerHTML="✅ PAT ok: "+j.account.account_id+"<br>"+log.innerHTML;
  let ws=new WebSocket(j.ws_url);
  ws.onopen=()=>{document.getElementById("status").innerText="🟢 CONNECTED TO DERIV"; document.getElementById("status").style.color="#22c55e"; log.innerHTML="🟢 CONNECTED<br>"+log.innerHTML; ws.send(JSON.stringify({ticks:"R_10",subscribe:1})); document.getElementById("btn").innerText="✅ CONNECTED";};
  ws.onmessage=(e)=>{let d=JSON.parse(e.data); if(d.tick){document.getElementById("price").innerText="R_10: "+d.tick.quote;}};
  ws.onerror=()=>{log.innerHTML="❌ WS Error<br>"+log.innerHTML;};
  ws.onclose=()=>{document.getElementById("status").innerText="DISCONNECTED - click again for new OTP";};
 }catch(e){log.innerHTML="❌ "+e.message+"<br>"+log.innerHTML; alert(e.message);}
}
</script></body></html>""", mimetype="text/html")

if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
