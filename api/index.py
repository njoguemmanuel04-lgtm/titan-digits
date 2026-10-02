from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        html = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>TITAN V34 - CONNECT FIX + MEMORY</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#0f172a] text-white p-3">
<div class="max-w-md mx-auto">
<h1 class="text-center font-black text-emerald-400">TITAN V34 - CONNECT FIX + MEMORY</h1>
<div class="text-center text-7xl font-black text-emerald-400 my-3" id="lastDigit">-</div>
<div class="text-center text-xs text-cyan-400" id="tickInfo">PASTE TOKEN & TAP CONNECT</div>

<div class="grid grid-cols-5 gap-2 my-3" id="digitGrid"></div>

<div class="flex justify-between text-xs bg-slate-800 p-2 rounded-xl mb-2">
<span>History:<b id="histCount">0</b></span>
<span>CONF:<b id="conf">0</b>%</span>
<span id="scanStatus">WAITING</span>
</div>

<div class="bg-slate-800 rounded-xl p-3 mb-3 border border-emerald-500/30">
<div id="scanDetails" class="text-[11px] text-gray-300">Waiting for ticks...</div>
<div id="bestMarket" class="text-sm font-bold text-yellow-400 mt-1"></div>
</div>

<div class="text-center text-xs mb-3 p-2 rounded-xl bg-slate-800" id="dotStatus">🔴 NOT CONNECTED - Paste token below</div>

<!-- TOKEN INPUT WITH MEMORY -->
<input id="token" type="password" placeholder="Paste Deriv Token a1-... here" class="w-full bg-slate-900 border border-slate-700 p-4 rounded-xl text-center text-sm mb-2">

<button onclick="connectNow()" class="w-full bg-blue-600 hover:bg-blue-500 font-black py-4 rounded-xl mb-2 text-base">🔌 CONNECT NOW</button>
<button onclick="toggleToken()" class="w-full bg-slate-700 font-bold py-2 rounded-xl mb-4 text-xs">👁️ Show / Hide Token</button>

<div class="grid grid-cols-4 gap-2 mb-3">
<div class="text-center"><div class="text-[10px] text-gray-400">STAKE</div><input id="stake" value="1" class="w-full bg-slate-800 p-2 rounded-xl text-center"></div>
<div class="text-center"><div class="text-[10px] text-gray-400">MARTIN</div><input id="martingale" value="2.1" class="w-full bg-slate-800 p-2 rounded-xl text-center"></div>
<div class="text-center"><div class="text-[10px] text-gray-400">TP $</div><input id="tp" value="10" class="w-full bg-slate-800 p-2 rounded-xl text-center border border-emerald-500"></div>
<div class="text-center"><div class="text-[10px] text-gray-400">SL $</div><input id="sl" value="20" class="w-full bg-slate-800 p-2 rounded-xl text-center border border-red-500"></div>
</div>

<button onclick="startTrading()" class="w-full bg-gradient-to-r from-emerald-400 to-cyan-400 text-black font-black py-4 rounded-xl mb-2">🧠 ONE BUTTON SCAN & TRADE</button>

<div class="grid grid-cols-2 gap-2 mb-3">
<button onclick="stopTrading()" class="bg-red-600 font-bold py-3 rounded-xl">⏹️ STOP</button>
<button onclick="clearLog()" class="bg-slate-800 font-bold py-3 rounded-xl">🧹 CLEAR</button>
</div>

<div class="text-center text-xs bg-black/50 p-2 rounded-xl">
<span id="balance">Bal:$0.00</span> | <span id="profit" class="font-bold">P:$0.00</span> | <span id="wins">W:0</span> <span id="loss">L:0</span><br>
Next:<span id="nextStake" class="text-yellow-400">$1</span> | <span id="tradeStatus">HOLD</span>
</div>

<div id="log" class="bg-black/80 rounded-xl p-2 mt-3 h-72 overflow-y-auto text-[11px] font-mono border border-slate-700"></div>

</div>

<script>
let history=[], counts=Array(10).fill(0), ws=null, trading=false, nextStake=1, profit=0, wins=0, losses=0, balance=0, dotConnected=false, awaitingResult=false;

