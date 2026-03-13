from kucoin_futures.client import Trade
from kucoin_futures.ws_client import KucoinFuturesWsClient
from kucoin_futures.client import WsToken
import asyncio
import time
import csv
import socket
import sys
import threading
import os
from datetime import datetime
from kucoin_futures.client import Market

local_sent_start_time = 0
local_sent_end_time = 0
cancel_start_time = 0
cancel_end_time = 0

#SYMBOL = 'PEOPLEUSDTM'
SYMBOL = 'XBTUSDTM'

#sub
YOUR_KEY = ''
YOUR_SEC = ''
YOUR_PASS = ""

#main
#YOUR_KEY = ''
#YOUR_SEC = ''
#YOUR_PASS = ""

csv_file = open('order_data.csv', 'w', newline='')
csv_writer = csv.writer(csv_file)

# 写入表头
csv_writer.writerow(["DateTime",
                     "GetSysTime", "LimitOrder", "CancelOrder",
                     "LimitOrderWs", "LimitOrderWsMsgTS", "LimitOrderTime","LimitOrderWsExtrasTs",
                     "CancelOrderWs", "CancelOrderWsMsgTS", "CancelOrderWsExtrasTs", "LimitOrderSrvRTT", "CancelOrderSrvRTT",
                    "WsLat", "WsTradeOrdersOpenLat", "WsTradeOrdersCancelLat"

                     ]), 
# Initialize row data
ROW_COUNT = 16
row_data = [""] * ROW_COUNT

pub_csv_file = open('websocket_pub.csv', 'w', newline='')
pub_csv_writer = csv.writer(pub_csv_file)
pub_csv_writer.writerow(["DateTime", "extraTs", "pushTs", "msgTs","msgTs - pushTs"])

# Function to log row data
def log_row(data):
    csv_writer.writerow(data)
    csv_file.flush()

# Function to get server time and calculate latency
def get_server_time(market):
    try:
        server_time = market.get_server_timestamp()
        server_time = market.get_server_timestamp()
        server_start_time = server_time['sttime']
        server_end_time = server_time['edtime']
        latency = server_end_time - server_start_time
    except:
        return 0

    return latency

def place_and_cancel_orders(client, market):
    global row_data,local_sent_start_time,local_sent_end_time,cancel_start_time,cancel_end_time

    # Log the row data when complete
    if local_sent_start_time != 0:
        row_data[4] -= local_sent_start_time
        row_data[5] -= local_sent_start_time
        row_data[6] -= local_sent_start_time
        row_data[7] -= local_sent_start_time

        row_data[8] -= cancel_start_time
        row_data[9] -= cancel_start_time
        row_data[10] -= cancel_start_time
        log_row(row_data)
    # Clear or re-initialize row_data after logging if necessary
    row_data = [0] * ROW_COUNT

    # Get current timestamp
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_data[0] = current_time

    # Server time calculation (building connection and getting latency)
    server_latency = get_server_time(market)
    row_data[1] = server_latency

    # Place limit order
    limit_order_response = client.create_limit_order(SYMBOL, 'buy', '1', '1', '0.1')
    print("limit_order_response", limit_order_response)
    local_sent_start_time = limit_order_response['sttime']
    local_sent_end_time = limit_order_response['edtime']
    srv_end_time = limit_order_response['srvedtime']
    srv_start_time = limit_order_response['srvsttime']
    row_data[2] = local_sent_end_time - local_sent_start_time
    row_data[11] = srv_end_time - srv_start_time

    # Cancel order
    cancel_response = client.cancel_order(limit_order_response['orderId'])
    cancel_start_time = cancel_response['sttime']
    cancel_end_time = cancel_response['edtime']
    row_data[3] = cancel_end_time - cancel_start_time 
    row_data[12] = cancel_response['srvedtime'] - cancel_response['srvsttime']

async def deal_msg_pub(msg):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws_arrive_time = time.time() * 1000  # Local arrival time in ms
    extraTs = msg['extras']['ts']
    pushTs = msg['extras']['__1'] / 1000 # to local ms
    msgTs = msg['data']['timestamp']
    pub_csv_writer.writerow([current_time, ws_arrive_time - extraTs, ws_arrive_time - pushTs, ws_arrive_time - msgTs, pushTs - msgTs])
    pub_csv_file.flush()
    

async def deal_msg(msg):
    global row_data,local_sent_start_time,local_sent_end_time,cancel_start_time,cancel_end_time
    # Filter out messages not related to the target symbol
    if msg['data']['symbol'] != SYMBOL:
        return
    # WebSocket latency handling
    ws_arrive_time_us = time.time() * 1000000  # Local arrival time in us
    ws_arrive_time = ws_arrive_time_us / 1000  # Local arrival time in ms
    extraTs = msg['extras']['ts']
    gwPushTs = msg['extras']['__1']
    if msg['data']['type'] == 'open':
        ts = msg['data']['ts'] / 1000000  # Push start time in ms
        order_time = msg['data']['orderTime'] / 1000000  # Order creation time in ms

        # Update row data for order placement WebSocket
        row_data[4] = ws_arrive_time
        row_data[5] = ts
        row_data[6] = order_time
        row_data[7] = extraTs
        # Local - GW push to get the msg latency
        row_data[14] = (ws_arrive_time_us - gwPushTs) / 1000

    elif msg['data']['type'] == 'canceled':
        ts = msg['data']['ts'] / 1000000  # Push start time in ms
        
        # Update row data for order cancelation WebSocket
        row_data[8] = ws_arrive_time
        row_data[9] = ts
        row_data[10] = extraTs
        # Local - GW push to get the msg latency
        row_data[15] = (ws_arrive_time_us - gwPushTs) / 1000

    if "ws_rtt_us" in msg:
        row_data[13] = msg['ws_rtt_us'] / 2 / 1000
    

async def _futures_ws_loop():
    wstoken = WsToken(key=YOUR_KEY, secret=YOUR_SEC, passphrase=YOUR_PASS)
    ws_client = await KucoinFuturesWsClient.create(None, wstoken, deal_msg, private=True)
    await ws_client.subscribe('/contractMarket/tradeOrders')

    wstoken_public= WsToken()
    ws_client_pub = await KucoinFuturesWsClient.create(None, wstoken_public, deal_msg_pub, private=False)
    await ws_client_pub.subscribe('/contractMarket/level2:XBTUSDTM')

    while True:
        await asyncio.sleep(60)

def futures_ws_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_futures_ws_loop())     

async def main():
    client = Trade(key=YOUR_KEY, secret=YOUR_SEC, passphrase=YOUR_PASS)    
    market = Market(url='https://api-futures.kucoin.com')

    # ws 接收线程
    t_ws = threading.Thread(target=futures_ws_loop)
    t_ws.start()
    await asyncio.sleep(4)
    market.TCP_NODELAY = 1
    client.TCP_NODELAY = 1
    
    while True:
        place_and_cancel_orders(client, market)
        await asyncio.sleep(1.5)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
