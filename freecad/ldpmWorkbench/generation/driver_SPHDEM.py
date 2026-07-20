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
## Description coming soon...
##
##
## ===========================================================================

# pyright: reportMissingImports=false

# Importing: standard
import os
import re
import shutil
import time
import tempfile
import numpy as np
from pathlib import Path
import multiprocessing
import functools
import math
import ast

# Importing: FreeCAD
import FreeCADGui as Gui
import FreeCAD as App
import Part
import Part,PartGui
import Mesh
import MeshPartGui, FreeCADGui
import MeshPart
import Mesh, Part, PartGui
import MaterialEditor
import ObjectsFem
import FemGui
import Fem
import femmesh.femmesh2mesh
import feminout.importVTKResults

try:  # FreeCAD 1.0 provides a PySide shim
    from PySide import QtCore, QtGui, QtWidgets  # type: ignore
except ImportError:  # FreeCAD 0.20 ships PySide2
    try:
        from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore
    except ImportError:  # Fall back for very old FreeCAD versions
        from PySide import QtCore, QtGui  # type: ignore
        QtWidgets = QtGui  # type: ignore



# Importing: generation
from freecad.ldpmWorkbench.generation.calc_LDPMCSL_meshVolume           import calc_LDPMCSL_meshVolume
from freecad.ldpmWorkbench.generation.calc_parVolume                    import calc_parVolume
from freecad.ldpmWorkbench.generation.calc_sieveCurve                   import calc_sieveCurve
from freecad.ldpmWorkbench.generation.calc_LDPMCSL_surfMeshSize         import calc_LDPMCSL_surfMeshSize
from freecad.ldpmWorkbench.generation.calc_LDPMCSL_surfMeshExtents      import calc_LDPMCSL_surfMeshExtents
from freecad.ldpmWorkbench.generation.check_particleOverlapMPI          import check_particleOverlapMPI
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_analysis              import gen_LDPMCSL_analysis
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_geometry              import gen_LDPMCSL_geometry
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_initialMesh           import gen_LDPMCSL_initialMesh
from freecad.ldpmWorkbench.generation.gen_particle                      import gen_particle
from freecad.ldpmWorkbench.generation.gen_particleMPI                   import gen_particleMPI
from freecad.ldpmWorkbench.generation.gen_particleList                  import gen_particleList

# Importing: input
from freecad.ldpmWorkbench.input.read_SPHDEM_inputs                     import read_SPHDEM_inputs

# Importing: output
from freecad.ldpmWorkbench.output.mkVtk_particles                       import mkVtk_particles
from freecad.ldpmWorkbench.output.mkData_nodes                          import mkData_nodes
from freecad.ldpmWorkbench.output.mkData_surfMesh                       import mkData_surfMesh
from freecad.ldpmWorkbench.output.mkData_particles                      import mkData_particles
from freecad.ldpmWorkbench.output.mkDisp_sieveCurves                    import mkDisp_sieveCurves




