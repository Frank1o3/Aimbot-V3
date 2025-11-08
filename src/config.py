""" Config loader using Pydantic """

from typing import Tuple, Union

import yaml
from pydantic import BaseModel, field_validator


class ColorHex(BaseModel):
    """A Pydantic-compatible color type (always stores int internally)."""
    value: int

    @field_validator("value", mode="before")
    @classmethod
    def parse_hex(cls, v: Union[int, str]) -> int:
        if isinstance(v, str):
            v = v.lstrip("#").lower()
            if len(v) != 6:
                raise ValueError("Hex string must be 6 characters (RRGGBB).")
            v = int(v, 16)
        if not 0 <= v <= 0xFFFFFF:
            raise ValueError(
                "Hex value must be between 0x000000 and 0xFFFFFF.")
        return v

    @property
    def r(self) -> int:
        return (self.value >> 16) & 0xFF

    @property
    def g(self) -> int:
        return (self.value >> 8) & 0xFF

    @property
    def b(self) -> int:
        return self.value & 0xFF

    @property
    def rgb(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def __str__(self) -> str:
        return f"#{self.value:06x}"


class General(BaseModel):
    target_win: str = ""
    fov: int = 150
    color: ColorHex = ColorHex(value=0xfa0000)
    debug_mode: bool = False


class Aimbot(BaseModel):
    enabled: bool = False
    tolerance: float = 5.0
    lead_factor: float = 0.35
    min_area: int = 50
    max_area: int = 150
    conf_thresh: float = 0.45


class Offset(BaseModel):
    x: float = 0.0
    y: float = 0.0
    min_area: int = 15


class Sensitivity(BaseModel):
    smoothness: float = 0.5
    min_sensitivity: float = 0.4
    max_sensitivity: float = 1.0


class Config(BaseModel):
    general: General = General()
    aimbot: Aimbot = Aimbot()
    offset: Offset = Offset()
    sensitivity: Sensitivity = Sensitivity()

    @classmethod
    def load(cls, path: str) -> "Config":
        """Load config from a YAML file into validated Pydantic models."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)
