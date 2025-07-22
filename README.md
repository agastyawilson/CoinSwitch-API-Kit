# CoinSwitch-API-Kit

Welcome to the repository! This project contains **three pieces of code** that interact with the CoinSwitch API to fetch cryptocurrency data, manage portfolios, and even place live trades. While I have little to no experience with coding, this has been a journey of "vibe code magic", experimentation, and learning as I go. 

While the scripts are written specifically for BTC/INR, you can easily adapt them to work with any trading pair supported by the CoinSwitch API. Just replace "BTC/INR" with the symbol of your choice (e.g., "ETH/USDT", "DOGE/INR", etc.), and you’re good to go!

Please use this code responsibly and follow the instructions below to set it up and run it.

---

## **Contents**

1. **Portfolio Fetcher**  
   - Fetches your cryptocurrency portfolio data from the CoinSwitch API.

2. **BTC Data Fetcher**  
   - Fetches the last 60 seconds of BTC/INR data.

3. **BTC Limit Order Placer**  
   - Places a live limit order for BTC/INR based on the current price.

---

## **Setup Instructions**

### **Prerequisites**
1. **Python**: Ensure Python 3.8 or higher is installed on your system.
2. **Dependencies**: Install the required Python libraries:
   ```bash
   pip install requests cryptography python-dotenv
   ```
3. **CoinSwitch API Keys**: You need an API key and secret key from CoinSwitch. These are required to authenticate your requests.

---

### **Step 1: Create a `.env` File**
The `.env` file is used to securely store your API keys. Create a file named `secrets.env` in the same directory as the code files and add the following:

```plaintext
COINSWITCH_API_KEY=your_api_key_here
COINSWITCH_SECRET_KEY=your_secret_key_here
```

Replace `your_api_key_here` and `your_secret_key_here` with your actual API credentials.

---

### **Step 2: Run the Code**
Each script is independent and can be run separately. Follow the instructions below for each script.

---

## **1. Portfolio Fetcher**

### **File Name**: `get_portfolio.py`

### **Purpose**:
Fetches your cryptocurrency portfolio data from the CoinSwitch API and displays it in a readable format.

### **How to Use**:
1. Ensure your `.env` file is set up with your API keys.
2. Run the script:
   ```bash
   python get_portfolio.py
   ```
3. The script will display your portfolio data, including available balances and blocked balances for each currency.

### **Example Output**:
```plaintext
Portfolio Data:

Currency: Bitcoin (BTC)
  Available Balance: 0.01234567 BTC
  Blocked Balance: 0.00000000 BTC

Currency: Ethereum (ETH)
  Available Balance: 0.12345678 ETH
  Blocked Balance: 0.00000000 ETH
```

---

## **2. BTC Data Fetcher**

### **File Name**: `get_price.py`

### **Purpose**:
Fetches the last 60 seconds of BTC/INR data from the CoinSwitch API.

### **How to Use**:
1. Ensure your `.env` file is set up with your API keys.
2. Run the script:
   ```bash
   python get_price.py
   ```
3. The script will display the close price of BTC/INR for the last 60 seconds.

### **Example Output**:
```plaintext
BTC Data (Last 60 Seconds):
  Time: 2025-07-22 13:05:00
  Close Price: 2,950,000.00 INR
  Time: 2025-07-22 13:06:00
  Close Price: 2,951,500.00 INR
```

### **Caveat**:
If no data is available for the last 60 seconds, the script will display:
```plaintext
No data found for the specified duration.
```

---

## **3. BTC Limit Order Placer**

### **File Name**: `place_order.py`

### **Purpose**:
Places a live limit order for BTC/INR based on the current price fetched from the CoinSwitch API.

### **How to Use**:
1. Ensure your `.env` file is set up with your API keys.
2. Run the script:
   ```bash
   python place_order.py
   ```
3. The script will:
   - Fetch the current price of BTC/INR.
   - Calculate the quantity of BTC to buy for a target INR amount (default: 10,000 INR).
   - Ask for confirmation before placing the order.
   - Place the order and display the response.

### **Example Output**:
```plaintext
--- Attempting to Place a 1000 INR BTC Limit Order ---
Calculated BTC quantity for 10000 INR at price 2,950,000.00: 0.003390 BTC (rounded to 6 decimal places)
WARNING: This will attempt to place a LIVE LIMIT BUY order for 0.003390 BTC/INR at price 2,950,000.00.
Are you sure you want to proceed? (yes/no): yes
Placing a LIMIT BUY order for 0.003390 BTC/INR at price 2,950,000.00...
Order Placement Response:
{
    "order_id": "123456789",
    "status": "success",
    "message": "Order placed successfully."
}
Fetching details for new order_id: 123456789...
Order Details:
{
    "order_id": "123456789",
    "status": "open",
    "quantity": "0.003390",
    "price": "2950000.00",
    "side": "BUY"
}
```

### **Caveat**:
- This script places **live trades**. Use it responsibly and ensure you understand the implications of live trading.
- If the order fails, the script will display an error message.

---

## **Important Caveats**

1. **Little Coding Experience**:
   - I have little to no experience with coding. This project is the result of "vibe code magic"—a mix of intuition and experimentation. While the code works for me, it may not be perfect or optimized.

2. **Live Trading Risks**:
   - The BTC Limit Order Placer script places **live trades**. Ensure you understand the risks and implications before using it.

3. **API Key Security**:
   - Keep your API keys secure. Do not share your `.env` file or hardcode your keys into the scripts.

4. **No Guarantees**:
   - This code is provided as-is, with no guarantees of accuracy or reliability. Use it at your own risk.

---

## **Disclaimer**
This project is for **educational and demonstration purposes only**. I am not responsible for any financial losses or unintended consequences resulting from the use of this code. Please use it responsibly and ensure you understand the functionality before running it.

---

## **Feedback**
If you have suggestions, improvements, or feedback, feel free to share!

---

Thank you for checking out this repository!
