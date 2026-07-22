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
## This file contains the function to read the inputs from the GUI and return
## them to the main script.
##
## ===========================================================================


def read_SPHDEM_inputs(form):

    # Basic Settings
    setupFile           = form[0].setupFile.text()


    # Simulation Settings
    numCPU              = form[0].numCPUbox.value()
    numIncrements       = form[0].numPIncBox.value()
    maxIter             = form[0].numIncBox.value()
    placementAlg        = form[0].placementAlg.currentText()

    # Geometry Settings
    geoType             = form[1].geometryType.currentText()
    dimensions = []
    if geoType == "Truncated Cone":
        dimensions.append(form[1].truncConeHeight.text())
        dimensions.append(form[1].truncConeRadBot.text())
        dimensions.append(form[1].truncConeRadTop.text())
    if geoType == "Box":
        dimensions.append(form[1].boxLength.text())
        dimensions.append(form[1].boxWidth.text())
        dimensions.append(form[1].boxHeight.text())
    if geoType == "Cylinder":
        dimensions.append(form[1].cylinderHeight.text())
        dimensions.append(form[1].cylinderRadius.text())
    if geoType == "Cone":
        dimensions.append(form[1].coneHeight.text())
        dimensions.append(form[1].coneRadius1.text())
        dimensions.append("0 mm")
    if geoType == "Prism":
        dimensions.append(form[1].prismCircumradius.text())
        dimensions.append(form[1].prismHeight.text())
        dimensions.append(form[1].prismPolygon.text())
    if geoType == "Dogbone":
        dimensions.append(form[1].dogboneLength.text())
        dimensions.append(form[1].dogboneWidth.text())
        dimensions.append(form[1].dogboneThickness.text())
        dimensions.append(form[1].gaugeLength.text())
        dimensions.append(form[1].gaugeWidth.text())
        dimensions.append(form[1].dogboneType.currentText())        
    cadFile             = form[1].cadFile.toPlainText()

    # Particle Settings
    minPar              = float(form[2].minPar.value() or 0)
    maxPar              = float(form[2].maxPar.value() or 0)      
    fullerCoef          = float(form[2].fullerCoef.value() or 0)  
    sieveCurveDiameter  = form[2].sieveDiameters.text()        
    sieveCurvePassing   = form[2].sievePassing.text()   
    minDistCoef         = float(form[2].minDistCoef.value() or 0)

    # Mix Design
    wcRatio             = float(form[3].wcRatio.value() or 0)
    densityWater        = float(form[3].waterDensity.text() or 0)
    cementC             = float(form[3].cementContent.text() or 0)
    flyashC             = float(form[3].flyashContent.text() or 0)
    silicaC             = float(form[3].silicaContent.text() or 0)
    scmC                = float(form[3].scmContent.text() or 0)
    fillerC             = 0.0
    cementDensity       = float(form[3].cementDensity.text() or 0)
    flyashDensity       = float(form[3].flyashDensity.text() or 0)
    silicaDensity       = float(form[3].silicaDensity.text() or 0)
    scmDensity          = float(form[3].scmDensity.text() or 0)
    fillerDensity       = 0.0
    airFrac1            = float(form[3].airFrac.value() or 0)
    airFrac2            = 0.0

    # Generation Data
    outputDir           = form[4].outputDir.text()
    modelType           = form[4].modelType.currentText()

    return setupFile, \
        numCPU, numIncrements,maxIter,placementAlg,\
        geoType, dimensions, cadFile,\
        minPar, maxPar, fullerCoef, sieveCurveDiameter, sieveCurvePassing, minDistCoef,\
        wcRatio, densityWater, cementC, flyashC, silicaC, scmC,\
        cementDensity, flyashDensity, silicaDensity, scmDensity, airFrac1, \
        fillerC, fillerDensity, airFrac2,\
        outputDir, modelType