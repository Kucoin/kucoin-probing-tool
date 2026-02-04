import websocket
import json
from datetime import datetime
import csv

# 定义CSV文件名
csv_filename = "btc_1s_kline_data.csv"

# 初始化CSV文件并写入表头
with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["timestamp", "datetime", "open", "high", "low", "close", "volume"])

# 存储数据用于绘图
data = []

# WebSocket 回调函数
def on_message(ws, message):
    msg = json.loads(message)
    
    # 解析K线数据
    kline = msg['k']
    timestamp = int(kline['t'] / 1000)  # 毫秒级时间戳转换为秒
    dt_str = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    open_price = float(kline['o'])
    high_price = float(kline['h'])
    low_price = float(kline['l'])
    close_price = float(kline['c'])
    volume = float(kline['v'])
    
    # 存入全局数据列表（用于绘图）
    data.append({'timestamp': timestamp, 'datetime': dt_str, 'close': close_price})

    # 追加数据到 CSV 文件
    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, dt_str, open_price, high_price, low_price, close_price, volume])

def on_error(ws, error):
    print("WebSocket 错误:", error)

def on_close(ws):
    print("### WebSocket 连接关闭 ###")

def on_open(ws):
    # 订阅 BTC/USDT 1秒K线数据
    params = {
        "method": "SUBSCRIBE",
        "params": ["btcusdt@kline_1s"],  # 1秒K线
        "id": 1
    }
    ws.send(json.dumps(params))

# 启动 WebSocket 连接
ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws",
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)

# 运行 WebSocket
ws.run_forever()
