"""Minimal importer: converts a tiny SKiDL netlist into a KiCad board via OpenPCB.

This is a purpose-built, minimal importer for the LED flashlight tutorial.
It does not attempt to be a full netlist parser; it expects the three parts
(B1, R1, D1) produced by `skidl/led_flashlight.py` and maps them to footprints.

Run with KiCad's Python (so `pcbnew` is available). Example:
    PYTHONPATH=$PWD kicadpy scripts/import_netlist.py led_flashlight.net
"""
import sys
import os
import json
from openpcb import Board, Part

try:
    import pcbnew
    _HAS_PCBNEW = True
except Exception:
    pcbnew = None
    _HAS_PCBNEW = False

if _HAS_PCBNEW:
    try:
        import wx
        if wx.GetApp() is None:
            wx.App(False)
    except Exception:
        pass
    
import traceback

def parse_minimal_netlist(path):
    """Parse the small tutorial netlist format.

    Supports JSON fallback produced by `skidl/led_flashlight.py` when SKiDL
    libraries are unavailable. Returns a dict with `parts` and `nets` keys.
    """
    with open(path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception:
            return {
                "parts": [
                    {"ref": "B1", "value": "Battery"},
                    {"ref": "R1", "value": "330"},
                    {"ref": "D1", "value": "LED"},
                ],
                "nets": []
            }

    # Normalize structure
    parts = data.get('parts', [])
    nets = data.get('nets', [])
    return {"parts": parts, "nets": nets}

FOOTPRINT_MAP = {
    "Battery": "Battery_Cell",
    "330": "R_0402",
    "LED": "LED_0603",
}

def footprint_for_part(p):
    return FOOTPRINT_MAP.get(p["value"], FOOTPRINT_MAP.get(p["ref"], "R_0402"))

def main(netlist_path, out_pcb='led_flashlight.kicad_pcb'):
    if not os.path.exists(netlist_path):
        print('Netlist not found:', netlist_path)
        sys.exit(1)
    netlist = parse_minimal_netlist(netlist_path)
    parts = netlist["parts"]
    nets = netlist["nets"]

    if _HAS_PCBNEW:
        try:
            board = pcbnew.BOARD()
        except Exception:
            try:
                board = pcbnew.NewBoard()
            except Exception:
                board = None

        if board is None:
            print('Error: failed to create pcbnew board object')
            sys.exit(1)

        
        netcode_for_name = {}
        for n in nets:
            name = n.get('name')
            if not name:
                continue
            netinfo = pcbnew.NETINFO_ITEM(board, name)
            board.Add(netinfo)
            netcode_for_name[name] = netinfo.GetNet()

        fp_map = {}
        pad_map = {}

        def _create_simple_fp(board, ref, value, x_mm, y_mm, footprint_name=None):
            fp = pcbnew.FOOTPRINT(board)
            fp.SetReference(ref)
            fp.SetValue(value or ref)
            fp.SetPosition(pcbnew.VECTOR2I(int(pcbnew.FromMM(x_mm)), int(pcbnew.FromMM(y_mm))))

            p1 = pcbnew.PAD(fp)
            p1.SetNumber('1')
            p1.SetFPRelativePosition(pcbnew.VECTOR2I(int(pcbnew.FromMM(-0.6)), 0))
            p1.SetSize(pcbnew.VECTOR2I(int(pcbnew.FromMM(0.9)), int(pcbnew.FromMM(0.9))))
            p1.SetShape(pcbnew.PAD_SHAPE_RECT)

            p2 = pcbnew.PAD(fp)
            p2.SetNumber('2')
            p2.SetFPRelativePosition(pcbnew.VECTOR2I(int(pcbnew.FromMM(0.6)), 0))
            p2.SetSize(pcbnew.VECTOR2I(int(pcbnew.FromMM(0.9)), int(pcbnew.FromMM(0.9))))
            p2.SetShape(pcbnew.PAD_SHAPE_RECT)

            fp.Add(p1)
            fp.Add(p2)
            board.Add(fp)

            fp_map[ref] = fp
            pad_map[(ref, '1')] = p1
            pad_map[(ref, '2')] = p2

            return fp

        _create_simple_fp(board, 'B1', 'Battery', 0.0, 0.0)
        _create_simple_fp(board, 'R1', '330', 2.0, 0.0)
        _create_simple_fp(board, 'D1', 'LED', 4.0, 0.0)

        
        for n in nets:
            name = n.get('name')
            nodes = n.get('nodes', [])
            netcode = netcode_for_name.get(name)
            if netcode is None:
                continue
            for node in nodes:
                ref = node.get('ref')
                pad = str(node.get('pad'))
                pad_obj = pad_map.get((ref, pad))
                if pad_obj is not None:
                    try:
                        pad_obj.SetNetCode(netcode)
                    except Exception:
                        try:
                            pad_obj.SetNet(netcode)
                        except Exception:
                            pass

        # Save board
        try:
            pcbnew.SaveBoard(out_pcb, board)
            print('Generated', out_pcb)
        except Exception:
            print('Error saving board:')
            traceback.print_exc()
            sys.exit(1)

    else:
        
        board = Board()
        created = {}
        for p in parts:
            fp = footprint_for_part(p)
            part = Part(footprint=fp, name=p["ref"])
            board.add_part(part)
            created[p["ref"]] = part

        board.add_part(created["B1"], position_mm=(0.0, 0.0))
        board.place_near(created["R1"], created["B1"], distance=2.0, direction="right")
        board.place_near(created["D1"], created["R1"], distance=2.0, direction="right")

        try:
            board.generate(out_pcb)
            print('Generated', out_pcb)
        except Exception:
            print('Error generating fallback board:')
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: kicadpy scripts/import_netlist.py <netlist>')
        sys.exit(1)
    main(sys.argv[1])
