import os, json
from converter import convert_rvt_to_ifc
from mep_extractor import extract_mep_data
from clash_detector import detect_clashes

os.makedirs('converted_ifc', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
open('uploads/test.rvt', 'w').close()

fname = convert_rvt_to_ifc('uploads/test.rvt', 'converted_ifc')
print(f'Converted: {fname}')

elements = extract_mep_data(f'converted_ifc/{fname}')
print(f'\n=== MEP ELEMENTS ({len(elements)}) ===')
for el in elements:
    props = el.get('flat_properties', {}) 
    print(f"  [{el['type']}] {el['name']}  id={el['ifc_id']}  loc={el['location']}  props={list(props.keys())}")

clashes = detect_clashes(elements)
print(f'\n=== CLASHES ({len(clashes)}) ===')
print(json.dumps(clashes, indent=2))
