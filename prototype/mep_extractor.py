import ifcopenshell
import ifcopenshell.util.placement

# IFC4 parent class — covers ALL MEP subtypes via inheritance.
# IfcOpenShell's by_type() returns all subtype instances too.
# Explicit subclasses are used as fallback for older schemas (IFC2X3).
MEP_PARENT_CLASS = "IfcDistributionElement"

MEP_EXPLICIT_CLASSES = [
    # Flow segments
    "IfcPipeSegment", "IfcPipeFitting",
    "IfcDuctSegment", "IfcDuctFitting",
    "IfcCableCarrierSegment", "IfcCableSegment",
    "IfcCableCarrierFitting", "IfcCableFitting",
    # Flow distribution
    "IfcFlowTerminal", "IfcFlowFitting",
    "IfcFlowController", "IfcFlowStorageDevice",
    "IfcFlowMovingDevice", "IfcEnergyConversionDevice",
    # Control
    "IfcDistributionControlElement",
    "IfcSensor", "IfcActuator", "IfcController",
    "IfcAlarm", "IfcUnitaryControlElement",
    # Electrical / fire
    "IfcElectricDistributionBoard", "IfcElectricAppliance",
    "IfcJunctionBox", "IfcLightFixture",
    "IfcFireSuppressionTerminal", "IfcSanitaryTerminal",
    "IfcStackTerminal", "IfcWasteTerminal",
    "IfcAirTerminal", "IfcAirTerminalBox",
    # HVAC
    "IfcCoil", "IfcFilter", "IfcHumidifier",
    "IfcChiller", "IfcBoiler", "IfcUnitaryEquipment",
    "IfcAirToAirHeatRecovery",
    # Plumbing
    "IfcInterceptor", "IfcMedicalDevice",
    # Structural MEP support
    "IfcDistributionFlowElement",
]

def _world_xyz(element):
    try:
        if hasattr(element, 'ObjectPlacement') and element.ObjectPlacement:
            m = ifcopenshell.util.placement.get_local_placement(element.ObjectPlacement)
            return {"x": round(float(m[0][3]), 4), "y": round(float(m[1][3]), 4), "z": round(float(m[2][3]), 4)}
    except Exception:
        pass
    return {}

def _all_psets(element):
    result = {}
    if not hasattr(element, 'IsDefinedBy'):
        return result
    for rel in element.IsDefinedBy:
        if not rel.is_a('IfcRelDefinesByProperties'):
            continue
        pd = rel.RelatingPropertyDefinition
        if pd.is_a('IfcPropertySet'):
            pset = {}
            for p in (pd.HasProperties or []):
                if p.is_a('IfcPropertySingleValue'):
                    v = p.NominalValue
                    pset[p.Name] = getattr(v, 'wrappedValue', None) if v else None
                elif p.is_a('IfcPropertyEnumeratedValue'):
                    pset[p.Name] = [getattr(v, 'wrappedValue', str(v)) for v in (p.EnumerationValues or [])]
                elif p.is_a('IfcPropertyListValue'):
                    pset[p.Name] = [getattr(v, 'wrappedValue', str(v)) for v in (p.ListValues or [])]
                elif p.is_a('IfcPropertyBoundedValue'):
                    pset[p.Name] = {
                        "lower": getattr(p.LowerBoundValue, 'wrappedValue', None) if p.LowerBoundValue else None,
                        "upper": getattr(p.UpperBoundValue, 'wrappedValue', None) if p.UpperBoundValue else None
                    }
                else:
                    pset[p.Name] = str(p)
            if pset:
                result[pd.Name or 'UnnamedPropertySet'] = pset

        elif pd.is_a('IfcElementQuantity'):
            qset = {}
            for q in (pd.Quantities or []):
                if q.is_a('IfcQuantityLength'):
                    qset[q.Name] = {"value": q.LengthValue, "unit": "m"}
                elif q.is_a('IfcQuantityArea'):
                    qset[q.Name] = {"value": q.AreaValue, "unit": "m2"}
                elif q.is_a('IfcQuantityVolume'):
                    qset[q.Name] = {"value": q.VolumeValue, "unit": "m3"}
                elif q.is_a('IfcQuantityCount'):
                    qset[q.Name] = {"value": q.CountValue, "unit": "count"}
                elif q.is_a('IfcQuantityWeight'):
                    qset[q.Name] = {"value": q.WeightValue, "unit": "kg"}
            if qset:
                result[pd.Name or 'UnnamedQuantities'] = qset
    return result

def _type_psets(element):
    result = {}
    if not hasattr(element, 'IsTypedBy'):
        return result
    for rel in element.IsTypedBy:
        if rel.is_a('IfcRelDefinesByType') and rel.RelatingType:
            t = rel.RelatingType
            result['_type_object'] = {
                'name': getattr(t, 'Name', None),
                'description': getattr(t, 'Description', None),
                'type': t.is_a(),
                'predefined_type': getattr(t, 'PredefinedType', None)
            }
            for k, v in _all_psets(t).items():
                result[f"[Type]{k}"] = v
    return result

