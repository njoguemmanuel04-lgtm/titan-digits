const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');

const app = express();
const server = http.createServer(app);

const PORT = process.env.PORT || 10000;
const APP_ID = process.env.DERIV_APP_ID || '1089';

const DERIV_URL =
  `wss://ws.derivws.com/websockets/v3?app_id=${APP_ID}`;

app.use(express.json());
app.use(express.static(__dirname));

app.get('/health', (req, res) => {
  res.json({
    status: 'online',
    titan: 'V8.7',
    deriv_proxy: true,
    time: new Date().toISOString()
  });
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

/*
  TITAN -> RENDER -> DERIV

  The phone connects to Render.
  Render connects to Deriv.
*/

const derivProxy = new WebSocket.Server({
  noServer: true
});

derivProxy.on('connection', (client) => {

  let upstream;

  function send(data) {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(data));
    }
  }

  send({
    type: 'proxy',
    status: 'connecting',
    message: 'Render is connecting Titan to Deriv...'
  });

  try {

    upstream = new WebSocket(DERIV_URL);

    upstream.on('open', () => {

      send({
        type: 'proxy',
        status: 'connected',
        message: 'Render connected to Deriv'
      });

    });

    upstream.on('message', (data) => {

      if (client.readyState === WebSocket.OPEN) {
        client.send(data.toString());
      }

    });

    upstream.on('error', (error) => {

      console.error(
        'Deriv upstream error:',
        error.message
      );

      send({
        type: 'proxy',
        status: 'error',
        message: 'Render could not reach Deriv'
      });

    });

    upstream.on('close', (code, reason) => {

      send({
        type: 'proxy',
        status: 'closed',
        message: 'Deriv connection closed',
        code: code,
        reason: reason
          ? reason.toString()
          : ''
      });

      if (client.readyState === WebSocket.OPEN) {
        client.close();
      }

    });

    client.on('message', (data) => {

      if (
        !upstream ||
        upstream.readyState !== WebSocket.OPEN
      ) {

        send({
          type: 'proxy',
          status: 'waiting',
          message: 'Waiting for Deriv connection...'
        });

        return;
      }

      upstream.send(data.toString());

    });

    client.on('close', () => {

      try {
        if (upstream) {
          upstream.close();
        }
      } catch {}

    });

    client.on('error', () => {

      try {
        if (upstream) {
          upstream.close();
        }
      } catch {}

    });

  } catch (error) {

    send({
      type: 'proxy',
      status: 'error',
      message: 'Could not create Deriv connection'
    });

    try {
      client.close();
    } catch {}

  }

});

server.on('upgrade', (request, socket, head) => {

  const url = new URL(
    request.url,
    `http://${request.headers.host}`
  );

  if (url.pathname !== '/deriv') {
    socket.destroy();
    return;
  }

  derivProxy.handleUpgrade(
    request,
    socket,
    head,
    (client) => {
      derivProxy.emit(
        'connection',
        client,
        request
      );
    }
  );

});

server.listen(PORT, '0.0.0.0', () => {

  console.log(
    `TITAN V8.7 running on port ${PORT}`
  );

  console.log(
    `Deriv proxy enabled: ${DERIV_URL}`
  );

});
