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
## Description coming soon...
##
##
## ================================================================================

from setuptools import setup
import os

version_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 
                            "freecad", "ldpmWorkbench", "version.py")
with open(version_path) as fp:
    exec(fp.read())

setup(name='freecad.ldpmWorkbench',
      version=str(__version__),
      packages=['freecad',
                'freecad.ldpmWorkbench'],
      maintainer="mtroemner",
      maintainer_email="mtroemner@gmail.com",
      url="TBD",
      description="LDPM Workbench",
      install_requires=['numpy','math','time'], 
      include_package_data=True)
