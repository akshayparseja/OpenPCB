#!/usr/bin/env python3
"""LED Flashlight Example using OpenPCB placement engine

This demonstrates the workflow:
1. SKiDL generates netlist with real KiCad libraries
2. Import netlist to create board with components
3. Use OpenPCB to place components in a sensible layout
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pcbnew
    import wx
    from openpcb.engine import Board, Part
    
    if not wx.App.Get():
        app = wx.App()
    
    board = Board()
    
    MM_TO_IU = 1000000
    
    def create_battery_fp():
        fp = pcbnew.FOOTPRINT(None)
        fp.SetReference('B1')
        fp.SetValue('Battery_Cell')
        for i, (x, y) in enumerate([(0, -2), (0, 2)], start=1):
            pad = pcbnew.PAD(fp)
            pad.SetNumber(str(i))
            pad.SetPosition(pcbnew.VECTOR2I(int(x * MM_TO_IU), int(y * MM_TO_IU)))
            pad.SetSize(pcbnew.VECTOR2I(int(1.5 * MM_TO_IU), int(1.5 * MM_TO_IU)))
            pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
            pad.SetDrillSize(pcbnew.VECTOR2I(int(0.8 * MM_TO_IU), int(0.8 * MM_TO_IU)))
            pad.SetLayerSet(pad.PTHMask())
            fp.Add(pad)
        return fp
    def create_resistor_fp():
        fp = pcbnew.FOOTPRINT(None)
        fp.SetReference('R1')
        fp.SetValue('330')
        for i, x in enumerate([-2, 2], start=1):
            pad = pcbnew.PAD(fp)
            pad.SetNumber(str(i))
            pad.SetPosition(pcbnew.VECTOR2I(int(x * MM_TO_IU), 0))
            pad.SetSize(pcbnew.VECTOR2I(int(1.2 * MM_TO_IU), int(1.2 * MM_TO_IU)))
            pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            pad.SetLayerSet(pad.SMDMask())
            fp.Add(pad)
        return fp

    def create_led_fp():
        fp = pcbnew.FOOTPRINT(None)
        fp.SetReference('D1')
        fp.SetValue('LED')
        for i, x in enumerate([-1.5, 1.5], start=1):
            pad = pcbnew.PAD(fp)
            pad.SetNumber(str(i))
            pad.SetPosition(pcbnew.VECTOR2I(int(x * MM_TO_IU), 0))
            pad.SetSize(pcbnew.VECTOR2I(int(1.0 * MM_TO_IU), int(1.0 * MM_TO_IU)))
            pad.SetShape(pcbnew.PAD_SHAPE_RECT if i == 1 else pcbnew.PAD_SHAPE_CIRCLE)
            pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            pad.SetLayerSet(pad.SMDMask())
            fp.Add(pad)
        return fp
    
    bat_fp = create_battery_fp()
    r_fp = create_resistor_fp()
    led_fp = create_led_fp()
    
    bat = Part(bat_fp)
    resistor = Part(r_fp)
    led = Part(led_fp)
    
    board.add_part(bat)
    board.add_part(resistor)
    board.add_part(led)
    
    try:
        if hasattr(bat.footprint, "SetOrientation"):
            bat.footprint.SetOrientation(900)  # tenths of a degree (90°)
        elif hasattr(bat.footprint, "SetOrientationDegrees"):
            bat.footprint.SetOrientationDegrees(90)
    except Exception:
        pass

    try:
        if hasattr(bat.footprint, "Reference"):
            bat.footprint.Reference().SetVisible(False)
        if hasattr(bat.footprint, "Value"):
            bat.footprint.Value().SetVisible(False)
    except Exception:
        pass

    bx, by = 10.0, 50.0
    bat.set_position_mm(bx, by)

    aw, ah = bat.get_bbox_size_mm()
    rw, rh = resistor.get_bbox_size_mm()
    lw, lh = led.get_bbox_size_mm()

    def pad1_pos_mm(fp):
        for pad in fp.Pads():
            try:
                if str(pad.GetNumber()) == '1' or pad.GetNumber().strip() == '1':
                    p = pad.GetPosition()
                    return (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))
            except Exception:
                continue
        # Fallback: return origin
        return (0.0, 0.0)

    b_pad = pad1_pos_mm(bat_fp)
    r_pad = pad1_pos_mm(r_fp)
    l_pad = pad1_pos_mm(led_fp)

    spacing = 12.0

    # Place battery so its pad1 is at (bx, by)
    bat_origin_x = bx - b_pad[0]
    bat_origin_y = by - b_pad[1]
    bat.set_position_mm(bat_origin_x, bat_origin_y)

    r_pad_x = bx + spacing
    r_origin_x = r_pad_x - r_pad[0]
    r_origin_y = by - r_pad[1]
    resistor.set_position_mm(r_origin_x, r_origin_y)

    l_pad_x = r_pad_x + spacing
    l_origin_x = l_pad_x - l_pad[0]
    l_origin_y = by - l_pad[1]
    led.set_position_mm(l_origin_x, l_origin_y)

    for p in (resistor, led):
        try:
            if hasattr(p.footprint, 'Reference'):
                p.footprint.Reference().SetVisible(False)
            if hasattr(p.footprint, 'Value'):
                p.footprint.Value().SetVisible(False)
        except Exception:
            pass
    
    # Generate the board
    board.generate('led_flashlight_placed.kicad_pcb')
    
    print("Created led_flashlight_placed.kicad_pcb with proper component placement!")
    print("Open it in KiCad PCB Editor to see the layout.")
    
except ImportError as e:
    print(f"Error: {e}")
    print("This script requires KiCad's Python environment (kicadpy)")
    sys.exit(1)
