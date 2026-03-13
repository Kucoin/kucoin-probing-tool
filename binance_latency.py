import json
import time
import hmac
import csv
import json
import os
import base64
import requests
import hashlib
import threading
import urllib
import websocket
from websocket import WebSocketApp

# Binance API 配置
API_KEY = ""
API_SECRET = ""
WS_STREAM_URL = "wss://stream.binance.com:9443/ws"
WS_URL = "wss://ws-api.binance.com:443/ws-api/v3"

local_order_start_time = 0
local_order_end_time = 0
local_cancel_start_time = 0
local_cancel_start_time = 0

csv_file = open("binance.csv", 'w', newline='')
csv_writer = csv.writer(csv_file)

csv_writer.writerow(["DateTime", "GetSysTime", "LimitOrder", "CancelOrder", "LimitOrderServer", "CancelOrderServer",
                     "LimitOrderWs", "LimitOrderWsMsgTS", "LimitOrderTime",
                     "CancelOrderWs", "CancelOrderWsMsgTS", "CancelOrderTime"])

ROW_COUNT = 12
row_data = [""] * ROW_COUNT

def log_row(data):
    csv_writer.writerow(data)
    csv_file.flush()

def rest_order_place():
    global row_data, local_order_start_time, local_order_end_time, local_cancel_start_time, local_cancel_end_time
    if local_order_start_time != 0:
        row_data[6] -= local_order_start_time
        row_data[7] -= local_order_start_time
        row_data[8] -= local_order_start_time
        
        row_data[9] -= local_cancel_start_time
        row_data[10] -= local_cancel_start_time
        row_data[11] -= local_cancel_start_time
        log_row(row_data)
    row_data = [""] * ROW_COUNT

    local_time = int(time.time() * 1000)
    row_data[0] = local_time
    time_resp = requests.get("https://api.binance.com/api/v3/time")
    row_data[1] = int(time_resp.json()["serverTime"]) - local_time
    
    params = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": "0.001",
        "price": "25000",
        "timestamp": local_time,
    }
    payload = '&'.join([f'{param}={value}' for param, value in params.items()])
    signature = hmac.new(
        API_SECRET.encode("ascii"),
        payload.encode("ascii"),
        hashlib.sha256
    ).hexdigest()
    # signature_base64 = base64.b64encode(signature).decode("ascii")

    params['signature'] = signature
    headers = {
        'X-MBX-APIKEY': API_KEY,
    }
    local_order_start_time = int(time.time() * 1000)
    response = requests.post(
        'https://api.binance.com/api/v3/order',
        headers=headers,
        data=params,
    )
    local_order_end_time = int(time.time() * 1000)
    row_data[2] = local_order_end_time - local_order_start_time
    message = response.json()
    order_time = message['transactTime']
    row_data[3] = order_time - local_order_start_time
    
    cancel_params = {
        "symbol": "BTCUSDT",
        "origClientOrderId": message['clientOrderId'],
        "timestamp": local_time,
    }
    payload = '&'.join([f'{param}={value}' for param, value in cancel_params.items()])
    signature = hmac.new(
        API_SECRET.encode("ascii"),
        payload.encode("ascii"),
        hashlib.sha256
    ).hexdigest()
    cancel_params['signature'] = signature
    local_cancel_start_time = int(time.time() * 1000)
    cancel_resp = requests.delete(
        'https://api.binance.com/api/v3/order',
        headers=headers,
        data=cancel_params,
    )
    local_cancel_end_time = int(time.time() * 1000)
    row_data[4] = local_cancel_end_time - local_cancel_start_time
    message = cancel_resp.json()
    cancel_time = message['transactTime']
    row_data[5] = cancel_time - local_cancel_start_time
    

def on_stream_open(ws):
    params = {
        "method": "SUBSCRIBE",
        "params": ["btcusdt@trade"],
        "id": 1
    }
    ws.send(json.dumps(params))
    
