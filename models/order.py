# https://github.com/manoharchalla-inor
# #manoharchalla-in

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Customer(BaseModel):
    customer_id: str
    company_name: str
    contact_email: str
    credit_rating: str  # EXCELLENT, GOOD, FAIR, POOR
    unpaid_invoices_count: int = 0
    has_overdue_payments: bool = False
    total_lifetime_value: float = 0.0


class Product(BaseModel):
    product_id: str
    name: str
    unit_price: float
    category: str
    description: str = ""


class InventoryItem(BaseModel):
    product_id: str
    available_quantity: int
    reserved_quantity: int = 0
    reorder_level: int = 10


class OrderItem(BaseModel):
    product_id: str
    quantity: int
    unit_price: float


class SalesOrderInput(BaseModel):
    customer_id: str
    items: List[OrderItem]
    notes: Optional[str] = None


class SalesOrder(BaseModel):
    order_id: str
    customer_id: str
    items: List[OrderItem]
    total_amount: float
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: str = "ORDER_RECEIVED"
    notes: Optional[str] = None


class Invoice(BaseModel):
    invoice_id: str
    order_id: str
    customer_id: str
    subtotal: float
    tax_amount: float
    shipping_fee: float
    total_amount: float
    issue_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    due_date: str
    status: str = "ISSUED"
