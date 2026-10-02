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
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TITAN V16.5 MAX USER SL/TP</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
body{background:#070b18;color:#e2e8f0;font-family:monospace}
.card{background:#11172d;border:1px solid #1e2a4a;border-radius:18px}
.input{background:#0b1226;border:1px solid #1e2a4a;border-radius:12px;color:#fff}
.mode-active{background:#00ff88!important;color:#000!important}
.mode-blue{background:#0ea5e9!important;color:#fff!important}
</style>
</head>
<body class="p-3 max-w-md mx-auto">
<div class="text-center py-3">
<div class="text-2xl font-black text-[#00ff88]">🔥 TITAN V16.5 MAX</div>
<div class="text-[10px] text-slate-400">USER SETS OWN SL/TP - NO DEFAULTS</div>
<div class="mt-2 flex justify-center gap-2 text-[9px] flex-wrap">
<span id="volBadge" class="bg-purple-500/20 text-purple-300 px-2 py-1 rounded-full">$0 VOL</span>
<span id="modeBadge" class="bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full">MODE: TOUCH</span>
<span id="slTpBadge" class="bg-slate-800 text-slate-400 px-2 py-1 rounded-full">SL/TP: Not Set</span>
</div>
</div>
<div class="card p-4">
<input id="token" type="password" placeholder="Paste Deriv API Token" class="input w-full px-3 py-2.5 text-xs mb-3">
<div class="grid grid-cols-2 gap-3 mb-3">
<select id="symbol" class="input w-full px-3 py-2.5 text-xs"><option value="R_10">R_10</option><option value="R_100">R_100</option><option value="frxEURUSD">EUR/USD</option><option value="frxGBPUSD">GBP/USD</option></select>
<select id="duration" class="input w-full px-3 py-2.5 text-xs"><option value="5t">5 Ticks</option><option value="5m">5 Min</option></select>
</div>
<div class="grid grid-cols-2 gap-3">
<div><div class="text-[11px] text-slate-400 mb-1">STAKE Auto</div><input id="stakeBase" value="1.0" readonly class="input w-full px-3 py-2.5 text-xs"><div class="text-[9px] text-yellow-400">Live $<span id="stakeLive">1.00</span><span id="streakInfo"></span></div></div>
<div><div class="text-[11px] text-slate-400 mb-1">MARTINGALE x</div><input id="martingaleFactor" value="2.1" class="input w-full px-3 py-2.5 text-xs"></div>
</div>
<div class="grid grid-cols-2 gap-3 mt-3">
<div><div class="text-[11px] text-slate-400 mb-1">STOP LOSS ($) - Optional</div><input id="stopLoss" type="number" placeholder="e.g. 10" class="input w-full px-3 py-2.5 text-xs border-red-500/30"><div class="text-[8px] text-slate-500">Leave empty = no SL</div></div>
<div><div class="text-[11px] text-slate-400 mb-1">TAKE PROFIT ($) - Optional</div><input id="takeProfit" type="number" placeholder="e.g. 50" class="input w-full px-3 py-2.5 text-xs border-green-500/30"><div class="text-[8px] text-slate-500">Leave empty = no TP</div></div>
</div>
<div id="progressWrap" class="hidden mt-3"><div class="bg-[#0b1226] rounded-full h-2.5 overflow-hidden border border-slate-800"><div id="slProgress" class="h-full transition-all" style="width:0%; background:#00ff88"></div></div><div class="flex justify-between text-[9px] text-slate-500 mt-1"><span id="slLabel">SL: Not set</span><span id="plDisplay" class="font-bold">$0.00</span><span id="tpLabel">TP: Not set</span></div></div>
<div class="flex justify-between items-center mt-3 bg-[#0b1226] border border-[#1e2a4a] rounded-xl px-3 py-2"><label class="text-[11px]"><input id="martingale" type="checkbox" checked> MARTINGALE x2.1</label><div id="status" class="text-[10px] text-yellow-400 font-bold">OFF</div></div>
<div class="grid grid-cols-4 gap-2 mt-4">
<button onclick="setM('differs')" id="m-differs" class="card py-3 text-[10px] font-bold">DIFFERS<br>$0.5</button>
<button onclick="setM('touchnotouch')" id="m-touchnotouch" class="card py-3 text-[10px] font-bold mode-blue">TOUCH<br>$1 x9</button>
<button onclick="setM('risefall')" id="m-risefall" class="card py-3 text-[10px] font-bold">FOREX<br>$1</button>
<button onclick="setM('matches')" id="m-matches" class="card py-3 text-[10px] font-bold">MATCHES<br>x9</button>
</div>
<div class="mt-4 bg-black border border-[#00ff88]/50 rounded-2xl p-4 text-center"><div id="sig" class="text-lg font-black text-[#00ff88]">WAITING TICKS...</div><div id="price" class="text-[10px] text-slate-400 mt-2">Price: -</div><div id="smartBarriers" class="text-[9px] text-purple-400">SMART S/R: --</div><div id="ticks" class="flex gap-1 justify-center flex-wrap mt-3"></div></div>
<button id="run" onclick="toggle()" class="w-full mt-3 bg-[#00ff88] text-black font-black py-4 rounded-2xl">▶️ RUN LIVE TRADER</button>
<button onclick="connect()" class="w-full mt-2 border border-[#00ff88]/30 text-[#00ff88] py-2.5 rounded-2xl text-xs">CONNECT REAL MAX</button>
</div>
<div class="card p-4 mt-4">
<div class="flex justify-between text-sm py-2 border-b border-slate-800"><span class="text-slate-400">Profit</span><span id="pl" class="text-[#00ff88] font-bold">$0.00</span></div>
<div class="flex justify-between text-sm py-2 border-b border-slate-800"><span>Trades</span><span id="trades">0</span></div>
<div class="flex justify-between text-sm py-2 border-b border-slate-800"><span>Win Rate</span><span id="winRate">0%</span></div>
<div class="flex justify-between text-sm py-2 border-b border-slate-800"><span>Volume</span><span id="vol" class="text-purple-300">$0</span></div>
<div class="flex justify-between text-sm py-2"><span>Last Digit</span><span id="lastDigit" class="text-[#00ff88]">-</span></div>
<div class="flex justify-between text-sm py-2"><span>Balance</span><span id="bal">$0</span></div>
</div>
<div class="card p-4 mt-4"><div id="log" class="bg-[#080d1f] rounded-xl p-3 text-[10px] h-[220px] overflow-y-auto">Idle. Set your own SL/TP or leave empty.</div></div>
<script>
let prices=[],ticks=[],ws=null,connected=false,running=false,mode='touchnotouch',pl=0,vol=0,currentStake=1.0,lossStreak=0,trades=0,wins=0,slHit=false,tpHit=false;
function setM(m){mode=m;document.querySelectorAll('[id^=m-]').forEach(b=>{b.classList.remove('mode-active','mode-blue');});let el=document.getElementById('m-'+m);if(m==='touchnotouch'||m==='risefall')el.classList.add('mode-blue');else el.classList.add('mode-active');if(m==='differs'){document.getElementById('stakeBase').value='0.5';currentStake=0.5;document.getElementById('duration').value='5t';}else{document.getElementById('stakeBase').value='1.0';currentStake=1.0;document.getElementById('duration').value='5m';}if(lossStreak>0)currentStake*=parseFloat(document.getElementById('martingaleFactor').value)||2.1;document.getElementById('modeBadge').innerText='MODE: '+m.toUpperCase();updateStakeUI();addLog('MODE → '+m.toUpperCase());}
function updateStakeUI(){document.getElementById('stakeLive').innerText=currentStake.toFixed(2);document.getElementById('streakInfo').innerText=lossStreak>0?' (x'+lossStreak+')':'';}
function addLog(x){let l=document.getElementById('log');let d=document.createElement('div');d.innerHTML='['+new Date().toLocaleTimeString()+'] '+x;l.prepend(d);}
function calcRSI(a,p=14){if(a.length<p+1)return 50;let g=0,l=0;for(let i=a.length-p;i<a.length;i++){let d=a[i]-a[i-1];if(d>0)g+=d;else l+=-d;}return l===0?70:100-(100/(1+g/l));}
function findSR(arr){if(arr.length<20)return null;let last=arr.slice(-50);let max=Math.max(...last),min=Math.min(...last),range=max-min,buf=range*0.15||0.0002;return{support:min,resistance:max,smartUpper:max+buf,smartLower:min-buf};}
function updateSLTPDisplay(){
  let slVal=document.getElementById('stopLoss').value; let tpVal=document.getElementById('takeProfit').value;
  let sl=parseFloat(slVal); let tp=parseFloat(tpVal);
  let hasSL=!isNaN(sl)&&sl>0; let hasTP=!isNaN(tp)&&tp>0;
  if(hasSL||hasTP){document.getElementById('progressWrap').classList.remove('hidden');} else {document.getElementById('progressWrap').classList.add('hidden');}
  document.getElementById('slLabel').innerText=hasSL?'SL: -$'+sl:'SL: Not set';
  document.getElementById('tpLabel').innerText=hasTP?'TP: +$'+tp:'TP: Not set';
  document.getElementById('plDisplay').innerText='$'+pl.toFixed(2);
  if(hasSL||hasTP){document.getElementById('slTpBadge').innerText=(hasSL?'SL:-$'+sl:'')+(hasSL&&hasTP?' / ':'')+(hasTP?'TP:+$'+tp:'');} else {document.getElementById('slTpBadge').innerText='SL/TP: Not Set - Running unlimited';}
  if(hasSL||hasTP){let progress=0; if(pl<0&&hasSL) progress=Math.min(100,Math.abs(pl)/sl*100); else if(pl>0&&hasTP) progress=Math.min(100,pl/tp*100); document.getElementById('slProgress').style.width=progress+'%'; document.getElementById('slProgress').style.background=pl<0?'#ef4444':'#00ff88';}
}
function checkSLTP(){
  let sl=parseFloat(document.getElementById('stopLoss').value); let tp=parseFloat(document.getElementById('takeProfit').value);
  let hasSL=!isNaN(sl)&&sl>0; let hasTP=!isNaN(tp)&&tp>0;
  updateSLTPDisplay();
  if(hasSL&&pl<=-sl&&!slHit){slHit=true;addLog('🛑 STOP LOSS HIT -$'+sl);alert('🛑 STOP LOSS HIT! '+pl.toFixed(2));running=false;document.getElementById('run').innerText='🛑 SL HIT - RESET';document.getElementById('run').style.background='#ef4444';return true;}
  if(hasTP&&pl>=tp&&!tpHit){tpHit=true;addLog('🎯 TAKE PROFIT HIT +$'+tp);alert('🎯 TAKE PROFIT HIT! '+pl.toFixed(2));running=false;document.getElementById('run').innerText='🎯 TP HIT - RESET';document.getElementById('run').style.background='#00ff88';return true;}
  return false;
}
function connect(){let t=document.getElementById('token').value.trim();if(!t){alert('Token');return;}let s=document.getElementById('symbol').value;if(ws)ws.close();ws=new WebSocket('wss://ws.binaryws.com/websockets/v3?app_id=1089');ws.onopen=()=>ws.send(JSON.stringify({authorize:t}));ws.onmessage=e=>{let d=JSON.parse(e.data);if(d.error){addLog('❌ '+d.error.message);return;}if(d.msg_type==='authorize'){connected=true;document.getElementById('status').innerText='✅ LIVE';document.getElementById('bal').innerText='$'+d.authorize.balance;ws.send(JSON.stringify({ticks:s,subscribe:1}));addLog('📡 LIVE '+s);}if(d.msg_type==='tick'){let p=parseFloat(d.tick.quote);let digit=parseInt(p.toString().slice(-1));prices.push(p);ticks.push(digit);if(prices.length>150)prices.shift();if(ticks.length>30)ticks.shift();let rsi=calcRSI(prices);let sr=findSR(prices);document.getElementById('price').innerText='Price '+p.toFixed(5)+' RSI '+rsi.toFixed(0)+' Stake $'+currentStake.toFixed(2);document.getElementById('lastDigit').innerText=digit;if(sr)document.getElementById('smartBarriers').innerText='S/R: '+sr.support.toFixed(5)+' - '+sr.resistance.toFixed(5);let sig='WAITING TICKS...';if(mode==='touchnotouch'&&sr){if(rsi>65)sig='TOUCH DOWN '+sr.smartLower.toFixed(5);else if(rsi<35)sig='TOUCH UP '+sr.smartUpper.toFixed(5);else sig='NO TOUCH '+sr.smartUpper.toFixed(5);}else if(mode==='differs'){let cnt=Array(10).fill(0);ticks.slice(-15).forEach(x=>cnt[x]++);sig='DIFFERS '+cnt.indexOf(Math.max(...cnt));}else if(mode==='matches'){let cnt=Array(10).fill(0);ticks.slice(-15).forEach(x=>cnt[x]++);sig='MATCHES '+cnt.indexOf(Math.max(...cnt));}else if(mode==='risefall'){if(rsi>70)sig='FALL';else if(rsi<30)sig='RISE';}document.getElementById('sig').innerText=sig;document.getElementById('ticks').innerHTML=ticks.slice(-20).map(x=>'<span style="display:inline-flex;width:22px;height:22px;border-radius:50%;background:'+(x===digit?'#00ff88;color:#000':'#1e2a4a')+';align-items:center;justify-content:center;font-size:10px;margin:1px">'+x+'</span>').join('');if(running)trade(sig);}if(d.msg_type==='buy'){addLog('🔴 BUY $'+currentStake);}if(d.msg_type==='proposal_open_contract'&&d.proposal_open_contract.is_sold){let profit=parseFloat(d.proposal_open_contract.profit);pl+=profit;vol+=currentStake;trades++;if(profit>0)wins++;document.getElementById('pl').innerText='$'+pl.toFixed(2);document.getElementById('vol').innerText='$'+vol.toFixed(2);document.getElementById('volBadge').innerText='$'+vol.toFixed(0)+' VOL';document.getElementById('trades').innerText=trades;document.getElementById('winRate').innerText=trades?Math.round(wins/trades*100)+'%':'0%';if(checkSLTP())return;let mf=parseFloat(document.getElementById('martingaleFactor').value)||2.1;let mart=document.getElementById('martingale').checked;if(profit>0){lossStreak=0;currentStake=parseFloat(document.getElementById('stakeBase').value)||1.0;addLog('✅ WIN +$'+profit.toFixed(2));}else{if(mart){lossStreak++;currentStake*=mf;addLog('❌ LOSS $'+profit.toFixed(2)+' → $'+currentStake.toFixed(2));}else addLog('❌ LOSS $'+profit.toFixed(2));}updateStakeUI();updateSLTPDisplay();}}}
let can=true;function trade(sig){if(!can)return;if(sig.includes('WAITING'))return;can=false;let sym=document.getElementById('symbol').value,type='',bar='';let m1=sig.match(/\d+/);let m2=sig.match(/\d+\.\d+/);if(sig.startsWith('DIFFERS')){type='DIGDIFF';bar=m1?m1[0]:'0';}else if(sig.startsWith('MATCHES')){type='DIGMATCH';bar=m1?m1[0]:'0';}else if(sig.includes('RISE')||sig.includes('FALL')){type=sig.includes('RISE')?'CALL':'PUT';}else if(sig.includes('TOUCH DOWN')||sig.includes('TOUCH UP')){type='ONETOUCH';bar=m2?m2[0]:'';}else if(sig.includes('NO TOUCH')){type='NOTOUCH';bar=m2?m2[0]:'';}if(!type){can=true;return;}let params={amount:currentStake,basis:'stake',contract_type:type,currency:'USD',duration:5,duration_unit:document.getElementById('duration').value.includes('m')?'m':'t',symbol:sym};if(bar)params.barrier=bar;ws.send(JSON.stringify({buy:1,price:currentStake,parameters:params}));setTimeout(()=>can=true,3000);}
function toggle(){if(!connected){alert('CONNECT first');return;}if(!running){slHit=false;tpHit=false;pl=0;vol=0;trades=0;wins=0;lossStreak=0;currentStake=parseFloat(document.getElementById('stakeBase').value)||1.0;document.getElementById('pl').innerText='$0.00';document.getElementById('vol').innerText='$0';document.getElementById('trades').innerText='0';document.getElementById('winRate').innerText='0%';}running=!running;document.getElementById('run').innerText=running?'⏹️ STOP TRADING':'▶️ RUN LIVE TRADER';document.getElementById('run').style.background=running?'#ef4444':'#00ff88';addLog(running?'▶️ STARTED':'⏹️ STOPPED');}
document.getElementById('stopLoss').addEventListener('input',updateSLTPDisplay);
document.getElementById('takeProfit').addEventListener('input',updateSLTPDisplay);
setM('touchnotouch');updateSLTPDisplay();
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
        bot.reply_to(m, "TITAN V16.5 - User sets own SL/TP\\nhttps://titan-digits.vercel.app", disable_web_page_preview=False)

if __name__ == '__main__':
    app.run()