def on_stream_message(ws, message):
    data = json.loads(message)
    if data['e'] == 'executionReport':
        print(data)
        if data['X'] == 'NEW':
            local_time = int(time.time() * 1000)
            event_time = data['E']
            order_time = data['O']
            row_data[6] = int(local_time)
            row_data[7] = int(event_time)
            row_data[8] = int(order_time)
        if data['X'] == 'CANCELED':
            local_time = int(time.time() * 1000)
            event_time = data['E']
            order_time = data['O']
            row_data[9] = int(local_time)
            row_data[10] = int(event_time)
            row_data[11] = int(order_time)
        

def on_stream_error(ws, error):
    print(f"错误: {error}")

def on_stream_close(ws, close_status_code, close_msg):
    print("WebSocket 连接关闭")
    

# 启动 WebSocket
def start_websocket():
    ws = websocket.create_connection(WS_URL)
    while True:
        time_params = {
        "method": "time",
        "id": 2
        }
        ws.send(json.dumps(time_params))
        data = json.loads(ws.recv())
        local_ts = int(time.time() * 1000)
        server_ts = data["result"]["serverTime"]
        # 下单
        timestamp = int(time.time() * 1000)
        params = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": 0.001,
            "price": 25000,
            "apiKey": API_KEY,
            "timestamp": timestamp,
        }

        payload = '&'.join([f'{param}={value}' for param, value in sorted(params.items())])
        signature = hmac.new(
            API_SECRET.encode("ascii"),
            payload.encode("ascii"),
            hashlib.sha256
        ).hexdigest()

        params['signature'] = signature
        order_request = {
            "id": 2,
            "method": "order.place",
            "params": params
        }

        ws.send(json.dumps(order_request))
        data = json.loads(ws.recv())
        print(data)
        local_ts = int(time.time() * 1000)
        server_ts = data['result']['transactTime']
        time.sleep(0.5)
        
        cancel_params = {
            "symbol": "BTCUSDT",
            "origClientOrderId": data["result"]["clientOrderId"],
            "apiKey": API_KEY,
            "timestamp": timestamp,
        }
        payload = '&'.join([f'{param}={value}' for param, value in sorted(cancel_params.items())])
        signature = hmac.new(
            API_SECRET.encode("ascii"),
            payload.encode("ascii"),
            hashlib.sha256
        ).hexdigest()
        cancel_params['signature'] = signature
        cancel_request = {
            "id": 3,
            "method": "order.cancel",
            "params": cancel_params
        }
        ws.send(json.dumps(cancel_request))
        data = json.loads(ws.recv())
        local_ts = int(time.time() * 1000)
        server_ts = data['result']['transactTime']
        time.sleep(1)

def on_stream_ping(ws, message):
    ws.pong(message)

def start_stream_websocket(listen_key):
    ws_url = f"wss://stream.binance.com:9443/ws/{listen_key}"
    ws = WebSocketApp(
        ws_url,
        on_message=on_stream_message,
        on_error=on_stream_error,
        on_close=on_stream_close,
        on_ping=on_stream_ping
    )
    ws.run_forever()
    
def create_listen_key():
    url = "https://api.binance.com/api/v3/userDataStream"
    headers = {"X-MBX-APIKEY": API_KEY}
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        return response.json()["listenKey"]
    else:
        raise Exception(f"Failed to create listen key: {response.json()}")

def keep_listen_key_alive(listen_key):
    url = f"https://api.binance.com/api/v3/userDataStream?listenKey={listen_key}"
    headers = {"X-MBX-APIKEY": API_KEY}
    response = requests.put(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to refresh listen key: {response.json()}")

if __name__ == "__main__":
    listen_key = create_listen_key()
    ws_stream_thread = threading.Thread(target=start_stream_websocket, args=(listen_key,), daemon=True)
    ws_stream_thread.start()
    while True:
        rest_order_place()
        time.sleep(1)
    # ws_thread = threading.Thread(target=start_websocket, daemon=True)
    # ws_stream_thread = threading.Thread(target=start_stream_websocket, daemon=True)
    
    # ws_thread.start()
    # ws_stream_thread.start()

    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("WebSocket 已停止")