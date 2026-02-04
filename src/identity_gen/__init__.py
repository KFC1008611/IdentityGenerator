"""Chinese Identity Generator CLI.

A Python CLI tool for generating realistic Chinese virtual identity information
including names, addresses, ID cards, phone numbers, and other personal data.
"""

__version__ = "0.5.1"
__author__ = "Identity Gen"
__email__ = "identity@example.com"

from .models import Identity, IdentityConfig
from .generator import IdentityGenerator
from .idcard_image_generator import (
    AvatarGenerator,
    IDCardImageGenerator,
    generate_idcard_image,
)

__all__ = [
    "Identity",
    "IdentityConfig",
    "IdentityGenerator",
    "AvatarGenerator",
    "IDCardImageGenerator",
    "generate_idcard_image",
]