const grid=document.getElementById("digitGrid");
for(let i=0;i<10;i++){
  let d=document.createElement("div");
  d.className="bg-slate-800 rounded-xl p-2 text-center";
  d.innerHTML=`<div class="font-black">${i}</div><div class="text-[10px]" id="pct${i}">0%</div>`;
  grid.appendChild(d);
}

function logM(m){
  let l=document.getElementById("log");
  let time=new Date().toLocaleTimeString();
  l.innerHTML+=`[${time}] ${m}<br>`;
  l.scrollTop=l.scrollHeight;
}

function updateGrid(){
  let t=history.length||1;
  for(let i=0;i<10;i++){
    document.getElementById(`pct${i}`).innerText=Math.round(counts[i]/t*100)+"%";
  }
}

function runScanner(){
  if(history.length<20){
    document.getElementById("scanStatus").innerText=`COLLECT ${history.length}/20`;
    document.getElementById("scanDetails").innerText=`Collecting ticks... ${history.length}/20`;
    return null;
  }
  let total=history.length;
  let over2=history.filter(d=>d>2).length;
  let over2Pct=Math.round(over2/total*100);
  let under2Pct=100-over2Pct;
  let over4=history.filter(d=>d>4).length;
  let over4Pct=Math.round(over4/total*100);

  document.getElementById("scanDetails").innerText=`Over2:${over2Pct}% Under2:${under2Pct}% | Over4:${over4Pct}% | Top favours: ${over2Pct>55?"Over2":under2Pct>55?"Under2":"None"}`;

  let opps=[];
  if(over2Pct>=76) opps.push({market:"DIGITOVER", barrier:2, conf:over2Pct, type:`Over2 ${over2Pct}%`});
  if(under2Pct>=76) opps.push({market:"DIGITUNDER", barrier:2, conf:100-over2Pct, type:`Under2 ${under2Pct}%`});
  if(over4Pct>=70) opps.push({market:"DIGITOVER", barrier:4, conf:over4Pct, type:`Over4 ${over4Pct}%`});

  opps.sort((a,b)=>b.conf-a.conf);
  let best=opps[0];
  if(best){
    document.getElementById("scanStatus").innerText=`✅ FAVOURABLE`;
    document.getElementById("conf").innerText=best.conf;
    document.getElementById("bestMarket").innerText=`🎯 ${best.type} → ${best.market} ${best.barrier}`;
    document.getElementById("tradeStatus").innerText=`READY ${best.type}`;
    return best;
  } else {
    document.getElementById("scanStatus").innerText=`⏸️ HOLD`;
    document.getElementById("bestMarket").innerText=`No high CONF - HOLD`;
    document.getElementById("tradeStatus").innerText=`HOLD`;
    return null;
  }
}

function connectTicks(){
  if(ws) ws.close();
  ws=new WebSocket("wss://ws.derivws.com/websockets/v3?app_id=1089");

  ws.onopen=()=>{
    ws.send(JSON.stringify({ticks:"R_10"}));
    logM("✅ TICK FEED CONNECTED R_10");
  };

  ws.onmessage=(e)=>{
    let data=JSON.parse(e.data);

    if(data.tick){
      let d=Number(String(data.tick.quote).slice(-1));
      history.push(d);
      counts[d]++;
      if(history.length>100) history.shift();
      document.getElementById("lastDigit").innerText=d;
      document.getElementById("tickInfo").innerText=`LIVE ${data.tick.quote} | LAST:${d}`;
      document.getElementById("histCount").innerText=history.length;
      updateGrid();
      let best=runScanner();
      if(best && trading &&!awaitingResult){
        doTrade(best);
      }
    }

    if(data.msg_type=="authorize"){
      balance=Number(data.authorize.balance);
      document.getElementById("balance").innerText=`Bal:$${balance.toFixed(2)}`;
      dotConnected=true;
      document.getElementById("dotStatus").innerHTML=`🟢 <b>CONNECTED</b> Bal:$${balance.toFixed(2)} | ${data.authorize.email}`;
      document.getElementById("dotStatus").className="text-center text-xs mb-3 p-2 rounded-xl bg-emerald-900/50 border border-emerald-500";
      logM(`🔐 AUTH OK Bal $${balance.toFixed(2)}`);
    }

    if(data.msg_type=="proposal_open_contract" && data.proposal_open_contract.is_sold){
      let p=Number(data.proposal_open_contract.profit);
      profit+=p;
      if(p>0) wins++; else losses++;

      // TP/SL CHECK
      let tp=Number(document.getElementById("tp").value);
      let sl=Number(document.getElementById("sl").value);
      if(profit>=tp){ logM(`🎯 TP HIT $${profit.toFixed(2)} - STOPPING`); trading=false; }
      if(profit<=-sl){ logM(`🛑 SL HIT $${profit.toFixed(2)} - STOPPING`); trading=false; }

      if(p>0) nextStake=Number(document.getElementById("stake").value);
      else nextStake=nextStake*Number(document.getElementById("martingale").value);

      document.getElementById("profit").innerText=`P:$${profit.toFixed(2)}`;
      document.getElementById("wins").innerText=`W:${wins}`;
      document.getElementById("loss").innerText=`L:${losses}`;
      document.getElementById("nextStake").innerText=`$${nextStake.toFixed(2)}`;

      if(p>0) logM(`✅ WIN +$${p.toFixed(2)} | Profit:$${profit.toFixed(2)} | Next:$${nextStake.toFixed(2)}`);
      else logM(`❌ LOSS $${p.toFixed(2)} | Profit:$${profit.toFixed(2)} | Next:$${nextStake.toFixed(2)}`);

      awaitingResult=false;
    }

    if(data.error){
      logM(`❌ ERR ${data.error.message}`);
      awaitingResult=false;
    }
  };

  ws.onerror=()=>{ logM("❌ WS ERROR - check internet"); };
}

