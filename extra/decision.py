import xml.etree.ElementTree as ET
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class BoundingBox:
    """Axis-Aligned Bounding Box for collision detection"""
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float
    
    @classmethod
    def from_point_and_size(cls, point: Tuple[float, float, float], 
                            width: float = 0.5, height: float = 0.5, 
                            depth: float = 0.5):
        """Create bounding box from center point and dimensions"""
        x, y, z = point
        return cls(
            min_x=x - width/2, max_x=x + width/2,
            min_y=y - depth/2, max_y=y + depth/2,
            min_z=z - height/2, max_z=z + height/2
        )
    
    def overlaps(self, other: 'BoundingBox') -> bool:
        """Check if this box overlaps with another box (AABB collision)"""
        return (self.max_x > other.min_x and self.min_x < other.max_x and
                self.max_y > other.min_y and self.min_y < other.max_y and
                self.max_z > other.min_z and self.min_z < other.max_z)
    
    def copy(self) -> 'BoundingBox':
        return BoundingBox(self.min_x, self.min_y, self.min_z,
                          self.max_x, self.max_y, self.max_z)


@dataclass
class Element:
    """Represents a building element with its properties"""
    element_id: str
    name: str
    element_type: str
    normalized_type: str  # PIPE, DUCT, STRUCTURE, CABLE_TRAY, OTHER
    position: Tuple[float, float, float]  # (x, y, z)
    bounding_box: Optional[BoundingBox] = None
    dimensions: Tuple[float, float, float] = (0.5, 0.5, 0.5)  # (width, height, depth)
    
    def get_bounding_box(self) -> BoundingBox:
        """Get or create bounding box for this element"""
        if self.bounding_box is None:
            self.bounding_box = BoundingBox.from_point_and_size(
                self.position, 
                self.dimensions[0], 
                self.dimensions[1], 
                self.dimensions[2]
            )
        return self.bounding_box
    
    def move_to(self, new_position: Tuple[float, float, float]):
        """Move element to new position"""
        self.position = new_position
        # Invalidate old bounding box
        self.bounding_box = BoundingBox.from_point_and_size(
            new_position, 
            self.dimensions[0], 
            self.dimensions[1], 
            self.dimensions[2]
        )


@dataclass
class Clash:
    """Represents a clash between two elements"""
    clash_id: str
    distance: float  # Negative = penetration depth
    position: Tuple[float, float, float]
    item1: Dict[str, Any]
    item2: Dict[str, Any]
    element1: Optional[Element] = None
    element2: Optional[Element] = None
    clash_type: str = ""  # PIPE_PIPE, PIPE_DUCT, PIPE_STRUCTURE, etc.
    decision: Optional['ClashDecision'] = None


@dataclass
class CandidateMove:
    """Represents a candidate rerouting solution"""
    direction: str  # UP, DOWN, LEFT, RIGHT, FORWARD, BACKWARD
    offset: float  # Distance to move
    new_position: Tuple[float, float, float]
    strategy: str  # OFFSET, LATERAL, DETOUR
    is_valid: bool = False
    collision_free: bool = False
    validation_message: str = ""


@dataclass
class ClashDecision:
    """Decision for resolving a clash"""
    clash_id: str
    move_element_id: str
    move_element_type: str
    fixed_element_id: str
    fixed_element_type: str
    clash_type: str
    original_position: Tuple[float, float, float]
    new_position: Tuple[float, float, float]
    strategy: str
    reason: str
    candidate_accepted: Optional[CandidateMove] = None


# ============================================================================
# ELEMENT TYPE NORMALIZATION
# ============================================================================

