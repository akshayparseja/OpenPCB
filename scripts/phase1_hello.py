"""Phase 1: Create a simple KiCad PCB with two footprints and save it as hello.kicad_pcb.

The script will try to use `pcbnew` when available. If `pcbnew` is not
installed, it falls back to composing a minimal `.kicad_pcb` file by
embedding two local footprint files from `data/footprints/`.

Run:
  python3 scripts/phase1_hello.py

This writes `hello.kicad_pcb` in the repository root.
"""
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
FP_DIR = ROOT / "data" / "footprints"
OUT = ROOT / "hello.kicad_pcb"


def load_module_text(name: str) -> str:
    p = FP_DIR / name
    if not p.exists():
        raise FileNotFoundError(f"Footprint file not found: {p}")
    return p.read_text(encoding="utf-8")


def set_module_position(mod_text: str, x: float, y: float) -> str:
    def repl(match):
        return f"(at {x} {y})"

    parts = re.split(r"(\(module\b)", mod_text, maxsplit=1)
    if len(parts) < 3:
        return mod_text
    head, module_kw, rest = parts
    new_rest = re.sub(r"\(at\s+[-0-9.eE]+\s+[-0-9.eE]+\)", repl, rest, count=1)
    return module_kw + new_rest


def compose_board(mod_texts: list[str]) -> str:
    header = "(kicad_pcb (version 20211014) (generator openpcb)\n"
    header += "  (general (thickness 1.6))\n"
    header += "  (paper A4)\n"
    header += "  (setup\n    (last_trace_width 0.25)\n  )\n"
    body = ""
    for t in mod_texts:
        body += t + "\n"

    footer = ")\n"
    return header + body + footer


def write_fallback_board():
    r0402 = load_module_text("R_0402.kicad_mod")
    led = load_module_text("LED_SMD.kicad_mod")
    r0402p = set_module_position(r0402, 0, 0)
    ledp = set_module_position(led, 10, 0)

    pcb_text = compose_board([r0402p, ledp])
    OUT.write_text(pcb_text, encoding="utf-8")
    print(f"Wrote fallback board to {OUT}")


def try_pcbnew_save():
    try:
        import pcbnew
    except Exception:
        return False
    try:
        import wx
        if not wx.GetApp():
            _wx_app = wx.App(False)
    except Exception:
        _wx_app = None
    try:
        board = pcbnew.BOARD()
    except Exception:
        try:
            board = pcbnew.new_board()
        except Exception:
            board = None

    if board is None:
        return False
    def create_resistor_0402(ref: str, x_mm: float, y_mm: float):
        fp = pcbnew.FOOTPRINT(board)
        fp.SetReference(ref)
        fp.SetValue('R')
        fp.SetPosition(pcbnew.VECTOR2I(int(pcbnew.FromMM(x_mm)), int(pcbnew.FromMM(y_mm))))
        pad1 = pcbnew.PAD(fp)
        pad1.SetNumber(1)
        pad1.SetFPRelativePosition(pcbnew.VECTOR2I(int(pcbnew.FromMM(-0.6)), int(pcbnew.FromMM(0))))
        pad1.SetSize(pcbnew.VECTOR2I(int(pcbnew.FromMM(0.9)), int(pcbnew.FromMM(0.9))))
        pad1.SetShape(pcbnew.PAD_SHAPE_RECT)
        pad2 = pcbnew.PAD(fp)
        pad2.SetNumber(2)
        pad2.SetFPRelativePosition(pcbnew.VECTOR2I(int(pcbnew.FromMM(0.6)), int(pcbnew.FromMM(0))))
        pad2.SetSize(pcbnew.VECTOR2I(int(pcbnew.FromMM(0.9)), int(pcbnew.FromMM(0.9))))
        pad2.SetShape(pcbnew.PAD_SHAPE_RECT)
        fp.Add(pad1)
        fp.Add(pad2)
        return fp

    def create_led_0603(ref: str, x_mm: float, y_mm: float):
        fp = pcbnew.FOOTPRINT(board)
        fp.SetReference(ref)
        fp.SetValue('D')
        fp.SetPosition(pcbnew.VECTOR2I(int(pcbnew.FromMM(x_mm)), int(pcbnew.FromMM(y_mm))))
        pad1 = pcbnew.PAD(fp)
        pad1.SetNumber(1)
        pad1.SetFPRelativePosition(pcbnew.VECTOR2I(int(pcbnew.FromMM(-0.75)), int(pcbnew.FromMM(0))))
        pad1.SetSize(pcbnew.VECTOR2I(int(pcbnew.FromMM(1.0)), int(pcbnew.FromMM(1.0))))
        pad1.SetShape(pcbnew.PAD_SHAPE_RECT)
        pad2 = pcbnew.PAD(fp)
        pad2.SetNumber(2)
        pad2.SetFPRelativePosition(pcbnew.VECTOR2I(int(pcbnew.FromMM(0.75)), int(pcbnew.FromMM(0))))
        pad2.SetSize(pcbnew.VECTOR2I(int(pcbnew.FromMM(1.0)), int(pcbnew.FromMM(1.0))))
        pad2.SetShape(pcbnew.PAD_SHAPE_RECT)
        fp.Add(pad1)
        fp.Add(pad2)
        return fp
    def load_fp(path: Path):
        try:
            fp = pcbnew.FootprintLoad(str(path.parent), path.name)
            return fp
        except Exception:
            return None

    r0402fp = load_fp(FP_DIR / "R_0402.kicad_mod")
    ledfp = load_fp(FP_DIR / "LED_SMD.kicad_mod")
    added = 0
    if r0402fp:
        r0402fp.SetPosition(pcbnew.wxPointMM(0, 0))
        board.Add(r0402fp)
        added += 1
    else:
        board.Add(create_resistor_0402('R1', 0, 0))
        added += 1
    if ledfp:
        ledfp.SetPosition(pcbnew.wxPointMM(10, 0))
        board.Add(ledfp)
        added += 1
    else:
        board.Add(create_led_0603('D1', 10, 0))
        added += 1

    try:
        pcbnew.SaveBoard(str(OUT), board)
        print(f"Saved board via pcbnew to {OUT}")
        return True
    except Exception:
        return False


def main():
    if not FP_DIR.exists():
        print(f"Footprints folder missing: {FP_DIR}\nMake sure data/footprints contains R_0402.kicad_mod and LED_SMD.kicad_mod")
        sys.exit(1)

    if try_pcbnew_save():
        return

    write_fallback_board()


if __name__ == "__main__":
    main()
