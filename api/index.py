import os
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from http.server import BaseHTTPRequestHandler

API_BASE = "https://api.derivws.com"
DERIV_APP_ID = os.environ.get("DERIV_APP_ID", "")

def deriv_request(method, url, token):
    headers = {"Authorization": "Bearer " + token,"Deriv-App-ID": DERIV_APP_ID,"Accept": "application/json","Content-Type": "application/json"}
    req = Request(url, method=method, headers=headers)
    try:
        with urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw)
    except HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try: data = json.loads(raw)
        except: data = {"error": raw or str(e)}
        return e.code, data
    except URLError as e:
        return 503, {"error": "Could not reach Deriv API: " + str(e.reason)}
    except Exception as e:
        return 500, {"error": str(e)}

def error_message(data):
    if isinstance(data, dict):
        if data.get("error"): return str(data["error"])
        errors = data.get("errors")
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict): return first.get("message", first.get("code", "Deriv API error"))
            return str(first)
        if data.get("message"): return str(data["message"])
    return "Unknown Deriv API error"

class handler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
    def do_POST(self):
        if self.path!= "/api/deriv-auth":
            self.send_json(404, {"ok": False,"error": "Endpoint not found"}); return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 50000:
                self.send_json(400, {"ok": False,"error": "Invalid request"}); return
            raw = self.rfile.read(length).decode("utf-8")
            body = json.loads(raw)
            token = str(body.get("token", "")).strip()
            if not token:
                self.send_json(400, {"ok": False,"error": "PAT is required"}); return
            if not DERIV_APP_ID:
                self.send_json(500, {"ok": False,"error": "DERIV_APP_ID is not configured in Vercel"}); return
            status, accounts_result = deriv_request("GET", API_BASE + "/trading/v1/options/accounts", token)
            if status!= 200:
                self.send_json(status, {"ok": False,"error": error_message(accounts_result),"stage": "accounts"}); return
            accounts = accounts_result.get("data", [])
            if isinstance(accounts, dict): accounts = [accounts]
            if not isinstance(accounts, list) or not accounts:
                self.send_json(404, {"ok": False,"error": "No Options trading account found","stage": "accounts"}); return
            demo_accounts = [a for a in accounts if str(a.get("account_type", "")).lower() == "demo"]
            account = demo_accounts[0] if demo_accounts else accounts[0]
            account_id = account.get("account_id")
            if not account_id:
                self.send_json(500, {"ok": False,"error": "Deriv account ID was not returned","stage": "accounts"}); return
            otp_url = API_BASE + "/trading/v1/options/accounts/" + str(account_id) + "/otp"
            otp_status, otp_result = deriv_request("POST", otp_url, token)
            if otp_status not in (200, 201):
                self.send_json(otp_status, {"ok": False,"error": error_message(otp_result),"stage": "otp"}); return
            otp_data = otp_result.get("data", {})
            if not isinstance(otp_data, dict): otp_data = {}
            ws_url = otp_data.get("url")
            if not ws_url:
                self.send_json(500, {"ok": False,"error": "Deriv did not return an authenticated WebSocket URL","stage": "otp"}); return
            self.send_json(200, {"ok": True,"account_id": account_id,"account_type": account.get("account_type", ""),"balance": account.get("balance", 0),"currency": account.get("currency", "USD"),"ws_url": ws_url})
        except json.JSONDecodeError:
            self.send_json(400, {"ok": False,"error": "Invalid JSON request"})
        except Exception as e:
            self.send_json(500, {"ok": False,"error": str(e)})
    def do_GET(self):
        html = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>TITAN V42 FOREX FIXED</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-[#0f172a] text-white p-3"><div class="max-w-md mx-auto">
<h1 class="text-center font-black text-emerald-400">TITAN V42 FOREX FIXED</h1>
<div class="text-center text-xs text-cyan-400 mb-2">EURUSD GBPUSD USDJPY FIXED RSI | 1 MIN</div>
<div id="price" class="text-center text-4xl font-black text-emerald-400 my-2">-</div>
<div id="symbolInfo" class="text-center text-xs text-cyan-400">SELECT PAIR & CONNECT</div>
<div class="grid grid-cols-3 gap-2 my-3 text-[10px]">
<div class="bg-slate-800 rounded-xl p-2 text-center">EMA20 <b id="ema20">-</b></div>
<div class="bg-slate-800 rounded-xl p-2 text-center">EMA50 <b id="ema50">-</b></div>
<div class="bg-slate-800 rounded-xl p-2 text-center">RSI <b id="rsi">-</b></div></div>
<div class="flex justify-between text-xs bg-slate-800 p-2 rounded-xl mb-2">
<span>Ticks:<b id="histCount">0</b></span><span>CONF:<b id="conf">0</b>%</span><span id="scanStatus">WAITING</span></div>
<div class="bg-slate-800 rounded-xl p-3 mb-3 border border-emerald-500/30">
<div id="scanDetails" class="text-[11px] text-gray-300">Waiting for 60 ticks...</div>
<div id="bestMarket" class="text-sm font-bold text-yellow-400 mt-1"></div></div>
<div id="dotStatus" class="text-center text-xs mb-3 p-2 rounded-xl bg-slate-800">🔴 NOT CONNECTED</div>
<select id="forexPair" class="w-full bg-slate-900 border border-emerald-500 p-3 rounded-xl text-center text-sm mb-2 font-bold">
<option value="frxEURUSD">EUR/USD - BEST</option>
<option value="frxGBPUSD">GBP/USD - FAST</option>
<option value="frxUSDJPY">USD/JPY - STABLE</option>
<option value="frxAUDUSD">AUD/USD - TRENDY</option>
<option value="frxUSDCAD">USD/CAD - SAFE</option></select>
<input id="token" type="password" placeholder="Paste Deriv PAT here" class="w-full bg-slate-900 border border-slate-700 p-4 rounded-xl text-center text-sm mb-2">
<button onclick="connectNow()" id="connectButton" class="w-full bg-blue-600 hover:bg-blue-500 font-black py-4 rounded-xl mb-2 text-base">🔌 CONNECT FOREX</button>
<button onclick="toggleToken()" class="w-full bg-slate-700 font-bold py-2 rounded-xl mb-3 text-xs">👁️ Show / Hide Token</button>
<div class="grid grid-cols-4 gap-2 mb-3">
<div class="text-center"><div class="text-[10px] text-gray-400">STAKE</div><input id="stake" value="1" class="w-full bg-slate-800 p-2 rounded-xl text-center"></div>
<div class="text-center"><div class="text-[10px] text-gray-400">MARTIN</div><input id="martingale" value="2.05" class="w-full bg-slate-800 p-2 rounded-xl text-center"></div>
<div class="text-center"><div class="text-[10px] text-gray-400">TP $</div><input id="tp" value="10" class="w-full bg-slate-800 p-2 rounded-xl text-center border border-emerald-500"></div>
<div class="text-center"><div class="text-[10px] text-gray-400">SL $</div><input id="sl" value="20" class="w-full bg-slate-800 p-2 rounded-xl text-center border border-red-500"></div></div>
<button onclick="startTrading()" class="w-full bg-gradient-to-r from-emerald-400 to-cyan-400 text-black font-black py-4 rounded-xl mb-2">🧠 TRADE FOREX 1 MIN</button>
<div class="grid grid-cols-2 gap-2 mb-3">
<button onclick="stopTrading()" class="bg-red-600 font-bold py-3 rounded-xl">⏹️ STOP</button>
<button onclick="clearLog()" class="bg-slate-800 font-bold py-3 rounded-xl">🧹 CLEAR</button></div>
<div class="text-center text-xs bg-black/50 p-2 rounded-xl">
<span id="balance">Bal:$0.00</span> | <span id="profit" class="font-bold">P:$0.00</span> | <span id="wins">W:0</span> <span id="loss">L:0</span><br>
Next: <span id="nextStake" class="text-yellow-400">$1</span> | <span id="tradeStatus">HOLD</span></div>
<div id="log" class="bg-black/80 rounded-xl p-2 mt-3 h-72 overflow-y-auto text-[11px] font-mono border border-slate-700"></div></div>
<script>
let prices=[];let ws=null;let trading=false;let dotConnected=false;let awaitingResult=false;
let nextStake=1;let profit=0;let wins=0;let losses=0;let balance=0;let pendingBuy=false;let pendingStake=0;let contractId=null;let currentSymbol="frxEURUSD";
function logM(m){let l=document.getElementById("log");let t=new Date().toLocaleTimeString();l.innerHTML+=`[${t}] ${m}<br>`;l.scrollTop=l.scrollHeight;}
function r2(n){return Math.round(n*100)/100;}
function calcEMA(data,period){let k=2/(period+1);let ema=data[0];for(let i=1;i<data.length;i++){ema=data[i]*k+ema*(1-k);}return ema;}
function calcRSI(prices,period=14){
 if(prices.length<period+1)return 50;
 let gains=0;let losses=0;
 for(let i=1;i<=period;i++){
  let diff=prices[prices.length-i]-prices[prices.length-i-1];
  if(diff>=0)gains+=diff; else losses-=diff;
 }
 let avgGain=gains/period;let avgLoss=losses/period;
 if(avgLoss===0)return 70;
 if(avgGain===0)return 30;
 let rs=avgGain/avgLoss;
 let rsi=100-(100/(1+rs));
 return rsi;
}
function runScanner(){
 if(prices.length<60){
  document.getElementById("scanStatus").innerText=`COLLECT ${prices.length}/60`;
  document.getElementById("scanDetails").innerText=`Collecting ticks... ${prices.length}/60`;
  return null;
 }
 let ema20=calcEMA(prices.slice(-20),20);
 let ema50=calcEMA(prices.slice(-50),50);
 let rsi=calcRSI(prices,14);
 let last=prices[prices.length-1];
 let prev=prices[prices.length-2];
 let q=prices.slice(-5);
 let rise5=q[0]<=q[1]&&q[1]<=q[2]&&q[2]<=q[3]&&q[3]<q[4];
 let fall5=q[0]>=q[1]&&q[1]>=q[2]&&q[2]>=q[3]&&q[3]>q[4];
 let trendUp=ema20>ema50;
 let trendDown=ema20<ema50;
 let priceAbove=last>ema20;
 let priceBelow=last<ema20;
 document.getElementById("ema20").innerText=ema20.toFixed(5);
 document.getElementById("ema50").innerText=ema50.toFixed(5);
 document.getElementById("rsi").innerText=rsi.toFixed(1);
 document.getElementById("scanDetails").innerText=`EMA20 ${ema20>ema50?'UP':'DOWN'} ${ema20.toFixed(5)} | EMA50 ${ema50.toFixed(5)} | RSI ${rsi.toFixed(1)} | 5T ${rise5?'RISE':fall5?'FALL':'FLAT'} | Last ${last>prev?'↑':'↓'}`;
 let opps=[];
 if(trendUp&&priceAbove&&rsi>50&&rsi<75&&(rise5||last>prev)){
  let conf=80+Math.min(12,(rsi-50)*0.8);
  if(rise5)conf+=5;
  conf=Math.round(Math.min(93,conf));
  opps.push({market:"CALL",conf:conf,type:`CALL ${currentSymbol} EMA UP RSI ${rsi.toFixed(0)}`});
 }
 if(trendDown&&priceBelow&&rsi<50&&rsi>25&&(fall5||last<prev)){
  let conf=80+Math.min(12,(50-rsi)*0.8);
  if(fall5)conf+=5;
  conf=Math.round(Math.min(93,conf));
  opps.push({market:"PUT",conf:conf,type:`PUT ${currentSymbol} EMA DOWN RSI ${rsi.toFixed(0)}`});
 }
 opps.sort((a,b)=>b.conf-a.conf);let best=opps[0];
 if(best&&best.conf>=80){
  document.getElementById("scanStatus").innerText="✅ FAVOURABLE";
  document.getElementById("conf").innerText=best.conf;
  document.getElementById("bestMarket").innerText=`🎯 ${best.type} → ${best.market} ${best.conf}%`;
  document.getElementById("tradeStatus").innerText=`READY ${best.type}`;
  return best;
 }
 document.getElementById("scanStatus").innerText="⏸️ HOLD";
 document.getElementById("bestMarket").innerText="Waiting for trend - hold is normal 70% time";
 document.getElementById("tradeStatus").innerText="HOLD";
 return null;
}
async function connectNow(){
 let token=document.getElementById("token").value.trim();
 if(!token){logM("❌ PASTE TOKEN FIRST");return;}
 currentSymbol=document.getElementById("forexPair").value;
 if(ws){try{ws.close();}catch(e){}}dotConnected=false;prices=[];
 document.getElementById("connectButton").innerText="⏳ CONNECTING...";
 document.getElementById("dotStatus").innerText=`🟡 GETTING ${currentSymbol}...`;
 logM(`🔐 Connecting ${currentSymbol}...`);
 try{
  let response=await fetch("/api/deriv-auth",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token:token})});
  let raw=await response.text();let data;try{data=JSON.parse(raw);}catch(e){throw new Error("Server returned: "+raw.slice(0,150));}
  if(!response.ok||!data.ok){throw new Error(data.error||"Deriv auth failed");}
  logM(`✅ ACCOUNT ${data.account_id} ${data.balance} ${data.currency}`);
  connectAuthenticatedWS(data.ws_url);
  localStorage.setItem("deriv_token",token);localStorage.setItem("deriv_pat",token);
 }catch(e){logM("❌ AUTH ERROR: "+e.message);document.getElementById("dotStatus").innerText="🔴 NOT CONNECTED";document.getElementById("connectButton").innerText="🔌 CONNECT FOREX";}
}
function connectAuthenticatedWS(wsUrl){
 try{ws=new WebSocket(wsUrl);}catch(e){logM("❌ WS CREATE ERROR: "+e.message);return;}
 ws.onopen=function(){
  logM(`🟢 CONNECTED - ${currentSymbol} 1 MIN FOREX`);dotConnected=true;
  document.getElementById("dotStatus").innerText=`🟢 CONNECTED ${currentSymbol}`;
  document.getElementById("dotStatus").className="text-center text-xs mb-3 p-2 rounded-xl bg-emerald-900/50 border border-emerald-500";
  document.getElementById("connectButton").innerText="✅ CONNECTED";
  ws.send(JSON.stringify({balance:1,subscribe:1,req_id:1}));
  ws.send(JSON.stringify({ticks:currentSymbol,subscribe:1,req_id:2}));
  logM(`📡 ${currentSymbol} TICK STREAM STARTED`);
 };
 ws.onmessage=function(event){
  let data;try{data=JSON.parse(event.data);}catch(e){return;}
  if(data.msg_type==="balance"){if(data.balance){balance=Number(data.balance.balance);document.getElementById("balance").innerText=`Bal:$${balance.toFixed(2)}`;}}
  if(data.msg_type==="tick"){
   if(!data.tick||data.tick.symbol!==currentSymbol)return;
   let quote=Number(data.tick.quote);
   prices.push(quote);
   if(prices.length>100)prices.shift();
   document.getElementById("price").innerText=quote.toFixed(5);
   document.getElementById("symbolInfo").innerText=`LIVE ${currentSymbol} ${quote.toFixed(5)}`;
   document.getElementById("histCount").innerText=prices.length;
   let best=runScanner();
   if(best&&trading&&!awaitingResult&&!pendingBuy){doTrade(best);}
  }
  if(data.msg_type==="proposal"&&pendingBuy){if(data.proposal&&data.proposal.id){ws.send(JSON.stringify({buy:data.proposal.id,price:Number(data.proposal.ask_price),req_id:20}));}}
  if(data.msg_type==="buy"&&data.buy){pendingBuy=false;contractId=data.buy.contract_id;awaitingResult=true;logM(`📈 BOUGHT ${contractId} $${pendingStake.toFixed(2)}`);ws.send(JSON.stringify({proposal_open_contract:1,contract_id:contractId,subscribe:1,req_id:21}));}
  if(data.msg_type==="proposal_open_contract"&&data.proposal_open_contract){
   let c=data.proposal_open_contract;if(c.is_sold||c.status==="sold"){
    let p=Number(c.profit||0);profit=r2(profit+p);
    if(p>0){wins++;nextStake=r2(Number(document.getElementById("stake").value));}
    else{losses++;nextStake=r2(nextStake*Number(document.getElementById("martingale").value));}
    document.getElementById("profit").innerText=`P:$${profit.toFixed(2)}`;document.getElementById("wins").innerText=`W:${wins}`;document.getElementById("loss").innerText=`L:${losses}`;document.getElementById("nextStake").innerText=`$${nextStake.toFixed(2)}`;
    logM(p>0?`✅ WIN +$${p.toFixed(2)} Profit:$${profit.toFixed(2)}`:`❌ LOSS $${p.toFixed(2)} Profit:$${profit.toFixed(2)}`);
    let tp=Number(document.getElementById("tp").value);let sl=Number(document.getElementById("sl").value);
    if(profit>=tp){trading=false;logM(`🎯 TP $${profit.toFixed(2)} STOPPED`);}
    if(profit<=-sl){trading=false;logM(`🛑 SL $${profit.toFixed(2)} STOPPED`);}
    awaitingResult=false;contractId=null;
   }
  }
  if(data.error){logM("❌ DERIV: "+data.error.message);pendingBuy=false;awaitingResult=false;}
 };
 ws.onerror=function(){dotConnected=false;document.getElementById("dotStatus").innerText="🔴 WS ERROR";logM("❌ WS ERROR");};
 ws.onclose=function(){dotConnected=false;document.getElementById("dotStatus").innerText="🔴 CLOSED";logM("🔴 WS CLOSED");document.getElementById("connectButton").innerText="🔌 CONNECT FOREX";};
}
function doTrade(best){
 if(!dotConnected||awaitingResult||pendingBuy)return;
 let stake=r2(Number(nextStake));
 let req={proposal:1,amount:stake,basis:"stake",contract_type:best.market,currency:"USD",symbol:currentSymbol,duration:1,duration_unit:"m",req_id:10};
 pendingBuy=true;pendingStake=stake;
 logM(`🎯 ${best.type} Stake $${stake} CONF ${best.conf}%`);
 ws.send(JSON.stringify(req));
}
function startTrading(){if(!dotConnected){logM("🔌 Connect first");connectNow();return;}trading=true;logM(`🧠 V42 FOREX ${currentSymbol} 1MIN STARTED CONF>=80%`);}
function stopTrading(){trading=false;pendingBuy=false;logM("⏹️ STOPPED");}
function clearLog(){document.getElementById("log").innerHTML="";}
function toggleToken(){let t=document.getElementById("token");t.type=t.type==="password"?"text":"password";}
document.getElementById("forexPair").addEventListener("change",function(){currentSymbol=this.value;prices=[];logM(`🔄 Pair changed to ${currentSymbol} - reconnect to apply`);});
window.onload=function(){let saved=localStorage.getItem("deriv_token")||localStorage.getItem("deriv_pat");if(saved){document.getElementById("token").value=saved;logM("💾 Token loaded");}};
</script></body></html>
"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))
