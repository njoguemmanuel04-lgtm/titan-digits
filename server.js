const express = require('express');
const WebSocket = require('ws');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 10000;

app.use(express.json());
app.use(express.static(__dirname));

/*
  TITAN -> Render -> Deriv
  SSE endpoint used by index.html
*/
app.get('/api/tick', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  let closed = false;

  const send = (data) => {
    if (!closed) {
      res.write(`data: ${JSON.stringify(data)}\n\n`);
    }
  };

  send({
    log: "Connecting Titan to Deriv..."
  });

  const deriv = new WebSocket(
    "wss://ws.binaryws.com/websockets/v3?app_id=1089"
  );

  deriv.on("open", () => {
    send({
      log: "Connected to Deriv"
    });

    deriv.send(
      JSON.stringify({
        ticks: "R_100",
        subscribe: 1
      })
    );
  });

  deriv.on("message", (data) => {
    try {
      const message = JSON.parse(data.toString());
      send(message);
    } catch (error) {
      send({
        error: "Invalid Deriv response"
      });
    }
  });

  deriv.on("error", (error) => {
    console.error("Deriv WebSocket error:", error.message);
    send({
      error: "Deriv connection error",
      message: error.message
    });
  });

  deriv.on("close", () => {
    send({
      log: "Deriv connection closed"
    });
    if (!closed) {
      res.end();
    }
  });

  req.on("close", () => {
    closed = true;
    try {
      deriv.close();
    } catch {}
    try {
      res.end();
    } catch {}
  });
});

/*
  Simple health check
*/
app.get("/health", (req, res) => {
  res.json({
    status: "online",
    titan: "V8.2",
    time: new Date().toISOString()
  });
});

/*
  Main Titan page
*/
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "index.html"));
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`TITAN V8.2 running on port ${PORT}`);
});
