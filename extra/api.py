from Autodesk.Revit.DB import *
doc = __revit__.ActiveUIDocument.Document
from Autodesk.Revit.UI import TaskDialog

doc = __revit__.ActiveUIDocument.Document

collector = FilteredElementCollector(doc).OfClass(Wall)

count = len(list(collector))

TaskDialog.Show("Walls", "Total walls: {}".format(count))