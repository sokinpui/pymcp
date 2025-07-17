# src/pymcp/__init__.py

from .lib import start_server
from .tools.decorators import tool

__all__ = ["tool", "start_server"]
