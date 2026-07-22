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
## Function to calculate the total volume of particles in a mixture and related
## values
##
## ===========================================================================

import numpy as np


def calc_parVolume(tetVolume, wcRatio, cementC, volFracAir, fullerCoef, flyashC,
              silicaC, scmC, fillerC, flyashDensity, silicaDensity, scmDensity,
              fillerDensity, densityCement, densityWater, minPar, maxPar, 
              newSieveCurveD, newSieveCurveP, NewSet, w_min, w_max):
    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    tetVolume:      total volume of the mix
    wcRatio:        water to cement ratio
    cementC:        cement content
    volFracAir:     volume fraction of air in the mix
    fullerCoef:     Fuller coefficient for particle size distribution
    flyashC:        mass of fly ash
    silicaC:        mass of silica fume
    scmC:           mass of supplementary cementitious materials
    fillerC:        mass of arbitrary filler
    flyashDensity:  density of fly ash
    silicaDensity:  density of silica fume
    scmDensity:     density of supplementary cementitious materials
    fillerDensity:  density of arbitrary filler
    densityCement:  density of cement
    densityWater:   density of water
    minPar:         minimum particle size
    maxPar:         maximum particle size
    newSieveCurveD: an array containing particle size data
    newSieveCurveP: an array containing cumulative percent passing data
    NewSet:         number of data points in newSieveCurveD and newSieveCurveP
    w_min:          minimum value for a weight distribution
    w_max:          maximum value for a weight distribution
    --------------------------------------------------------------------------
    ### Outputs ###
    parVolSimTotal: total volume of particles in the mix
    cdf:            cumulative distribution function
    cdf1:           cumulative distribution function
    kappa_i:        kappa value
    --------------------------------------------------------------------------
    """
    
    # Calculate volume fractions of each component in the mixture and make sure to ignore if density is zero
    if densityCement != 0:
        volFracCement = cementC / densityCement
    else:
        volFracCement = 0
    if flyashDensity != 0:
        volFracFly = flyashC / flyashDensity
    else:
        volFracFly = 0
    if silicaDensity != 0:
        volFracSilica = silicaC / silicaDensity
    else:
        volFracSilica = 0
    if scmDensity != 0:
        volFracSCM = scmC / scmDensity
    else:
        volFracSCM = 0
    if fillerDensity != 0:
        volFracFiller = fillerC / fillerDensity
    else:
        volFracFiller = 0
    if densityWater != 0:
        volFracWater = wcRatio * cementC / densityWater
    else:
        volFracWater = 0

    # Calculate volume fraction of particles
    volFracPar = (1-volFracCement-volFracFly-volFracSilica-volFracSCM-
                  volFracFiller-volFracWater - volFracAir)
    
    # Check if a pre-defined particle size distribution curve is available
    if newSieveCurveD == 0:
        
        # Calculate volume fraction of particles using Fuller's equation
        volFracParSim = (1 - (minPar / maxPar) ** fullerCoef) * volFracPar
        cdf = 0
        cdf1 = 0
        kappa_i = 0
        
    else:
        
        # Calculate Kappa value
        A = 0
        for i in range(0, NewSet):
            B = (newSieveCurveP[i+1] - newSieveCurveP[i]) / (
                newSieveCurveD[i+1] - newSieveCurveD[i]) * (
                1 / newSieveCurveD[i] / newSieveCurveD[i] -
                1 / newSieveCurveD[i+1] / newSieveCurveD[i+1])
            A = A + B
        kappa = 2 / A
        kappa_i = [0] * 100
        for i in range(0, NewSet):
            kappa_i[i] = (kappa * (newSieveCurveP[i+1] - newSieveCurveP[i]) /
                          (newSieveCurveD[i+1] - newSieveCurveD[i]))
        kappa_i = np.trim_zeros(kappa_i, trim='b')
        
        # Calculate volume fraction of particles using simulated values
        w_sim = w_max - w_min
        volFracParSim = w_sim * volFracPar
        
        # Calculate CDF
        cdf = [0] * 100
        cdf1 = [0] * 100
        for i in range(0, NewSet):
            cdf1[i] = (kappa_i[i] * (1 / (newSieveCurveD[i] ** 2) -
                                      1 / (newSieveCurveD[i+1] ** 2))) / 2
            if i > 0:
                cdf[i] = cdf1[i-1] + cdf[i-1]
        cdf[NewSet] = cdf1[NewSet-1] + cdf[NewSet-1]
        cdf = np.trim_zeros(cdf, trim='b')
        cdf1 = np.trim_zeros(cdf1, trim='b')
        
    # Calculate total volume of particles
    parVolSimTotal = volFracParSim * tetVolume

    # Return total particle volume, CDF, and other related values
    return volFracPar, parVolSimTotal, cdf, cdf1, kappa_i



