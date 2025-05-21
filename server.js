const express = require('express');
const http    = require('http');
const { Server } = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

// Serve static files (stream page)
app.use('/', express.static(__dirname + '/public'));

// REST endpoint stub for future notifications
app.use(express.json());
app.post('/notify', (req, res) => {
  // TODO: integrate your push‑notification logic here
  console.log('Notification payload:', req.body);
  res.sendStatus(200);
});

let piSocket = null;

io.of('/pi').on('connection', socket => {
  console.log('Pi connected:', socket.id);
  piSocket = socket;

  socket.on('disconnect', () => {
    console.log('Pi disconnected');
    piSocket = null;
  });
});

io.of('/client').on('connection', socket => {
  console.log('Client connected:', socket.id);

  // Tell Pi to start streaming
  if (piSocket) piSocket.emit('start_stream');

  // Forward JPEG frames from Pi to this client
  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
    // If no more clients, tell Pi to stop
    if (io.of('/client').sockets.size === 0 && piSocket) {
      piSocket.emit('stop_stream');
    }
  });
  
  socket.on("change_resolution", (res) => {
  console.log(`🔄 Resolution change requested: ${res.width}x${res.height}`);
  if (piSocket) {
    piSocket.emit("change_resolution", res);
  }
});
});

// Relay JPEG blobs from Pi to all clients
io.of('/pi').on('connection', socket => {
  socket.on('frame', data => {
    // binary JPEG blob
    io.of('/client').emit('frame', data);
  });
});

server.listen(9265, () => {
  console.log('Server listening on port 9265');
});
