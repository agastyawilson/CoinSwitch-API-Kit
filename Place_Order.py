import os
import time
import json
import requests
import urllib.parse
import urllib3
from urllib.parse import urlencode, unquote_plus, urlparse
from cryptography.hazmat.primitives.asymmetric import ed25519
from dotenv import load_dotenv
from typing import Dict, Optional


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# --- Load Environment Variables ---
load_dotenv(
    dotenv_path="path/to/your/secrets.env",
    override=True,
)

COINSWITCH_API_KEY = "KEY_HERE"
COINSWITCH_SECRET_KEY = "SECRET_KEY_HERE"

if not COINSWITCH_API_KEY or not COINSWITCH_SECRET_KEY:
    raise ValueError(
        "API credentials are missing. Please check your secrets.env file."
    )


# --- CoinSwitchAPI Class ---
class CoinSwitchAPI:
    BASE_URL = "https://coinswitch.co"  # Base URL for the CoinSwitch API

    def __init__(self, api_key: str, secret_key: str):
        """
        Initialize the API client with the API key and secret key.
        """
        self.api_key = api_key
        self.secret_key = secret_key

    def _generate_signature(
        self,
        method: str,
        endpoint: str,
        epoch_time: str,
        params: Optional[Dict] = None,
        payload: Optional[Dict] = None,
    ) -> str:
        """
        Generates the Ed25519 signature required for authenticated requests.
        """
        try:
            unquote_endpoint = endpoint
            if method == "GET" and params and len(params) != 0:
                endpoint += ('&', '?')[urlparse(endpoint).query == ''] + urlencode(params)
                unquote_endpoint = urllib.parse.unquote_plus(endpoint)

            signature_msg = method + unquote_endpoint + epoch_time

            request_string = bytes(signature_msg, 'utf-8')
            secret_key_bytes = bytes.fromhex(self.secret_key)
            secret_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_key_bytes)
            signature_bytes = secret_key.sign(request_string)
            signature = signature_bytes.hex()
            return signature
        except Exception as e:
            raise ValueError(f"Error generating signature: {e}")

    def _send_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        payload: Optional[Dict] = None,
    ) -> Dict:
        """
        Sends an HTTP request to the CoinSwitch API.
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "X-AUTH-APIKEY": self.api_key,
        }

        # Generate the epoch time once and use it for both header and signature
        try:
            epoch_time = str(int(time.time() * 1000))
            signature = self._generate_signature(
                method, endpoint, epoch_time, params, payload
            )
            headers["X-AUTH-SIGNATURE"] = signature
            headers["X-AUTH-EPOCH"] = epoch_time
        except ValueError as e:
            raise ValueError(f"Failed to generate signature: {e}")

        try:
            # Send the request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params if method == "GET" else None,
                json=payload if method in ["POST", "DELETE"] else None,
                timeout=10,
            )
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during API request: {e}")

    # --- API Methods ---
    def get_historical_candles(
        self, symbol: str, interval: str, start_time: int, end_time: int, exchange: str
    ) -> Dict:
        """
        Fetches historical candle data for a cryptocurrency.
        """
        endpoint = "/trade/api/v2/candles"
        params = {
            "symbol": symbol,
            "interval": interval,
            "start_time": start_time,
            "end_time": end_time,
            "exchange": exchange,
        }
        try:
            return self._send_request("GET", endpoint, params=params)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch historical candles: {e}")

    def get_current_price_from_candle(
        self, symbol: str, exchange: str
    ) -> Optional[float]:
        """
        Fetches the current approximate price of a symbol using the latest 1-minute candle.
        This uses the historical candles endpoint as a proxy for a real-time ticker.
        Returns None if price cannot be fetched.
        """
        try:
            end_time_ms = int(time.time() * 1000)
            # Request data for the last 5 minutes (to be safe and get at least one candle)
            start_time_ms = end_time_ms - (5 * 60 * 1000)  # 5 minutes ago

            print(
                f"DEBUG: Attempting to fetch latest 1-min candle for {symbol} on {exchange} "
                f"(from {start_time_ms} to {end_time_ms})..."
            )
            candles_response = self.get_historical_candles(
                symbol=symbol,
                interval="1",  # 1-minute interval for the most recent data
                start_time=start_time_ms,
                end_time=end_time_ms,
                exchange=exchange,
            )

            # --- Critical Debugging Output ---
            print(f"DEBUG: Raw candles_response received:\n{json.dumps(candles_response, indent=4)}")
            # --- End Critical Debugging Output ---
            if (
                candles_response
                and "data" in candles_response
                and isinstance(candles_response["data"], list)
                and candles_response["data"] # Check if the list is non-empty
            ):
                # The API typically returns candles in reverse chronological order (newest first)
                latest_candle = candles_response["data"][0] # CORRECTED: Access "data" key
                close_price_str = latest_candle.get("c")
                if close_price_str:
                    price = float(close_price_str)
                    print(
                        f"DEBUG: Latest approximate close price from candle for {symbol}: {price}"
                    )
                    return price
                else:
                    print(
                        f"WARNING: 'c' (close price) key not found in latest candle, "
                        f"or its value is empty for {symbol}. Latest candle data: {json.dumps(latest_candle, indent=4)}"
                    )
            else:
                print(
                    f"WARNING: No valid candle data (empty 'data' list or missing 'data' key) "
                    f"found for {symbol} in response."
                )
            return None
        except Exception as e:
            print(f"ERROR: Failed to get current price from candle for {symbol}: {e}")
            return None

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,  # MUST be 'LIMIT' as per docs (Page 15)
        quantity: float,
        exchange: str,
        price: float,  # Price is MANDATORY for 'LIMIT' orders (Page 15)
    ) -> Dict:
        """
        Places a buy or sell order.
        Note: CoinSwitch API currently supports only 'LIMIT' order type for direct placement.
        """
        endpoint = "/trade/api/v2/order"
        payload = {
            "side": side,
            "symbol": symbol,
            "type": order_type,  # Explicitly using 'LIMIT' as required by docs
            "quantity": quantity,
            "exchange": exchange,
            "price": price,  # Mandatory for LIMIT orders
        }
        try:
            print("Placing order payload:", payload)
            return self._send_request("POST", endpoint, payload=payload)
        except Exception as e:
            raise RuntimeError(f"Failed to place order: {e}")

    def get_order_details(self, order_id: str) -> Dict:
        """
        Fetches details of a specific order.
        """
        endpoint = "/trade/api/v2/order"
        params = {"order_id": order_id}
        try:
            return self._send_request("GET", endpoint, params=params)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch order details: {e}")


# --- Main Script for Demonstration ---
if __name__ == "__main__":
    # Initialize the API client
    api_client = CoinSwitchAPI(COINSWITCH_API_KEY, COINSWITCH_SECRET_KEY)

    # --- Attempting to Place a 100 INR BTC Limit Order ---
    print("\n--- Attempting to Place a 1000 INR BTC Limit Order ---")
    TARGET_INR_AMOUNT = 10000
    TRADE_SYMBOL = "BTC/INR"
    TRADE_EXCHANGE = "coinswitchx"

    try:
        # 1. Get the current approximate price using candle data
        current_btc_price = api_client.get_current_price_from_candle(
            TRADE_SYMBOL, TRADE_EXCHANGE
        )

        if current_btc_price:
            # 2. Calculate the BTC quantity needed for the target INR amount
            btc_quantity = TARGET_INR_AMOUNT / current_btc_price
            btc_quantity = round(
                btc_quantity, 6
            )  # Round to 6 decimal places for quantity

            # The price for a LIMIT order needs to be the specific price you want to pay.
            # We'll use the fetched current_btc_price directly as the limit price.
            order_price = current_btc_price

            print(
                f"Calculated BTC quantity for {TARGET_INR_AMOUNT} INR "
                f"at price {order_price}: {btc_quantity} BTC (rounded to 6 decimal places)"
            )

            # 3. Perform a quick check for calculated quantity (should not be zero/negative)
            if btc_quantity <= 0.0:
                print(
                    "ERROR: Calculated BTC quantity is zero or negative. "
                    "Cannot place order. Adjust TARGET_INR_AMOUNT or check price."
                )
            else:
                # 4. Confirmation for live trade (CRITICAL!)
                confirm = input(
                    f"WARNING: This will attempt to place a LIVE LIMIT BUY order for {btc_quantity} {TRADE_SYMBOL} "
                    f"at price {order_price}.\nAre you sure you want to proceed? (yes/no): "
                ).lower()

                if confirm == "yes":
                    print(
                        f"Placing a LIMIT BUY order for {btc_quantity} {TRADE_SYMBOL} at price {order_price}..."
                    )
                    # 5. Place the order
                    order_response = api_client.place_order(
                        symbol=TRADE_SYMBOL,
                        side="BUY",
                        order_type="LIMIT",  # IMPORTANT: As per docs, only LIMIT is supported
                        quantity=btc_quantity,
                        exchange=TRADE_EXCHANGE,
                        price=order_price,  # IMPORTANT: Price is mandatory for LIMIT orders
                    )
                    print(
                        "Order Placement Response:",
                        json.dumps(order_response, indent=4),
                    )

                    # --- Optional: Check order status after placing ---
                    if (
                        order_response
                        and "order_id" in order_response
                        and order_response["order_id"]
                    ):
                        order_id = order_response["order_id"]
                        print(f"\nFetching details for new order_id: {order_id}...")
                        time.sleep(2)  # Give a small moment for order to process
                        order_details = api_client.get_order_details(order_id)
                        print("Order Details:", json.dumps(order_details, indent=4))
                    elif "message" in order_response:
                        print(
                            f"Order placement failed with message: {order_response['message']}"
                        )
                    else:
                        print(
                            "Order placement response did not contain an order_id or explicit error message."
                        )

                else:
                    print("Order placement cancelled by user.")
        else:
            print(f"Could not get current price for {TRADE_SYMBOL}. Cannot place order.")
    except Exception as e:
        print(f"Error placing order: {e}")

    print("\n--- Script finished ---")