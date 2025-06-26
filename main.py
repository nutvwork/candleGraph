import asyncio
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplfinance as mpf
import requests
import base64
from io import BytesIO
from datetime import datetime, timedelta
import websockets

# Test New Verion1
class DerivChartGenerator:
    def __init__(self):
        
        self.app_id = 667216  # Free app ID สำหรับ demo
        self.app_id = 667226  # Free app ID สำหรับ demo
        self.app_id = 66726  # Free app ID สำหรับ demo
        self.ws_url = f"wss://ws.binaryws.com/websockets/v3?app_id={self.app_id}"
        self.assets = ["R_10", "R_25", "R_50", "R_75", "R_100"]
        # self.assets = ["R_10"]
        
    async def get_ticks_history(self, symbol, count=60):
        """ดึงข้อมูล ticks history จาก Deriv API"""
        try:
            async with websockets.connect(self.ws_url) as websocket:
                # ส่ง request สำหรับ ticks history
                request = {
                    "ticks_history": symbol,
                    "adjust_start_time": 1,
                    "count": count,
                    "end": "latest",
                    "start": 1,
                    "style": "ticks"
                }
                
                await websocket.send(json.dumps(request))
                response = await websocket.recv()
                data = json.loads(response)
                
                if 'error' in data:
                    print(f"Error for {symbol}: {data['error']['message']}")
                    return None
                    
                return data
                
        except Exception as e:
            print(f"Error connecting to WebSocket for {symbol}: {e}")
            return None
    
    def ticks_to_ohlc(self, ticks_data, timeframe_minutes=1):
        """แปลง ticks data เป็น OHLC data"""
        if not ticks_data or 'history' not in ticks_data:
            return None
            
        times = ticks_data['history']['times']
        prices = ticks_data['history']['prices']
        
        # สร้าง DataFrame
        df = pd.DataFrame({
            'timestamp': times,
            'price': prices
        })
        
        # แปลง timestamp เป็น datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('datetime', inplace=True)
        
        # Resample เป็น 1 minute candles
        ohlc = df['price'].resample(f'{timeframe_minutes}min').ohlc()
        ohlc['volume'] = df['price'].resample(f'{timeframe_minutes}min').count()
        
        # ลบ rows ที่มี NaN
        ohlc.dropna(inplace=True)
        
        # เอาแค่ 60 แท่งล่าสุด
        ohlc = ohlc.tail(60)
        
        return ohlc
    
    def calculate_ema(self, data, period):
        """คำนวณ EMA"""
        return data.ewm(span=period, adjust=False).mean()
    
    def create_candlestick_chart(self, symbol, ohlc_data):
        """สร้างกราฟ candlestick พร้อม EMA"""
        if ohlc_data is None or ohlc_data.empty:
            print(f"No data available for {symbol}")
            return None
            
        # คำนวณ EMA
        ohlc_data['ema3'] = self.calculate_ema(ohlc_data['close'], 3)
        ohlc_data['ema5'] = self.calculate_ema(ohlc_data['close'], 5)
        
        # สร้าง additional plots สำหรับ EMA
        apds = [
            mpf.make_addplot(ohlc_data['ema3'], color='blue', width=1.5, label='EMA 3'),
            mpf.make_addplot(ohlc_data['ema5'], color='red', width=1.5, label='EMA 5')
        ]
        
        # กำหนด style
        style = mpf.make_mpf_style(
            base_mpf_style='charles',
            rc={'font.size': 8}
        )
        
        # สร้างกราห
        fig, axes = mpf.plot(
            ohlc_data,
            type='candle',
            style=style,
            addplot=apds,
            volume=True,
            title=f"{symbol} - 1M Timeframe (60 Candles)",
            ylabel='Price',
            ylabel_lower='Volume',
            figsize=(12, 8),
            returnfig=True,
            show_nontrading=False
        )
        
        # เพิ่ม legend สำหรับ EMA
        axes[0].legend(['EMA 3', 'EMA 5'], loc='upper left')
        
        return fig
    
    def save_chart_as_image(self, fig, symbol):
        """บันทึกกราฟเป็น image และส่งกลับเป็น base64"""
        if fig is None:
            return None
            
        # บันทึกเป็น bytes
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        
        # แปลงเป็น base64
        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        
        # ปิด figure เพื่อประหยัด memory
        plt.close(fig)
        
        return img_base64
    
    def send_to_api(self, symbol, image_base64, ohlc_data):
        """ส่งข้อมูลไปยัง API"""
        if image_base64 is None:
            print(f"No image data for {symbol}")
            return False
            
        try:
            # เตรียมข้อมูลสำหรับส่ง
            latest_data = ohlc_data.iloc[-1]  # ข้อมูลแท่งล่าสุด
            
            payload = {
                'symbol': symbol,
                'timeframe': '1M',
                'image_data': image_base64,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'latest_price': float(latest_data['close']),
                'latest_open': float(latest_data['open']),
                'latest_high': float(latest_data['high']),
                'latest_low': float(latest_data['low']),
                'latest_volume': int(latest_data['volume']),
                'ema3': float(latest_data['ema3']),
                'ema5': float(latest_data['ema5'])
            }
            
            # ส่ง POST request
            response = requests.post(
                'https://lovetoshopmall.com/iqlab/saveImage.php',
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            print(f"📝 {symbol}: API Response - {response.text}")
            if response.status_code == 200:
                print(f"✅ {symbol}: Successfully sent to API")
                return True
            else:
                print(f"❌ {symbol}: API Error - Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {symbol}: Request Error - {e}")
            return False
        except Exception as e:
            print(f"❌ {symbol}: Unexpected Error - {e}")
            return False
    
    async def process_symbol(self, symbol):
        """ประมวลผลสำหรับ symbol เดียว"""
        print(f"🔄 Processing {symbol}...")
        
        # ดึงข้อมูล ticks
        ticks_data = await self.get_ticks_history(symbol, count=1000)  # ขอข้อมูลเยอะหน่อยเพื่อให้ได้ 60 แท่ง
        
        if ticks_data is None:
            print(f"❌ {symbol}: Failed to get ticks data")
            return False
            
        # แปลงเป็น OHLC
        ohlc_data = self.ticks_to_ohlc(ticks_data)
        
        if ohlc_data is None or ohlc_data.empty:
            print(f"❌ {symbol}: Failed to convert to OHLC")
            return False
            
        print(f"📊 {symbol}: Got {len(ohlc_data)} candles")
        
        # สร้างกราฟ
        fig = self.create_candlestick_chart(symbol, ohlc_data)
        
        if fig is None:
            print(f"❌ {symbol}: Failed to create chart")
            return False
            
        # แปลงเป็น base64
        image_base64 = self.save_chart_as_image(fig, symbol)
        
        if image_base64 is None:
            print(f"❌ {symbol}: Failed to convert to base64")
            return False
            
        # ส่งไปยัง API
        success = self.send_to_api(symbol, image_base64, ohlc_data)
        
        return success
    
    async def run_all_assets(self):
        """รันสำหรับ assets ทั้งหมด"""
        print("🚀 Starting chart generation for all assets...")
        print(f"Assets: {', '.join(self.assets)}")
        print("-" * 50)
        
        successful = 0
        failed = 0
        
        for symbol in self.assets:
            try:
                success = await self.process_symbol(symbol)
                if success:
                    successful += 1
                else:
                    failed += 1
                    
                # หน่วงเวลาเล็กน้อยระหว่าง requests
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ {symbol}: Unexpected error - {e}")
                failed += 1
        
        print("-" * 50)
        print(f"✅ Completed: {successful} successful, {failed} failed")
        print(f"📊 Total processed: {successful + failed}/{len(self.assets)} assets")

# สำหรับรันโปรแกรม
async def main():
    generator = DerivChartGenerator()
    await generator.run_all_assets()

# รันโปรแกรม
if __name__ == "__main__":
    # ติดตั้ง dependencies ที่จำเป็น
    print("📦 Required packages:")
    print("pip install pandas numpy matplotlib mplfinance requests websockets")
    print("-" * 50)
    
    # รันโปรแกรม
    asyncio.run(main())
