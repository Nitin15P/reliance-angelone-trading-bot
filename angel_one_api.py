from SmartApi import SmartConnect
import pyotp
import pandas as pd
from datetime import datetime
import time
import logging
import requests
import os
import threading

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AngelOneAPI")

API_KEY = os.getenv("ANGEL_API_KEY")

LIVE_TRADING = False

class AngelOneAPI:
    def __init__(self):
        # Please add your Angel One API credentials below
        self.api_key = ""  # Add your API Key here
        self.username = ""  # Add your AngelOne Client ID here
        self.mpin = ""      # Add your MPIN here
        self.totp_secret = ""  # Add your TOTP Secret here

        if not all([self.api_key, self.username, self.mpin, self.totp_secret]):
            raise ValueError("Please set your Angel One API credentials in angel_one_api.py")

        # Connect to Angel One
        self.smart_api = None
        self.auth_token = None
        self.refresh_token = None
        self.feed_token = None
        
        # Default token for Reliance Industries
        self.reliance_token = {
            "exchange": "NSE",
            "token": "2885",  # Reliance NSE token
            "symbol": "RELIANCE-EQ"
        }
        
        # Connection status
        self.is_connected = False
        
        # Last price cache
        self.last_price = None
        self.last_price_time = None
        
    def connect(self):
        """Connect to Angel One API"""
        try:
            self.smart_api = SmartConnect(self.api_key)
            
            # Generate TOTP
            totp = pyotp.TOTP(self.totp_secret).now()
            
            # Generate Session (Login)
            data = self.smart_api.generateSession(self.username, self.mpin, totp)
            
            # Check for login errors
            if data.get('status') == False:
                logger.error(f"Login Failed: {data['message']}")
                self.is_connected = False
                return False
            
            # If login is successful
            logger.info("Login Successful!")
            
            # Fetch session tokens
            self.auth_token = data['data']['jwtToken']
            self.refresh_token = data['data']['refreshToken']
            
            # Fetch feed token
            self.feed_token = self.smart_api.getfeedToken()
            
            self.is_connected = True
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Angel One API: {str(e)}")
            self.is_connected = False
            return False
            
    def get_reliance_ltp(self):
        """Get Last Traded Price for Reliance Industries"""
        try:
            # Check if we're connected
            if not self.is_connected:
                self.connect()
                if not self.is_connected:
                    logger.error("Unable to connect to Angel One API")
                    return None
                
            # Check if we have a recent price (within 5 seconds)
            current_time = time.time()
            if self.last_price and self.last_price_time and (current_time - self.last_price_time < 5):
                return self.last_price
                
            # Correct format for ltpData - it needs to be called properly
            exchange = self.reliance_token["exchange"]
            token = self.reliance_token["token"]
            symbol = self.reliance_token["symbol"]
            
            # Fix: Call ltpData correctly with the exchange and the symbol arguments separately
            ltp_data = self.smart_api.ltpData(exchange, symbol, token)
            
            if ltp_data and ltp_data.get('status') and ltp_data.get('data'):
                price = ltp_data['data'].get('ltp')
                if price:
                    # Cache the price
                    self.last_price = price
                    self.last_price_time = current_time
                    return price
            
            logger.error(f"Error getting LTP data: {ltp_data}")
            return self.get_reliance_price_fallback()
            
        except Exception as e:
            logger.error(f"Error fetching Reliance LTP: {str(e)}")
            return self.get_reliance_price_fallback()
            
    def get_reliance_price_fallback(self):
        """Alternative method to get Reliance price if API fails"""
        try:
            # Try MoneyControl API
            url_mc = "https://priceapi.moneycontrol.com/pricefeed/nse/equitycash/RIL"
            response = requests.get(url_mc, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and data.get('data') and data['data'].get('pricecurrent'):
                    price = float(data['data']['pricecurrent'])
                    self.last_price = price
                    self.last_price_time = time.time()
                    return price
        except Exception as e:
            logger.warning(f"MoneyControl fallback failed: {str(e)}")

        try:
            # Try Yahoo Finance API
            url_yahoo = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=RELIANCE.NS"
            response = requests.get(url_yahoo, timeout=5)
            if response.status_code == 200:
                data = response.json()
                quote = data.get("quoteResponse", {}).get("result", [])
                if quote and quote[0].get("regularMarketPrice"):
                    price = float(quote[0]["regularMarketPrice"])
                    self.last_price = price
                    self.last_price_time = time.time()
                    return price
        except Exception as e:
            logger.warning(f"Yahoo Finance fallback failed: {str(e)}")

        logger.error("All fallback methods failed. Price unavailable.")
        return None
            
    def get_quote(self, exchange="NSE", symbol="RELIANCE-EQ", token="2885"):
        """Get full quote for a symbol"""
        try:
            # Check if we're connected
            if not self.is_connected:
                self.connect()
                if not self.is_connected:
                    logger.error("Unable to connect to Angel One API")
                    return None
                    
            # Fix: Call ltpData with correct parameter format
            quote_data = self.smart_api.ltpData(exchange, symbol, token)
            return quote_data
            
        except Exception as e:
            logger.error(f"Error fetching quote: {str(e)}")
            return None
            
    def get_historical_data(self, exchange="NSE", symbol="RELIANCE-EQ", token="2885", 
                           interval="ONE_DAY", from_date=None, to_date=None):
        """Get historical data for a symbol"""
        try:
            # Check if we're connected
            if not self.is_connected:
                self.connect()
                if not self.is_connected:
                    logger.error("Unable to connect to Angel One API")
                    return None
                    
            # Set default dates if not provided
            if not from_date:
                from_date = (datetime.now().date() - pd.Timedelta(days=30)).strftime("%Y-%m-%d")
            if not to_date:
                to_date = datetime.now().date().strftime("%Y-%m-%d")
                
            # Get historical data
            historical_params = {
                "exchange": exchange,
                "symboltoken": token,
                "interval": interval,
                "fromdate": from_date,
                "todate": to_date
            }
            
            historical_data = self.smart_api.getCandleData(historical_params)
            return historical_data
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return None
            
    def disconnect(self):
        """Terminate the API session"""
        try:
            if self.smart_api:
                self.smart_api.terminateSession(self.username)
                self.is_connected = False
                logger.info("Disconnected from Angel One API")
                
        except Exception as e:
            logger.error(f"Error disconnecting from Angel One API: {str(e)}")

    def place_order(self, variety, tradingsymbol, symboltoken, transactiontype, exchange, ordertype, producttype, duration, price=0, squareoff=0, stoploss=0, quantity=1):
        """
        Place an order if LIVE_TRADING is True. Otherwise, log and skip.
        """
        if not LIVE_TRADING:
            logger.info(f"Order NOT placed (LIVE_TRADING=False): {transactiontype} {quantity} {tradingsymbol} at {price}")
            return {"status": False, "message": "LIVE_TRADING is disabled. Order not placed."}
        try:
            if not self.is_connected:
                self.connect()
                if not self.is_connected:
                    logger.error("Unable to connect to Angel One API for placing order")
                    return {"status": False, "message": "Connection failed"}
            order_params = {
                "variety": variety,
                "tradingsymbol": tradingsymbol,
                "symboltoken": symboltoken,
                "transactiontype": transactiontype,
                "exchange": exchange,
                "ordertype": ordertype,
                "producttype": producttype,
                "duration": duration,
                "price": price,
                "squareoff": squareoff,
                "stoploss": stoploss,
                "quantity": quantity
            }
            response = self.smart_api.placeOrder(order_params)
            logger.info(f"Order placed: {response}")
            return response
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return {"status": False, "message": str(e)}

    def start_automated_trading(self, price_threshold=2500, check_interval=60, max_trades_per_day=5, stop_loss_pct=0.02):
        """
        Start an automated trading loop that buys if price < price_threshold.
        Adds basic risk management and exit conditions.
        """
        if not LIVE_TRADING:
            logger.info("Automated trading not started because LIVE_TRADING is False.")
            return

        trades_today = 0
        last_buy_price = None
        last_trade_date = datetime.now().date()

        def trading_loop():
            nonlocal trades_today, last_buy_price, last_trade_date
            logger.info("Automated trading started.")
            while LIVE_TRADING:
                try:
                    # Reset trades if the date has changed
                    current_date = datetime.now().date()
                    if current_date != last_trade_date:
                        trades_today = 0
                        last_buy_price = None
                        last_trade_date = current_date

                    if trades_today >= max_trades_per_day:
                        logger.info("Max trades per day reached. Pausing automated trading until tomorrow.")
                        time.sleep(60 * 60)  # Sleep for 1 hour before checking again
                        continue

                    price = self.get_reliance_ltp()
                    if price is not None:
                        logger.info(f"Checked Reliance price: {price}")

                        # Risk management: Stop-loss check
                        if last_buy_price and price < last_buy_price * (1 - stop_loss_pct):
                            logger.info(f"Stop-loss triggered! Price {price} < {last_buy_price * (1 - stop_loss_pct)}. Placing SELL order.")
                            self.place_order(
                                variety="NORMAL",
                                tradingsymbol=self.reliance_token["symbol"],
                                symboltoken=self.reliance_token["token"],
                                transactiontype="SELL",
                                exchange=self.reliance_token["exchange"],
                                ordertype="MARKET",
                                producttype="INTRADAY",
                                duration="DAY",
                                quantity=1
                            )
                            last_buy_price = None
                            trades_today += 1
                            time.sleep(check_interval)
                            continue

                        # Entry condition
                        if price < price_threshold:
                            logger.info(f"Price below threshold ({price} < {price_threshold}), placing BUY order.")
                            order_resp = self.place_order(
                                variety="NORMAL",
                                tradingsymbol=self.reliance_token["symbol"],
                                symboltoken=self.reliance_token["token"],
                                transactiontype="BUY",
                                exchange=self.reliance_token["exchange"],
                                ordertype="MARKET",
                                producttype="INTRADAY",
                                duration="DAY",
                                quantity=1
                            )
                            if order_resp.get("status"):
                                last_buy_price = price
                                trades_today += 1
                        else:
                            logger.info(f"Price above threshold ({price} >= {price_threshold}), no action.")
                    else:
                        logger.warning("Could not fetch Reliance price.")
                except Exception as e:
                    logger.error(f"Automated trading loop error: {str(e)}")
                time.sleep(check_interval)
        thread = threading.Thread(target=trading_loop, daemon=True)
        thread.start()

# Create a singleton instance
angel_api = AngelOneAPI()

# Function to get current Reliance price
def get_reliance_price():
    """Get current price of Reliance Industries stock"""
    try:
        price = angel_api.get_reliance_ltp()
        if price:
            return price
        else:
            return None  # No hardcoded fallback
    except Exception as e:
        logger.error(f"Error in get_reliance_price: {str(e)}")
        return None

# Start automated trading if LIVE_TRADING is True
if LIVE_TRADING:
    # You can adjust the threshold, interval, max trades, and stop-loss as needed
    angel_api.start_automated_trading(price_threshold=2500, check_interval=60, max_trades_per_day=5, stop_loss_pct=0.02)