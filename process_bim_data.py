import ifcopenshell
import ifcopenshell.geom
import xml.etree.ElementTree as ET
import json
import os
import pandas as pd
from collections import defaultdict
import re

# --- 1. IFC Data Extraction ---

def get_property_sets(element):
    """Extracts all property sets from an IFC element."""
    property_sets = {}
    if hasattr(element, 'IsDefinedBy'):
        for definition in element.IsDefinedBy:
            if isinstance(definition, ifcopenshell.entity_instance) and definition.is_a('IfcRelDefinesByProperties'):
                prop_set_def = definition.RelatingPropertyDefinition
                if prop_set_def and prop_set_def.is_a('IfcPropertySet'):
                    set_name = prop_set_def.Name
                    properties = {}
                    for prop in prop_set_def.HasProperties:
                        if prop.is_a('IfcPropertySingleValue'):
                            prop_name = prop.Name
                            prop_value = prop.NominalValue.wrappedValue if prop.NominalValue else None
                            properties[prop_name] = prop_value
                    property_sets[set_name] = properties
    return property_sets

def get_quantities(element):
    """Extracts all quantities from an IFC element."""
    quantities = {}
    if hasattr(element, 'IsDefinedBy'):
        for definition in element.IsDefinedBy:
            if isinstance(definition, ifcopenshell.entity_instance) and definition.is_a('IfcRelDefinesByProperties'):
                prop_set_def = definition.RelatingPropertyDefinition
                if prop_set_def and prop_set_def.is_a('IfcElementQuantity'):
                    set_name = prop_set_def.Name
                    quantity_values = {}
                    for quantity in prop_set_def.Quantities:
                        q_name = quantity.Name
                        q_value = None
                        if hasattr(quantity, 'LengthValue'):
                            q_value = quantity.LengthValue
                        elif hasattr(quantity, 'AreaValue'):
                            q_value = quantity.AreaValue
                        elif hasattr(quantity, 'VolumeValue'):
                            q_value = quantity.VolumeValue
                        elif hasattr(quantity, 'WeightValue'):
                            q_value = quantity.WeightValue
                        quantity_values[q_name] = q_value
                    quantities[set_name] = quantity_values
    return quantities

def get_bounding_box(element, settings):
    """Calculates the bounding box of an element."""
    try:
        shape = ifcopenshell.geom.create_shape(settings, element)
        verts = shape.geometry.verts
        min_x = min(verts[i] for i in range(0, len(verts), 3))
        max_x = max(verts[i] for i in range(0, len(verts), 3))
        min_y = min(verts[i] for i in range(1, len(verts), 3))
        max_y = max(verts[i] for i in range(1, len(verts), 3))
        min_z = min(verts[i] for i in range(2, len(verts), 3))
        max_z = max(verts[i] for i in range(2, len(verts), 3))
        return {
            "min": {"x": min_x, "y": min_y, "z": min_z},
            "max": {"x": max_x, "y": max_y, "z": max_z}
        }
    except Exception:
        return None

def get_element_spatial_container(element):
    """Finds the spatial container (e.g., storey) of an element."""
    if hasattr(element, 'ContainedInStructure'):
        for rel in element.ContainedInStructure:
            if rel.is_a('IfcRelContainedInSpatialStructure'):
                spatial_structure = rel.RelatingStructure
                if spatial_structure and spatial_structure.is_a('IfcBuildingStorey'):
                    return {
                        "step_id": spatial_structure.id(),
                        "global_id": spatial_structure.GlobalId,
                        "name": spatial_structure.Name
                    }
    return None

