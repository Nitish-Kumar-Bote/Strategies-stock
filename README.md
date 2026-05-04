# Strategies-stock

Algorithmic options trading system for Indian stock markets (NSE/BSE) using **RSI + EMA** strategies via the Nuva Wealth API.

## Architecture

```
┌──────────────────────┐
│     New_Login.py     │
│   Authentication &   │
│   Session Setup      │
└──────────┬───────────┘
           │ request_token (saved to disk)
           ▼
┌──────────────────────────────────────────────────────┐
│                    RSI_NUVA.py                        │
│              Market Data Streaming                    │
│                                                       │
│  Context manager wrapping Nuva Wealth WebSocket feed │
│  Supplies real-time quotes to strategy modules        │
└─────────┬──────────────────────────┬─────────────────┘
          │                          │
          ▼                          ▼
┌──────────────────────┐   ┌──────────────────────┐
│     RSIBUY.py        │   │     STOPBUY.py       │
│   Entry Signals      │   │   Exit Management    │
│                      │   │                      │
│  Scans 47 NSE stocks │   │  Monitors active     │
│  + BANKNIFTY index   │   │  positions from      │
│  for RSI+EMA entries │   │  rsi_sand/ directory │
│                      │   │                      │
│  Writes new positions│   │  Checks stop-loss,   │
│  to rsi_sand/        │   │  archives completed  │
│                      │   │  trades to           │
│                      │   │  history_data/       │
└──────────────────────┘   └──────────────────────┘
          │                          │
          ▼                          ▼
┌──────────────────────────────────────────────────────┐
│              Nuva Wealth Trading API                  │
│                                                       │
│  - Authentication (API key + secret + request_token)  │
│  - Historical OHLCV (5-min candles)                   │
│  - Real-time streaming quotes (WebSocket)             │
│  - Order execution                                    │
└──────────────────────────────────────────────────────┘
```

## File Descriptions

| File | Purpose |
|---|---|
| `New_Login.py` | Automated browser login to Nuva Wealth using Selenium + TOTP 2FA. Extracts `request_token` and saves it for other modules. |
| `RSI_NUVA.py` | Context manager for real-time market data streaming. Wraps Nuva Wealth's WebSocket quote feed with callback-based data collection. |
| `RSIBUY.py` | Entry signal scanner. Monitors 47 NSE stocks + BANKNIFTY, calculates RSI(14) and EMA(20) on 5-minute candles, and writes new position files when signals trigger. |
| `STOPBUY.py` | Exit signal manager. Reads active positions from `rsi_sand/`, monitors EMA trend reversals for stop-loss, tracks PnL, and archives completed trades to `history_data/`. |

## Strategy Logic

### Entry Conditions (RSIBUY)

| Signal | RSI | Price vs EMA(20) | Option |
|---|---|---|---|
| **Green** (bullish) | Crosses above 60 | Price > EMA | Buy OTM Call |
| **Red** (bearish) | Crosses below 40 | Price < EMA | Buy OTM Put |

- **Timeframe**: 5-minute candles
- **Instruments**: April futures options on NFO
- **Option Selection**: Nearest Thursday expiry, one strike OTM from ATM

### Exit Conditions (STOPBUY)

| Position | Exit when |
|---|---|
| Call (long) | EMA(20) < Price (uptrend breaks) |
| Put (long) | EMA(20) > Price (downtrend breaks) |

Positions are checked every 60 seconds. Completed trades are moved to `history_data/` with full indicator history.

## Data Flow

```
1. New_Login.py
   └─ Selenium login → extracts request_token → saves to nuvarequest_token.txt

2. RSIBUY.py (runs continuously, 60s interval)
   └─ Activate session with request_token
   └─ For each of 48 tickers:
       ├─ Fetch 5-min OHLCV via API
       ├─ Calculate RSI(14) and EMA(20)
       ├─ Check entry conditions
       └─ If signal → write CSV to rsi_sand/{ticker}.csv

3. STOPBUY.py (runs continuously, 60s interval)
   └─ Read all CSVs from rsi_sand/
   └─ For each active position:
       ├─ Fetch current market price via streaming
       ├─ Calculate PnL
       ├─ Check exit conditions (EMA crossover)
       ├─ Append state row to CSV
       └─ If stopped → move CSV to history_data/
```

## Monitored Stocks

47 NSE stocks + BANKNIFTY index:

```
SAIL, ADANIENT, ADANIPORTS, APOLLOHOSP, ASIANPAINT, AXISBANK, BAJAJ-AUTO,
BAJFINANCE, BAJAJFINSV, BPCL, BHARTIARTL, BRITANNIA, CIPLA, COALINDIA,
DIVISLAB, DRREDDY, EICHERMOT, GRASIM, HCLTECH, HDFCBANK, HDFCLIFE,
HEROMOTOCO, HINDALCO, HINDUNILVR, HDFC, ICICIBANK, ITC, INDUSINDBK, INFY,
JSWSTEEL, KOTAKBANK, LT, M&M, MARUTI, NTPC, NESTLEIND, ONGC, POWERGRID,
RELIANCE, SBILIFE, SBIN, SUNPHARMA, TCS, TATACONSUM, TATAMOTORS, TATASTEEL,
TECHM, TITAN, UPL, ULTRACEMCO, WIPRO, BANKNIFTY
```

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3 |
| Broker API | Nuva Wealth APIConnect SDK |
| Browser Automation | Selenium WebDriver + ChromeDriver |
| 2FA | pyotp (TOTP) |
| Data Analysis | pandas, numpy |
| Streaming | WebSocket (via Nuva SDK) |
| IPC | File-based (CSV in shared directories) |

## External File Dependencies

| File | Used By | Purpose |
|---|---|---|
| `~/Desktop/Kiteconnect/Carry.csv` | New_Login.py | API credentials for login |
| `~/Desktop/Kiteconnect/IRYS.csv` | RSIBUY.py, STOPBUY.py | API credentials for trading |
| `~/Desktop/Kiteconnect/python-settings.ini` | All modules | API configuration |
| `~/Downloads/nuvarequest_token.txt` | RSIBUY.py, STOPBUY.py | Auth token (generated by New_Login.py) |
| `~/Desktop/instruments.csv` | RSIBUY.py, STOPBUY.py | Full instruments database |
| `~/Desktop/Kiteconnect/chromedriver.exe` | New_Login.py | Selenium Chrome driver |

## Output Directories

| Directory | Written By | Purpose |
|---|---|---|
| `~/Desktop/RSI_EMA/rsi_sand/` | RSIBUY.py | Active position CSVs |
| `~/Desktop/RSI_EMA/history_data/` | STOPBUY.py | Archived completed trades |

## Startup Sequence

```bash
# 1. Authenticate (generates request token)
python New_Login.py

# 2. Start entry scanner (leave running)
python RSIBUY.py

# 3. Start exit manager (leave running, in separate terminal)
python STOPBUY.py
```

Both RSIBUY and STOPBUY run as infinite loops with 60-second polling intervals. RSIBUY creates new position files; STOPBUY consumes and archives them.
