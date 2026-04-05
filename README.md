# ⚙️ BIMFlow

### *The open-source BIM processing pipeline that bridges Revit files and structured data*

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![IfcOpenShell](https://img.shields.io/badge/IfcOpenShell-0.7.x-FF6B35?style=flat-square)](https://ifcopenshell.org)
[![IFC](https://img.shields.io/badge/Format-IFC%204-009688?style=flat-square)](https://www.buildingsmart.org/standards/bsi-standards/industry-foundation-classes/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](CONTRIBUTING.md)

> BIMFlow is a full-stack BIM data processing pipeline that accepts Revit `.rvt` files, converts them to the open `.ifc` standard, parses MEP (Mechanical, Electrical, Plumbing) elements, and exposes them as structured JSON via REST APIs — making BIM data programmatically accessible for the first time.

---

## 📸 Preview

> *(Replace placeholders below with actual screenshots or a GIF demo)*

| Upload Interface | MEP Data View |
|:---:|:---:|
| ![Upload UI](docs/screenshots/upload.png) | ![MEP Data](docs/screenshots/mep_data.png) |

```
[ GIF Demo Placeholder ]
docs/demo/bimflow_demo.gif
```

---

## ✨ Features

### 📂 File Handling
- Drag-and-drop `.rvt` file upload via browser
- Server-side file validation and secure storage
- Automatic filename sanitization and collision prevention
- Uploaded files persisted under `/uploads`

### 🔄 Conversion Pipeline
- `.rvt` → `.ifc` conversion endpoint (mocked; architected for Revit API)
- Pluggable converter interface — swap mock with real implementation in one place
- Converted IFC files stored in structured `/converted_ifc` directory
- Conversion status returned synchronously via JSON response

### 🔍 Data Extraction
- Full IFC file parsing powered by [IfcOpenShell](https://ifcopenshell.org)
- Targeted MEP element extraction by IFC class
- Attribute normalization across heterogeneous BIM models
- Clean JSON output for every extracted element

### 🌐 API System
- RESTful endpoints for conversion, download, and MEP data retrieval
- Consistent JSON response schema with error handling
- Filename-based routing — no database required
- Designed for easy integration with frontend frameworks or external tools

### 🖥️ Frontend Visualization
- Lightweight HTML/CSS/JS frontend (no build step required)
- Dynamic rendering of MEP element tables from API data
- File upload form with conversion trigger
- Structured display of element attributes per category

---

## 🏗️ System Architecture

BIMFlow follows a linear processing pipeline from upload to UI render:

```
┌──────────────┐
│   Browser    │  User uploads .rvt file
└──────┬───────┘
       │ POST /api/convert
       ▼
┌──────────────────────┐
│   Flask Web Server   │  Receives file, validates format
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│   Conversion Layer   │  .rvt → .ifc
│   (Mock / Real API)  │  Stores result in /converted_ifc
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│   IfcOpenShell       │  Opens .ifc file
│   Parsing Engine     │  Iterates all IFC entities
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│   MEP Extractor      │  Filters MEP IFC classes
│                      │  Extracts + normalizes attributes
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│   JSON Transformer   │  Builds structured response payload
└──────┬───────────────┘
       │ GET /api/mep-data/<filename>
       ▼
┌──────────────────────┐
│   REST API Layer     │  Serves JSON to client
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│   Frontend UI        │  Renders MEP elements in browser
└──────────────────────┘
```

**Pipeline Summary:**

| Stage | Input | Output | Tool |
|---|---|---|---|
| Upload | `.rvt` file | Saved to `/uploads` | Flask |
| Convert | `.rvt` path | `.ifc` in `/converted_ifc` | Mock / Revit API |
| Parse | `.ifc` file | IFC entity objects | IfcOpenShell |
| Extract | IFC entities | MEP element dicts | Custom extractor |
| Serve | MEP dicts | JSON response | Flask REST |
| Render | JSON payload | UI table | Vanilla JS |

---

## ⚙️ Tech Stack

### Backend
| Technology | Role |
|---|---|
| Python 3.9+ | Core language |
| Flask 2.x | Web framework and API server |
| Werkzeug | File handling, request utilities |

### Parsing Engine
| Technology | Role |
|---|---|
| IfcOpenShell 0.7.x | IFC file parsing and entity iteration |
| IFC4 Standard | Data format for BIM interoperability |

### Frontend
| Technology | Role |
|---|---|
| HTML5 / CSS3 | Page structure and styling |
| Vanilla JavaScript | Dynamic API calls and DOM rendering |
| Jinja2 | Server-side HTML templating (Flask) |

### Future Integrations *(Roadmap)*
| Technology | Purpose |
|---|---|
| Revit API (pyRevit) | Real `.rvt` → `.ifc` conversion |
| Autodesk Forge / APS | Cloud-based model processing |
| Three.js | 3D geometry visualization |
| Open3D / NumPy | Geometry processing |
| Socket.IO | Real-time collaboration |

---

## 📁 Project Structure

```
bimflow/
│
├── app.py                    # Flask application entry point
├── converter.py              # RVT → IFC conversion logic (mock/real)
├── ifc_parser.py             # IfcOpenShell parsing + MEP extraction
├── requirements.txt          # Python dependencies
│
├── uploads/                  # Incoming .rvt files from UI upload
│   └── .gitkeep
│
├── converted_ifc/            # Converted .ifc files (post-processing)
│   └── .gitkeep
│
├── outputs/                  # Reserved for processed outputs / reports
│   └── .gitkeep
│
├── templates/                # Jinja2 HTML templates (Flask)
│   └── index.html            # Main frontend page
│
├── static/                   # Static assets served by Flask
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js           # Frontend API calls + DOM rendering
│
└── docs/                     # Documentation assets
    ├── screenshots/
    └── demo/
```

---

## 🔌 API Documentation

### `POST /api/convert`

**Description:** Accepts a `.rvt` file upload, runs it through the conversion pipeline, and returns the path to the generated `.ifc` file.

**Request:**
```
Content-Type: multipart/form-data
Body: file=<revit_file.rvt>
```

**Response:**
```json
{
  "success": true,
  "message": "File converted successfully",
  "ifc_file": "converted_ifc/sample_model.ifc",
  "filename": "sample_model.ifc"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid file format. Only .rvt files are accepted."
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:5000/api/convert \
  -F "file=@/path/to/model.rvt"
```

---

### `GET /download/<filename>`

**Description:** Downloads a previously converted `.ifc` file by filename.

**URL Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `filename` | string | Name of the `.ifc` file in `/converted_ifc` |

**Response:** Binary file download (`application/octet-stream`)

**Example:**
```
GET /download/sample_model.ifc
```

**cURL:**
```bash
curl -OJ http://localhost:5000/download/sample_model.ifc
```

---

### `GET /api/mep-data/<filename>`

**Description:** Parses a stored `.ifc` file and returns all extracted MEP elements as structured JSON.

**URL Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `filename` | string | Name of the `.ifc` file in `/converted_ifc` |

**Response:**
```json
{
  "success": true,
  "filename": "sample_model.ifc",
  "total_elements": 42,
  "mep_data": {
    "IfcPipeSegment": [
      {
        "id": "1HvX8zK1T6uBkQaF8...",
        "name": "Pipe Segment:150mm",
        "type": "IfcPipeSegment",
        "attributes": {
          "NominalDiameter": 150,
          "FlowDirection": "SOURCE",
          "SystemType": "SupplyHydronics"
        }
      }
    ],
    "IfcDuctSegment": [...],
    "IfcCableCarrierSegment": [...]
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "File not found: nonexistent.ifc"
}
```

**cURL:**
```bash
curl http://localhost:5000/api/mep-data/sample_model.ifc
```

---

## 🧾 MEP Data Extraction

### What are MEP Elements?

MEP stands for **Mechanical, Electrical, and Plumbing** — the three major building systems that keep a structure functional:

- **Mechanical:** HVAC, ventilation ducts, air handling equipment
- **Electrical:** Cable trays, conduit, lighting fixtures, switchgear
- **Plumbing:** Pipes, valves, fittings, water distribution networks

In a BIM model, these are represented as distinct IFC (Industry Foundation Classes) entities with rich attribute data.

### Extracted IFC Classes

| IFC Class | Category | Description |
|---|---|---|
| `IfcPipeSegment` | Plumbing | Straight pipe runs |
| `IfcPipeFitting` | Plumbing | Elbows, tees, reducers |
| `IfcValve` | Plumbing | Flow control valves |
| `IfcDuctSegment` | Mechanical | Straight duct runs |
| `IfcDuctFitting` | Mechanical | Duct transitions and bends |
| `IfcAirTerminal` | Mechanical | Grilles, diffusers, registers |
| `IfcCableCarrierSegment` | Electrical | Cable trays and conduit |
| `IfcCableSegment` | Electrical | Individual cables |
| `IfcFlowTerminal` | Electrical | Light fixtures, outlets |
| `IfcPump` | Mechanical | Pumping equipment |
| `IfcFan` | Mechanical | Fan units |

### Sample JSON Response

```json
{
  "success": true,
  "filename": "office_building.ifc",
  "total_elements": 187,
  "mep_data": {
    "IfcPipeSegment": [
      {
        "id": "2O2Fr$t4X7Zf8glImU4Uxe",
        "name": "Pipe - Domestic Cold Water : 25mm",
        "type": "IfcPipeSegment",
        "attributes": {
          "NominalDiameter": 25,
          "SystemType": "DomesticColdWater",
          "FlowDirection": "SOURCE",
          "Length": 2400.0
        }
      }
    ],
    "IfcDuctSegment": [
      {
        "id": "3KLp9mN2Y8Qf7abJnV5Wqr",
        "name": "Rectangular Duct : 400x200mm",
        "type": "IfcDuctSegment",
        "attributes": {
          "Width": 400,
          "Height": 200,
          "SystemType": "SupplyAir",
          "AirFlowRate": 0.85
        }
      }
    ]
  }
}
```

### Field Reference

| Field | Type | Description |
|---|---|---|
| `id` | string | Globally unique IFC GUID |
| `name` | string | Human-readable element name from BIM model |
| `type` | string | IFC class name (e.g., `IfcPipeSegment`) |
| `attributes` | object | Key-value pairs of IFC property set values |

---

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.9 or higher
- pip
- Git
- *(Optional)* A sample `.ifc` file for testing

### Step 1 — Clone the Repository

```bash
git clone https://github.com/yourusername/bimflow.git
cd bimflow
```

### Step 2 — Create a Virtual Environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

**Key dependencies:**
```
Flask==2.3.x
ifcopenshell==0.7.x
Werkzeug==2.3.x
```

### Step 4 — Create Required Directories

```bash
mkdir -p uploads converted_ifc outputs
```

### Step 5 — Run the Server

```bash
python app.py
```

The server starts at: **http://localhost:5000**

### Step 6 — Access the Frontend

Open your browser and navigate to:
```
http://localhost:5000
```

You should see the BIMFlow upload interface.

---

## 🔬 How It Works Internally

### Mock Conversion vs Real Conversion

The conversion layer (`converter.py`) is intentionally abstracted:

```python
def convert_rvt_to_ifc(rvt_path: str, output_dir: str) -> str:
    """
    Current: Copies file with .ifc extension (mock).
    Production: Call Revit API / IFC exporter here.
    """
    # Mock implementation
    ifc_filename = Path(rvt_path).stem + ".ifc"
    ifc_path = Path(output_dir) / ifc_filename
    shutil.copy(rvt_path, ifc_path)
    return str(ifc_path)
```

To plug in a real converter (e.g., pyRevit or Forge), replace only this function. The rest of the pipeline is agnostic to how the `.ifc` was produced.

### Role of IfcOpenShell

IfcOpenShell is the industry-standard open-source library for reading and writing IFC files. BIMFlow uses it to:

1. **Open** an `.ifc` file: `model = ifcopenshell.open(ifc_path)`
2. **Iterate** all entities by type: `model.by_type("IfcPipeSegment")`
3. **Read** entity attributes: `element.NominalDiameter`, `element.GlobalId`
4. **Access** property sets via IfcOpenShell's pset API

### Data Transformation Logic

```python
MEP_CLASSES = [
    "IfcPipeSegment", "IfcPipeFitting", "IfcValve",
    "IfcDuctSegment", "IfcDuctFitting", "IfcAirTerminal",
    "IfcCableCarrierSegment", "IfcCableSegment",
    "IfcFlowTerminal", "IfcPump", "IfcFan"
]

def extract_mep_elements(ifc_path):
    model = ifcopenshell.open(ifc_path)
    results = {}

    for ifc_class in MEP_CLASSES:
        elements = model.by_type(ifc_class)
        if elements:
            results[ifc_class] = [
                {
                    "id": el.GlobalId,
                    "name": el.Name or "Unnamed",
                    "type": ifc_class,
                    "attributes": get_psets(el)
                }
                for el in elements
            ]

    return results
```

### Backend Request Flow

```
Request  →  Flask Router  →  Validate Input
                          →  Call Converter (mock/real)
                          →  Invoke IfcOpenShell Parser
                          →  Run MEP Extractor
                          →  Serialize to JSON
                          →  Return HTTP Response
```

---

## 🚧 Known Limitations

> Transparency matters. Here's what BIMFlow does and does not do today:

| Limitation | Detail |
|---|---|
| **Mock Conversion** | The `.rvt` → `.ifc` conversion does not actually process Revit files. It renames/copies the file. Real conversion requires Revit installed or Autodesk APIs. |
| **No Geometry Extraction** | Only non-geometric attributes (names, IDs, property sets) are extracted. 3D coordinates and solid geometry are not parsed. |
| **No Authentication** | The API has no access control. Not suitable for production without adding auth middleware. |
| **Single-threaded** | Flask's development server is single-threaded. Heavy IFC files may block the server. Use Gunicorn for production. |
| **No Persistent Storage** | No database. Data is derived on-demand from files on disk. |
| **IFC Validity Assumed** | No schema validation is performed on uploaded IFC files. |

---

## 🔮 Future Roadmap

### Near-Term
- [ ] **Real RVT → IFC Conversion** via pyRevit or Dynamo script integration
- [ ] **IFC Schema Validation** using IfcOpenShell's validation module
- [ ] **Async Processing Queue** (Celery + Redis) for large file handling
- [ ] **Progress Indicator** via WebSocket for long conversions

### Mid-Term
- [ ] **Autodesk Forge / APS Integration** for cloud-based model derivative extraction
- [ ] **3D Visualization** using Three.js + IFCLoader for in-browser model viewing
- [ ] **Property Set Browser** — explore all psets, not just MEP
- [ ] **Export to CSV / Excel** for MEP element schedules

### Long-Term
- [ ] **Clash Detection Engine** — AABB (Axis-Aligned Bounding Box) based MEP clash detection
- [ ] **AI/ML BIM Analysis** — anomaly detection, missing element classification, smart tagging
- [ ] **Real-Time Collaboration** via Socket.IO — multi-user model review sessions
- [ ] **Digital Twin Integration** — connect BIM elements to live sensor / IoT data streams
- [ ] **Plugin Architecture** — extensible extractor plugins for custom IFC workflows

---

## 🧪 Example Workflow

Here is a complete end-to-end walkthrough using the BIMFlow interface and API:

**Step 1 — Upload the Revit File**
```
Open http://localhost:5000
Select your .rvt file using the upload form
Click "Convert"
```

**Step 2 — Conversion Response**
```json
POST /api/convert
→ {
    "success": true,
    "filename": "mechanical_floor_3.ifc"
  }
```

**Step 3 — Fetch MEP Data**
```bash
curl http://localhost:5000/api/mep-data/mechanical_floor_3.ifc
```

**Step 4 — View Response**
```json
{
  "total_elements": 63,
  "mep_data": {
    "IfcDuctSegment": [ ... 14 elements ... ],
    "IfcPipeSegment": [ ... 31 elements ... ],
    "IfcValve":       [ ... 18 elements ... ]
  }
}
```

**Step 5 — Frontend Display**

The UI automatically calls `/api/mep-data/<filename>` and renders a categorized table of all extracted MEP elements with their attributes.

---

## 🤝 Contributing

Contributions are welcome! BIMFlow is designed with contribution-friendliness in mind.

### Getting Started

```bash
# Fork the repo, then:
git clone https://github.com/YOUR_USERNAME/bimflow.git
cd bimflow
git checkout -b feature/your-feature-name
```

### Code Structure Expectations

- **`converter.py`** — Add real conversion logic here. Keep interface identical: `convert_rvt_to_ifc(rvt_path, output_dir) → str`
- **`ifc_parser.py`** — Add new IFC class extractors by extending `MEP_CLASSES` and the attribute mapping
- **`app.py`** — Keep routes thin. Business logic belongs in dedicated modules
- **Tests** — Add tests under `/tests` using `pytest`. Each extractor function should have unit tests with sample `.ifc` fixture files

### What We Need

| Area | Examples |
|---|---|
| Conversion | Real pyRevit / Forge integration |
| Parsing | Additional IFC classes, geometry extraction |
| Frontend | Better visualization, charts, 3D viewer |
| Testing | Unit tests, integration tests, fixture IFC files |
| Docs | Better diagrams, video walkthroughs |

### Submitting Changes

```bash
git add .
git commit -m "feat: add IfcFlowController extraction support"
git push origin feature/your-feature-name
# Open a Pull Request on GitHub
```

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 BIMFlow Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software...
```

---

<div align="center">

**Built with ❤️ for the AEC (Architecture, Engineering, Construction) tech community**

*Making BIM data open, accessible, and programmable.*

[⭐ Star this repo](https://github.com/yourusername/bimflow) · [🐛 Report a Bug](https://github.com/yourusername/bimflow/issues) · [💡 Request a Feature](https://github.com/yourusername/bimflow/issues)

<<<<<<< HEAD
</div>
=======
</div>
>>>>>>> 8881cb116574f87e9a933534a7273bf3634114d7
