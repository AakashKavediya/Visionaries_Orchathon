"""
Clash detection module: AABB-based MEP element clash detection
and automated resolution strategy generation.
"""

TYPE_MAP = {
    'IfcPipeSegment': 'PIPE', 'IfcPipeFitting': 'PIPE',
    'IfcDuctSegment': 'DUCT', 'IfcDuctFitting': 'DUCT',
    'IfcFlowTerminal': 'TERMINAL', 'IfcFlowFitting': 'FITTING',
    'IfcFlowController': 'CONTROLLER',
    'IfcFlowStorageDevice': 'STORAGE', 'IfcFlowMovingDevice': 'DEVICE',
    'IfcEnergyConversionDevice': 'DEVICE',
}

# Lower number = more likely to stay fixed (higher routing priority)
MOVE_PRIORITY = {
    'TERMINAL': 0, 'FITTING': 1, 'CONTROLLER': 2,
    'DEVICE': 3, 'STORAGE': 3, 'PIPE': 4, 'DUCT': 4, 'OTHER': 5,
}

DEFAULT_HALF = {
    'PIPE':       {'hx': 1.0,  'hy': 0.05, 'hz': 0.05},
    'DUCT':       {'hx': 1.0,  'hy': 0.20, 'hz': 0.15},
    'TERMINAL':   {'hx': 0.20, 'hy': 0.20, 'hz': 0.10},
    'FITTING':    {'hx': 0.10, 'hy': 0.10, 'hz': 0.10},
    'CONTROLLER': {'hx': 0.10, 'hy': 0.10, 'hz': 0.10},
    'STORAGE':    {'hx': 0.30, 'hy': 0.30, 'hz': 0.30},
    'DEVICE':     {'hx': 0.20, 'hy': 0.20, 'hz': 0.20},
    'OTHER':      {'hx': 0.10, 'hy': 0.10, 'hz': 0.10},
}


def _stype(ifc_type):
    return TYPE_MAP.get(ifc_type, 'OTHER')


def _bbox(el):
    loc = el.get('location', {})
    if not loc:
        return None
    x, y, z = loc.get('x', 0.0), loc.get('y', 0.0), loc.get('z', 0.0)
    fp = el.get('flat_properties', {})
    st = _stype(el.get('type', ''))
    d = DEFAULT_HALF.get(st, DEFAULT_HALF['OTHER'])

    if st == 'PIPE':
        diam = fp.get('NominalDiameter') or fp.get('OutsideDiameter') or (d['hy'] * 2)
        length = fp.get('Length') or fp.get('OverallLength') or (d['hx'] * 2)
        hx = float(length) / 2
        r = float(diam) / 2
        hy = hz = r
    elif st == 'DUCT':
        w = fp.get('Width') or fp.get('BaseDimension') or (d['hy'] * 2)
        h = fp.get('Height') or fp.get('ProfileHeight') or (d['hz'] * 2)
        length = fp.get('Length') or fp.get('OverallLength') or (d['hx'] * 2)
        hx = float(length) / 2
        hy = float(w) / 2
        hz = float(h) / 2
    else:
        hx, hy, hz = d['hx'], d['hy'], d['hz']

    return {
        'min_x': x - hx, 'max_x': x + hx,
        'min_y': y - hy, 'max_y': y + hy,
        'min_z': z - hz, 'max_z': z + hz,
        'center': [x, y, z],
    }


def _overlaps(b1, b2):
    return (
        b1['min_x'] < b2['max_x'] and b1['max_x'] > b2['min_x'] and
        b1['min_y'] < b2['max_y'] and b1['max_y'] > b2['min_y'] and
        b1['min_z'] < b2['max_z'] and b1['max_z'] > b2['min_z']
    )


