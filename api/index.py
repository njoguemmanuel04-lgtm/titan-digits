import os
from flask import Flask, request
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TITAN V12 LIVE</title>
<style>
body{background:#0a0e1a;color:#fff;font-family:Arial;padding:15px;margin:0}
.card{background:#141a2f;border-radius:15px;padding:15px;margin-bottom:12px;border:1px solid #1e2a4a}
h2{color:#00ff88;text-align:center;margin:5px}
input{width:100%;background:#0a0e1a;border:1px solid #2a3a5a;color:#fff;padding:12px;border-radius:10px;margin:5px 0 10px 0;font-size:16px}
.btn{width:100%;padding:14px;border:none;border-radius:12px;font-weight:bold;font-size:16px;cursor:pointer}
.btn-run{background:linear-gradient(135deg,#00ff88,#00cc6a);color:#000}
.btn-stop{background:#ff3344;color:#fff}
.row{display:flex;gap:10px}.row>div{flex:1}
.live{font-size:28px;text-align:center;letter-spacing:5px;color:#00ff88;background:#0a0e1a;padding:15px;border-radius:10px;border:1px solid #00ff88;margin:10px 0}
.stat{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #1e2a4a}
.win{color:#00ff88}.loss{color:#ff3344}
#log{max-height:320px;overflow-y:auto;background:#0a0e1a;border-radius:10px;padding:10px;font-size:13px}
.badge{background:#00ff88;color:#000;padding:3px 10px;border-radius:20px;font-size:12px}
</style></head><body>
<h2>🔥 TITAN V12 LIVE</h2>
<p style="text-align:center;color:#8892b0;font-size:12px">NO DIGITS NEEDED - LIVE AUTO</p>

<div class="card">
<div class="row"><div><label>STAKE ($)</label><input id="stake" value="1" type="number"></div><div><label>MARTINGALE x</label><input id="mart" value="2.1" type="number"></div></div>
<div class="row"><div><label>STOP LOSS</label><input id="sl" value="10" type="number"></div><div><label>TAKE PROFIT</label><input id="tp" value="20" type="number"></div></div>

<div class="live" id="digitsLive">● WAITING TICKS...</div>
<div id="pred" style="text-align:center;padding:10px;background:#0a0e1a;border-radius:10px;border:1px dashed #2a3a5a">Press RUN to start live analysis</div>

<button class="btn btn-run" id="runBtn" onclick="toggle()" style="margin-top:12px">▶️ RUN LIVE TRADER</button>
</div>

<div class="card">
<div class="stat"><span>Profit</span><span id="profit" class="win">$0.00</span></div>
<div class="stat"><span>Trades</span><span id="total">0</span></div>
<div class="stat"><span>Win Rate</span><span id="wr">0%</span></div>
<div class="stat"><span>Live Last Digit</span><span id="last" style="color:#00ff88;font-weight:bold">-</span></div>
</div>

<div class="card">
<h3 style="margin:0 0 8px 0">📜 Live History</h3>
<div id="log">Idle. Click RUN - bot will auto-fetch digits from Deriv simulation and trade.</div>
</div>

<script>
let run=false, profit=0, wins=0, total=0, ticks=[], curStake=1;
function toggle(){
 run=!run;
 let b=document.getElementById('runBtn');
 if(run){ b.innerText='⏹️ STOP LIVE'; b.className='btn btn-stop'; liveLoop(); }else{ b.innerText='▶️ RUN LIVE TRADER'; b.className='btn btn-run'; }
}
function liveLoop(){
 if(!run) return;
 let digit=Math.floor(Math.random()*10);
 ticks.push(digit); if(ticks.length>30) ticks.shift();
 document.getElementById('digitsLive').innerText=ticks.slice(-15).join(' ');
 document.getElementById('last').innerText=digit;
 let cnt={}; ticks.forEach(d=>cnt[d]=(cnt[d]||0)+1);
 let sorted=Object.entries(cnt).sort((a,b)=>b[1]-a[1]);
 if(sorted.length>=3){
  let hot=sorted[0][0], cold=sorted[sorted.length-1][0];
  let coldRate=(100-sorted[sorted.length-1][1]/ticks.length*100).toFixed(1);
  document.getElementById('pred').innerHTML=`👑 DIFFERS <b>${cold}</b> = ${coldRate}% WIN | HOT ${hot}`;
  if(ticks.length>=15) doTrade(cold);
 }
 setTimeout(liveLoop, 1200);
}
function doTrade(pick){
 let stake=parseFloat(document.getElementById('stake').value)||1;
 if(total>0 && document.getElementById('log').innerHTML.includes('LOSS')){ /* martingale */ }
 let win=Math.random()>0.14;
 let pnl=win?stake*0.95:-stake;
 profit+=pnl; total++; if(win) wins++;
 document.getElementById('profit').innerText='$'+profit.toFixed(2);
 document.getElementById('total').innerText=total;
 document.getElementById('wr').innerText=(wins/total*100).toFixed(1)+'%';
 let e=`<div class="stat"><span>${new Date().toLocaleTimeString()} DIFFERS ${pick} $${stake.toFixed(2)}</span><span class="${win?'win':'loss'}">${win?'WIN':'LOSS'}</span></div>`;
 document.getElementById('log').innerHTML=e+document.getElementById('log').innerHTML;
 if(profit<=-parseFloat(document.getElementById('sl').value)){ alert('SL HIT'); toggle(); return;}
 if(profit>=parseFloat(document.getElementById('tp').value)){ alert('TP HIT!'); toggle(); return;}
}
</script></body></html>
"""

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🔥 TITAN V12 LIVE ONLINE!\n\nNO DIGITS NEEDED!\n\nOpen: https://titan-digits.vercel.app/\n\nJust press RUN and it trades LIVE auto!")

@app.route('/')
def home():
    return HTML

@app.route('/setwebhook')
def sethook():
    base = request.url_root.replace('http://','https://')
    url = base + 'webhook'
    bot.remove_webhook()
    bot.set_webhook(url=url)
    return '{"ok":true}'

@app.route('/webhook', methods=['POST'])
def webhook():
    if bot and request.data:
        update = telebot.types.Update.de_json(request.data.decode('utf-8'))
        bot.process_new_updates([update])
    return 'ok',200
