const express = require('express');
const { WebSocketServer } = require('ws');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 10000;

app.use(express.static(__dirname));

app.get('/api/ping', (req,res)=>res.json({ok:true}));

const server = app.listen(PORT, ()=> console.log('TITAN V8 LIVE on '+PORT));
const wss = new WebSocketServer({ server, path: '/ticks' });

wss.on('connection', (client)=>{
  console.log('Client connected');
  const WebSocket = require('ws');
  const deriv = new WebSocket('wss://ws.binaryws.com/websockets/v3?app_id=1089', {
    headers: { Origin: 'https://app.deriv.com' }
  });
  deriv.on('open', ()=>{
    console.log('Deriv open');
    deriv.send(JSON.stringify({ticks:'R_100'}));
  });
  deriv.on('message', (data)=>{
    if(client.readyState===1) client.send(data.toString());
  });
  client.on('message', (msg)=>{ 
    try{ deriv.send(msg.toString()); }catch{}
  });
  client.on('close', ()=>{ try{deriv.close()}catch{} });
  deriv.on('close', ()=>{ try{client.close()}catch{} });
});

app.get('/', (req,res)=> res.sendFile(path.join(__dirname,'index.html')));
