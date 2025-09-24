#!/usr/bin/env python3
"""
Minimal Flask Server - ทดสอบว่าปัญหาอยู่ที่ Flask หรือไม่
"""

from flask import Flask, jsonify
import time

app = Flask(__name__)

@app.route('/api/test')
def test():
    """API ที่ไม่ทำอะไรเลย - แค่ return JSON"""
    return jsonify({
        'message': 'Hello World',
        'timestamp': time.time(),
        'status': 'ok'
    })

@app.route('/api/sleep')
def test_sleep():
    """API ที่ sleep 100ms เพื่อทดสอบ"""
    time.sleep(0.1)  # 100ms
    return jsonify({
        'message': 'Slept for 100ms',
        'timestamp': time.time()
    })

@app.route('/')
def home():
    """หน้าแรกแบบเรียบง่าย"""
    return '<h1>Minimal Test Server</h1><p>Test endpoints: /api/test, /api/sleep</p>'

if __name__ == '__main__':
    print("🧪 Minimal Flask Server for Testing")
    print("Endpoints:")
    print("  /api/test - Instant response")
    print("  /api/sleep - 100ms sleep")
    print("  http://localhost:5000")
    
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)