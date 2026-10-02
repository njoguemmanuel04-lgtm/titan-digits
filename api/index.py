import os
from flask import Flask, request, Response
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TITAN V16.2 MAX TURNOVER</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{font-family:monospace;background:#050508;color:#fff}.mode-active{background:#00ff88;color:#000!important}.mode-forex-active{background:#00aaff;color:#fff!important}.max-glow{box-shadow:0 0 20px #00ff88}</style>
</head>
<body class="p-2 max-w-6xl mx-auto">
<div class="bg-gradient-to-r from-[#00ff88]/20 to-purple-500/20 border border-[#00ff88] rounded-xl p-3 mb-2 max-glow">
<div class="flex justify-between"><div class="font-black text-lg">TITAN V16.2 MAX</div><div id="vol" class="text-[#00ff88] font-black text-lg">$0</div></div>
<div class="text-[10px]">🚀 AUTO MARTINGALE x2.1 + $1 TOUCH x9 = MAX TURNOVER</div>
</div>
<div class="bg-[#0a0a0f] border border-gray-800 rounded-xl p-3 mb-2">
<input id="token" type="password" placeholder="Deriv Token" class="w-full bg-black border border-gray-700 rounded-lg px-3 py-2 text-xs mb-2">
<div class="grid grid-cols-3 gap-2">
<select id="symbol" class="bg-black border border-gray-700 rounded-lg px-2 py-2 text-xs"><option value="R_10">R_10</option><option value="R_100">R_100</option><option value="frxEURUSD">EUR/USD</option><option value="frxGBPUSD">GBP/USD</option></select>
<select id="duration" class="bg-black border border-gray-700 rounded-lg px-2 py-2 text-xs"><option value="5t">5 Ticks</option><option value="5m">5 Min</option></select>
<label class="flex items-center gap-1 text-[10px] bg-purple-900/30 rounded-lg px-2"><input id="martingale" type="checkbox" checked> MARTINGALE x2.1</label>
</div>
<button onclick="connect()" class="w-full mt-2 bg-[#00ff88] text-black font-black py-2 rounded-lg text-xs">CONNECT REAL MAX</button>
<div class="grid grid-cols-4 gap-2 mt-2 text-[10px]"><div>Bal: <span id="bal" class="text-[#00ff88] font-bold">$0</span></div><div>P/L: <span id="pl">$0</span></div><div>Stake: <span id="stakeDisplay" class="text-yellow-400">$0.50</span></div><div id="status" class="text-yellow-400">OFF</div></div>
<div id="smartBarriers" class="text-[9px] text-purple-400 mt-1">SMART S/R: --</div>
</div>
<div class="grid grid-cols-4 gap-2 mb-2">
<button onclick="setM('differs')" id="m-differs" class="bg-[#0a0a0f] border border-gray-800 rounded-xl py-2 text-[10px]">DIFFERS $0.5</button>
<button onclick="setM('touchnotouch')" id="m-touchnotouch" class="mode-forex-active border border-purple-500 rounded-xl py-2 text-[10px]">TOUCH $1 x9</button>
<button onclick="setM('risefall')" id="m-risefall" class="bg-[#0a0a0f] border border-blue-500/30 rounded-xl py-2 text-[10px]">FOREX $1</button>
<button onclick="setM('matches')" id="m-matches" class="bg-[#0a0a0f] border border-gray-800 rounded-xl py-2 text-[10px]">MATCHES x9</button>
</div>
<div class="bg-black border border-gray-800 rounded-xl p-3">
<div id="sig" class="font-black">WAITING MAX</div>
<div id="price" class="text-[10px]">Price: - RSI: -</div>
<div id="ticks" class="flex gap-1 flex-wrap mt-2"></div>
<button id="run" onclick="toggle()" class="w-full mt-3 bg-[#00ff88] text-black font-black rounded-xl py-3">RUN MAX TURNOVER</button>
<div id="log" class="text-[9px] mt-3 space-y-1 h-[200px] overflow-y-auto"></div>
</div>
<script>
let prices=[],ticks=[],ws=null,connected=false,running=false,mode='touchnotouch',pl=0,vol=0,currentStake=0.5,lossStreak=0;
function setM(m){mode=m;document.querySelectorAll('[id^=m-]').forEach(b=>{b.classList.remove('mode-active','mode-forex-active')});document.getElementById('m-'+m).classList.add(m==='touchnotouch'||m==='risefall'?'mode-forex-active':'mode-active');if(m==='touchnotouch'||m==='risefall'||m==='matches')currentStake=1.0;else currentStake=0.5;if(lossStreak>0)currentStake*=Math.pow(2.1,lossStreak);document.getElementById('stakeDisplay').innerText='$'+currentStake.toFixed(2);}
function addLog(x){let l=document.getElementById('log');let d=document.createElement('div');d.innerHTML='['+new Date().toLocaleTimeString()+'] '+x;l.prepend(d);}
function calcRSI(a,p=14){if(a.length<p+1)return 50;let g=0,l=0;for(let i=a.length-p;i<a.length;i++){let d=a[i]-a[i-1];if(d>0)g+=d;else l+=-d;}return l===0?70:100-(100/(1+g/l));}
function findSR(arr){if(arr.length<20)return null;let last=arr.slice(-50);let max=Math.max(...last),min=Math.min(...last),range=max-min,buf=range*0.15||0.0002;return{support:min,resistance:max,smartUpper:max+buf,smartLower:min-buf};}
function connect(){let t=document.getElementById('token').value.trim();if(!t){alert('token');return;}let s=document.getElementById('symbol').value;if(ws)ws.close();ws=new WebSocket('wss://ws.binaryws.com/websockets/v3?app_id=1089');ws.onopen=()=>{ws.send(JSON.stringify({authorize:t}));};ws.onmessage=e=>{let d=JSON.parse(e.data);if(d.error){addLog('❌ '+d.error.message);return;}if(d.msg_type==='authorize'){connected=true;document.getElementById('status').innerText='✅ LIVE';document.getElementById('bal').innerText='$'+d.authorize.balance;ws.send(JSON.stringify({ticks:s,subscribe:1}));addLog('📡 MAX MODE LIVE '+s);}if(d.msg_type==='tick'){let p=parseFloat(d.tick.quote);prices.push(p);ticks.push(parseInt(p.toString().slice(-1)));if(prices.length>150)prices.shift();let rsi=calcRSI(prices);let sr=findSR(prices);document.getElementById('price').innerText=`Price ${p.toFixed(5)} RSI ${rsi.toFixed(0)} | Stake $${currentStake.toFixed(2)} x${lossStreak>0?lossStreak:''}`;if(sr)document.getElementById('smartBarriers').innerText=`S/R: ${sr.support.toFixed(5)} - ${sr.resistance.toFixed(5)} | Barriers: ${sr.smartLower.toFixed(5)} / ${sr.smartUpper.toFixed(5)}`;let sig='WAITING';if(mode==='touchnotouch'&&sr){if(rsi>65)sig=`SMART TOUCH DOWN ${sr.smartLower.toFixed(5)}`;else if(rsi<35)sig=`SMART TOUCH UP ${sr.smartUpper.toFixed(5)}`;else sig=`SMART NO TOUCH ${sr.smartUpper.toFixed(5)}`;}else if(mode==='differs'&&ticks.length>=20){let cnt=Array(10).fill(0);ticks.slice(-20).forEach(x=>cnt[x]++);let hot=cnt.indexOf(Math.max(...cnt));sig=`DIFFERS ${hot}`;}else if(mode==='matches'&&ticks.length>=20){let cnt=Array(10).fill(0);ticks.slice(-20).forEach(x=>cnt[x]++);let hot=cnt.indexOf(Math.max(...cnt));sig=`MATCHES ${hot}`;}else if(mode==='risefall'){if(rsi>70)sig='FALL';else if(rsi<30)sig='RISE';}document.getElementById('sig').innerText=sig;if(running)trade(sig,sr);}if(d.msg_type==='buy'){addLog(`🔴 BUY ${d.buy.contract_id} $${currentStake} ${d.buy.barrier||''}`);}if(d.msg_type==='proposal_open_contract'&&d.proposal_open_contract.is_sold){let profit=parseFloat(d.proposal_open_contract.profit);pl+=profit;vol+=currentStake;document.getElementById('pl').innerText='$'+pl.toFixed(2);document.getElementById('vol').innerText='$'+vol.toFixed(2);let mart=document.getElementById('martingale').checked;if(profit>0){addLog(`✅ WIN $${profit.toFixed(2)} → Reset stake`);lossStreak=0;if(mode==='touchnotouch'||mode==='risefall'||mode==='matches')currentStake=1.0;else currentStake=0.5;}else{if(mart){lossStreak++;currentStake*=2.1;addLog(`❌ LOSS $${profit.toFixed(2)} → Martingale x2.1 → Next $${currentStake.toFixed(2)} (streak ${lossStreak})`);}else{addLog(`❌ LOSS $${profit.toFixed(2)}`);}}document.getElementById('stakeDisplay').innerText='$'+currentStake.toFixed(2);}}}}
let can=true;function trade(sig,sr){if(!can)return;if(sig.includes('WAITING'))return;can=false;let sym=document.getElementById('symbol').value,type='',bar='';if(sig.startsWith('DIFFERS')){type='DIGDIFF';bar=sig.match(/\d/)?.[0];}else if(sig.startsWith('MATCHES')){type='DIGMATCH';bar=sig.match(/\d/)?.[0];}else if(sig.includes('RISE')||sig.includes('FALL'))type=sig.includes('RISE')?'CALL':'PUT';else if(sig.includes('TOUCH DOWN')){type='ONETOUCH';bar=sig.match(/\d+\.\d+/)?.[0];}else if(sig.includes('TOUCH UP')){type='ONETOUCH';bar=sig.match(/\d+\.\d+/)?.[0];}else if(sig.includes('NO TOUCH')){type='NOTOUCH';bar=sig.match(/\d+\.\d+/)?.[0];}let params={amount:currentStake,basis:'stake',contract_type:type,currency:'USD',duration:5,duration_unit:'t',symbol:sym};if(bar)params.barrier=bar;ws.send(JSON.stringify({buy:1,price:currentStake,parameters:params}));setTimeout(()=>can=true,4000);}
function toggle(){if(!connected){alert('connect');return;}running=!running;document.getElementById('run').innerText=running?'STOP MAX':'RUN MAX TURNOVER';addLog(running?'▶️ MAX TURNOVER STARTED - Martingale ON, $1 Touch':'⏹️ STOPPED');}
setM('touchnotouch');addLog('V16.2 MAX ready. $0.5 digits, $1 touch/forex, Martingale x2.1, 5 sec speed.');
</script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def home():
    return Response(HTML, mimetype='text/html')

@app.route('/api', methods=['POST'])
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    if request.method == 'POST' and bot:
        bot.process_new_updates([telebot.types.Update.de_json(request.get_json(force=True))])
        return 'ok'
    return 'ok'

if bot:
    @bot.message_handler(commands=['start'])
    def start(m):
        bot.reply_to(m, "TITAN V16.2 MAX LIVE\nOpen: https://titan-digits.vercel.app", disable_web_page_preview=False)

if __name__ == '__main__':
    app.run()
