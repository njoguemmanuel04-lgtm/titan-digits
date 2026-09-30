const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const dns = require('dns');

const app = express();
const server = http.createServer(app);

const PORT = process.env.PORT || 10000;

/*
  1089 is Deriv's public testing App ID.
  For production, use your own registered Deriv App ID.
*/
const APP_ID =
  process.env.DERIV_APP_ID || '1089';

const DERIV_URL =
  `wss://ws.derivws.com/websockets/v3?app_id=${APP_ID}`;

app.use(express.json());
app.use(express.static(__dirname));


/* =========================================================
   HEALTH
   ========================================================= */

app.get('/health', (req, res) => {

  res.json({

    status: 'online',

    titan: 'V8.7',

    deriv_proxy: true,

    deriv_endpoint: 'ws.derivws.com',

    time: new Date().toISOString()

  });

});


/* =========================================================
   MAIN PAGE
   ========================================================= */

app.get('/', (req, res) => {

  res.sendFile(
    path.join(__dirname, 'index.html')
  );

});


/* =========================================================
   DERIV PROXY
   ========================================================= */

const derivProxy =
  new WebSocket.Server({
    noServer: true
  });


derivProxy.on(
  'connection',
  (client) => {

    let upstream = null;

    let pingTimer = null;


    function send(data) {

      if (
        client.readyState ===
        WebSocket.OPEN
      ) {

        client.send(
          JSON.stringify(data)
        );

      }

    }


    send({

      type: 'proxy',

      status: 'connecting',

      message:
        'Render is connecting Titan to Deriv...'

    });


    /*
      Connect to Deriv.

      IPv4 is forced to avoid possible
      IPv6 routing problems.
    */

    try {

      upstream =
        new WebSocket(
          DERIV_URL,
          {
            family: 4,

            handshakeTimeout: 15000
          }
        );


      /* ==============================================
         DERIV CONNECTED
         ============================================== */

      upstream.on(
        'open',
        () => {

          console.log(
            'CONNECTED TO DERIV'
          );


          send({

            type: 'proxy',

            status: 'connected',

            message:
              'Render connected to Deriv'

          });


          /*
            Keep Deriv connection alive.
            Deriv recommends periodic activity
            on WebSocket sessions.
          */

          pingTimer =
            setInterval(
              () => {

                if (
                  upstream &&
                  upstream.readyState ===
                  WebSocket.OPEN
                ) {

                  upstream.send(
                    JSON.stringify({
                      ping: 1
                    })
                  );

                }

              },
              30000
            );

        }
      );


      /* ==============================================
         DERIV MESSAGE
         ============================================== */

      upstream.on(
        'message',
        (data) => {

          if (
            client.readyState ===
            WebSocket.OPEN
          ) {

            client.send(
              data.toString()
            );

          }

        }
      );


      /* ==============================================
         DERIV ERROR
         ============================================== */

      upstream.on(
        'error',
        (error) => {

          const message =
            error &&
            error.message
              ? error.message
              : 'Unknown WebSocket error';


          console.error(
            'DERIV ERROR:',
            message
          );


          send({

            type: 'proxy',

            status: 'error',

            message:
              'Deriv error: ' +
              message

          });

        }
      );


      /* ==============================================
         DERIV CLOSED
         ============================================== */

      upstream.on(
        'close',
        (code, reason) => {

          if (pingTimer) {

            clearInterval(
              pingTimer
            );

            pingTimer = null;

          }


          const closeReason =
            reason
              ? reason.toString()
              : '';


          console.log(
            'DERIV CLOSED:',
            code,
            closeReason
          );


          send({

            type: 'proxy',

            status: 'closed',

            message:
              'Deriv connection closed',

            code: code,

            reason:
              closeReason

          });


          if (
            client.readyState ===
            WebSocket.OPEN
          ) {

            client.close();

          }

        }
      );


      /* ==============================================
         PHONE → RENDER → DERIV
         ============================================== */

      client.on(
        'message',
        (data) => {

          if (
            !upstream ||
            upstream.readyState !==
            WebSocket.OPEN
          ) {

            send({

              type: 'proxy',

              status: 'waiting',

              message:
                'Waiting for Deriv connection...'

            });

            return;

          }


          try {

            upstream.send(
              data.toString()
            );

          } catch (error) {

            console.error(
              'FORWARD ERROR:',
              error.message
            );

          }

        }
      );


      /* ==============================================
         CLIENT CLOSED
         ============================================== */

      client.on(
        'close',
        () => {

          if (pingTimer) {

            clearInterval(
              pingTimer
            );

            pingTimer = null;

          }


          try {

            if (upstream) {

              upstream.close();

            }

          } catch (error) {}

        }
      );


      client.on(
        'error',
        () => {

          try {

            if (upstream) {

              upstream.close();

            }

          } catch (error) {}

        }
      );

    } catch (error) {

      console.error(
        'CREATE DERIV SOCKET ERROR:',
        error.message
      );


      send({

        type: 'proxy',

        status: 'error',

        message:
          'Could not create Deriv connection: ' +
          error.message

      });


      try {

        client.close();

      } catch (e) {}

    }

  }
);


/* =========================================================
   UPGRADE HTTP → WEBSOCKET
   ========================================================= */

server.on(
  'upgrade',
  (request, socket, head) => {

    const url =
      new URL(
        request.url,
        `http://${request.headers.host}`
      );


    if (
      url.pathname !== '/deriv'
    ) {

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

  }
);


/* =========================================================
   START SERVER
   ========================================================= */

server.listen(
  PORT,
  '0.0.0.0',
  () => {

    console.log(
      `TITAN V8.7 running on port ${PORT}`
    );

    console.log(
      `Deriv endpoint: ${DERIV_URL}`
    );

  }
);
