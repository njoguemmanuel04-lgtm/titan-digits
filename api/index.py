import os
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from http.server import BaseHTTPRequestHandler


API_BASE = "https://api.derivws.com"
DERIV_APP_ID = os.environ.get("DERIV_APP_ID", "")


def deriv_request(method, url, token):
    headers = {
        "Authorization": "Bearer " + token,
        "Deriv-App-ID": DERIV_APP_ID,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    req = Request(url, method=method, headers=headers)

    try:
        with urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw)

    except HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")

        try:
            data = json.loads(raw)
        except Exception:
            data = {"error": raw or str(e)}

        return e.code, data

    except URLError as e:
        return 503, {
            "error": "Could not reach Deriv API: " + str(e.reason)
        }

    except Exception as e:
        return 500, {
            "error": str(e)
        }


def error_message(data):
    if isinstance(data, dict):

        if data.get("error"):
            return str(data["error"])

        errors = data.get("errors")

        if isinstance(errors, list) and errors:
            first = errors[0]

            if isinstance(first, dict):
                return first.get(
                    "message",
                    first.get("code", "Deriv API error")
                )

            return str(first)

        if data.get("message"):
            return str(data["message"])

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

        if self.path != "/api/deriv-auth":
            self.send_json(404, {
                "ok": False,
                "error": "Endpoint not found"
            })
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))

            if length <= 0 or length > 50000:
                self.send_json(400, {
                    "ok": False,
                    "error": "Invalid request"
                })
                return

            raw = self.rfile.read(length).decode("utf-8")
            body = json.loads(raw)

            token = str(body.get("token", "")).strip()

            if not token:
                self.send_json(400, {
                    "ok": False,
                    "error": "PAT is required"
                })
                return

            if not DERIV_APP_ID:
                self.send_json(500, {
                    "ok": False,
                    "error": "DERIV_APP_ID is not configured in Vercel"
                })
                return

            # --------------------------------------------------
            # STEP 1: GET OPTIONS ACCOUNTS
            # --------------------------------------------------

            status, accounts_result = deriv_request(
                "GET",
                API_BASE + "/trading/v1/options/accounts",
                token
            )

            if status != 200:

                self.send_json(status, {
                    "ok": False,
                    "error": error_message(accounts_result),
                    "stage": "accounts"
                })
                return

            accounts = accounts_result.get("data", [])

            if isinstance(accounts, dict):
                accounts = [accounts]

            if not isinstance(accounts, list) or not accounts:
                self.send_json(404, {
                    "ok": False,
                    "error": "No Options trading account found",
                    "stage": "accounts"
                })
                return

            # --------------------------------------------------
            # PREFER DEMO ACCOUNT
            # --------------------------------------------------

            demo_accounts = [
                a for a in accounts
                if str(a.get("account_type", "")).lower() == "demo"
            ]

            if demo_accounts:
                account = demo_accounts[0]
            else:
                account = accounts[0]

            account_id = account.get("account_id")

            if not account_id:
                self.send_json(500, {
                    "ok": False,
                    "error": "Deriv account ID was not returned",
                    "stage": "accounts"
                })
                return

            # --------------------------------------------------
            # STEP 2: REQUEST ONE-TIME PASSWORD / WS URL
            # --------------------------------------------------

            otp_url = (
                API_BASE
                + "/trading/v1/options/accounts/"
                + str(account_id)
                + "/otp"
            )

            otp_status, otp_result = deriv_request(
                "POST",
                otp_url,
                token
            )

            if otp_status not in (200, 201):

                self.send_json(otp_status, {
                    "ok": False,
                    "error": error_message(otp_result),
                    "stage": "otp"
                })
                return

            otp_data = otp_result.get("data", {})

            if not isinstance(otp_data, dict):
                otp_data = {}

            ws_url = otp_data.get("url")

            if not ws_url:
                self.send_json(500, {
                    "ok": False,
                    "error": "Deriv did not return an authenticated WebSocket URL",
                    "stage": "otp"
                })
                return

            # --------------------------------------------------
            # SUCCESS
            # --------------------------------------------------

            self.send_json(200, {
                "ok": True,
                "account_id": account_id,
                "account_type": account.get("account_type", ""),
                "balance": account.get("balance", 0),
                "currency": account.get("currency", "USD"),
                "ws_url": ws_url
            })

        except json.JSONDecodeError:
            self.send_json(400, {
                "ok": False,
                "error": "Invalid JSON request"
            })

        except Exception as e:
            self.send_json(500, {
                "ok": False,
                "error": str(e)
            })

    def do_GET(self):

        html = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport"
