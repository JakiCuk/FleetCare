"""ORM models package.

Importing this package registers every model on ``Base.metadata`` so that
Alembic autogenerate and ``create_all`` see the full schema. All model
classes are re-exported here for convenient ``from app.models import X``.
"""

from __future__ import annotations

from app.models.car import Car, UserCarGroup
from app.models.document import (
    InsurancePolicy,
    TechnicalInspection,
    Vignette,
)
from app.models.expense import Expense
from app.models.fuel import FuelRecord
from app.models.notification import NotificationLog, NotificationRule
from app.models.odometer import OdometerReading
from app.models.service import ServiceInterval, ServiceRecord
from app.models.settings import AppSetting
from app.models.tire import TireMeasurement, TireSet
from app.models.user import User

__all__ = [
    "AppSetting",
    "Car",
    "Expense",
    "FuelRecord",
    "InsurancePolicy",
    "NotificationLog",
    "NotificationRule",
    "OdometerReading",
    "ServiceInterval",
    "ServiceRecord",
    "TechnicalInspection",
    "TireMeasurement",
    "TireSet",
    "User",
    "UserCarGroup",
    "Vignette",
]
