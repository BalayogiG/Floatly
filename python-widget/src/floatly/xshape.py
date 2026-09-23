"""Restrict a window's clickable area to an arbitrary polygon via the X11
Shape extension's *input* shape.

Qt's `QWidget.setMask()` sets the window's *bounding* shape too, which also
clips what gets composited — combined with a translucent background that
produces an opaque black window outside the mask instead of transparency.
Going straight to `XShapeCombineRegion` with `ShapeInput` only touches hit
testing, leaving the ARGB bounding shape (and therefore transparency)
alone: everywhere outside the polygon stays invisible *and* click-through,
everywhere inside stays exactly as it already rendered.
"""

from __future__ import annotations

import ctypes
import ctypes.util
from collections.abc import Sequence

SHAPE_INPUT = 2
SHAPE_SET = 0
WINDING_RULE = 1  # X.h: EvenOddRule=0, WindingRule=1


class _XPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_short), ("y", ctypes.c_short)]


class InputShaper:
    """Holds its own X11 connection for setting a window's input shape.

    Raises RuntimeError if unavailable (e.g. no X11/XWayland connection) —
    callers should degrade to "no shaping, whole window interactive".
    """

    def __init__(self) -> None:
        x11_path = ctypes.util.find_library("X11") or "libX11.so.6"
        xext_path = ctypes.util.find_library("Xext") or "libXext.so.6"
        self._x11 = ctypes.CDLL(x11_path)
        self._xext = ctypes.CDLL(xext_path)

        self._x11.XOpenDisplay.restype = ctypes.c_void_p
        self._x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self._x11.XPolygonRegion.restype = ctypes.c_void_p
        self._x11.XPolygonRegion.argtypes = [
            ctypes.POINTER(_XPoint),
            ctypes.c_int,
            ctypes.c_int,
        ]
        self._x11.XDestroyRegion.restype = ctypes.c_int
        self._x11.XDestroyRegion.argtypes = [ctypes.c_void_p]
        self._x11.XFlush.restype = ctypes.c_int
        self._x11.XFlush.argtypes = [ctypes.c_void_p]

        self._xext.XShapeCombineRegion.restype = None
        self._xext.XShapeCombineRegion.argtypes = [
            ctypes.c_void_p,  # Display*
            ctypes.c_ulong,  # Window
            ctypes.c_int,  # dest_kind
            ctypes.c_int,  # x_off
            ctypes.c_int,  # y_off
            ctypes.c_void_p,  # Region
            ctypes.c_int,  # op
        ]

        self._display = self._x11.XOpenDisplay(None)
        if not self._display:
            raise RuntimeError(
                "XOpenDisplay failed — input shaping needs an X11/XWayland connection"
            )

    def set_input_polygon(self, window_id: int, points: Sequence[tuple[int, int]]) -> None:
        n = len(points)
        arr = (_XPoint * n)(*(_XPoint(int(x), int(y)) for x, y in points))
        region = self._x11.XPolygonRegion(arr, n, WINDING_RULE)
        self._xext.XShapeCombineRegion(
            self._display, window_id, SHAPE_INPUT, 0, 0, region, SHAPE_SET
        )
        self._x11.XDestroyRegion(region)
        self._x11.XFlush(self._display)

    def clear_input_shape(self, window_id: int) -> None:
        """Reset the input shape to match the window's full bounding rect."""
        self._xext.XShapeCombineRegion(
            self._display, window_id, SHAPE_INPUT, 0, 0, None, SHAPE_SET
        )
        self._x11.XFlush(self._display)
