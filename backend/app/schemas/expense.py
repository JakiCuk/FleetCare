"""Expense and expense-breakdown schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ExpenseCategory = Literal["fuel", "service", "documents", "tires", "other"]


class ExpenseBase(BaseModel):
    occurred_at: date
    description: str | None = Field(default=None, max_length=255)
    amount: Decimal
    category: ExpenseCategory


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    occurred_at: date | None = None
    description: str | None = Field(default=None, max_length=255)
    amount: Decimal | None = None
    category: ExpenseCategory | None = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    occurred_at: date
    description: str | None = None
    amount: Decimal
    category: str


class ExpenseBreakdownItem(BaseModel):
    category: str
    amount: float


class ExpenseBreakdown(BaseModel):
    total: float = 0.0
    breakdown: list[ExpenseBreakdownItem] = Field(default_factory=list)
