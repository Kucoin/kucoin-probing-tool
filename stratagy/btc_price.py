import websocket
import json
import pandas as pd
import csv
from datetime import datetime

# 定义CSV文件名称
csv_filename = "btc_trade_data.csv"

# 初始化CSV文件并写入表头
with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["timestamp", "datetime", "price"])

# WebSocket回调函数
def on_message(ws, message):
    msg = json.loads(message)
    timestamp = int(msg['E'] / 1000)  # 毫秒级时间戳转换为秒级
    price = float(msg['p'])
    datetime_str = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    # 将数据写入CSV文件
    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, datetime_str, price])

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    # 订阅BTCUSDT交易对的逐笔交易数据
    params = {
        "method": "SUBSCRIBE",
        "params": ["btcusdt@trade"],
        "id": 1
    }
    ws.send(json.dumps(params))

# 启动WebSocket连接
ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws",
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)
ws.run_forever()