def _materials(element, ifc_file):
    out = []
    try:
        for rel in ifc_file.get_inverse(element):
            if not rel.is_a('IfcRelAssociatesMaterial'):
                continue
            mat = rel.RelatingMaterial
            if not mat:
                continue
            if mat.is_a('IfcMaterial'):
                out.append({"name": mat.Name, "category": getattr(mat, 'Category', None)})
            elif mat.is_a('IfcMaterialList'):
                for m in (mat.Materials or []):
                    out.append({"name": m.Name})
            elif mat.is_a('IfcMaterialLayerSetUsage'):
                for layer in (mat.ForLayerSet.MaterialLayers or []):
                    if layer.Material:
                        out.append({"name": layer.Material.Name, "thickness_m": getattr(layer, 'LayerThickness', None)})
            elif mat.is_a('IfcMaterialConstituentSet'):
                for c in (mat.MaterialConstituents or []):
                    if c.Material:
                        out.append({"name": c.Material.Name, "fraction": getattr(c, 'Fraction', None)})
    except Exception:
        pass
    return out

def _systems(element, ifc_file):
    out = []
    try:
        for rel in ifc_file.get_inverse(element):
            if rel.is_a('IfcRelAssignsToGroup'):
                g = rel.RelatingGroup
                if g and (g.is_a('IfcDistributionSystem') or g.is_a('IfcSystem') or g.is_a('IfcZone')):
                    out.append({"id": getattr(g, 'GlobalId', None), "name": getattr(g, 'Name', None), "type": g.is_a()})
    except Exception:
        pass
    return out

def _spatial(element, ifc_file):
    try:
        for rel in ifc_file.get_inverse(element):
            if rel.is_a('IfcRelContainedInSpatialStructure'):
                c = rel.RelatingStructure
                if c:
                    return {"id": getattr(c, 'GlobalId', None), "name": getattr(c, 'Name', None),
                            "type": c.is_a(), "elevation": getattr(c, 'Elevation', None)}
    except Exception:
        pass
    return {}

def _connections(element, ifc_file):
    out = []
    try:
        for rel in ifc_file.get_inverse(element):
            if rel.is_a('IfcRelConnectsElements'):
                other = rel.RelatedElement if rel.RelatingElement == element else rel.RelatingElement
                if other and other != element:
                    out.append({"id": getattr(other, 'GlobalId', None), "ifc_id": other.id(),
                                "type": other.is_a(), "name": getattr(other, 'Name', None)})
    except Exception:
        pass
    return out

def _flat_props(all_props):
    flat = {}
    for pset_data in all_props.values():
        if isinstance(pset_data, dict):
            for k, v in pset_data.items():
                if k.startswith('_'):
                    continue
                if isinstance(v, (int, float, str, bool)) or v is None:
                    flat[k] = v
                elif isinstance(v, dict) and 'value' in v:
                    flat[k] = v['value']
    return flat


def _build_element_record(el, ifc_file):
    all_props = _all_psets(el)
    all_props.update(_type_psets(el))
    flat = _flat_props(all_props)

    return {
        "id": getattr(el, 'GlobalId', 'unknown'),
        "ifc_id": el.id(),
        "type": el.is_a(),
        "name": getattr(el, 'Name', None) or 'Unnamed',
        "tag": getattr(el, 'Tag', None),
        "description": getattr(el, 'Description', None),
        "object_type": getattr(el, 'ObjectType', None),
        "predefined_type": getattr(el, 'PredefinedType', None),
        "properties": all_props,
        "flat_properties": flat,
        "materials": _materials(el, ifc_file),
        "systems": _systems(el, ifc_file),
        "spatial_containment": _spatial(el, ifc_file),
        "connected_to": _connections(el, ifc_file),
        "location": _world_xyz(el),
    }


def extract_mep_data(ifc_filepath):
    try:
        ifc_file = ifcopenshell.open(ifc_filepath)
    except Exception as e:
        raise ValueError(f"Failed to open IFC file: {str(e)}")

    seen = set()
    elements_out = []

    # ── Strategy 1: broad parent-class query (IFC4) ──────────────────────────
    # IfcDistributionElement covers every MEP subtype: pipes, ducts, terminals,
    # fittings, controllers, sensors, equipment, cables, etc.
    try:
        for el in ifc_file.by_type(MEP_PARENT_CLASS):
            eid = el.id()
            if eid in seen:
                continue
            seen.add(eid)
            elements_out.append(_build_element_record(el, ifc_file))
    except Exception:
        pass  # Schema may not support the parent class — fall through

    # ── Strategy 2: explicit per-class fallback (IFC2X3 / partial schemas) ───
    # Always run this so classes NOT covered by the parent (e.g. older exports)
    # are still picked up — deduplication by seen set prevents double counting.
    for ifc_class in MEP_EXPLICIT_CLASSES:
        try:
            items = ifc_file.by_type(ifc_class)
        except Exception:
            continue
        for el in items:
            eid = el.id()
            if eid in seen:
                continue
            seen.add(eid)
            elements_out.append(_build_element_record(el, ifc_file))

    return elements_out
