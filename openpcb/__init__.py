"""OpenPCB core package.

This package provides a small Engine wrapper around KiCad's pcbnew API.
"""
from .engine import Board, Part

__all__ = ["Board", "Part"]
