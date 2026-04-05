from Autodesk.Revit.DB import *

app = __revit__.Application

file_path = r"C:\models\file.rvt"

doc = app.OpenDocumentFile(file_path)

options = IFCExportOptions()
options.FileVersion = IFCVersion.IFC4

doc.Export(r"C:\output", "file.ifc", options)

doc.Close(False)