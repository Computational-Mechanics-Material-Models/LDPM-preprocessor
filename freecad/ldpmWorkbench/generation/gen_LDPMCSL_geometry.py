## ===========================================================================
## LDPM WORKBENCH:github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor
##
## Copyright (c) 2023 
## All rights reserved. 
##
## Use of this source code is governed by a BSD-style license that can be
## found in the LICENSE file at the top level of the distribution and at
## github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
##
## ===========================================================================
## Developed by Northwestern University
## For U.S. Army ERDC Contract No. W9132T22C0015
## Primary Authors: Matthew Troemner
## ===========================================================================
##
## This function creates a 3D geometric shape using dimensions and parameters 
## passed to it. The function supports several different shapes including 
## boxes, cylinders, cones, spheres, ellipsoids, arbitrary prisms, and notched 
## prisms of square, semi-circle, and semi-ellipse shapes. The 'Dogbone' 
## option creates a special 3D dogbone shape using specific dimensions passed 
## to the function.
##
## ===========================================================================

# pyright: reportMissingImports=false
import os
import re
import math

from freecad.ldpmWorkbench.input.read_LDPMCSL_inputs import file_extension, is_cad_geometry_file

import FreeCAD as App
import ImportGui
import Fem
import JoinFeatures
import BOPTools.JoinFeatures
import Part
import Sketcher
from FreeCAD import Base

try:
    import importDXF
except ImportError:
    try:
        from draftlibs import importDXF
    except ImportError:
        importDXF = None


