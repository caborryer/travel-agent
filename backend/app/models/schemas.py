from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

VALID_CURRENCIES = {"EUR", "USD", "GBP", "ARS", "BRL", "MXN", "COP", "CLP", "PEN", "UYU"}


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=5000)


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's travel query",
    )
    session_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Optional session identifier",
    )


class Destination(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    country: str = Field(default="", max_length=100)
    estimated_price: str = Field(default="", max_length=200)
    currency: str = Field(default="EUR", max_length=3)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_CURRENCIES:
            return "EUR"
        return v

    best_season: str = Field(default="", max_length=200)
    why_lowcost: str = Field(default="", max_length=500)
    value_score: int = Field(default=3, ge=1, le=5)
    activities: list[str] = Field(default_factory=list)
    source: str = Field(default="", max_length=500)
    weather_note: Optional[str] = Field(None, max_length=200)
    image_url: Optional[str] = Field(None, max_length=500)

    @field_validator("activities")
    @classmethod
    def validate_activities(cls, v: list[str]) -> list[str]:
        return [a[:100] for a in v if isinstance(a, str)][:10]


class ChatResponse(BaseModel):
    session_id: str = Field(..., min_length=1)
    destinations: list[Destination] = Field(default_factory=list)
    message: str = Field(..., max_length=5000)
