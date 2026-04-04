import xml.etree.ElementTree as ET

# -----------------------------
# LOAD XML FILE
# -----------------------------
tree = ET.parse("hero.xml")   # your file name
root = tree.getroot()

# -----------------------------
# EXTRACT CLASH DATA
# -----------------------------
clashes = []

for clash in root.findall(".//clashresult"):
    
    clash_id = clash.get("name")
    distance = float(clash.get("distance"))

    # Get position
    pos = clash.find(".//pos3f")
    x = float(pos.get("x"))
    y = float(pos.get("y"))
    z = float(pos.get("z"))

    # Get both objects
    objects = clash.findall(".//clashobject")

    def extract_object(obj):
        element_id = obj.find(".//value").text
        
        name = ""
        obj_type = ""

        for tag in obj.findall(".//smarttag"):
            if tag.find("name").text == "Item Name":
                name = tag.find("value").text
            if tag.find("name").text == "Item Type":
                obj_type = tag.find("value").text

        return element_id, name, obj_type

    id1, name1, type1 = extract_object(objects[0])
    id2, name2, type2 = extract_object(objects[1])

    clashes.append([
        clash_id, distance,
        f"({x:.2f}, {y:.2f}, {z:.2f})",
        name1, type1, id1,
        name2, type2, id2
    ])

# -----------------------------
# PRINT TABLE
# -----------------------------
print("\nCLASH DATA TABLE\n")

header = [
    "Clash ID", "Distance", "Position",
    "Item1 Name", "Type1", "ID1",
    "Item2 Name", "Type2", "ID2"
]

# Print header
print("{:<10} {:<10} {:<25} {:<15} {:<10} {:<10} {:<15} {:<10} {:<10}".format(*header))
print("-" * 120)

# Print rows
for row in clashes[:20]:   # show first 20 (remove [:20] for all)
    print("{:<10} {:<10} {:<25} {:<15} {:<10} {:<10} {:<15} {:<10} {:<10}".format(*row))