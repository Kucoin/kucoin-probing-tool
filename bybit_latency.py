
import time
import csv
import websocket
import json
import os
from pybit.unified_trading import HTTP, WebSocketTrading, WebSocket


API_KEY = "vG6SDfOpQdNKhejLkM"
API_SECRET = "871VSB8ANf4EmPD5paRWGpBG0VW2Yx0w1gHF"


local_order_start_time = 0
local_order_end_time = 0
local_cancel_start_time = 0
local_cancel_start_time = 0

csv_file = open("bybit.csv", 'w', newline='')
csv_writer = csv.writer(csv_file)

csv_writer.writerow(["DateTime", "GetSysTime", "LimitOrder", "CancelOrder", "LimitOrderServer", "CancelOrderServer",
                     "LimitOrderWs", "LimitOrderWsMsgTS", "LimitOrderTime", "LimitOrderWsExtrasTs",
                     "CancelOrderWs", "CancelOrderWsMsgTS", "CancelOrderTime", "CancelOrderWsExtrasTs"])

ROW_COUNT = 14
row_data = [""] * ROW_COUNT

session = HTTP(
    api_key=API_KEY,
    api_secret=API_SECRET
)

ws = WebSocket(
    testnet=False,
    channel_type="private",
    api_key=API_KEY,
    api_secret=API_SECRET
)

#1. 用rest下撤单，记录下单时间，用websocket获取成交时间，计算延迟
def rest_place_order():
    global row_data, local_order_start_time, local_order_end_time, local_cancel_start_time, local_cancel_end_time
    if local_order_start_time != 0:
        row_data[6] -= local_order_start_time
        row_data[7] -= local_order_start_time
        row_data[8] -= local_order_start_time
        row_data[9] -= local_order_start_time
        
        row_data[10] -= local_order_start_time
        row_data[11] -= local_order_start_time
        row_data[12] -= local_order_start_time
        row_data[13] -= local_order_start_time
        log_row(row_data)
    row_data = [""] * ROW_COUNT
    
    local_time = int(time.time() * 1000)
    row_data[0] = local_time
    time_resp = session.get_server_time()
    time_nano = int(time_resp["result"]["timeNano"])
    server_time_ms = time_nano // 1_000_000
    row_data[1] = server_time_ms - local_time
    local_order_start_time = int(time.time() * 1000)
    order_resp = session.place_order(
        category="spot",
        symbol="BTCUSDT",
        side="Buy",
        orderType="Limit",
        qty="0.001",
        price="10000",
        timeInForce="PostOnly",
        orderLinkId=str(local_time),
        isLeverage=0,
        orderFilter="Order",
    )
    local_order_end_time = int(time.time() * 1000)
    row_data[2] = local_order_end_time - local_order_start_time

    order_time = order_resp["time"]
    row_data[3] = order_time - local_order_start_time

    order_id = order_resp["result"]["orderId"]
    local_cancel_start_time = int(time.time() * 1000)
    cancel_resp = session.cancel_order(
        category="spot",
        symbol="BTCUSDT",
        order_id=order_id
    )
    local_cancel_end_time = int(time.time() * 1000)
    row_data[4] = local_cancel_end_time - local_cancel_start_time
    cancel_time = cancel_resp["time"]
    row_data[5] = cancel_time - local_cancel_start_time

def log_row(data):
    csv_writer.writerow(data)
    csv_file.flush()

def handle_trade_message(message):
    local_ts = int(time.time() * 1000)
    server_ts = message.get("ts", None)

    trade_ts = None
    if "data" in message and len(message["data"]) > 0:
        trade_ts = message["data"][0].get("T", None)

    # print("Trade Timestamp:", trade_ts)
    # print("Trade Message Timestamp:", server_ts)
    # print("Trade Local Timestamp:", local_ts)
    
def handle_order_message(message):
    global row_data, local_order_start_time, local_cancel_start_time
    if message['data'][0]['orderStatus'] == 'New':
        local_ts = int(time.time() * 1000)
        creation_ts = message['creationTime']
        created_ts = message['data'][0]['createdTime']
        updated_ts = message['data'][0]['updatedTime']
        
        row_data[6] = int(local_ts)
        row_data[7] = int(creation_ts)
        row_data[8] = int(created_ts)
        row_data[9] = int(updated_ts)
    elif message['data'][0]['orderStatus'] == 'Cancelled':
        local_ts = int(time.time() * 1000)
        creation_ts = message['creationTime']
        created_ts = message['data'][0]['createdTime']
        updated_ts = message['data'][0]['updatedTime']

        row_data[10] = int(local_ts)
        row_data[11] = int(creation_ts)
        row_data[12] = int(created_ts)
        row_data[13] = int(updated_ts)
    else:
        print(message)
    
        

def trade_steam():
    ws.trade_stream(symbol="BTCUSDT", callback=handle_trade_message)
    
def order_stream():
    ws.order_stream(callback=handle_order_message)

def handle_place_order_message(message):
    local_ts = int(time.time() * 1000)
    server_ts = message["header"]["Timenow"]
    # print("Place Order Local Timestamp:", local_ts)
    # print("Place Order Message Timestamp:", server_ts)

    time.sleep(0.5)

    ws_trading.cancel_order(
        handle_cancel_order_message,
        category="linear",
        symbol="BTCUSDT",
        order_id=message["data"]["orderId"]
    )

def handle_cancel_order_message(message):
    local_ts = int(time.time() * 1000)
    server_ts = message["header"]["Timenow"]
    # print("Cancel Order Local Timestamp:", local_ts)
    # print("Cancel Order Message Timestamp:", server_ts)

ws_trading = WebSocketTrading(
    testnet=False,
    api_key=API_KEY,
    api_secret=API_SECRET,
)

def send_ping():
    uri = "wss://stream.bybit.com/v5/trade"
    ws = websocket.create_connection(uri)
    message = {"op": "ping"}
    ws.send(json.dumps(message))

    response = ws.recv()
    local_ts = int(time.time() * 1000)

    resp_json = json.loads(response)

    server_ts = None
    if "data" in resp_json and len(resp_json["data"]) > 0:
        server_ts = resp_json["data"][0]

    print("receive pong local Timestamp:", local_ts)

    ws.close()

def ws_place_order():
    while True:
        ws_trading.place_order(
            callback=handle_place_order_message,
            category="linear",
            symbol="BTCUSDT",
            side="Buy",
            orderType="Limit",
            price="15000",
            qty="0.001"
        )

        send_ping()
        time.sleep(1)
        
if __name__ == "__main__":
    order_stream()
    while True:
        rest_place_order()
        time.sleep(1)
        
