# /home/pi/pi_stream.py

import socketio
import time
import io
import base64
from picamera2 import Picamera2
from PIL import Image

SERVER_URL = 'http://75.183.209.207:9265'  # your server's LAN IP
NAMESPACE = '/pi'

sio = socketio.Client()

running = False

@sio.event(namespace=NAMESPACE)
def connect():
    print('✅ Pi connected to server (namespace /pi).')

@sio.event(namespace=NAMESPACE)
def connect_error(e):
    print('❌ Pi connect_error:', e)

@sio.event(namespace=NAMESPACE)
def disconnect():
    print('❌ Pi disconnected from server.')

@sio.on('start_stream', namespace=NAMESPACE)
def on_start_stream():
    global running
    if running:
        return
    running = True
    print('▶️ start_stream received. Beginning streaming...')
    # configure picamera2
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    try:
        while running:
            frame = picam2.capture_array()               # Grab frame
            img = Image.fromarray(frame).convert("RGB")                 # To PIL
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=50)     # Compress
            b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            sio.emit('frame', b64, namespace=NAMESPACE)  # Send
            time.sleep(0.1)                              # ~10fps
    finally:
        picam2.stop()
        print('🛑 Camera released.')

@sio.on('stop_stream', namespace=NAMESPACE)
def on_stop_stream():
    global running
    print('⏸️ stop_stream received. Halting stream...')
    running = False

def main():
    try:
        sio.connect(
            SERVER_URL,
            namespaces=[NAMESPACE],
            transports=['websocket']
        )
        sio.wait()
    except Exception as e:
        print('❌ Connection failed:', e)

if __name__ == '__main__':
    main()