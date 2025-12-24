
# 🚀 Binance Futures Testnet Trading Bot (Python)

## 📌 Overview

This project is a **simplified trading bot for Binance USDT-M Futures Testnet**, built as part of a technical screening assignment for a Junior Python Developer role.

The bot uses the **official `python-binance` library** to place trades on **Binance Futures Testnet**, with strong focus on:

* correctness
* safety
* input validation
* exchange rule compliance
* clean, reusable code structure

It supports **real order execution on the Binance Futures Testnet** and logs all important actions and errors.

---

## ✅ Features Implemented

### Core Requirements

* ✅ Binance **USDT-M Futures Testnet** support
* ✅ Uses official **Binance Futures REST API** via `python-binance`
* ✅ Market order placement (BUY / SELL)
* ✅ Symbol-specific leverage handling
* ✅ Isolated margin mode
* ✅ Command-line interface (CLI)
* ✅ Input validation (quantity, leverage, symbol rules)
* ✅ Exchange rule handling:

  * Minimum notional
  * Lot size / precision
  * Available margin checks
* ✅ Logs API requests, responses, and errors
* ✅ Outputs order details and execution status

### Bonus / Advanced

* 🔹 Stop-Limit logic infrastructure included
* 🔹 Pre-trade margin estimation with safety buffer
* 🔹 Automatic quantity adjustment to valid step size
* 🔹 Clear user guidance when orders cannot be placed

---

## 🛠 Tech Stack

* **Language:** Python 3
* **Library:** `python-binance`
* **Exchange:** Binance Futures Testnet (USDT-M)
* **Interface:** Command-line (CLI)
* **Logging:** Python `logging` module

---

## 📂 Project Structure

```
.
├── bot.py           # Main trading bot (CLI-based)
├── bot.log          # Log file (API calls, errors, events)
├── .env.example     # Environment variable template
├── requirements.txt # Dependencies
└── README.md        # Project documentation
```

---

## 🔐 Environment Setup

Create a `.env` file in the project root:

```env
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
```

> ⚠️ **Important:**
> API keys must be generated from
> 👉 [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
> with **Futures permission enabled**.

---

## 📦 Installation

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# OR
.venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

---

## ▶️ How to Run

```bash
python bot.py
```

### Example CLI Flow

```
Symbol (e.g. BTCUSDT / ETHUSDT): BTCUSDT
Side (BUY / SELL): BUY
Order Type (MARKET only for this flow): MARKET
Quantity (e.g. 0.003): 0.003
Desired Leverage (e.g. 20): 20
```

---

## 📤 Example Output

```
Symbol: BTCUSDT
Mark price: 87106.17
Requested qty: 0.003 -> Adjusted qty: 0.003
Notional: 261.32 USDT
Available USDT: 5000.00
Estimated required margin: 14.37 USDT

✅ Market order placed.
Order ID: 11126728277
Status: NEW
Executed Qty: 0.000
```

> ℹ️ On Binance Futures **Testnet**, market orders may briefly appear as `NEW` due to testnet liquidity and matching engine delay.

---

## 🧠 Key Design Considerations

* **Exchange-aware validation**
  Prevents common Binance errors such as:

  * Insufficient margin
  * Invalid precision
  * Minimum notional violations

* **Safety-first execution**
  Orders are placed **only after**:

  * Margin sufficiency is verified
  * Quantity is adjusted to valid step size

* **Reusable architecture**
  `BasicBot` class is extensible for:

  * Limit orders
  * Stop-Limit orders
  * TWAP / Grid strategies
  * WebSocket integration

---

## 📄 Logs

All activity is logged to:

```
bot.log
```

Including:

* Bot initialization
* Leverage and margin changes
* Order placement responses
* API and validation errors


