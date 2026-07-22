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
## Function to generate a Python script for visualizing a single tetrahedron in
## Paraview
##
## ===========================================================================

from pathlib import Path


def mkPy_LDPM_singleDebugParaview(geoName, outDir, outName, tempPath):


    
    # Generate VTK file for visualizing particles
    with open(Path(tempPath + geoName + \
        '-paraview.py'),"w") as output_file:                                       


        output_file.write("""
#### import the simple module from the paraview
from paraview.simple import *
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()
        \n""")
                          

        path4 = str(Path(outDir + outName + "\\" + geoName + '-para-mesh.000.vtk\''))
        path4 = path4.replace("\\", "\\\\")
        path5 = str(Path(outDir + outName + "\\" + geoName + '-para-facets.000.vtk\''))
        path5 = path5.replace("\\", "\\\\")
        path6 = str(Path(outDir + outName + "\\" + geoName + '-para-particles.000.vtk\''))
        path6 = path6.replace("\\", "\\\\")



        output_file.write('lDPMgeo000paraTet000vtk = LegacyVTKReader(registrationName=\'' + geoName + '-para-mesh.000.vtk\', FileNames=[\'' + path4 + '])\n')
        output_file.write('lDPMgeo000paraTetFacets000vtk = LegacyVTKReader(registrationName=\'' + geoName + '-para-facets.000.vtk\', FileNames=[\'' + path5 + '])\n')
        output_file.write('lDPMgeo000paraTetParticles000vtk = LegacyVTKReader(registrationName=\'' + geoName + '-para-particles.000.vtk\', FileNames=[\'' + path6 + '])\n')



        output_file.write("""
# get active view
renderView1 = GetActiveViewOrCreate('RenderView')


# reset view to fit data
renderView1.ResetCamera(False)

# get the material library
materialLibrary1 = GetMaterialLibrary()


# show data in view
lDPMgeo000paraTet000vtkDisplay = Show(lDPMgeo000paraTet000vtk, renderView1, 'UnstructuredGridRepresentation')

# trace defaults for the display properties.
lDPMgeo000paraTet000vtkDisplay.Selection = None
lDPMgeo000paraTet000vtkDisplay.Representation = 'Surface'
lDPMgeo000paraTet000vtkDisplay.ColorArrayName = [None, '']
lDPMgeo000paraTet000vtkDisplay.LookupTable = None
lDPMgeo000paraTet000vtkDisplay.MapScalars = 1
lDPMgeo000paraTet000vtkDisplay.MultiComponentsMapping = 0
lDPMgeo000paraTet000vtkDisplay.InterpolateScalarsBeforeMapping = 1
lDPMgeo000paraTet000vtkDisplay.Opacity = 1.0
lDPMgeo000paraTet000vtkDisplay.PointSize = 2.0
lDPMgeo000paraTet000vtkDisplay.LineWidth = 1.0
lDPMgeo000paraTet000vtkDisplay.RenderLinesAsTubes = 0
lDPMgeo000paraTet000vtkDisplay.RenderPointsAsSpheres = 0
lDPMgeo000paraTet000vtkDisplay.Interpolation = 'Gouraud'
lDPMgeo000paraTet000vtkDisplay.Specular = 0.0
lDPMgeo000paraTet000vtkDisplay.SpecularColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTet000vtkDisplay.SpecularPower = 100.0
lDPMgeo000paraTet000vtkDisplay.Luminosity = 0.0
lDPMgeo000paraTet000vtkDisplay.Ambient = 0.0
lDPMgeo000paraTet000vtkDisplay.Diffuse = 1.0
lDPMgeo000paraTet000vtkDisplay.Roughness = 0.3
lDPMgeo000paraTet000vtkDisplay.Metallic = 0.0
lDPMgeo000paraTet000vtkDisplay.EdgeTint = [1.0, 1.0, 1.0]
lDPMgeo000paraTet000vtkDisplay.Anisotropy = 0.0
lDPMgeo000paraTet000vtkDisplay.AnisotropyRotation = 0.0
lDPMgeo000paraTet000vtkDisplay.BaseIOR = 1.5
lDPMgeo000paraTet000vtkDisplay.CoatStrength = 0.0
lDPMgeo000paraTet000vtkDisplay.CoatIOR = 2.0
lDPMgeo000paraTet000vtkDisplay.CoatRoughness = 0.0
lDPMgeo000paraTet000vtkDisplay.CoatColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTet000vtkDisplay.SelectTCoordArray = 'None'
lDPMgeo000paraTet000vtkDisplay.SelectNormalArray = 'None'
lDPMgeo000paraTet000vtkDisplay.SelectTangentArray = 'None'
lDPMgeo000paraTet000vtkDisplay.Texture = None
lDPMgeo000paraTet000vtkDisplay.RepeatTextures = 1
lDPMgeo000paraTet000vtkDisplay.InterpolateTextures = 0
lDPMgeo000paraTet000vtkDisplay.SeamlessU = 0
lDPMgeo000paraTet000vtkDisplay.SeamlessV = 0
lDPMgeo000paraTet000vtkDisplay.UseMipmapTextures = 0
lDPMgeo000paraTet000vtkDisplay.ShowTexturesOnBackface = 1
lDPMgeo000paraTet000vtkDisplay.BaseColorTexture = None
lDPMgeo000paraTet000vtkDisplay.NormalTexture = None
lDPMgeo000paraTet000vtkDisplay.NormalScale = 1.0
lDPMgeo000paraTet000vtkDisplay.CoatNormalTexture = None
lDPMgeo000paraTet000vtkDisplay.CoatNormalScale = 1.0
lDPMgeo000paraTet000vtkDisplay.MaterialTexture = None
lDPMgeo000paraTet000vtkDisplay.OcclusionStrength = 1.0
lDPMgeo000paraTet000vtkDisplay.AnisotropyTexture = None
lDPMgeo000paraTet000vtkDisplay.EmissiveTexture = None
lDPMgeo000paraTet000vtkDisplay.EmissiveFactor = [1.0, 1.0, 1.0]
lDPMgeo000paraTet000vtkDisplay.FlipTextures = 0
lDPMgeo000paraTet000vtkDisplay.BackfaceRepresentation = 'Follow Frontface'
lDPMgeo000paraTet000vtkDisplay.BackfaceAmbientColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTet000vtkDisplay.BackfaceOpacity = 1.0
lDPMgeo000paraTet000vtkDisplay.Position = [0.0, 0.0, 0.0]
lDPMgeo000paraTet000vtkDisplay.Scale = [1.0, 1.0, 1.0]
lDPMgeo000paraTet000vtkDisplay.Orientation = [0.0, 0.0, 0.0]
lDPMgeo000paraTet000vtkDisplay.Origin = [0.0, 0.0, 0.0]
lDPMgeo000paraTet000vtkDisplay.CoordinateShiftScaleMethod = 'Always Auto Shift Scale'
lDPMgeo000paraTet000vtkDisplay.Pickable = 1
lDPMgeo000paraTet000vtkDisplay.Triangulate = 0
lDPMgeo000paraTet000vtkDisplay.UseShaderReplacements = 0
lDPMgeo000paraTet000vtkDisplay.ShaderReplacements = ''
lDPMgeo000paraTet000vtkDisplay.NonlinearSubdivisionLevel = 1
lDPMgeo000paraTet000vtkDisplay.UseDataPartitions = 0
lDPMgeo000paraTet000vtkDisplay.OSPRayUseScaleArray = 'All Approximate'
lDPMgeo000paraTet000vtkDisplay.OSPRayScaleArray = ''
lDPMgeo000paraTet000vtkDisplay.OSPRayScaleFunction = 'PiecewiseFunction'
lDPMgeo000paraTet000vtkDisplay.OSPRayMaterial = 'None'
lDPMgeo000paraTet000vtkDisplay.BlockSelectors = ['/']
lDPMgeo000paraTet000vtkDisplay.BlockColors = []
lDPMgeo000paraTet000vtkDisplay.BlockOpacities = []
lDPMgeo000paraTet000vtkDisplay.Orient = 0
lDPMgeo000paraTet000vtkDisplay.OrientationMode = 'Direction'
lDPMgeo000paraTet000vtkDisplay.SelectOrientationVectors = 'None'
lDPMgeo000paraTet000vtkDisplay.Scaling = 0
lDPMgeo000paraTet000vtkDisplay.ScaleMode = 'No Data Scaling Off'
lDPMgeo000paraTet000vtkDisplay.ScaleFactor = 0.6963770329408047
lDPMgeo000paraTet000vtkDisplay.SelectScaleArray = 'None'
lDPMgeo000paraTet000vtkDisplay.GlyphType = 'Arrow'
lDPMgeo000paraTet000vtkDisplay.UseGlyphTable = 0
lDPMgeo000paraTet000vtkDisplay.GlyphTableIndexArray = 'None'
lDPMgeo000paraTet000vtkDisplay.UseCompositeGlyphTable = 0
lDPMgeo000paraTet000vtkDisplay.UseGlyphCullingAndLOD = 0
lDPMgeo000paraTet000vtkDisplay.LODValues = []
lDPMgeo000paraTet000vtkDisplay.ColorByLODIndex = 0
lDPMgeo000paraTet000vtkDisplay.GaussianRadius = 0.03481885164704023
lDPMgeo000paraTet000vtkDisplay.ShaderPreset = 'Sphere'
lDPMgeo000paraTet000vtkDisplay.CustomTriangleScale = 3
lDPMgeo000paraTet000vtkDisplay.Emissive = 0
lDPMgeo000paraTet000vtkDisplay.ScaleByArray = 0
lDPMgeo000paraTet000vtkDisplay.SetScaleArray = [None, '']
lDPMgeo000paraTet000vtkDisplay.ScaleArrayComponent = 0
lDPMgeo000paraTet000vtkDisplay.UseScaleFunction = 1
lDPMgeo000paraTet000vtkDisplay.ScaleTransferFunction = 'PiecewiseFunction'
lDPMgeo000paraTet000vtkDisplay.OpacityByArray = 0
lDPMgeo000paraTet000vtkDisplay.OpacityArray = [None, '']
lDPMgeo000paraTet000vtkDisplay.OpacityArrayComponent = 0
lDPMgeo000paraTet000vtkDisplay.OpacityTransferFunction = 'PiecewiseFunction'
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid = 'GridAxesRepresentation'
lDPMgeo000paraTet000vtkDisplay.SelectionCellLabelBold = 0
lDPMgeo000paraTet000vtkDisplay.SelectionCellLabelColor = [0.0, 1.0, 0.0]
lDPMgeo000paraTet000vtkDisplay.SelectionCellLabelFontFamily = 'Arial'
lDPMgeo000paraTet000vtkDisplay.SelectionCellLabelFontFile = ''
lDPMgeo000paraTet000vtkDisplay.SelectionCellLabelFontSize = 18
lDPMgeo000paraTet000vtkDisplay.SelectionCellLabelItalic = 0
lDPMgeo000paraTet000vtkDisplay.SelectionCellLabelJustification = 'Left'
lDPMgeo000paraTet000vtkDisplay.SelectionCellLabelOpacity = 1.0
lDPMgeo000paraTet000vtkDisplay.SelectionCellLabelShadow = 0
lDPMgeo000paraTet000vtkDisplay.SelectionPointLabelBold = 0
lDPMgeo000paraTet000vtkDisplay.SelectionPointLabelColor = [1.0, 1.0, 0.0]
lDPMgeo000paraTet000vtkDisplay.SelectionPointLabelFontFamily = 'Arial'
lDPMgeo000paraTet000vtkDisplay.SelectionPointLabelFontFile = ''
lDPMgeo000paraTet000vtkDisplay.SelectionPointLabelFontSize = 18
lDPMgeo000paraTet000vtkDisplay.SelectionPointLabelItalic = 0
lDPMgeo000paraTet000vtkDisplay.SelectionPointLabelJustification = 'Left'
lDPMgeo000paraTet000vtkDisplay.SelectionPointLabelOpacity = 1.0
lDPMgeo000paraTet000vtkDisplay.SelectionPointLabelShadow = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes = 'PolarAxesRepresentation'
lDPMgeo000paraTet000vtkDisplay.ScalarOpacityFunction = None
lDPMgeo000paraTet000vtkDisplay.ScalarOpacityUnitDistance = 11.056155192466099
lDPMgeo000paraTet000vtkDisplay.UseSeparateOpacityArray = 0
lDPMgeo000paraTet000vtkDisplay.OpacityArrayName = [None, '']
lDPMgeo000paraTet000vtkDisplay.OpacityComponent = 0
lDPMgeo000paraTet000vtkDisplay.SelectMapper = 'Projected tetra'
lDPMgeo000paraTet000vtkDisplay.SamplingDimensions = [128, 128, 128]
lDPMgeo000paraTet000vtkDisplay.UseFloatingPointFrameBuffer = 1
lDPMgeo000paraTet000vtkDisplay.SelectInputVectors = [None, '']
lDPMgeo000paraTet000vtkDisplay.NumberOfSteps = 40
lDPMgeo000paraTet000vtkDisplay.StepSize = 0.25
lDPMgeo000paraTet000vtkDisplay.NormalizeVectors = 1
lDPMgeo000paraTet000vtkDisplay.EnhancedLIC = 1
lDPMgeo000paraTet000vtkDisplay.ColorMode = 'Blend'
lDPMgeo000paraTet000vtkDisplay.LICIntensity = 0.8
lDPMgeo000paraTet000vtkDisplay.MapModeBias = 0.0
lDPMgeo000paraTet000vtkDisplay.EnhanceContrast = 'Off'
lDPMgeo000paraTet000vtkDisplay.LowLICContrastEnhancementFactor = 0.0
lDPMgeo000paraTet000vtkDisplay.HighLICContrastEnhancementFactor = 0.0
lDPMgeo000paraTet000vtkDisplay.LowColorContrastEnhancementFactor = 0.0
lDPMgeo000paraTet000vtkDisplay.HighColorContrastEnhancementFactor = 0.0
lDPMgeo000paraTet000vtkDisplay.AntiAlias = 0
lDPMgeo000paraTet000vtkDisplay.MaskOnSurface = 1
lDPMgeo000paraTet000vtkDisplay.MaskThreshold = 0.0
lDPMgeo000paraTet000vtkDisplay.MaskIntensity = 0.0
lDPMgeo000paraTet000vtkDisplay.MaskColor = [0.5, 0.5, 0.5]
lDPMgeo000paraTet000vtkDisplay.GenerateNoiseTexture = 0
lDPMgeo000paraTet000vtkDisplay.NoiseType = 'Gaussian'
lDPMgeo000paraTet000vtkDisplay.NoiseTextureSize = 128
lDPMgeo000paraTet000vtkDisplay.NoiseGrainSize = 2
lDPMgeo000paraTet000vtkDisplay.MinNoiseValue = 0.0
lDPMgeo000paraTet000vtkDisplay.MaxNoiseValue = 0.8
lDPMgeo000paraTet000vtkDisplay.NumberOfNoiseLevels = 1024
lDPMgeo000paraTet000vtkDisplay.ImpulseNoiseProbability = 1.0
lDPMgeo000paraTet000vtkDisplay.ImpulseNoiseBackgroundValue = 0.0
lDPMgeo000paraTet000vtkDisplay.NoiseGeneratorSeed = 1
lDPMgeo000paraTet000vtkDisplay.CompositeStrategy = 'AUTO'
lDPMgeo000paraTet000vtkDisplay.UseLICForLOD = 0
lDPMgeo000paraTet000vtkDisplay.WriteLog = ''

# init the 'PiecewiseFunction' selected for 'OSPRayScaleFunction'
lDPMgeo000paraTet000vtkDisplay.OSPRayScaleFunction.Points = [0.0, 0.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0]
lDPMgeo000paraTet000vtkDisplay.OSPRayScaleFunction.UseLogScale = 0

# init the 'Arrow' selected for 'GlyphType'
lDPMgeo000paraTet000vtkDisplay.GlyphType.TipResolution = 20
lDPMgeo000paraTet000vtkDisplay.GlyphType.TipRadius = 0.1
lDPMgeo000paraTet000vtkDisplay.GlyphType.TipLength = 0.35
lDPMgeo000paraTet000vtkDisplay.GlyphType.ShaftResolution = 20
lDPMgeo000paraTet000vtkDisplay.GlyphType.ShaftRadius = 0.03
lDPMgeo000paraTet000vtkDisplay.GlyphType.Invert = 0

# init the 'PiecewiseFunction' selected for 'ScaleTransferFunction'
lDPMgeo000paraTet000vtkDisplay.ScaleTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0]
lDPMgeo000paraTet000vtkDisplay.ScaleTransferFunction.UseLogScale = 0

# init the 'PiecewiseFunction' selected for 'OpacityTransferFunction'
lDPMgeo000paraTet000vtkDisplay.OpacityTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0]
lDPMgeo000paraTet000vtkDisplay.OpacityTransferFunction.UseLogScale = 0

# init the 'GridAxesRepresentation' selected for 'DataAxesGrid'
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XTitle = 'X Axis'
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YTitle = 'Y Axis'
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZTitle = 'Z Axis'
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XTitleFontFamily = 'Arial'
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XTitleFontFile = ''
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XTitleBold = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XTitleItalic = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XTitleFontSize = 12
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XTitleShadow = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XTitleOpacity = 1.0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YTitleFontFamily = 'Arial'
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YTitleFontFile = ''
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YTitleBold = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YTitleItalic = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YTitleFontSize = 12
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YTitleShadow = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YTitleOpacity = 1.0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZTitleFontFamily = 'Arial'
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZTitleFontFile = ''
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZTitleBold = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZTitleItalic = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZTitleFontSize = 12
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZTitleShadow = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZTitleOpacity = 1.0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.FacesToRender = 63
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.CullBackface = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.CullFrontface = 1
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ShowGrid = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ShowEdges = 1
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ShowTicks = 1
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.LabelUniqueEdgesOnly = 1
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.AxesToLabel = 63
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XLabelFontFamily = 'Arial'
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XLabelFontFile = ''
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XLabelBold = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XLabelItalic = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XLabelFontSize = 12
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XLabelShadow = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XLabelOpacity = 1.0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YLabelFontFamily = 'Arial'
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YLabelFontFile = ''
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YLabelBold = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YLabelItalic = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YLabelFontSize = 12
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YLabelShadow = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YLabelOpacity = 1.0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZLabelFontFamily = 'Arial'
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZLabelFontFile = ''
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZLabelBold = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZLabelItalic = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZLabelFontSize = 12
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZLabelShadow = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZLabelOpacity = 1.0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XAxisNotation = 'Mixed'
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XAxisPrecision = 2
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XAxisUseCustomLabels = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.XAxisLabels = []
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YAxisNotation = 'Mixed'
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YAxisPrecision = 2
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YAxisUseCustomLabels = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.YAxisLabels = []
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZAxisNotation = 'Mixed'
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZAxisPrecision = 2
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZAxisUseCustomLabels = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.ZAxisLabels = []
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.UseCustomBounds = 0
lDPMgeo000paraTet000vtkDisplay.DataAxesGrid.CustomBounds = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]

# init the 'PolarAxesRepresentation' selected for 'PolarAxes'
lDPMgeo000paraTet000vtkDisplay.PolarAxes.Visibility = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.Translation = [0.0, 0.0, 0.0]
lDPMgeo000paraTet000vtkDisplay.PolarAxes.Scale = [1.0, 1.0, 1.0]
lDPMgeo000paraTet000vtkDisplay.PolarAxes.Orientation = [0.0, 0.0, 0.0]
lDPMgeo000paraTet000vtkDisplay.PolarAxes.EnableCustomBounds = [0, 0, 0]
lDPMgeo000paraTet000vtkDisplay.PolarAxes.CustomBounds = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
lDPMgeo000paraTet000vtkDisplay.PolarAxes.EnableCustomRange = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.CustomRange = [0.0, 1.0]
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisVisibility = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.RadialAxesVisibility = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.DrawRadialGridlines = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarArcsVisibility = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.DrawPolarArcsGridlines = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.NumberOfRadialAxes = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.AutoSubdividePolarAxis = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.NumberOfPolarAxis = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.MinimumRadius = 0.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.MinimumAngle = 0.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.MaximumAngle = 90.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.RadialAxesOriginToPolarAxis = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.Ratio = 1.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarArcsColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTet000vtkDisplay.PolarAxes.LastRadialAxisColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTet000vtkDisplay.PolarAxes.SecondaryPolarArcsColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTet000vtkDisplay.PolarAxes.SecondaryRadialAxesColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisTitleVisibility = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisTitle = 'Radial Distance'
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisTitleLocation = 'Bottom'
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarLabelVisibility = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarLabelExponentLocation = 'Labels'
lDPMgeo000paraTet000vtkDisplay.PolarAxes.RadialLabelVisibility = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.RadialLabelLocation = 'Bottom'
lDPMgeo000paraTet000vtkDisplay.PolarAxes.RadialUnitsVisibility = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.ScreenSize = 10.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisTitleOpacity = 1.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisTitleFontFamily = 'Arial'
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisTitleFontFile = ''
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisTitleBold = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisTitleItalic = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisTitleShadow = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisTitleFontSize = 12
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisLabelOpacity = 1.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisLabelFontFamily = 'Arial'
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisLabelFontFile = ''
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisLabelBold = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisLabelItalic = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisLabelShadow = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisLabelFontSize = 12
lDPMgeo000paraTet000vtkDisplay.PolarAxes.LastRadialAxisTextOpacity = 1.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.LastRadialAxisTextFontFamily = 'Arial'
lDPMgeo000paraTet000vtkDisplay.PolarAxes.LastRadialAxisTextFontFile = ''
lDPMgeo000paraTet000vtkDisplay.PolarAxes.LastRadialAxisTextBold = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.LastRadialAxisTextItalic = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.LastRadialAxisTextShadow = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.LastRadialAxisTextFontSize = 12
lDPMgeo000paraTet000vtkDisplay.PolarAxes.SecondaryRadialAxesTextOpacity = 1.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.SecondaryRadialAxesTextFontFamily = 'Arial'
lDPMgeo000paraTet000vtkDisplay.PolarAxes.SecondaryRadialAxesTextFontFile = ''
lDPMgeo000paraTet000vtkDisplay.PolarAxes.SecondaryRadialAxesTextBold = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.SecondaryRadialAxesTextItalic = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.SecondaryRadialAxesTextShadow = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.SecondaryRadialAxesTextFontSize = 12
lDPMgeo000paraTet000vtkDisplay.PolarAxes.EnableDistanceLOD = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.DistanceLODThreshold = 0.7
lDPMgeo000paraTet000vtkDisplay.PolarAxes.EnableViewAngleLOD = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.ViewAngleLODThreshold = 0.7
lDPMgeo000paraTet000vtkDisplay.PolarAxes.SmallestVisiblePolarAngle = 0.5
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarTicksVisibility = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.ArcTicksOriginToPolarAxis = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.TickLocation = 'Both'
lDPMgeo000paraTet000vtkDisplay.PolarAxes.AxisTickVisibility = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.AxisMinorTickVisibility = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.ArcTickVisibility = 1
lDPMgeo000paraTet000vtkDisplay.PolarAxes.ArcMinorTickVisibility = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.DeltaAngleMajor = 10.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.DeltaAngleMinor = 5.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisMajorTickSize = 0.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisTickRatioSize = 0.3
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisMajorTickThickness = 1.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.PolarAxisTickRatioThickness = 0.5
lDPMgeo000paraTet000vtkDisplay.PolarAxes.LastRadialAxisMajorTickSize = 0.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.LastRadialAxisTickRatioSize = 0.3
lDPMgeo000paraTet000vtkDisplay.PolarAxes.LastRadialAxisMajorTickThickness = 1.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.LastRadialAxisTickRatioThickness = 0.5
lDPMgeo000paraTet000vtkDisplay.PolarAxes.ArcMajorTickSize = 0.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.ArcTickRatioSize = 0.3
lDPMgeo000paraTet000vtkDisplay.PolarAxes.ArcMajorTickThickness = 1.0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.ArcTickRatioThickness = 0.5
lDPMgeo000paraTet000vtkDisplay.PolarAxes.Use2DMode = 0
lDPMgeo000paraTet000vtkDisplay.PolarAxes.UseLogAxis = 0

# show data in view
lDPMgeo000paraTetFacets000vtkDisplay = Show(lDPMgeo000paraTetFacets000vtk, renderView1, 'GeometryRepresentation')

# trace defaults for the display properties.
lDPMgeo000paraTetFacets000vtkDisplay.Selection = None
lDPMgeo000paraTetFacets000vtkDisplay.Representation = 'Surface'
lDPMgeo000paraTetFacets000vtkDisplay.ColorArrayName = [None, '']
lDPMgeo000paraTetFacets000vtkDisplay.LookupTable = None
lDPMgeo000paraTetFacets000vtkDisplay.MapScalars = 1
lDPMgeo000paraTetFacets000vtkDisplay.MultiComponentsMapping = 0
lDPMgeo000paraTetFacets000vtkDisplay.InterpolateScalarsBeforeMapping = 1
lDPMgeo000paraTetFacets000vtkDisplay.Opacity = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.PointSize = 2.0
lDPMgeo000paraTetFacets000vtkDisplay.LineWidth = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.RenderLinesAsTubes = 0
lDPMgeo000paraTetFacets000vtkDisplay.RenderPointsAsSpheres = 0
lDPMgeo000paraTetFacets000vtkDisplay.Interpolation = 'Gouraud'
lDPMgeo000paraTetFacets000vtkDisplay.Specular = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.SpecularColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetFacets000vtkDisplay.SpecularPower = 100.0
lDPMgeo000paraTetFacets000vtkDisplay.Luminosity = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.Ambient = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.Diffuse = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.Roughness = 0.3
lDPMgeo000paraTetFacets000vtkDisplay.Metallic = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.EdgeTint = [1.0, 1.0, 1.0]
lDPMgeo000paraTetFacets000vtkDisplay.Anisotropy = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.AnisotropyRotation = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.BaseIOR = 1.5
lDPMgeo000paraTetFacets000vtkDisplay.CoatStrength = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.CoatIOR = 2.0
lDPMgeo000paraTetFacets000vtkDisplay.CoatRoughness = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.CoatColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetFacets000vtkDisplay.SelectTCoordArray = 'None'
lDPMgeo000paraTetFacets000vtkDisplay.SelectNormalArray = 'None'
lDPMgeo000paraTetFacets000vtkDisplay.SelectTangentArray = 'None'
lDPMgeo000paraTetFacets000vtkDisplay.Texture = None
lDPMgeo000paraTetFacets000vtkDisplay.RepeatTextures = 1
lDPMgeo000paraTetFacets000vtkDisplay.InterpolateTextures = 0
lDPMgeo000paraTetFacets000vtkDisplay.SeamlessU = 0
lDPMgeo000paraTetFacets000vtkDisplay.SeamlessV = 0
lDPMgeo000paraTetFacets000vtkDisplay.UseMipmapTextures = 0
lDPMgeo000paraTetFacets000vtkDisplay.ShowTexturesOnBackface = 1
lDPMgeo000paraTetFacets000vtkDisplay.BaseColorTexture = None
lDPMgeo000paraTetFacets000vtkDisplay.NormalTexture = None
lDPMgeo000paraTetFacets000vtkDisplay.NormalScale = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.CoatNormalTexture = None
lDPMgeo000paraTetFacets000vtkDisplay.CoatNormalScale = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.MaterialTexture = None
lDPMgeo000paraTetFacets000vtkDisplay.OcclusionStrength = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.AnisotropyTexture = None
lDPMgeo000paraTetFacets000vtkDisplay.EmissiveTexture = None
lDPMgeo000paraTetFacets000vtkDisplay.EmissiveFactor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetFacets000vtkDisplay.FlipTextures = 0
lDPMgeo000paraTetFacets000vtkDisplay.BackfaceRepresentation = 'Follow Frontface'
lDPMgeo000paraTetFacets000vtkDisplay.BackfaceAmbientColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetFacets000vtkDisplay.BackfaceOpacity = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.Position = [0.0, 0.0, 0.0]
lDPMgeo000paraTetFacets000vtkDisplay.Scale = [1.0, 1.0, 1.0]
lDPMgeo000paraTetFacets000vtkDisplay.Orientation = [0.0, 0.0, 0.0]
lDPMgeo000paraTetFacets000vtkDisplay.Origin = [0.0, 0.0, 0.0]
lDPMgeo000paraTetFacets000vtkDisplay.CoordinateShiftScaleMethod = 'Always Auto Shift Scale'
lDPMgeo000paraTetFacets000vtkDisplay.Pickable = 1
lDPMgeo000paraTetFacets000vtkDisplay.Triangulate = 0
lDPMgeo000paraTetFacets000vtkDisplay.UseShaderReplacements = 0
lDPMgeo000paraTetFacets000vtkDisplay.ShaderReplacements = ''
lDPMgeo000paraTetFacets000vtkDisplay.NonlinearSubdivisionLevel = 1
lDPMgeo000paraTetFacets000vtkDisplay.UseDataPartitions = 0
lDPMgeo000paraTetFacets000vtkDisplay.OSPRayUseScaleArray = 'All Approximate'
lDPMgeo000paraTetFacets000vtkDisplay.OSPRayScaleArray = ''
lDPMgeo000paraTetFacets000vtkDisplay.OSPRayScaleFunction = 'PiecewiseFunction'
lDPMgeo000paraTetFacets000vtkDisplay.OSPRayMaterial = 'None'
lDPMgeo000paraTetFacets000vtkDisplay.BlockSelectors = ['/']
lDPMgeo000paraTetFacets000vtkDisplay.BlockColors = []
lDPMgeo000paraTetFacets000vtkDisplay.BlockOpacities = []
lDPMgeo000paraTetFacets000vtkDisplay.Orient = 0
lDPMgeo000paraTetFacets000vtkDisplay.OrientationMode = 'Direction'
lDPMgeo000paraTetFacets000vtkDisplay.SelectOrientationVectors = 'None'
lDPMgeo000paraTetFacets000vtkDisplay.Scaling = 0
lDPMgeo000paraTetFacets000vtkDisplay.ScaleMode = 'No Data Scaling Off'
lDPMgeo000paraTetFacets000vtkDisplay.ScaleFactor = 0.5189018249511719
lDPMgeo000paraTetFacets000vtkDisplay.SelectScaleArray = 'None'
lDPMgeo000paraTetFacets000vtkDisplay.GlyphType = 'Arrow'
lDPMgeo000paraTetFacets000vtkDisplay.UseGlyphTable = 0
lDPMgeo000paraTetFacets000vtkDisplay.GlyphTableIndexArray = 'None'
lDPMgeo000paraTetFacets000vtkDisplay.UseCompositeGlyphTable = 0
lDPMgeo000paraTetFacets000vtkDisplay.UseGlyphCullingAndLOD = 0
lDPMgeo000paraTetFacets000vtkDisplay.LODValues = []
lDPMgeo000paraTetFacets000vtkDisplay.ColorByLODIndex = 0
lDPMgeo000paraTetFacets000vtkDisplay.GaussianRadius = 0.025945091247558595
lDPMgeo000paraTetFacets000vtkDisplay.ShaderPreset = 'Sphere'
lDPMgeo000paraTetFacets000vtkDisplay.CustomTriangleScale = 3

lDPMgeo000paraTetFacets000vtkDisplay.Emissive = 0
lDPMgeo000paraTetFacets000vtkDisplay.ScaleByArray = 0
lDPMgeo000paraTetFacets000vtkDisplay.SetScaleArray = [None, '']
lDPMgeo000paraTetFacets000vtkDisplay.ScaleArrayComponent = 0
lDPMgeo000paraTetFacets000vtkDisplay.UseScaleFunction = 1
lDPMgeo000paraTetFacets000vtkDisplay.ScaleTransferFunction = 'PiecewiseFunction'
lDPMgeo000paraTetFacets000vtkDisplay.OpacityByArray = 0
lDPMgeo000paraTetFacets000vtkDisplay.OpacityArray = [None, '']
lDPMgeo000paraTetFacets000vtkDisplay.OpacityArrayComponent = 0
lDPMgeo000paraTetFacets000vtkDisplay.OpacityTransferFunction = 'PiecewiseFunction'
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid = 'GridAxesRepresentation'
lDPMgeo000paraTetFacets000vtkDisplay.SelectionCellLabelBold = 0
lDPMgeo000paraTetFacets000vtkDisplay.SelectionCellLabelColor = [0.0, 1.0, 0.0]
lDPMgeo000paraTetFacets000vtkDisplay.SelectionCellLabelFontFamily = 'Arial'
lDPMgeo000paraTetFacets000vtkDisplay.SelectionCellLabelFontFile = ''
lDPMgeo000paraTetFacets000vtkDisplay.SelectionCellLabelFontSize = 18
lDPMgeo000paraTetFacets000vtkDisplay.SelectionCellLabelItalic = 0
lDPMgeo000paraTetFacets000vtkDisplay.SelectionCellLabelJustification = 'Left'
lDPMgeo000paraTetFacets000vtkDisplay.SelectionCellLabelOpacity = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.SelectionCellLabelShadow = 0
lDPMgeo000paraTetFacets000vtkDisplay.SelectionPointLabelBold = 0
lDPMgeo000paraTetFacets000vtkDisplay.SelectionPointLabelColor = [1.0, 1.0, 0.0]
lDPMgeo000paraTetFacets000vtkDisplay.SelectionPointLabelFontFamily = 'Arial'
lDPMgeo000paraTetFacets000vtkDisplay.SelectionPointLabelFontFile = ''
lDPMgeo000paraTetFacets000vtkDisplay.SelectionPointLabelFontSize = 18
lDPMgeo000paraTetFacets000vtkDisplay.SelectionPointLabelItalic = 0
lDPMgeo000paraTetFacets000vtkDisplay.SelectionPointLabelJustification = 'Left'
lDPMgeo000paraTetFacets000vtkDisplay.SelectionPointLabelOpacity = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.SelectionPointLabelShadow = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes = 'PolarAxesRepresentation'
lDPMgeo000paraTetFacets000vtkDisplay.SelectInputVectors = [None, '']
lDPMgeo000paraTetFacets000vtkDisplay.NumberOfSteps = 40
lDPMgeo000paraTetFacets000vtkDisplay.StepSize = 0.25
lDPMgeo000paraTetFacets000vtkDisplay.NormalizeVectors = 1
lDPMgeo000paraTetFacets000vtkDisplay.EnhancedLIC = 1
lDPMgeo000paraTetFacets000vtkDisplay.ColorMode = 'Blend'
lDPMgeo000paraTetFacets000vtkDisplay.LICIntensity = 0.8
lDPMgeo000paraTetFacets000vtkDisplay.MapModeBias = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.EnhanceContrast = 'Off'
lDPMgeo000paraTetFacets000vtkDisplay.LowLICContrastEnhancementFactor = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.HighLICContrastEnhancementFactor = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.LowColorContrastEnhancementFactor = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.HighColorContrastEnhancementFactor = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.AntiAlias = 0
lDPMgeo000paraTetFacets000vtkDisplay.MaskOnSurface = 1
lDPMgeo000paraTetFacets000vtkDisplay.MaskThreshold = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.MaskIntensity = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.MaskColor = [0.5, 0.5, 0.5]
lDPMgeo000paraTetFacets000vtkDisplay.GenerateNoiseTexture = 0
lDPMgeo000paraTetFacets000vtkDisplay.NoiseType = 'Gaussian'
lDPMgeo000paraTetFacets000vtkDisplay.NoiseTextureSize = 128
lDPMgeo000paraTetFacets000vtkDisplay.NoiseGrainSize = 2
lDPMgeo000paraTetFacets000vtkDisplay.MinNoiseValue = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.MaxNoiseValue = 0.8
lDPMgeo000paraTetFacets000vtkDisplay.NumberOfNoiseLevels = 1024
lDPMgeo000paraTetFacets000vtkDisplay.ImpulseNoiseProbability = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.ImpulseNoiseBackgroundValue = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.NoiseGeneratorSeed = 1
lDPMgeo000paraTetFacets000vtkDisplay.CompositeStrategy = 'AUTO'
lDPMgeo000paraTetFacets000vtkDisplay.UseLICForLOD = 0
lDPMgeo000paraTetFacets000vtkDisplay.WriteLog = ''

# init the 'PiecewiseFunction' selected for 'OSPRayScaleFunction'
lDPMgeo000paraTetFacets000vtkDisplay.OSPRayScaleFunction.Points = [0.0, 0.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0]
lDPMgeo000paraTetFacets000vtkDisplay.OSPRayScaleFunction.UseLogScale = 0

# init the 'Arrow' selected for 'GlyphType'
lDPMgeo000paraTetFacets000vtkDisplay.GlyphType.TipResolution = 20
lDPMgeo000paraTetFacets000vtkDisplay.GlyphType.TipRadius = 0.1
lDPMgeo000paraTetFacets000vtkDisplay.GlyphType.TipLength = 0.35
lDPMgeo000paraTetFacets000vtkDisplay.GlyphType.ShaftResolution = 20
lDPMgeo000paraTetFacets000vtkDisplay.GlyphType.ShaftRadius = 0.03
lDPMgeo000paraTetFacets000vtkDisplay.GlyphType.Invert = 0

# init the 'PiecewiseFunction' selected for 'ScaleTransferFunction'
lDPMgeo000paraTetFacets000vtkDisplay.ScaleTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0]
lDPMgeo000paraTetFacets000vtkDisplay.ScaleTransferFunction.UseLogScale = 0

# init the 'PiecewiseFunction' selected for 'OpacityTransferFunction'
lDPMgeo000paraTetFacets000vtkDisplay.OpacityTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0]
lDPMgeo000paraTetFacets000vtkDisplay.OpacityTransferFunction.UseLogScale = 0

# init the 'GridAxesRepresentation' selected for 'DataAxesGrid'
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XTitle = 'X Axis'
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YTitle = 'Y Axis'
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZTitle = 'Z Axis'
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XTitleFontFamily = 'Arial'
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XTitleFontFile = ''
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XTitleBold = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XTitleItalic = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XTitleFontSize = 12
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XTitleShadow = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XTitleOpacity = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YTitleFontFamily = 'Arial'
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YTitleFontFile = ''
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YTitleBold = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YTitleItalic = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YTitleFontSize = 12
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YTitleShadow = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YTitleOpacity = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZTitleFontFamily = 'Arial'
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZTitleFontFile = ''
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZTitleBold = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZTitleItalic = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZTitleFontSize = 12
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZTitleShadow = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZTitleOpacity = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.FacesToRender = 63
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.CullBackface = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.CullFrontface = 1
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ShowGrid = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ShowEdges = 1
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ShowTicks = 1
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.LabelUniqueEdgesOnly = 1
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.AxesToLabel = 63
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XLabelFontFamily = 'Arial'
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XLabelFontFile = ''
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XLabelBold = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XLabelItalic = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XLabelFontSize = 12
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XLabelShadow = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XLabelOpacity = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YLabelFontFamily = 'Arial'
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YLabelFontFile = ''
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YLabelBold = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YLabelItalic = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YLabelFontSize = 12
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YLabelShadow = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YLabelOpacity = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZLabelFontFamily = 'Arial'
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZLabelFontFile = ''
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZLabelBold = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZLabelItalic = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZLabelFontSize = 12
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZLabelShadow = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZLabelOpacity = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XAxisNotation = 'Mixed'
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XAxisPrecision = 2
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XAxisUseCustomLabels = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.XAxisLabels = []
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YAxisNotation = 'Mixed'
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YAxisPrecision = 2
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YAxisUseCustomLabels = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.YAxisLabels = []
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZAxisNotation = 'Mixed'
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZAxisPrecision = 2
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZAxisUseCustomLabels = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.ZAxisLabels = []
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.UseCustomBounds = 0
lDPMgeo000paraTetFacets000vtkDisplay.DataAxesGrid.CustomBounds = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]

# init the 'PolarAxesRepresentation' selected for 'PolarAxes'
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.Visibility = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.Translation = [0.0, 0.0, 0.0]
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.Scale = [1.0, 1.0, 1.0]
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.Orientation = [0.0, 0.0, 0.0]
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.EnableCustomBounds = [0, 0, 0]
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.CustomBounds = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.EnableCustomRange = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.CustomRange = [0.0, 1.0]
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisVisibility = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.RadialAxesVisibility = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.DrawRadialGridlines = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarArcsVisibility = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.DrawPolarArcsGridlines = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.NumberOfRadialAxes = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.AutoSubdividePolarAxis = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.NumberOfPolarAxis = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.MinimumRadius = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.MinimumAngle = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.MaximumAngle = 90.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.RadialAxesOriginToPolarAxis = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.Ratio = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarArcsColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.LastRadialAxisColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.SecondaryPolarArcsColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.SecondaryRadialAxesColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisTitleVisibility = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisTitle = 'Radial Distance'
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisTitleLocation = 'Bottom'
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarLabelVisibility = 1

lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarLabelExponentLocation = 'Labels'
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.RadialLabelVisibility = 1

lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.RadialLabelLocation = 'Bottom'
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.RadialUnitsVisibility = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.ScreenSize = 10.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisTitleOpacity = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisTitleFontFamily = 'Arial'
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisTitleFontFile = ''
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisTitleBold = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisTitleItalic = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisTitleShadow = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisTitleFontSize = 12
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisLabelOpacity = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisLabelFontFamily = 'Arial'
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisLabelFontFile = ''
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisLabelBold = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisLabelItalic = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisLabelShadow = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisLabelFontSize = 12
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.LastRadialAxisTextOpacity = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.LastRadialAxisTextFontFamily = 'Arial'
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.LastRadialAxisTextFontFile = ''
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.LastRadialAxisTextBold = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.LastRadialAxisTextItalic = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.LastRadialAxisTextShadow = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.LastRadialAxisTextFontSize = 12
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.SecondaryRadialAxesTextOpacity = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.SecondaryRadialAxesTextFontFamily = 'Arial'
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.SecondaryRadialAxesTextFontFile = ''
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.SecondaryRadialAxesTextBold = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.SecondaryRadialAxesTextItalic = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.SecondaryRadialAxesTextShadow = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.SecondaryRadialAxesTextFontSize = 12
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.EnableDistanceLOD = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.DistanceLODThreshold = 0.7
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.EnableViewAngleLOD = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.ViewAngleLODThreshold = 0.7
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.SmallestVisiblePolarAngle = 0.5
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarTicksVisibility = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.ArcTicksOriginToPolarAxis = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.TickLocation = 'Both'
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.AxisTickVisibility = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.AxisMinorTickVisibility = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.ArcTickVisibility = 1
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.ArcMinorTickVisibility = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.DeltaAngleMajor = 10.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.DeltaAngleMinor = 5.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisMajorTickSize = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisTickRatioSize = 0.3
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisMajorTickThickness = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.PolarAxisTickRatioThickness = 0.5
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.LastRadialAxisMajorTickSize = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.LastRadialAxisTickRatioSize = 0.3
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.LastRadialAxisMajorTickThickness = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.LastRadialAxisTickRatioThickness = 0.5
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.ArcMajorTickSize = 0.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.ArcTickRatioSize = 0.3
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.ArcMajorTickThickness = 1.0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.ArcTickRatioThickness = 0.5
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.Use2DMode = 0
lDPMgeo000paraTetFacets000vtkDisplay.PolarAxes.UseLogAxis = 0

# show data in view
lDPMgeo000paraTetParticles000vtkDisplay = Show(lDPMgeo000paraTetParticles000vtk, renderView1, 'UnstructuredGridRepresentation')

# get 2D transfer function for 'Diameter'
diameterTF2D = GetTransferFunction2D('Diameter')
diameterTF2D.AutomaticRescaleRangeMode = "Grow and update on 'Apply'"
diameterTF2D.Boxes = []
diameterTF2D.ScalarRangeInitialized = 0
diameterTF2D.Range = [0.0, 1.0, 0.0, 1.0]
diameterTF2D.OutputDimensions = [10, 10]

# get color transfer function/color map for 'Diameter'
diameterLUT = GetColorTransferFunction('Diameter')
diameterLUT.AutomaticRescaleRangeMode = "Grow and update on 'Apply'"
diameterLUT.InterpretValuesAsCategories = 0
diameterLUT.AnnotationsInitialized = 0
diameterLUT.ShowCategoricalColorsinDataRangeOnly = 0
diameterLUT.RescaleOnVisibilityChange = 0
diameterLUT.EnableOpacityMapping = 0
diameterLUT.TransferFunction2D = diameterTF2D
diameterLUT.Use2DTransferFunction = 0
diameterLUT.UseLogScale = 0
diameterLUT.UseOpacityControlPointsFreehandDrawing = 0
diameterLUT.ShowDataHistogram = 0
diameterLUT.AutomaticDataHistogramComputation = 0
diameterLUT.DataHistogramNumberOfBins = 10
diameterLUT.ColorSpace = 'Diverging'
diameterLUT.UseBelowRangeColor = 0
diameterLUT.BelowRangeColor = [0.0, 0.0, 0.0]
diameterLUT.UseAboveRangeColor = 0
diameterLUT.AboveRangeColor = [0.5, 0.5, 0.5]
diameterLUT.NanColor = [1.0, 1.0, 0.0]
diameterLUT.NanOpacity = 1.0
diameterLUT.Discretize = 1
diameterLUT.NumberOfTableValues = 256
diameterLUT.ScalarRangeInitialized = 1.0
diameterLUT.HSVWrap = 0
diameterLUT.VectorComponent = 0
diameterLUT.VectorMode = 'Magnitude'
diameterLUT.AllowDuplicateScalars = 1
diameterLUT.Annotations = []
diameterLUT.ActiveAnnotatedValues = []
diameterLUT.IndexedColors = []
diameterLUT.IndexedOpacities = []

# get opacity transfer function/opacity map for 'Diameter'
diameterPWF = GetOpacityTransferFunction('Diameter')
diameterPWF.AllowDuplicateScalars = 1
diameterPWF.UseLogScale = 0
diameterPWF.ScalarRangeInitialized = 1

# trace defaults for the display properties.
lDPMgeo000paraTetParticles000vtkDisplay.Selection = None
lDPMgeo000paraTetParticles000vtkDisplay.Representation = 'Surface'
lDPMgeo000paraTetParticles000vtkDisplay.ColorArrayName = ['POINTS', 'Diameter']
lDPMgeo000paraTetParticles000vtkDisplay.LookupTable = diameterLUT
lDPMgeo000paraTetParticles000vtkDisplay.MapScalars = 1
lDPMgeo000paraTetParticles000vtkDisplay.MultiComponentsMapping = 0
lDPMgeo000paraTetParticles000vtkDisplay.InterpolateScalarsBeforeMapping = 1
lDPMgeo000paraTetParticles000vtkDisplay.Opacity = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.PointSize = 2.0
lDPMgeo000paraTetParticles000vtkDisplay.LineWidth = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.RenderLinesAsTubes = 0
lDPMgeo000paraTetParticles000vtkDisplay.RenderPointsAsSpheres = 0
lDPMgeo000paraTetParticles000vtkDisplay.Interpolation = 'Gouraud'
lDPMgeo000paraTetParticles000vtkDisplay.Specular = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.SpecularColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetParticles000vtkDisplay.SpecularPower = 100.0
lDPMgeo000paraTetParticles000vtkDisplay.Luminosity = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.Ambient = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.Diffuse = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.Roughness = 0.3
lDPMgeo000paraTetParticles000vtkDisplay.Metallic = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.EdgeTint = [1.0, 1.0, 1.0]
lDPMgeo000paraTetParticles000vtkDisplay.Anisotropy = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.AnisotropyRotation = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.BaseIOR = 1.5
lDPMgeo000paraTetParticles000vtkDisplay.CoatStrength = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.CoatIOR = 2.0
lDPMgeo000paraTetParticles000vtkDisplay.CoatRoughness = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.CoatColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetParticles000vtkDisplay.SelectTCoordArray = 'None'
lDPMgeo000paraTetParticles000vtkDisplay.SelectNormalArray = 'None'
lDPMgeo000paraTetParticles000vtkDisplay.SelectTangentArray = 'None'
lDPMgeo000paraTetParticles000vtkDisplay.Texture = None
lDPMgeo000paraTetParticles000vtkDisplay.RepeatTextures = 1
lDPMgeo000paraTetParticles000vtkDisplay.InterpolateTextures = 0
lDPMgeo000paraTetParticles000vtkDisplay.SeamlessU = 0
lDPMgeo000paraTetParticles000vtkDisplay.SeamlessV = 0
lDPMgeo000paraTetParticles000vtkDisplay.UseMipmapTextures = 0
lDPMgeo000paraTetParticles000vtkDisplay.ShowTexturesOnBackface = 1
lDPMgeo000paraTetParticles000vtkDisplay.BaseColorTexture = None
lDPMgeo000paraTetParticles000vtkDisplay.NormalTexture = None
lDPMgeo000paraTetParticles000vtkDisplay.NormalScale = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.CoatNormalTexture = None
lDPMgeo000paraTetParticles000vtkDisplay.CoatNormalScale = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.MaterialTexture = None
lDPMgeo000paraTetParticles000vtkDisplay.OcclusionStrength = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.AnisotropyTexture = None
lDPMgeo000paraTetParticles000vtkDisplay.EmissiveTexture = None
lDPMgeo000paraTetParticles000vtkDisplay.EmissiveFactor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetParticles000vtkDisplay.FlipTextures = 0
lDPMgeo000paraTetParticles000vtkDisplay.BackfaceRepresentation = 'Follow Frontface'
lDPMgeo000paraTetParticles000vtkDisplay.BackfaceAmbientColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetParticles000vtkDisplay.BackfaceOpacity = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.Position = [0.0, 0.0, 0.0]
lDPMgeo000paraTetParticles000vtkDisplay.Scale = [1.0, 1.0, 1.0]
lDPMgeo000paraTetParticles000vtkDisplay.Orientation = [0.0, 0.0, 0.0]
lDPMgeo000paraTetParticles000vtkDisplay.Origin = [0.0, 0.0, 0.0]
lDPMgeo000paraTetParticles000vtkDisplay.CoordinateShiftScaleMethod = 'Always Auto Shift Scale'
lDPMgeo000paraTetParticles000vtkDisplay.Pickable = 1
lDPMgeo000paraTetParticles000vtkDisplay.Triangulate = 0
lDPMgeo000paraTetParticles000vtkDisplay.UseShaderReplacements = 0
lDPMgeo000paraTetParticles000vtkDisplay.ShaderReplacements = ''
lDPMgeo000paraTetParticles000vtkDisplay.NonlinearSubdivisionLevel = 1
lDPMgeo000paraTetParticles000vtkDisplay.UseDataPartitions = 0
lDPMgeo000paraTetParticles000vtkDisplay.OSPRayUseScaleArray = 'All Approximate'
lDPMgeo000paraTetParticles000vtkDisplay.OSPRayScaleArray = 'Diameter'
lDPMgeo000paraTetParticles000vtkDisplay.OSPRayScaleFunction = 'PiecewiseFunction'
lDPMgeo000paraTetParticles000vtkDisplay.OSPRayMaterial = 'None'
lDPMgeo000paraTetParticles000vtkDisplay.BlockSelectors = ['/']
lDPMgeo000paraTetParticles000vtkDisplay.BlockColors = []
lDPMgeo000paraTetParticles000vtkDisplay.BlockOpacities = []
lDPMgeo000paraTetParticles000vtkDisplay.Orient = 0
lDPMgeo000paraTetParticles000vtkDisplay.OrientationMode = 'Direction'
lDPMgeo000paraTetParticles000vtkDisplay.SelectOrientationVectors = 'None'
lDPMgeo000paraTetParticles000vtkDisplay.Scaling = 0
lDPMgeo000paraTetParticles000vtkDisplay.ScaleMode = 'No Data Scaling Off'
lDPMgeo000paraTetParticles000vtkDisplay.ScaleFactor = 0.6963770329408047
lDPMgeo000paraTetParticles000vtkDisplay.SelectScaleArray = 'Diameter'
lDPMgeo000paraTetParticles000vtkDisplay.GlyphType = 'Arrow'
lDPMgeo000paraTetParticles000vtkDisplay.UseGlyphTable = 0
lDPMgeo000paraTetParticles000vtkDisplay.GlyphTableIndexArray = 'Diameter'
lDPMgeo000paraTetParticles000vtkDisplay.UseCompositeGlyphTable = 0
lDPMgeo000paraTetParticles000vtkDisplay.UseGlyphCullingAndLOD = 0
lDPMgeo000paraTetParticles000vtkDisplay.LODValues = []
lDPMgeo000paraTetParticles000vtkDisplay.ColorByLODIndex = 0
lDPMgeo000paraTetParticles000vtkDisplay.GaussianRadius = 0.03481885164704023
lDPMgeo000paraTetParticles000vtkDisplay.ShaderPreset = 'Sphere'
lDPMgeo000paraTetParticles000vtkDisplay.CustomTriangleScale = 3

lDPMgeo000paraTetParticles000vtkDisplay.Emissive = 0
lDPMgeo000paraTetParticles000vtkDisplay.ScaleByArray = 0
lDPMgeo000paraTetParticles000vtkDisplay.SetScaleArray = ['POINTS', 'Diameter']
lDPMgeo000paraTetParticles000vtkDisplay.ScaleArrayComponent = ''
lDPMgeo000paraTetParticles000vtkDisplay.UseScaleFunction = 1
lDPMgeo000paraTetParticles000vtkDisplay.ScaleTransferFunction = 'PiecewiseFunction'
lDPMgeo000paraTetParticles000vtkDisplay.OpacityByArray = 0
lDPMgeo000paraTetParticles000vtkDisplay.OpacityArray = ['POINTS', 'Diameter']
lDPMgeo000paraTetParticles000vtkDisplay.OpacityArrayComponent = ''
lDPMgeo000paraTetParticles000vtkDisplay.OpacityTransferFunction = 'PiecewiseFunction'
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid = 'GridAxesRepresentation'
lDPMgeo000paraTetParticles000vtkDisplay.SelectionCellLabelBold = 0
lDPMgeo000paraTetParticles000vtkDisplay.SelectionCellLabelColor = [0.0, 1.0, 0.0]
lDPMgeo000paraTetParticles000vtkDisplay.SelectionCellLabelFontFamily = 'Arial'
lDPMgeo000paraTetParticles000vtkDisplay.SelectionCellLabelFontFile = ''
lDPMgeo000paraTetParticles000vtkDisplay.SelectionCellLabelFontSize = 18
lDPMgeo000paraTetParticles000vtkDisplay.SelectionCellLabelItalic = 0
lDPMgeo000paraTetParticles000vtkDisplay.SelectionCellLabelJustification = 'Left'
lDPMgeo000paraTetParticles000vtkDisplay.SelectionCellLabelOpacity = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.SelectionCellLabelShadow = 0
lDPMgeo000paraTetParticles000vtkDisplay.SelectionPointLabelBold = 0
lDPMgeo000paraTetParticles000vtkDisplay.SelectionPointLabelColor = [1.0, 1.0, 0.0]
lDPMgeo000paraTetParticles000vtkDisplay.SelectionPointLabelFontFamily = 'Arial'
lDPMgeo000paraTetParticles000vtkDisplay.SelectionPointLabelFontFile = ''
lDPMgeo000paraTetParticles000vtkDisplay.SelectionPointLabelFontSize = 18
lDPMgeo000paraTetParticles000vtkDisplay.SelectionPointLabelItalic = 0
lDPMgeo000paraTetParticles000vtkDisplay.SelectionPointLabelJustification = 'Left'
lDPMgeo000paraTetParticles000vtkDisplay.SelectionPointLabelOpacity = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.SelectionPointLabelShadow = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes = 'PolarAxesRepresentation'
lDPMgeo000paraTetParticles000vtkDisplay.ScalarOpacityFunction = diameterPWF
lDPMgeo000paraTetParticles000vtkDisplay.ScalarOpacityUnitDistance = 11.056155192466099
lDPMgeo000paraTetParticles000vtkDisplay.UseSeparateOpacityArray = 0
lDPMgeo000paraTetParticles000vtkDisplay.OpacityArrayName = ['POINTS', 'Diameter']
lDPMgeo000paraTetParticles000vtkDisplay.OpacityComponent = ''
lDPMgeo000paraTetParticles000vtkDisplay.SelectMapper = 'Projected tetra'
lDPMgeo000paraTetParticles000vtkDisplay.SamplingDimensions = [128, 128, 128]
lDPMgeo000paraTetParticles000vtkDisplay.UseFloatingPointFrameBuffer = 1
lDPMgeo000paraTetParticles000vtkDisplay.SelectInputVectors = [None, '']
lDPMgeo000paraTetParticles000vtkDisplay.NumberOfSteps = 40
lDPMgeo000paraTetParticles000vtkDisplay.StepSize = 0.25
lDPMgeo000paraTetParticles000vtkDisplay.NormalizeVectors = 1
lDPMgeo000paraTetParticles000vtkDisplay.EnhancedLIC = 1
lDPMgeo000paraTetParticles000vtkDisplay.ColorMode = 'Blend'
lDPMgeo000paraTetParticles000vtkDisplay.LICIntensity = 0.8
lDPMgeo000paraTetParticles000vtkDisplay.MapModeBias = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.EnhanceContrast = 'Off'
lDPMgeo000paraTetParticles000vtkDisplay.LowLICContrastEnhancementFactor = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.HighLICContrastEnhancementFactor = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.LowColorContrastEnhancementFactor = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.HighColorContrastEnhancementFactor = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.AntiAlias = 0
lDPMgeo000paraTetParticles000vtkDisplay.MaskOnSurface = 1
lDPMgeo000paraTetParticles000vtkDisplay.MaskThreshold = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.MaskIntensity = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.MaskColor = [0.5, 0.5, 0.5]
lDPMgeo000paraTetParticles000vtkDisplay.GenerateNoiseTexture = 0
lDPMgeo000paraTetParticles000vtkDisplay.NoiseType = 'Gaussian'
lDPMgeo000paraTetParticles000vtkDisplay.NoiseTextureSize = 128
lDPMgeo000paraTetParticles000vtkDisplay.NoiseGrainSize = 2
lDPMgeo000paraTetParticles000vtkDisplay.MinNoiseValue = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.MaxNoiseValue = 0.8
lDPMgeo000paraTetParticles000vtkDisplay.NumberOfNoiseLevels = 1024
lDPMgeo000paraTetParticles000vtkDisplay.ImpulseNoiseProbability = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.ImpulseNoiseBackgroundValue = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.NoiseGeneratorSeed = 1
lDPMgeo000paraTetParticles000vtkDisplay.CompositeStrategy = 'AUTO'
lDPMgeo000paraTetParticles000vtkDisplay.UseLICForLOD = 0
lDPMgeo000paraTetParticles000vtkDisplay.WriteLog = ''

# init the 'PiecewiseFunction' selected for 'OSPRayScaleFunction'
lDPMgeo000paraTetParticles000vtkDisplay.OSPRayScaleFunction.Points = [0.0, 0.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0]
lDPMgeo000paraTetParticles000vtkDisplay.OSPRayScaleFunction.UseLogScale = 0

# init the 'Arrow' selected for 'GlyphType'
lDPMgeo000paraTetParticles000vtkDisplay.GlyphType.TipResolution = 20
lDPMgeo000paraTetParticles000vtkDisplay.GlyphType.TipRadius = 0.1
lDPMgeo000paraTetParticles000vtkDisplay.GlyphType.TipLength = 0.35
lDPMgeo000paraTetParticles000vtkDisplay.GlyphType.ShaftResolution = 20
lDPMgeo000paraTetParticles000vtkDisplay.GlyphType.ShaftRadius = 0.03
lDPMgeo000paraTetParticles000vtkDisplay.GlyphType.Invert = 0



# init the 'GridAxesRepresentation' selected for 'DataAxesGrid'
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XTitle = 'X Axis'
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YTitle = 'Y Axis'
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZTitle = 'Z Axis'
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XTitleFontFamily = 'Arial'
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XTitleFontFile = ''
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XTitleBold = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XTitleItalic = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XTitleFontSize = 12
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XTitleShadow = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XTitleOpacity = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YTitleFontFamily = 'Arial'
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YTitleFontFile = ''
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YTitleBold = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YTitleItalic = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YTitleFontSize = 12
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YTitleShadow = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YTitleOpacity = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZTitleFontFamily = 'Arial'
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZTitleFontFile = ''
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZTitleBold = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZTitleItalic = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZTitleFontSize = 12
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZTitleShadow = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZTitleOpacity = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.FacesToRender = 63
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.CullBackface = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.CullFrontface = 1
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ShowGrid = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ShowEdges = 1
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ShowTicks = 1
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.LabelUniqueEdgesOnly = 1
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.AxesToLabel = 63
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XLabelFontFamily = 'Arial'
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XLabelFontFile = ''
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XLabelBold = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XLabelItalic = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XLabelFontSize = 12
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XLabelShadow = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XLabelOpacity = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YLabelFontFamily = 'Arial'
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YLabelFontFile = ''
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YLabelBold = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YLabelItalic = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YLabelFontSize = 12
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YLabelShadow = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YLabelOpacity = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZLabelFontFamily = 'Arial'
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZLabelFontFile = ''
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZLabelBold = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZLabelItalic = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZLabelFontSize = 12
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZLabelShadow = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZLabelOpacity = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XAxisNotation = 'Mixed'
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XAxisPrecision = 2
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XAxisUseCustomLabels = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.XAxisLabels = []
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YAxisNotation = 'Mixed'
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YAxisPrecision = 2
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YAxisUseCustomLabels = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.YAxisLabels = []
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZAxisNotation = 'Mixed'
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZAxisPrecision = 2
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZAxisUseCustomLabels = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.ZAxisLabels = []
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.UseCustomBounds = 0
lDPMgeo000paraTetParticles000vtkDisplay.DataAxesGrid.CustomBounds = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]

# init the 'PolarAxesRepresentation' selected for 'PolarAxes'
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.Visibility = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.Translation = [0.0, 0.0, 0.0]
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.Scale = [1.0, 1.0, 1.0]
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.Orientation = [0.0, 0.0, 0.0]
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.EnableCustomBounds = [0, 0, 0]
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.CustomBounds = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.EnableCustomRange = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.CustomRange = [0.0, 1.0]
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisVisibility = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.RadialAxesVisibility = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.DrawRadialGridlines = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarArcsVisibility = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.DrawPolarArcsGridlines = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.NumberOfRadialAxes = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.AutoSubdividePolarAxis = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.NumberOfPolarAxis = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.MinimumRadius = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.MinimumAngle = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.MaximumAngle = 90.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.RadialAxesOriginToPolarAxis = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.Ratio = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarArcsColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.LastRadialAxisColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.SecondaryPolarArcsColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.SecondaryRadialAxesColor = [1.0, 1.0, 1.0]
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisTitleVisibility = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisTitle = 'Radial Distance'
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisTitleLocation = 'Bottom'
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarLabelVisibility = 1

lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarLabelExponentLocation = 'Labels'
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.RadialLabelVisibility = 1

lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.RadialLabelLocation = 'Bottom'
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.RadialUnitsVisibility = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.ScreenSize = 10.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisTitleOpacity = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisTitleFontFamily = 'Arial'
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisTitleFontFile = ''
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisTitleBold = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisTitleItalic = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisTitleShadow = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisTitleFontSize = 12
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisLabelOpacity = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisLabelFontFamily = 'Arial'
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisLabelFontFile = ''
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisLabelBold = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisLabelItalic = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisLabelShadow = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisLabelFontSize = 12
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.LastRadialAxisTextOpacity = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.LastRadialAxisTextFontFamily = 'Arial'
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.LastRadialAxisTextFontFile = ''
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.LastRadialAxisTextBold = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.LastRadialAxisTextItalic = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.LastRadialAxisTextShadow = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.LastRadialAxisTextFontSize = 12
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.SecondaryRadialAxesTextOpacity = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.SecondaryRadialAxesTextFontFamily = 'Arial'
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.SecondaryRadialAxesTextFontFile = ''
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.SecondaryRadialAxesTextBold = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.SecondaryRadialAxesTextItalic = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.SecondaryRadialAxesTextShadow = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.SecondaryRadialAxesTextFontSize = 12
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.EnableDistanceLOD = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.DistanceLODThreshold = 0.7
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.EnableViewAngleLOD = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.ViewAngleLODThreshold = 0.7
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.SmallestVisiblePolarAngle = 0.5
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarTicksVisibility = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.ArcTicksOriginToPolarAxis = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.TickLocation = 'Both'
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.AxisTickVisibility = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.AxisMinorTickVisibility = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.ArcTickVisibility = 1
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.ArcMinorTickVisibility = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.DeltaAngleMajor = 10.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.DeltaAngleMinor = 5.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisMajorTickSize = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisTickRatioSize = 0.3
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisMajorTickThickness = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.PolarAxisTickRatioThickness = 0.5
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.LastRadialAxisMajorTickSize = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.LastRadialAxisTickRatioSize = 0.3
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.LastRadialAxisMajorTickThickness = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.LastRadialAxisTickRatioThickness = 0.5
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.ArcMajorTickSize = 0.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.ArcTickRatioSize = 0.3
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.ArcMajorTickThickness = 1.0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.ArcTickRatioThickness = 0.5
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.Use2DMode = 0
lDPMgeo000paraTetParticles000vtkDisplay.PolarAxes.UseLogAxis = 0

# show color bar/color legend
lDPMgeo000paraTetParticles000vtkDisplay.SetScalarBarVisibility(renderView1, True)

# update the view to ensure updated data information
renderView1.Update()



# create a new 'Glyph'
glyph1 = Glyph(registrationName='Glyph1', Input=lDPMgeo000paraTetParticles000vtk,
    GlyphType='Arrow')
glyph1.OrientationArray = ['POINTS', 'No orientation array']
glyph1.ScaleArray = ['POINTS', 'Diameter']
glyph1.VectorScaleMode = 'Scale by Magnitude'
glyph1.ScaleFactor = 0.6963770329408047
glyph1.GlyphTransform = 'Transform2'
glyph1.GlyphMode = 'Uniform Spatial Distribution (Bounds Based)'
glyph1.MaximumNumberOfSamplePoints = 5000
glyph1.Seed = 10339
glyph1.Stride = 1

# init the 'Arrow' selected for 'GlyphType'
glyph1.GlyphType.TipResolution = 20
glyph1.GlyphType.TipRadius = 0.1
glyph1.GlyphType.TipLength = 0.35
glyph1.GlyphType.ShaftResolution = 20
glyph1.GlyphType.ShaftRadius = 0.03
glyph1.GlyphType.Invert = 0

# init the 'Transform2' selected for 'GlyphTransform'
glyph1.GlyphTransform.Translate = [0.0, 0.0, 0.0]
glyph1.GlyphTransform.Rotate = [0.0, 0.0, 0.0]
glyph1.GlyphTransform.Scale = [1.0, 1.0, 1.0]

# Properties modified on glyph1
glyph1.GlyphType = 'Sphere'
glyph1.ScaleFactor = 1.0
glyph1.GlyphMode = 'All Points'

# show data in view
glyph1Display = Show(glyph1, renderView1, 'GeometryRepresentation')

# trace defaults for the display properties.
glyph1Display.Selection = None
glyph1Display.Representation = 'Surface'
glyph1Display.ColorArrayName = ['POINTS', 'Diameter']
glyph1Display.LookupTable = diameterLUT
glyph1Display.MapScalars = 1
glyph1Display.MultiComponentsMapping = 0
glyph1Display.InterpolateScalarsBeforeMapping = 1
glyph1Display.Opacity = 1.0
glyph1Display.PointSize = 2.0
glyph1Display.LineWidth = 1.0
glyph1Display.RenderLinesAsTubes = 0
glyph1Display.RenderPointsAsSpheres = 0
glyph1Display.Interpolation = 'Gouraud'
glyph1Display.Specular = 0.0
glyph1Display.SpecularColor = [1.0, 1.0, 1.0]
glyph1Display.SpecularPower = 100.0
glyph1Display.Luminosity = 0.0
glyph1Display.Ambient = 0.0
glyph1Display.Diffuse = 1.0
glyph1Display.Roughness = 0.3
glyph1Display.Metallic = 0.0
glyph1Display.EdgeTint = [1.0, 1.0, 1.0]
glyph1Display.Anisotropy = 0.0
glyph1Display.AnisotropyRotation = 0.0
glyph1Display.BaseIOR = 1.5
glyph1Display.CoatStrength = 0.0
glyph1Display.CoatIOR = 2.0
glyph1Display.CoatRoughness = 0.0
glyph1Display.CoatColor = [1.0, 1.0, 1.0]
glyph1Display.SelectTCoordArray = 'None'
glyph1Display.SelectNormalArray = 'Normals'
glyph1Display.SelectTangentArray = 'None'
glyph1Display.Texture = None
glyph1Display.RepeatTextures = 1
glyph1Display.InterpolateTextures = 0
glyph1Display.SeamlessU = 0
glyph1Display.SeamlessV = 0
glyph1Display.UseMipmapTextures = 0
glyph1Display.ShowTexturesOnBackface = 1
glyph1Display.BaseColorTexture = None
glyph1Display.NormalTexture = None
glyph1Display.NormalScale = 1.0
glyph1Display.CoatNormalTexture = None
glyph1Display.CoatNormalScale = 1.0
glyph1Display.MaterialTexture = None
glyph1Display.OcclusionStrength = 1.0
glyph1Display.AnisotropyTexture = None
glyph1Display.EmissiveTexture = None
glyph1Display.EmissiveFactor = [1.0, 1.0, 1.0]
glyph1Display.FlipTextures = 0
glyph1Display.BackfaceRepresentation = 'Follow Frontface'
glyph1Display.BackfaceAmbientColor = [1.0, 1.0, 1.0]
glyph1Display.BackfaceOpacity = 1.0
glyph1Display.Position = [0.0, 0.0, 0.0]
glyph1Display.Scale = [1.0, 1.0, 1.0]
glyph1Display.Orientation = [0.0, 0.0, 0.0]
glyph1Display.Origin = [0.0, 0.0, 0.0]
glyph1Display.CoordinateShiftScaleMethod = 'Always Auto Shift Scale'
glyph1Display.Pickable = 1
glyph1Display.Triangulate = 0
glyph1Display.UseShaderReplacements = 0
glyph1Display.ShaderReplacements = ''
glyph1Display.NonlinearSubdivisionLevel = 1
glyph1Display.UseDataPartitions = 0
glyph1Display.OSPRayUseScaleArray = 'All Approximate'
glyph1Display.OSPRayScaleArray = 'Diameter'
glyph1Display.OSPRayScaleFunction = 'PiecewiseFunction'
glyph1Display.OSPRayMaterial = 'None'
glyph1Display.BlockSelectors = ['/']
glyph1Display.BlockColors = []
glyph1Display.BlockOpacities = []
glyph1Display.Orient = 0
glyph1Display.OrientationMode = 'Direction'
glyph1Display.SelectOrientationVectors = 'None'
glyph1Display.Scaling = 0
glyph1Display.ScaleMode = 'No Data Scaling Off'
glyph1Display.ScaleFactor = 1.1127780914306642
glyph1Display.SelectScaleArray = 'Diameter'
glyph1Display.GlyphType = 'Arrow'
glyph1Display.UseGlyphTable = 0
glyph1Display.GlyphTableIndexArray = 'Diameter'
glyph1Display.UseCompositeGlyphTable = 0
glyph1Display.UseGlyphCullingAndLOD = 0
glyph1Display.LODValues = []
glyph1Display.ColorByLODIndex = 0
glyph1Display.GaussianRadius = 0.055638904571533206
glyph1Display.ShaderPreset = 'Sphere'
glyph1Display.CustomTriangleScale = 3

glyph1Display.Emissive = 0
glyph1Display.ScaleByArray = 0
glyph1Display.SetScaleArray = ['POINTS', 'Diameter']
glyph1Display.ScaleArrayComponent = ''
glyph1Display.UseScaleFunction = 1
glyph1Display.ScaleTransferFunction = 'PiecewiseFunction'
glyph1Display.OpacityByArray = 0
glyph1Display.OpacityArray = ['POINTS', 'Diameter']
glyph1Display.OpacityArrayComponent = ''
glyph1Display.OpacityTransferFunction = 'PiecewiseFunction'
glyph1Display.DataAxesGrid = 'GridAxesRepresentation'
glyph1Display.SelectionCellLabelBold = 0
glyph1Display.SelectionCellLabelColor = [0.0, 1.0, 0.0]
glyph1Display.SelectionCellLabelFontFamily = 'Arial'
glyph1Display.SelectionCellLabelFontFile = ''
glyph1Display.SelectionCellLabelFontSize = 18
glyph1Display.SelectionCellLabelItalic = 0
glyph1Display.SelectionCellLabelJustification = 'Left'
glyph1Display.SelectionCellLabelOpacity = 1.0
glyph1Display.SelectionCellLabelShadow = 0
glyph1Display.SelectionPointLabelBold = 0
glyph1Display.SelectionPointLabelColor = [1.0, 1.0, 0.0]
glyph1Display.SelectionPointLabelFontFamily = 'Arial'
glyph1Display.SelectionPointLabelFontFile = ''
glyph1Display.SelectionPointLabelFontSize = 18
glyph1Display.SelectionPointLabelItalic = 0
glyph1Display.SelectionPointLabelJustification = 'Left'
glyph1Display.SelectionPointLabelOpacity = 1.0
glyph1Display.SelectionPointLabelShadow = 0
glyph1Display.PolarAxes = 'PolarAxesRepresentation'
glyph1Display.SelectInputVectors = ['POINTS', 'Normals']
glyph1Display.NumberOfSteps = 40
glyph1Display.StepSize = 0.25
glyph1Display.NormalizeVectors = 1
glyph1Display.EnhancedLIC = 1
glyph1Display.ColorMode = 'Blend'
glyph1Display.LICIntensity = 0.8
glyph1Display.MapModeBias = 0.0
glyph1Display.EnhanceContrast = 'Off'
glyph1Display.LowLICContrastEnhancementFactor = 0.0
glyph1Display.HighLICContrastEnhancementFactor = 0.0
glyph1Display.LowColorContrastEnhancementFactor = 0.0
glyph1Display.HighColorContrastEnhancementFactor = 0.0
glyph1Display.AntiAlias = 0
glyph1Display.MaskOnSurface = 1
glyph1Display.MaskThreshold = 0.0
glyph1Display.MaskIntensity = 0.0
glyph1Display.MaskColor = [0.5, 0.5, 0.5]
glyph1Display.GenerateNoiseTexture = 0
glyph1Display.NoiseType = 'Gaussian'
glyph1Display.NoiseTextureSize = 128
glyph1Display.NoiseGrainSize = 2
glyph1Display.MinNoiseValue = 0.0
glyph1Display.MaxNoiseValue = 0.8
glyph1Display.NumberOfNoiseLevels = 1024
glyph1Display.ImpulseNoiseProbability = 1.0
glyph1Display.ImpulseNoiseBackgroundValue = 0.0
glyph1Display.NoiseGeneratorSeed = 1
glyph1Display.CompositeStrategy = 'AUTO'
glyph1Display.UseLICForLOD = 0
glyph1Display.WriteLog = ''

# init the 'PiecewiseFunction' selected for 'OSPRayScaleFunction'
glyph1Display.OSPRayScaleFunction.Points = [0.0, 0.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0]
glyph1Display.OSPRayScaleFunction.UseLogScale = 0

# init the 'Arrow' selected for 'GlyphType'
glyph1Display.GlyphType.TipResolution = 20
glyph1Display.GlyphType.TipRadius = 0.1
glyph1Display.GlyphType.TipLength = 0.35
glyph1Display.GlyphType.ShaftResolution = 20
glyph1Display.GlyphType.ShaftRadius = 0.03
glyph1Display.GlyphType.Invert = 0



# init the 'GridAxesRepresentation' selected for 'DataAxesGrid'
glyph1Display.DataAxesGrid.XTitle = 'X Axis'
glyph1Display.DataAxesGrid.YTitle = 'Y Axis'
glyph1Display.DataAxesGrid.ZTitle = 'Z Axis'
glyph1Display.DataAxesGrid.XTitleFontFamily = 'Arial'
glyph1Display.DataAxesGrid.XTitleFontFile = ''
glyph1Display.DataAxesGrid.XTitleBold = 0
glyph1Display.DataAxesGrid.XTitleItalic = 0
glyph1Display.DataAxesGrid.XTitleFontSize = 12
glyph1Display.DataAxesGrid.XTitleShadow = 0
glyph1Display.DataAxesGrid.XTitleOpacity = 1.0
glyph1Display.DataAxesGrid.YTitleFontFamily = 'Arial'
glyph1Display.DataAxesGrid.YTitleFontFile = ''
glyph1Display.DataAxesGrid.YTitleBold = 0
glyph1Display.DataAxesGrid.YTitleItalic = 0
glyph1Display.DataAxesGrid.YTitleFontSize = 12
glyph1Display.DataAxesGrid.YTitleShadow = 0
glyph1Display.DataAxesGrid.YTitleOpacity = 1.0
glyph1Display.DataAxesGrid.ZTitleFontFamily = 'Arial'
glyph1Display.DataAxesGrid.ZTitleFontFile = ''
glyph1Display.DataAxesGrid.ZTitleBold = 0
glyph1Display.DataAxesGrid.ZTitleItalic = 0
glyph1Display.DataAxesGrid.ZTitleFontSize = 12
glyph1Display.DataAxesGrid.ZTitleShadow = 0
glyph1Display.DataAxesGrid.ZTitleOpacity = 1.0
glyph1Display.DataAxesGrid.FacesToRender = 63
glyph1Display.DataAxesGrid.CullBackface = 0
glyph1Display.DataAxesGrid.CullFrontface = 1
glyph1Display.DataAxesGrid.ShowGrid = 0
glyph1Display.DataAxesGrid.ShowEdges = 1
glyph1Display.DataAxesGrid.ShowTicks = 1
glyph1Display.DataAxesGrid.LabelUniqueEdgesOnly = 1
glyph1Display.DataAxesGrid.AxesToLabel = 63
glyph1Display.DataAxesGrid.XLabelFontFamily = 'Arial'
glyph1Display.DataAxesGrid.XLabelFontFile = ''
glyph1Display.DataAxesGrid.XLabelBold = 0
glyph1Display.DataAxesGrid.XLabelItalic = 0
glyph1Display.DataAxesGrid.XLabelFontSize = 12
glyph1Display.DataAxesGrid.XLabelShadow = 0
glyph1Display.DataAxesGrid.XLabelOpacity = 1.0
glyph1Display.DataAxesGrid.YLabelFontFamily = 'Arial'
glyph1Display.DataAxesGrid.YLabelFontFile = ''
glyph1Display.DataAxesGrid.YLabelBold = 0
glyph1Display.DataAxesGrid.YLabelItalic = 0
glyph1Display.DataAxesGrid.YLabelFontSize = 12
glyph1Display.DataAxesGrid.YLabelShadow = 0
glyph1Display.DataAxesGrid.YLabelOpacity = 1.0
glyph1Display.DataAxesGrid.ZLabelFontFamily = 'Arial'
glyph1Display.DataAxesGrid.ZLabelFontFile = ''
glyph1Display.DataAxesGrid.ZLabelBold = 0
glyph1Display.DataAxesGrid.ZLabelItalic = 0
glyph1Display.DataAxesGrid.ZLabelFontSize = 12
glyph1Display.DataAxesGrid.ZLabelShadow = 0
glyph1Display.DataAxesGrid.ZLabelOpacity = 1.0
glyph1Display.DataAxesGrid.XAxisNotation = 'Mixed'
glyph1Display.DataAxesGrid.XAxisPrecision = 2
glyph1Display.DataAxesGrid.XAxisUseCustomLabels = 0
glyph1Display.DataAxesGrid.XAxisLabels = []
glyph1Display.DataAxesGrid.YAxisNotation = 'Mixed'
glyph1Display.DataAxesGrid.YAxisPrecision = 2
glyph1Display.DataAxesGrid.YAxisUseCustomLabels = 0
glyph1Display.DataAxesGrid.YAxisLabels = []
glyph1Display.DataAxesGrid.ZAxisNotation = 'Mixed'
glyph1Display.DataAxesGrid.ZAxisPrecision = 2
glyph1Display.DataAxesGrid.ZAxisUseCustomLabels = 0
glyph1Display.DataAxesGrid.ZAxisLabels = []
glyph1Display.DataAxesGrid.UseCustomBounds = 0
glyph1Display.DataAxesGrid.CustomBounds = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]

# init the 'PolarAxesRepresentation' selected for 'PolarAxes'
glyph1Display.PolarAxes.Visibility = 0
glyph1Display.PolarAxes.Translation = [0.0, 0.0, 0.0]
glyph1Display.PolarAxes.Scale = [1.0, 1.0, 1.0]
glyph1Display.PolarAxes.Orientation = [0.0, 0.0, 0.0]
glyph1Display.PolarAxes.EnableCustomBounds = [0, 0, 0]
glyph1Display.PolarAxes.CustomBounds = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
glyph1Display.PolarAxes.EnableCustomRange = 0
glyph1Display.PolarAxes.CustomRange = [0.0, 1.0]
glyph1Display.PolarAxes.PolarAxisVisibility = 1
glyph1Display.PolarAxes.RadialAxesVisibility = 1
glyph1Display.PolarAxes.DrawRadialGridlines = 1
glyph1Display.PolarAxes.PolarArcsVisibility = 1
glyph1Display.PolarAxes.DrawPolarArcsGridlines = 1
glyph1Display.PolarAxes.NumberOfRadialAxes = 0
glyph1Display.PolarAxes.AutoSubdividePolarAxis = 1
glyph1Display.PolarAxes.NumberOfPolarAxis = 0
glyph1Display.PolarAxes.MinimumRadius = 0.0
glyph1Display.PolarAxes.MinimumAngle = 0.0
glyph1Display.PolarAxes.MaximumAngle = 90.0
glyph1Display.PolarAxes.RadialAxesOriginToPolarAxis = 1
glyph1Display.PolarAxes.Ratio = 1.0
glyph1Display.PolarAxes.PolarAxisColor = [1.0, 1.0, 1.0]
glyph1Display.PolarAxes.PolarArcsColor = [1.0, 1.0, 1.0]
glyph1Display.PolarAxes.LastRadialAxisColor = [1.0, 1.0, 1.0]
glyph1Display.PolarAxes.SecondaryPolarArcsColor = [1.0, 1.0, 1.0]
glyph1Display.PolarAxes.SecondaryRadialAxesColor = [1.0, 1.0, 1.0]
glyph1Display.PolarAxes.PolarAxisTitleVisibility = 1
glyph1Display.PolarAxes.PolarAxisTitle = 'Radial Distance'
glyph1Display.PolarAxes.PolarAxisTitleLocation = 'Bottom'
glyph1Display.PolarAxes.PolarLabelVisibility = 1

glyph1Display.PolarAxes.PolarLabelExponentLocation = 'Labels'
glyph1Display.PolarAxes.RadialLabelVisibility = 1

glyph1Display.PolarAxes.RadialLabelLocation = 'Bottom'
glyph1Display.PolarAxes.RadialUnitsVisibility = 1
glyph1Display.PolarAxes.ScreenSize = 10.0
glyph1Display.PolarAxes.PolarAxisTitleOpacity = 1.0
glyph1Display.PolarAxes.PolarAxisTitleFontFamily = 'Arial'
glyph1Display.PolarAxes.PolarAxisTitleFontFile = ''
glyph1Display.PolarAxes.PolarAxisTitleBold = 0
glyph1Display.PolarAxes.PolarAxisTitleItalic = 0
glyph1Display.PolarAxes.PolarAxisTitleShadow = 0
glyph1Display.PolarAxes.PolarAxisTitleFontSize = 12
glyph1Display.PolarAxes.PolarAxisLabelOpacity = 1.0
glyph1Display.PolarAxes.PolarAxisLabelFontFamily = 'Arial'
glyph1Display.PolarAxes.PolarAxisLabelFontFile = ''
glyph1Display.PolarAxes.PolarAxisLabelBold = 0
glyph1Display.PolarAxes.PolarAxisLabelItalic = 0
glyph1Display.PolarAxes.PolarAxisLabelShadow = 0
glyph1Display.PolarAxes.PolarAxisLabelFontSize = 12
glyph1Display.PolarAxes.LastRadialAxisTextOpacity = 1.0
glyph1Display.PolarAxes.LastRadialAxisTextFontFamily = 'Arial'
glyph1Display.PolarAxes.LastRadialAxisTextFontFile = ''
glyph1Display.PolarAxes.LastRadialAxisTextBold = 0
glyph1Display.PolarAxes.LastRadialAxisTextItalic = 0
glyph1Display.PolarAxes.LastRadialAxisTextShadow = 0
glyph1Display.PolarAxes.LastRadialAxisTextFontSize = 12
glyph1Display.PolarAxes.SecondaryRadialAxesTextOpacity = 1.0
glyph1Display.PolarAxes.SecondaryRadialAxesTextFontFamily = 'Arial'
glyph1Display.PolarAxes.SecondaryRadialAxesTextFontFile = ''
glyph1Display.PolarAxes.SecondaryRadialAxesTextBold = 0
glyph1Display.PolarAxes.SecondaryRadialAxesTextItalic = 0
glyph1Display.PolarAxes.SecondaryRadialAxesTextShadow = 0
glyph1Display.PolarAxes.SecondaryRadialAxesTextFontSize = 12
glyph1Display.PolarAxes.EnableDistanceLOD = 1
glyph1Display.PolarAxes.DistanceLODThreshold = 0.7
glyph1Display.PolarAxes.EnableViewAngleLOD = 1
glyph1Display.PolarAxes.ViewAngleLODThreshold = 0.7
glyph1Display.PolarAxes.SmallestVisiblePolarAngle = 0.5
glyph1Display.PolarAxes.PolarTicksVisibility = 1
glyph1Display.PolarAxes.ArcTicksOriginToPolarAxis = 1
glyph1Display.PolarAxes.TickLocation = 'Both'
glyph1Display.PolarAxes.AxisTickVisibility = 1
glyph1Display.PolarAxes.AxisMinorTickVisibility = 0
glyph1Display.PolarAxes.ArcTickVisibility = 1
glyph1Display.PolarAxes.ArcMinorTickVisibility = 0
glyph1Display.PolarAxes.DeltaAngleMajor = 10.0
glyph1Display.PolarAxes.DeltaAngleMinor = 5.0
glyph1Display.PolarAxes.PolarAxisMajorTickSize = 0.0
glyph1Display.PolarAxes.PolarAxisTickRatioSize = 0.3
glyph1Display.PolarAxes.PolarAxisMajorTickThickness = 1.0
glyph1Display.PolarAxes.PolarAxisTickRatioThickness = 0.5
glyph1Display.PolarAxes.LastRadialAxisMajorTickSize = 0.0
glyph1Display.PolarAxes.LastRadialAxisTickRatioSize = 0.3
glyph1Display.PolarAxes.LastRadialAxisMajorTickThickness = 1.0
glyph1Display.PolarAxes.LastRadialAxisTickRatioThickness = 0.5
glyph1Display.PolarAxes.ArcMajorTickSize = 0.0
glyph1Display.PolarAxes.ArcTickRatioSize = 0.3
glyph1Display.PolarAxes.ArcMajorTickThickness = 1.0
glyph1Display.PolarAxes.ArcTickRatioThickness = 0.5
glyph1Display.PolarAxes.Use2DMode = 0
glyph1Display.PolarAxes.UseLogAxis = 0

# show color bar/color legend
glyph1Display.SetScalarBarVisibility(renderView1, True)

# update the view to ensure updated data information
renderView1.Update()

# set active source
SetActiveSource(lDPMgeo000paraTet000vtk)

# change representation type
lDPMgeo000paraTet000vtkDisplay.SetRepresentationType('Feature Edges')

# set active source
SetActiveSource(lDPMgeo000paraTetFacets000vtk)

# change representation type
lDPMgeo000paraTetFacets000vtkDisplay.SetRepresentationType('Surface With Edges')

# get color legend/bar for diameterLUT in view renderView1
diameterLUTColorBar = GetScalarBar(diameterLUT, renderView1)
diameterLUTColorBar.AutoOrient = 1
diameterLUTColorBar.Orientation = 'Vertical'
diameterLUTColorBar.WindowLocation = 'Lower Right Corner'
diameterLUTColorBar.Position = [0.89, 0.02]
diameterLUTColorBar.Title = 'Diameter'
diameterLUTColorBar.ComponentTitle = ''
diameterLUTColorBar.TitleJustification = 'Centered'
diameterLUTColorBar.HorizontalTitle = 0
diameterLUTColorBar.TitleOpacity = 1.0
diameterLUTColorBar.TitleFontFamily = 'Arial'
diameterLUTColorBar.TitleFontFile = ''
diameterLUTColorBar.TitleBold = 0
diameterLUTColorBar.TitleItalic = 0
diameterLUTColorBar.TitleShadow = 0
diameterLUTColorBar.TitleFontSize = 16
diameterLUTColorBar.LabelOpacity = 1.0
diameterLUTColorBar.LabelFontFamily = 'Arial'
diameterLUTColorBar.LabelFontFile = ''
diameterLUTColorBar.LabelBold = 0
diameterLUTColorBar.LabelItalic = 0
diameterLUTColorBar.LabelShadow = 0
diameterLUTColorBar.LabelFontSize = 16
diameterLUTColorBar.ScalarBarThickness = 16
diameterLUTColorBar.ScalarBarLength = 0.33
diameterLUTColorBar.DrawBackground = 0
diameterLUTColorBar.BackgroundColor = [1.0, 1.0, 1.0, 0.5]
diameterLUTColorBar.BackgroundPadding = 2.0
diameterLUTColorBar.DrawScalarBarOutline = 0
diameterLUTColorBar.ScalarBarOutlineColor = [1.0, 1.0, 1.0]
diameterLUTColorBar.ScalarBarOutlineThickness = 1
diameterLUTColorBar.AutomaticLabelFormat = 1

diameterLUTColorBar.DrawTickMarks = 1
diameterLUTColorBar.DrawTickLabels = 1
diameterLUTColorBar.UseCustomLabels = 0
diameterLUTColorBar.CustomLabels = []
diameterLUTColorBar.AddRangeLabels = 1

diameterLUTColorBar.DrawDataRange = 0

diameterLUTColorBar.DrawAnnotations = 1
diameterLUTColorBar.AddRangeAnnotations = 0
diameterLUTColorBar.AutomaticAnnotations = 0
diameterLUTColorBar.DrawNanAnnotation = 0
diameterLUTColorBar.NanAnnotation = 'NaN'
diameterLUTColorBar.TextPosition = 'Ticks right/top, annotations left/bottom'
diameterLUTColorBar.ReverseLegend = 0

# change scalar bar placement
diameterLUTColorBar.WindowLocation = 'Any Location'
diameterLUTColorBar.Position = [0.658129175946548, 0.3979475484606614]
diameterLUTColorBar.ScalarBarLength = 0.33000000000000007

# set active source
SetActiveSource(lDPMgeo000paraTetParticles000vtk)

# Properties modified on diameterLUTColorBar
diameterLUTColorBar.Title = 'Diameter, d [mm]'
diameterLUTColorBar.TitleFontFamily = 'Times'
diameterLUTColorBar.LabelFontFamily = 'Times'

# Apply a preset using its name. Note this may not work as expected when presets have duplicate names.
diameterLUT.ApplyPreset('Yellow 15', True)

# set active source
SetActiveSource(lDPMgeo000paraTetFacets000vtk)

# Properties modified on lDPMgeo000paraTetFacets000vtkDisplay
lDPMgeo000paraTetFacets000vtkDisplay.EdgeColor = [0.0, 0.0, 0.0]

#================================================================
# addendum: following script captures some of the application
# state to faithfully reproduce the visualization during playback
#================================================================

# get layout
layout1 = GetLayout()

#--------------------------------
# saving layout sizes for layouts

# layout/tab size in pixels
layout1.SetSize(1796, 877)

# reset view to fit data
renderView1.ResetCamera(False)

#--------------------------------------------
# uncomment the following to render all views
# RenderAllViews()
# alternatively, if you want to write images, you can use SaveScreenshot(...).
        \n""")