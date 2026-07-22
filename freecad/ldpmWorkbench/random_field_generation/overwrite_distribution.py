#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# created by Jan Elias
# jan.elias@vut.cz
# Brno University of Technology,
# 2021

import numpy as np
import os
import matplotlib.pyplot as plt
#from scipy.stats import norm, gamma, weibull_min, lognorm
#from scipy.spatial import Voronoi, Delaunay
#from scipy.special import gamma as gammafunc
#import shutil
#from grafted import GD, findGD
#from scipy.stats.stats import pearsonr, spearmanr

from rand_field_generator import RandomField  
from rand_field_generator import crateDistributionObject  

if __name__ == '__main__':

    RFname = "FIELD_Gaussian"
    varnum = 0
    disttype = "Gamma"
    distparams = [1.,0.8]    

    newRFname = RFname + "_transformed_" + disttype

    #load random field file
    RF = RandomField(readFromFolder = "FIELD_Gaussian")

    #load actual realizations of variable varnum
    GF = RF.loadNumpyFile(os.path.join(RF.folder,"fieldValues_%d"%varnum))

    #transform to probabilities
    GF = RF.dist[varnum].cdf(GF)

    #create distribution
    dist, stats = crateDistributionObject(disttype,distparams)

   #transform to new distribution
    GF = dist.ppf(GF)

    #save field
    if not os.path.isdir(newRFname): os.mkdir(newRFname)
    RF.saveNumpyFile(os.path.join(newRFname,"fieldValues_%d"%varnum), GF)  

    #check result
    plt.rcParams.update({'font.size': 18})
    plt.rcParams.update({'axes.linewidth': 2})
    plt.rcParams.update({'font.family' : 'serif'})
    plt.rcParams.update({'font.serif' : 'Times New Roman'})
    plt.rcParams.update({'text.usetex':True})

    hist, bins = np.histogram(GF, density=True, bins = int(np.sqrt(GF.size)))    
    fig = plt.figure()
    ax = fig.add_axes([0.15,0.15,0.8,0.8])
    ax.bar((bins[1:]+bins[:-1])/2., hist, color="k", alpha=0.5, width = (bins[1]-bins[0])*0.8)
    xlim = ax.get_xlim()
    x = np.linspace(xlim[0],xlim[1],num =100)
    y = dist.pdf(x)
    ax.plot(x,y,'-r',lw=2)
    fig.savefig(os.path.join(newRFname,'dist_error_%d.png'%varnum))
    #plt.show()
    plt.close(fig)   

    
