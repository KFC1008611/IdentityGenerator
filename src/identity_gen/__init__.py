"""Chinese Identity Generator CLI.

A Python CLI tool for generating realistic Chinese virtual identity information
including names, addresses, ID cards, phone numbers, and other personal data.
"""

__version__ = "0.3.1"
__author__ = "Identity Gen"
__email__ = "identity@example.com"

from .models import Identity, IdentityConfig
from .generator import IdentityGenerator

__all__ = ["Identity", "IdentityConfig", "IdentityGenerator"]
