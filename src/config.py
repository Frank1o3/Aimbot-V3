""" Config loader """

from typing import Union, Tuple, get_type_hints, Any
import yaml


class ColorHex:
    """
    A custom type designed to store a 24-bit RGB hexadecimal color value (0xRRGGBB)
    and provide easy access to its R, G, and B components.
    """

    # ... (ColorHex class implementation remains the same for brevity) ...

    def __init__(self, hex_value: Union[int, str]):
        """
        Initializes the ColorHex object.

        Args:
            hex_value: The color value, expected as an integer (e.g., 0xe600e6) 
                       or a hex string (e.g., "e600e6" or "#e600e6").
        """

        # --- Type Check and Assignment ---
        if isinstance(hex_value, str):
            # Process string input
            clean_hex = hex_value.lstrip('#').lower()
            if len(clean_hex) != 6:
                raise ValueError("Hex string must be 6 characters (RRGGBB).")
            self._value = int(clean_hex, 16)
        else:
            # Process integer input (direct assignment)
            self._value = hex_value

        # --- Input Validation (applies to both paths) ---
        if not 0 <= self._value <= 0xFFFFFF:
            raise ValueError(
                "Hex integer must be between 0x000000 and 0xFFFFFF.")

        print(f"Initialized ColorHex with internal value: 0x{self._value:06x}")

    # --- Properties for Component Extraction ---

    @property
    def r(self) -> int:
        """Extracts the Red component (0-255)."""
        return (self._value >> 16) & 0xFF

    @property
    def g(self) -> int:
        """Extracts the Green component (0-255)."""
        return (self._value >> 8) & 0xFF

    @property
    def b(self) -> int:
        """Extracts the Blue component (0-255)."""
        return self._value & 0xFF

    @property
    def rgb(self) -> Tuple[int, int, int]:
        """Returns the R, G, B components as a tuple."""
        return (self.r, self.g, self.b)

    # --- Standard Python methods for representation ---

    def __repr__(self) -> str:
        """Official string representation."""
        return f"ColorHex(0x{self._value:06x})"

    def __str__(self) -> str:
        """User-friendly string representation (the #RRGGBB format)."""
        return f"#{self._value:06x}"


class General:
    """ General settings """
    target_win: str = ""
    fov: int = 150
    color: ColorHex = ColorHex(0xfa0000)
    trigger_bot: bool = False


class Aimbot:
    """ Aimbot settings """
    enabled: bool = False
    tolerance: float = 5.0
    lead_factor: float = 0.35


class Offset:
    """ Offset settings """
    x: float = 0.0  # Changed to float to match YAML data
    y: float = 0.0  # Changed to float to match YAML data
    min_area: int = 15


class Sensitivity:
    """ Sensitivity settings """
    smoothness: float = 0.5
    min_sensitivity: float = 0.4
    max_sensitivity: float = 1.0


class Config:
    """ Main config class """
    general: General = General()
    aimbot: Aimbot = Aimbot()
    offset: Offset = Offset()
    sensitivity: Sensitivity = Sensitivity()

    @classmethod
    def load(cls, path: str) -> "Config":
        """Load config from YAML file with type conversion"""
        with open(path, "r", encoding="UTF-8") as file:
            data = yaml.safe_load(file)

        config = cls()

        for section_name, section_data in data.items():
            section_instance = getattr(config, section_name, None)
            if section_instance:
                section_class: type[Any] = type(section_instance)
                hints = get_type_hints(section_class)

                for key, value in section_data.items():
                    if hasattr(section_instance, key):
                        expected_type = hints.get(key)

                        if expected_type is ColorHex:
                            try:
                                value = ColorHex(value)
                            except (TypeError, ValueError) as e:
                                print(
                                    f"Error converting '{key}' to ColorHex: {e}")
                                continue

                        setattr(section_instance, key, value)
                    else:
                        print(
                            f"Warning: Key '{key}' not found in '{section_name}'.")

        print("\nConfiguration Loaded Successfully!")
        return config