def _resolve(b1, b2, move_center):
    CLEARANCE = 0.05
    ox = min(b1['max_x'], b2['max_x']) - max(b1['min_x'], b2['min_x'])
    oy = min(b1['max_y'], b2['max_y']) - max(b1['min_y'], b2['min_y'])
    oz = min(b1['max_z'], b2['max_z']) - max(b1['min_z'], b2['min_z'])
    cx, cy, cz = move_center

    options = [
        ('UP',    oz, [cx, cy, cz + oz + CLEARANCE]),
        ('DOWN',  oz, [cx, cy, cz - oz - CLEARANCE]),
        ('NORTH', oy, [cx, cy + oy + CLEARANCE, cz]),
        ('SOUTH', oy, [cx, cy - oy - CLEARANCE, cz]),
        ('EAST',  ox, [cx + ox + CLEARANCE, cy, cz]),
        ('WEST',  ox, [cx - ox - CLEARANCE, cy, cz]),
    ]
    options.sort(key=lambda o: o[1])
    direction, offset, new_pos = options[0]
    offset = round(offset + CLEARANCE, 4)
    new_pos = [round(v, 4) for v in new_pos]
    return direction, offset, new_pos


def _reason(t1, t2, move_el, fixed_el, p1, p2):
    mn, fn = move_el.get('name', '?'), fixed_el.get('name', '?')
    if p1 == p2:
        return (f"Both '{mn}' and '{fn}' have equal routing priority — "
                f"moving element with higher IFC step ID ({move_el['ifc_id']}) for consistency")
    if move_el.get('type', '').startswith('IfcFlowTerminal'):
        return f"Flow terminals connect via flexible links and are repositionable; keeping '{fn}' on its fixed route"
    if t1 in ('PIPE', 'DUCT') and t2 in ('PIPE', 'DUCT') and t1 != t2:
        moving = 'PIPE' if t1 == 'PIPE' else 'DUCT'
        return f"{moving} run rerouted to preserve the larger distribution routing of the fixed element '{fn}'"
    return f"'{mn}' selected to move to resolve {t1}–{t2} clash with '{fn}'"


def detect_clashes(mep_elements):
    """
    Detects AABB clashes between all MEP element pairs.
    Returns a list of clash dicts matching the project output schema.
    """
    valid, boxes = [], []
    for el in mep_elements:
        bb = _bbox(el)
        if bb:
            valid.append(el)
            boxes.append(bb)

    clashes = []
    for i in range(len(valid)):
        for j in range(i + 1, len(valid)):
            el1, el2 = valid[i], valid[j]
            b1, b2 = boxes[i], boxes[j]
            if not _overlaps(b1, b2):
                continue

            t1, t2 = _stype(el1['type']), _stype(el2['type'])
            p1, p2 = MOVE_PRIORITY.get(t1, 5), MOVE_PRIORITY.get(t2, 5)

            if p1 < p2:
                move_el, fixed_el, move_box = el1, el2, b1
            elif p2 < p1:
                move_el, fixed_el, move_box = el2, el1, b2
            else:
                if el1['ifc_id'] > el2['ifc_id']:
                    move_el, fixed_el, move_box = el1, el2, b1
                else:
                    move_el, fixed_el, move_box = el2, el1, b2

            direction, offset, new_pos = _resolve(b1, b2, move_box['center'])

            clash_type = f"{_stype(move_el['type'])}_{_stype(fixed_el['type'])}"
            clash_id = f"Clash{len(clashes) + 1}"

            clashes.append({
                "clash_id": clash_id,
                "move_element_id": str(move_el['ifc_id']),
                "move_element_global_id": move_el['id'],
                "move_element_type": _stype(move_el['type']),
                "move_element_name": move_el.get('name'),
                "fixed_element_id": str(fixed_el['ifc_id']),
                "fixed_element_global_id": fixed_el['id'],
                "fixed_element_type": _stype(fixed_el['type']),
                "fixed_element_name": fixed_el.get('name'),
                "clash_type": clash_type,
                "original_position": [round(v, 4) for v in move_box['center']],
                "new_position": new_pos,
                "strategy": "OFFSET",
                "reason": _reason(t1, t2, move_el, fixed_el, p1, p2),
                "offset": offset,
                "direction": direction,
            })

    return clashes
