import websockets
import json
import time
import base64
import hashlib
import hmac
import argparse
import asyncio
import logging
import csv
from urllib.parse import quote

logging.basicConfig(filename="error.log", level=logging.ERROR, format='%(asctime)s %(levelname)s:%(message)s')

def parse_arguments():
    parser = argparse.ArgumentParser(description="WebSocket Client Configuration")
    parser.add_argument("--apikey", required=True, help="Your API key")
    parser.add_argument("--secret", required=True, help="Your secret key")
    parser.add_argument("--order_file", default="order.csv", help="CSV file to save order timing data")
    parser.add_argument("--cancel_file", default="cancel.csv", help="CSV file to save cancel timing data")
    return parser.parse_args()

SEND_TIMES = 100
passphrase = "a123456"

order_receive = 0
cancel_send = 0
cancel_receive = 0
order_fail = 0
cancel_fail = 0
order_responses = []
cancel_responses = []
cancel_client_oid_table = {}
order_client_oid_table = {}

def sign(plain: str, key: str) -> str:
    hm = hmac.new(key.encode(), plain.encode(), hashlib.sha256)
    signature = base64.b64encode(hm.digest()).decode()
    return signature

async def send_heartbeat(ws):
    while True:
        try:
            timestamp = str(int(time.time() * 1000))
            ping_payload = json.dumps({
                "id": f"ping-{timestamp}"
            })
            await ws.ping(ping_payload)
            await asyncio.sleep(5)
        except websockets.ConnectionClosed:
            print("WebSocket connection closed.")
            break
        except Exception as e:
            print(f"Heartbeat error: {e}")
            break

async def cancel_order(ws, client_oid):
    try:
        timestamp = str(int(time.time() * 1000))
        cancel_msg = {
            "id": f"cancel-{client_oid}-{timestamp}",
            "op": "futures.cancel",
            "args": {
                "symbol": "XBTUSDTM",
                "clientOid": client_oid
            }
        }
        await ws.send(json.dumps(cancel_msg, ensure_ascii=False))
        global cancel_send, cancel_client_oid_table
        cancel_send += 1
        cancel_client_oid_table[client_oid] = cancel_msg["id"]
    except Exception as e:
        logging.error(f"Cancel order error for {client_oid}: {e}")

async def send_orders(ws, order_id, response_queue):
    client_oid = f"order{order_id}"
    try:
        timestamp = str(int(time.time() * 1000))
        order_msg = {
            "id": f"order-{order_id}-{timestamp}",
            "op": "futures.order",
            "args": {
                "symbol": "XBTUSDTM",
                "type": "limit",
                "side": "buy",
                "price": "0.1",
                "leverage": "1",
                "size": "1",
                "timeInForce": "GTC",
                "marginMode": "ISOLATED",
                "clientOid": client_oid
            }
        }
        await ws.send(json.dumps(order_msg, ensure_ascii=False))
        global order_client_oid_table
        order_client_oid_table[client_oid] = order_msg["id"]
    except Exception as e:
        logging.error(f"Order {order_id} error: {e}")

async def place_orders(ws, response_queue):
    for order_id in range(1, SEND_TIMES + 1):
        await send_orders(ws, order_id, response_queue)

async def repeat_place_orders(ws, response_queue, delay=3):
    count = 0
    global order_receive, order_fail, cancel_fail, cancel_send, cancel_receive, order_responses, cancel_responses, cancel_client_oid_table, order_client_oid_table

    while True:
        order_receive = 0
        cancel_send = 0
        cancel_receive = 0
        order_fail = 0
        cancel_fail = 0
        order_responses.clear()
        cancel_responses.clear()
        cancel_client_oid_table = {f"order{i}": False for i in range(1, 101)}
        order_client_oid_table = {f"order{i}": False for i in range(1, 101)}

        await place_orders(ws, response_queue)
        await asyncio.sleep(delay)

        if order_receive != SEND_TIMES:
            logging.error(f"订单响应数量不足：收到 {order_receive} 个订单返回，应为{SEND_TIMES}。")
        if cancel_receive != cancel_send:
            logging.error(f"撤单响应数量不足：收到 {cancel_receive} 个撤单返回，应为{cancel_send}。")
        if order_fail != 0:
            logging.error(f"下单失败数量：{order_fail}")
            await cancel_all_orders(ws)
        if cancel_fail != 0:
            logging.error(f"撤单失败数量：{cancel_fail}")
            await cancel_all_orders(ws)

        count += 1
        if count % 10 == 0:
            logging.error(f"第{count}轮结束")
        await asyncio.sleep(1)