def driver_SPHDEM(self,fastGen,tempPath):

    # Read in inputs from input panel
    [setupFile, \
        numCPU, numIncrements,maxIter,placementAlg,\
        geoType, dimensions, cadFile,\
        minPar, maxPar, fullerCoef, sieveCurveDiameter, sieveCurvePassing, minDistCoef,\
        wcRatio, densityWater, cementC, flyashC, silicaC, scmC,\
        cementDensity, flyashDensity, silicaDensity, scmDensity, airFrac1, \
        fillerC, fillerDensity, airFrac2,\
        outDir, modelType] = read_SPHDEM_inputs(self.form)

    # Make output directory if does not exist
    try:
        os.mkdir(outDir)
    except:
        pass

    # Initialize code start time to measure performance
    start_time = time.time()


    # Store document
    docGui = Gui.activeDocument()

    # Make new document and set view if does not exisit
    try:
        docGui.activeView().viewAxonometric()
    except:
        App.newDocument("Unnamed")
        docGui = Gui.activeDocument()
        docGui.activeView().viewAxonometric()
    Gui.runCommand('Std_PerspectiveCamera',1)

    try:
        sieveCurveDiameter = ast.literal_eval(sieveCurveDiameter)
        sieveCurvePassing = ast.literal_eval(sieveCurvePassing)
    except:
        pass

    try:
        grainAggSieveD = ast.literal_eval(grainAggSieveD)
        grainAggSieveP = ast.literal_eval(grainAggSieveP)
    except:
        pass

    try:
        grainITZSieveD = ast.literal_eval(grainITZSieveD)
        grainITZSieveP = ast.literal_eval(grainITZSieveP)
    except:
        pass


    try:
        grainBinderSieveD = ast.literal_eval(grainBinderSieveD)
        grainBinderSieveP = ast.literal_eval(grainBinderSieveP)
    except:
        pass



    if modelType in ["Discrete Fresh Concrete (DFC)"]:
        elementType = "DFC"
    else:
        error_msg = f"Element type '{modelType}' not recognized. Please select a valid model type."
        print(error_msg)
        raise ValueError(error_msg)


    if fillerC > 0:
        airFrac = airFrac2
    else:
        airFrac = airFrac1
    
    verbose = "On"

    self.form[4].progressBar.setValue(1) 
    self.form[4].statusWindow.setText("Status: Generating objects.") 



    geoName = elementType + "geo" + str(0).zfill(3)
    meshName = elementType + "mesh" + str(0).zfill(3)
    analysisName = elementType + "analysis"
    materialName = elementType + "material"
    dataFilesName = elementType + 'dataFiles'+ str(0).zfill(3)
    visualFilesName = elementType + 'visualFiles'+ str(0).zfill(3)

    i = 0
    try:
        test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName)[0] != None)
    except:
        test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName) != [])

    while test == True:
        i = i+1
        geoName = elementType + "geo" + str(i).zfill(3)
        meshName = elementType + "mesh" + str(i).zfill(3)
        dataFilesName = elementType + 'dataFiles'+ str(i).zfill(3)
        visualFilesName = elementType + 'visualFiles'+ str(i).zfill(3)
        try:
            test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName)[0] != None)
        except:
            test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName) != [])

    # Generate geometry
    self.form[4].statusWindow.setText("Status: Generating geometry.") 
    genGeo = gen_LDPMCSL_geometry(dimensions,geoType,geoName,cadFile)
    self.form[4].progressBar.setValue(2) 

    # Set view
    docGui.activeView().viewAxonometric()
    Gui.SendMsgToActiveView("ViewFit")
    Gui.runCommand('Std_DrawStyle',6)
    Gui.runCommand('Std_PerspectiveCamera',1)


    # Generate analysis objects
    self.form[4].statusWindow.setText("Status: Generating analysis objects.") 
    genAna = gen_LDPMCSL_analysis(analysisName,materialName)
    self.form[4].progressBar.setValue(3) 


    # Generate surface mesh
    self.form[4].statusWindow.setText("Status: Generating surface mesh.") 
    [meshVertices,meshTets,surfaceNodes,surfaceFaces] = gen_LDPMCSL_initialMesh(cadFile,analysisName,geoName,meshName,minPar)
    self.form[4].progressBar.setValue(5) 


    # Gets extents of geometry
    [minC,maxC] = calc_LDPMCSL_surfMeshExtents(meshVertices)







    # Convert density to Kg/m3
    cementC = cementC * (1.0E+12)
    flyashC = flyashC * (1.0E+12)
    silicaC = silicaC * (1.0E+12)
    scmC = scmC * (1.0E+12)
    fillerC = fillerC * (1.0E+12)
    cementDensity = cementDensity * (1.0E+12)
    flyashDensity = flyashDensity * (1.0E+12)
    silicaDensity = silicaDensity * (1.0E+12)
    scmDensity = scmDensity * (1.0E+12)
    fillerDensity = fillerDensity * (1.0E+12)
    densityWater = densityWater * (1.0E+12)




    self.form[4].statusWindow.setText("Status: Calculating input data.") 
    

    # Gets volume of geometry
    tetVolume = calc_LDPMCSL_meshVolume(meshVertices,meshTets)





    # Calculation of surface mesh size
    maxEdgeLength = calc_LDPMCSL_surfMeshSize(meshVertices,surfaceFaces)


    # Basic Calcs
    parOffset = minDistCoef*minPar

    
    # Store coordinates of meshTets in new format
    coord1 = meshVertices[meshTets[:,0]-1]
    coord2 = meshVertices[meshTets[:,1]-1]
    coord3 = meshVertices[meshTets[:,2]-1]
    coord4 = meshVertices[meshTets[:,3]-1]



    verts = meshVertices[np.array(meshTets).flatten()-1]
    max_dist = np.max(np.sqrt(np.sum(verts**2, axis=1)))




    if fastGen == True:

        ########################## Alternative Route to Farm Out Particle Processes ##############################

            # Make a temporary file that will be used to store the parameters and then run the generation:

    # Write these seven matrices to temporary files that will later be read back in by the generation script:
    # coord1, coord2, coord3, coord4, meshVertices, meshTets, surfaceNodes
        
        np.save(tempPath + "coord1.npy", coord1)
        np.save(tempPath + "coord2.npy", coord2)
        np.save(tempPath + "coord3.npy", coord3)
        np.save(tempPath + "coord4.npy", coord4)
        np.save(tempPath + "meshVertices.npy", meshVertices)
        np.save(tempPath + "meshTets.npy", meshTets)
        np.save(tempPath + "surfaceNodes.npy", surfaceNodes)

        # Get the current directory 
        currentDir = os.path.dirname(os.path.realpath(__file__))


        with open(Path(currentDir + "/tempGen.py"), "w") as f:
            f.write("""\n
# ================================================================================
# LDPM WORKBENCH - github.com/Concrete-Chrono-Development/chrono-preprocessor
#     
# ================================================================================
# LDPM Workbench Parameter File
# ================================================================================
#
# LDPM Workbench developed by Northwestern University
#
# ================================================================================

from gen_SPHDEM_multiStep   import gen_SPHDEM_multiStep                     
                    
            \n\n""")
            f.write('tempPath = r"' + tempPath + '"\n')
            f.write('numCPU = ' + str(numCPU) + "\n")
            f.write('numIncrements = ' + str(numIncrements) + "\n")
            f.write('maxIter = ' + str(maxIter) + "\n")
            f.write('parOffset = ' + str(parOffset) + "\n")
            f.write('maxEdgeLength = ' + str(maxEdgeLength) + "\n")
            f.write('max_dist = ' + str(max_dist) + "\n")
            f.write('minPar = ' + str(minPar) + "\n")
            f.write('maxPar = ' + str(maxPar) + "\n")
            if fullerCoef == "":
                f.write("fullerCoef = None\n")
            else:
                f.write("fullerCoef = " + str(fullerCoef) + "\n")
            if sieveCurveDiameter == "":
                f.write('sieveCurveDiameter = ""\n')
            else:
                f.write("sieveCurveDiameter = " + str(sieveCurveDiameter) + "\n")
            if sieveCurvePassing == "":
                f.write("sieveCurvePassing = None\n")
            else:
                f.write("sieveCurvePassing = " + str(sieveCurvePassing) + "\n")
            f.write("wcRatio = " + str(wcRatio) + "\n")
            f.write("densityWater = " + str(densityWater) + "\n")
            f.write("cementC = " + str(cementC) + "\n")
            f.write("flyashC = " + str(flyashC) + "\n")
            f.write("silicaC = " + str(silicaC) + "\n")
            f.write("scmC = " + str(scmC) + "\n")
            f.write("cementDensity = " + str(cementDensity) + "\n")
            f.write("flyashDensity = " + str(flyashDensity) + "\n")
            f.write("silicaDensity = " + str(silicaDensity) + "\n")
            f.write("scmDensity = " + str(scmDensity) + "\n")
            f.write("airFrac = " + str(airFrac) + "\n")
            f.write("fillerC = " + str(fillerC) + "\n")
            f.write("fillerDensity = " + str(fillerDensity) + "\n")
            f.write("tetVolume = " + str(tetVolume) + "\n")
            f.write("minC = [" + str(minC[0]) + ", " + str(minC[1]) + ", " + str(minC[2]) + "]\n")
            f.write("maxC = [" + str(maxC[0]) + ", " + str(maxC[1]) + ", " + str(maxC[2]) + "]\n")
            f.write('verbose = "' + str(verbose) + '"\n')


            f.write("""

def main():
                
    generation = gen_SPHDEM_multiStep(tempPath, numCPU, numIncrements, maxIter, parOffset, maxEdgeLength, max_dist, minPar, maxPar, sieveCurveDiameter, sieveCurvePassing, wcRatio, cementC, airFrac, fullerCoef, flyashC, silicaC, scmC, fillerC, flyashDensity, silicaDensity, scmDensity, fillerDensity, cementDensity, densityWater, tetVolume, minC, maxC, verbose)
                
                
if __name__ == '__main__':
    main()
            """)

        
       
        # Run the generation   
        os.system("python " + str(Path(currentDir + "/tempGen.py")))

        # Read the temporary internalNodes file
        internalNodes = np.load(tempPath + "internalNodes.npy")

        # Read the temporary materialList file
        materialList = np.load(tempPath + "materialList.npy")

        # Read the temporary parDiameterList file
        parDiameterList = np.load(tempPath + "parDiameterList.npy")

        # Read the particleID file
        particleID = np.load(tempPath + "particleID.npy")


        # Read the volFracPar file
        volFracPar = np.load(tempPath + "volFracPar.npy")

        # Remove the temporary files
        os.remove(Path(currentDir + "/tempGen.py"))

        # Remove the temporary data files
        os.remove(tempPath + "internalNodes.npy")
        os.remove(tempPath + "materialList.npy")
        os.remove(tempPath + "parDiameterList.npy")

        os.remove(tempPath + "volFracPar.npy")
        os.remove(tempPath + "coord1.npy")
        os.remove(tempPath + "coord2.npy")
        os.remove(tempPath + "coord3.npy")
        os.remove(tempPath + "coord4.npy")
        os.remove(tempPath + "meshVertices.npy")
        os.remove(tempPath + "meshTets.npy")
        os.remove(tempPath + "surfaceNodes.npy")
        os.remove(tempPath + "particleID.npy")



    else:





        #################### Begin Setting Up Particles and Materials (Normal Method) ##############################



        # Shift sieve curve if needed
        if sieveCurveDiameter != (0 or None or [] or ""):
            # Shifts sieve curve to appropriate range
            [newSieveCurveD, newSieveCurveP, NewSet, w_min, w_max] = calc_sieveCurve(minPar, maxPar, sieveCurveDiameter, sieveCurvePassing)
        else:
            newSieveCurveD, newSieveCurveP, w_min, w_max, NewSet = 0, 0, 0, 0, 0

        # Calculates volume of particles needed
        [volFracPar, parVolTotal, cdf, cdf1, kappa_i] = calc_parVolume(tetVolume, wcRatio, cementC,
                                                    airFrac, fullerCoef, 
                                                    flyashC, silicaC, scmC, fillerC,
                                                    flyashDensity, silicaDensity, 
                                                    scmDensity, fillerDensity, cementDensity,
                                                    densityWater, minPar, maxPar,
                                                    newSieveCurveD, newSieveCurveP, 
                                                    NewSet, w_min, w_max)



        self.form[4].statusWindow.setText("Status: Calculating list of particles.") 
        # Calculate list of particle diameters for placement
        [maxParNum,parDiameterList] = gen_particleList(parVolTotal,minPar,maxPar,newSieveCurveD,\
            cdf,kappa_i,NewSet,fullerCoef)
    
        # Initialize empty particle nodes list outside geometry
        internalNodes = (np.zeros((len(parDiameterList),3))+2)*maxC
    












        ########################## Begin Placing Particles ##############################

        


        self.form[4].statusWindow.setText('Status: Placing particles into geometry. (' + str(0) + '/' + str(len(internalNodes)) + ')') 
        
        # Initialize values
        newMaxIter = 6
        particlesPlaced = 0




        if numCPU > 1:
        
            
            for increment in range(numIncrements-1):

                process_pool = multiprocessing.Pool(numCPU)

                outputMPI = process_pool.map(functools.partial(gen_particleMPI, surfaceNodes,maxParNum, minC, maxC, meshVertices, \
                    meshTets, coord1,coord2,coord3,coord4,newMaxIter,maxIter,minPar,\
                    maxPar,parOffset,verbose,parDiameterList,maxEdgeLength,max_dist,internalNodes), parDiameterList[particlesPlaced:particlesPlaced+math.floor(len(parDiameterList)/numIncrements)])

                nodeMPI = np.array(outputMPI)[:,0:3]
                diameter = np.array(outputMPI)[:,3]
                newMaxIter = int(max(np.array(outputMPI)[:,4]))
                maxAttempts = int(max(np.array(outputMPI)[:,5]))

                particlesPlaced = particlesPlaced+len(np.array(outputMPI)[:,0:3])        

                for x in range(len(nodeMPI)):

                    # Store placed particles from this increment
                    internalNodes[particlesPlaced+x,:] = nodeMPI[x,:]

                    # Obtain extents for floating bin for node to test
                    binMin = np.array(([nodeMPI[x,0]-diameter[x]/2-maxPar/2-parOffset,\
                        nodeMPI[x,1]-diameter[x]/2-maxPar/2-parOffset,nodeMPI[x,2]-\
                        diameter[x]/2-maxPar/2-parOffset]))
                    binMax = np.array(([nodeMPI[x,0]+diameter[x]/2+maxPar/2+parOffset,\
                        nodeMPI[x,1]+diameter[x]/2+maxPar/2+parOffset,nodeMPI[x,2]+\
                        diameter[x]/2+maxPar/2+parOffset]))

                    # Check if particle overlapping any just added particles (ignore first one placed)
                    if x > 0:

                        overlap = check_particleOverlapMPI(nodeMPI[x,:],diameter[x],binMin,\
                            binMax,minPar,parOffset,nodeMPI[0:x],diameter[0:x])

                        if overlap == True:

                            [newMaxIter,node,iterReq] = gen_particle(surfaceNodes,\
                                parDiameterList[particlesPlaced+x], meshVertices, \
                                meshTets,newMaxIter,maxIter,minPar,\
                                maxPar,parOffset,parDiameterList,coord1,coord2,coord3,coord4,maxEdgeLength,max_dist,internalNodes)
                            
                            internalNodes[particlesPlaced+x,:] = node[0,:]


                self.form[4].progressBar.setValue(95*((x)/len(parDiameterList))+6) 
                self.form[4].statusWindow.setText("Status: Placing particles into geometry. (" + str(x) + '/' + str(len(parDiameterList)) + ')')


        # Generate particles for length of needed aggregate (not placed via MPI)
        for x in range(particlesPlaced,len(parDiameterList)):

            # Generate particle
            [newMaxIter,node,iterReq] = gen_particle(surfaceNodes,parDiameterList[x],meshVertices,meshTets,newMaxIter,maxIter,minPar,maxPar,\
                parOffset,parDiameterList,coord1,coord2,coord3,coord4,maxEdgeLength,max_dist,internalNodes)

            # Update progress bar every 1% of placement
            if x % np.rint(len(parDiameterList)/100) == 0:
                self.form[4].progressBar.setValue(80*((x)/len(parDiameterList))+6) 

            if len(parDiameterList)<=1000:
                # Update number particles placed every 1%
                if x % np.rint(len(parDiameterList)/100) == 0:
                    self.form[4].statusWindow.setText("Status: Placing particles into geometry. (" + str(x) + '/' + str(len(parDiameterList)) + ')')
            elif len(parDiameterList)<=10000:
                # Update number particles placed every 0.1%
                if x % np.rint(len(parDiameterList)/1000) == 0:
                    self.form[4].statusWindow.setText("Status: Placing particles into geometry. (" + str(x) + '/' + str(len(parDiameterList)) + ')')
            else:
                # Update number particles placed every 0.01%
                if x % np.rint(len(parDiameterList)/10000) == 0:
                    self.form[4].statusWindow.setText("Status: Placing particles into geometry. (" + str(x) + '/' + str(len(parDiameterList)) + ')')

            internalNodes[x,:] = node

        self.form[4].statusWindow.setText("Status: Placing particles into geometry. (" + str(len(parDiameterList)) + '/' + str(len(parDiameterList)) + ')')


        materialList = np.ones(len(parDiameterList))




        ########################## End Placing Particles ##############################







    ########################## Begin Tetrahedralization and Tesselation ##############################





    self.form[4].progressBar.setValue(95) 







    self.form[4].progressBar.setValue(98) 






    App.activeDocument().addObject('App::DocumentObjectGroup',dataFilesName)
    App.activeDocument().getObject(dataFilesName).Label = 'Data Files'

    App.activeDocument().addObject('App::DocumentObjectGroup',visualFilesName)
    App.activeDocument().getObject(visualFilesName).Label = 'Visualization Files'




    App.getDocument(App.ActiveDocument.Name).getObject(analysisName).addObject(App.getDocument(App.ActiveDocument.Name).getObject(dataFilesName))
    App.getDocument(App.ActiveDocument.Name).getObject(analysisName).addObject(App.getDocument(App.ActiveDocument.Name).getObject(visualFilesName))


    # If data files requested, generate them

    self.form[4].statusWindow.setText("Status: Writing node data file.")

    mkData_nodes(geoName,tempPath,internalNodes)


    self.form[4].statusWindow.setText("Status: Writing surface mesh file.")

    mkData_surfMesh(surfaceNodes,surfaceFaces,geoName,tempPath)


    self.form[4].statusWindow.setText("Status: Writing particle data file.")

    # If data files requested, generate Particle Data File
    mkData_particles(internalNodes,parDiameterList,geoName,tempPath)


    # If visuals requested, generate them

    self.form[4].statusWindow.setText("Status: Writing visualization files.")

    # If visuals requested, generate Particle VTK File
    mkVtk_particles(internalNodes,parDiameterList,materialList,geoName,tempPath)



    i = 0
    # Use single names for geoTypes
    if geoType in ["Box","Cylinder","Cone","Sphere","Ellipsoid","Prism","Dogbone","Custom"]:
        geoTypeOutName = geoType
    elif geoType == "Truncated Cone":
        geoTypeOutName = "TruncatedCone"
    elif geoType == "Notched Prism - Semi Circle":
        geoTypeOutName = "NotchedPrismSemiCircle"
    elif geoType == "Notched Prism - Square":
        geoTypeOutName = "NotchedPrismSquare"
    elif geoType == "Notched Prism - Ellipse":
        geoTypeOutName = "NotchedPrismEllipse"
    elif geoType == "Import CAD or Mesh":
        geoTypeOutName = "ImportedFile"

    outName = '/' + geoName + geoTypeOutName + str(i).zfill(3)
    while os.path.isdir(Path(outDir + outName)):
        i = i+1
        outName = '/' + geoName + geoTypeOutName + str(i).zfill(3)


    # Move files to selected output directory
    print('Moving files.')
    shutil.move(tempPath, outDir + outName)


    print("Generated files written to: " + str(Path(outDir + outName)))






    # Set linked object for node data file
    nodesData = App.ActiveDocument.addObject("Part::FeaturePython", "nodesData")
    #nodesData.ViewObject.Proxy = IconViewProviderToFile(nodesData,os.path.join(ICONPATH,'FEMMeshICON.svg'))
    App.getDocument(App.ActiveDocument.Name).getObject(dataFilesName).addObject(nodesData)
    nodesData.addProperty("App::PropertyFile",'Location','Node Data File','Location of node data file').Location=str(Path(outDir + outName + '/' + geoName + '-data-nodes.dat'))
    
    # Set linked object for node data file
    particlesData = App.ActiveDocument.addObject("Part::FeaturePython", "particlesData")
    #particlesData.ViewObject.Proxy = IconViewProviderToFile(particlesData,os.path.join(ICONPATH,'FEMMeshICON.svg'))
    App.getDocument(App.ActiveDocument.Name).getObject(dataFilesName).addObject(particlesData)
    particlesData.addProperty("App::PropertyFile",'Location','Particle Data File','Location of particle data file').Location=str(Path(outDir + outName + '/' + geoName + '-data-particles.dat'))
    

 
    # Import back the Particles VTK file
    feminout.importVTKResults.insert(str(Path(outDir + outName + '/' + geoName + '-para-particles.000.vtk')),App.ActiveDocument.Name)
    SPHDEMimport = geoName + '_para_particles_000'




    Gui.getDocument(App.ActiveDocument.Name).getObject(SPHDEMimport).DisplayMode = u"Nodes"
    Gui.getDocument(App.ActiveDocument.Name).getObject(SPHDEMimport).Field = u"Diameter"
    App.getDocument(App.ActiveDocument.Name).getObject(visualFilesName).addObject(App.getDocument(App.ActiveDocument.Name).getObject(SPHDEMimport))
    App.getDocument(App.ActiveDocument.Name).getObject(SPHDEMimport).Label = "particlesVTK"





    # Set visualization properties for geometry
    Gui.getDocument(App.ActiveDocument.Name).getObject(geoName).Transparency = 95
    Gui.getDocument(App.ActiveDocument.Name).getObject(geoName).DrawStyle = u"Dashed"

    # Remove mesh object
    App.getDocument(App.ActiveDocument.Name).removeObject(meshName)





    simProps = [\
        "TotalTime",\
        "TimestepSize",\
        "NumberOfThreads",\
        "NumberOutputSteps",\
        ]




    simPropDesc = [\
        "Description coming soon...",\
        "Description coming soon...",\
        "Description coming soon...",\
        "Description coming soon...",\
        ]







    # Add appropriate simulation properties
    for x in range(len(simProps)):
        App.getDocument(App.ActiveDocument.Name).getObject(analysisName).addProperty("App::PropertyFloat",simProps[x],"Simulation",simPropDesc[x])#.Density=0.25
    App.getDocument(App.ActiveDocument.Name).getObject(analysisName).addProperty("App::PropertyEnumeration","Solver","Simulation","Solver software").Solver=['Project Chrono']
    App.getDocument(App.ActiveDocument.Name).getObject(analysisName).addProperty("App::PropertyEnumeration","IntegrationScheme","Simulation","Integrator type").IntegrationScheme=['Explicit']






    self.form[4].progressBar.setValue(100) 

    # Display sieve curve data
    mkDisp_sieveCurves(volFracPar, tetVolume, minPar, maxPar,fullerCoef,sieveCurveDiameter,sieveCurvePassing,parDiameterList)

    # Switch back to model window
    mw=Gui.getMainWindow()
    mdi=mw.findChild(QtWidgets.QMdiArea)
    mdi.activatePreviousSubWindow()

    # Switch to FEM GUI
    App.ActiveDocument.recompute()



    Gui.Control.closeDialog()
    Gui.activateWorkbench("FemWorkbench")
    FemGui.setActiveAnalysis(App.activeDocument().getObject(analysisName))
    





