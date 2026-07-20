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
## This file contains the function to read the selected constitutive equation
## set and material parameter set and return the appropriate material info.
##
## ===========================================================================


def gen_LDPMCSL_properties(constitutiveEQ, matParaSet):

    """
    Variable List:
    --------------------------------------------------------------------------
    ### Inputs ###
    constitutiveEQ: Constitutive equation set
    matParaSet: Material parameter set
    --------------------------------------------------------------------------
    ### Outputs ###
    materialProps: List of material properties
    materialPropDesc: List of material property descriptions
    materialPropsVal: List of material property values
    --------------------------------------------------------------------------    
    """

  
    # Properties for Cusatis et al. 2011 Section "X" from:
    #--- Cusatis, G., Mencarelli, A., Pelessone, D., & Baylot, J. (2011). Lattice discrete particle model (LDPM) for failure behavior of concrete. 
    #--- II: Calibration and validation. Cement and Concrete composites, 33(9), 891-905.

    if constitutiveEQ in ['Concrete-Failure-V1', 'Concrete-Failure-V2', 'Concrete-Failure-V3', 'Concrete-Failure-V4']:

        materialProps = [\
            "Density",\
            "NormalModulus",\
            "ShearNormalCoupling",\
            "TensileStrength",\
            "TensileCharacteristicLength",\
            "ShearTensileStrengthRatio",\
            "SofteningExponent",\
            "CompressiveStrength",\
            "InitialHardeningModulusRatio",\
            "FinalHardeningModulusRatio",\
            "TransitionalStrainRatio",\
            "DeviatoricStrainRatio",\
            "DeviatoricDamage",\
            "InitialInternalFrictionCoefficient",\
            "FinalInternalFrictionCoefficient",\
            "TransitionalNormalStress",\
            "DensificationRatio"\
            ]

        materialPropDesc = [\
            "D [tonne/mm^3]",\
            "E_0 [MPa]",\
            "alpha [-]",\
            "sigma_t [MPa]",\
            "l_t [mm]",\
            "r_st [-]",\
            "n_t [-]",\
            "sigma_c0 [Mpa]",\
            "H_c0/E_0 [-]",\
            "H_c1/E_0 [-]",\
            "k_c0 [-]",\
            "k_c1 [-]",\
            "k_c2 [-]",\
            "mu_0 [-]",\
            "mu_inf [-]",\
            "sigma_N0 [MPa]",\
            "E_d/E_0"\
            ]

        if matParaSet == 'Cusatis et al. 2011 Section 3':
            materialPropsVal = [\
                "2.37e-9",\
                "43748",\
                "0.25",\
                "4.03",\
                "120.0",\
                "2.7",\
                "0.2",\
                "150.0",\
                "0.4",\
                "0.1",\
                "2.0",\
                "1.0",\
                "5.0",\
                "0.2",\
                "0.0",\
                "600.0",\
                "1.0"\
                ]

        elif matParaSet == 'Cusatis et al. 2011 Section 4':
            materialPropsVal = [\
                "2.4e-9",\
                "46260",\
                "0.25",\
                "3.04",\
                "100.0",\
                "5.75",\
                "0.2",\
                "35.0",\
                "0.1",\
                "0.1",\
                "4.0",\
                "1.0",\
                "5.0",\
                "0.05",\
                "0.0",\
                "600.0",\
                "1.0"\
                ]

        elif matParaSet == 'Cusatis et al. 2011 Section 5.1':
            materialPropsVal = [\
                "2.29e-9",\
                "38636",\
                "0.25",\
                "4.16",\
                "100.0",\
                "2.7",\
                "0.2",\
                "120.0",\
                "0.67",\
                "0.1",\
                "3.8",\
                "1.2",\
                "5.0",\
                "0.4",\
                "0.0",\
                "600.0",\
                "1.81"\
                ]

        else:
            materialPropsVal = [\
                "0",\
                "0",\
                "0",\
                "0",\
                "0",\
                "0",\
                "0",\
                "0",\
                "0",\
                "0",\
                "0",\
                "0",\
                "0",\
                "0",\
                "0",\
                "0",\
                "0"\
                ]


    else:
        materialProps=[]
        materialPropDesc=[]
        materialPropsVal=[]

    return materialProps, materialPropDesc, materialPropsVal