def extract_ifc_data(ifc_path):
    """
    Reads an IFC file and extracts all useful BIM data.
    """
    ifc_file = ifcopenshell.open(ifc_path)
    settings = ifcopenshell.geom.settings()
    
    ifc_data = {
        "metadata": {
            "schema": ifc_file.schema,
            "filename": os.path.basename(ifc_path),
            "export_time": ifc_file.header.file_name.time_stamp,
            "exporting_application": ifc_file.header.file_name.originating_system,
            "author": ", ".join(ifc_file.header.file_name.author),
            "organization": ", ".join(ifc_file.header.file_name.organization),
        },
        "project_hierarchy": {},
        "elements": [],
    }

    # Project hierarchy
    project = ifc_file.by_type('IfcProject')[0]
    ifc_data["project_hierarchy"]["project"] = {
        "name": project.Name,
        "global_id": project.GlobalId,
        "step_id": project.id()
    }

    elements = []
    products = ifc_file.by_type('IfcProduct')
    for product in products:
        element_data = {
            "step_id": product.id(),
            "global_id": product.GlobalId,
            "name": product.Name,
            "description": product.Description,
            "ifc_type": product.is_a(),
            "object_type": product.ObjectType,
            "tag": getattr(product, 'Tag', None),
            "spatial_container": get_element_spatial_container(product),
            "properties": get_property_sets(product),
            "quantities": get_quantities(product),
            "bounding_box": get_bounding_box(product, settings),
        }
        
        # Revit Element ID from properties
        revit_id = None
        for pset_name, pset in element_data["properties"].items():
            if "ElementId" in pset:
                revit_id = pset["ElementId"]
                break
            # Sometimes it's just "Id"
            if not revit_id and "Id" in pset:
                 revit_id = pset["Id"]
        element_data["revit_element_id"] = revit_id

        elements.append(element_data)

    ifc_data["elements"] = elements
    return ifc_data

# --- 2. XML Clash Data Extraction ---

