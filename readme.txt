For futures testing:
1, copy kucoin_futures_lat.py and futures_core to your colo machine
2, python3 kucoin_futures_lat.py
run the program for 5 ~ 10 minutes and 2 CSV files(order_data.csv websocket_pub.csv) will be generated which records the latency for order placement and cancelling.

For spot testing:
1, copy kucoin_spot_lat.py and spot_core to your colo machine
2, python3 kucoin_spot_lat.py
run the program for 5 ~ 10 minutes and 2 CSV files(spot_order_data.csv and spot_websocket_pub.csv) will be generated which records the latency for order placement and cancelling.
