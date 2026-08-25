# https://github.com/manoharchalla-inor
# #manoharchalla-in

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Database Configuration
DB_NAME = "order_to_cash.db"
DATABASE_PATH = str(BASE_DIR / DB_NAME)

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = "gpt-4o-mini"

# Business Rules & Risk Thresholds
PAYMENT_RISK_THRESHOLD = 70.0  # Score >= 70 flags order for Human Review
HIGH_VALUE_ORDER_THRESHOLD = 10000.00  # Orders above this get extra risk weight
MAX_UNPAID_INVOICES_LIMIT = 2  # More than 2 unpaid invoices adds risk
OVERDUE_DAYS_LIMIT = 30  # Overdue days > 30 adds risk

# Tax & Pricing
DEFAULT_TAX_RATE = 0.08  # 8% tax
STANDARD_SHIPPING_FEE = 25.00
HIGH_VALUE_SHIPPING_FEE = 0.00  # Free shipping over threshold

# Currency
CURRENCY_SYMBOL = "$"
