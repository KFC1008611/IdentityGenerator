"""Chinese Identity Generator CLI."""

__version__ = "0.2.0"
__author__ = "Identity Gen"
__email__ = "identity@example.com"

from .models import Identity, IdentityConfig
from .generator import IdentityGenerator

__all__ = ["Identity", "IdentityConfig", "IdentityGenerator"]