async def receive_messages(ws, message_queue):
    try:
        while True:
            message = await ws.recv()
            recv_time = str(int(time.time() * 1000))
            await message_queue.put((recv_time, message))
    except websockets.ConnectionClosed:
        logging.error("WebSocket connection closed.")
    except Exception as e:
        logging.error(f"Error receiving message: {e}")

async def process_messages(ws, message_queue, order_output_file, cancel_output_file):
    global order_receive, cancel_receive, order_fail, cancel_fail, order_responses, cancel_responses, cancel_client_oid_table, order_client_oid_table

    try:
        with open(order_output_file, mode="a", newline="") as order_csvfile, \
             open(cancel_output_file, mode="a", newline="") as cancel_csvfile:

            order_writer = csv.writer(order_csvfile)
            cancel_writer = csv.writer(cancel_csvfile)

            order_writer.writerow(["clientOid", "recv_time - send_time (ms)", "out_time - in_time (ms)"])
            cancel_writer.writerow(["clientOid", "recv_time - send_time (ms)", "out_time - in_time (ms)"])

            while True:
                recv_time, message = await message_queue.get()
                data = json.loads(message)
                in_time = data.get("inTime")
                out_time = data.get("outTime")
                msg_id = data.get("id")

                if not msg_id:
                    continue

                parts = msg_id.split("-")
                op = parts[0]
                send_time = parts[2] if len(parts) > 2 else ""
                client_oid = data.get("data", {}).get("clientOid", "")

                recv_minus_send = int(recv_time) - int(send_time) if send_time else ""
                out_minus_in = int(out_time) - int(in_time) if out_time and in_time else ""

                if op == "order":
                    order_receive += 1
                    order_responses.append(data)
                    if client_oid:
                        order_client_oid_table[client_oid] = "order"
                        await cancel_order(ws, client_oid)
                        order_writer.writerow([client_oid, recv_minus_send, out_minus_in])
                elif op == "cancel":
                    cancel_receive += 1
                    cancel_responses.append(data)
                    if client_oid in cancel_client_oid_table:
                        cancel_client_oid_table[client_oid] = "cancel"
                        cancel_writer.writerow([client_oid, recv_minus_send, out_minus_in])

    except Exception as e:
        logging.error(f"Error processing messages: {e}")

async def cancel_all_orders(ws):
    for order_id in range(1, 101):
        client_oid = f"order{order_id}"
        await cancel_order(ws, client_oid)

async def test_websocket(apikey, secret, order_file, cancel_file):
    timestamp = str(int(time.time() * 1000))
    url_path = f"apikey={apikey}&timestamp={timestamp}"
    original = f"{apikey}{timestamp}"

    sign_value = quote(sign(original, secret))
    passphrase_sign = quote(sign(passphrase, secret))

    ws_url = f"ws://10.50.195.75:10240/v1/private?{url_path}&sign={sign_value}&passphrase={passphrase_sign}"
    response_queue = asyncio.Queue()

    try:
        async with websockets.connect(ws_url) as ws:
            print(f"Connected to WebSocket server: {ws_url}")
            auth_response = await ws.recv()
            print(f"Received session message: {auth_response}")

            session_info = sign(auth_response, secret)
            await ws.send(session_info)

            welcome_msg = await ws.recv()
            logging.error(f"Welcome message: {welcome_msg}")

            await asyncio.gather(
                receive_messages(ws, response_queue),
                process_messages(ws, response_queue, order_file, cancel_file),
                repeat_place_orders(ws, response_queue, delay=3),
            )
    except websockets.ConnectionClosed:
        logging.error("WebSocket connection closed.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    args = parse_arguments()
    asyncio.run(test_websocket(args.apikey, args.secret, args.order_file, args.cancel_file))
