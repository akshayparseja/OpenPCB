# OpenPCB
OpenPCB is focused on open-source automated circuit board generation from user specification to Gerber/KiCad files with fully open-sourced tools.
It provides a framework for generating physical hardware layouts directly from Python code, replacing manual placement and routing with algorithmic synthesis.

Quick Phase 1 setup

1. Install KiCad (recommended 7 or 8). On macOS you can use the official installer from https://kicad.org or Homebrew:

```bash
brew install --cask kicad
```

2. Install SKiDL (optional for later phases):

```bash
pip3 install skidl
```

3. Run the Phase 1 script (it will try to use `pcbnew` if available; otherwise it writes a fallback `hello.kicad_pcb` using local footprints):

```bash
PYTHONPATH=$PWD python3 scripts/phase1_hello.py
```

4. Open `hello.kicad_pcb` in KiCad (File -> Open) to confirm the two footprints are present.

If you don't have KiCad installed yet, the script will still produce `hello.kicad_pcb` from the local footprint files in `data/footprints/` so you can inspect the result after installing KiCad.

Tutorial: LED Flashlight (SKiDL → OpenPCB)
----------------------------------------

Quick steps to try the end-to-end demo locally:

1. Install SKiDL (system Python):

```bash
pip install skidl
```

2. Generate netlist (system Python):

```bash
python3 skidl/led_flashlight.py
# -> writes led_flashlight.net
```

3. Run the importer with KiCad's Python so `pcbnew` is available:

```bash
PYTHONPATH=$PWD kicadpy scripts/import_netlist.py led_flashlight.net
# -> writes led_flashlight.kicad_pcb
```

4. Open `led_flashlight.kicad_pcb` in KiCad and verify the Battery, R1 and D1 placements.

Notes:
- The importer provided here is intentionally minimal for the tutorial and expects the three parts B1, R1 and D1. We'll generalize this in Phase 2.
- If your SKiDL libraries use different symbol names, adjust `skidl/led_flashlight.py` accordingly.
