"""Core engine for OpenPCB.

Provides a lightweight Board/Part API built on top of KiCad's `pcbnew` (KiCad 8 API).

The implementation prefers real `pcbnew` objects when available, but includes
lightweight fallbacks so the module can be imported and unit-tested without
KiCad installed.

Key classes:
- `Part`: wraps a `pcbnew.Footprint`-like object and exposes get/set position in mm.
- `Board`: holds parts and provides `place_near(part, anchor, distance, direction)`
  to position parts relative to each other, and `generate(filename)` to save the board.

Note: When running with real KiCad, pass real `pcbnew.Footprint` objects to `Part`.
"""
from typing import Optional, Tuple

try:
    import pcbnew
    _HAS_PCBNEW = True
except Exception:
    pcbnew = None
    _HAS_PCBNEW = False


def _to_mm(value) -> float:
    """Convert internal pcbnew units to millimeters.

    If `pcbnew` is not available this is a passthrough (value already mm).
    """
    if _HAS_PCBNEW:
        try:
            return pcbnew.ToMM(value)
        except Exception:
            return float(value)
    return float(value)


def _from_mm(value_mm: float):
    """Convert millimeters to pcbnew internal units.

    If `pcbnew` is not available, return the float unchanged.
    """
    if _HAS_PCBNEW:
        try:
            return pcbnew.FromMM(value_mm)
        except Exception:
            return value_mm
    return value_mm


class Part:
    """Wraps a pcbnew Footprint-like object.

    The wrapped object must implement `GetPosition()` and `SetPosition(pt)` when
    running with KiCad. For lightweight testing, you can pass any object that
    exposes `pos_mm` attribute (tuple of two floats) and the wrapper will use it.
    """

    def __init__(self, footprint: Optional[object] = None, name: Optional[str] = None):
        self.footprint = footprint
        self.name = name or getattr(footprint, "GetReference", lambda: "")()

    def get_position_mm(self) -> Tuple[float, float]:
        """Return (x_mm, y_mm) position of the part's origin in millimeters."""
        if hasattr(self.footprint, "pos_mm"):
            return tuple(self.footprint.pos_mm)

        if _HAS_PCBNEW and self.footprint is not None:
            pos = self.footprint.GetPosition()
            try:
                return (_to_mm(pos.x), _to_mm(pos.y))
            except Exception:
                return (float(pos.x), float(pos.y))

        return (0.0, 0.0)

    def get_bbox_size_mm(self) -> Tuple[float, float]:
        """Return an approximate bounding-box size (width_mm, height_mm) for the part.

        Attempts to use the footprint's bounding box when running with `pcbnew`.
        Falls back to a conservative default size when unavailable.
        """
        default_w, default_h = 6.0, 3.0

        if hasattr(self.footprint, "GetBoundingBox") and _HAS_PCBNEW:
            try:
                bbox = self.footprint.GetBoundingBox()
                w = _to_mm(bbox.GetWidth())
                h = _to_mm(bbox.GetHeight())
                if w <= 0 or h <= 0:
                    return (default_w, default_h)
                return (w, h)
            except Exception:
                pass

        if hasattr(self.footprint, "Pads"):
            try:
                xs = []
                ys = []
                for pad in self.footprint.Pads():
                    try:
                        p = pad.GetPosition()
                        xs.append(_to_mm(p.x))
                        ys.append(_to_mm(p.y))
                    except Exception:
                        continue
                if xs and ys:
                    w = max(xs) - min(xs)
                    h = max(ys) - min(ys)
                    if w > 0 and h > 0:
                        return (w + 1.0, h + 1.0)
            except Exception:
                pass

        return (default_w, default_h)

    def set_position_mm(self, x_mm: float, y_mm: float):
        """Set the part origin to (`x_mm`, `y_mm`)."""
        if _HAS_PCBNEW and self.footprint is not None:
            try:
                self.footprint.SetPosition(pcbnew.wxPointMM(x_mm, y_mm))
                return
            except Exception:

                try:
                    self.footprint.SetPosition(pcbnew.VECTOR2I(int(_from_mm(x_mm)), int(_from_mm(y_mm))))
                    return
                except Exception:
                    pass


        if hasattr(self.footprint, "pos_mm"):
            self.footprint.pos_mm = (float(x_mm), float(y_mm))
            return


        self.footprint = type("_virtual", (), {})()
        self.footprint.pos_mm = (float(x_mm), float(y_mm))


