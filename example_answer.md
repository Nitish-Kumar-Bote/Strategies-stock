# Interview Q&A - Strategies-stock Project

## 1. "Tell me about your project"

This is an **algorithmic options trading system** for the Indian stock market. It monitors 47 NSE stocks plus the BANKNIFTY index, generates **buy/sell signals** using RSI and EMA technical indicators on 5-minute candles, and executes options trades automatically through the Nuva Wealth broker API. The system has four modules — authentication, market data streaming, entry signal generation, and exit management — all running as continuous Python processes.

---

## 2. "Explain the architecture"

The system has **4 modules**:

- **New_Login.py** — Handles Selenium-based automated login with TOTP 2FA. Extracts the `request_token` from the broker and saves it to disk.
- **RSI_NUVA.py** — A context manager that wraps the Nuva Wealth WebSocket streaming API. It subscribes to real-time quotes and collects bid/ask and price data via callbacks.
- **RSIBUY.py** — The entry signal engine. It runs in a loop every 60 seconds, fetches 5-minute OHLCV data for all 48 tickers, computes RSI(14) and EMA(20), and when entry conditions are met, writes a position file to the `rsi_sand/` directory.
- **STOPBUY.py** — The exit manager. It reads active positions from `rsi_sand/`, monitors each one for EMA-based trend reversals (stop-loss), tracks PnL in real time, and archives completed trades to `history_data/`.

RSIBUY and STOPBUY communicate through **file-based IPC** — CSV files in a shared directory. One writes, the other reads and archives.

---

## 3. "What is your strategy logic?"

**Entry:**

- **Bullish (Green)**: RSI crosses above 60 AND price is above EMA(20) → Buy an OTM Call option
- **Bearish (Red)**: RSI crosses below 40 AND price is below EMA(20) → Buy an OTM Put option

I use **two confirmations** — RSI for momentum and EMA for trend direction. This avoids false signals from using RSI alone.

**Option Selection:**

- Finds the nearest Thursday expiry
- Selects one strike OTM from ATM
- Trades April futures options on NFO

**Exit:**

- For Calls: Exit when EMA(20) crosses below price (uptrend breaks)
- For Puts: Exit when EMA(20) crosses above price (downtrend breaks)

---

## 4. "Why RSI + EMA together?"

RSI alone gives **overbought/oversold** signals but produces many false positives in a trending market. EMA alone tells you the **trend direction** but doesn't tell you when to enter. Combining both gives a **momentum + trend confirmation** — RSI identifies the momentum shift, and EMA confirms the trend is in the right direction. This filters out a lot of noise.

---

## 5. "What indicators are you using and what are the parameters?"

- **RSI (Relative Strength Index)** with period 14 — measures momentum on a 0-100 scale. I use 60 as the bullish threshold and 40 as the bearish threshold, not the standard 70/30, because I want to **catch the trend early** rather than wait for extreme levels.
- **EMA (Exponential Moving Average)** with span 20 — gives more weight to recent prices compared to SMA. Used as a trend filter — price above EMA means uptrend, below means downtrend.
- **Timeframe**: 5-minute candles for intraday precision.

---

## 6. "How does the data flow work?"

1. First, `New_Login.py` authenticates via Selenium, extracts the `request_token`, and saves it to a file.
2. `RSIBUY.py` reads that token, activates the API session, and loops through all 48 tickers every 60 seconds:
   - Fetches 5-min OHLCV using the broker's historical data API
   - Calculates RSI and EMA
   - Checks entry conditions
   - If a signal triggers, it finds the appropriate OTM option and writes a CSV to `rsi_sand/`
3. `STOPBUY.py` reads from `rsi_sand/`, gets live prices via WebSocket streaming, calculates PnL, checks exit conditions, appends state to the CSV each minute, and moves the file to `history_data/` when the trade closes.

The inter-process communication is **file-based** — RSIBUY writes files, STOPBUY reads and archives them.

---

## 7. "How are you getting real-time market data?"

Through the **Nuva Wealth streaming API** wrapped in `RSI_NUVA.py`. It uses WebSocket-based quote streaming. I implemented it as a **context manager** (with `__enter__`/`__exit__`) so the usage is clean:

```python
with inter(symbol, nuva, 'd2') as data:
    # data collected via callback
```

The callback receives JSON responses, parses the relevant fields, and collects them in a list. After 1 second it unsubscribes and returns the data.

---

## 8. "How does authentication work?"

The broker uses a **three-legged OAuth flow**:

1. `New_Login.py` opens a Chrome browser via Selenium
2. It navigates to the Nuva Wealth login URL, enters the user ID and password
3. It generates a **TOTP** using the `pyotp` library (same as Google Authenticator) and enters the 6-digit code
4. After successful login, the browser redirects to a callback URL containing the `request_token`
5. The script extracts that token from the URL and saves it to disk
6. The trading modules then use this `request_token` along with the API key and secret to generate the final `access_token` for all API calls

---

## 9. "What tech stack are you using?"

- **Python 3** as the language
- **Nuva Wealth APIConnect SDK** for broker integration
- **Selenium WebDriver** with ChromeDriver for automated login
- **pyotp** for TOTP-based 2FA
- **pandas and numpy** for indicator calculations
- **WebSocket** (via broker SDK) for real-time streaming
- **CSV files** for inter-process communication and trade logging

---

