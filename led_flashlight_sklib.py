from collections import defaultdict
from skidl import Pin, Part, Alias, SchLib, SKIDL, TEMPLATE

from skidl.pin import pin_types

SKIDL_lib_version = '0.0.1'

led_flashlight = SchLib(tool=SKIDL).add_parts(*[
        Part(**{ 'name':'Battery_Cell', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'Battery_Cell'}), 'ref_prefix':'BT', 'fplist':[''], 'footprint':'Battery_Cell', 'keywords':'battery cell', 'description':'Single-cell battery', 'datasheet':'~', 'pins':[
            Pin(num='1',name='+',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='-',func=pin_types.PASSIVE,unit=1)] }),
        Part(**{ 'name':'R', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'R'}), 'ref_prefix':'R', 'fplist':[''], 'footprint':'R_0402', 'keywords':'R res resistor', 'description':'Resistor', 'datasheet':'~', 'pins':[
            Pin(num='1',name='~',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='~',func=pin_types.PASSIVE,unit=1)] }),
        Part(**{ 'name':'LED', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'LED'}), 'ref_prefix':'D', 'fplist':[''], 'footprint':'LED_0603', 'keywords':'LED diode', 'description':'Light emitting diode', 'datasheet':'~', 'pins':[
            Pin(num='1',name='K',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='A',func=pin_types.PASSIVE,unit=1)] })])