def parse_xml_clash_report(xml_path):
    """
    Parses a Navisworks XML clash report.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    clash_data = {
        "file_info": {
            "filename": root.find('.//batchtest').get('filename'),
            "filepath": root.find('.//batchtest').get('filepath'),
            "units": root.find('.//batchtest').get('units'),
        },
        "clash_tests": [],
    }

    for clashtest in root.findall('.//clashtest'):
        test_info = {
            "name": clashtest.get('name'),
            "test_type": clashtest.get('test_type'),
            "status": clashtest.get('status'),
            "tolerance": clashtest.get('tolerance'),
            "summary": {
                "total": int(clashtest.find('.//summary').get('total')),
                "new": int(clashtest.find('.//summary').get('new')),
                "active": int(clashtest.find('.//summary').get('active')),
                "reviewed": int(clashtest.find('.//summary').get('reviewed')),
                "approved": int(clashtest.find('.//summary').get('approved')),
                "resolved": int(clashtest.find('.//summary').get('resolved')),
            },
            "clash_results": [],
        }

        for result in clashtest.findall('.//clashresult'):
            status_node = result.find('.//status')
            distance_node = result.find('.//distance')
            clashpoint_node = result.find('.//clashpoint/pos3f')
            gridlocation_node = result.find('.//gridlocation')
            createddate_node = result.find('.//createddate/date')
            image_node = result.find('.//image')

            clash_result = {
                "name": result.get('name'),
                "guid": result.get('guid'),
                "status": status_node.text if status_node is not None else None,
                "distance": float(distance_node.text) if distance_node is not None else None,
                "clash_point": {
                    "x": float(clashpoint_node.get('x')) if clashpoint_node is not None else None,
                    "y": float(clashpoint_node.get('y')) if clashpoint_node is not None else None,
                    "z": float(clashpoint_node.get('z')) if clashpoint_node is not None else None,
                },
                "grid_location": gridlocation_node.text if gridlocation_node is not None else None,
                "created_date": createddate_node.text if createddate_node is not None else None,
                "image_href": image_node.get('href') if image_node is not None else None,
                "objects": [],
            }

            for obj in result.findall('.//clashobject'):
                layer_node = obj.find('.//layer')
                name_node = obj.find('.//name')
                type_node = obj.find('.//type')

                clash_object = {
                    "element_id": None,
                    "layer": layer_node.text if layer_node is not None else None,
                    "item_name": name_node.text if name_node is not None else None,
                    "item_type": type_node.text if type_node is not None else None,
                    "smart_tags": {},
                }
                
                # Find Element ID in smart tags
                for tag in obj.findall('.//smarttag'):
                    prop = tag.find('property')
                    if prop is not None:
                        name_node = prop.find('name')
                        value_node = prop.find('value')
                        if name_node is not None and value_node is not None and name_node.text is not None:
                            name = name_node.text
                            value = value_node.text
                            clash_object["smart_tags"][name] = value
                            if name == 'Element ID':
                                clash_object['element_id'] = value

                clash_result["objects"].append(clash_object)
            
            test_info["clash_results"].append(clash_result)
        
        clash_data["clash_tests"].append(test_info)

    return clash_data

# --- 3. ID Mapping and Merging ---

def create_id_maps(ifc_data):
    """Creates dictionaries for fast ID lookups."""
    ifc_map_by_step_id = {elem['step_id']: elem for elem in ifc_data['elements']}
    ifc_map_by_global_id = {elem['global_id']: elem for elem in ifc_data['elements']}
    
    # Handle potential non-unique Revit IDs
    ifc_map_by_revit_id = defaultdict(list)
    for elem in ifc_data['elements']:
        if elem.get('revit_element_id'):
            ifc_map_by_revit_id[str(elem['revit_element_id'])].append(elem)
            
    return ifc_map_by_step_id, ifc_map_by_global_id, ifc_map_by_revit_id

def merge_datasets(ifc_data, clash_data):
    """
    Merges IFC and Clash data based on element IDs.
    """
    ifc_map_by_step_id, ifc_map_by_global_id, ifc_map_by_revit_id = create_id_maps(ifc_data)
    
    merged_results = []
    unmatched_clashes = []
    matched_ifc_step_ids = set()
    id_mapping_log = []

    for test in clash_data['clash_tests']:
        for clash in test['clash_results']:
            merged_clash = {
                "clash_id": clash['guid'],
                "clash_name": clash['name'],
                "clash_guid": clash['guid'],
                "distance": clash['distance'],
                "position": clash['clash_point'],
                "grid_location": clash['grid_location'],
                "created_at": clash['created_date'],
                "objects": []
            }

            all_objects_matched = True
            for obj in clash['objects']:
                xml_element_id = obj.get('element_id')
                matched_ifc_element = None
                match_type = "unresolved"

                # 1. Exact match on Revit Element ID
                if xml_element_id and str(xml_element_id) in ifc_map_by_revit_id:
                    # For simplicity, take the first match if multiple exist
                    matched_ifc_element = ifc_map_by_revit_id[str(xml_element_id)][0]
                    match_type = "exact_revit_id"
                
                # Heuristic matching could be added here if needed

                merged_object = {
                    "xml_element_id": xml_element_id,
                    "matched": matched_ifc_element is not None,
                    "match_type": match_type,
                    "clash_details": {
                        "item_name": obj["item_name"],
                        "item_type": obj["item_type"],
                        "layer": obj["layer"],
                    },
                    "ifc": None
                }

                if matched_ifc_element:
                    matched_ifc_step_ids.add(matched_ifc_element['step_id'])
                    merged_object["ifc"] = {
                        "global_id": matched_ifc_element['global_id'],
                        "step_id": matched_ifc_element['step_id'],
                        "name": matched_ifc_element['name'],
                        "type": matched_ifc_element['ifc_type'],
                        "storey": matched_ifc_element.get('spatial_container', {}).get('name'),
                        "bounding_box": matched_ifc_element.get('bounding_box'),
                        "properties": matched_ifc_element.get('properties'),
                        "quantities": matched_ifc_element.get('quantities'),
                    }
                    id_mapping_log.append({
                        "xml_element_id": xml_element_id,
                        "ifc_step_id": matched_ifc_element['step_id'],
                        "ifc_global_id": matched_ifc_element['global_id'],
                        "match_type": match_type
                    })
                else:
                    all_objects_matched = False
                    unmatched_clashes.append(obj)

                merged_clash["objects"].append(merged_object)
            
            merged_results.append(merged_clash)

    unmatched_ifc = [elem for elem in ifc_data['elements'] if elem['step_id'] not in matched_ifc_step_ids]

    return merged_results, id_mapping_log, unmatched_ifc, unmatched_clashes

# --- 4. Export and Main Execution ---

def export_to_json(data, filename, indent=2):
    """Exports data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=indent, default=str) # Use default=str for non-serializable types

