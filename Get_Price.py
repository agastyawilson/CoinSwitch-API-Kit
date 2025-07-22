import os
import time
import requests
import json
from urllib.parse import urlencode, unquote_plus, urlparse
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from dotenv import load_dotenv  # For loading environment variables from .env files
from typing import Dict, Optional


# --- Load Environment Variables ---
# Load the API keys from the specified .env file
load_dotenv(dotenv_path="path/to/your/secrets.env", override=True)

COINSWITCH_API_KEY = os.getenv("COINSWITCH_API_KEY")
COINSWITCH_SECRET_KEY = os.getenv("COINSWITCH_SECRET_KEY")

if not COINSWITCH_API_KEY or not COINSWITCH_SECRET_KEY:
    raise ValueError("API credentials are missing. Please check your secrets.env file.")


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
            # Prepare the endpoint for signature calculation
            endpoint_for_signature = endpoint
            if method == "GET" and params:
                endpoint_for_signature += (
                    "&" if urlparse(endpoint_for_signature).query else "?"
                ) + urlencode(params)
                endpoint_for_signature = unquote_plus(endpoint_for_signature)

            # Prepare the signature message
            signature_msg = method + endpoint_for_signature + epoch_time
            if payload:
                signature_msg += json.dumps(payload, separators=(",", ":"), sort_keys=True)

            # Generate the signature
            secret_key_bytes = bytes.fromhex(self.secret_key)
            secret_key = Ed25519PrivateKey.from_private_bytes(secret_key_bytes)
            signature_bytes = secret_key.sign(bytes(signature_msg, "utf-8"))
            return signature_bytes.hex()
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

        try:
            # Generate the epoch time and signature
            epoch_time = str(int(time.time() * 1000))
            signature = self._generate_signature(
                method, endpoint, epoch_time, params, payload
            )
            headers["X-AUTH-SIGNATURE"] = signature
            headers["X-AUTH-EPOCH"] = epoch_time

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
        return self._send_request("GET", endpoint, params=params)


# --- Fetch BTC Data (Last 60 Seconds) ---
def fetch_btc_data(api_key: str, secret_key: str):
    """
    Fetches the last 60 seconds of BTC data using the CoinSwitch API.
    """
    # Initialize the API client
    api_client = CoinSwitchAPI(api_key, secret_key)

    try:
        # Define the time range
        end_time_ms = int(time.time() * 1000)  # Current time in milliseconds
        start_time_ms = end_time_ms - (60 * 1000)  # 60 seconds ago

        # Fetch historical candles for BTC/INR
        response = api_client.get_historical_candles(
            symbol="BTC/INR",  # BTC/INR trading pair
            interval="60",  # 1-minute interval
            start_time=start_time_ms,
            end_time=end_time_ms,
            exchange="coinswitchx",  # Replace with the correct exchange if needed
        )

        # Process and display the response
        if response and "data" in response and isinstance(response["data"], list):
            print("BTC Data (Last 60 Seconds):")
            for candle in response["data"]:
                start_time = int(candle.get("start_time", 0))
                close_price = float(candle.get("c", 0))
                print(f"  Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time / 1000))}")
                print(f"  Close Price: {close_price:,.2f} INR")
        else:
            print("No data found for the specified duration.")
    except Exception as e:
        print(f"Error fetching BTC data: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    # Fetch and display BTC data
    fetch_btc_data(COINSWITCH_API_KEY, COINSWITCH_SECRET_KEY)