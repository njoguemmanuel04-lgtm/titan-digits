from http.server import BaseHTTPRequestHandler

HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TITAN V37 MASTERPIECE</title>
<style>
body{background:#020617;color:#e2e8f0;font-family:Arial;padding:10px;margin:0}
.card{background:#0f172a;border-radius:12px;padding:12px;margin:8px 0;border:1px solid #1e293b}
.btn{width:100%;padding:14px;border:none;border-radius:10px;font-weight:bold;font-size:16px;cursor:pointer;margin:6px 0}
.btn-blue{background:#2563eb;color:white}.btn-green{background:linear-gradient(90deg,#10b981,#06b6d4);color:#000}
.btn-red{background:#ef4444;color:white}.btn-gray{background:#334155;color:white}
input{background:#020617;border:1px solid #475569;color:white;padding:12px;border-radius:8px;width:100%;box-sizing:border-box}
.grid4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px}
#log{background:#000;height:280px;overflow-y:auto;font-family:monospace;font-size:11px;padding:8px;border-radius:8px}
.ok{color:#10b981}.bad{color:#ef4444}.info{color:#38bdf8}.warn{color:#facc15}
.badge{padding:2px 8px;border-radius:99px;font-size:11px;font-weight:bold}
.bg-green{background:#064e3b;color:#10b981;border:1px solid #10b981}
.bg-red{background:#450a0a;color:#ef4444;border:1px solid #ef4444}
.bg-yellow{background:#422006;color:#facc15;border:1px solid #facc15}
</style></head><body>
<h2 style="text-align:center;color:#10b981">TITAN V37 - MASTERPIECE 78%+</h2>
<div class="card"><div class="grid4" style="text-align:center">
<div><div style="font-size:10px;color:#94a3b8">HIST</div><div id="histCount" style="font-size:20px;font-weight:bold">0</div></div>
<div><div style="font-size:10px;color:#94a3b8">LAST</div><div id="lastDigit" style="font-size:20px;font-weight:bold">-</div></div>
<div><div style="font-size:10px;color:#94a3b8">PRICE</div><div id="tickPrice" style="font-size:12px;font-weight:bold">-</div></div>
<div><div style="font-size:10px;color:#94a3b8">CONF</div><div id="conf" style="font-size:20px;font-weight:bold">0%</div></div>
</div><div id="scanDetails" style="margin-top:8px;font-size:11px;color:#94a3b8">Collecting 0/100...</div>
<div id="bestMarket" style="margin-top:4px;font-weight:bold;font-size:13px">-</div>
<div style="margin-top:6px"><span id="scanStatus" class="badge bg-red">COLLECTING</span> <span id="connBadge" class="badge bg-red">OFF</span></div></div>
<div class="card"><div id="connectStatus" style="text-align:center;padding:8px;border-radius:8px;background:#1e293b">DISCONNECTED</div>
<input type="password" id="tokenInput" placeholder="Paste Deriv API Token - saved forever">
<button class="btn btn-blue" onclick="connectDeriv()">CONNECT NOW</button></div>
<div class="card grid4">
<div><div style="font-size:10px">STAKE</div><input id="stake" value="1" type="number" step="0.1"></div>
<div><div style="font-size:10px">MARTIN x</div><input id="martin" value="2.05" type="number" step="0.05"></div>
<div><div style="font-size:10px">TP $</div><input id="tp" value="15" type="number"></div>
<div><div style="font-size:10px">SL $</div><input id="sl" value="30" type="number"></div>
</div><div class="card" style="font-size:12px">
<label><input type="checkbox" id="useOverUnder" checked> Over/Under</label>
<label style="margin-left:12px"><input type="checkbox" id="useMatchDiff" checked> Match/Diff</label>
<label style="margin-left:12px"><input type="checkbox" id="useTouch"> Touch</label>
</div><button class="btn btn-green" onclick="startBot()" id="startBtn">ONE BUTTON SCAN & TRADE</button>
<div style="display:flex;gap:8px"><button class="btn btn-red" style="flex:1" onclick="stopBot()">STOP</button><button class="btn btn-gray" style="flex:1" onclick="clearAll()">CLEAR</button></div>
<div class="card"><div style="display:flex;justify-content:space-between;font-size:13px"><span id="bal">Bal:$0</span><span id="profit">P:$0</span><span id="wl">W:0 L:0</span></div><div style="font-size:12px;margin-top:4px"><span id="nextStake">Next:$1.00</span> | <span id="tradeStatus">READY</span></div></div><div id="log"></div>
<script>
let ws=null,history=[],prices=[],running=false,wins=0,losses=0,profit=0,currentStake=1,awaitingResult=false,activeContractId=null,balance=0;
const APP_ID="1089",SYMBOL="R_10";
function log(m,c="info"){let el=document.getElementById("log");el.innerHTML+=`<div>[${new Date().toLocaleTimeString()}] <span class="${c}">${m}</span></div>`;el.scrollTop=el.scrollHeight;}
function saveToken(t){localStorage.setItem("deriv_pat",t);}function loadToken(){let t=localStorage.getItem("deriv_pat");if(t){document.getElementById("tokenInput").value=t;log("PAT loaded from memory","ok");}}loadToken();
function connectDeriv(){let token=document.getElementById("tokenInput").value.trim();if(!token){log("Paste PAT","bad");return;}saveToken(token);if(ws)ws.close();ws=new WebSocket(`wss://ws.derivws.com/websockets/v3?app_id=${APP_ID}`);ws.onopen=()=>{document.getElementById("connBadge").innerText="ON";document.getElementById("connBadge").className="badge bg-green";document.getElementById("connectStatus").innerText="CONNECTED";log("WS CONNECTED","ok");ws.send(JSON.stringify({authorize:token}));ws.send(JSON.stringify({ticks:SYMBOL}));ws.send(JSON.stringify({balance:1}));};ws.onmessage=(e)=>{let d=JSON.parse(e.data);if(d.msg_type==="authorize"){if(d.error){log(d.error.message,"bad");return;}balance=parseFloat(d.authorize.balance);document.getElementById("bal").innerText=`Bal:$${balance.toFixed(2)}`;log(`AUTH ${d.authorize.loginid}`,"ok");}if(d.msg_type==="tick"){let p=d.tick.quote;let digit=parseInt(p.toString().slice(-1));if(isNaN(digit))return;prices.push(p);if(prices.length>300)prices.shift();history.push(digit);if(history.length>300)history.shift();document.getElementById("histCount").innerText=history.length;document.getElementById("lastDigit").innerText=digit;document.getElementById("tickPrice").innerText=p.toFixed(3);if(running&&history.length>=100&&!awaitingResult){let best=runMasterScanner();if(best)executeTrade(best);}}if(d.msg_type==="balance"){balance=parseFloat(d.balance.balance);document.getElementById("bal").innerText=`Bal:$${balance.toFixed(2)}`;}if(d.msg_type==="buy"){if(d.error){log(d.error.message,"bad");awaitingResult=false;return;}activeContractId=d.buy.contract_id;log(`BOUGHT ${activeContractId}`,"info");ws.send(JSON.stringify({proposal_open_contract:1,contract_id:activeContractId,subscribe:1}));}if(d.msg_type==="proposal_open_contract"){let c=d.proposal_open_contract;if(!c||!c.is_sold)return;let pf=parseFloat(c.profit);profit+=pf;if(pf>0){wins++;log(`WIN +$${pf.toFixed(2)}`,"ok");currentStake=parseFloat(document.getElementById("stake").value);}else{losses++;log(`LOSS $${pf.toFixed(2)}`,"bad");let m=parseFloat(document.getElementById("martin").value)||2.05;currentStake*=m;if(currentStake>15)currentStake=parseFloat(document.getElementById("stake").value);}document.getElementById("profit").innerText=`P:$${profit.toFixed(2)}`;document.getElementById("wl").innerText=`W:${wins} L:${losses}`;document.getElementById("nextStake").innerText=`Next:$${currentStake.toFixed(2)}`;awaitingResult=false;}}};ws.onclose=()=>{document.getElementById("connBadge").innerText="OFF";document.getElementById("connBadge").className="badge bg-red";};}
function runMasterScanner(){
if(history.length<100){document.getElementById("scanDetails").innerText=`Collecting ${history.length}/100`;return null;}
let total=history.length;let recent20=history.slice(-20),recent10=history.slice(-10);
let counts=Array(10).fill(0);history.forEach(x=>counts[x]++);
let over2=history.filter(x=>x>2).length,over2Pct=Math.round(over2/total*100),under2Pct=100-over2Pct;
let over4=history.filter(x=>x>4).length,over4Pct=Math.round(over4/total*100),under4Pct=100-over4Pct;
let recentOver2=recent10.filter(x=>x>2).length,recentUnder2=recent10.filter(x=>x<=2).length;
let recentOver4=recent10.filter(x=>x>4).length,recentUnder4=recent10.filter(x=>x<=4).length;
let last=history[history.length-1];
let choppy = (last===2||last===3||last===4) && (history[history.length-2]===2||history[history.length-2]===3||history[history.length-2]===4);
let maxC=Math.max(...counts),maxD=counts.indexOf(maxC),maxPct=Math.round(maxC/total*100);
let minC=Math.min(...counts),minD=counts.indexOf(minC);
let recentCounts=Array(10).fill(0);recent20.forEach(x=>recentCounts[x]++);
let notSeen20 = !recent20.includes(minD);
let opps=[];
let useOU=document.getElementById("useOverUnder").checked;
let useMD=document.getElementById("useMatchDiff").checked;
if(useOU && !choppy){
 if(over2Pct>=82 && recentOver2>=8) opps.push({market:"DIGITOVER",barrier:2,conf:over2Pct,type:`Over2 ${over2Pct}%`});
 if(under2Pct>=82 && recentUnder2>=8) opps.push({market:"DIGITUNDER",barrier:2,conf:under2Pct,type:`Under2 ${under2Pct}%`});
 if(over4Pct>=80 && recentOver4>=7) opps.push({market:"DIGITOVER",barrier:4,conf:over4Pct,type:`Over4 ${over4Pct}%`});
 if(under4Pct>=80 && recentUnder4>=8) opps.push({market:"DIGITUNDER",barrier:4,conf:under4Pct,type:`Under4 ${under4Pct}%`});
}
if(useMD){
 if(maxPct>=24 && recentCounts[maxD]>=6) opps.push({market:"DIGITMATCH",barrier:maxD,conf:maxPct+recentCounts[maxD],type:`MATCH ${maxD} ${maxPct}%`});
 if(minC<=3 && notSeen20) opps.push({market:"DIGITDIFF",barrier:minD,conf:95-minC*5,type:`DIFF ${minD} Cold`});
}
opps.sort((a,b)=>b.conf-a.conf);
let best=opps[0];
document.getElementById("scanDetails").innerText=`O2:${over2Pct}% U2:${under2Pct}% O4:${over4Pct}% U4:${under4Pct}% Hot:${maxD} ${maxPct}% Cold:${minD} Choppy:${choppy?'YES':'NO'}`;
if(best && best.conf>=78){
 document.getElementById("scanStatus").innerText="FAVOURABLE";document.getElementById("scanStatus").className="badge bg-green";
 document.getElementById("conf").innerText=best.conf+"%";
 document.getElementById("bestMarket").innerText=`🎯 ${best.type} -> ${best.market} B:${best.barrier}`;
 document.getElementById("tradeStatus").innerText=`READY ${best.type}`;
 return best;
}else{
 document.getElementById("scanStatus").innerText="HOLD";document.getElementById("scanStatus").className="badge bg-yellow";
 document.getElementById("bestMarket").innerText="No 78% edge - HOLDING";
 return null;
}}
function executeTrade(s){if(awaitingResult)return;let prop={proposal:1,amount:currentStake,basis:"stake",contract_type:s.market,currency:"USD",symbol:"R_10",barrier:s.barrier.toString(),duration:1,duration_unit:"t"};log(`TRADE ${s.type} $${currentStake.toFixed(2)}`,"info");ws.send(JSON.stringify(prop));awaitingResult=true;let h=(e)=>{let d=JSON.parse(e.data);if(d.msg_type==="proposal"&&d.proposal){ws.send(JSON.stringify({buy:d.proposal.id,price:currentStake}));ws.removeEventListener("message",h);}};ws.addEventListener("message",h);}
function startBot(){if(!ws||ws.readyState!==1){log("Connect first","bad");return;}running=true;document.getElementById("startBtn").innerText="MASTER SCANNING 78%+";log("MASTER BOT STARTED","ok");}
function stopBot(){running=false;document.getElementById("startBtn").innerText="ONE BUTTON SCAN & TRADE";log("STOPPED","bad");}
function clearAll(){history=[];prices=[];wins=0;losses=0;profit=0;currentStake=parseFloat(document.getElementById("stake").value)||1;document.getElementById("histCount").innerText="0";document.getElementById("log").innerHTML="";}
</script></body></html>
"""

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode("utf-8"))
    def do_POST(self):
        self.do_GET()