class ElementTypeNormalizer:
    """Normalizes element names to standard types"""
    
    # Mapping for Pipe types
    PIPE_KEYWORDS = ['pipe', 'soil', 'vent', 'waste', 'water', 'gas', 
                     'drain', 'sewer', 'rainwater', 'cold', 'hot']
    
    # Mapping for Duct types  
    DUCT_KEYWORDS = ['duct', 'fad', 'sad', 'ted', 'air', 'hvac', 'supply', 
                     'return', 'exhaust', 'diffuser', 'grille']
    
    # Mapping for Structure types
    STRUCTURE_KEYWORDS = ['manhole', 'solid', 'beam', 'column', 'slab', 
                          'wall', 'foundation', 'structure']
    
    # Mapping for Cable Tray types
    CABLE_TRAY_KEYWORDS = ['cable', 'tray', 'conduit', 'electrical', 
                           'busway', 'wire']
    
    @classmethod
    def normalize(cls, element_name: str, element_type: str) -> str:
        """
        Normalize element to one of: PIPE, DUCT, STRUCTURE, CABLE_TRAY, OTHER
        """
        name_lower = element_name.lower()
        type_lower = element_type.lower()
        
        # Check STRUCTURE first (highest priority - should not move)
        if any(kw in name_lower for kw in cls.STRUCTURE_KEYWORDS):
            return "STRUCTURE"
        
        # Check PIPE
        if any(kw in name_lower for kw in cls.PIPE_KEYWORDS):
            return "PIPE"
        
        # Check DUCT
        if any(kw in name_lower for kw in cls.DUCT_KEYWORDS):
            return "DUCT"
        
        # Check CABLE TRAY
        if any(kw in name_lower for kw in cls.CABLE_TRAY_KEYWORDS):
            return "CABLE_TRAY"
        
        # Default based on type or unknown
        if "solid" in type_lower:
            return "STRUCTURE"
        
        return "OTHER"


# ============================================================================
# CLASH TYPE IDENTIFIER
# ============================================================================

class ClashTypeIdentifier:
    """Identifies the type of clash between two elements"""
    
    # Priority order for clash types (higher index = higher priority)
    CLASH_TYPE_PRIORITY = {
        "PIPE_STRUCTURE": 10,
        "DUCT_STRUCTURE": 9,
        "CABLE_TRAY_STRUCTURE": 8,
        "PIPE_DUCT": 7,
        "CABLE_TRAY_PIPE": 6,
        "CABLE_TRAY_DUCT": 5,
        "PIPE_PIPE": 4,
        "DUCT_DUCT": 3,
        "STRUCTURE_STRUCTURE": 2,
        "OTHER": 1,
    }
    
    @classmethod
    def identify(cls, type1: str, type2: str) -> str:
        """Identify clash type based on normalized element types"""
        types = sorted([type1, type2])
        
        if types == ["DUCT", "PIPE"]:
            return "PIPE_DUCT"
        elif types == ["CABLE_TRAY", "PIPE"]:
            return "CABLE_TRAY_PIPE"
        elif types == ["CABLE_TRAY", "DUCT"]:
            return "CABLE_TRAY_DUCT"
        elif types == ["PIPE", "PIPE"]:
            return "PIPE_PIPE"
        elif types == ["DUCT", "DUCT"]:
            return "DUCT_DUCT"
        elif "STRUCTURE" in types:
            if "PIPE" in types:
                return "PIPE_STRUCTURE"
            elif "DUCT" in types:
                return "DUCT_STRUCTURE"
            elif "CABLE_TRAY" in types:
                return "CABLE_TRAY_STRUCTURE"
            return "STRUCTURE_STRUCTURE"
        else:
            return "OTHER"
    
    @classmethod
    def get_priority(cls, clash_type: str) -> int:
        """Get priority of clash type (higher = more critical)"""
        return cls.CLASH_TYPE_PRIORITY.get(clash_type, 1)


# ============================================================================
# DECISION ENGINE
# ============================================================================