def gen_LDPMCSL_geometry(dimensions,geoType,geoName,cadFile):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - dimensions: List of dimensions for the geometry
    - geoType: Type of geometry to be created
    - geoName: Name of the geometry
    - cadFile: Path to the CAD or mesh file to be imported
    --------------------------------------------------------------------------
    ### Outputs ###
    - geo: Geometry object
    --------------------------------------------------------------------------
    """  


    # Check if dimensions are positive (ignore geometries we cannot check)
    if geoType not in ['Ellipsoid', 'Dogbone', 'Custom', 'Import CAD', 'Import CAD or Mesh', 'Sweep-3DP']:
        if all(float(i.strip(" mm")) > 0 for i in dimensions):
            pass
        else:
            raise Exception("One or more geometry dimensions are less than or equal to zero. Please revise.")




    if geoType == "Box":

        # Create a box and name it
        geo           = App.ActiveDocument.addObject("Part::Box",geoName)
        geo.Label     = geoName
        geo.Height    = dimensions[0]
        geo.Width     = dimensions[1]
        geo.Length    = dimensions[2]


    if geoType == "Cylinder":

        # Create a cylinder and name it
        geo           = App.ActiveDocument.addObject("Part::Cylinder",geoName)
        geo.Label     = geoName
        geo.Height    = dimensions[0]
        geo.Radius    = dimensions[1]


    if geoType == "Truncated Cone":

        # Create a cone and name it
        geo           = App.ActiveDocument.addObject("Part::Cone",geoName)
        geo.Label     = geoName
        geo.Height    = dimensions[0]
        geo.Radius1   = dimensions[1]
        geo.Radius2   = dimensions[2]

    if geoType == "Cone":

        # Create a cone and name it
        geo           = App.ActiveDocument.addObject("Part::Cone",geoName)
        geo.Label     = geoName
        geo.Height    = dimensions[0]
        geo.Radius1   = dimensions[1]
        geo.Radius2   = dimensions[2]

    if geoType == "Sphere":

        # Create a sphere and name it
        geo           = App.ActiveDocument.addObject("Part::Sphere",geoName)
        geo.Label     = geoName
        geo.Radius    = dimensions[0]

    if geoType == "Ellipsoid":

        # Create an ellipsoid and name it
        geo           = App.ActiveDocument.addObject("Part::Ellipsoid",geoName)
        geo.Label     = geoName
        geo.Radius1   = dimensions[0]
        geo.Radius2   = dimensions[1]
        geo.Radius3   = dimensions[2]
        geo.Angle1    = dimensions[3]
        geo.Angle2    = dimensions[4]
        geo.Angle3    = dimensions[5]

    if geoType == "Arbitrary Prism":

        # Create a prism and name it
        geo           = App.ActiveDocument.addObject("Part::Prism",geoName)
        geo.Label     = geoName
        geo.Circumradius = dimensions[0]
        geo.Height    = dimensions[1]
        geo.Polygon   = int(dimensions[2])

    if geoType == "Notched Prism - Square":

        # Create a notched prism and name it
        geo           = App.ActiveDocument.addObject("Part::Box",geoName+"Box")
        geo.Length    = dimensions[0]
        geo.Width     = dimensions[1]
        geo.Height    = dimensions[2]
        geo.Placement = App.Placement(App.Vector(0.00,0.00,0.00),App.Rotation(App.Vector(0.00,0.00,1.00),0.00))
        geo.Label     = geoName+'Box'

        # Create the notch
        geo           = App.ActiveDocument.addObject("Part::Box",geoName+"Notch")
        geo.Length    = dimensions[3]    # Notch Width
        geo.Width     = dimensions[1]    # Box width
        geo.Height    = dimensions[4]    # Notch Depth
        geo.Placement = App.Placement(App.Vector(0.00, 0.00, 0.00), App.Rotation(App.Vector(0.00, 0.00, 1.00), 0.00))
        geo.Label     = geoName + 'Notch'
        App.getDocument(App.ActiveDocument.Name).getObject(geoName+'Notch').Placement = App.Placement(App.Vector((float(dimensions[0].strip(" mm"))/2-float(dimensions[3].strip(" mm"))/2),0.00,0.00),App.Rotation(App.Vector(0.00,0.00,1.00),0.00))

        # Cut out the notch
        j = BOPTools.JoinFeatures.makeCutout(name=geoName)
        j.Base = App.ActiveDocument.getObject(geoName+'Box')
        j.Tool = App.ActiveDocument.getObject(geoName+'Notch')
        j.Proxy.execute(j)
        j.purgeTouched()
        for obj in j.ViewObject.Proxy.claimChildren():
            obj.ViewObject.hide()

        geo = App.ActiveDocument.getObject(geoName)

    if geoType == "Notched Prism - Semi Circle":

        # Create a notched prism and name it
        geo            = App.ActiveDocument.addObject("Part::Box",geoName+"Box")
        geo.Length     = dimensions[0]
        geo.Width      = dimensions[1]
        geo.Height     = dimensions[2]
        geo.Placement  = App.Placement(App.Vector(0.00,0.00,0.00),App.Rotation(App.Vector(0.00,0.00,1.00),0.00))
        geo.Label      = geoName+'Box'

        geo            = App.ActiveDocument.addObject("Part::Box",geoName+"BoxNotch")
        geo.Length     = dimensions[3] # BoxNotch Width
        geo.Width      = dimensions[1]
        geo.Height     = dimensions[4] # BoxNotch Depth
        geo.Placement  = App.Placement(App.Vector(float(dimensions[0].strip(" mm"))/2-float(dimensions[3].strip(" mm"))/2,0.00,0.00),App.Rotation(App.Vector(0.00,0.00,1.00),0.00))
        geo.Label      = geoName+'BoxNotch'

        geo            = App.ActiveDocument.addObject("Part::Cylinder",geoName+"CylinderNotch")
        geo.Radius     = float(dimensions[3].strip(" mm"))/2
        geo.Height     = float(dimensions[1].strip(" mm"))
        geo.Angle      = 360.00
        geo.FirstAngle = 0.00
        geo.SecondAngle= 0.00
        geo.Placement  = App.Placement(App.Vector(float(dimensions[0].strip(" mm"))/2,0.00,float(dimensions[4].strip(" mm"))),App.Rotation(App.Vector(1.00,0.00,0.00),-90.00))
        geo.Label      = geoName+'CylinderNotch'

        j = BOPTools.JoinFeatures.makeConnect(name=geoName+'Connect')
        j.Objects = [App.ActiveDocument.getObject(geoName+'BoxNotch'), App.ActiveDocument.getObject(geoName+'CylinderNotch')]
        j.Proxy.execute(j)
        j.purgeTouched()
        for obj in j.ViewObject.Proxy.claimChildren():
            obj.ViewObject.hide()

        j = BOPTools.JoinFeatures.makeCutout(name=geoName)
        j.Base = App.ActiveDocument.getObject(geoName+'Box')
        j.Tool = App.ActiveDocument.getObject(geoName+'Connect')
        j.Proxy.execute(j)
        j.purgeTouched()
        for obj in j.ViewObject.Proxy.claimChildren():
            obj.ViewObject.hide()

        geo = App.ActiveDocument.getObject(geoName)

    if geoType == "Notched Prism - Semi Ellipse":

        # Create a notched prism and name it
        geo            = App.ActiveDocument.addObject("Part::Box",geoName+"Box")
        geo.Length     = dimensions[0]
        geo.Width      = dimensions[1]
        geo.Height     = dimensions[2]
        geo.Placement  = App.Placement(App.Vector(0.00,0.00,0.00),App.Rotation(App.Vector(0.00,0.00,1.00),0.00))
        geo.Label      = geoName+'Box'

        geo            = App.ActiveDocument.addObject("Part::Box",geoName+"BoxNotch")
        geo.Length     = dimensions[3] # BoxNotch Width
        geo.Width      = dimensions[1]
        geo.Height     = dimensions[4] # BoxNotch Depth
        geo.Placement  = App.Placement(App.Vector(float(dimensions[0].strip(" mm"))/2-float(dimensions[3].strip(" mm"))/2,0.00,0.00),App.Rotation(App.Vector(0.00,0.00,1.00),0.00))
        geo.Label      = geoName+'BoxNotch'

        if float(dimensions[5].strip(" mm")) > float(dimensions[3].strip(" mm"))/2:
            geo        = App.ActiveDocument.addObject("Part::Ellipse",geoName+"Ellipse")
            geo.MajorRadius = float(dimensions[5].strip(" mm"))
            geo.MinorRadius = float(dimensions[3].strip(" mm"))/2
            geo.Angle1 = 0.00
            geo.Angle2 = 360.00
            geo.Placement = App.Placement(App.Vector(0.00,0.00,0.00),App.Rotation(App.Vector(1.00,0.00,0.00),-90.00))
            geo.Label  = geoName+"Ellipse"
        else:
            geo        = App.ActiveDocument.addObject("Part::Ellipse",geoName+"Ellipse")
            geo.MajorRadius = float(dimensions[3].strip(" mm"))/2
            geo.MinorRadius = float(dimensions[5].strip(" mm"))
            geo.Angle1 = 0.00
            geo.Angle2 = 360.00
            geo.Placement = App.Placement(App.Vector(0.00,0.00,0.00),App.Rotation(App.Vector(1.00,0.00,0.00),-90.00))
            geo.Label  = geoName+"Ellipse"

        f              = App.ActiveDocument.addObject('Part::Extrusion',geoName+'EllipseNotch')
        f.Base         = App.ActiveDocument.getObject(geoName+'Ellipse')
        f.DirMode      = "Normal"
        f.DirLink      = None
        f.LengthFwd    = float(dimensions[1].strip(" mm"))
        f.LengthRev    = 0.000000000000000
        f.Solid        = True
        f.Reversed     = False
        f.Symmetric    = False
        f.TaperAngle   = 0.000000000000000
        f.TaperAngleRev= 0.000000000000000

        if float(dimensions[5].strip(" mm")) > float(dimensions[3].strip(" mm"))/2:
            App.ActiveDocument.getObject(geoName+'EllipseNotch').Placement = App.Placement(App.Vector(float(dimensions[0].strip(" mm"))/2,0.00,float(dimensions[4].strip(" mm"))),App.Rotation(App.Vector(0.00,1.00,0.00),90.00))
        else:
            App.ActiveDocument.getObject(geoName+'EllipseNotch').Placement = App.Placement(App.Vector(float(dimensions[0].strip(" mm"))/2,0.00,float(dimensions[4].strip(" mm"))),App.Rotation(App.Vector(0.00,1.00,0.00),0.00))

        App.ActiveDocument.recompute()

        j = BOPTools.JoinFeatures.makeConnect(name=geoName+'Connect')
        j.Objects = [App.ActiveDocument.getObject(geoName+'BoxNotch'), App.ActiveDocument.getObject(geoName+'EllipseNotch')]
        j.Proxy.execute(j)
        j.purgeTouched()
        for obj in j.ViewObject.Proxy.claimChildren():
            obj.ViewObject.hide()

        j = BOPTools.JoinFeatures.makeCutout(name=geoName)
        j.Base = App.ActiveDocument.getObject(geoName+'Box')
        j.Tool = App.ActiveDocument.getObject(geoName+'Connect')
        j.Proxy.execute(j)
        j.purgeTouched()
        for obj in j.ViewObject.Proxy.claimChildren():
            obj.ViewObject.hide()

        App.ActiveDocument.getObject(geoName+'Ellipse').Visibility = False
        App.ActiveDocument.getObject(geoName+'EllipseNotch').Visibility = False
        App.ActiveDocument.getObject(geoName+'BoxNotch').Visibility = False

        geo = App.ActiveDocument.getObject(geoName)





    if geoType == "Dogbone":

        # Define variables
        length = float(dimensions[0].strip(" mm"))  # Length of the part
        width = float(dimensions[1].strip(" mm"))  # Width of the part
        thickness = float(dimensions[2].strip(" mm"))  # Thickness of the part
        gauge_length = float(dimensions[3].strip(" mm"))  # Gauge length of the dogbone
        gauge_width = float(dimensions[4].strip(" mm"))  # Gauge width of the dogbone
        dogbone_type = dimensions[5]  # Type of the dogbone shape

        # Create a rectangular shape
        rectangle = App.ActiveDocument.addObject("Part::Box", geoName+"Rectangle")
        rectangle.Length = width
        rectangle.Width = thickness
        rectangle.Height = length

        # Create a dogbone shape
        if dogbone_type == 'Rounded':
            radius = (width-gauge_width)/2
            dogbone1 = App.ActiveDocument.addObject("Part::Cylinder", geoName+"Dogbone1")
            dogbone1.Radius = radius
            dogbone1.Height = thickness
            dogbone1.Placement = App.Placement(App.Vector(0, 0, length/2-gauge_length/2),App.Rotation(App.Vector(1,0,0),-90.00))

            dogbone2 = App.ActiveDocument.addObject("Part::Cylinder", geoName+"Dogbone2")
            dogbone2.Radius = radius
            dogbone2.Height = thickness
            dogbone2.Placement = App.Placement(App.Vector(width, 0, length/2-gauge_length/2),App.Rotation(App.Vector(1,0,0),-90.00))

            dogbone3 = App.ActiveDocument.addObject("Part::Cylinder", geoName+"Dogbone3")
            dogbone3.Radius = radius
            dogbone3.Height = thickness
            dogbone3.Placement = App.Placement(App.Vector(0, 0, length/2+gauge_length/2),App.Rotation(App.Vector(1,0,0),-90.00))

            dogbone4 = App.ActiveDocument.addObject("Part::Cylinder", geoName+"Dogbone4")
            dogbone4.Radius = radius
            dogbone4.Height = thickness
            dogbone4.Placement = App.Placement(App.Vector(width, 0, length/2+gauge_length/2),App.Rotation(App.Vector(1,0,0),-90.00))

            side1 = App.ActiveDocument.addObject("Part::Box", geoName+"side1")
            side1.Length = (width-gauge_width)/2
            side1.Width = thickness
            side1.Height = gauge_length
            side1.Placement = App.Placement(App.Vector(0, 0, length/2-gauge_length/2),App.Rotation(App.Vector(0,0,0),0.00))

            side2 = App.ActiveDocument.addObject("Part::Box", geoName+"side2")
            side2.Length = (width-gauge_width)/2
            side2.Width = thickness
            side2.Height = gauge_length
            side2.Placement = App.Placement(App.Vector(width-(width-gauge_width)/2, 0, length/2-gauge_length/2),App.Rotation(App.Vector(0,0,0),0.00))

            DogboneInsert = App.ActiveDocument.addObject("Part::MultiFuse", geoName+"DogboneInsert")
            DogboneInsert.Shapes = [dogbone1, dogbone2, dogbone3, dogbone4, side1, side2]

        else:
            side1 = App.ActiveDocument.addObject("Part::Box", geoName+"side1")
            side1.Length = (width-gauge_width)/2
            side1.Width = thickness
            side1.Height = gauge_length
            side1.Placement = App.Placement(App.Vector(0, 0, length/2-gauge_length/2),App.Rotation(App.Vector(0,0,0),0.00))

            side2 = App.ActiveDocument.addObject("Part::Box", geoName+"side2")
            side2.Length = (width-gauge_width)/2
            side2.Width = thickness
            side2.Height = gauge_length
            side2.Placement = App.Placement(App.Vector(width-(width-gauge_width)/2, 0, length/2-gauge_length/2),App.Rotation(App.Vector(0,0,0),0.00))

            DogboneInsert = App.ActiveDocument.addObject("Part::MultiFuse", geoName+"DogboneInsert")
            DogboneInsert.Shapes = [side1, side2]

        # Subtract the dogbone from the rectangle
        part = App.ActiveDocument.addObject("Part::Cut",geoName)
        part.Base = rectangle
        part.Tool = DogboneInsert
        geo = part

    if geoType == "Custom":
        part_name = ""
        if dimensions:
            part_name = str(dimensions[0]).strip()
        if not part_name and cadFile:
            part_name = str(cadFile).strip()
        if not part_name:
            raise Exception(
                "Custom geometry requires a selected FreeCAD body. "
                "Use Select Object on the Geometry tab and choose a solid in the document."
            )
        doc = App.getDocument(App.ActiveDocument.Name)
        part = doc.getObject(part_name)
        if part is None:
            by_label = doc.getObjectsByLabel(part_name)
            part = by_label[0] if by_label else None
        if part is None:
            raise Exception(f"Custom geometry object '{part_name}' was not found in the active document.")
        if not hasattr(part, "Shape") or part.Shape is None or part.Shape.isNull():
            raise Exception(f"Custom geometry object '{part_name}' has no valid solid shape.")
        part.Label = geoName
        geo = part



    if geoType == "Import CAD or Mesh":
        # Check if filetype is CAD (needing meshing) or mesh (already meshed)
        filename = os.path.basename(cadFile)
        filename, file_extension = os.path.splitext(filename)
        filename = re.sub("\.", "_", filename)
        filename = re.sub("/.", "_", filename)
        filename = re.sub("-", "_", filename)
        # If filename starts with a number, resub it with an underscore
        filename = re.sub("^\d", "_", filename)
        

        # If the file is a CAD file insert with ImportGui, else insert with Fem
        if is_cad_geometry_file(cadFile):
            ImportGui.insert(cadFile,App.ActiveDocument.Name)
            geo = App.getDocument(App.ActiveDocument.Name).getObject("Part__Feature")
            geo.Label = geoName            

        else:
            Fem.insert(cadFile,App.ActiveDocument.Name)
            geo = App.getDocument(App.ActiveDocument.Name).getObject(filename)
            geo.Label = geoName


    if geoType == "Sweep-3DP":
        import math
        
        profile_type = int(dimensions[0])
        path_type = int(dimensions[4])
        path_distance = dimensions[5]
        path_diameter = dimensions[6]
        path_side = dimensions[7]
        path_file = dimensions[8]
        path_sketch_name = dimensions[9] if len(dimensions) > 9 else ""
        num_layers = int(dimensions[10]) if len(dimensions) > 10 else 1
        raster_loops = int(dimensions[11]) if len(dimensions) > 11 and str(dimensions[11]).strip() else 1
        raster_spacing = float(str(dimensions[12]).strip().split()[0]) if len(dimensions) > 12 and str(dimensions[12]).strip() else 5.0
        raster_num_slices = int(dimensions[13]) if len(dimensions) > 13 and str(dimensions[13]).strip() else num_layers
        raster_dirs = []
        for _i in range(8):
            _idx = 14 + _i
            if len(dimensions) > _idx and str(dimensions[_idx]).strip():
                raster_dirs.append(float(str(dimensions[_idx]).strip()))
            else:
                raster_dirs.append(0.0 if _i % 2 == 0 else 90.0)
        raster_corner_fillet = float(str(dimensions[22]).strip().split()[0]) if len(dimensions) > 22 and str(dimensions[22]).strip() else 0.0
        raster_path_length = float(str(dimensions[23]).strip().split()[0]) if len(dimensions) > 23 and str(dimensions[23]).strip() else None
        if path_type == 3:
            num_layers = max(1, min(8, raster_num_slices))
        
        layer_shapes = []
        
        for layer_idx in range(num_layers):
            if profile_type == 0:
                _lh = float(dimensions[2].strip(" mm"))
                z_offset = layer_idx * _lh + (_lh / 2.0 if path_type == 3 else 0.0)
            else:
                z_offset = 0
            
            current_geoName = geoName if num_layers == 1 else f"{geoName}_Layer{layer_idx}"
            
            if profile_type == 0:
                layer_width = float(dimensions[1].strip(" mm"))
                layer_height = float(dimensions[2].strip(" mm"))
                v1 = App.Vector(0, -layer_width/2, -layer_height/2)
                v2 = App.Vector(0,  layer_width/2, -layer_height/2)
                v3 = App.Vector(0,  layer_width/2,  layer_height/2)
                v4 = App.Vector(0, -layer_width/2,  layer_height/2)
                line1 = Part.LineSegment(v1, v2)
                line2 = Part.LineSegment(v2, v3)
                line3 = Part.LineSegment(v3, v4)
                line4 = Part.LineSegment(v4, v1)
                edge1 = line1.toShape()
                edge2 = line2.toShape()
                edge3 = line3.toShape()
                edge4 = line4.toShape()
                profile_wire = Part.Wire([edge1, edge2, edge3, edge4])
                if not profile_wire.isClosed():
                    raise Exception("Profile wire is not closed!")
                profile_face = Part.Face(profile_wire)
                profile_obj = App.ActiveDocument.addObject("Part::Feature", current_geoName + '_Profile')
                profile_obj.Shape = profile_face
                profile_obj.Label = current_geoName + '_Profile'
                profile_obj.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 0, 1), 0))
            else:
                profile_file = dimensions[3]
                if not profile_file or profile_file.strip() == "":
                    raise Exception("Profile CAD file path is required when using CAD.")
                if not os.path.exists(profile_file):
                    raise Exception(f"Profile CAD file not found: {profile_file}")
                if file_extension(profile_file) != "dxf":
                    raise Exception(f"Unsupported profile file format: .{file_extension(profile_file)}.")
                
                if importDXF is None:
                    raise Exception("DXF import module not available in FreeCAD.")
                
                try:
                    objects_before = set(App.ActiveDocument.Objects)
                    importDXF.insert(profile_file, App.ActiveDocument.Name)
                    App.ActiveDocument.recompute()
                    objects_after = set(App.ActiveDocument.Objects)
                    imported_objs = list(objects_after - objects_before)
                    
                    if not imported_objs:
                        imported_objs = [obj for obj in App.ActiveDocument.Objects 
                                       if obj.Label.startswith(os.path.splitext(os.path.basename(profile_file))[0])]
                    
                    if not imported_objs:
                        raise Exception(f"Failed to import profile from DXF file '{profile_file}'.")
                    
                    profile_obj = None
                    for obj in imported_objs:
                        if hasattr(obj, 'Shape') and obj.Shape and not obj.Shape.isNull():
                            profile_obj = obj
                            break
                    
                    if profile_obj is None:
                        profile_obj = imported_objs[0]
                    
                    profile_obj.Label = current_geoName + '_Profile'
                    App.ActiveDocument.recompute()
                    
                except Exception as e:
                    raise Exception(f"Failed to import profile DXF file '{profile_file}': {str(e)}")
            if path_type == 0:
                if not path_distance or path_distance.strip() == "":
                    raise Exception("Path distance is required for straight line path.")
                distance = float(path_distance.strip(" mm"))
                if distance <= 0:
                    raise Exception("Path distance must be > 0.")
                start_point = App.Vector(0, 0, z_offset)
                end_point = App.Vector(distance, 0, z_offset)
                edge = Part.LineSegment(start_point, end_point).toShape()
                path_obj = App.ActiveDocument.addObject("Part::Feature", current_geoName + "_Path")
                path_obj.Shape = edge
                path_obj.Label = current_geoName + "_Path"

            elif path_type == 1:
                if not path_side or path_side.strip() == "":
                    raise Exception("Square side is required for square path.")
                try:
                    side = float(path_side.strip(" mm"))
                except:
                    raise Exception(f"Invalid square side value: '{path_side}'.")
                if side <= 0:
                    raise Exception(f"Square side must be > 0 (got {side}mm).")
                p1 = App.Vector(0, 0, z_offset)
                p2 = App.Vector(side, 0, z_offset)
                p3 = App.Vector(side, side, z_offset)
                p4 = App.Vector(0, side, z_offset)
                e1 = Part.LineSegment(p1, p2).toShape()
                e2 = Part.LineSegment(p2, p3).toShape()
                e3 = Part.LineSegment(p3, p4).toShape()
                e4 = Part.LineSegment(p4, p1).toShape()
                square_wire = Part.Wire([e1, e2, e3, e4])
                if not square_wire.isClosed():
                    raise Exception("Square wire is not closed!")
                path_obj = App.ActiveDocument.addObject("Part::Feature", current_geoName + "_Path")
                path_obj.Shape = square_wire
                path_obj.Label = current_geoName + "_Path"
                App.ActiveDocument.recompute()

            elif path_type == 2:
                if not path_sketch_name or path_sketch_name.strip() == "":
                    raise Exception("Path sketch is required when using FreeCAD Sketch option.")
                
                try:
                    sketch_obj = App.ActiveDocument.getObject(path_sketch_name)
                    if sketch_obj is None:
                        raise Exception(f"Sketch object '{path_sketch_name}' not found in document.")
                    
                    if not hasattr(sketch_obj, 'TypeId') or 'Sketch' not in sketch_obj.TypeId:
                        raise Exception(f"Object '{path_sketch_name}' is not a sketch object.")
                    
                    if not sketch_obj.Shape or sketch_obj.Shape.isNull():
                        raise Exception(f"Sketch '{path_sketch_name}' has no valid geometry.")
                    
                    edges = sketch_obj.Shape.Edges
                    if not edges:
                        raise Exception(f"Sketch '{path_sketch_name}' contains no edges.")
                    
                    try:
                        spine_wire = Part.Wire(edges)
                    except:
                        spine_wire = Part.Compound(edges)
                    
                    path_obj = App.ActiveDocument.addObject("Part::Feature", current_geoName + "_Path")
                    path_obj.Shape = spine_wire
                    path_obj.Label = current_geoName + "_Path"
                    path_obj.Placement = App.Placement(App.Vector(0, 0, z_offset), App.Rotation(App.Vector(0, 0, 1), 0))
                    App.ActiveDocument.recompute()
                    
                except Exception as e:
                    raise Exception(f"Failed to use sketch '{path_sketch_name}' as path: {str(e)}")
            elif path_type == 3:
                loops = max(1, int(raster_loops))
                num_lines = loops + 1
                spacing = max(1e-6, float(raster_spacing))
                fillet_r = max(0.0, float(raster_corner_fillet))

                if profile_type == 0:
                    eff_w = max(1e-6, float(dimensions[1].strip(" mm")))
                else:
                    try:
                        bb = profile_face.BoundBox
                        eff_w = max(1e-6, max(bb.XLength, bb.YLength))
                    except Exception:
                        eff_w = 1.0

                total_length = float(raster_path_length) if raster_path_length is not None else max(spacing * 4.0, spacing * (num_lines + 2))
                if total_length <= eff_w:
                    total_length = eff_w + 1.0

                seg_len = total_length - eff_w
                if seg_len <= 0:
                    seg_len = 1.0
                half_len = seg_len / 2.0
                half_span = spacing * (num_lines - 1) / 2.0

                angle_deg = raster_dirs[layer_idx] if layer_idx < len(raster_dirs) else 0.0
                angle_rad = math.radians(angle_deg)
                cos_a = math.cos(angle_rad)
                sin_a = math.sin(angle_rad)

                def _rot_xy(v):
                    return App.Vector(
                        v.x * cos_a - v.y * sin_a,
                        v.x * sin_a + v.y * cos_a,
                        v.z,
                    )

                segments = []
                for i in range(num_lines):
                    y = i * spacing - half_span
                    forward = (i % 2 == 0)
                    p0 = App.Vector(-half_len, y, z_offset) if forward else App.Vector(half_len, y, z_offset)
                    p1 = App.Vector(half_len, y, z_offset) if forward else App.Vector(-half_len, y, z_offset)

                    rp0 = _rot_xy(p0)
                    rp1 = _rot_xy(p1)
                    segments.append(Part.LineSegment(rp0, rp1).toShape())

                    if i < num_lines - 1:
                        y_next = (i + 1) * spacing - half_span
                        corner_x = half_len if forward else -half_len

                        r_eff = 0.0
                        if fillet_r > 0:
                            r_eff = min(fillet_r, abs(y_next - y) * 0.5, seg_len * 0.25)

                        if r_eff > 0:
                            sign_x = 1.0 if forward else -1.0
                            horiz_end = App.Vector(corner_x - sign_x * r_eff, y, z_offset)
                            segments[-1] = Part.LineSegment(_rot_xy(p0), _rot_xy(horiz_end)).toShape()

                            arc_start = App.Vector(corner_x - sign_x * r_eff, y, z_offset)
                            arc_end = App.Vector(corner_x, y + r_eff, z_offset)
                            arc_center = App.Vector(corner_x - sign_x * r_eff, y + r_eff, z_offset)
                            arc = Part.Arc(_rot_xy(arc_start), _rot_xy(arc_center), _rot_xy(arc_end)).toShape()
                            segments.append(arc)

                            conn_start = App.Vector(corner_x, y + r_eff, z_offset)
                        else:
                            conn_start = App.Vector(corner_x, y, z_offset)

                        conn_end = App.Vector(corner_x, y_next, z_offset)
                        rc0 = _rot_xy(conn_start)
                        rc1 = _rot_xy(conn_end)
                        segments.append(Part.LineSegment(rc0, rc1).toShape())
                path_obj = App.ActiveDocument.addObject("Part::Feature", current_geoName + "_Path")
                path_obj.Shape = Part.Wire(segments)
                path_obj.Label = current_geoName + "_Path"
                App.ActiveDocument.recompute()
            else:
                raise Exception(f"Unsupported Sweep-3DP path type index: {path_type}")
            
            App.ActiveDocument.recompute()
            
            def find_connected_edges(edges):
                if not edges:
                    return []
                
                groups = []
                remaining = list(edges)
                
                while remaining:
                    current_group = [remaining.pop(0)]
                    changed = True
                    
                    while changed:
                        changed = False
                        for edge in remaining[:]:
                            for group_edge in current_group:
                                v1_start = edge.Vertexes[0].Point
                                v1_end = edge.Vertexes[-1].Point
                                v2_start = group_edge.Vertexes[0].Point
                                v2_end = group_edge.Vertexes[-1].Point
                                
                                if (v1_start.distanceToPoint(v2_start) < 1e-6 or
                                    v1_start.distanceToPoint(v2_end) < 1e-6 or
                                    v1_end.distanceToPoint(v2_start) < 1e-6 or
                                    v1_end.distanceToPoint(v2_end) < 1e-6):
                                    current_group.append(edge)
                                    remaining.remove(edge)
                                    changed = True
                                    break
                            if changed:
                                break
                    
                    groups.append(current_group)
                
                return groups
            
            spine_wires = []
            
            if isinstance(path_obj.Shape, Part.Wire):
                spine_wires = [path_obj.Shape]
            elif hasattr(path_obj.Shape, 'Wires') and path_obj.Shape.Wires:
                spine_wires = list(path_obj.Shape.Wires)
            elif hasattr(path_obj.Shape, 'Edges') and path_obj.Shape.Edges:
                try:
                    spine_wires = [Part.Wire(path_obj.Shape.Edges)]
                except Exception:
                    if len(path_obj.Shape.Edges) == 1:
                        spine_wires = [Part.Wire([path_obj.Shape.Edges[0]])]
                    else:
                        edge_groups = find_connected_edges(path_obj.Shape.Edges)
                        if edge_groups:
                            for group in edge_groups:
                                try:
                                    spine_wires.append(Part.Wire(group))
                                except Exception:
                                    pass
                        if not spine_wires:
                            raise Exception("Path edges are not connected.")
            else:
                raise Exception("Path must contain a valid wire or edges.")
            
            if not spine_wires:
                raise Exception("No valid path wires found.")
            
            spine_wire = spine_wires[0]
            
            if path_type == 2 and spine_wire and len(spine_wire.Edges) > 0:
                segment_edges = []
                for edge in spine_wire.Edges:
                    try:
                        pts = edge.discretize(Deflection=0.05)
                        for i in range(len(pts) - 1):
                            segment_edges.append(Part.LineSegment(pts[i], pts[i + 1]).toShape())
                    except Exception:
                        segment_edges.append(edge)
                if segment_edges:
                    try:
                        spine_wire = Part.Wire(segment_edges)
                    except Exception:
                        pass
            
            if isinstance(profile_obj.Shape, Part.Face):
                profile_wire = profile_obj.Shape.Wires[0] if profile_obj.Shape.Wires else None
            elif isinstance(profile_obj.Shape, Part.Wire):
                profile_wire = profile_obj.Shape
            elif hasattr(profile_obj.Shape, 'Wires') and profile_obj.Shape.Wires:
                profile_wire = profile_obj.Shape.Wires[0]
            elif hasattr(profile_obj.Shape, 'Edges') and profile_obj.Shape.Edges:
                profile_wire = Part.Wire(profile_obj.Shape.Edges)
            else:
                raise Exception("Profile must be a valid wire or face.")
            
            if isinstance(profile_obj.Shape, Part.Face):
                profile_face = profile_obj.Shape
            elif isinstance(profile_obj.Shape, Part.Wire):
                profile_face = Part.Face(profile_obj.Shape)
            elif hasattr(profile_obj.Shape, 'Wires') and profile_obj.Shape.Wires:
                profile_face = Part.Face(profile_obj.Shape.Wires[0])
            else:
                profile_face = Part.Face(Part.Wire(profile_obj.Shape.Edges))
            
            import math as _math

            def _get_edge_tangent(edge):
                try:
                    t = edge.tangentAt(edge.FirstParameter)
                    if t.Length > 1e-6:
                        t.normalize()
                        return t
                except Exception:
                    pass
                try:
                    va = edge.Vertexes[0].Point
                    vb = edge.Vertexes[-1].Point
                    d = vb.sub(va)
                    if d.Length > 1e-6:
                        d.normalize()
                        return d
                except Exception:
                    pass
                return None

            def _make_profile_for_edge(base_face, edge_start, tangent):
                profile_center = base_face.BoundBox.Center
                f = base_face.copy()
                f.translate(edge_start.sub(App.Vector(profile_center.x, profile_center.y, profile_center.z)))
                if tangent is not None:
                    try:
                        fn = f.normalAt(0, 0)
                        fn.normalize()
                    except Exception:
                        fn = App.Vector(0, 0, 1)
                    dot = max(-1.0, min(1.0, fn.dot(tangent)))
                    if abs(dot) < 0.9999:
                        ax = fn.cross(tangent)
                        if ax.Length > 1e-6:
                            ax.normalize()
                            ang = _math.degrees(_math.acos(dot))
                            ctr = f.BoundBox.Center
                            f.rotate(App.Vector(ctr.x, ctr.y, ctr.z), ax, ang)
                return f

            def _sweep_single_edge(edge, face):
                seg_wire = Part.Wire([edge])
                wire = face.Wires[0] if face.Wires else Part.Wire(face.Edges)
                try:
                    s = seg_wire.makePipeShell([wire], True, False)
                    if s.isValid():
                        return s
                except Exception:
                    pass
                try:
                    s = seg_wire.makePipeShell([wire], False, False)
                    if s.isValid():
                        return Part.Solid(s)
                except Exception:
                    pass
                return None

            def _make_corner_fill(vertex_pt, t1, t2, half_w, half_h, z_up):
                try:
                    origin = App.Vector(
                        vertex_pt.x - half_w,
                        vertex_pt.y - half_w,
                        vertex_pt.z - half_h
                    )
                    box = Part.makeBox(half_w * 2, half_w * 2, half_h * 2, origin)
                    return box
                except Exception:
                    return None

            all_segment_shapes = []

            for path_idx, active_spine_wire in enumerate(spine_wires):
                path_geoName = current_geoName if len(spine_wires) == 1 else f"{current_geoName}_Path{path_idx}"

                edges = active_spine_wire.Edges
                seg_solids = []

                if profile_type == 0:
                    half_w = layer_width / 2.0
                    half_h = layer_height / 2.0
                    z_up = App.Vector(0, 0, 1)
                else:
                    bb = profile_face.BoundBox
                    half_w = max(bb.XLength, bb.YLength) / 2.0
                    half_h = bb.ZLength / 2.0
                    z_up = App.Vector(0, 0, 1)

                for seg_edge in edges:
                    seg_tangent = _get_edge_tangent(seg_edge)
                    seg_start = seg_edge.Vertexes[0].Point
                    placed_face = _make_profile_for_edge(profile_face, seg_start, seg_tangent)
                    seg_solid = _sweep_single_edge(seg_edge, placed_face)
                    if seg_solid is not None:
                        seg_solids.append(seg_solid)

                ordered_edges = list(edges)
                for i in range(len(ordered_edges) - 1):
                    e1 = ordered_edges[i]
                    e2 = ordered_edges[i + 1]
                    v1_end = e1.Vertexes[-1].Point
                    v2_start = e2.Vertexes[0].Point
                    if v1_end.distanceToPoint(v2_start) < 1e-4:
                        corner_pt = v1_end
                    else:
                        corner_pt = None

                    if corner_pt is not None:
                        t1 = _get_edge_tangent(e1)
                        t2 = _get_edge_tangent(e2)
                        if t1 is not None and t2 is not None:
                            fill = _make_corner_fill(corner_pt, t1, t2, half_w, half_h, z_up)
                            if fill is not None:
                                seg_solids.append(fill)

                if active_spine_wire.isClosed() and len(ordered_edges) > 1:
                    e_last = ordered_edges[-1]
                    e_first = ordered_edges[0]
                    t1 = _get_edge_tangent(e_last)
                    t2 = _get_edge_tangent(e_first)
                    corner_pt = e_last.Vertexes[-1].Point
                    if t1 is not None and t2 is not None:
                        fill = _make_corner_fill(corner_pt, t1, t2, half_w, half_h, z_up)
                        if fill is not None:
                            seg_solids.append(fill)

                if not seg_solids:
                    raise Exception(f"Segment-by-segment {path_idx}.")

                if len(seg_solids) == 1:
                    sweep_shape = seg_solids[0]
                else:
                    combined = seg_solids[0]
                    for s in seg_solids[1:]:
                        try:
                            combined = combined.fuse(s)
                        except Exception:
                            pass
                    try:
                        combined = combined.removeSplitter()
                    except Exception:
                        pass
                    sweep_shape = combined
                layer_geo = App.ActiveDocument.addObject("Part::Feature", path_geoName)
                layer_geo.Shape = sweep_shape
                layer_geo.Label = path_geoName
                App.ActiveDocument.recompute()
                layer_shapes.append(layer_geo)
            
            try:
                profile_obj.ViewObject.Visibility = False
            except Exception:
                pass
            try:
                path_obj.ViewObject.Visibility = False
            except Exception:
                pass

        # Fuse all layer shapes into a single solid
        shapes_to_fuse = all_segment_shapes if all_segment_shapes else [ls.Shape for ls in layer_shapes]
        if not shapes_to_fuse:
            raise Exception(
                "Sweep-3DP generated no geometry "
            )
        if len(shapes_to_fuse) == 1:
            merged_shape = shapes_to_fuse[0]
        else:
            merged_shape = shapes_to_fuse[0]
            for s in shapes_to_fuse[1:]:
                try:
                    merged_shape = merged_shape.fuse(s)
                except Exception:
                    pass
        for _fn in ('removeSplitter', 'refine'):
            try:
                merged_shape = getattr(merged_shape, _fn)()
            except Exception:
                pass
        geo = App.ActiveDocument.addObject("Part::Feature", geoName)
        geo.Shape = merged_shape
        geo.Label = geoName
        App.ActiveDocument.recompute()
        for layer_geo in layer_shapes:
            try:
                App.ActiveDocument.removeObject(layer_geo.Name)
            except Exception:
                pass
        



    App.ActiveDocument.recompute()
    
    try:
        return geo
    except NameError:
        raise Exception(
            f"Geometry type '{geoType}' did not create a geometry object."
        )
