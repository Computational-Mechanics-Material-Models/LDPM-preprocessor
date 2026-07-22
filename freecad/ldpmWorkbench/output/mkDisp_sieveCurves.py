## ================================================================================
## LDPM WORKBENCH:github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor
##
## Copyright (c) 2023 
## All rights reserved. 
##
## Use of this source code is governed by a BSD-style license that can be found
## in the LICENSE file at the top level of the distribution and at
## github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
##
## ================================================================================
## Developed by Northwestern University
## For U.S. Army ERDC Contract No. W9132T22C0015
## Primary Authors: Matthew Troemner
## ================================================================================
##
## This file contains the function to generate and display sieve curves for the 
## input sieve curve and generated particle size distribution.
##
## ================================================================================

# pyright: reportMissingImports=false
try:
    from FreeCAD.Plot import Plot
except ImportError:
    from freecad.plot import Plot
import numpy as np
import math



def mkDisp_sieveCurves(volFracPar,parVolTotal, tetVolume,minPar_sim, maxPar_sim, minPar_exp, maxPar_exp,fullerCoef,
                       sieveCurveDiameter,sieveCurvePassing,parDiameterList,tempPath):

    """
    Variable List:
    --------------------------------------------------------------------------
    ### Inputs ###
    volFracPar:              Volume fraction of particles in the geometry
    parVolTotal:             Total volume of particles using experimental limits
    tetVolume:               Volume of the tetrahedral mesh
    minPar_sim:                  Minimum particle diameter in simulation
    maxPar_sim:                  Maximum particle diameter in simulation
    minPar_exp:                  Minimum particle diameter in experiment
    maxPar_exp:                  Maximum particle diameter in experiment
    fullerCoef:              Fuller coefficient of the input particle size distribution
    sieveCurveDiameter:          List of diameters for the input sieve curve
    sieveCurvePassing:          List of percent passing for the input sieve curve
    parDiameterList:         List of diameters for the generated particle size distribution
    --------------------------------------------------------------------------
    ### Outputs ###
    Display of the input sieve curve and generated particle size distribution
    --------------------------------------------------------------------------
    """

    # Generate plot of sieve curve
    Plot.figure("Particle Sieve Curve")

    # Get volume of small particles and generated particles
    F_a = (maxPar_sim/maxPar_exp)**fullerCoef # Volume fraction of particles smaller than maxPar_sim
    F_0_exp = (minPar_exp/maxPar_exp)**fullerCoef # Volume fraction of particles smaller than minPar_exp
    # F_a_exp = (maxPar_exp/maxPar_exp)**fullerCoef # Volume fraction of particles smaller than maxPar_exp
    # volFracSim = (F_a_exp - F_a)/(F_a_exp - F_0_exp)
    volFracSim = (1 - F_a)/(1 - F_0_exp)

    totalVol = sum(4/3*math.pi*(parDiameterList/2)**3) # Total volume of generated particles
    volParticles=volFracPar*tetVolume # Total volume of particles in the geometry included small particles
    volExtra=volParticles - totalVol - parVolTotal*volFracSim # Volume of small particles not included in generated particles
 


    # Initialize Diameters
    parDiameterList = np.flip(parDiameterList)
    diameters = np.linspace(0,maxPar_exp,num=1000)
    passingPercent=np.zeros(1000)
    passingPercentTheory=np.zeros(1000)


    # Get Passing Percent of Placed Particles
    for x in range(1000):
        passing=parDiameterList[parDiameterList<diameters[x]]
        vol=sum(4/3*math.pi*(passing/2)**3)+volExtra
        passingPercent[x]=vol/volParticles*100

    # Calculations for sieve curve plotting for shifted generated particle size distribution (for comparison with Fuller Curve)
    if fullerCoef != 0:
        # Generate values for small particles
        diametersTheory = diameters
        passingPercentTheory=100*(diametersTheory/maxPar_exp)**fullerCoef

    else:
        # Reformat sieve curve into numpy arrays for interpolation
        diametersTheory = np.asarray(sieveCurveDiameter, dtype=np.float32)
        passingPercentTheory = np.asarray([x*100 for x in sieveCurvePassing], dtype=np.float32)

        # Get Interpolated passingPercentTheory value for largest diameter in generated particle size distribution
        # This is used to shift the generated particle size distribution to match the input sieve curve
        for x in range(len(diametersTheory)):
            if diametersTheory[x+1] == maxPar_exp:
                shiftValue = passingPercent[999]-passingPercentTheory[x+1]
                break
            elif (diametersTheory[x] <= maxPar_exp) and (diametersTheory[x+1] >= maxPar_exp):
                shiftValue = passingPercent[999]-(passingPercentTheory[x] + (passingPercentTheory[x+1]-passingPercentTheory[x])/(diametersTheory[x+1]-diametersTheory[x])*(maxPar_exp-diametersTheory[x]))
                break
            else:
                shiftValue = 0

        # Shift passingPercent by shiftValue
        passingPercent = passingPercent - shiftValue

    # Plotting
    Plot.plot(diametersTheory, passingPercentTheory, 'Theoretical Curve') 
    # Plot.plot(diameters[passingPercent_exp>min(passingPercent_exp)], passingPercent_exp[passingPercent_exp>min(passingPercent_exp)], 'Experiment Data') 
    Plot.plot(diameters[passingPercent>min(passingPercent)], passingPercent[passingPercent>min(passingPercent)], 'Simulated Data') 
    # Plotting Formatting
    Plot.xlabel('Particle Diameter, $d$ (mm)') 
    Plot.ylabel('Percent Passing, $P$ (%)')
    Plot.grid(True)
    Plot.legend() 


    # --- Saving to CSV with pandas ---
    # Build a DataFrame; pandas will align columns by index automatically

    mask_sim = passingPercent > min(passingPercent)
    # mask_exp = passingPercent_exp > min(passingPercent_exp)

    
    import os
    sieve_curve_file = os.path.join(tempPath, "seiveCurve_particle_data.dat")
    
    with open(sieve_curve_file, "w") as f:
        f.write("Diameter_Theory\tPassing_Theory\tDiameter_Sim\tPassing_Sim\n")
        for dT, pT, dS, pS in zip(
            diametersTheory, passingPercentTheory,
            diameters[mask_sim], passingPercent[mask_sim],
            # diameters[mask_exp], passingPercent_exp[mask_exp],
        ):
            f.write(f"{dT}\t{pT}\t{dS}\t{pS}\n")


    print("Data saved to particle_data.dat")


