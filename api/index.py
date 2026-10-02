<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TITAN V16.1 SMART BARRIER</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{font-family:monospace;background:#050508;color:#fff}.mode-active{background:#00ff88;color:#000!important}.mode-forex-active{background:#00aaff;color:#fff!important}</style>
</head>
<body class="p-2 max-w-6xl mx-auto">
<div class="bg-[#0a0a0f] border border-purple-500/30 rounded-xl p-3 mb-2">
<input id="token" type="password" placeholder="Deriv API Token" class="w-full bg-black border border-gray-700 rounded-lg px-3 py-2 text-xs mb-2">
<div class="grid grid-cols-2 gap-2">
<select id="symbol" class="bg-black border border-gray-700 rounded-lg px-2 py-2 text-xs"><option value="R_10">R_10</option><option value="frxEURUSD">EUR/USD</option></select>
<select id="duration" class="bg-black border border-gray-700 rounded-lg px-2 py-2 text-xs"><option value="5t">5 Ticks</option><option value="5m">5 Min</option></select>
</div>
<button onclick="connect()" class="w-full mt-2 bg-[#00ff88] text-black font-black px-4 py-2 rounded-lg text-xs">CONNECT REAL - SMART S/R</button>
<div class="grid grid-cols-2 gap-2 mt-2 text-[10px]"><div id="support" class="bg-green-900/20 border border-green-500/40 rounded p-2">SUPPORT: --</div><div id="resistance" class="bg-red-900/20 border border-red-500/40 rounded p-2">RESISTANCE: --</div></div>
<div id="smartBarrierDisplay" class="text-[10px] text-purple-400 mt-1">SMART BARRIERS: AUTO</div>
</div>
<div class="grid grid-cols-4 gap-2 mb-2">
<button onclick="setM('differs')" id="m-differs" class="mode-active border rounded-xl py-2 text-[10px]">DIFFERS</button>
<button onclick="setM('evenodd')" id="m-evenodd" class="bg-[#0a0a0f] border border-gray-800 rounded-xl py-2 text-[10px]">EVEN/ODD</button>
<button onclick="setM('touchnotouch')" id="m-touchnotouch" class="mode-forex-active border border-purple-500 rounded-xl py-2 text-[10px]">SMART TOUCH</button>
<button onclick="setM('risefall')" id="m-risefall" class="bg-[#0a0a0f] border border-blue-500/30 rounded-xl py-2 text-[10px]">RISE/FALL</button>
</div>
<div class="bg-[#0a0a0f] border border-gray-800 rounded-xl p-3">
<div id="sig" class="font-black text-[12px]">WAITING SMART</div>
<div id="price" class="text-[11px]">Price: -</div>
<div id="ticks" class="flex gap-1 flex-wrap mt-2"></div>
<div class="relative bg-black rounded h-[70px] mt-2">
<div id="barrierLineUp" class="absolute w-full border-t border-dashed border-purple-400 text-[8px]" style="top:20%">UP</div>
<div id="barrierLineDown" class="absolute w-full border-t border-dashed border-green-400 text-[8px]" style="top:80%">DOWN</div>
<div id="currentPriceLine" class="absolute w-full border-t border-white/50 text-[8px]" style="top:50%">PRICE</div>
</div>
<button id="run" onclick="toggle()" class="w-full mt-3 bg-[#00ff88] text-black font-black rounded-xl py-3">RUN SMART</button>
</div>
<script>
let prices=[],ticks=[],ws=null,connected=false,running=false,mode='touchnotouch',support=0,resistance=0,smartUpper=0,smartLower=0;
function setM(m){mode=m;document.querySelectorAll('[id^=m-]').forEach(b=>{b.classList.remove('mode-active','mode-forex-active')});document.getElementById('m-'+m).classList.add(m==='touchnotouch'||m==='risefall'?'mode-forex-active':'mode-active');}
function calcRSI(a,p=14){if(a.length<p+1)return 50;let g=0,l=0;for(let i=a.length-p;i<a.length;i++){let d=a[i]-a[i-1];if(d>0)g+=d;else l+=-d;}return l===0?70:100-(100/(1+g/l));}
function findSR(arr){if(arr.length<20)return null;let last=arr.slice(-50);let max=Math.max(...last),min=Math.min(...last);let rh=[],rl=[];for(let i=1;i<last.length-1;i++){if(last[i]>last[i-1]&&last[i]>last[i+1])rh.push(last[i]);if(last[i]<last[i-1]&&last[i]<last[i+1])rl.push(last[i]);}let res=rh.length?Math.max(...rh.slice(-3)):max,sup=rl.length?Math.min(...rl.slice(-3)):min,range=res-sup,buf=range*0.15||0.0002;return{support:sup,resistance:res,smartUpper:res+buf,smartLower:sup-buf,range};}
function connect(){let t=document.getElementById('token').value.trim();if(!t){alert('token');return;}let s=document.getElementById('symbol').value;if(ws)ws.close();ws=new WebSocket('wss://ws.binaryws.com/websockets/v3?app_id=1089');ws.onopen=()=>{ws.send(JSON.stringify({authorize:t}));};ws.onmessage=e=>{let d=JSON.parse(e.data);if(d.msg_type==='authorize'){connected=true;ws.send(JSON.stringify({ticks:s,subscribe:1}));}if(d.msg_type==='tick'){let p=parseFloat(d.tick.quote);prices.push(p);ticks.push(parseInt(p.toString().slice(-1)));if(prices.length>150)prices.shift();let rsi=calcRSI(prices);let sr=findSR(prices);if(sr){support=sr.support;resistance=sr.resistance;smartUpper=sr.smartUpper;smartLower=sr.smartLower;document.getElementById('support').innerHTML=`SUPPORT ${support.toFixed(5)} LOWER ${smartLower.toFixed(5)}`;document.getElementById('resistance').innerHTML=`RESISTANCE ${resistance.toFixed(5)} UPPER ${smartUpper.toFixed(5)}`;document.getElementById('smartBarrierDisplay').innerText=`SMART U:${smartUpper.toFixed(5)} L:${smartLower.toFixed(5)}`;}document.getElementById('price').innerText=`Price ${p.toFixed(5)} RSI ${rsi.toFixed(1)}`;let sig='WAITING';if(mode==='touchnotouch'&&sr){if(rsi>68&&p>=sr.resistance*0.999)sig=`SMART TOUCH DOWN ${sr.smartLower.toFixed(5)}`;else if(rsi<32&&p<=sr.support*1.001)sig=`SMART TOUCH UP ${sr.smartUpper.toFixed(5)}`;else if(rsi>60)sig=`SMART TOUCH UP ${sr.smartUpper.toFixed(5)}`;else sig=`SMART NO TOUCH ${sr.smartUpper.toFixed(5)}`;document.getElementById('sig').innerText=sig;}if(running&&sr)trade(p,sr);}};}
let can=true;function trade(price,sr){if(!can)return;let sig=document.getElementById('sig').innerText;if(sig.includes('WAITING'))return;can=false;let stake=0.5,sym=document.getElementById('symbol').value,type='ONETOUCH',bar=sig.match(/\d+\.\d+/)?.[0]||'';if(sig.includes('NO TOUCH'))type='NOTOUCH';let params={amount:stake,basis:'stake',contract_type:type,currency:'USD',duration:5,duration_unit:'t',symbol:sym,barrier:bar};ws.send(JSON.stringify({buy:1,price:stake,parameters:params}));setTimeout(()=>can=true,5000);}
function toggle(){if(!connected){alert('connect');return;}running=!running;document.getElementById('run').innerText=running?'STOP SMART':'RUN SMART';}
</script>
</body>
</html>
