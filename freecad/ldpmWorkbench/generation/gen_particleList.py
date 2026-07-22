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
## This function generates a sorted array of particle diameters based on user 
## inputs for either a Fuller Coefficient case or a case with a provided
## discrete sieve curve. 
##
## ===========================================================================

import math
import numpy as np


def _verbose_on(value):
    return str(value).strip().lower() in ["on", "y", "yes", "true", "1"]


def gen_particleList(parVolTotal, minPar_sim, maxPar_sim, minPar_exp, maxPar_exp, newSieveCurveD, cdf, kappa_i, 
                 NewSet, fullerCoef, verbose="On"):
    
    """
    Variable List:
    --------------------------------------------------------------------------
    ### Inputs ###
    parVolTotal:     float, total volume of particles
    minPar_sim:      float, minimum diameter of particles in simulation
    maxPar_sim:      float, maximum diameter of particles in simulation
    minPar_exp:      float, minimum diameter of particles in experiment
    maxPar_exp:      float, maximum diameter of particles in experiment
    newSieveCurveD:  numpy array, diameters of particles in sieve curve
    cdf:             numpy array, cumulative distribution function
    kappa_i:         numpy array, coefficient used in particle simulation
    NewSet:          int, number of sieves
    fullerCoef:      float, Fuller coefficient
    --------------------------------------------------------------------------
    ### Outputs ###
    maxparNum:       int, maximum number of particles that can be generated
    parDiameterList: numpy array, particle diameters (sorted large-to-small)
    --------------------------------------------------------------------------
    """

    # Determine 'q' value based on Fuller Coefficient
    q = 3.0-fullerCoef

    F_0 = (minPar_sim/maxPar_exp)**fullerCoef # Volume fraction of particles smaller than minPar_sim
    F_a = (maxPar_sim/maxPar_exp)**fullerCoef # Volume fraction of particles smaller than maxPar_sim
    F_0_exp = (minPar_exp/maxPar_exp)**fullerCoef # Volume fraction of particles smaller than minPar_exp
    F_a_exp = (maxPar_exp/maxPar_exp)**fullerCoef # Volume fraction of particles smaller than maxPar_exp
    
    if _verbose_on(verbose):
        print("F_0: ", F_0, " F_a: ", F_a, " F_0_exp: ", F_0_exp, " F_a_exp: ", F_a_exp)
    volFracSim = (F_a - F_0)/(F_a_exp - F_0_exp)
    if _verbose_on(verbose):
        print("Volume Fraction within Simulation Limits: ", volFracSim)
    parVolTotal = parVolTotal*volFracSim # Adjust total particle volume based on simulation size limits    
    

    # Calculate the volume of the smallest particle
    # smallparVolume = 4/3*math.pi*(minPar_exp/2)**3
    smallparVolume = 4/3*math.pi*(minPar_sim/2)**3
    
    # Determine maximum number of particles
    maxparNum = np.ceil(parVolTotal/smallparVolume)
    if _verbose_on(verbose):
        print("Maximum Number of Particles: ", maxparNum)
    # Initialize arrays for particle diameters and volumes
    parDiameter = np.zeros(int(maxparNum))
    parVol = np.zeros(int(maxparNum))

    # Remove particles below minPar_sim or above maxPar_sim

    if _verbose_on(verbose):
        print("minPar_simulation: ", minPar_sim, " maxPar_simulation: ", maxPar_sim)

    P_minPar_sim = (1-(minPar_sim/minPar_exp)**(-q))/(1-minPar_exp**q/maxPar_exp**q)
    P_maxPar_sim = (1-(maxPar_sim/minPar_exp)**(-q))/(1-minPar_exp**q/maxPar_exp**q)

    if _verbose_on(verbose):
        print("P_minPar_sim: ", P_minPar_sim, " P_maxPar_sim: ", P_maxPar_sim)
    

    # Counter for particle array indexing
    i = 0

    # If no Sieve Curve is provided
    if newSieveCurveD == 0:

        # Count particles individually for small arrays
        if len(parDiameter) <= 100:
            while sum(parVol) < parVolTotal:
                # Randomly calculate the particle diameter
                P = np.random.uniform(P_minPar_sim, P_maxPar_sim)
                parDiameter[i] = minPar_exp*(1-P*(1-minPar_exp**q/maxPar_exp**q))**(-1/q)
                # parDiameter[i] = minPar_exp*(1-np.random.rand(1)*(1-minPar_exp**q\
                    # /maxPar_exp**q))**(-1/q)
                parVol[i] = 4/3*math.pi*(parDiameter[i]/2)**3
                i = i+1         

        # Count particles in bunches of 100 for medium arrays
        elif len(parDiameter) <= 1000:
            while sum(parVol) < parVolTotal:
                # Randomly calculate particle diameters
                P = np.random.uniform(P_minPar_sim, P_maxPar_sim, 100)
                parDiameter[i:i+100] = minPar_exp*(1-P*(1-minPar_exp**q/maxPar_exp**q))**(-1/q)
                # parDiameter[i:i+100] = minPar_exp*(1-np.random.rand(100)*\
                    # (1-minPar_exp**q/maxPar_exp**q))**(-1/q)
                parVol[i:i+100] = 4/3*math.pi*(parDiameter[i:i+100]/2)**3
                i = i+100

        # Count particles in bunches of 1000 for large arrays
        else:
            while sum(parVol) < parVolTotal:
                # Randomly calculate particle diameters
                P = np.random.uniform(P_minPar_sim, P_maxPar_sim, 1000)
                parDiameter[i:i+1000] = minPar_exp*(1-P*\
                    (1-minPar_exp**q/maxPar_exp**q))**(-1/q)
                # parDiameter[i:i+1000] = minPar_exp*(1-np.random.rand(1000)*\
                    # (1-minPar_exp**q/maxPar_exp**q))**(-1/q)
                parVol[i:i+1000] = 4/3*math.pi*(parDiameter[i:i+1000]/2)**3
                i = i+1000

    # If a Sieve Curve is provided
    else:
        while sum(parVol) < parVolTotal:
            F = np.random.rand(1)
            for x in range(0,NewSet):
                if (F >= cdf[x] and F < cdf[x+1]) :
                    # Calculate the diameter of the selected particle
                    parDiameter[i] = ((newSieveCurveD[x]**2*kappa_i[x])/(kappa_i[x]-2*(F-cdf[x])*newSieveCurveD[x]**2))**0.5
                    parVol[i] = 4/3*math.pi*(parDiameter[i]/2)**3
                    i = i+1         

    # Remove trailing zeros from arrays
    parDiameter = np.trim_zeros(parDiameter)
    parVol = np.trim_zeros(parVol)


    # Remove accidental extra placed particles
    while sum(parVol) > parVolTotal:
        parDiameter = np.delete(parDiameter, -1)
        parVol = np.delete(parVol, -1)

    # parDiameterList_exp = np.sort(parDiameter)[::-1]

    # # Apply simulation particle size bounds
    # mask = (parDiameter >= minPar_sim) & (parDiameter <= maxPar_sim)
    # parDiameter = parDiameter[mask]
    # parVol      = parVol[mask]

    # Sort particle diameters large-to-small
    parDiameterList = np.sort(parDiameter)[::-1]
    # return maxparNum, parDiameterList, parDiameterList_exp
    return maxparNum, parDiameterList