class Board:
    """Simple board container and placement engine.

    Usage:
    - Create `Part` objects wrapping real `pcbnew` footprints, or lightweight
      parts with `pos_mm` attributes for testing.
    - Use `place_near` to position parts relative to anchors.
    - Call `generate(filename)` to save (when `pcbnew` is available) or emit
      a JSON summary otherwise.
    """

    def __init__(self):
        self.parts = []
        if _HAS_PCBNEW:
            try:
                self.board = pcbnew.BOARD()
            except Exception:
                try:
                    self.board = pcbnew.NewBoard()
                except Exception:
                    self.board = None
        else:
            self.board = None

    def add_part(self, part: Part, position_mm: Optional[Tuple[float, float]] = None):
        """Add a `Part` to the board.

        If `position_mm` is provided, the part origin will be set to that
        coordinate; otherwise the part's existing position is preserved.
        """
        if position_mm is not None:
            part.set_position_mm(*position_mm)
        self.parts.append(part)

    def place_near(self, part: Part, anchor: Part, distance: float = 5.0, direction: str = "right"):
        """Place `part` near `anchor`.

        Parameters:
        - `part`: Part to move.
        - `anchor`: Part used as reference for placement.
        - `distance`: gap in millimeters between anchor origin and part origin.
        - `direction`: one of "top", "bottom", "left", "right".

        The method computes the new X,Y based on the anchor's origin and the
        requested direction. It uses the simple rule of shifting the part's
        origin by the `distance` along the requested axis. For more advanced
        placement (respecting footprints' bounding boxes), callers can extend
        this method.
        """
        ax, ay = anchor.get_position_mm()

        # Try to respect bounding boxes when computing placement so parts
        # don't overlap. If bounding-box data isn't available, fall back to
        # the simple origin-based shift.
        aw, ah = anchor.get_bbox_size_mm() if hasattr(anchor, "get_bbox_size_mm") else (0.0, 0.0)
        pw, ph = part.get_bbox_size_mm() if hasattr(part, "get_bbox_size_mm") else (0.0, 0.0)

        dir_lower = str(direction).lower()
        if dir_lower == "top":
            nx = ax
            ny = ay - (ah / 2.0) - (ph / 2.0) - float(distance)
        elif dir_lower == "bottom":
            nx = ax
            ny = ay + (ah / 2.0) + (ph / 2.0) + float(distance)
        elif dir_lower == "left":
            nx = ax - (aw / 2.0) - (pw / 2.0) - float(distance)
            ny = ay
        elif dir_lower == "right":
            nx = ax + (aw / 2.0) + (pw / 2.0) + float(distance)
            ny = ay
        else:
            raise ValueError("direction must be one of: top, bottom, left, right")

        part.set_position_mm(nx, ny)
        return (nx, ny)

    def generate(self, filename: str):
        """Save the board.

        If `pcbnew` is available and `self.board` is a real board, `pcbnew.SaveBoard`
        is used. Otherwise a small JSON summary with part positions is written
        so the result can be inspected without KiCad.
        """
        if _HAS_PCBNEW:
            try:
                if self.board is None:
                    try:
                        self.board = pcbnew.BOARD()
                    except Exception:
                        try:
                            self.board = pcbnew.NewBoard()
                        except Exception:
                            self.board = None

                if self.board is not None:
                    def _create_simple_fp(name: str, x_mm: float, y_mm: float):
                        fp = pcbnew.FOOTPRINT(self.board)
                        fp.SetReference(name)
                        fp.SetValue(name)
                        fp.SetPosition(pcbnew.VECTOR2I(int(_from_mm(x_mm)), int(_from_mm(y_mm))))
                        p1 = pcbnew.PAD(fp)
                        p1.SetNumber(1)
                        p1.SetFPRelativePosition(pcbnew.VECTOR2I(int(_from_mm(-0.6)), 0))
                        p1.SetSize(pcbnew.VECTOR2I(int(_from_mm(0.9)), int(_from_mm(0.9))))
                        p1.SetShape(pcbnew.PAD_SHAPE_RECT)
                        p2 = pcbnew.PAD(fp)
                        p2.SetNumber(2)
                        p2.SetFPRelativePosition(pcbnew.VECTOR2I(int(_from_mm(0.6)), 0))
                        p2.SetSize(pcbnew.VECTOR2I(int(_from_mm(0.9)), int(_from_mm(0.9))))
                        p2.SetShape(pcbnew.PAD_SHAPE_RECT)
                        fp.Add(p1)
                        fp.Add(p2)
                        return fp

                    for p in self.parts:
                        if getattr(p.footprint, "GetReference", None) is not None:
                            try:
                                self.board.Add(p.footprint)
                            except Exception:
                                pass
                        else:
                            x, y = p.get_position_mm()
                            fp = _create_simple_fp(p.name or "P", x, y)
                            self.board.Add(fp)

                    pcbnew.SaveBoard(filename, self.board)
                    return filename
            except Exception as e:
                raise RuntimeError(f"Failed to save board via pcbnew: {e}")

        import json

        summary = {"parts": []}
        for p in self.parts:
            summary["parts"].append({"name": p.name, "pos_mm": p.get_position_mm()})

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return filename