## 10. "What challenges did you face?"

- **Authentication automation**: Automating the 2FA login with TOTP required careful timing and Selenium element handling.
- **Real-time data reliability**: WebSocket connections can drop, so I implemented retry logic (up to 10 attempts) for streaming data.
- **Option chain navigation**: Finding the correct ATM strike and then selecting the OTM option required parsing the full instruments database and matching by expiry, strike, and option type.
- **Process synchronization**: Since RSIBUY and STOPBUY run as separate processes, I had to use file-based IPC. I used directory-based signaling — RSIBUY creates files, STOPBUY reads and moves them when done.

---

## 11. "How do you handle errors?"

- API calls are wrapped in **retry loops** (up to 10 attempts) to handle transient network issues
- The main loop in RSIBUY wraps each ticker's processing in a try-except so one stock failure doesn't crash the entire scanner
- File operations in STOPBUY have specific exception handling for file moves
- The streaming context manager auto-unsubscribes on exit via `__exit__`

---

## 12. "Why file-based IPC and not a database?"

For this scale — monitoring 48 tickers with simple position data — CSV files are simple, human-readable, and require no additional infrastructure. Each position is one file, so there's no contention. For a production system with higher throughput, I would move to a proper database like SQLite or Redis.

---

## Quick-Hit Answers

**"What is RSI?"**
A momentum oscillator between 0-100 that measures the speed of price changes. Calculated from average gains vs average losses over N periods.

**"What is EMA?"**
A moving average that gives exponentially more weight to recent prices. Reacts faster to price changes than SMA.

**"Why 5-minute candles?"**
Good balance between noise and responsiveness for intraday options trading. Smaller timeframes have too much noise; larger ones are too slow.

**"Why OTM options?"**
Lower premium cost, higher leverage. Combined with a momentum strategy, OTM options offer better risk-reward when the signal is correct.

---

## Roles and Responsibilities

### Role: Python Developer / Algorithmic Trading Developer

---

### 1. System Design & Architecture

- Designed the overall architecture of the algorithmic trading system with 4 modular components (Authentication, Streaming, Entry Engine, Exit Manager)
- Separated concerns — authentication module independent of strategy logic, data streaming abstracted as a reusable context manager
- Designed the file-based inter-process communication pattern between RSIBUY and STOPBUY using CSV as the lightweight IPC mechanism
- Planned the data pipeline: API authentication → historical data fetch → indicator computation → signal generation → position tracking → trade archival

### 2. Authentication Module (New_Login.py)

- Implemented automated broker login using Selenium WebDriver
- Integrated TOTP-based 2FA automation using the `pyotp` library to handle the broker's two-factor authentication
- Built the `request_token` extraction logic by parsing the redirected callback URL after successful login
- Managed secure credential handling by reading API keys from CSV configuration files

### 3. Market Data Streaming (RSI_NUVA.py)

- Developed a context manager class (`inter`) for the Nuva Wealth WebSocket streaming API
- Implemented callback-based data collection for real-time bid/ask and price feeds
- Handled subscription and unsubscription lifecycle for quote feeds
- Supported multiple streaming types (`a9`, `d2`, `b0`, `b1`) for different data fields

### 4. Strategy & Indicator Implementation (RSIBUY.py)

- Implemented the **RSI (Relative Strength Index)** indicator from scratch using pandas EWM smoothing on gains/losses
- Implemented the **EMA (Exponential Moving Average)** indicator using pandas `ewm()` with configurable span
- Built the core signal logic:
  - Green signal: RSI crosses above 60 + Price > EMA(20) → Buy OTM Call
  - Red signal: RSI crosses below 40 + Price < EMA(20) → Buy OTM Put
- Developed the option chain scanner to find ATM strikes and select appropriate OTM options based on signal direction
- Built the instruments database parser to match tickers with their exchange tokens and futures contracts
- Implemented the 5-minute OHLCV data fetcher using the broker's intraday chart API

### 5. Position Management & Exit Logic (STOPBUY.py)

- Developed the exit signal engine that monitors active positions in real time
- Implemented stop-loss logic based on EMA trend reversal detection
- Built PnL tracking by comparing entry price with live market price from WebSocket streaming
- Designed the position lifecycle: active CSV in `rsi_sand/` → state updates appended each cycle → archived to `history_data/` on exit
- Managed file operations for moving completed trades to the history directory

### 6. API Integration

- Integrated the Nuva Wealth (formerly Kite Connect) broker API for order execution, historical data, and streaming
- Worked with API constants: `AssetTypeEnum`, `ChartExchangeEnum`, `IntradayIntervalEnum` for correct market segment targeting
- Handled API session management — token generation, session activation, and token refresh

### 7. Testing & Monitoring

- Tested the RSI and EMA calculations against known values to ensure indicator accuracy
- Validated signal generation by running the scanner on historical market hours and cross-checking signals
- Monitored live trade execution and verified that entry/exit signals triggered at correct price levels
- Tracked PnL across multiple trades to evaluate strategy performance

### 8. Deployment & Operations

- Set up the multi-process execution model: RSIBUY and STOPBUY running as separate continuous processes
- Managed the startup sequence: authentication first, then entry scanner, then exit manager
- Configured the directory structure for active positions (`rsi_sand/`) and trade history (`history_data/`)
- Maintained the instruments CSV database with up-to-date contract information for each expiry cycle