def main():
    """
    Main function to run the entire pipeline.
    """
    # --- Configuration ---
    # Assumes files are in a 'stages' subdirectory relative to the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ifc_file_path = os.path.join(script_dir, 'stages', 'RVT_Model_MEP_for_Orkathon.ifc')
    xml_file_path = os.path.join(script_dir, 'stages', 'hero.xml')
    output_dir = os.path.join(script_dir, 'output')

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # --- 1. Extraction ---
    print("Step 1: Extracting data from IFC file...")
    ifc_data = extract_ifc_data(ifc_file_path)
    export_to_json(ifc_data, os.path.join(output_dir, 'ifc_full_data.json'))
    print(f"  - Extracted {len(ifc_data['elements'])} IFC entities.")

    print("Step 2: Extracting data from XML clash report...")
    clash_data = parse_xml_clash_report(xml_file_path)
    export_to_json(clash_data, os.path.join(output_dir, 'clash_full_data.json'))
    total_clashes = sum(len(test['clash_results']) for test in clash_data['clash_tests'])
    print(f"  - Extracted {total_clashes} clash results.")

    # --- 2. Merging ---
    print("Step 3: Merging datasets and mapping IDs...")
    merged_data, id_mapping, unmatched_ifc, unmatched_clashes = merge_datasets(ifc_data, clash_data)
    
    num_successful_matches = len(id_mapping)
    num_unmatched_ifc = len(unmatched_ifc)
    num_unmatched_clashes = len(unmatched_clashes)
    
    print(f"  - Successful matches: {num_successful_matches}")
    print(f"  - Unmatched IFC entities: {num_unmatched_ifc}")
    print(f"  - Unmatched clash objects: {num_unmatched_clashes}")

    # --- 3. Exporting ---
    print("Step 4: Exporting final JSON files...")
    export_to_json(merged_data, os.path.join(output_dir, 'merged_dataset.json'))
    export_to_json(id_mapping, os.path.join(output_dir, 'id_mapping.json'))
    export_to_json(unmatched_ifc, os.path.join(output_dir, 'unmatched_ifc.json'))
    export_to_json(unmatched_clashes, os.path.join(output_dir, 'unmatched_clashes.json'))
    print(f"  - All files written to '{output_dir}' directory.")

    # --- 4. Summary Preview ---
    print("\n--- Merged Data Preview (first 2 clashes) ---")
    df = pd.json_normalize(merged_data, record_path=['objects'], meta=['clash_name', 'distance', ['position', 'x'], ['position', 'y'], ['position', 'z']])
    
    # Select and rename columns for a cleaner preview
    preview_cols = {
        'clash_name': 'ClashName',
        'distance': 'Distance',
        'xml_element_id': 'XMLElementID',
        'matched': 'Matched',
        'match_type': 'MatchType',
        'ifc.step_id': 'IFC_StepID',
        'ifc.name': 'IFC_Name',
        'ifc.type': 'IFC_Type'
    }
    
    # Filter for columns that exist in the dataframe
    existing_cols = {k: v for k, v in preview_cols.items() if k in df.columns}
    
    if not df.empty:
        preview_df = df[list(existing_cols.keys())].rename(columns=existing_cols)
        print(preview_df.head(10).to_string())
    else:
        print("No merged data to preview.")

if __name__ == "__main__":
    main()
