import websocket
import json
import pandas as pd
from datetime import datetime

# กำหนด App ID (แทนที่ด้วย app_id ของคุณ)
APP_ID = "66726"  # เปลี่ยนเป็น app_id ที่ได้จาก Deriv

# WebSocket URL
WS_URL = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"

# ตัวแปรสำหรับเก็บข้อมูล candlestick
candles = []

def on_open(ws):
    print("[open] Connection established")
    # ส่งคำขอ ticks_history เพื่อดึงข้อมูล candlestick
    request = {
        "ticks_history": "R_100",  # สัญลักษณ์ (เช่น R_100 สำหรับ Volatility 100 Index)
        "adjust_start_time": 1,
        "count": 100,  # จำนวน candlestick ที่ต้องการ
        "end": "latest",  # ดึงข้อมูลจนถึงล่าสุด
        "granularity": 60,  # 1 นาที (60 วินาที)
        "style": "candles"  # รูปแบบ candlestick
    }
    ws.send(json.dumps(request))

def on_message(ws, message):
    global candles
    data = json.loads(message)
    
    # ตรวจสอบว่ามีข้อมูล candlestick หรือไม่
    if data.get("msg_type") == "candles":
        for candle in data["candles"]:
            candles.append({
                "time": datetime.fromtimestamp(candle["epoch"]),
                "open": float(candle["open"]),
                "high": float(candle["high"]),
                "low": float(candle["low"]),
                "close": float(candle["close"])
                
            })
        # แปลงเป็น DataFrame
        df = pd.DataFrame(candles)
        print("Candlestick Data:")
        print(df)
    
    elif data.get("error"):
        print(f"[error] {data['error']['message']}")

def on_error(ws, error):
    print(f"[error] {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"[close] Connection closed: {close_msg}")

# สร้าง WebSocket connection
ws = websocket.WebSocketApp(
    WS_URL,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

# รัน WebSocket
ws.run_forever()