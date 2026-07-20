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
## Function to shift total sieve curve to coarse sieve curve
##
## ===========================================================================



import numpy as np



def calc_sieveCurve(minPar, maxPar, sieveCurveDiameter, sieveCurvePassing):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    minPar:                minimum particle size
    maxPar:                maximum particle size
    sieveCurveDiameter:    an array of particle size data
    sieveCurvePassing:     an array of cumulative percent passing data
    --------------------------------------------------------------------------
    ### Outputs ###
    newSieveCurveD:        shifted sieve curve diameter data
    newSieveCurveP:        shifted sieve curve percent passing data
    NewSet:                number of lines in shifted sieve curve data
    w_min:                 minimum weight of particles
    w_max:                 maximum weight of particles
    --------------------------------------------------------------------------
    """

    
    # Get number of lines in sieve curve data
    nblines = len(sieveCurveDiameter)
    
    # Find range of diameters containing the minimum particle size
    for i in range(0, nblines):
        if minPar >= sieveCurveDiameter[i] and minPar<sieveCurveDiameter[i+1]:
            minRange = i
            
    # Find range of diameters containing the maximum particle size
    for i in range(0, nblines):
        if maxPar > sieveCurveDiameter[i] and maxPar<=sieveCurveDiameter[i+1]:
            maxRange = i
            
    # Calculate minimum and maximum weights from sieve curve data
    w_min = sieveCurvePassing[minRange] + (
        sieveCurvePassing[minRange+1] - sieveCurvePassing[minRange]) / (
        sieveCurveDiameter[minRange+1] - sieveCurveDiameter[minRange]) * (
        minPar - sieveCurveDiameter[minRange])
    w_max = sieveCurvePassing[maxRange] + (
        sieveCurvePassing[maxRange+1] - sieveCurvePassing[maxRange]) / (
        sieveCurveDiameter[maxRange+1] - sieveCurveDiameter[maxRange]) * (
        maxPar - sieveCurveDiameter[maxRange])
    
    # Get number of data points in new sieve curve
    NewSet = maxRange - minRange + 1
    
    # Initialize new sieve curve arrays
    newSieveCurveD = [0] * 100
    newSieveCurveP = [0] * 100
    
    # Fill in new sieve curve data
    for i in range(0, NewSet+1):
        if i == 0:
            newSieveCurveD[i] = minPar
            newSieveCurveP[i] = 0
        elif NewSet > 1 and i > 0 and i < NewSet:
            newSieveCurveD[i] = sieveCurveDiameter[minRange + i]
            newSieveCurveP[i] = (sieveCurvePassing[minRange + i] - w_min) / (
                w_max - w_min)
        elif NewSet == i:
            newSieveCurveD[i] = maxPar
            newSieveCurveP[i] = 1
            
    # Trim excess zeros from new sieve curve arrays
    newSieveCurveD = np.trim_zeros(newSieveCurveD, trim='b')
    newSieveCurveP = np.trim_zeros(newSieveCurveP, trim='b')
    
    # Return new sieve curve data and related values
    return newSieveCurveD, newSieveCurveP, NewSet, w_min, w_max

