import os, json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_BASE = "https://api.derivws.com"
DERIV_APP_ID = os.environ.get("DERIV_APP_ID", "1089")

HTML = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TITAN V36 - ALL MARKETS</title>
<style>
body{background:#0f172a;color:#e2e8f0;font-family:Arial;padding:10px;margin:0}
.card{background:#1e293b;border-radius:12px;padding:12px;margin:8px 0;border:1px solid #334155}
.btn{width:100%;padding:14px;border:none;border-radius:10px;font-weight:bold;font-size:16px;cursor:pointer;margin:6px 0}
.btn-blue{background:#2563eb;color:white}
.btn-green{background:linear-gradient(90deg,#10b981,#06b6d4);color:black}
.btn-red{background:#ef4444;color:white}
.btn-gray{background:#334155;color:white}
input{background:#0f172a;border:1px solid #475569;color:white;padding:12px;border-radius:8px;width:100%;box-sizing:border-box}
.grid4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px}
.stat{font-size:12px;color:#94a3b8}
#log{background:#020617;height:260px;overflow-y:auto;font-family:monospace;font-size:12px;padding:8px;border-radius:8px;border:1px solid #1e293b}
.ok{color:#10b981} .bad{color:#ef4444} .info{color:#38bdf8}
.badge{display:inline-block;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:bold}
.bg-green{background:#064e3b;color:#10b981;border:1px solid #10b981}
.bg-red{background:#450a0a;color:#ef4444;border:1px solid #ef4444}
</style>
</head>
<body>
<h2 style="text-align:center">TITAN V36 - 6 MARKETS</h2>
<div class="card" id="scanBox">
<div class="grid4" style="text-align:center">
<div><div class="stat">HISTORY</div><div id="histCount" style="font-size:20px;font-weight:bold">0</div></div>
<div><div class="stat">LAST DIGIT</div><div id="lastDigit" style="font-size:20px;font-weight:bold">-</div></div>
<div><div class="stat">TICK PRICE</div><div id="tickPrice" style="font-size:14px;font-weight:bold">-</div></div>
<div><div class="stat">CONF</div><div id="conf" style="font-size:20px;font-weight:bold">0%</div></div>
</div>
<div style="margin-top:8px;font-size:13px" id="scanDetails">Collecting 0/50...</div>
<div style="margin-top:4px;font-size:13px;font-weight:bold" id="bestMarket">-</div>
<div style="margin-top:4px"><span id="scanStatus" class="badge bg-red">COLLECTING</span> <span id="connBadge" class="badge bg-red">DISCONNECTED</span></div>
</div>
<div class="card">
<div id="connectStatus" style="text-align:center;padding:8px;border-radius:8px;background:#1e293b;border:1px solid #334155">DISCONNECTED</div>
<input type="password" id="tokenInput" placeholder="Paste Deriv API Token - will be saved" style="margin-top:8px">
<button class="btn btn-blue" onclick="connectDeriv()" id="connectBtn">CONNECT NOW</button>
<button class="btn btn-gray" style="padding:8px;font-size:12px" onclick="toggleToken()">Show / Hide Token</button>
</div>
<div class="card grid4">
<div><div class="stat">STAKE</div><input id="stake" value="1" type="number" step="0.1"></div>
<div><div class="stat">MARTIN</div><input id="martin" value="2.1" type="number" step="0.1"></div>
<div><div class="stat">TP $</div><input id="tp" value="10" type="number"></div>
<div><div class="stat">SL $</div><input id="sl" value="20" type="number"></div>
</div>
<div class="card">
<label style="font-size:12px"><input type="checkbox" id="useOverUnder" checked> Over/Under</label>
<label style="font-size:12px;margin-left:10px"><input type="checkbox" id="useMatchDiff" checked> Matches/Differs</label>
<label style="font-size:12px;margin-left:10px"><input type="checkbox" id="useTouch"> Touch/NoTouch</label>
</div>
<button class="btn btn-green" onclick="startBot()" id="startBtn">ONE BUTTON SCAN & TRADE</button>
<div style="display:flex;gap:8px">
<button class="btn btn-red" style="flex:1" onclick="stopBot()">STOP</button>
<button class="btn btn-gray" style="flex:1" onclick="clearAll()">CLEAR</button>
</div>
<div class="card">
<div style="display:flex;justify-content:space-between;font-size:13px">
<span id="bal">Bal:$0</span><span id="profit">P:$0</span><span id="wl">W:0 L:0</span>
</div>
<div style="font-size:13px;margin-top:4px"><span id="nextStake">Next:$1.00</span> | <span id="tradeStatus">READY</span></div>
</div>
<div id="log"></div>
<script>
let ws=null,history=[],prices=[],running=false,wins=0,losses=0,profit=0,currentStake=1,martin=2.1,awaitingResult=false,activeContractId=null,balance=0,tokenMemory="";
const APP_ID="1089",SYMBOL="R_10";
function log(msg,cls="info"){let el=document.getElementById("log");let time=new Date().toLocaleTimeString();el.innerHTML+=`<div>[${time}] <span class="${cls}">${msg}</span></div>`;el.scrollTop=el.scrollHeight;}
function saveToken(t){localStorage.setItem("deriv_pat",t);tokenMemory=t;}
function loadToken(){let t=localStorage.getItem("deriv_pat");if(t){document.getElementById("tokenInput").value=t;tokenMemory=t;log("PAT loaded","ok");}}
function toggleToken(){let inp=document.getElementById("tokenInput");inp.type=inp.type==="password"?"text":"password";}
loadToken();
function connectDeriv(){let token=document.getElementById("tokenInput").value.trim();if(!token){log("Paste PAT first","bad");return;}saveToken(token);if(ws)ws.close();ws=new WebSocket(`wss://ws.derivws.com/websockets/v3?app_id=${APP_ID}`);ws.onopen=()=>{document.getElementById("connBadge").innerText="CONNECTED";document.getElementById("connBadge").className="badge bg-green";document.getElementById("connectStatus").innerHTML="CONNECTED TO DERIV";document.getElementById("connectStatus").style.borderColor="#10b981";document.getElementById("connectBtn").innerHTML="CONNECTED";log("WS CONNECTED","ok");ws.send(JSON.stringify({authorize:token}));ws.send(JSON.stringify({ticks:SYMBOL}));ws.send(JSON.stringify({balance:1}));};ws.onmessage=(msg)=>{let data=JSON.parse(msg.data);if(data.msg_type==="authorize"){if(data.error){log(`AUTH FAILED: ${data.error.message}`,"bad");return;}log(`AUTHENTICATED ${data.authorize.loginid}`,"ok");balance=parseFloat(data.authorize.balance||0);document.getElementById("bal").innerText=`Bal:$${balance.toFixed(2)}`;}if(data.msg_type==="tick"){let price=data.tick.quote;let digit=parseInt(price.toString().slice(-1));if(isNaN(digit))return;prices.push(price);if(prices.length>200)prices.shift();history.push(digit);if(history.length>200)history.shift();document.getElementById("histCount").innerText=history.length;document.getElementById("lastDigit").innerText=digit;document.getElementById("tickPrice").innerText=price.toFixed(3);if(running&&history.length>=50&&!awaitingResult){let best=runScanner();if(best)executeTrade(best);}}if(data.msg_type==="balance"){balance=parseFloat(data.balance.balance);document.getElementById("bal").innerText=`Bal:$${balance.toFixed(2)}`;}if(data.msg_type==="buy"){if(data.error){log(`BUY ERROR: ${data.error.message}`,"bad");awaitingResult=false;return;}activeContractId=data.buy.contract_id;log(`BOUGHT ${activeContractId} $${currentStake.toFixed(2)}`,"info");ws.send(JSON.stringify({proposal_open_contract:1,contract_id:activeContractId,subscribe:1}));}if(data.msg_type==="proposal_open_contract"){let c=data.proposal_open_contract;if(!c)return;if(c.is_sold){let p=parseFloat(c.profit);profit+=p;if(p>0){wins++;log(`WIN +$${p.toFixed(2)} | Profit:$${profit.toFixed(2)}`,"ok");currentStake=parseFloat(document.getElementById("stake").value);}else{losses++;log(`LOSS $${p.toFixed(2)} | Profit:$${profit.toFixed(2)}`,"bad");currentStake=currentStake*martin;}document.getElementById("profit").innerText=`P:$${profit.toFixed(2)}`;document.getElementById("wl").innerText=`W:${wins} L:${losses}`;document.getElementById("nextStake").innerText=`Next:$${currentStake.toFixed(2)}`;awaitingResult=false;activeContractId=null;checkTP_SL();}}};ws.onerror=()=>{log("WEBSOCKET ERROR","bad");};ws.onclose=()=>{document.getElementById("connBadge").innerText="DISCONNECTED";document.getElementById("connBadge").className="badge bg-red";};}
function runScanner(){
if(history.length<50){document.getElementById("scanStatus").innerText=`COLLECT ${history.length}/50`;document.getElementById("scanDetails").innerText=`Collecting... ${history.length}/50`;return null;}
let total=history.length,recent10=history.slice(-10),recent20=history.slice(-20);
let counts=Array(10).fill(0);history.forEach(d=>counts[d]++);
let over2=history.filter(d=>d>2).length,over2Pct=Math.round(over2/total*100),under2Pct=100-over2Pct;
let over4=history.filter(d=>d>4).length,over4Pct=Math.round(over4/total*100),under4Pct=100-over4Pct;
let recentOver2=recent10.filter(d=>d>2).length,recentOver4=recent10.filter(d=>d>4).length;
let lastDigit=history[history.length-1],choppy=(lastDigit===2||lastDigit===3||lastDigit===4);
let maxCount=Math.max(...counts),maxDigit=counts.indexOf(maxCount),maxPct=Math.round(maxCount/total*100);
let minCount=Math.min(...counts),minDigit=counts.indexOf(minCount),minPct=Math.round(minCount/total*100);
let recentCounts=Array(10).fill(0);recent20.forEach(d=>recentCounts[d]++);let recentMax=Math.max(...recentCounts);
document.getElementById("scanDetails").innerText=`O2:${over2Pct}%(${recentOver2}/10) U2:${under2Pct}% | O4:${over4Pct}% U4:${under4Pct}% | Hot:${maxDigit} ${maxPct}% Cold:${minDigit} ${minPct}% ${choppy?'CHOPPY':''}`;
let opps=[],useOU=document.getElementById("useOverUnder").checked,useMD=document.getElementById("useMatchDiff").checked,useTouch=document.getElementById("useTouch").checked;
if(useOU){if(over2Pct>=80&&recentOver2>=7&&!choppy)opps.push({market:"DIGITOVER",barrier:2,conf:over2Pct,type:`Over2 ${over2Pct}%`,symbol:SYMBOL});if(under2Pct>=80&&recentOver2<=3&&!choppy)opps.push({market:"DIGITUNDER",barrier:2,conf:under2Pct,type:`Under2 ${under2Pct}%`,symbol:SYMBOL});if(over4Pct>=75&&recentOver4>=7)opps.push({market:"DIGITOVER",barrier:4,conf:over4Pct,type:`Over4 ${over4Pct}%`,symbol:SYMBOL});if(under4Pct>=78&&recentOver4<=3)opps.push({market:"DIGITUNDER",barrier:4,conf:under4Pct,type:`Under4 ${under4Pct}%`,symbol:SYMBOL});}
if(useMD){if(maxPct>=22&&recentCounts[maxDigit]>=5)opps.push({market:"DIGITMATCH",barrier:maxDigit,conf:maxPct+recentCounts[maxDigit]*2,type:`MATCH ${maxDigit} ${maxPct}%`,symbol:SYMBOL});let notSeenRecent=!recent20.includes(minDigit);if(minPct<=4&&notSeenRecent)opps.push({market:"DIGITDIFF",barrier:minDigit,conf:(100-minPct),type:`DIFF ${minDigit} ${100-minPct}%`,symbol:SYMBOL});}
if(useTouch&&prices.length>=50){let currentPrice=prices[prices.length-1],avg=prices.slice(-20).reduce((a,b)=>a+b,0)/20,range=Math.max(...prices.slice(-20))-Math.min(...prices.slice(-20));if(currentPrice>avg&&range>0.5){let touchBarrier=(currentPrice+range*0.6).toFixed(3);opps.push({market:"TOUCH",barrier:touchBarrier,conf:72,type:`TOUCH ${touchBarrier}`,symbol:SYMBOL,isTouch:true});}if(range>1.0){let noTouchBarrier=(currentPrice+range*1.5).toFixed(3);opps.push({market:"NOTOUCH",barrier:noTouchBarrier,conf:70,type:`NOTOUCH ${noTouchBarrier}`,symbol:SYMBOL,isTouch:true});}}
opps.sort((a,b)=>b.conf-a.conf);let best=opps[0];if(best&&best.conf>=72){document.getElementById("scanStatus").innerText="FAVOURABLE";document.getElementById("conf").innerText=best.conf+"%";document.getElementById("bestMarket").innerText=`🎯 ${best.type} → ${best.market} ${best.barrier}`;document.getElementById("tradeStatus").innerText=`READY ${best.type}`;return best;}document.getElementById("scanStatus").innerText="HOLD";document.getElementById("bestMarket").innerText="No 72% edge - HOLD";document.getElementById("tradeStatus").innerText="HOLD";return null;}
function executeTrade(signal){if(awaitingResult)return;martin=parseFloat(document.getElementById("martin").value)||2.1;if(currentStake>10){log("Stake cap $10 reached - reset","bad");currentStake=parseFloat(document.getElementById("stake").value)||1;}let proposal={};if(signal.isTouch){proposal={proposal:1,amount:currentStake,basis:"stake",contract_type:signal.market,currency:"USD",symbol:signal.symbol,barrier:signal.barrier.toString(),duration:5,duration_unit:"t"};}else{proposal={proposal:1,amount:currentStake,basis:"stake",contract_type:signal.market,currency:"USD",symbol:signal.symbol,barrier:signal.barrier.toString(),duration:1,duration_unit:"t"};}log(`TRADE ${signal.type} Stake:$${currentStake.toFixed(2)} CONF:${signal.conf}%`,"info");ws.send(JSON.stringify(proposal));awaitingResult=true;let handler=(e)=>{let d=JSON.parse(e.data);if(d.msg_type==="proposal"&&d.proposal){if(d.error){log(`PROPOSAL ERROR ${d.error.message}`,"bad");awaitingResult=false;ws.removeEventListener("message",handler);return;}log(`PROPOSAL $${d.proposal.ask_price} ID:${d.proposal.id}`,"info");ws.send(JSON.stringify({buy:d.proposal.id,price:currentStake}));ws.removeEventListener("message",handler);}};ws.addEventListener("message",handler);}
function startBot(){if(!ws||ws.readyState!==1){log("Connect first","bad");return;}running=true;document.getElementById("startBtn").innerText="SCANNING & TRADING...";log("SMART SCAN & TRADE STARTED - ALL MARKETS","ok");}
function stopBot(){running=false;document.getElementById("startBtn").innerText="ONE BUTTON SCAN & TRADE";log("STOPPED","bad");}
function clearAll(){history=[];prices=[];wins=0;losses=0;profit=0;currentStake=parseFloat(document.getElementById("stake").value)||1;document.getElementById("histCount").innerText="0";document.getElementById("profit").innerText="P:$0";document.getElementById("wl").innerText="W:0 L:0";document.getElementById("log").innerHTML="";log("CLEARED","info");}
function checkTP_SL(){let tp=parseFloat(document.getElementById("tp").value)||10,sl=parseFloat(document.getElementById("sl").value)||20;if(profit>=tp){log(`TP HIT $${profit.toFixed(2)} STOPPING`,"ok");stopBot();}if(profit<=-sl){log(`SL HIT $${profit.toFixed(2)} STOPPING`,"bad");stopBot();}}
</script>
</body>
</html>
"""

def deriv_request(method, url, token=None, data=None):
    req = Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    body = json.dumps(data).encode() if data else None
    try:
        with urlopen(req, data=body, timeout=20) as r:
            return json.loads(r.read().decode()), r.status
    except HTTPError as e:
        try:
            b = e.read().decode()
            return json.loads(b), e.code
        except:
            return {"error": str(e)}, e.code

try:
    from http.server import BaseHTTPRequestHandler
    class handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode("utf-8"))
        def do_POST(self): self.do_GET()
        def log_message(self, *a): pass
except: pass
