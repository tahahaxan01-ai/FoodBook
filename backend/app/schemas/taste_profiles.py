from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# 9 Taste Dimensions standard
TASTE_DIMENSIONS = [
    "spicy",
    "sweet",
    "salty",
    "sour",
    "umami",
    "smoky",
    "creamy",
    "crispy",
    "rich"
]


class TasteVector(BaseModel):
    """
    9-dimensional taste vector.
    Each value normalized between 0.0 and 1.0.
    """
    spicy: float = Field(default=0.5, ge=0.0, le=1.0)
    sweet: float = Field(default=0.5, ge=0.0, le=1.0)
    salty: float = Field(default=0.5, ge=0.0, le=1.0)
    sour: float = Field(default=0.5, ge=0.0, le=1.0)
    umami: float = Field(default=0.5, ge=0.0, le=1.0)
    smoky: float = Field(default=0.5, ge=0.0, le=1.0)
    creamy: float = Field(default=0.5, ge=0.0, le=1.0)
    crispy: float = Field(default=0.5, ge=0.0, le=1.0)
    rich: float = Field(default=0.5, ge=0.0, le=1.0)

    def to_list(self) -> List[float]:
        return [
            self.spicy,
            self.sweet,
            self.salty,
            self.sour,
            self.umami,
            self.smoky,
            self.creamy,
            self.crispy,
            self.rich
        ]

    @classmethod
    def from_list(cls, values: Optional[List[float]]) -> "TasteVector":
        if not values or len(values) < 9:
            return cls()
        return cls(
            spicy=float(values[0]),
            sweet=float(values[1]),
            salty=float(values[2]),
            sour=float(values[3]),
            umami=float(values[4]),
            smoky=float(values[5]),
            creamy=float(values[6]),
            crispy=float(values[7]),
            rich=float(values[8])
        )


class TasteProfileResponse(BaseModel):
    user_id: str
    taste_vector: List[float] = Field(default_factory=lambda: [0.5]*9)
    taste_attributes: Optional[TasteVector] = None
    preferred_cuisines: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)
    budget_level: Optional[Union[int, str]] = None
    preferred_dining_styles: List[str] = Field(default_factory=list)
    updated_at: Optional[datetime] = None


class TasteProfileUpdate(BaseModel):
    taste_vector: Optional[List[float]] = None
    taste_attributes: Optional[TasteVector] = None
    preferred_cuisines: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    budget_level: Optional[Union[int, str]] = None
    preferred_dining_styles: Optional[List[str]] = None

    @field_validator("taste_vector")
    @classmethod
    def validate_taste_vector(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None:
            if len(v) != 9:
                raise ValueError("Taste vector must contain exactly 9 dimensions [spicy, sweet, salty, sour, umami, smoky, creamy, crispy, rich]")
            for val in v:
                if not (0.0 <= val <= 1.0):
                    raise ValueError(f"Taste vector values must be between 0.0 and 1.0 (got {val})")
        return v


class TasteVectorUpdate(BaseModel):
    taste_vector: Optional[List[float]] = None
    taste_attributes: Optional[TasteVector] = None
