import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path("C:/Users/yusuf/AppData/Local/Programs/Python/Python312/Lib/site-packages/cnlib/data")
coins = ["kapcoin-usd_train", "metucoin-usd_train", "tamcoin-usd_train"]

for coin in coins:
    df = pd.read_parquet(data_dir / f"{coin}.parquet")
    print(f"--- {coin} ---")
    print(f"Shape: {df.shape}")
    first = df["Close"].iloc[0]
    last = df["Close"].iloc[-1]
    peak = df["Close"].max()
    print(f"Close: start={first:.2f}, end={last:.2f}, peak={peak:.2f}")
    print(f"Total return: {(last/first - 1)*100:.1f}%")

    returns = df["Close"].pct_change().dropna()
    print(f"Daily return: mean={returns.mean()*100:.3f}%, std={returns.std()*100:.3f}%")
    print(f"Max drawdown from peak: {((df['Close'] / df['Close'].cummax()) - 1).min()*100:.1f}%")
    print(f"Days with >5% drop: {(returns < -0.05).sum()}")
    print(f"Days with >10% drop: {(returns < -0.10).sum()}")
    print()

# Buy-and-hold simulation (no leverage, equal weight)
print("=== Buy-and-Hold Simulation (no leverage) ===")
dfs = {c: pd.read_parquet(data_dir / f"{c}.parquet") for c in coins}
capital = 3000.0
per_coin = capital / 3
for coin, df in dfs.items():
    shares = per_coin / df["Close"].iloc[0]
    final = shares * df["Close"].iloc[-1]
    print(f"{coin}: ${per_coin:.0f} -> ${final:.0f} ({(final/per_coin-1)*100:.0f}%)")