class DecisionEngine:
    """
    Rule-based engine to decide which element should move in a clash
    """
    
    # RULES: (type1, type2) -> element to move (1 = first, 2 = second, 0 = either)
    RULES = {
        ("PIPE", "DUCT"): 1,  # Move Pipe
        ("CABLE_TRAY", "PIPE"): 2,  # Move Pipe
        ("CABLE_TRAY", "DUCT"): 1,  # Move Cable Tray
        ("PIPE", "PIPE"): 0,  # Either can move
        ("DUCT", "DUCT"): 0,  # Either can move
        ("PIPE", "STRUCTURE"): 1,  # Move Pipe (Structure fixed)
        ("DUCT", "STRUCTURE"): 1,  # Move Duct (Structure fixed)
        ("CABLE_TRAY", "STRUCTURE"): 1,  # Move Cable Tray (Structure fixed)
    }
    
    # Move reason mapping
    REASONS = {
        "PIPE_DUCT": "Pipe is more flexible and easier to reroute than duct",
        "CABLE_TRAY_PIPE": "Pipe is more flexible and easier to reroute than cable tray",
        "CABLE_TRAY_DUCT": "Cable tray is more flexible than duct",
        "PIPE_PIPE": "Either pipe can move - selecting the one with higher ID for consistency",
        "DUCT_DUCT": "Either duct can move - selecting the one with higher ID for consistency",
        "PIPE_STRUCTURE": "Structural elements cannot be moved",
        "DUCT_STRUCTURE": "Structural elements cannot be moved",
        "CABLE_TRAY_STRUCTURE": "Structural elements cannot be moved",
        "DEFAULT": "Selected based on engineering best practices"
    }
    
    @classmethod
    def decide(cls, clash: Clash) -> ClashDecision:
        """
        Decide which element should move to resolve the clash
        
        Returns:
            ClashDecision object with the decision details
        """
        type1 = clash.element1.normalized_type if clash.element1 else "OTHER"
        type2 = clash.element2.normalized_type if clash.element2 else "OTHER"
        
        clash_type = ClashTypeIdentifier.identify(type1, type2)
        
        # Get which element should move (1 = element1, 2 = element2, 0 = either)
        rule_key = tuple(sorted([type1, type2]))
        move_choice = cls.RULES.get(rule_key, 0)
        
        # If either can move, pick the one with higher ID (deterministic)
        if move_choice == 0:
            # Compare IDs (numeric part if possible)
            id1 = int(''.join(filter(str.isdigit, clash.item1.get('id', '0')))) if clash.item1 else 0
            id2 = int(''.join(filter(str.isdigit, clash.item2.get('id', '0')))) if clash.item2 else 0
            move_choice = 1 if id1 > id2 else 2
        
        # Determine which element moves
        if move_choice == 1:
            move_element = clash.element1
            fixed_element = clash.element2
            move_type = type1
            fixed_type = type2
        else:
            move_element = clash.element2
            fixed_element = clash.element1
            move_type = type2
            fixed_type = type1
        
        # Get reason
        reason = cls.REASONS.get(clash_type, cls.REASONS["DEFAULT"])
        
        return ClashDecision(
            clash_id=clash.clash_id,
            move_element_id=move_element.element_id if move_element else "",
            move_element_type=move_type,
            fixed_element_id=fixed_element.element_id if fixed_element else "",
            fixed_element_type=fixed_type,
            clash_type=clash_type,
            original_position=move_element.position if move_element else (0, 0, 0),
            new_position=(0, 0, 0),  # To be filled by rerouting engine
            strategy="",
            reason=reason
        )


# ============================================================================
# REROUTING ENGINE
# ============================================================================

