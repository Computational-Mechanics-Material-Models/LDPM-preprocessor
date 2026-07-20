#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# created by Jan Elias
# jan.elias@vut.cz
# Brno University of Technology,
# 2023

import os
import sys
import shutil
sys.path.insert(0, os.path.abspath('..'))
from random_field_generation.rf_generator import RandomField
import numpy as np

#delete previous field
if os.path.isdir("example_field"): shutil.rmtree("example_field")

#create some random set of points (mm)
size = np.array([400., 300., 200.])
np.save("points",np.random.rand(3000,3)*size)

#3D, simple Gaussian field, periodic, default setting
#"""
RF = RandomField(dimension = 3, dist_types=["Gaussian"], dist_params=[[3,8]], name = "example_field", corr_l = 70., filesavetype="binary", x_range = [0.,size[0]], y_range = [0.,size[1]], z_range = [0.,size[2]], sampling_type = "LHS", periodic = True, grid_file = "points.npy")
RF.generateRandVariables(500, seed = 8)        #generation of random numbers, critical step
RF.generateFieldOnGrid()    #direct generation of the field, your own file with coordinated can be supplied at the first line as "grid_file"
RF.errorEvaluation(max_node_num = 5e3, grid_data = True)      #check of correlation, cross correlation and distribution, not needed
RF.saveGridNodesVTKDots()  #save field as VTK file  
#"""

#3D, simple Gaussian field, non-periodic, default setting, EOLE projection to some data file
"""
RF = RandomField(dimension = 3, dist_types=["Gaussian"], dist_params=[[3,8]], name = "example_field", corr_l = 70., filesavetype="binary", x_range = [0.,size[0]], y_range = [0.,size[1]], z_range = [0.,size[2]], sampling_type = "LHS")
RF.generateRandVariables(500, seed = 8)        #generation of random numbers, critical step
RF.generateFieldOnGrid()
RF.generateFieldEOLE(nodefile="points.npy")    #EOLE projection
RF.errorEvaluation(max_node_num = 5e3)      #check of correlation, cross correlation and distribution, not needed
RF.saveFieldNodesVTKDots()  #save field as VTK file  
#"""

#3D, truncated Gaussian field, non-periodic, different correlation lengths in X,Y, and Z, EOLE projection to some data file
"""
RF = RandomField(dimension = 3, dist_types=["TruncatedGaussian"], dist_params=[[1,0.4,0]], name = "example_field", corr_l = [70., 140., 200.], filesavetype="text", x_range = [0.,size[0]], y_range = [0.,size[1]], z_range = [0.,size[2]], sampling_type = "LHS")
RF.generateRandVariables(20, seed = 8)        #generation of random numbers, critical step
RF.generateFieldOnGrid()
RF.generateFieldEOLE(nodefile="points.npy")    #EOLE projection
RF.errorEvaluation(max_node_num = 5e3)      #check of correlation, cross correlation and distribution, not needed
RF.saveFieldNodesVTKDots()  #save field as VTK file  
#"""


#2D, cross correlated non-Gaussian field, periodic, EOLE projection to some data file
"""
RF = RandomField(dimension = 2, dist_types=["Weibull","Lognormal","Gamma"], dist_params=[[1,5],[1,0.25],[1.,0.8]], name = "example_field", corr_l = 70., filesavetype="binary", x_range = [0.,size[0]], y_range = [0.,size[1]], CC=[[1.,0.9, 0.9],[0.9,1.0,0.9],[0.9,0.9,1.0]], sampling_type = "LHS", periodic = True)
RF.generateRandVariables(500, seed = 8)        #generation of random numbers, critical step
RF.generateFieldOnGrid()
RF.generateFieldEOLE(nodefile="points.npy")    #EOLE projection
RF.errorEvaluation(max_node_num = 5e3)      #check of correlation, cross correlation and distribution, not needed
RF.saveFieldNodesVTKDots()  #save field as VTK file  
#"""

#1D, cross correlated non-Gaussian field, non-periodic, EOLE projection to some data file, sparse matrix representation
"""
RF = RandomField(dimension = 1, dist_types = ["Grafted","TruncatedGaussian"], dist_params=[[1.,0.2, 30,1e-4],[10.,5.,0]], name = "example_field", corr_l = 70., filesavetype="binary", x_range = [0.,size[0]], CC=[[1.,0.9],[0.9,1]], sampling_type = "LHS", sparse = True)
RF.generateRandVariables(500, seed = 8)        #generation of random numbers, critical step
RF.generateFieldOnGrid()
RF.generateFieldEOLE(nodefile="points.npy")    #EOLE projection
RF.errorEvaluation(max_node_num = 5e3)      #check of correlation, cross correlation and distribution, not needed
RF.saveFieldNodesVTKDots()  #save field as VTK file  
#"""

#3D, cross correlated non-Gaussian field, periodic, EOLE projection to some data file, sparse matrix representation
"""
RF = RandomField(dimension = 3, dist_types = ["Uniform","Gaussian", "Triangular"], dist_params=[[1.,4],[10.,5.],[-2, 4, 0]], name = "example_field", corr_l = 70., filesavetype="binary", x_range = [0.,size[0]], y_range = [0.,size[1]], z_range = [0.,size[2]], CC=[[1.,0.9, 0.9],[0.9,1.0,0.9],[0.9,0.9,1.0]], sampling_type = "LHS", periodic = True, sparse = True)
RF.generateRandVariables(500, seed = 8)        #generation of random numbers, critical step
RF.generateFieldOnGrid()
RF.generateFieldEOLE(nodefile="points.npy")    #EOLE projection
RF.errorEvaluation(max_node_num = 5e3)      #check of correlation, cross correlation and distribution, not needed
RF.saveFieldNodesVTKDots()  #save field as VTK file  
#"""

#2D, user supplied distribution, exponential autocorrelation, Spearman correlation, sparse matrix representation
"""
np.save("dist.npy",np.array([[0,0],[1,2./3.],[2,2./3.],[2.00000001,0]]))
RF = RandomField(dimension = 2, dist_types=["File"], dist_params=[["dist.npy"]], name = "example_field", corr_l = 100., filesavetype="binary", x_range = [0.,size[0]], y_range = [0.,size[1]],  sampling_type = "LHS", corr_f = "exponential", rank_correlation = True,  grid_file = "points.npy",num_eig_estimation=2000, sparse = True)
RF.generateRandVariables(500, seed = 8)        #generation of random numbers, critical step
RF.generateFieldOnGrid()
RF.errorEvaluation(max_node_num = 5e3, grid_data = True)      #check of correlation, cross correlation and distribution, not needed
RF.saveGridNodesVTKDots()  #save field as VTK file  
#"""
