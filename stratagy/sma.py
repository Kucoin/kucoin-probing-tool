import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 读取数据
data = pd.read_csv("BTCUSDT_1m_20250304_20250305.csv")
data["Open Time"] = pd.to_datetime(data["Open Time"])

# 计算移动平均（MA）以及SMA_9
data["MA5"] = data["Close"].rolling(window=5).mean()    # 5周期移动平均
data["MA10"] = data["Close"].rolling(window=10).mean()   # 10周期移动平均
data["MA30"] = data["Close"].rolling(window=30).mean()   # 30周期移动平均
data["SMA_9"] = data["Close"].rolling(window=9).mean()   # 9周期SMA

# 定义判断反转的函数
def check_reversal(sma_series, current_index, current_window=3, past_window=3):
    if current_index < past_window + current_window:
        return None  # 数据不足，无法判断
 
    # 获取当前窗口和过去窗口的SMA值
    current_smas = sma_series.iloc[current_index - current_window + 1:current_index + 1]
    past_smas = sma_series.iloc[current_index - past_window - current_window + 1:current_index - current_window + 1]
 
    # 计算当前窗口和过去窗口的趋势（斜率）
    current_trend = np.polyfit(range(current_window), current_smas, 1)[0]
    past_trend = np.polyfit(range(past_window), past_smas, 1)[0]
 
    # 判断是否发生反转
    if past_trend < 0 and current_trend > 0:
        return 'Upward Reversal'
    elif past_trend > 0 and current_trend < 0:
        return 'Downward Reversal'
    else:
        return None

# 应用反转判断
data['Reversal'] = None
for i in range(len(data)):
    data.at[i, 'Reversal'] = check_reversal(data['MA10'], i, current_window=3, past_window=3)

# 输出部分数据查看结果
print(data[['Close', 'MA10', 'Reversal']])

# 绘制曲线及反转点
plt.figure(figsize=(12, 6))
plt.plot(data["Open Time"], data["Close"], label="Close Price", color="black")
plt.plot(data["Open Time"], data["SMA_9"], label="SMA 9", color="blue")

# 找出并标记反转点
reversal_up = data[data["Reversal"] == "Upward Reversal"]
reversal_down = data[data["Reversal"] == "Downward Reversal"]

plt.scatter(reversal_up["Open Time"], reversal_up["SMA_9"], color="green", marker="^", s=100, label="Upward Reversal")
plt.scatter(reversal_down["Open Time"], reversal_down["SMA_9"], color="red", marker="v", s=100, label="Downward Reversal")

plt.xlabel("Time")
plt.ylabel("Price")
plt.title("SMA_9 曲线及反转点")
plt.legend()
plt.xticks(rotation=45)
plt.grid(True)
plt.savefig("sma_chart.png")
plt.show()