class ReroutingEngine:
    """
    Generates candidate rerouting solutions and validates them using AABB
    """
    
    # Default offset distances (in meters)
    OFFSET_UP = 1.0
    OFFSET_DOWN = -1.0
    LATERAL_OFFSET = 0.5
    DETOUR_OFFSET = 0.75
    
    # Candidate generation strategies
    STRATEGIES = ['OFFSET', 'LATERAL', 'DETOUR']
    
    def __init__(self, all_elements: List[Element]):
        """
        Initialize with all elements for collision checking
        
        Args:
            all_elements: List of all elements in the model
        """
        self.all_elements = all_elements
        self.element_map = {e.element_id: e for e in all_elements if e}
    
    def generate_candidates(self, move_element: Element, clash_point: Tuple[float, float, float],
                           fixed_element: Optional[Element] = None) -> List[CandidateMove]:
        """
        Generate candidate moves for the element
        
        Args:
            move_element: Element to move
            clash_point: Point where clash occurs
            fixed_element: Fixed element (for reference)
            
        Returns:
            List of candidate moves
        """
        candidates = []
        x, y, z = move_element.position
        
        # Strategy 1: OFFSET - Move vertically
        for offset in [self.OFFSET_UP, self.OFFSET_DOWN]:
            new_z = z + offset
            candidates.append(CandidateMove(
                direction="UP" if offset > 0 else "DOWN",
                offset=abs(offset),
                new_position=(x, y, new_z),
                strategy="OFFSET"
            ))
        
        # Strategy 2: LATERAL - Move horizontally
        for offset in [self.LATERAL_OFFSET, -self.LATERAL_OFFSET]:
            # Try X direction
            new_x = x + offset
            candidates.append(CandidateMove(
                direction="RIGHT" if offset > 0 else "LEFT",
                offset=abs(offset),
                new_position=(new_x, y, z),
                strategy="LATERAL"
            ))
            
            # Try Y direction
            new_y = y + offset
            candidates.append(CandidateMove(
                direction="FORWARD" if offset > 0 else "BACKWARD",
                offset=abs(offset),
                new_position=(x, new_y, z),
                strategy="LATERAL"
            ))
        
        # Strategy 3: DETOUR - Combine X and Z or Y and Z
        # Detour up and right
        candidates.append(CandidateMove(
            direction="UP+RIGHT",
            offset=math.sqrt(self.OFFSET_UP**2 + self.LATERAL_OFFSET**2),
            new_position=(x + self.LATERAL_OFFSET, y, z + self.OFFSET_UP),
            strategy="DETOUR"
        ))
        
        # Detour up and left
        candidates.append(CandidateMove(
            direction="UP+LEFT",
            offset=math.sqrt(self.OFFSET_UP**2 + self.LATERAL_OFFSET**2),
            new_position=(x - self.LATERAL_OFFSET, y, z + self.OFFSET_UP),
            strategy="DETOUR"
        ))
        
        # Detour down and right
        candidates.append(CandidateMove(
            direction="DOWN+RIGHT",
            offset=math.sqrt(self.OFFSET_UP**2 + self.LATERAL_OFFSET**2),
            new_position=(x + self.LATERAL_OFFSET, y, z - self.OFFSET_UP),
            strategy="DETOUR"
        ))
        
        return candidates
    
    def validate_candidate(self, move_element: Element, candidate: CandidateMove,
                          fixed_element: Optional[Element] = None,
                          clearance: float = 0.1) -> CandidateMove:
        """
        Validate a candidate move using AABB collision detection
        
        Args:
            move_element: Element to move
            candidate: Candidate move to validate
            fixed_element: Fixed element (skip checking against this)
            clearance: Minimum clearance distance required
            
        Returns:
            Validated candidate with collision check results
        """
        # Save original position
        original_position = move_element.position
        
        # Temporarily move element
        move_element.move_to(candidate.new_position)
        
        # Check for collisions with all other elements
        collisions = []
        for other in self.all_elements:
            if other.element_id == move_element.element_id:
                continue
            if fixed_element and other.element_id == fixed_element.element_id:
                continue
            
            # Get bounding boxes
            box1 = move_element.get_bounding_box()
            box2 = other.get_bounding_box()
            
            # Check overlap
            if box1.overlaps(box2):
                collisions.append(other.element_id)
                
                # Also check clearance (soft clash)
                expanded_box = BoundingBox(
                    box2.min_x - clearance, box2.min_y - clearance, box2.min_z - clearance,
                    box2.max_x + clearance, box2.max_y + clearance, box2.max_z + clearance
                )
                if box1.overlaps(expanded_box):
                    collisions.append(f"{other.element_id}(clearance)")
        
        # Restore original position
        move_element.move_to(original_position)
        
        # Update candidate
        candidate.is_valid = len(collisions) == 0
        candidate.collision_free = len(collisions) == 0
        candidate.validation_message = f"No collisions" if len(collisions) == 0 else f"Collisions with: {collisions}"
        
        return candidate
    
    def find_best_candidate(self, candidates: List[CandidateMove]) -> Optional[CandidateMove]:
        """
        Find the best candidate move based on:
        1. Valid (no collisions)
        2. Minimal movement distance
        3. Preferred strategy (OFFSET > LATERAL > DETOUR)
        
        Args:
            candidates: List of candidate moves
            
        Returns:
            Best candidate or None if none valid
        """
        valid_candidates = [c for c in candidates if c.is_valid]
        
        if not valid_candidates:
            return None
        
        # Score candidates (lower is better)
        def score(candidate: CandidateMove) -> float:
            strategy_score = {
                "OFFSET": 0,
                "LATERAL": 1,
                "DETOUR": 2
            }.get(candidate.strategy, 3)
            return strategy_score * 10 + candidate.offset
        
        return min(valid_candidates, key=score)