function connectNow(){
  let token=document.getElementById("token").value.trim();
  if(!token){ logM("❌ PASTE TOKEN FIRST in box"); return; }

  // TOKEN MEMORY SAVE
  localStorage.setItem("deriv_token", token);
  logM(`💾 Token saved to memory`);

  connectTicks();
  setTimeout(()=>{
    if(ws && ws.readyState===1){
      ws.send(JSON.stringify({authorize:token}));
      logM(`🔌 Authorizing ${token.slice(0,6)}...`);
    }
  }, 1000);
}

function doTrade(best){
  if(!dotConnected){ logM("❌ NOT CONNECTED - Tap CONNECT NOW"); return; }
  if(awaitingResult) return;

  let stake=nextStake;
  let req={proposal:1, amount:stake, basis:"stake", contract_type:best.market, currency:"USD", symbol:"R_10", duration:1, duration_unit:"t", barrier:best.barrier};

  logM(`🎯 TRADE → ${best.type} Stake:$${stake} CONF:${best.conf}%`);
  ws.send(JSON.stringify(req));

  let h=(ev)=>{
    let d=JSON.parse(ev.data);
    if(d.msg_type=="proposal"){
      ws.send(JSON.stringify({buy:d.proposal.id, price:d.proposal.ask_price}));
      logM(`📤 PROP $${d.proposal.ask_price} → BUYING...`);
    }
    if(d.msg_type=="buy" && d.buy){
      logM(`📈 BOUGHT ${d.buy.contract_id} $${stake} CONFIRMED`);
      awaitingResult=true;
      ws.send(JSON.stringify({proposal_open_contract:1, contract_id:d.buy.contract_id, subscribe:1}));
    }
  };

  ws.addEventListener("message", h);
  setTimeout(()=>ws.removeEventListener("message", h), 5000);
}

function startTrading(){
  trading=true;
  logM("🧠 SMART SCAN & TRADE STARTED - Waiting for favourable...");
  if(!dotConnected) connectNow();
}

function stopTrading(){ trading=false; logM("⏹️ STOPPED"); }
function clearLog(){ document.getElementById("log").innerHTML=""; }
function toggleToken(){
  let t=document.getElementById("token");
  t.type=t.type=="password"?"text":"password";
}

// TOKEN MEMORY LOAD ON START
window.onload=()=>{
  let saved=localStorage.getItem("deriv_token");
  if(saved){
    document.getElementById("token").value=saved;
    logM(`💾 Token loaded from memory ${saved.slice(0,6)}... Tap CONNECT NOW`);
  } else {
    logM("👋 Paste Deriv token to start");
  }
}
</script>
</body>
</html>
"""
        self.wfile.write(html.encode())
