import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 读取数据
data = pd.read_csv("BTCUSDT_1m_20250304_20250305.csv")
data["Open Time"] = pd.to_datetime(data["Open Time"])

# 计算移动平均（MA）
data["MA5"] = data["Close"].rolling(window=5).mean()    # 5周期移动平均
data["MA10"] = data["Close"].rolling(window=10, min_periods=1).mean()
data["MA30"] = data["Close"].rolling(window=30).mean()   # 30周期移动平均

# 定义函数：利用二阶差分找出拐点（局部极值点）
def find_turning_points(series):
    d2 = np.diff(np.sign(np.diff(series)))
    # 拐点对应于二阶差分非零的点，注意需要偏移1
    turning_indices = np.where(d2 != 0)[0] + 1
    return turning_indices

# 计算 MA10 曲线的拐点
tp_ma10 = find_turning_points(data["MA10"].values)
time_threshold = 600
price_threshold = 100

# 利用贪心算法，从每个拐点出发，遍历后续数据点，
# 如果时间差或价格差超过阈值，则将该线段标粗，并将该点更新为新的参照拐点
highlight_segments = []  # 存储待高亮的线段 (起始索引, 结束索引)
if len(tp_ma10) > 0:
    last_tp = tp_ma10[0]  # 以第一个拐点作为起点
    for i in range(last_tp + 1, len(data)):
        time_diff = data["Open Time"].iloc[i] - data["Open Time"].iloc[last_tp]
        price_diff = abs(float(data["MA10"].iloc[i]) - float(data["MA10"].iloc[last_tp]))
        if time_diff > time_threshold or price_diff > price_threshold:
            highlight_segments.append((last_tp, i))
            # 使用 np.searchsorted 找到 tp_ma10 中第一个大于或等于 i 的索引
            j = np.searchsorted(tp_ma10, i)
            if j < len(tp_ma10):
                last_tp = tp_ma10[j]  # 更新为下一个拐点的下标
            else:
                break

# 绘制图形
plt.figure(figsize=(12, 6))
plt.plot(data["Open Time"], data["Close"], label="Close Price", color="black", linewidth=1)
plt.plot(data["Open Time"], data["MA10"], label="MA10", color="red", linewidth=1)
# plt.scatter(data["Open Time"].iloc[tp_ma10], data["MA10"].iloc[tp_ma10],
#             color="red", marker="o", s=50, label="MA10 拐点")

# 绘制高亮线段，注意只为第一个线段添加图例标签
for j, (start_idx, end_idx) in enumerate(highlight_segments):
    plt.plot(data["Open Time"].iloc[start_idx:end_idx+1],
             data["MA10"].iloc[start_idx:end_idx+1],
             color="blue", linewidth=3,
             label="高亮区段" if j == 0 else "")

plt.xticks(rotation=45)
plt.xlabel("Time")
plt.ylabel("Price")
plt.title("BTC MA10")
plt.legend()
plt.grid()

# 保存图像
plt.savefig("ma_chart_with_highlighted_segments.png")