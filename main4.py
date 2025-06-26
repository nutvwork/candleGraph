import websocket
import json
import pandas as pd
from datetime import datetime
import mplfinance as mpf
import requests
import os

# กำหนด App ID (แทนที่ด้วย app_id ของคุณ)
APP_ID = "66726"  # เปลี่ยนเป็น app_id ที่ได้จาก Deriv
WS_URL = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"

# ตัวแปรสำหรับเก็บข้อมูล candlestick
candles = []

# สร้าง custom style สำหรับกราฟ (สีแดง/เขียว)
my_style = mpf.make_mpf_style(
    base_mpl_style='default',
    marketcolors=mpf.make_marketcolors(
        up='green',
        down='red',
        edge='inherit',
        wick='black',
        volume='blue'
    )
)

def on_open(ws):
    print("[open] Connection established")
    request = {
        "ticks_history": "R_100",
        "adjust_start_time": 1,
        "count": 100,
        "end": "latest",
        "granularity": 60,
        "style": "candles"
    }
    ws.send(json.dumps(request))

def on_message(ws, message):
    global candles
    data = json.loads(message)
    
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
        df.set_index("time", inplace=True)
        print("Candlestick Data:")
        print(df)
        
        # บันทึกกราฟเป็นไฟล์ภาพ
        image_path = "candlestick_chart.png"
        mpf.plot(df, type='candle', title='Candlestick Chart (R_100)', style=my_style, volume=False, savefig=image_path)
        print(f"[info] Graph saved to {image_path}")
        
        # ส่งไฟล์ภาพไปยัง endpoint
        try:
            with open(image_path, 'rb') as image_file:
                files = {'image': (image_path, image_file, 'image/png')}
                response = requests.post('https://thepapers.in/deriv/saveImage.php', files=files)
                
                if response.status_code == 200:
                    print(f"[success] Image sent successfully: {response.text}")
                else:
                    print(f"[error] Failed to send image: Status {response.status_code}, Response: {response.text}")
        
        except Exception as e:
            print(f"[error] Failed to send image: {e}")
        
        # ลบไฟล์ภาพหลังจากส่ง (ถ้าต้องการ)
        # os.remove(image_path)
        print(f"[info] Deleted temporary image file: {image_path}")
        
        # ปิด WebSocket หลังจากส่งภาพ
        ws.close()
    
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