import argparse
import importlib.util
import os
import sys
from pathlib import Path


# 🔥 Default input path (your file)
DEFAULT_INPUT_PATH = r"C:\Users\Aakash Kavediya\Downloads\Revit_Model_For_Orchathon\Revit_Model_For_Orchathon\24118-UA-TA-H5-MDL-AR-000001.rvt"


def _is_revit_runtime() -> bool:
    return "__revit__" in globals()


def _run_revit_export(output_dir: str, filename: str, ifc_version: str) -> int:
    from Autodesk.Revit.DB import IFCExportOptions, IFCVersion  # type: ignore
    from Autodesk.Revit.UI import TaskDialog  # type: ignore

    doc = __revit__.ActiveUIDocument.Document  # type: ignore[name-defined]

    options = IFCExportOptions()
    options.FileVersion = IFCVersion.IFC4 if ifc_version.upper() == "IFC4" else IFCVersion.IFC2x3

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    success = doc.Export(output_dir, filename, options)

    if success:
        TaskDialog.Show("Success", f"IFC export completed: {os.path.join(output_dir, filename)}")
        return 0

    TaskDialog.Show("Error", "IFC export failed.")
    return 1


def _load_mock_converter():
    project_root = Path(__file__).resolve().parents[1]
    converter_path = project_root / "prototype" / "converter.py"

    if not converter_path.exists():
        raise FileNotFoundError(f"Mock converter not found at: {converter_path}")

    spec = importlib.util.spec_from_file_location("prototype_converter", converter_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load converter module from: {converter_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "convert_rvt_to_ifc"):
        raise AttributeError("prototype/converter.py does not define convert_rvt_to_ifc")

    return module.convert_rvt_to_ifc


def _run_cli_mock_conversion(input_file: str, output_dir: str) -> int:
    convert_rvt_to_ifc = _load_mock_converter()

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    out_name = convert_rvt_to_ifc(input_file, output_dir)
    out_path = str(Path(output_dir) / out_name)

    print("Revit API not available in this Python runtime.")
    print("Used project mock converter instead.")
    print(f"Generated IFC: {out_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="RVT to IFC conversion utility")

    # 👇 Default path applied here
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_PATH,
        help="Path to .rvt file"
    )

    parser.add_argument(
        "--output-dir",
        default=str(Path("converted_ifc").resolve()),
        help="Output directory"
    )

    parser.add_argument(
        "--filename",
        default="output.ifc",
        help="Output IFC filename (Revit runtime mode)"
    )

    parser.add_argument(
        "--ifc-version",
        default="IFC4",
        choices=["IFC4", "IFC2x3"],
        help="IFC schema version for Revit runtime mode"
    )

    args = parser.parse_args()

    # 🔥 Revit mode
    if _is_revit_runtime():
        try:
            return _run_revit_export(args.output_dir, args.filename, args.ifc_version)
        except Exception as exc:
            print(f"Revit export failed: {exc}")
            return 1

    # 🔥 Normal Python mode (now uses default path)
    try:
        return _run_cli_mock_conversion(args.input, args.output_dir)
    except Exception as exc:
        print(f"Mock conversion failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())