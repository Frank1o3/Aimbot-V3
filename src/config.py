""" Config loader using Pydantic v2 with ColorHex as RootModel """

from typing import Tuple, Any

import yaml
from pydantic import BaseModel, RootModel, field_validator


class ColorHex(RootModel[int]):
    """
    A Pydantic RootModel that stores a 24-bit color as an int.
    Accepts int (e.g. 0xe400e4 or 14942436) or hex string ("#e400e4" or "e400e4").
    """

    @field_validator("root", mode="before")
    @classmethod
    def _parse_root(cls, v: Any):
        # Accept already-int values
        if isinstance(v, int):
            val = v
        elif isinstance(v, str):
            s = v.lstrip("#").lower()
            if len(s) != 6:
                raise ValueError("Hex string must be 6 characters (RRGGBB).")
            try:
                val = int(s, 16)
            except ValueError as exc:
                raise ValueError("Invalid hex color string.") from exc
        else:
            raise TypeError("Color must be an int or hex string.")
        if not 0 <= val <= 0xFFFFFF:
            raise ValueError(
                "Hex value must be between 0x000000 and 0xFFFFFF.")
        return val

    # convenience property
    @property
    def value(self) -> int:
        return self.root

    @property
    def r(self) -> int:
        return (self.root >> 16) & 0xFF

    @property
    def g(self) -> int:
        return (self.root >> 8) & 0xFF

    @property
    def b(self) -> int:
        return self.root & 0xFF

    @property
    def rgb(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def __str__(self) -> str:
        return f"#{self.root:06x}"

    def __repr__(self) -> str:
        return f"ColorHex(0x{self.root:06x})"


class General(BaseModel):
    target_win: str = ""
    fov: int = 150
    color: ColorHex = ColorHex(0xfa0000)
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

    def to_serializable(self, value: Any) -> Any:
        """
        Convert Pydantic models and ColorHex into YAML-safe primitives.
        """

        # ColorHex → hex string "#rrggbb"
        if isinstance(value, ColorHex):
            return str(value)

        # Pydantic model → dict
        if isinstance(value, BaseModel):
            dumped = value.model_dump()
            return {k: self.to_serializable(v) for k, v in dumped.items()}

        # dict → dict
        if isinstance(value, dict):
            return {k: self.to_serializable(v) for k, v in value.items()}

        # list → list
        if isinstance(value, list):
            return [self.to_serializable(v) for v in value]

        # primitive
        return value


    def save(self, path: str) -> None:
        """
        Save the current configuration back to a YAML file.
        Ensures ColorHex values are stored as standard 6-digit hex strings.
        """

        # Convert whole Config model to serializable dict
        data = self.to_serializable(self)

        # Write YAML
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                data,
                f,
                sort_keys=False,
                allow_unicode=True,
                default_flow_style=False
            )