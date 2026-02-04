import requests
import pandas as pd
import time
from datetime import datetime, timedelta

# 定义参数
symbol = "BTCUSDT"    # 交易对
interval = "1m"       # 1分钟K线
start_time = "2025-03-04 15:00:00"  # 开始时间（UTC时间）
end_time = "2025-03-05 15:00:00"    # 结束时间（UTC时间）
csv_filename = "BTCUSDT_1m_20250304_20250305.csv"

# 将时间转换为时间戳（毫秒）
def date_to_milliseconds(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp() * 1000)

start_ts = date_to_milliseconds(start_time)
end_ts = date_to_milliseconds(end_time)

# 定义函数：获取K线数据
def get_binance_klines(symbol, interval, start_time, end_time, limit=1000):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': start_time,
        'endTime': end_time,
        'limit': limit
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data

# 初始化 CSV 文件，并写入表头
columns = ['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume']
df_list = []

while start_ts < end_ts:
    # 获取数据
    print(f"Fetching data from {datetime.utcfromtimestamp(start_ts/1000)}...")
    data = get_binance_klines(symbol, interval, start_ts, end_ts)
    
    if not data:
        print("No data received, exiting loop.")
        break
    
    # 处理数据
    df = pd.DataFrame(data, columns=[
        'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time',
        'Quote Asset Volume', 'Number of Trades', 'Taker Buy Base Volume',
        'Taker Buy Quote Volume', 'Ignore'
    ])
    
    # 转换时间戳
    df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
    df = df[columns]  # 只保留必要的列
    df_list.append(df)
    
    # 更新 start_ts 为下一批数据的时间
    start_ts = int(df.iloc[-1]['Open Time'].timestamp() * 1000) + 60000  # +1分钟

    # 避免API请求速率限制
    time.sleep(0.5)

# 合并数据并保存到 CSV
final_df = pd.concat(df_list, ignore_index=True)
final_df.to_csv(csv_filename, index=False)
print(f"✅ 数据已保存到 {csv_filename}，共 {len(final_df)} 行数据。")
