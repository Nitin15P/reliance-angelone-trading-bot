# Stock Prediction & Automated Trading Bot

This project provides:
- **A Streamlit dashboard** for viewing live Reliance Industries stock data, quotes, and historical charts.
- **An automated trading bot** that can place buy/sell orders on Angel One based on configurable price thresholds and risk management rules.

---

## Features

- Fetches live and historical stock data using Angel One API and public APIs (MoneyControl, Yahoo Finance).
- Automated trading loop (runs in background) that:
  - Monitors Reliance price at regular intervals.
  - Places a buy order if price drops below a configurable threshold.
  - Implements basic risk management (stop-loss, max trades per day).
  - All trades and actions are logged.
- Manual trading is also supported via the `place_order` method.
- Safety switch: Set `LIVE_TRADING = False` to disable all real trading (safe for demo/testing).

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/reliance-stock-dashboard.git
cd reliance-stock-dashboard
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Angel One API Credentials

Edit `angel_one_api.py` and add your Angel One API credentials:

```python
self.api_key = "YOUR_API_KEY"
self.username = "YOUR_CLIENT_ID"
self.mpin = "YOUR_MPIN"
self.totp_secret = "YOUR_TOTP_SECRET"
```

> **Note:** Never commit your credentials to version control.

### 4. Set Trading Mode

- By default, `LIVE_TRADING = False` (no real trades).
- Set `LIVE_TRADING = True` in `angel_one_api.py` to enable automated trading.

### 5. Run the Dashboard

```bash
streamlit run dashboard_streamlit.py
```

The dashboard will open in your browser.

---

## Project Structure

```
.
├── angel_one_api.py                # Angel One API integration and fallback logic
├── dashboard_streamlit.py          # Streamlit dashboard UI
├── requirements.txt                # Python dependencies
├── .gitignore                      # Ignore logs, credentials, and system files
├── RELIANCE_3months_raw.csv        # Raw historical data (empty by default)
├── RELIANCE_processed_data.csv     # Processed data with indicators (empty by default)
├── logs/                           # (Ignored) Log files
├── Collab.ipynb                    # Jupyter notebook for model development
└── README.md                       # This file
```

---

## Data & Model

- **Data**: CSVs are empty by default. Use the notebook or dashboard to fetch and process data.
- **Model**: LSTM model with PSO hyperparameter tuning (see `Collab.ipynb` for training pipeline).

---

## Risk Management

- **Max trades per day:** Prevents overtrading by limiting the number of trades per day.
- **Stop-loss:** Automatically sells if the price drops below a set percentage from the last buy price.
- **Daily reset:** Trade counters reset at midnight.

---

## Best Practices

- **No Sensitive Data**: All logs, credentials, and user-specific files are excluded via `.gitignore`.
- **Reproducibility**: Anyone can start fresh by adding their credentials and running the dashboard.
- **Fallbacks**: If Angel One API fails, public APIs are used for price data.
- **Extensible**: Add more stocks or strategies by extending the codebase.

---

## Contributing

1. Fork the repo and create your branch.
2. Make your changes.
3. Ensure no credentials or logs are committed.
4. Submit a pull request.

---

## License

MIT License

---

## Disclaimer

This project is for educational purposes only. Use at your own risk. Automated trading involves financial risk. Always test thoroughly with `LIVE_TRADING = False` before enabling real trading.

---
