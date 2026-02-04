import time
import hmac
import base64
import json
import websocket
import threading

class OKXWebSocketClient:
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.base_url = "wss://ws.okx.com:8443/ws/v5/private"
        self.ws = None
        self.is_authenticated = False
        self.count = 0

    def _generate_signature(self, timestamp):
        message = f"{timestamp}GET/users/self/verify"
        mac = hmac.new(self.secret_key.encode('utf-8'), message.encode('utf-8'), digestmod='sha256')
        return base64.b64encode(mac.digest()).decode('utf-8')

    def _get_timestamp(self):
        return int(time.time())

    def _authenticate(self):
        # 发送认证请求
        timestamp = self._get_timestamp()
        signature = self._generate_signature(timestamp)
        auth_data = {
            "op": "login",
            "args": [
                {
                    "apiKey": self.api_key,
                    "passphrase": self.passphrase,
                    "timestamp": timestamp,
                    "sign": signature
                }
            ]
        }
        self.ws.send(json.dumps(auth_data))

    def on_message(self, ws, message):
        data = json.loads(message)
        print(f"Received: {json.dumps(data, indent=2)}")
        if "event" in data and data["event"] == "login":
            if data["code"] == "0":
                self.is_authenticated = True
                print("Authentication successful")
            else:
                print(f"Authentication failed: {data}")

    def on_error(self, ws, error):
        print(f"Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("Connection closed")

    def on_open(self, ws):
        print("Connection established")
        self._authenticate()

    def start(self):
        self.ws = websocket.WebSocketApp(
            self.base_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )
        threading.Thread(target=self.ws.run_forever).start()

        while not self.is_authenticated:
            time.sleep(1)

        timestamp = str(int(time.time() * 1000))
        order_data = {
            "id": timestamp,
            "op": "order",
            "args": [{
                "instId": "BTC-USDT",
                "tdMode": "spot_isolated",
                "side": "buy",
                "ordType": "limit",
                "sz": "0.001",
                "px": "25000"
            }]
        }
        while True:
            self.ws.send(json.dumps(order_data))
            self.count += 1
            time.sleep(1)
            print(self.count)


API_KEY = "1da65981-2ea1-4dc6-aefe-986b8da5de8f"
SECRET_KEY = "55A979FF725251D9799B3CF67D9E5FA3"
PASSPHRASE = "Killua@1997"

# 示例使用
if __name__ == "__main__":
    client = OKXWebSocketClient(API_KEY, SECRET_KEY, PASSPHRASE)
    client.start()
