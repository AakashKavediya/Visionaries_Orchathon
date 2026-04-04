<div align="center">

<!-- HERO BANNER -->
<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:04080f,50:0a1c35,100:00d4ff&height=200&section=header&text=MEP%20CLASH%20DETECTION&fontSize=38&fontColor=ffffff&fontAlignY=38&desc=AI-Assisted%20BIM%20Coordination%20Platform&descAlignY=58&descSize=16&descColor=00d4ff&animation=fadeIn" />

<br/>

<!-- TYPING ANIMATION -->
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=15&duration=3000&pause=1000&color=00D4FF&center=true&vCenter=true&multiline=true&width=700&height=60&lines=%F0%9F%94%8D+Detect+Clashes+%E2%80%A2+%F0%9F%94%81+Auto+Reroute+%E2%80%A2+%F0%9F%93%84+Generate+Reports+%E2%80%A2+%F0%9F%A7%A0+AI+Powered" alt="Typing Animation" />

<br/><br/>

<!-- BADGES ROW 1 -->
[![Stage](https://img.shields.io/badge/◉_STAGE_1-ACTIVE_DEVELOPMENT-00d4ff?style=for-the-badge&labelColor=0a1c35)](.)&nbsp;
[![Build](https://img.shields.io/badge/BUILD-PASSING-10ffb0?style=for-the-badge&logo=github-actions&logoColor=white&labelColor=0a1c35)](.)&nbsp;
[![AI](https://img.shields.io/badge/AI-INTEGRATION_PLANNED-a855f7?style=for-the-badge&logo=openai&logoColor=white&labelColor=0a1c35)](.)

<!-- BADGES ROW 2 -->
[![Input](https://img.shields.io/badge/INPUT-.RVT_REVIT_MODELS-ff6b35?style=for-the-badge&logo=autodesk&logoColor=white&labelColor=0a1c35)](.)&nbsp;
[![Python](https://img.shields.io/badge/PYTHON-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=0a1c35)](.)&nbsp;
[![License](https://img.shields.io/badge/LICENSE-MIT-ffffff?style=for-the-badge&labelColor=0a1c35)](.)

<br/>

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║    Resolving MEP conflicts before they reach the job site.       ║
║    Turning complex BIM coordination into automated intelligence. ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

</div>

<br/>

---

## 🧭 Navigation

<div align="center">

[📌 Overview](#-overview) &nbsp;·&nbsp; [⚠️ Problem](#%EF%B8%8F-the-problem) &nbsp;·&nbsp; [🔍 Clash Types](#-clash-types) &nbsp;·&nbsp; [⚙️ Architecture](#%EF%B8%8F-system-architecture) &nbsp;·&nbsp; [🧪 Roadmap](#-development-roadmap) &nbsp;·&nbsp; [🚀 Future](#-future-vision) &nbsp;·&nbsp; [👥 Team](#-the-team)

</div>

---

## 📌 Overview

<table>
<tr>
<td width="65%">

**MEP Clash Detection & Rerouting** is an AI-assisted BIM coordination platform that automatically detects and resolves conflicts in **Mechanical, Electrical, and Plumbing** systems — *before* they become expensive on-site mistakes.

Built for BIM coordinators and MEP engineers who demand **speed, precision, and automation** in their design workflows.

**Core capabilities:**
- 🔍 Automated clash detection across all MEP disciplines
- 🔁 Intelligent rerouting with constraint awareness
- 📄 Structured reports with clash location & severity
- 🧠 AI priority scoring *(planned)*

</td>
<td width="35%" align="center">

```
  ┌───────────────┐
  │   .rvt File   │
  │   BIM Model   │
  └──────┬────────┘
         │
         ▼
  ┌───────────────┐
  │    DETECT     │  ← Clash Engine
  └──────┬────────┘
         │
         ▼
  ┌───────────────┐
  │    REROUTE    │  ← AI Logic
  └──────┬────────┘
         │
         ▼
  ┌───────────────┐
  │    REPORT     │  ← Output
  └───────────────┘
```

</td>
</tr>
</table>

---

## ⚠️ The Problem

> In traditional MEP coordination, clashes are discovered **late** — often on the construction site — leading to costly rework, schedule delays, and design conflicts between disciplines.

<br/>

<div align="center">

| | Without This System | With This System |
|:---:|:---|:---|
| 🔴 | Manual clash detection in Revit / Navisworks | ✅ Automated detection in seconds |
| 🔴 | Hours of cross-discipline coordination | ✅ Instant multi-system analysis |
| 🔴 | Human error in complex MEP overlaps | ✅ Consistent, algorithmic accuracy |
| 🔴 | Expensive rework discovered on-site | ✅ Issues resolved at the design stage |
| 🔴 | No prioritization of critical clashes | ✅ AI-powered severity scoring *(planned)* |

</div>

---

## 🔍 Clash Types

<div align="center">

```
╔══════════════╦══════════════════╦══════════════╦══════════════════════════════════════════════╗
║   INDICATOR  ║   CLASH TYPE     ║   SEVERITY   ║   DESCRIPTION                                ║
╠══════════════╬══════════════════╬══════════════╬══════════════════════════════════════════════╣
║      🔴      ║  Pipe – Pipe     ║  HARD CLASH  ║  Physical overlap between plumbing pipes     ║
║      🟦      ║  Duct – Duct     ║  HARD CLASH  ║  Overlapping HVAC ductwork sections          ║
║      🟠      ║  Pipe – Duct     ║ INTER-SYSTEM ║  Cross-discipline: plumbing vs. mechanical   ║
║      🟡      ║  Cable Tray      ║  SOFT CLASH  ║  Electrical tray violates MEP clearances     ║
║      🟣      ║  Inter-System    ║   COMPLEX    ║  Multi-discipline conflicts across all MEP   ║
╚══════════════╩══════════════════╩══════════════╩══════════════════════════════════════════════╝
```

</div>

---

## ⚙️ System Architecture

```mermaid
flowchart TD
    A([📂 INPUT\n.rvt BIM File]) --> B

    subgraph ENGINE["⚙️ PROCESSING CORE"]
        direction TB
        B[🔍 Clash Detection Engine\nElement-pair intersection analysis]
        B --> C[📊 Clash Data Extraction\nType · Location · Component IDs · Coordinates]
        C --> D{🔁 Rerouting\nDecision Engine}
    end

    D -->|Simple Clash| E([⚡ STAGE 1\nBasic Offset / Elevation Shift])
    D -->|Complex Clash| F([🧠 STAGE 2\nConstraint-Aware Pathfinding])
    D -->|Critical Clash| G([🤖 AI COPILOT\nNatural Language Suggestions])

    E --> H[📄 Report Generator]
    F --> H
    G --> H

    H --> I([📥 OUTPUT\nClash Report + Rerouting Paths])

    style A fill:#0a1c35,stroke:#00d4ff,stroke-width:2px,color:#c8dff0
    style B fill:#0a1c35,stroke:#00d4ff,color:#c8dff0
    style C fill:#0a1c35,stroke:#00d4ff,color:#c8dff0
    style D fill:#0d2040,stroke:#ff6b35,stroke-width:2px,color:#ffffff
    style E fill:#0a1c35,stroke:#ff6b35,color:#c8dff0
    style F fill:#0a1c35,stroke:#a855f7,color:#c8dff0
    style G fill:#0a1c35,stroke:#a855f7,stroke-dasharray:5,color:#c8dff0
    style H fill:#0a1c35,stroke:#10ffb0,color:#c8dff0
    style I fill:#0a1c35,stroke:#10ffb0,stroke-width:2px,color:#c8dff0
    style ENGINE fill:#06111f,stroke:#00d4ff33,color:#607a94
```

---

## 📂 Input & Output

<table>
<tr>
<td width="50%">

### 📥 Input Specification

```yaml
# ─────────────────────────────────
#  ACCEPTED INPUT FORMAT
# ─────────────────────────────────

format:      .rvt  (Autodesk Revit BIM)
disciplines:
  - Mechanical   # HVAC, ductwork, AHUs
  - Electrical   # Cable trays, conduits
  - Plumbing     # Pipes, fittings, valves

metadata:
  - Coordinate reference system
  - Level & grid definitions
  - Element parameter data
```

</td>
<td width="50%">

### 📤 Output Specification

```yaml
# ─────────────────────────────────
#  GENERATED OUTPUT
# ─────────────────────────────────

clash_report:
  - clash_type: HARD | SOFT | INTER-SYSTEM
  - severity:   CRITICAL | MAJOR | MINOR
  - location:   { x, y, z } coordinates
  - components: [ element_id_A, element_id_B ]

rerouting:
  - suggested_path: offset / elevation shift
  - constraint_check: clearance & code pass
  - ai_priority_score: planned 🧠

export_formats:
  - Structured PDF report
  - HTML visual dashboard
```

</td>
</tr>
</table>

---

## 🧪 Development Roadmap

### 🟠 Stage 1 — Core Detection Engine &nbsp; `In Progress`

<div align="center">

```
Progress ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━░░░░░░░░░  80%
```

</div>

| Status | Task |
|:------:|:-----|
| ✅ | Parse and extract clash data from `.rvt` Revit models |
| ✅ | Detect and classify clash types — hard, soft, inter-system |
| ✅ | Output clash type, location (XYZ), and affected component IDs |
| ✅ | Apply basic offset/elevation-shift rerouting for simple clashes |
| 🔄 | Cover all simple clash scenario variations end-to-end |

<br/>

### 🟣 Stage 2 — Intelligent Rerouting Engine &nbsp; `Planned`

<div align="center">

```
Progress ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%
```

</div>

| Status | Task |
|:------:|:-----|
| ⬜ | Handle full-scale production BIM models (100,000+ elements) |
| ⬜ | Constraint-aware rerouting respecting codes, structure & clearances |
| ⬜ | Batch multi-clash optimization — resolve cascading conflicts |
| ⬜ | Minimize disruption to surrounding design elements |

---

## ⚠️ Engineering Challenges

<table>
<tr>
<td width="33%" align="center">

```
┌────────────────────┐
│  01  COMPLEXITY    │
└────────────────────┘
```

Revit models contain **deeply nested parametric relationships**. Robust parsing requires understanding the full Revit API object graph — families, instances, geometry, and constraints.

</td>
<td width="33%" align="center">

```
┌────────────────────┐
│  02  REROUTING     │
└────────────────────┘
```

Rerouted paths must comply with **building codes, structural limits, and MEP clearance standards** — not just avoid geometric overlap.

</td>
<td width="33%" align="center">

```
┌────────────────────┐
│  03  PERFORMANCE   │
└────────────────────┘
```

Real-world models exceed **100,000+ elements**. Clash detection must run at scale without sacrificing accuracy or introducing false positives.

</td>
</tr>
</table>

---

## 🚀 Future Vision

<div align="center">

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FUTURE ENHANCEMENT PIPELINE                         │
├───────────────────┬─────────────────────────────────────────────────────────┤
│  ⚡ REAL-TIME     │  Live clash detection as elements are placed in Revit    │
├───────────────────┼─────────────────────────────────────────────────────────┤
│  🤖 AUTO-RESOLVE  │  Zero-touch resolution for common clash patterns         │
├───────────────────┼─────────────────────────────────────────────────────────┤
│  🧠 AI COPILOT    │  Prompt-based MEP solutions from natural language input  │
├───────────────────┼─────────────────────────────────────────────────────────┤
│  📊 SMART SCORING │  AI scoring by severity, cost impact & schedule risk     │
├───────────────────┼─────────────────────────────────────────────────────────┤
│  🔗 NAVISWORKS    │  Native export to NWD / NWF clash test formats           │
├───────────────────┼─────────────────────────────────────────────────────────┤
│  ☁️ CLOUD COLLAB  │  Multi-user real-time coordination dashboard             │
└───────────────────┴─────────────────────────────────────────────────────────┘
```

</div>

---

## 👥 The Team

<div align="center">

<br/>

| &nbsp; | Name | Role | Focus Area |
|:------:|:-----|:-----|:-----------|
| 🔵 | **Karan Mishra** | Core Developer | Clash detection engine & Revit API integration |
| 🟠 | **Anup Mehta** | Systems Architect | System design, data pipeline & performance |
| 🟢 | **Aakash Kavediya** | BIM Specialist | MEP workflows, model validation & standards |
| 🟣 | **Shlok Khade** | AI Integration | Rerouting intelligence & AI prioritization |

<br/>

</div>

---

<div align="center">

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:00d4ff,50:0a1c35,100:04080f&height=120&section=footer&animation=fadeIn" />

```
  ◈  Practical  ·  Scalable  ·  Intelligent  ◈
```

*Designed to mirror real-world BIM coordination workflows —*
*from first clash detection to construction-ready resolution.*

<br/>

![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Revit API](https://img.shields.io/badge/-Revit%20API-ff6b35?style=flat-square&logo=autodesk&logoColor=white)
![BIM](https://img.shields.io/badge/-BIM%20Coordination-00d4ff?style=flat-square)
![MEP](https://img.shields.io/badge/-MEP%20Engineering-a855f7?style=flat-square)
![AI](https://img.shields.io/badge/-AI%20Powered-10ffb0?style=flat-square&logo=openai&logoColor=black)

</div>
