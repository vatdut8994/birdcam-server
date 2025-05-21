const express = require('express');
const http = require('http');
const { Server } = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: '*' }
});

app.use('/', express.static(__dirname + '/public'));

let piSocket = null;

// Handle Pi connections on namespace /pi
io.of('/pi').on('connection', socket => {
  console.log('👉 Pi connected:', socket.id);
  piSocket = socket;

  socket.on('disconnect', () => {
    console.log('❌ Pi disconnected');
    piSocket = null;
  });

  socket.on('frame', data => {
    console.log('Frame received:', new Date().toISOString());
    io.of('/client').emit('frame', data);
  });
});

// Handle web/app clients on namespace /client
io.of('/client').on('connection', socket => {
  console.log('👉 Client connected:', socket.id);
  if (piSocket) {
    console.log('   → telling Pi to start_stream');
    piSocket.emit('start_stream');
  } else {
    console.log('   ⚠️ No Pi connected, cannot start stream');
  }

  socket.on('disconnect', () => {
    console.log('❌ Client disconnected:', socket.id);
    if (io.of('/client').sockets.size === 0 && piSocket) {
      console.log('   → telling Pi to stop_stream');
      piSocket.emit('stop_stream');
    }
  });
});

server.listen(9265, '0.0.0.0', () => {
  console.log('✅ Server listening on 0.0.0.0:9265');
});