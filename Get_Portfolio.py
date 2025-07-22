import os
import time
import requests
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from dotenv import load_dotenv
from typing import Dict, Optional


# --- Load Environment Variables ---
load_dotenv(dotenv_path="path/to/your/secrets.env", override=True)

COINSWITCH_API_KEY = os.getenv("COINSWITCH_API_KEY")
COINSWITCH_SECRET_KEY = os.getenv("COINSWITCH_SECRET_KEY")

if not COINSWITCH_API_KEY or not COINSWITCH_SECRET_KEY:
    raise ValueError("API credentials are missing. Please check your secrets.env file.")


# --- CoinSwitchAPI Class ---
class CoinSwitchAPI:
    BASE_URL = "https://coinswitch.co"

    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key

    def _generate_signature(self, method: str, endpoint: str, epoch_time: str) -> str:
        try:
            signature_msg = method + endpoint + epoch_time
            secret_key_bytes = bytes.fromhex(self.secret_key)
            secret_key = Ed25519PrivateKey.from_private_bytes(secret_key_bytes)
            signature_bytes = secret_key.sign(bytes(signature_msg, 'utf-8'))
            return signature_bytes.hex()
        except Exception as e:
            raise ValueError(f"Error generating signature: {e}")

    def _send_request(self, method: str, endpoint: str) -> Dict:
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "X-AUTH-APIKEY": self.api_key,
        }

        try:
            epoch_time = str(int(time.time() * 1000))
            signature = self._generate_signature(method, endpoint, epoch_time)
            headers["X-AUTH-SIGNATURE"] = signature
            headers["X-AUTH-EPOCH"] = epoch_time

            response = requests.request(method=method, url=url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during API request: {e}")

    def get_account_balances(self) -> Dict:
        endpoint = "/trade/api/v2/user/portfolio"
        return self._send_request("GET", endpoint)


# --- Fetch Portfolio Data ---
if __name__ == "__main__":
    # Initialize the API client
    api_client = CoinSwitchAPI(COINSWITCH_API_KEY, COINSWITCH_SECRET_KEY)

    try:
        # Fetch account balances
        portfolio_data = api_client.get_account_balances()

        # Display portfolio data
        if portfolio_data and "data" in portfolio_data and isinstance(portfolio_data["data"], list):
            print("Portfolio Data:")
            for entry in portfolio_data["data"]:
                currency_name = entry.get("name", "N/A")
                currency_code = entry.get("currency", "N/A")
                main_balance = float(entry.get("main_balance", 0))
                blocked_balance = float(entry.get("blocked_balance_order", 0))

                print(f"\nCurrency: {currency_name} ({currency_code})")
                print(f"  Available Balance: {main_balance:,.8f} {currency_code}")
                print(f"  Blocked Balance: {blocked_balance:,.8f} {currency_code}")
        else:
            print("No portfolio data found or unexpected format received.")
    except Exception as e:
        print(f"Error fetching portfolio data: {e}")