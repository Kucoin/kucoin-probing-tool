import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1) 读取数据并做初步处理
df = pd.read_csv('BTCUSDT_1m_20250304_20250305.csv')
df['Open Time'] = pd.to_datetime(df['Open Time'])
df.sort_values('Open Time', inplace=True)
df.reset_index(drop=True, inplace=True)

# 把字符串列转换为数值列
for col in ['Open','High','Low','Close','Volume']:
    df[col] = df[col].astype(float)

# 2) 计算波动指标，这里以单根K线的高低价差(Range)为例
df['Range'] = df['High'] - df['Low']

# 3) 设定一个阈值，判断单根K线是否处于“小范围波动”
#   （此处阈值=50 仅为示例，请结合历史回测或经验设定）
threshold = 250
df['IsSmallRange'] = df['Range'] < threshold

# 4) 将连续的 True/False 段落分组：同一段连续True共享同一个 GroupID
#   - 当 IsSmallRange 和上一根不同，就视为新一段
df['GroupID'] = (df['IsSmallRange'] != df['IsSmallRange'].shift(1)).cumsum()

# 5) 在所有 True 段落中，挑出持续时间 >= 1 小时的区间
#    注意：假设你的原始数据是一分钟一根K线且没有数据缺失。
#    如果存在缺失或数据粒度不同，需要做更细致的判断。
qualified_groups = []
for gid, group in df.groupby('GroupID'):
    # 如果这一段都是 True（即小波动）
    if group['IsSmallRange'].all():
        start_time = group['Open Time'].iloc[0]
        end_time   = group['Open Time'].iloc[-1]
        
        # 若时间跨度 >= 1小时
        if (end_time - start_time) >= pd.Timedelta('1h'):
            qualified_groups.append(group)

# 6) 画图：先画所有数据的收盘价（细线），再对符合条件的区间做加粗标注
plt.figure(figsize=(12, 6))
plt.plot(df['Open Time'], df['Close'], label='Close Price', linewidth=1)

# 对满足条件的时间段，用更粗的线段标示
# 你可以换别的颜色或线型做区分
for subdf in qualified_groups:
    plt.plot(subdf['Open Time'], subdf['Close'], linewidth=3, label='Small Range > 1H')

plt.xlabel('Time')
plt.ylabel('Price')
plt.title('BTC Price with Small-Range Intervals (>=1H) Highlighted')
plt.legend()
plt.savefig("ma_chart_box.png")
