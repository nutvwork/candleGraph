import asyncio
from deriv_api import DerivAPI
import pandas as pd
from datetime import datetime
import mplfinance as mpf

# กำหนด App ID
APP_ID = "66726"  # เปลี่ยนเป็น app_id ของคุณ

async def main():
    # สร้าง instance ของ DerivAPI
    api = DerivAPI(app_id=APP_ID)

    try:
        # ส่งคำขอ ticks_history เพื่อดึงข้อมูล candlestick
        request = {
            "ticks_history": "R_100",
            "adjust_start_time": 1,
            "count": 100,
            "end": "latest",
            "granularity": 60,  # 1 นาที
            "style": "candles"
        }
        response = await api.ticks_history(request)
        
        # แปลงข้อมูล candlestick เป็น DataFrame
        candles = response["candles"]
        df = pd.DataFrame([{
            "time": datetime.fromtimestamp(candle["epoch"]),
            "open": float(candle["open"]),
            "high": float(candle["high"]),
            "low": float(candle["low"]),
            "close": float(candle["close"])
            
        } for candle in candles])
        
        print("Candlestick Data:")
        print(df)
        
        # สร้าง custom style
        my_style = mpf.make_mpf_style(
            base_mpl_style='default',
            marketcolors=mpf.make_marketcolors(
                up='green',          # สีสำหรับแท่ง bullish (ราคาปิด > ราคาเปิด)
                down='red',          # สีสำหรับแท่ง bearish (ราคาปิด < ราคาเปิด)
                edge='inherit',      # สีขอบใช้ตาม up/down
                wick='black',        # สีไส้เทียน
                volume='blue'        # สีแท่ง volume
            )
        )


        # สมมติว่า df เป็น DataFrame จากโค้ดด้านบน
        df.set_index("time", inplace=True)  # ตั้ง time เป็น index
        mpf.plot(df, type="candle", title="Candlestick Chart (R_100)", style=my_style,volume=False)

    except Exception as e:
        print(f"[error] {e}")
    
    finally:
        # ปิดการเชื่อมต่อ
        await api.disconnect()
        print("[close] Disconnected from Deriv API")

# รัน async function
if __name__ == "__main__":
    asyncio.run(main())