# ============================================================================
# MAIN SYSTEM
# ============================================================================

class ClashResolutionSystem:
    """
    Main system for clash detection and rerouting
    """
    
    def __init__(self):
        self.clashes: List[Clash] = []
        self.elements: List[Element] = []
        self.decisions: List[ClashDecision] = []
        self.resolved_clashes: List[ClashDecision] = []
        self.unresolved_clashes: List[Clash] = []
    
    def add_element(self, element: Element):
        """Add an element to the system"""
        self.elements.append(element)
    
    def add_clash(self, clash: Clash):
        """Add a clash to the system"""
        # Link elements to clash
        clash.element1 = self._find_element(clash.item1.get('id', ''))
        clash.element2 = self._find_element(clash.item2.get('id', ''))
        self.clashes.append(clash)
    
    def _find_element(self, element_id: str) -> Optional[Element]:
        """Find element by ID"""
        for e in self.elements:
            if e.element_id == element_id:
                return e
        return None
    
    def process_clashes(self):
        """Process all clashes: decide, generate candidates, validate, select"""
        rerouting_engine = ReroutingEngine(self.elements)
        
        for clash in self.clashes:
            # Step 1: Make decision
            decision = DecisionEngine.decide(clash)
            
            # Step 2: Get move element
            move_element = self._find_element(decision.move_element_id)
            
            if not move_element:
                # Can't find element to move
                self.unresolved_clashes.append(clash)
                continue
            
            # Step 3: Generate candidate moves
            candidates = rerouting_engine.generate_candidates(
                move_element, 
                clash.position,
                self._find_element(decision.fixed_element_id)
            )
            
            # Step 4: Validate candidates
            validated_candidates = []
            for candidate in candidates:
                validated = rerouting_engine.validate_candidate(
                    move_element, candidate,
                    self._find_element(decision.fixed_element_id)
                )
                validated_candidates.append(validated)
            
            # Step 5: Find best candidate
            best_candidate = rerouting_engine.find_best_candidate(validated_candidates)
            
            if best_candidate:
                # Update decision with solution
                decision.new_position = best_candidate.new_position
                decision.strategy = best_candidate.strategy
                decision.candidate_accepted = best_candidate
                self.resolved_clashes.append(decision)
            else:
                # No valid solution found
                self.unresolved_clashes.append(clash)
    
    def print_summary(self):
        """Print resolution summary"""
        print("\n" + "="*80)
        print("CLASH RESOLUTION SUMMARY")
        print("="*80)
        print(f"Total Clashes: {len(self.clashes)}")
        print(f"Resolved: {len(self.resolved_clashes)}")
        print(f"Unresolved: {len(self.unresolved_clashes)}")
        print(f"Resolution Rate: {len(self.resolved_clashes)/len(self.clashes)*100:.1f}%")
        
        print("\n" + "-"*80)
        print("RESOLVED CLASHES")
        print("-"*80)
        
        for decision in self.resolved_clashes[:20]:  # Show first 20
            print(f"\nClash {decision.clash_id}:")
            print(f"  Type: {decision.clash_type}")
            print(f"  Move: {decision.move_element_type} (ID: {decision.move_element_id})")
            print(f"  Fixed: {decision.fixed_element_type} (ID: {decision.fixed_element_id})")
            print(f"  Reason: {decision.reason}")
            print(f"  Strategy: {decision.strategy}")
            print(f"  Original Position: {decision.original_position}")
            print(f"  New Position: {decision.new_position}")
            if decision.candidate_accepted:
                print(f"  Direction: {decision.candidate_accepted.direction}")
                print(f"  Offset: {decision.candidate_accepted.offset:.2f}m")
    
    def export_resolutions(self) -> List[Dict]:
        """Export resolutions as dictionary for JSON output"""
        return [
            {
                "clash_id": d.clash_id,
                "move_element_id": d.move_element_id,
                "move_element_type": d.move_element_type,
                "fixed_element_id": d.fixed_element_id,
                "fixed_element_type": d.fixed_element_type,
                "clash_type": d.clash_type,
                "original_position": list(d.original_position),
                "new_position": list(d.new_position),
                "strategy": d.strategy,
                "reason": d.reason,
                "offset": d.candidate_accepted.offset if d.candidate_accepted else None,
                "direction": d.candidate_accepted.direction if d.candidate_accepted else None
            }
            for d in self.resolved_clashes
        ]