content="width=device-width,initial-scale=1.0">

<title>TITAN V35 - DERIV CONNECT FIX</title>

<script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-[#0f172a] text-white p-3">

<div class="max-w-md mx-auto">

<h1 class="text-center font-black text-emerald-400">
TITAN V35
</h1>

<div class="text-center text-xs text-cyan-400 mb-2">
PAT + OTP CONNECTION
</div>

<div
id="lastDigit"
class="text-center text-7xl font-black text-emerald-400 my-3">
-
</div>

<div
id="tickInfo"
class="text-center text-xs text-cyan-400">
PASTE TOKEN & TAP CONNECT
</div>

<div
class="grid grid-cols-5 gap-2 my-3"
id="digitGrid">
</div>

<div
class="flex justify-between text-xs bg-slate-800 p-2 rounded-xl mb-2">

<span>
History:<b id="histCount">0</b>
</span>

<span>
CONF:<b id="conf">0</b>%
</span>

<span id="scanStatus">
WAITING
</span>

</div>

<div
class="bg-slate-800 rounded-xl p-3 mb-3 border border-emerald-500/30">

<div
id="scanDetails"
class="text-[11px] text-gray-300">
Waiting for ticks...
</div>

<div
id="bestMarket"
class="text-sm font-bold text-yellow-400 mt-1">
</div>

</div>

<div
id="dotStatus"
class="text-center text-xs mb-3 p-2 rounded-xl bg-slate-800">
🔴 NOT CONNECTED - Paste token below
</div>

<input
id="token"
type="password"
placeholder="Paste Deriv PAT here"
class="w-full bg-slate-900 border border-slate-700 p-4 rounded-xl text-center text-sm mb-2">

<button
onclick="connectNow()"
id="connectButton"
class="w-full bg-blue-600 hover:bg-blue-500 font-black py-4 rounded-xl mb-2 text-base">

🔌 CONNECT NOW

</button>

<button
onclick="toggleToken()"
class="w-full bg-slate-700 font-bold py-2 rounded-xl mb-4 text-xs">

👁️ Show / Hide Token

</button>

<div class="grid grid-cols-4 gap-2 mb-3">

<div class="text-center">
<div class="text-[10px] text-gray-400">
STAKE
</div>
<input
id="stake"
value="1"
class="w-full bg-slate-800 p-2 rounded-xl text-center">
</div>

<div class="text-center">
<div class="text-[10px] text-gray-400">
MARTIN
</div>
<input
id="martingale"
value="2.1"
class="w-full bg-slate-800 p-2 rounded-xl text-center">
</div>

<div class="text-center">
<div class="text-[10px] text-gray-400">
TP $
</div>
<input
id="tp"
value="10"
class="w-full bg-slate-800 p-2 rounded-xl text-center border border-emerald-500">
</div>

<div class="text-center">
<div class="text-[10px] text-gray-400">
SL $
</div>
<input
id="sl"
value="20"
class="w-full bg-slate-800 p-2 rounded-xl text-center border border-red-500">
</div>

</div>

<button
onclick="startTrading()"
class="w-full bg-gradient-to-r from-emerald-400 to-cyan-400 text-black font-black py-4 rounded-xl mb-2">

🧠 ONE BUTTON SCAN & TRADE

</button>

<div class="grid grid-cols-2 gap-2 mb-3">

<button
onclick="stopTrading()"
class="bg-red-600 font-bold py-3 rounded-xl">

⏹️ STOP

</button>

<button
onclick="clearLog()"
class="bg-slate-800 font-bold py-3 rounded-xl">

🧹 CLEAR

</button>

</div>

<div class="text-center text-xs bg-black/50 p-2 rounded-xl">

<span id="balance">
Bal:$0.00
</span>

|

<span id="profit" class="font-bold">
P:$0.00
</span>

|

<span id="wins">
W:0
</span>

<span id="loss">
L:0
</span>

<br>

Next:

<span
id="nextStake"
class="text-yellow-400">
$1
</span>

|

<span id="tradeStatus">
HOLD
</span>

</div>

<div
id="log"
class="bg-black/80 rounded-xl p-2 mt-3 h-72 overflow-y-auto text-[11px] font-mono border border-slate-700">
</div>

</div>


<script>

let history = [];
let counts = Array(10).fill(0);

let ws = null;

let trading = false;
let dotConnected = false;
let awaitingResult = false;

let nextStake = 1;
let profit = 0;
let wins = 0;
let losses = 0;
let balance = 0;

let pendingBuy = false;
let pendingStake = 0;

let contractId = null;


const grid =
document.getElementById("digitGrid");


for(let i=0;i<10;i++){

    let d=document.createElement("div");

    d.className=
    "bg-slate-800 rounded-xl p-2 text-center";

    d.innerHTML=
    `<div class="font-black">${i}</div>
     <div class="text-[10px]" id="pct${i}">0%</div>`;

    grid.appendChild(d);
}


function logM(message){

    let l=document.getElementById("log");

    let time =
    new Date().toLocaleTimeString();

    l.innerHTML +=
    `[${time}] ${message}<br>`;

    l.scrollTop =
    l.scrollHeight;
}


function updateGrid(){

    let total =
    history.length || 1;

    for(let i=0;i<10;i++){

        document.getElementById(
            `pct${i}`
        ).innerText =
        Math.round(
            counts[i] / total * 100
        ) + "%";
    }
}


function runScanner(){

    if(history.length < 20){

        document.getElementById(
            "scanStatus"
        ).innerText =
        `COLLECT ${history.length}/20`;

        document.getElementById(
            "scanDetails"
        ).innerText =
        `Collecting ticks... ${history.length}/20`;

        return null;
    }


    let total =
    history.length;


    let over2 =
    history.filter(
        d => d > 2
    ).length;


    let over2Pct =
    Math.round(
        over2 / total * 100
    );


    let under2Pct =
    100 - over2Pct;


    let over4 =
    history.filter(
        d => d > 4
    ).length;


    let over4Pct =
    Math.round(
        over4 / total * 100
    );


    document.getElementById(
        "scanDetails"
    ).innerText =
    `Over2:${over2Pct}% ` +
    `Under2:${under2Pct}% | ` +
    `Over4:${over4Pct}%`;


    let opps=[];


    if(over2Pct >= 76){

        opps.push({
            market:"DIGITOVER",
            barrier:2,
            conf:over2Pct,
            type:`Over2 ${over2Pct}%`
        });

    }


    if(under2Pct >= 76){

        opps.push({
            market:"DIGITUNDER",
            barrier:2,
            conf:under2Pct,
            type:`Under2 ${under2Pct}%`
        });

    }


    if(over4Pct >= 70){

        opps.push({
            market:"DIGITOVER",
            barrier:4,
            conf:over4Pct,
            type:`Over4 ${over4Pct}%`
        });

    }


    opps.sort(
        (a,b) => b.conf - a.conf
    );


    let best =
    opps[0];


    if(best){

        document.getElementById(
            "scanStatus"
        ).innerText =
        "✅ FAVOURABLE";


        document.getElementById(
            "conf"
        ).innerText =
        best.conf;


        document.getElementById(
            "bestMarket"
        ).innerText =
        `🎯 ${best.type} → ${best.market} ${best.barrier}`;


        document.getElementById(
            "tradeStatus"
        ).innerText =
        `READY ${best.type}`;


        return best;

    }


    document.getElementById(
        "scanStatus"
    ).innerText =
    "⏸️ HOLD";


    document.getElementById(
        "bestMarket"
    ).innerText =
    "No high CONF - HOLD";


    document.getElementById(
        "tradeStatus"
    ).innerText =
    "HOLD";


    return null;
}


async function connectNow(){

    let token =
    document.getElementById(
        "token"
    ).value.trim();


    if(!token){

        logM(
            "❌ PASTE TOKEN FIRST"
        );

        return;
    }


    if(ws){

        try{
            ws.close();
        }catch(e){}
    }


    dotConnected=false;


    document.getElementById(
        "connectButton"
    ).innerText =
    "⏳ CONNECTING...";


    document.getElementById(
        "dotStatus"
    ).innerText =
    "🟡 GETTING DERIV ACCOUNT...";


    logM(
        "🔐 Starting PAT authentication..."
    );


    try{

        /*
         * IMPORTANT:
         * The PAT is sent to our HTTPS backend.
         * We do NOT put the PAT into a WebSocket URL.
         */

        let response =
        await fetch(
            "/api/deriv-auth",
            {
                method:"POST",

                headers:{
                    "Content-Type":
                    "application/json"
                },

                body:JSON.stringify({
                    token:token
                })
            }
        );


        let raw =
        await response.text();


        let data;


        try{

            data =
            JSON.parse(raw);

        }catch(e){

            throw new Error(
                "Server returned invalid response: " +
                raw.slice(0,150)
            );
        }


        if(!response.ok || !data.ok){

            throw new Error(
                data.error ||
                "Deriv authentication failed"
            );
        }


        logM(
            `✅ ACCOUNT ${data.account_id}`
        );


        logM(
            `💰 ${data.account_type.toUpperCase()} ` +
            `${data.currency} ${data.balance}`
        );


        if(!data.ws_url){

            throw new Error(
                "No authenticated WebSocket URL returned"
            );
        }


        /*
         * The URL is generated by Deriv's OTP endpoint.
         */

        logM(
            "🔑 OTP WebSocket URL received"
        );


        connectAuthenticatedWS(
            data.ws_url
        );


        /*
         * Remember PAT locally.
         * This is convenient but users should
         * understand localStorage is not a vault.
         */

        localStorage.setItem(
            "deriv_token",
            token
        );


        logM(
            "💾 Token remembered on this device"
        );


    }catch(error){

        logM(
            "❌ AUTH ERROR: " +
            error.message
        );


        document.getElementById(
            "dotStatus"
        ).innerText =
        "🔴 NOT CONNECTED";


        document.getElementById(
            "connectButton"
        ).innerText =
        "🔌 CONNECT NOW";
    }
}


function connectAuthenticatedWS(wsUrl){

    try{

        ws =
        new WebSocket(wsUrl);

    }catch(error){

        logM(
            "❌ WS CREATE ERROR: " +
            error.message
        );

        return;
    }


    ws.onopen = function(){

        logM(
            "🟢 AUTHENTICATED WS CONNECTED"
        );


        dotConnected=true;


        document.getElementById(
            "dotStatus"
        ).innerText =
        "🟢 CONNECTED TO DERIV";


        document.getElementById(
            "dotStatus"
        ).className =
        "text-center text-xs mb-3 p-2 rounded-xl " +
        "bg-emerald-900/50 border border-emerald-500";


        document.getElementById(
            "connectButton"
        ).innerText =
        "✅ CONNECTED";


        /*
         * Balance subscription
         */

        ws.send(
            JSON.stringify({
                balance:1,
                subscribe:1,
                req_id:1
            })
        );


        /*
         * R_10 live ticks
         */

        ws.send(
            JSON.stringify({
                ticks:"R_10",
                subscribe:1,
                req_id:2
            })
        );


        logM(
            "📡 R_10 TICK STREAM STARTED"
        );

    };


    ws.onmessage = function(event){

        let data;


        try{

            data =
            JSON.parse(event.data);

        }catch(e){

            return;
        }


        /*
         * BALANCE
         */

        if(data.msg_type === "balance"){

            if(data.balance){

                balance =
                Number(
                    data.balance.balance
                );


                document.getElementById(
                    "balance"
                ).innerText =
                `Bal:$${balance.toFixed(2)}`;
            }

        }


        /*
         * TICK
         */

        if(data.msg_type === "tick"){

            if(!data.tick){
                return;
            }


            let quote =
            Number(
                data.tick.quote
            );


            let digit =
            Number(
                String(
                    data.tick.quote
                ).slice(-1)
            );


            history.push(digit);

            counts[digit]++;


            if(history.length > 100){

                let removed =
                history.shift();

                counts[removed]--;
            }


            document.getElementById(
                "lastDigit"
            ).innerText =
            digit;


            document.getElementById(
                "tickInfo"
            ).innerText =
            `LIVE ${quote} | LAST:${digit}`;


            document.getElementById(
                "histCount"
            ).innerText =
            history.length;


            updateGrid();


            let best =
            runScanner();


            if(
                best &&
                trading &&
                !awaitingResult &&
                !pendingBuy
            ){

                doTrade(best);
            }

        }


        /*
         * PROPOSAL
         */

        if(
            data.msg_type === "proposal" &&
            pendingBuy
        ){

            if(
                data.proposal &&
                data.proposal.id
            ){

                let proposalId =
                data.proposal.id;


                let ask =
                Number(
                    data.proposal.ask_price
                );


                logM(
                    `📤 PROPOSAL $${ask.toFixed(2)}`
                );


                ws.send(
                    JSON.stringify({
                        buy:proposalId,
                        price:ask,
                        req_id:20
                    })
                );
            }

        }


        /*
         * BUY
         */

        if(
            data.msg_type === "buy" &&
            data.buy
        ){

            pendingBuy=false;


            contractId =
            data.buy.contract_id;


            awaitingResult=true;


            logM(
                `📈 BOUGHT ${contractId} ` +
                `$${pendingStake.toFixed(2)}`
            );


            ws.send(
                JSON.stringify({
                    proposal_open_contract:1,
                    contract_id:contractId,
                    subscribe:1,
                    req_id:21
                })
            );

        }


        /*
         * CONTRACT RESULT
         */

        if(
            data.msg_type ===
            "proposal_open_contract" &&
            data.proposal_open_contract
        ){

            let contract =
            data.proposal_open_contract;


            if(
                contract.is_sold ||
                contract.status === "sold"
            ){

                let p =
                Number(
                    contract.profit || 0
                );


                profit += p;


                if(p > 0){

                    wins++;

                    nextStake =
                    Number(
                        document.getElementById(
                            "stake"
                        ).value
                    );

                }else{

                    losses++;

                    nextStake =
                    nextStake *
                    Number(
                        document.getElementById(
                            "martingale"
                        ).value
                    );
                }


                document.getElementById(
                    "profit"
                ).innerText =
                `P:$${profit.toFixed(2)}`;


                document.getElementById(
                    "wins"
                ).innerText =
                `W:${wins}`;


                document.getElementById(
                    "loss"
                ).innerText =
                `L:${losses}`;


                document.getElementById(
                    "nextStake"
                ).innerText =
                `$${nextStake.toFixed(2)}`;


                if(p > 0){

                    logM(
                        `✅ WIN +$${p.toFixed(2)} ` +
                        `| Profit:$${profit.toFixed(2)}`
                    );

                }else{

                    logM(
                        `❌ LOSS $${p.toFixed(2)} ` +
                        `| Profit:$${profit.toFixed(2)}`
                    );
                }


                let tp =
                Number(
                    document.getElementById(
                        "tp"
                    ).value
                );


                let sl =
                Number(
                    document.getElementById(
                        "sl"
                    ).value
                );


                if(profit >= tp){

                    trading=false;

                    logM(
                        `🎯 TP HIT $${profit.toFixed(2)} - STOPPED`
                    );
                }


                if(profit <= -sl){

                    trading=false;

                    logM(
                        `🛑 SL HIT $${profit.toFixed(2)} - STOPPED`
                    );
                }


                awaitingResult=false;
                contractId=null;
            }

        }


        /*
         * DERIV ERROR
         */

        if(data.error){

            logM(
                "❌ DERIV: " +
                data.error.message
            );


            pendingBuy=false;
            awaitingResult=false;
        }

    };


    ws.onerror = function(){

        dotConnected=false;


        document.getElementById(
            "dotStatus"
        ).innerText =
        "🔴 WEBSOCKET ERROR";


        document.getElementById(
            "connectButton"
        ).innerText =
        "🔌 CONNECT NOW";


        logM(
            "❌ AUTHENTICATED WS ERROR"
        );

    };


    ws.onclose = function(){

        dotConnected=false;


        document.getElementById(
            "dotStatus"
        ).innerText =
        "🔴 CONNECTION CLOSED";


        document.getElementById(
            "connectButton"
        ).innerText =
        "🔌 CONNECT NOW";


        logM(
            "🔴 DERIV WS CLOSED"
        );
    };
}


function doTrade(best){

    if(!dotConnected){

        logM(
            "❌ NOT CONNECTED"
        );

        return;
    }


    if(awaitingResult || pendingBuy){

        return;
    }


    let stake =
    Number(
        nextStake
    );


    if(!Number.isFinite(stake) || stake <= 0){

        logM(
            "❌ Invalid stake"
        );

        return;
    }


    /*
     * IMPORTANT:
     * Current API uses underlying_symbol,
     * NOT symbol.
     */

    let request = {

        proposal:1,

        amount:stake,

        basis:"stake",

        contract_type:
        best.market,

        currency:"USD",

        underlying_symbol:"R_10",

        duration:1,

        duration_unit:"t",

        barrier:String(
            best.barrier
        ),

        req_id:10
    };


    pendingBuy=true;

    pendingStake=stake;


    logM(
        `🎯 TRADE ${best.type} ` +
        `Stake:$${stake.toFixed(2)} ` +
        `CONF:${best.conf}%`
    );


    ws.send(
        JSON.stringify(request)
    );
}


function startTrading(){

    if(!dotConnected){

        logM(
            "🔌 Connect to Deriv first"
        );

        connectNow();

        return;
    }


    trading=true;


    logM(
        "🧠 SMART SCAN & TRADE STARTED"
    );
}


function stopTrading(){

    trading=false;

    pendingBuy=false;

    logM(
        "⏹️ STOPPED"
    );
}


function clearLog(){

    document.getElementById(
        "log"
    ).innerHTML="";
}


function toggleToken(){

    let t =
    document.getElementById(
        "token"
    );


    t.type =
    t.type === "password"
    ? "text"
    : "password";
}


/*
 * LOAD REMEMBERED PAT
 */

window.onload=function(){

    let saved =
    localStorage.getItem(
        "deriv_token"
    );


    if(saved){

        document.getElementById(
            "token"
        ).value =
        saved;


        logM(
            "💾 Token loaded from memory"
        );

    }else{

        logM(
            "👋 Paste your Deriv PAT"
        );
    }
};

</script>

</body>
</html>
"""

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.end_headers()

        self.wfile.write(
            html.encode("utf-8")
        )
