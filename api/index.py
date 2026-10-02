import os
from flask import Flask, request, Response
import telebot
BOT_TOKEN=os.environ.get("BOT_TOKEN","")
bot=telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
app=Flask(__name__)
HTML="""
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TITAN V16.6 FIXED</title><script src="https://cdn.tailwindcss.com"></script>
<style>body{background:#070b18;color:#e2e8f0;font-family:monospace}.card{background:#11172d;border:1px solid #1e2a4a;border-radius:18px}.input{background:#0b1226;border:1px solid #1e2a4a;border-radius:12px;color:#fff}.mode-active{background:#00ff88!important;color:#000!important}.mode-blue{background:#0ea5e9!important;color:#fff!important}</style>
</head><body class="p-3 max-w-md mx-auto">
<div class="text-center py-3"><div class="text-2xl font-black text-[#00ff88]">🔥 TITAN V16.6 FIXED</div><div class="text-[10px] text-slate-400">CONNECT BUTTON FIXED</div>
<div class="mt-2 flex justify-center gap-2 text-[9px] flex-wrap"><span id="volBadge" class="bg-purple-500/20 text-purple-300 px-2 py-1 rounded-full">$0 VOL</span><span id="modeBadge" class="bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full">MODE: TOUCH</span><span id="slTpBadge" class="bg-slate-800 text-slate-400 px-2 py-1 rounded-full">SL/TP: Not Set</span></div></div>
<div class="card p-4">
<div class="bg-[#00ff88]/10 border border-[#00ff88] rounded-xl p-2 mb-3"><div class="text-[10px] text-[#00ff88] font-bold">🔑 PASTE DERIV TOKEN</div><input id="token" type="text" placeholder="Paste token from app.deriv.com/account/api-token" class="input w-full px-3 py-3 text-sm mt-1 bg-black" style="border:2px solid #00ff88"></div>
<div class="grid grid-cols-2 gap-3 mb-3"><select id="symbol" class="input w-full px-3 py-2.5 text-xs"><option value="R_10">R_10</option><option value="R_25">R_25</option><option value="R_50">R_50</option><option value="R_75">R_75</option><option value="R_100">R_100</option></select><select id="duration" class="input w-full px-3 py-2.5 text-xs"><option value="5t">5 Ticks</option><option value="5m">5 Min</option></select></div>
<div class="grid grid-cols-2 gap-3"><div><div class="text-[11px] text-slate-400 mb-1">STAKE Auto</div><input id="stakeBase" value="1.0" class="input w-full px-3 py-2.5 text-xs"><div class="text-[9px] text-yellow-400">Live $<span id="stakeLive">1.00</span><span id="streakInfo"></span></div></div><div><div class="text-[11px] text-slate-400 mb-1">MARTINGALE x</div><input id="martingaleFactor" value="2.1" class="input w-full px-3 py-2.5 text-xs"></div></div>
<div class="grid grid-cols-2 gap-3 mt-3"><div><div class="text-[11px] text-slate-400 mb-1">STOP LOSS - Optional</div><input id="stopLoss" type="number" placeholder="e.g. 10" class="input w-full px-3 py-2.5 text-xs"></div><div><div class="text-[11px] text-slate-400 mb-1">TAKE PROFIT - Optional</div><input id="takeProfit" type="number" placeholder="e.g. 50" class="input w-full px-3 py-2.5 text-xs"></div></div>
<div class="flex justify-between items-center mt-3 bg-[#0b1226] border border-[#1e2a4a] rounded-xl px-3 py-2"><label class="text-[11px]"><input id="martingale" type="checkbox" checked> MARTINGALE</label><div id="status" class="text-[10px] text-yellow-400 font-bold">OFFLINE</div></div>
<div class="grid grid-cols-4 gap-2 mt-4"><button onclick="setM('differs')" id="m-differs" class="card py-3 text-[10px] font-bold">DIFFERS<br>$0.5</button><button onclick="setM('touchnotouch')" id="m-touchnotouch" class="card py-3 text-[10px] font-bold mode-blue">TOUCH<br>$1 x9</button><button onclick="setM('risefall')" id="m-risefall" class="card py-3 text-[10px] font-bold">FOREX<br>$1</button><button onclick="setM('matches')" id="m-matches" class="card py-3 text-[10px] font-bold">MATCHES<br>x9</button></div>
<div class="mt-4 bg-black border border-[#00ff88]/50 rounded-2xl p-4 text-center"><div id="sig" class="text-lg font-black text-[#00ff88]">WAITING TICKS...</div><div id="price" class="text-[10px] text-slate-400 mt-2">Price: -</div><div id="smartBarriers" class="text-[9px] text-purple-400">S/R: --</div><div id="ticks" class="flex gap-1 justify-center flex-wrap mt-3"></div></div>
<button id="run" onclick="toggle()" class="w-full mt-3 bg-[#00ff88] text-black font-black py-4 rounded-2xl">▶️ RUN LIVE TRADER</button>
<button id="connBtn" onclick="connect()" class="w-full mt-2 border-2 border-[#00ff88] text-[#00ff88] py-3 rounded-2xl text-sm font-bold">🔌 CONNECT REAL MAX - CLICK HERE</button>
</div>
<div class="card p-4 mt-4"><div class="flex justify-between text-sm py-2 border-b border-slate-800"><span>Profit</span><span id="pl" class="text-[#00ff88] font-bold">$0.00</span></div><div class="flex justify-between text-sm py-2 border-b border-slate-800"><span>Balance</span><span id="bal">$0</span></div><div class="flex justify-between text-sm py-2"><span>Last Digit</span><span id="lastDigit" class="text-[#00ff88]">-</span></div></div>
<div class="card p-4 mt-4"><div id="log" class="bg-[#080d1f] rounded-xl p-3 text-[10px] h-[220px] overflow-y-auto">Idle. V16.6 fixed connect.</div></div>
<script>
let prices=[],ticks=[],ws=null,connected=false,running=false,mode='touchnotouch',pl=0,vol=0,currentStake=1.0,lossStreak=0;
function setM(m){mode=m;document.querySelectorAll('[id^=m-]').forEach(b=>b.classList.remove('mode-active','mode-blue'));let el=document.getElementById('m-'+m);if(m==='touchnotouch'||m==='risefall')el.classList.add('mode-blue');else el.classList.add('mode-active');document.getElementById('modeBadge').innerText='MODE: '+m.toUpperCase();addLog('MODE → '+m.toUpperCase());}
function addLog(x){let l=document.getElementById('log');let d=document.createElement('div');d.innerHTML='['+new Date().toLocaleTimeString()+'] '+x;l.prepend(d);}
function connect(){
 let t=document.getElementById('token').value.trim();
 if(!t||t.length<10){alert('❌ Paste valid Deriv API token first! Get from app.deriv.com/account/api-token');return;}
 document.getElementById('status').innerText='CONNECTING...';document.getElementById('status').style.color='#facc15';
 document.getElementById('connBtn').innerText='⏳ CONNECTING... PLEASE WAIT';
 addLog('🔌 Connecting... token '+t.substring(0,4)+'...');
 if(ws)try{ws.close()}catch(e){}
 try{ws=new WebSocket('wss://ws.binaryws.com/websockets/v3?app_id=1089');}catch(e){addLog('❌ WS Error '+e);alert('WebSocket blocked. Open in Chrome.');return;}
 ws.onopen=function(){addLog('✅ WS Open, authorizing...');ws.send(JSON.stringify({authorize:t}));};
 ws.onerror=function(e){addLog('❌ WebSocket Error - Open in Chrome, not Telegram');document.getElementById('status').innerText='WS ERROR';document.getElementById('connBtn').innerText='❌ FAILED - OPEN IN CHROME';alert('Failed to connect. Please open titan-digits.vercel.app in Chrome browser, not Telegram. Telegram blocks Deriv.');};
 ws.onclose=function(){if(!connected)addLog('❌ Closed. Token invalid or blocked.');};
 ws.onmessage=function(e){let d=JSON.parse(e.data);if(d.error){addLog('❌ '+d.error.message);alert('Deriv Error: '+d.error.message+' - Check token is REAL account with Read+Trade');document.getElementById('status').innerText='AUTH FAILED';document.getElementById('connBtn').innerText='❌ AUTH FAILED';return;}if(d.msg_type==='authorize'){connected=true;document.getElementById('status').innerText='✅ LIVE - '+d.authorize.logininfo.currency+' $'+d.authorize.balance;document.getElementById('status').style.color='#00ff88';document.getElementById('bal').innerText='$'+d.authorize.balance;document.getElementById('connBtn').innerText='✅ CONNECTED - '+d.authorize.balance;addLog('✅ LIVE! Balance $'+d.authorize.balance);let s=document.getElementById('symbol').value;ws.send(JSON.stringify({ticks:s,subscribe:1}));}
 if(d.msg_type==='tick'){let p=parseFloat(d.tick.quote);prices.push(p);if(prices.length>150)prices.shift();document.getElementById('price').innerText='Price '+p.toFixed(5)+' Stake $'+currentStake;let digit=parseInt(p.toString().slice(-1));document.getElementById('lastDigit').innerText=digit;}}
}
function toggle(){if(!connected){alert('Click CONNECT REAL MAX first!');return;}running=!running;document.getElementById('run').innerText=running?'⏹️ STOP TRADING':'▶️ RUN LIVE TRADER';addLog(running?'▶️ STARTED':'⏹️ STOPPED');}
setM('touchnotouch');
</script></body></html>
"""
@app.route('/',methods=['GET'])
def home():return Response(HTML,mimetype='text/html')
@app.route('/api',methods=['POST'])
@app.route(f'/{BOT_TOKEN}',methods=['POST'])
def webhook():
 if request.method=='POST' and bot:bot.process_new_updates([telebot.types.Update.de_json(request.get_json(force=True))]);return 'ok'
 return 'ok'
if __name__=='__main__':app.run()
