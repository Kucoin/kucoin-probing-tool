import ccxt
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

# ============== 1. 初始化交易所并获取数据 ==============
def get_binance_1m_data(symbol="BTC/USDT", limit=200):
    """
    使用 ccxt 从 Binance 获取1分钟 K线数据示例。
    参数:
        symbol: 交易对, 如 "BTC/USDT"
        limit:  获取多少条数据
    返回:
        pd.DataFrame, 包含时间、开高低收成交量等
    """
    exchange = ccxt.binance()
    # 获取最近 limit 根 1分钟K线 (candles)
    # 返回的数据格式: [时间戳(ms), 开, 高, 低, 收, 成交量]
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=limit)

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    # 转换时间戳为可读时间
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    # 转换列为浮点型
    for col in ['open','high','low','close','volume']:
        df[col] = df[col].astype(float)

    return df

# ============== 2. 计算 MA10 并判断拐头 ==============
def compute_ma10_slope_signals(df):
    """
    在 DataFrame 中加入 MA10, 同时根据 MA10 是否拐头向上/向下给出信号:
    - +1 表示 MA10 由下降转为上升 (向上拐头)
    - -1 表示 MA10 由上升转为下降 (向下拐头)
    -  0 表示无拐头变化

    返回:
        同步更新包含 'MA10', 'signal' 的 df
    """
    df['MA10'] = df['close'].rolling(30).mean()
    # MA10 前后两根做差
    df['MA10_diff'] = df['MA10'].diff()

    # 当 MA10_diff 由负变正，则视为 “向上拐点”
    # 当 MA10_diff 由正变负，则视为 “向下拐点”
    # 用一个简单的逻辑: 
    #   curr_diff > 0 and prev_diff <= 0 => +1 信号
    #   curr_diff < 0 and prev_diff >= 0 => -1 信号
    df['signal'] = 0
    for i in range(1, len(df)):
        if df.loc[i, 'MA10_diff'] > 0 and df.loc[i - 1, 'MA10_diff'] <= 0:
            df.loc[i, 'signal'] = 1
        elif df.loc[i, 'MA10_diff'] < 0 and df.loc[i - 1, 'MA10_diff'] >= 0:
            df.loc[i, 'signal'] = -1

    return df

# ============== 3. 简易模拟盘逻辑 ==============
def backtest_simple_trend(df):
    """
    基于 MA10 拐头信号的简单多空策略回测，并在每次交易时扣除 0.1% 手续费：
      - pos = 0 => 空仓
      - pos = 1 => 多头
      - pos = -1 => 空头

    当 signal=1 (向上拐点) => 平空 & 开多
    当 signal=-1 (向下拐点) => 平多 & 开空

    手续费逻辑:
      - 每次平仓时，需要扣除 平仓手续费 = close_price * fee_rate
      - 每次开仓时，需要扣除 开仓手续费 = close_price * fee_rate
      - fee_rate = 0.001 (千分之一)
    """
    df = df.copy()  # 不修改原 df
    df['position'] = 0   # 每根K线结束后的持仓: 0 / 1 / -1
    df['trade_price'] = np.nan  # 换仓时的价格
    df['pnl'] = 0.0      # 记录每根K线收盘时策略的累计盈亏

    position = 0
    entry_price = 0.0
    cum_pnl = 0.0
    fee_rate = 0.0000  # 手续费率：千分之一

    for i in range(len(df)):
        close_price = df.loc[i, 'close']
        signal = df.loc[i, 'signal']

        if i == 0:
            # 第一根K线默认空仓，不做任何交易
            df.loc[i, 'position'] = 0
            df.loc[i, 'pnl'] = 0.0
            df.loc[i, 'trade_price'] = close_price
            continue

        # 如果有信号，先平仓，再开仓
        if signal == 1:
            # 如果之前是空头，需要平空
            if position == -1:
                # 已实现盈亏 = (入场价 - 当前价) * 1BTC (因为是做空)
                cum_pnl += (entry_price - close_price)
                # 平仓手续费 (平掉 -1 BTC)
                fee_close = close_price * fee_rate
                cum_pnl -= fee_close

            # 然后开多
            position = 1
            entry_price = close_price
            df.loc[i, 'trade_price'] = close_price

            # 开多手续费
            fee_open = close_price * fee_rate
            cum_pnl -= fee_open

        elif signal == -1:
            # 如果之前是多头，需要平多
            if position == 1:
                # 已实现盈亏 = (当前价 - 入场价) * 1BTC
                cum_pnl += (close_price - entry_price)
                # 平仓手续费
                fee_close = close_price * fee_rate
                cum_pnl -= fee_close

            # 然后开空
            position = -1
            entry_price = close_price
            df.loc[i, 'trade_price'] = close_price

            # 开空手续费
            fee_open = close_price * fee_rate
            cum_pnl -= fee_open

        # 计算当前浮动盈亏
        if position == 1:
            float_pnl = close_price - entry_price
        elif position == -1:
            float_pnl = entry_price - close_price
        else:
            float_pnl = 0.0

        df.loc[i, 'position'] = position
        df.loc[i, 'pnl'] = cum_pnl + float_pnl

    return df

# ============== 4. 主流程 & 画图 ==============
def main():
    # （1）获取数据，这里只是获取最近200根 1分钟K线做回测演示
    df = get_binance_1m_data(symbol="BTC/USDT", limit=1000)

    # （2）计算 MA10 和信号
    df = compute_ma10_slope_signals(df)

    # （3）回测逻辑
    df = backtest_simple_trend(df)
    
    df_long = df[df['signal'] == 1]   # 向上拐点
    df_short = df[df['signal'] == -1] # 向下拐点

    # （4）画图
    # 1) 价格和 MA10 曲线
    plt.figure()
    plt.title("BTC/USDT 1m K-line & MA10")
    plt.plot(df['timestamp'], df['close'], label='Close Price')
    plt.plot(df['timestamp'], df['MA10'], label='MA10')
    plt.scatter(df_long['timestamp'], df_long['close'], marker='^', label='Open Long')
    plt.scatter(df_short['timestamp'], df_short['close'], marker='v', label='Open Short')
    plt.legend()
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig("price.png")

    # 2) 资金曲线
    plt.figure()
    plt.title("Strategy PnL Curve")
    plt.plot(df['timestamp'], df['pnl'], label='PnL')
    plt.scatter(df_long['timestamp'], df_long['pnl'], marker='^', label='Open Long')
    plt.scatter(df_short['timestamp'], df_short['pnl'], marker='v', label='Open Short')
    plt.legend()
    plt.xlabel("Time")
    plt.ylabel("PnL")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig("money.png")

if __name__ == "__main__":
    main()