# ============================================================================
# XML PARSER (Integration with your existing code)
# ============================================================================

def parse_navisworks_xml(xml_file_path: str) -> Tuple[List[Clash], List[Element]]:
    """
    Parse Navisworks XML clash report
    
    Args:
        xml_file_path: Path to the XML file
        
    Returns:
        Tuple of (clashes list, elements list)
    """
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    
    clashes = []
    elements_map = {}
    
    # Find all clash rows
    # Note: Adjust namespace based on your XML structure
    for content_row in root.findall(".//tr[@class='contentRow']"):
        try:
            # Extract clash ID
            clash_id_elem = content_row.find(".//td[@colspan='2']")
            clash_id = clash_id_elem.text.strip() if clash_id_elem is not None else "Unknown"
            
            # Extract distance
            distance_elem = content_row.find(".//td[@class='contentCell']")
            distance = float(distance_elem.text) if distance_elem is not None else 0
            
            # Extract position
            position_cells = content_row.findall(".//td[@colspan='3']")
            position_text = position_cells[0].text if position_cells else "x:0,y:0,z:0"
            # Parse "x:6.217, y:13.867, z:8.720"
            pos_dict = {}
            for part in position_text.split(','):
                if ':' in part:
                    key, val = part.split(':')
                    pos_dict[key.strip()] = float(val.strip())
            position = (pos_dict.get('x', 0), pos_dict.get('y', 0), pos_dict.get('z', 0))
            
            # Extract item1 info
            item1_id_elem = content_row.find(".//td[@class='item1Content']")
            item1_id = ""
            item1_name = ""
            item1_type = ""
            
            if item1_id_elem is not None:
                # Parse item1 info
                for elem in item1_id_elem.iter():
                    if elem.tag == 'i' and elem.text:
                        item1_id = elem.tail.strip() if elem.tail else ""
                    elif elem.tag == 'td' and not elem.get('class'):
                        pass
            
            # Alternative extraction - look for specific pattern
            item1_cells = content_row.findall(".//td[@class='item1Content']")
            if len(item1_cells) >= 4:
                item1_id = item1_cells[0].text.strip() if item1_cells[0].text else ""
                item1_name = item1_cells[2].text.strip() if len(item1_cells) > 2 and item1_cells[2].text else ""
                item1_type = item1_cells[3].text.strip() if len(item1_cells) > 3 and item1_cells[3].text else ""
            
            # Extract item2 info
            item2_cells = content_row.findall(".//td[@class='item2Content']")
            if len(item2_cells) >= 4:
                item2_id = item2_cells[0].text.strip() if item2_cells[0].text else ""
                item2_name = item2_cells[2].text.strip() if len(item2_cells) > 2 and item2_cells[2].text else ""
                item2_type = item2_cells[3].text.strip() if len(item2_cells) > 3 and item2_cells[3].text else ""
            else:
                item2_id = ""
                item2_name = ""
                item2_type = ""
            
            # Create clash
            clash = Clash(
                clash_id=clash_id,
                distance=distance,
                position=position,
                item1={"id": item1_id, "name": item1_name, "type": item1_type},
                item2={"id": item2_id, "name": item2_name, "type": item2_type}
            )
            
            # Create elements
            for item, pos in [(item1_id, position), (item2_id, position)]:
                if item and item not in elements_map:
                    # Determine element type from name
                    normalized_type = ElementTypeNormalizer.normalize(
                        item1_name if item == item1_id else item2_name,
                        item1_type if item == item1_id else item2_type
                    )
                    
                    element = Element(
                        element_id=item,
                        name=item1_name if item == item1_id else item2_name,
                        element_type=item1_type if item == item1_id else item2_type,
                        normalized_type=normalized_type,
                        position=pos
                    )
                    elements_map[item] = element
            
            clashes.append(clash)
            
        except Exception as e:
            print(f"Error parsing clash: {e}")
            continue
    
    return clashes, list(elements_map.values())


