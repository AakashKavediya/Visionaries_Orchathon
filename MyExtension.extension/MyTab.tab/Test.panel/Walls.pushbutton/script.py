# type: ignore
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog

doc = __revit__.ActiveUIDocument.Document

collector = FilteredElementCollector(doc).OfClass(Wall)
count = len(list(collector))

TaskDialog.Show("Walls", "Total walls: {}".format(count))