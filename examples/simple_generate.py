"""Simple example showing how to use `openpcb.engine`.

This example will work without KiCad by using lightweight mock parts. When
`pcbnew` is available, pass real `pcbnew.Footprint` objects to `Part`.
"""
try:
    import wx
    if not wx.GetApp():
        wx.App(False)
except Exception:
    pass

from openpcb.engine import Board, Part


class MockFootprint:
    def __init__(self, name, x=0.0, y=0.0):
        self.ref = name
        self.pos_mm = (float(x), float(y))

    def GetReference(self):
        return self.ref


def main():
    b = Board()

    mcu_fp = MockFootprint("U1", x=10.0, y=10.0)
    r1_fp = MockFootprint("R1")

    mcu = Part(mcu_fp, name="MCU")
    r1 = Part(r1_fp, name="R1")

    b.add_part(mcu)
    b.add_part(r1)

    b.place_near(r1, mcu, distance=5.0, direction="right")

    out = b.generate("example.kicad_pcb")
    print("Generated:", out)


if __name__ == "__main__":
    main()
