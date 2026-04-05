# 👁️ Visionaries Orchathon: BIM Clash Detection & Resolution

### *An end-to-end pipeline for identifying, visualizing, and resolving clashes in BIM models.*

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14.x-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)
[![IfcOpenShell](https://img.shields.io/badge/IfcOpenShell-0.7.x-FF6B35?style=flat-square)](https://ifcopenshell.org)
[![IFC](https://img.shields.io/badge/Format-IFC-009688?style=flat-square)](https://www.buildingsmart.org/standards/bsi-standards/industry-foundation-classes/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

> This project is a comprehensive solution for BIM (Building Information Modeling) analysis. It processes `.ifc` files to detect clashes (interferences) between architectural and MEP (Mechanical, Electrical, Plumbing) elements, extracts detailed data, and presents it in a user-friendly web interface to help in resolving the identified issues.

---

## ✨ Features

### 🔍 Core Processing
- **IFC Parsing:** In-depth parsing of `.ifc` files using IfcOpenShell to access the complete model hierarchy.
- **Clash Detection:** A sophisticated engine to identify geometric clashes between different elements in the BIM model.
- **Data Extraction:** Extracts properties and geometry for all elements, with a special focus on MEP components.
- **JSON Output:** Processed data, including clash results and element details, is serialized into structured JSON files for easy consumption.

### 🖥️ Web Interface (BIM Fixer)
- **Clash Visualization:** A modern web application built with Next.js to display clash results in an interactive and understandable format.
- **Data Filtering and Sorting:** Allows users to filter and sort clashes and element data to focus on critical issues.
- **3D Model Interaction (Future):** The groundwork is laid for future integration of a 3D viewer to visualize clashes directly in the model.

### ⚙️ API & Integration
- **Flask Backend:** A Python-based backend provides the processing power and serves the data to the frontend.
- **RESTful API:** A simple API to trigger processing and fetch results.
- **Modular Design:** The frontend and backend are decoupled, allowing for independent development and deployment.

---

## 🏗️ System Architecture

The project follows a clear data flow from the raw BIM file to the user interface:

```mermaid
graph TD
    A[Input IFC File (.ifc)] --> B{Python Backend};
    B -- Processes --> C[Output JSON Files];
    C -- Serves Data --> D{Next.js Frontend};

    subgraph B [Python Backend (Flask, IfcOpenShell)]
        direction LR
        B1(Parse IFC) --> B2(Detect Clashes);
        B2 --> B3(Extract Data);
    end

    subgraph C [Output JSON]
        C1(clash_results.json)
        C2(element_data.json)
    end

    subgraph D [BIM Fixer Frontend]
        D1(Fetch JSON Data) --> D2(Display Clashes);
        D2 --> D3(User Interaction);
    end
```

---

## 🛠️ Tech Stack

| Category | Technology | Role |
|---|---|---|
| **Backend** | Python, Flask | Core logic, API server |
| **BIM Processing** | IfcOpenShell | Parsing and analyzing `.ifc` files |
| **Frontend** | Next.js, React | User interface and data visualization |
| **Data Format** | JSON | Data interchange between backend and frontend |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+ and Node.js 18+
- A sample `.ifc` file for testing.

### 1. Backend Setup
```bash
# Navigate to the prototype directory
cd prototype

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install Python dependencies
pip install -r requirements.txt

# Run the backend server
python app.py
```
The backend will be running at `http://localhost:5000`.

### 2. Frontend Setup
```bash
# Navigate to the frontend directory
cd bim_fixer

# Install Node.js dependencies
npm install

# Run the development server
npm run dev
```
The frontend will be available at `http://localhost:3000`.

---

## 📁 Project Structure
```
.
├── bim_fixer/              # Next.js Frontend
│   ├── app/
│   └── package.json
├── prototype/              # Python Backend
│   ├── app.py
│   └── requirements.txt
├── output/                 # Generated JSON data
│   ├── clash_full_data.json
│   └── ifc_full_data.json
├── stages/                 # Processing scripts and sample files
│   └── RVT_Model_MEP_for_Orkathon.ifc
└── README.md
```

---

## 🔮 Future Roadmap

- [ ] **3D Clash Visualization:** Integrate a 3D viewer (like Three.js or Cesium) to show clashes in the context of the model.
- [ ] **Automated Resolution Suggestions:** Use AI to suggest possible solutions for common clash types.
- [ ] **Real-time Collaboration:** Allow multiple users to view and comment on clash results simultaneously.
- [ ] **Reporting:** Generate PDF or HTML reports of the clash analysis.

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

<div align="center">

**Built with ❤️ for the Visionaries Orchathon**

</div>
