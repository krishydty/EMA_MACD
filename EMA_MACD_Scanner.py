import time
import pandas as pd

from upstox_client import Configuration, ApiClient
from upstox_client.api.history_api import HistoryApi
from upstox_client.rest import ApiException

# ——— YOUR CONFIG ———
API_KEY      = "d6eb7200-41a1-4572-b7c2-1e2c119bac7e"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0MjcxNjEiLCJqdGkiOiI2ODA4YTcxNmRlZWQwYjcwYjVjNDA4OTQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzQ1Mzk3NTI2LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NDU0NDU2MDB9.AK1w9mhB0jLDfIWMgRrPGcVcw0cPr6345sq9Hi3JNxA"
SYMBOLS      = [
    "NSE_EQ|INE009A01021",  # INFY
    "NSE_EQ|INE075A01022",  # TCS
]
INTERVAL     = "1minute"
API_VERSION  = "2.0"

# ——— CLIENT SETUP ———
cfg = Configuration()
cfg.access_token = ACCESS_TOKEN
client = ApiClient(cfg)
history_api = HistoryApi(client)

def fetch_and_process():
    for inst in SYMBOLS:
        try:
            # fetch raw candles
            resp = history_api.get_intra_day_candle_data(inst, INTERVAL, API_VERSION)
            raw  = resp.data.candles

            # drop the 7th field if present
            if raw and len(raw[0]) == 7:
                raw = [candle[:6] for candle in raw]

            # build a 6-column DataFrame
            df = pd.DataFrame(raw, columns=["ts","open","high","low","close","volume"])
            df["ts"] = pd.to_datetime(df["ts"])
            df = df.sort_values("ts").tail(50).reset_index(drop=True)

            # once we have 26+ bars, compute indicators
            if len(df) >= 26:
                df["ema12"]  = df["close"].ewm(span=12, adjust=False).mean()
                df["ema26"]  = df["close"].ewm(span=26, adjust=False).mean()
                df["macd"]   = df["ema12"] - df["ema26"]
                df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
                df["hist"]   = df["macd"] - df["signal"]
                df["ema20"]  = df["close"].ewm(span=20, adjust=False).mean()

                prev = df.iloc[-2]
                last = df.iloc[-1]

                # extract by key to avoid attribute-method collision
                ts    = last["ts"].strftime("%H:%M")
                close = last["close"]
                ema20 = last["ema20"]
                hist  = last["hist"]
                prev_hist = prev["hist"]

                # print the latest bar + indicators
                print(f"{inst} | {ts}  C:{close:.2f}  EMA20:{ema20:.2f}  Hist:{hist:.6f}")

                # alert on histogram crossover + close > EMA20
                if prev_hist <= 0 < hist:
                    print("🔔 MACD crossover detected")
                if close > ema20:
                    print("🔔 Price above EMA20")
                if hist > 0 and close > ema20:
                    print("🟢 BUY")

        except ApiException as e:
            print(f"API error for {inst}: {e}")
        except Exception as e:
            print(f"Error for {inst}: {e}")

    print("-" * 60)

def main():
    print("🔍 1-min EMA+MACD tester starting… (Ctrl+C to exit)")
    try:
        while True:
            fetch_and_process()
            time.sleep(60)  # wait for next 1-min candle
    except KeyboardInterrupt:
        print("🛑 Exiting tester.")

if __name__ == "__main__":
    main()