# ============================================================================
# DEMO FUNCTION
# ============================================================================

def run_demo():
    """Run a demo with sample data based on your clash report"""
    
    # Create sample elements based on the first few clashes
    elements = [
        Element("9512141", "FAD", "Solid", "DUCT", (6.217, 13.867, 8.720)),
        Element("9447390", "FAD", "Solid", "DUCT", (6.242, 13.867, 8.625)),
        Element("9512098", "FAD", "Solid", "DUCT", (13.179, 12.850, 4.055)),
        Element("9655153", "SAD", "Solid", "DUCT", (13.179, 12.850, 4.051)),
        Element("9778240", "MANHOLE", "Solid", "STRUCTURE", (21.297, 6.566, -0.172)),
        Element("8754584", "Soil Pipe", "Solid", "PIPE", (21.297, 6.566, -0.172)),
        Element("9497495", "FAD", "Solid", "DUCT", (6.242, 13.867, 8.625)),
        Element("9437364", "FAD", "Solid", "DUCT", (6.217, 14.092, 8.600)),
        Element("9447392", "FAD", "Solid", "DUCT", (6.635, 14.122, 8.625)),
        Element("9447393", "FAD", "Solid", "DUCT", (6.505, 13.867, 8.625)),
        Element("9747794", "Vent Pipe", "Solid", "PIPE", (9.286, -7.744, -0.170)),
        Element("9778645", "MANHOLE", "Solid", "STRUCTURE", (9.286, -7.744, -0.170)),
        Element("9740353", "MANHOLE", "Solid", "STRUCTURE", (-1.950, 4.507, -0.227)),
        Element("9741501", "Soil Pipe", "Solid", "PIPE", (-1.950, 4.507, -0.227)),
        Element("9512143", "FAD", "Solid", "DUCT", (5.774, 9.059, 8.300)),
        Element("9697637", "TED", "Solid", "DUCT", (5.774, 9.059, 8.300)),
    ]
    
    # Create clashes from your data
    clashes_data = [
        ("Clash1", -0.125, (6.217, 13.867, 8.720), "9512141", "9447390"),
        ("Clash2", -0.117, (13.179, 12.850, 4.055), "9512098", "9655153"),
        ("Clash3", -0.102, (21.297, 6.566, -0.172), "9778240", "8754584"),
        ("Clash4", -0.100, (6.242, 13.867, 8.625), "9497495", "9447390"),
        ("Clash5", -0.100, (6.217, 14.092, 8.600), "9512141", "9437364"),
        ("Clash8", -0.097, (9.286, -7.744, -0.170), "9747794", "9778645"),
        ("Clash9", -0.097, (-1.950, 4.507, -0.227), "9740353", "9741501"),
        ("Clash10", -0.096, (5.774, 9.059, 8.300), "9512143", "9697637"),
    ]
    
    clashes = []
    for clash_id, distance, position, id1, id2 in clashes_data:
        # Find names
        name1 = next((e.name for e in elements if e.element_id == id1), "Unknown")
        name2 = next((e.name for e in elements if e.element_id == id2), "Unknown")
        type1 = next((e.element_type for e in elements if e.element_id == id1), "Solid")
        type2 = next((e.element_type for e in elements if e.element_id == id2), "Solid")
        
        clash = Clash(
            clash_id=clash_id,
            distance=distance,
            position=position,
            item1={"id": id1, "name": name1, "type": type1},
            item2={"id": id2, "name": name2, "type": type2}
        )
        clashes.append(clash)
    
    # Initialize and run system
    system = ClashResolutionSystem()
    
    for element in elements:
        system.add_element(element)
    
    for clash in clashes:
        system.add_clash(clash)
    
    # Process all clashes
    system.process_clashes()
    
    # Print results
    system.print_summary()
    
    # Export resolutions
    resolutions = system.export_resolutions()
    
    print("\n" + "="*80)
    print("SAMPLE RESOLUTIONS (JSON format)")
    print("="*80)
    import json
    print(json.dumps(resolutions[:5], indent=2))
    
    return system


