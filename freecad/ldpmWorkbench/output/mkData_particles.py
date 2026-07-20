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
## Function to generate a data file for all particles in the model.
##
## ===========================================================================

from pathlib import Path

def mkData_particles(nodes,diameters,geoName,tempPath):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - nodes:        Array of all nodes in the model
    - diameters:    Array of all particle diameters
    - geoName:      Name of the geometry file
    - tempPath:     Path to the temporary directory
    --------------------------------------------------------------------------
    ### Outputs ###
    - A data file of all particles in the model
    --------------------------------------------------------------------------
    """

    # Generate data file for particles
    with open(Path(tempPath + geoName + \
        '-data-particles.dat'),"w") as f:                                       
        f.write('// ================================================================================\n')  
        f.write('// LDPM WORKBENCH - github.com/Concrete-Chrono-Development/chrono-preprocessor\n')  
        f.write('//\n')  
        f.write('// Copyright (c) 2023 \n')  
        f.write('// All rights reserved. \n')  
        f.write('//\n')  
        f.write('// Use of the code that generated this file is governed by a BSD-style license that\n')  
        f.write('// can be found in the LICENSE file at the top level of the distribution and at\n')  
        f.write('// github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE\n')  
        f.write('//\n')  
        f.write('// ================================================================================\n')  
        f.write('// Particle Data File\n')  
        f.write('// ================================================================================\n')  
        f.write('//\n')  
        f.write('// Data Structure:\n')  
        f.write('// n x y z d\n')  
        f.write('//\n')  
        f.write('// ================================================================================\n')  
        for x in range(0,len(diameters)):
            f.write(str(x) + ' ' + str(nodes[x,0]) + ' ' + str(nodes[x,1]) \
                + ' ' + str(nodes[x,2]) + ' ' + str(diameters[x]) + '\n')
        f.write('\n')  
