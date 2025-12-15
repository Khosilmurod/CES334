#!/usr/bin/env python3
"""
Plant Guardian Web Viewer

Real-time moisture monitoring with animated guardian
- Moisture > 1500 (50%): Guardian stays alive  
- Moisture <= 1500 (50%): Guardian dies
- Tap event: Guardian swipes to defend the plant
"""

from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
from pathlib import Path
import webbrowser
from threading import Timer

# MQTT Configuration
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "murad/vase/#"

# Moisture thresholds (0-4095 range)
MOISTURE_THRESHOLD = 1500  # 50% threshold

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plant-guardian-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

# Global state
current_moisture = 0
is_alive = True

def on_mqtt_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    if rc == 0:
        print("✅ Connected to MQTT broker!")
        client.subscribe(TOPIC)
        print(f"📡 Subscribed to topic: {TOPIC}")
    else:
        print("❌ Failed to connect, return code =", rc)

def on_mqtt_message(client, userdata, msg):
    """MQTT message callback"""
    global current_moisture, is_alive
    
    topic = msg.topic
    payload = msg.payload.decode()
    
    if "events" in topic:
        # Tap event
        print(f"💥 TAP event received: {payload}")
        socketio.emit('tap_event', {'data': payload}, namespace='/')
        socketio.sleep(0)  # Allow emission to complete
        print(f"📤 Emitted tap_event to all clients")
        
    else:
        # Moisture reading
        try:
            moisture_value = int(payload)
            current_moisture = moisture_value
            
            # Calculate percentage (0-4095 range mapped to 0-100%)
            moisture_percent = (moisture_value / 4095) * 100
            
            # Determine if alive based on threshold
            was_alive = is_alive
            is_alive = moisture_value > MOISTURE_THRESHOLD
            
            print(f"🌿 Moisture: {moisture_value} ({moisture_percent:.1f}%) - {'Alive' if is_alive else 'Dead'}")
            
            # Emit to all connected clients
            socketio.emit('moisture_update', {
                'value': moisture_value,
                'percent': moisture_percent,
                'alive': is_alive,
                'changed': was_alive != is_alive
            }, namespace='/')
            socketio.sleep(0)  # Allow emission to complete
            print(f"📤 Emitted moisture_update to all clients")
            
        except ValueError:
            print(f"⚠️ Invalid moisture value: {payload}")

# Initialize MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_message = on_mqtt_message

@app.route('/')
def index():
    """Serve the plant guardian viewer page"""
    return render_template('index.html')

@app.route('/web_assets/<path:filename>')
def serve_assets(filename):
    """Serve 3D model assets"""
    assets_dir = Path(__file__).parent / "web_assets"
    return send_from_directory(assets_dir, filename)

@app.route('/static/web_assets/<path:filename>')
def serve_static_assets(filename):
    """Serve 3D model assets via static route"""
    assets_dir = Path(__file__).parent / "web_assets"
    return send_from_directory(assets_dir, filename)

@socketio.on('connect')
def handle_connect():
    """Handle new client connections"""
    print(f"🔌 Client connected")
    # Send current state to new client
    moisture_percent = (current_moisture / 4095) * 100
    emit('moisture_update', {
        'value': current_moisture,
        'percent': moisture_percent,
        'alive': is_alive,
        'changed': False
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnections"""
    print(f"🔌 Client disconnected")

def open_browser():
    """Open browser after short delay"""
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🌱 Plant Guardian Web Viewer")
    print("="*50)
    print("🌐 Starting at: http://localhost:5000")
    print(f"📡 MQTT Broker: {BROKER}:{PORT}")
    print(f"📡 MQTT Topic: {TOPIC}")
    print(f"💧 Moisture Threshold: {MOISTURE_THRESHOLD} (50%)")
    print("="*50)
    print("\n🌿 Waiting for sensor data...")
    
    # Connect to MQTT broker
    try:
        mqtt_client.connect(BROKER, PORT, 60)
        mqtt_client.loop_start()
        print("✅ MQTT client started")
    except Exception as e:
        print(f"❌ MQTT connection error: {e}")
    
    # Open browser after 1 second
    Timer(1, open_browser).start()
    
    # Run Flask-SocketIO server
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
