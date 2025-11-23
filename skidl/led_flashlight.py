"""SKiDL example: LED flashlight

Generates a tiny netlist for a battery -> resistor -> LED circuit.
Run with KiCad Python (kicadpy) to emit a netlist that the OpenPCB importer will consume.
"""
import json

try:
	from skidl import Part, Net, generate_netlist

	BAT = Part('Device', 'Battery_Cell', ref='B1', footprint='Battery_Cell')
	R1 = Part('Device', 'R', ref='R1', value='330', footprint='R_0402')
	D1 = Part('Device', 'LED', ref='D1', value='LED', footprint='LED_0603')

	VPLUS = Net('V+')
	GND = Net('GND')

	VPLUS += BAT['+'], R1[1], D1['A']
	GND += BAT['-'], D1['K']

	generate_netlist()
	print('Wrote led_flashlight.net')

except Exception as e:
	print(f"SKiDL error: {e}")
	import traceback
	traceback.print_exc()
	fallback = {
		"parts": [
			{"ref": "B1", "value": "Battery", "footprint": "Battery_Cell"},
			{"ref": "R1", "value": "330", "footprint": "R_0402"},
			{"ref": "D1", "value": "LED", "footprint": "LED_0603"},
		],
		"nets": [
			{
				"name": "V+",
				"nodes": [
					{"ref": "B1", "pad": "1"},
					{"ref": "R1", "pad": "1"},
					{"ref": "D1", "pad": "1"}
				]
			},
			{
				"name": "GND",
				"nodes": [
					{"ref": "B1", "pad": "2"},
					{"ref": "D1", "pad": "2"}
				]
			}
		]
	}

	with open('led_flashlight.net', 'w', encoding='utf-8') as f:
		json.dump(fallback, f, indent=2)

	print('SKiDL libs unavailable — wrote fallback JSON netlist: led_flashlight.net')