# ============================================================================
# AABB COLLISION TESTING UTILITY
# ============================================================================

class AABBCollisionTester:
    """Utility class for testing AABB collisions"""
    
    @staticmethod
    def test_overlap(box1: BoundingBox, box2: BoundingBox) -> bool:
        """Test if two bounding boxes overlap"""
        return box1.overlaps(box2)
    
    @staticmethod
    def test_all_collisions(elements: List[Element]) -> List[Tuple[Element, Element]]:
        """Find all collisions between elements"""
        collisions = []
        for i, e1 in enumerate(elements):
            for e2 in elements[i+1:]:
                if e1.get_bounding_box().overlaps(e2.get_bounding_box()):
                    collisions.append((e1, e2))
        return collisions
    
    @staticmethod
    def visualize_boxes(elements: List[Element], title: str = "Bounding Boxes"):
        """Simple text visualization of bounding boxes"""
        print(f"\n{title}")
        print("-" * 60)
        for e in elements:
            box = e.get_bounding_box()
            print(f"{e.element_id} ({e.normalized_type}): "
                  f"X[{box.min_x:.2f}-{box.max_x:.2f}] "
                  f"Y[{box.min_y:.2f}-{box.max_y:.2f}] "
                  f"Z[{box.min_z:.2f}-{box.max_z:.2f}]")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("AI-BASED CLASH DETECTION & REROUTING SYSTEM")
    print("CEC Hackathon 2025")
    print("="*80)
    
    # Run demo
    system = run_demo()
    
    # Demonstrate AABB collision testing
    print("\n" + "="*80)
    print("AABB COLLISION TESTING DEMO")
    print("="*80)
    
    tester = AABBCollisionTester()
    
    # Test collisions before rerouting
    print("\n--- BEFORE REROUTING ---")
    collisions = tester.test_all_collisions(system.elements)
    print(f"Found {len(collisions)} element collisions")
    
    # Visualize a few elements
    tester.visualize_boxes(system.elements[:5], "First 5 Elements")
    
    # Test a specific clash resolution
    if system.resolved_clashes:
        first_resolution = system.resolved_clashes[0]
        print(f"\n--- TESTING SPECIFIC RESOLUTION ---")
        print(f"Clash: {first_resolution.clash_id}")
        print(f"Moving element {first_resolution.move_element_id}")
        print(f"Original position: {first_resolution.original_position}")
        print(f"New position: {first_resolution.new_position}")
        print(f"Strategy: {first_resolution.strategy}")