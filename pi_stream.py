import socketio
import time
import io
import base64
from picamera2 import Picamera2
from PIL import Image

SERVER_URL = 'http://192.168.1.200:9265'  # your server's LAN IP
NAMESPACE = '/pi'

sio = socketio.Client()

running = False
resolution = (320, 240)  # default
picam2 = Picamera2()

@sio.event(namespace=NAMESPACE)
def connect():
    print('✅ Pi connected to server (namespace /pi).')

@sio.event(namespace=NAMESPACE)
def connect_error(e):
    print('❌ Pi connect_error:', e)

@sio.event(namespace=NAMESPACE)
def disconnect():
    print('❌ Pi disconnected from server.')

@sio.on('change_resolution', namespace=NAMESPACE)
def on_change_resolution(data):
    global running, resolution
    width = data.get('width', 640)
    height = data.get('height', 480)
    print(f"🔧 Changing resolution to {width}x{height}")
    resolution = (width, height)
    if running:
        running = False
        time.sleep(1)  # let camera stop
        configure_camera()
        running = True  # resume
        print("✅ Resolution updated and resumed stream.")

def configure_camera():
    global picam2, resolution
    picam2.stop()
    config = picam2.create_preview_configuration(main={"size": resolution})
    picam2.configure(config)
    picam2.start()

@sio.on('start_stream', namespace=NAMESPACE)
def on_start_stream():
    global running
    if running:
        return
    running = True
    print('▶️ start_stream received. Beginning streaming...')
    configure_camera()
    try:
        while running:
            frame = picam2.capture_array()
            img = Image.fromarray(frame).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=50)
            b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            sio.emit('frame', b64, namespace=NAMESPACE)
            time.sleep(0.1)
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
