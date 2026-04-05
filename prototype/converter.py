import os
import time

def convert_rvt_to_ifc(input_filepath, output_directory):
    """
    Mock function to simulate converting an RVT file to IFC.
    In a production application, this would call Autodesk Forge API
    or a local Revit add-in subprocess.

    Produces a valid minimal IFC4 file with mock MEP elements so
    ifcopenshell can parse it end-to-end for development & testing.
    """
    # Simulate processing delay
    time.sleep(3)

    filename = os.path.basename(input_filepath)
    base_name, _ = os.path.splitext(filename)
    output_filename = f"{base_name}.ifc"
    output_filepath = os.path.join(output_directory, output_filename)

    # Minimal valid IFC4 file with mock MEP elements (no inline comments - not valid in STEP)
    mock_ifc_content = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('{output_filename}','2024-04-05T00:00:00',('Mock Converter'),('Visionaries_Orchathon'),'IfcOpenShell','Mock App','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPERSON($,'Visionaries User',$,$,$,$,$,$);
#2=IFCORGANIZATION($,'Visionaries_Orchathon',$,$,$);
#3=IFCPERSONANDORGANIZATION(#1,#2,$);
#4=IFCAPPLICATION(#2,'1.0','Mock Converter','MockConv');
#5=IFCOWNERHISTORY(#3,#4,$,.ADDED.,$,$,$,0);
#6=IFCDIRECTION((1.,0.,0.));
#7=IFCDIRECTION((0.,0.,1.));
#8=IFCCARTESIANPOINT((0.,0.,0.));
#9=IFCAXIS2PLACEMENT3D(#8,#7,#6);
#10=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.0E-5,#9,$);
#11=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#12=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
#13=IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
#14=IFCUNITASSIGNMENT((#11,#12,#13));
#15=IFCPROJECT('0iAZKz9ETExupT0oBJjCpK',#5,'Mock MEP Project',$,$,$,$,(#10),#14);
#16=IFCCARTESIANPOINT((0.,0.,0.));
#17=IFCAXIS2PLACEMENT3D(#16,$,$);
#18=IFCLOCALPLACEMENT($,#17);
#19=IFCSITE('1iAZKz9ETExupT0oBJjCpK',#5,'Site',$,$,#18,$,$,.ELEMENT.,#16,$,$,$,$);
#20=IFCRELAGGREGATES('2iAZKz9ETExupT0oBJjCpK',#5,$,$,#15,(#19));
#21=IFCBUILDING('3iAZKz9ETExupT0oBJjCpK',#5,'Building A',$,$,#18,$,$,.ELEMENT.,$,$,$);
#22=IFCRELAGGREGATES('4iAZKz9ETExupT0oBJjCpK',#5,$,$,#19,(#21));
#23=IFCBUILDINGSTOREY('5iAZKz9ETExupT0oBJjCpK',#5,'Level 1',$,$,#18,$,$,.ELEMENT.,0.);
#24=IFCRELAGGREGATES('6iAZKz9ETExupT0oBJjCpK',#5,$,$,#21,(#23));
#30=IFCCARTESIANPOINT((5.0,5.0,3.0));
#31=IFCAXIS2PLACEMENT3D(#30,$,$);
#32=IFCLOCALPLACEMENT(#18,#31);
#33=IFCCARTESIANPOINT((5.2,5.0,3.0));
#34=IFCAXIS2PLACEMENT3D(#33,$,$);
#35=IFCLOCALPLACEMENT(#18,#34);
#36=IFCCARTESIANPOINT((5.0,5.0,3.1));
#37=IFCAXIS2PLACEMENT3D(#36,$,$);
#38=IFCLOCALPLACEMENT(#18,#37);
#39=IFCCARTESIANPOINT((2.0,8.0,4.0));
#40=IFCAXIS2PLACEMENT3D(#39,$,$);
#41=IFCLOCALPLACEMENT(#18,#40);
#42=IFCCARTESIANPOINT((9.0,9.0,3.5));
#43=IFCAXIS2PLACEMENT3D(#42,$,$);
#44=IFCLOCALPLACEMENT(#18,#43);
#50=IFCPIPESEGMENT('PipeSegA001',#5,'Hot Water Pipe - Main',$,'Domestic Hot Water',#32,$,$,.USERDEFINED.,$);
#51=IFCPIPESEGMENT('PipeSegB002',#5,'Cold Water Supply Pipe',$,'Cold Supply',#35,$,$,.USERDEFINED.,$);
#52=IFCDUCTSEGMENT('DuctSegC003',#5,'Supply Air Duct - Main',$,'HVAC Supply',#38,$,$,.USERDEFINED.,$);
#53=IFCFLOWTERMINAL('FlowTermD004',#5,'Air Diffuser - Ceiling',$,'HVAC Terminal',#41,$,$,$);
#54=IFCFLOWFITTING('FlowFitE005',#5,'Pipe Elbow 90-deg',$,'Pipe Fitting',#44,$,$,$);
#60=IFCPROPERTYSINGLEVALUE('NominalDiameter',$,IFCLENGTHMEASURE(0.1),$);
#61=IFCPROPERTYSINGLEVALUE('FlowRate',$,IFCVOLUMEMEASURE(0.002),$);
#62=IFCPROPERTYSINGLEVALUE('Material',$,IFCLABEL('Copper'),$);
#63=IFCPROPERTYSINGLEVALUE('Length',$,IFCLENGTHMEASURE(2.0),$);
#64=IFCPROPERTYSET('PSetPipeA001',#5,'Pset_PipeInformation',$,(#60,#61,#62,#63));
#65=IFCRELDEFINESBYPROPERTIES('RPSetPipeA001',#5,$,$,(#50),#64);
#66=IFCPROPERTYSINGLEVALUE('NominalDiameter',$,IFCLENGTHMEASURE(0.08),$);
#67=IFCPROPERTYSINGLEVALUE('FlowRate',$,IFCVOLUMEMEASURE(0.0015),$);
#68=IFCPROPERTYSINGLEVALUE('Material',$,IFCLABEL('PVC'),$);
#69=IFCPROPERTYSINGLEVALUE('Length',$,IFCLENGTHMEASURE(2.0),$);
#70=IFCPROPERTYSET('PSetPipeB002',#5,'Pset_PipeInformation',$,(#66,#67,#68,#69));
#71=IFCRELDEFINESBYPROPERTIES('RPSetPipeB002',#5,$,$,(#51),#70);
#72=IFCPROPERTYSINGLEVALUE('Width',$,IFCLENGTHMEASURE(0.4),$);
#73=IFCPROPERTYSINGLEVALUE('Height',$,IFCLENGTHMEASURE(0.3),$);
#74=IFCPROPERTYSINGLEVALUE('AirFlow',$,IFCVOLUMEMEASURE(0.5),$);
#75=IFCPROPERTYSINGLEVALUE('Length',$,IFCLENGTHMEASURE(2.0),$);
#76=IFCPROPERTYSET('PSetDuctC003',#5,'Pset_DuctInformation',$,(#72,#73,#74,#75));
#77=IFCRELDEFINESBYPROPERTIES('RPSetDuctC003',#5,$,$,(#52),#76);
#78=IFCPROPERTYSINGLEVALUE('DiffuserType',$,IFCLABEL('Square'),$);
#79=IFCPROPERTYSINGLEVALUE('NeckDiameter',$,IFCLENGTHMEASURE(0.15),$);
#80=IFCPROPERTYSET('PSetTermD004',#5,'Pset_AirTerminalInformation',$,(#78,#79));
#81=IFCRELDEFINESBYPROPERTIES('RPSetTermD004',#5,$,$,(#53),#80);
#82=IFCPROPERTYSINGLEVALUE('FittingType',$,IFCLABEL('Elbow-90'),$);
#83=IFCPROPERTYSINGLEVALUE('NominalDiameter',$,IFCLENGTHMEASURE(0.1),$);
#84=IFCPROPERTYSET('PSetFitE005',#5,'Pset_FittingInformation',$,(#82,#83));
#85=IFCRELDEFINESBYPROPERTIES('RPSetFitE005',#5,$,$,(#54),#84);
#90=IFCRELCONTAINEDINSPATIALSTRUCTURE('ContainMEP001',#5,$,$,(#50,#51,#52,#53,#54),#23);
ENDSEC;
END-ISO-10303-21;
"""

    with open(output_filepath, 'w') as f:
        f.write(mock_ifc_content)

    return output_filename
