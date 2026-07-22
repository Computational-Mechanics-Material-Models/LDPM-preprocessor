#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# created by Jan Elias
# jan.elias@vut.cz
# Brno University of Technology,
# 2020

import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.stats import norm, gamma, weibull_min, lognorm, uniform, triang, truncnorm
from scipy.sparse.linalg import eigsh
from scipy.spatial import Voronoi, Delaunay
from scipy.special import gamma as gammafunc
import shutil
from freecad.ldpmWorkbench.random_field_generation.grafted import GD, findGD
from freecad.ldpmWorkbench.random_field_generation.custom_dist import pointDist
from scipy.stats.stats import pearsonr, spearmanr
from scipy.interpolate import interp1d
from scipy.sparse import bsr_array, coo_array
import sys
import time
try:
    from tqdm import tqdm
except Exception:
    def tqdm(iterable=None, *args, **kwargs):
        return iterable if iterable is not None else []

############################################################################################################    
############################################################################################################  
def crateDistributionObject(disttype,distparams):
    dist = []
    dist_stat = []
    if disttype == "Gaussian": 
        #mean + standard deviation
        dist = norm(distparams[0], distparams[1]) 
        dist_stat = [distparams[0],distparams[1]]
    elif disttype == "TruncatedGaussian": 
        #mean, standard deviation, cuttoff        
        dist = truncnorm((distparams[2]-distparams[0])/distparams[1], float('inf'), loc=distparams[0], scale=distparams[1]) 
        mean, variance = dist.stats()
        dist_stat = [mean, variance**0.5]
    elif disttype == "Triangular": 
        #a, b, c (peak position)
        dist = triang((distparams[2]-distparams[0])/(distparams[1]-distparams[0]), distparams[0], distparams[1]-distparams[0])        
        mean, variance = dist.stats()
        dist_stat = [mean, variance**0.5]
    elif disttype == "Uniform": 
        #a + b
        dist = uniform(distparams[0], distparams[1]-distparams[0])        
        dist_stat = [0.5*(distparams[0]+distparams[1]),1./np.sqrt(12.)*(distparams[1]-distparams[0])]
    elif disttype == "Gamma": 
        #mean + standard deviation
        shape = (distparams[0]/distparams[1])**2
        scale = (distparams[1]**2)/distparams[0]
        dist = gamma(shape, 0., scale)
        dist_stat = [distparams[0],distparams[1]]
    elif disttype == "Weibull": 
        #mean + shape
        mean = distparams[0]
        shape = distparams[1]
        scale = mean/gammafunc(1.+1./shape)
        dist = weibull_min(shape, 0., scale)
        mean, variance = dist.stats()
        dist_stat = [mean, variance**0.5]
    elif disttype == "Lognormal": 
        #mean + standard deviation
        mean = distparams[0]
        std = distparams[1]
        s = (np.log(1.+(std/mean)**2))**0.5
        scale = np.exp( np.log((mean**2) / ((mean**2 + std**2)**0.5) ) )
        dist = lognorm(s, 0., scale)
        dist_stat = [mean,std]
    elif disttype == "Grafted": 
        dist =  findGD(mean = distparams[0], std = distparams[1], m = distparams[2], Pgr =distparams[3]) 
        dist_stat = [distparams[0],distparams[1]]
    elif disttype == "File":
        filename=distparams[0]
        if filename.endswith(".npy"):
            d = np.load(filename)            
        else:
            d = np.loadtxt(filename)
        dist = pointDist(d)
        dist_stat = [dist.mean,dist.std]
    else: raise ValueError('Unknown distribution type: "%s"'%disttype)
    return dist, dist_stat

############################################################################################################    
############################################################################################################    

class RandomField():    
    def __init__(self, dimension = 3, readFromFolder = "none", dist_types=["Gaussian"], CC = np.array([[1]]), dist_params=[[0,1]], name="FIELD",corr_l = 0.5, corr_f='square_exponential',x_range=[0.,1],y_range=[0.,2],z_range=[0.,0.5], sampling_type = "Sobol", filesavetype="binary", periodic = False, rank_correlation=False, spatial_separation=True, grid_file = None, trace_fraction=0.99, grid_spacing = 1./3.,num_eig_estimation=200, sparse = False, corr_cutoff = 1e-3, save_indiv_realiz_files = False, memory_efficient=False):

        if readFromFolder == "none":
            self.dim = dimension            
            self.cross_correlation_matrix =np.array(CC)
            self.Nvar = self.cross_correlation_matrix.shape[0]

            if( (not self.Nvar == len(dist_types)) or (not self.Nvar == len(dist_params)) ):
                raise ValueError("Error: number of random field in 'dist_types', 'dist_params' and 'CC' does not correspond")

            self.name = name
        
            self.filesavetype = filesavetype

            self.dist_types = dist_types
            self.dist_params = dist_params

            self.corr_l = np.ones(3) #correlation length
            if hasattr(corr_l,"__len__"):
                if (len(corr_l)>=self.dim):
                    for i in range(self.dim): self.corr_l[i] = corr_l[i]
                else:
                    raise ValueError("Correlation length array is too short, len = ", len(corr_l))
            else:
                self.corr_l *= corr_l

            self.corr_f = corr_f #correlation function
            self.rank_corr = rank_correlation#using Spearman or Pearson correlation

            self.spat_sep = spatial_separation

            self.trace_fraction = trace_fraction
            self.grid_spacing = grid_spacing; #for computational reason might be 1/3
            self.num_eig_estimation = num_eig_estimation

            self.x_range = np.array(x_range)
            self.y_range = np.array(y_range)
            if self.dim<2: self.y_range=np.array([0,0])
            self.z_range = np.array(z_range)
            if self.dim<3: self.z_range=np.array([0,0])

            self.grid_file = grid_file


            self.sampling_type = sampling_type# MC, LHS, Freet or Sobol
            self.folder = self.name

            self.periodic = np.array([0,0,0]).astype(bool)
            if hasattr(periodic, '__len__'): 
                for i in range(min(len(self.periodic),len(periodic))):
                    self.periodic[i] = bool(periodic[i])
            elif (bool(periodic)):   
                for i in range(3):
                    self.periodic[i] = True

            self.sparse = sparse
            self.covmat_cutoff = corr_cutoff #correlation bellow treated as zero

            self.save_separated = save_indiv_realiz_files
            self.memory_eff = memory_efficient

            self.saveReport()

        else: 
            self.folder = readFromFolder
            self.loadReport()
            
        self.createDistributionObjects()

        self.corr_l2 = np.square(self.corr_l)

        if self.periodic[0]: gap_mult=0
        else: gap_mult=1
        self.x_range_gap = np.array([self.x_range[0]-gap_mult*self.corr_l[0],self.x_range[1]+gap_mult*self.corr_l[0]])
        if self.dim<2: 
            self.y_range_gap=np.array([0,0])
        else: 
            if self.periodic[1]: gap_mult=0
            else: gap_mult=1
            self.y_range_gap = np.array([self.y_range[0]-gap_mult*self.corr_l[1],self.y_range[1]+gap_mult*self.corr_l[1]])
        if self.dim<3: 
            self.z_range_gap=np.array([0,0])
        else: 
            if self.periodic[2]: gap_mult=0
            else: gap_mult=1
            self.z_range_gap = np.array([self.z_range[0]-gap_mult*self.corr_l[2],self.z_range[1]+gap_mult*self.corr_l[2]]) 

        if (self.grid_file is not None) or (self.corr_f != "square_exponential"):
            self.spat_sep = False      

        self.spatialFactorization()
        self.loadRandomVariables()

    #############################################################################
    def loadReport(self):

        reportFile = os.path.join(self.folder, "report.dat")
        print("Loading random field from file " + reportFile); sys.stdout.flush()
        self.grid_file = None

        if not os.path.isfile(reportFile): raise ValueError("Error: report file " + reportFile + " not found" )

        self.name = os.path.basename(os.path.normpath(self.folder))
    
        self.cross_correlation_matrix = np.array([[1]]) 

        f = open(reportFile,"r")
        while True:
            line = f.readline()
            if not line: break

            line = line.split()
            if not line:
                continue
            if   line[0] =="dimension:": self.dim = int(line[1])
            elif   line[0] =="range_x:": self.x_range = np.array([float(line[1]), float(line[2])])
            elif line[0] =="range_y:": self.y_range = np.array([float(line[1]), float(line[2])])
            elif line[0] =="range_z:": self.z_range = np.array([float(line[1]), float(line[2])])
            elif line[0] =="correlation_length:": self.corr_l = np.array([float(line[1]),float(line[2]),float(line[3])])
            elif line[0] =="correlation_function:": self.corr_f = line[1]
            elif line[0] =="number_of_variables:": self.Nvar = int(line[1])
            elif line[0] =="distributions:": 
                k = 1
                self.dist_types = []
                self.dist_params = []
                for var in range(self.Nvar):
                    self.dist_types.append(line[k])
                    pl = int(line[k+1])
                    params = []
                    for l in range(pl):
                        params.append(float(line[k+2+l]))
                    self.dist_params.append(params)
                    k=k+2+pl
            elif line[0] =="cross_correlation:": 
                self.cross_correlation_matrix = np.ones((self.Nvar,self.Nvar))
                k = 1
                for i in range(self.Nvar):
                    for j in range(i+1,self.Nvar):
                        self.cross_correlation_matrix[i,j] = self.cross_correlation_matrix[j,i]  = float(line[k])
                        k = k+1
            elif line[0] =="save_type:": self.filesavetype = line[1]
            elif line[0] =="sampling_type:": self.sampling_type = line[1]
            elif line[0] =="rank_correlation:": self.rank_corr = bool(int(line[1]))
            elif line[0] =="periodic:": self.periodic = np.array(line[1:]).astype(float).astype(bool)
            elif line[0] =="grad_spacing:": self.grid_spacing = float(line[1])
            elif line[0] =="trace_fraction:": self.trace_fraction = float(line[1])
            elif line[0] =="spatial_separation:": self.spat_sep = bool(int(line[1]))
            elif line[0] =="memory_efficient:": self.memory_eff = bool(int(line[1]))
            elif line[0] =="grid_file:": self.grid_file = line[1]
            elif line[0] =="num_eig_estimation:": self.num_eig_estimation = int(line[1])
            elif line[0] =="sparse:": self.sparse = bool(int(line[1]))
            elif line[0] =="save_indiv_realiz_files:": self.save_separated = bool(int(line[1]))
            elif line[0] =="corr_cutoff:": self.covmat_cutoff = float(line[1])
        f.close()


    #############################################################################
    def saveReport(self):
        if not os.path.isdir(self.folder): os.mkdir(self.folder)

        report_path = os.path.join(self.folder, "report.dat")
        with open(report_path, "w", newline="\n") as f:
            f.write("field_name:\t%s\n"%self.name)
            f.write("dimension:\t%d\n"%self.dim)
            f.write("range_x:\t%e\t%e\n"%(self.x_range[0],self.x_range[1]))
            f.write("range_y:\t%e\t%e\n"%(self.y_range[0],self.y_range[1]))
            f.write("range_z:\t%e\t%e\n"%(self.z_range[0],self.z_range[1]))
            f.write("correlation_length:\t%e\t%e\t%e\n"%(self.corr_l[0],self.corr_l[1],self.corr_l[2]))
            f.write("correlation_function:\t%s\n"%self.corr_f)
            f.write("number_of_variables:\t%d\n"%self.Nvar)
            f.write("distributions:")
            for i in range(self.Nvar):
                f.write("\t%s\t%d"%(self.dist_types[i],len(self.dist_params[i])))
                if self.dist_types[i]=="file": f.write("\t%s"%self.dist_params[i][0])
                else:
                    for j in self.dist_params[i]:
                        if isinstance(j, str):
                            f.write("\t%s"%j)
                        else:
                            f.write("\t%e"%j)
            f.write("\n")
            if (self.Nvar>1):
                f.write("cross_correlation:")
                for i in range(self.Nvar):
                    for j in range(i+1,self.Nvar):
                        f.write("\t%e"%self.cross_correlation_matrix[i,j])
                f.write("\n")
            f.write("save_type:\t%s\n"%self.filesavetype)
            f.write("sampling_type:\t%s\n"%self.sampling_type)
            f.write("rank_correlation:\t%d\n"%self.rank_corr)
            f.write("periodic:\t%d\t%d\t%d\n"%(self.periodic[0],self.periodic[1],self.periodic[2]))
            f.write("grad_spacing:\t%e\n"%self.grid_spacing)
            f.write("trace_fraction:\t%e\n"%self.trace_fraction)
            f.write("spatial_separation:\t%d\n"%self.spat_sep)
            f.write("memory_efficient:\t%d\n"%self.memory_eff)
            f.write("save_indiv_realiz_files:\t%d\n"%self.save_separated)
            f.write("num_eig_estimation:\t%d\n"%self.num_eig_estimation)
            f.write("corr_cutoff:\t%e\n"%self.covmat_cutoff)
            f.write("sparse:\t%d\n"%self.sparse)


    #############################################################################
    def saveNumpyFile(self, name, data, fmt="%e"):
        if self.filesavetype == "binary":
            np.save(os.path.join(self.folder,name), data)
        else:
            np.savetxt(os.path.join(self.folder,name+".dat"), data,fmt=fmt)

    #############################################################################
    def checkNUmpyFileExistence(self, name):
        appendix = ".dat"
        if self.filesavetype == "binary": appendix = ".npy"
        if os.path.isfile(os.path.join(self.folder, name + appendix)): return True
        else: return False

    #############################################################################
    def loadNumpyFile(self, name):
        if self.filesavetype == "binary":
            return np.load(os.path.join(self.folder,name + ".npy"))
        else:
            return np.loadtxt(os.path.join(self.folder,name + ".dat"))
            
    #############################################################################
    def checkNumpyFileExistence(self, name):
        if self.filesavetype == "binary":
            return os.path.isfile(os.path.join(self.folder,name + ".npy"))
        else:
            return os.path.isfile(os.path.join(self.folder,name + ".dat"))            

    #############################################################################
    def createDistributionObjects(self):
        self.dist = [] #objects
        self.dist_stat = [] #mean and standard deviation
        for i in range(self.Nvar):
            d1, d2 = crateDistributionObject(self.dist_types[i],self.dist_params[i])
            self.dist.append( d1 )
            self.dist_stat.append( d2 )


    #############################################################################
    def getCorrelation(self,X2):
        a = np.zeros(len(X2))
        for d in range(self.dim):
            a += X2[:,d]/self.corr_l2[d]
        if self.corr_f == "square_exponential": 
            return np.exp(-a)
        elif self.corr_f == "exponential": 
            return np.exp(-np.sqrt(a))
        else: 
            raise ValueError("Error: autocorrelation function", self.corr_f, "not implemented")
            exit(1)        

    #############################################################################
    def generateSpatialCovarianceMatrixSeparated(self,X,lab):
        print("Generating covariance matrix %s"%lab); sys.stdout.flush()

        if lab=="X":
            xsize = self.x_range[1]-self.x_range[0]
            direction = 0
        elif lab=="Y":  
            xsize = self.y_range[1]-self.y_range[0]
            direction = 1
        elif lab=="Z":  
            xsize = self.z_range[1]-self.z_range[0]
            direction = 2
        else: 
            print("unknow covariance matrix type"); sys.stdout.flush()
            exit(1)
        nx = len(X);
        CX = np.zeros([nx,nx]);
        for i in range(nx):
            dist2 = np.zeros((nx,3))
            dx = abs(X[i]-X)
            if self.periodic[direction]:
                dx = np.minimum(dx,xsize-dx)
            dist2[:,direction] = np.square(dx);
            corr = self.getCorrelation(dist2)
            corr[np.where(corr<self.covmat_cutoff)[0]] = 0.
            CX[i,:] = corr
        print("[DONE]"); sys.stdout.flush()
        return CX


    #############################################################################
    def generateSpatialCovarianceMatrixCompactSparse(self, nodes):
        print("Generating sparse covariance matrix"); sys.stdout.flush()
        
        size = np.zeros(3)
        size[0] = self.x_range[1]-self.x_range[0]
        size[1] = self.y_range[1]-self.y_range[0]
        size[2] = self.z_range[1]-self.z_range[0]

        n = nodes.shape[0]
        m = self.grid.shape[0]
        row = []
        col = []
        data = []
                
        for i in tqdm(range(n)):
            d2 = np.zeros((m,3))
            for j in range(self.dim):
                dx = abs(self.grid[:,j]-nodes[i,j])
                if self.periodic[j]:
                    dx = np.minimum(dx,size[j]-dx)
                d2[:,j] = np.square(dx)
            corr = self.getCorrelation(d2)
            ind = np.where(np.abs(corr)>self.covmat_cutoff)[0]           
            data.append(corr[ind].astype("float32"))
            col.append(ind)
            row.append(np.zeros(len(ind)).astype(int) + i)            
            #if i%1000==0: print("progress {:2.1%}".format(float(i)/n),)


        data = np.concatenate(data)
        row = np.concatenate(row)
        col = np.concatenate(col)
        D0 = coo_array((data, (row, col)), shape=(n, m))
        return D0

    #############################################################################
    def generateSpatialCovarianceMatrixCompact(self, nodes):

        if self.sparse: return self.generateSpatialCovarianceMatrixCompactSparse(nodes)
        
        print("Generating covariance matrix"); sys.stdout.flush()

        size = np.zeros(3)
        size[0] = self.x_range[1]-self.x_range[0]
        size[1] = self.y_range[1]-self.y_range[0]
        size[2] = self.z_range[1]-self.z_range[0]

        n = nodes.shape[0]
        m = self.grid.shape[0]
        D0 = np.zeros((n,m))        
        
        for i in tqdm(range(n)):
            d2 = np.zeros((m,3))
            for j in range(self.dim):
                dx = abs(self.grid[:,j]-nodes[i,j])
                if self.periodic[j]:
                    dx = np.minimum(dx,size[j]-dx)
                d2[:,j] = np.square(dx)                
            corr = self.getCorrelation(d2)
            ind = np.where(np.abs(corr)<self.covmat_cutoff)[0]
            corr[ind]=0
            D0[i,:] = corr
            #if i%1000==0: print("progress {:2.1%}".format(float(i)/n),)
        print("[DONE]")
        return D0

    #############################################################################
    # based on Li HS, Lü ZZ, Yuan XK. Nataf transformation based point estimate method. Chin Sci Bull 2008;53(17):2586–92

    def natafTransformation(self,var1, var2, corr0, Ngausspoints=6, p=0.005):
    
        if abs(corr0)<1E-10:return 0.
        if abs(corr0)>1.-1E-10: return 1.

        if Ngausspoints==2:
            Z = [-1,1]
            P = [0.5,0.5]
        elif Ngausspoints==3: 
            Z = [-1.73205080757,0,1.73205080757]
            P = [0.166666666667,0.66666666666,0.166666666667]
        elif Ngausspoints==4: 
            Z = [-2.33441421834,-0.74196378430,0.74196378430,2.33441421834]
            P = [0.045875854768,0.454124145232,0.454124145232,0.045875854768]
        elif Ngausspoints==5: 
            Z = [-2.85697001387,-1.3552617997,0,1.3552617997,2.85697001387]
            P = [0.011257411328,0.222075922006,0.533333333333,0.222075922006,0.011257411328]
        elif Ngausspoints==6: 
            Z = [-3.32425743359,-1.88917587773,-0.616706590154,0.616706590154,1.88917587773,3.32425743359]
            P = [0.00255578440233,0.088615746029,0.408828469542,0.408828469542,0.088615746029,0.00255578440233]
        elif Ngausspoints==7: 
            Z = [-3.75043971768,-2.36675941078,-1.1544053948,0,1.1544053948,2.36675941078,3.75043971768]
            P = [0.000548268858737,0.0307571239681,0.240123178599,0.457142857143,0.240123178599,0.0307571239681,0.000548268858737]
        else: raise ValueError('Number of Guass points out of range 2-7')
    
    
        RN = corr0
        R = 0.
        it = 0
        while abs(RN-R)/corr0>p:
            R = RN; S = 0.; C = np.array([[1., R],[R, 1.]])
            L = np.linalg.cholesky(C)
            for i in range(Ngausspoints):
                for j in range(Ngausspoints):
                    Y = np.dot(L,np.array([Z[i],Z[j]]))                    
                    X = [self.dist[var1].ppf(norm.cdf(Y[0])), self.dist[var2].ppf(norm.cdf(Y[1]))]
                    S = S+P[i]*P[j]*(X[0]-self.dist_stat[var1][0])*(X[1]-self.dist_stat[var2][0])/(self.dist_stat[var1][1] * self.dist_stat[var2][1])
            RN = corr0+R-S
            it +=1            
        corr = RN
        return corr

    #############################################################################
    def natafTransformationInterpolationUniform(self):
        #return interp1d([-1,1], [-1,1])
        return interp1d([0.000000e+00, 2.040816e-02, 4.081633e-02, 6.122449e-02, 8.163265e-02, 1.020408e-01, 1.224490e-01, 1.428571e-01, 1.632653e-01, 1.836735e-01, 2.040816e-01, 2.244898e-01, 2.448980e-01, 2.653061e-01, 2.857143e-01, 3.061224e-01, 3.265306e-01, 3.469388e-01, 3.673469e-01, 3.877551e-01, 4.081633e-01, 4.285714e-01, 4.489796e-01, 4.693878e-01, 4.897959e-01, 5.102041e-01, 5.306122e-01, 5.510204e-01, 5.714286e-01, 5.918367e-01, 6.122449e-01, 6.326531e-01, 6.530612e-01, 6.734694e-01, 6.938776e-01, 7.142857e-01, 7.346939e-01, 7.551020e-01, 7.755102e-01, 7.959184e-01, 8.163265e-01, 8.367347e-01, 8.571429e-01, 8.775510e-01, 8.979592e-01, 9.183673e-01, 9.387755e-01, 9.591837e-01, 9.795918e-01, 1.000000e+00],[0.000000e+00, 2.136383e-02, 4.272437e-02, 6.407833e-02, 8.542249e-02, 1.067537e-01, 1.280689e-01, 1.493651e-01, 1.706395e-01, 1.918894e-01, 2.131121e-01, 2.343051e-01, 2.554661e-01, 2.765928e-01, 2.976829e-01, 3.187343e-01, 3.397449e-01, 3.607124e-01, 3.816349e-01, 4.025101e-01, 4.233358e-01, 4.441097e-01, 4.648295e-01, 4.854927e-01, 5.060967e-01, 5.266388e-01, 5.471161e-01, 5.675258e-01, 5.878646e-01, 6.081293e-01, 6.283165e-01, 6.484226e-01, 6.684438e-01, 6.883761e-01, 7.082154e-01, 7.279572e-01, 7.475969e-01, 7.671294e-01, 7.865494e-01, 8.058511e-01, 8.250283e-01, 8.440744e-01, 8.629822e-01, 8.817441e-01, 9.006229e-01, 9.188518e-01, 9.368274e-01, 9.545182e-01, 9.730748e-01, 1.000000e+00])

    #############################################################################
    def backNatafTransformation(self,NG):
        NG2 = np.zeros(NG.shape)
        for var in range(self.Nvar):
            NG2[var] = self.dist[var].ppf(norm.cdf(NG[var]))   
        return NG2


    #############################################################################
    def natafTransformationInterpolation(self,var):

        #Spearman rank correlation
        if self.dist_types[var]=='Gaussian': 
            return interp1d([-1,1], [-1,1])
        elif self.dist_types[var]=='Uniform': 
            return self.natafTransformationInterpolationUniform()
        elif self.checkNUmpyFileExistence("NatafTransform_%d"%var):
            print("Loading Nataf transformation of model %d"%var); sys.stdout.flush()
            x,NR = self.loadNumpyFile("NatafTransform_%d"%var)
            return interp1d(x, NR)

        print("Nataf transformation of model %d"%var); sys.stdout.flush()
        # Nataf transformation - approximate
        ni = 0
        N = 50
        x = np.linspace(0,1,N)
        NR = np.zeros(N);
        for i in range(N): NR[i] = self.natafTransformation(var,var, x[i]) 

        if 1:
            self.saveNumpyFile('NatafTransform_%d'%var,np.vstack([x,NR]))

            try:
                plt.rcParams.update({'font.size': 18})
                plt.rcParams.update({'axes.linewidth': 2})
                plt.rcParams.update({'font.family' : 'serif'})
                plt.rcParams.update({'font.serif' : 'Times New Roman'})
                plt.rcParams.update({'text.usetex':False})
    
                fig = plt.figure()
                ax = fig.add_axes([0.15,0.15,0.8,0.8])
                ax.plot([0,1],[0,1],':',color="grey",lw=2)
                ax.plot(x,NR,'-o',color="k",lw=1.5)
                ax.set_xlim([0,1]); ax.set_ylim([0,1])
                #ax.axis("equal")
                ax.set_xlabel("correlation in original space"); ax.set_ylabel("correlation in Gaussian space")            
                fig.savefig(os.path.join(self.folder,'NatafTransform_%d.png'%var))
                #plt.show()
                plt.close(fig)
            except Exception as plot_error:
                print(f"Skipping Nataf plot for model {var}: {plot_error}"); sys.stdout.flush()
            
        print("[DONE]"); sys.stdout.flush()
        return interp1d(x, NR)

    #############################################################################
    def natafTransformationCrossCorMatrix(self):

        print("Nataf transformation of cross correlation matrix"); sys.stdout.flush()
        self.cross_correlation_matrix_transformed = np.ones((self.Nvar,self.Nvar))
        if self.rank_corr:
            #the uniform distribution is used to transform Spearman correlation from uniform distribution to Gaussian, the decomposition is 
            unifint = self.natafTransformationInterpolationUniform()
            self.cross_correlation_matrix_transformed = unifint(self.cross_correlation_matrix)
        else:
            for i in range(self.Nvar):
                for j in range(i+1,self.Nvar):
                    if self.dist_types[i]=='Gaussian' and self.dist_types[j]=='Gaussian':
                        self.cross_correlation_matrix_transformed[i,j] = self.cross_correlation_matrix_transformed[j,i] = self.cross_correlation_matrix[i,j]
                    else:
                        self.cross_correlation_matrix_transformed[i,j] = self.cross_correlation_matrix_transformed[j,i] = self.natafTransformation(i,j, self.cross_correlation_matrix[i,j])
        print("[DONE]"); sys.stdout.flush()

    #############################################################################
    def findAllEigenvalues(self,C):
        if C.shape[0]==1: return np.array([1]), np.array([[1]])

        lam, EV =np.linalg.eig(C)
        #lam, EV = sparse.linalg.eigs(C, k=C.shape[0], which='LR', return_eigenvectors=True)
        #lam = np.real(lam)
        #EV = np.real(EV)

        ind = np.flipud(np.argsort(lam))
        lam = lam[ind]
        EV = EV[:,ind]
        return lam, EV 

    #############################################################################
    def findLargetsEigenvalues(self,C,eigsnum):
        print("searching for eigenvalues and eigenvectors"); sys.stdout.flush()
        
        trace = C.trace()

        if  eigsnum == -1:
            n = C.shape[0]
            nstep = int(n/4)
            initest = self.num_eig_estimation

            #C = sparse.coo_matrix(C)
            k = min(initest,n-1)
            lam, EV = eigsh(C, k=k)
            p = 0        
            print("found ",len(lam),"eigenvalues corresponding to ", sum(lam)/trace," of trace" ); sys.stdout.flush()
            while sum(lam)/trace<self.trace_fraction:
                p += 1
                k = min(initest+p*nstep,n-1)
                lam, EV = eigsh(C, k=k)
                print("found ",len(lam),"eigenvalues corresponding to ", sum(lam)/trace," of trace" ); sys.stdout.flush()
            lam = np.flipud(lam)
            EV = np.fliplr(EV)
            t = 0
            sumL = lam[0];
            while sumL<trace*self.trace_fraction:
                t += 1
                sumL += lam[t]
        
            lam = lam[:t+1]; EV = EV[:,:t+1]
        else:
            lam, EV = eigsh(C, k=eigsnum)
        print("[DONE] used %d eigenvalues, %.3f%% of trace"%(len(lam),np.sum(lam)/trace*100.)); sys.stdout.flush()
        return lam, EV    

    #############################################################################
    def separate2FullEigenvaluesSpatial(self, lambdaX,lambdaY,lambdaZ):

        print("Combination of eigenmodes"); sys.stdout.flush()
        nx = len(lambdaX); ny = len(lambdaY); nz = len(lambdaZ)
        n = nx*ny*nz

        lam = np.zeros(nx*ny*nz)
        ijk = np.zeros([nx*ny*nz,3]).astype("int")
        n = 0    
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    lam[i*ny*nz+j*nz+k] = lambdaX[i]*lambdaY[j]*lambdaZ[k]
                    ijk[n,:] = [i,j,k]
                    n += 1

        ind = np.flipud(np.argsort(lam))
        lam = lam[ind]
        ijk = ijk[ind,:]
        
        t = 0
        D = lam/np.sum(lam)
        sumD = 0.
        while sumD<self.trace_fraction:
            sumD = sumD+D[t]
            t += 1

        p = sum(lam[:t+1])/sum(lam)
        ijk = ijk[:t+1,:]

        print("[DONE] used %d eigenvalues, %.3f%% of trace"%(t,p*100)); sys.stdout.flush()
        return ijk

    #############################################################################    
    def saveFactorization(self):

        if self.spat_sep:
            for mod in range(self.num_nataf):
                self.saveNumpyFile("eigenvalues_X_%d"%mod,self.eigenValsXYZ[mod][0])
                self.saveNumpyFile("eigenvalues_Y_%d"%mod,self.eigenValsXYZ[mod][1])
                self.saveNumpyFile("eigenvalues_Z_%d"%mod,self.eigenValsXYZ[mod][2])
                self.saveNumpyFile("eigenvectors_X_%d"%mod,self.eigenVecsXYZ[mod][0])
                self.saveNumpyFile("eigenvectors_Y_%d"%mod,self.eigenVecsXYZ[mod][1])
                self.saveNumpyFile("eigenvectors_Z_%d"%mod,self.eigenVecsXYZ[mod][2])
            self.saveNumpyFile("ijk",self.ijk,fmt='%d')
        else: 
            for mod in range(self.num_nataf):
                self.saveNumpyFile("eigenvalues_%d"%mod,self.lam[mod])
                self.saveNumpyFile("eigenvectors_%d"%mod,self.EV[mod])
        if( self.Nvar>1 ):
            self.saveNumpyFile("eigenvalues_C",self.eigenValsC)
            self.saveNumpyFile("eigenvectors_C",self.eigenVecsC)

    #############################################################################    
    def generateSpatialGrid(self):

        if not self.grid_file==None:
            if self.grid_file.endswith(".npy"): 
                self.grid = np.load(self.grid_file)
            else: 
                self.grid = np.loadtxt(self.grid_file)
        else:
            #generate grid nodes
            if self.checkNUmpyFileExistence("grid_nodesX") and self.checkNUmpyFileExistence("grid_nodesY") and self.checkNUmpyFileExistence("grid_nodesZ"):
                print("Loading grid"); sys.stdout.flush()
                self.GX = self.loadNumpyFile("grid_nodesX")
                self.GY = self.loadNumpyFile("grid_nodesY")
                self.GZ = self.loadNumpyFile("grid_nodesZ")
            else:                        
                #CREATE GRID 
                print("Generating grid"); sys.stdout.flush()
                gs = self.grid_spacing*self.corr_l
                xw = (self.x_range_gap[1]-self.x_range_gap[0]); xn = int(np.ceil(xw/gs[0])+0.5); x0 = self.x_range_gap[0]+(xw-xn*gs[0])/2.
                yw = (self.y_range_gap[1]-self.y_range_gap[0]); yn = int(np.ceil(yw/gs[1])+0.5); y0 = self.y_range_gap[0]+(yw-yn*gs[1])/2.
                zw = (self.z_range_gap[1]-self.z_range_gap[0]); zn = int(np.ceil(zw/gs[2])+0.5); z0 = self.z_range_gap[0]+(zw-zn*gs[2])/2.

                self.GX = np.arange(x0,x0+(xn+0.1)*gs[0],gs[0])
                self.GY = np.arange(y0,y0+(yn+0.1)*gs[1],gs[1])
                self.GZ = np.arange(z0,z0+(zn+0.1)*gs[2],gs[2])

                self.saveNumpyFile("grid_nodesX", self.GX)
                self.saveNumpyFile("grid_nodesY", self.GY)
                self.saveNumpyFile("grid_nodesZ", self.GZ)

            X, Y, Z = np.meshgrid(self.GX,self.GY,self.GZ, indexing="ij");
            X = np.reshape(X,[-1,1]); Y = np.reshape(Y,[-1,1]); Z = np.reshape(Z,[-1,1])
            self.grid = np.hstack([X,Y,Z])
        self.saveNumpyFile("grid_nodes", self.grid)


    #############################################################################
    def crossCorrelationFactorization(self): 
        # spectral decomposition of cross correlation matrix
        if (self.Nvar>1):
            if self.checkNUmpyFileExistence("eigenvalues_C") and  self.checkNUmpyFileExistence("eigenvectors_C"):
                    self.eigenValsC = self.loadNumpyFile("eigenvalues_C")
                    self.eigenVecsC = self.loadNumpyFile("eigenvectors_C")
            else:
                self.natafTransformationCrossCorMatrix()
                self.eigenValsC, self.eigenVecsC = self.findAllEigenvalues(self.cross_correlation_matrix_transformed)
                if(min(self.eigenValsC)<0): raise ValueError("Error: cross correlation matrix is not positive definite")
        else:
            self.eigenValsC = np.ones(1)
            self.eigenVecsC = np.ones((1,1))

    #############################################################################
    def createNatafModels(self):
        self.generateSpatialGrid()
        self.crossCorrelationFactorization()

        self.nataf_interp = []
        self.nataf_interp_codes = np.zeros(self.Nvar).astype(int)
        if self.rank_corr == True:
            self.nataf_interp.append(self.natafTransformationInterpolationUniform())
        else:
            for var in range(self.Nvar):
                found = False
                for prevvar in range(var):
                    if self.dist_types[var]==self.dist_types[prevvar]:
                        if self.dist_params[var]==self.dist_params[prevvar] or self.dist_types[var]=="Uniform" or self.dist_types[var]=="Gaussian":
                            found = True
                            self.nataf_interp_codes[var] = self.nataf_interp_codes[prevvar]    
                if not found:
                    self.nataf_interp_codes[var] = len(self.nataf_interp)
                    self.nataf_interp.append(self.natafTransformationInterpolation(var))

        self.num_nataf = len(self.nataf_interp) 

    #############################################################################
    def spatialFactorization(self):      
        
        self.createNatafModels()

        #find eigenvalues and eigenvectors
        if self.spat_sep:
            allFilesFound = True

            for mod in range(self.num_nataf):
                if (not self.checkNUmpyFileExistence("eigenvalues_X_%d"%mod)) or  (not self.checkNUmpyFileExistence("eigenvalues_Y_%d"%mod)) or (not self.checkNUmpyFileExistence("eigenvalues_Z_%d"%mod)) or (not self.checkNUmpyFileExistence("eigenvectors_X_%d"%mod)) or  (not self.checkNUmpyFileExistence("eigenvectors_Y_%d"%mod)) or (not self.checkNUmpyFileExistence("eigenvectors_Z_%d"%mod)):
                     allFilesFound = False
            
            if not self.checkNUmpyFileExistence("ijk"):
                 allFilesFound = False

            if allFilesFound:
                print("Loading factorization from",self.folder); sys.stdout.flush()                

                self.eigenValsXYZ = []
                self.eigenVecsXYZ = []
                for mod in range(self.num_nataf):
                    self.eigenValsXYZ.append([ self.loadNumpyFile("eigenvalues_X_%d"%mod), self.loadNumpyFile("eigenvalues_Y_%d"%mod), self.loadNumpyFile("eigenvalues_Z_%d"%mod)])
                    self.eigenVecsXYZ.append([ self.loadNumpyFile("eigenvectors_X_%d"%mod), self.loadNumpyFile("eigenvectors_Y_%d"%mod), self.loadNumpyFile("eigenvectors_Z_%d"%mod)])

                self.ijk = (self.loadNumpyFile("ijk")).astype(int)

            else:  
                

                # compute covariance matrix
                CXraw = self.generateSpatialCovarianceMatrixSeparated(self.GX,"X")
                CYraw = self.generateSpatialCovarianceMatrixSeparated(self.GY,"Y")
                CZraw = self.generateSpatialCovarianceMatrixSeparated(self.GZ,"Z")

                GaussEigenValsX, GaussEigenVecsX = self.findAllEigenvalues(CXraw)
                GaussEigenValsY, GaussEigenVecsY = self.findAllEigenvalues(CYraw)
                GaussEigenValsZ, GaussEigenVecsZ = self.findAllEigenvalues(CZraw)

                self.ijk = self.separate2FullEigenvaluesSpatial(GaussEigenValsX,GaussEigenValsY,GaussEigenValsZ)

                # spectral decomposition of covariance matrix
                self.eigenValsXYZ = []
                self.eigenVecsXYZ = []

                for code in range(self.num_nataf):
                    CX = self.nataf_interp[code](CXraw)
                    CY = self.nataf_interp[code](CYraw)
                    CZ = self.nataf_interp[code](CZraw)
                    eigenValsX, eigenVecsX = self.findAllEigenvalues(CX)
                    eigenValsY, eigenVecsY = self.findAllEigenvalues(CY)
                    eigenValsZ, eigenVecsZ = self.findAllEigenvalues(CZ)
          
                    self.eigenValsXYZ.append([eigenValsX,eigenValsY,eigenValsZ])
                    self.eigenVecsXYZ.append([eigenVecsX,eigenVecsY,eigenVecsZ])                                                                
                                
                self.saveFactorization()
            self.Neig = self.ijk.shape[0]*self.Nvar
        else:
            self.lam = []
            self.EV = []
            for mod in range(self.num_nataf):
                if self.checkNUmpyFileExistence("eigenvalues_%d"%mod) and self.checkNUmpyFileExistence("eigenvectors_%d"%mod):   
                    self.lam.append(self.loadNumpyFile("eigenvalues_%d"%mod))
                    self.EV.append(self.loadNumpyFile("eigenvectors_%d"%mod))
                else:
                    C = self.generateSpatialCovarianceMatrixCompact(self.grid)
                    eignum = -1
                    if mod>1: eignum = len(self.lam[0])
                    if self.sparse:
                        C.data = self.nataf_interp[mod](C.data)
                    else:
                        C = self.nataf_interp[mod](C)
                    lam,EV = self.findLargetsEigenvalues(C,eignum)
                    self.lam.append(lam)
                    self.EV.append(EV)
            self.saveFactorization()

            self.Neig = len(self.lam[0])*self.Nvar

    #############################################################################
    def saveRandomVariables(self):
        self.saveNumpyFile("random_variables",self.X)  

    #############################################################################
    def loadRandomVariables(self):
        if not self.checkNumpyFileExistence("random_variables"): return;
        print("Loading random variables"); sys.stdout.flush()
        self.X = self.loadNumpyFile("random_variables")
        self.Nrealz = self.X.shape[1]      
        if not self.X.shape[0] == self.Neig:
            print("Error: number of eigenvalues dos not correspond to data in random_variables file"); sys.stdout.flush()
    
    #############################################################################
    
    def generateRandVariables(self, Nrealz, seed = "none"):

        if seed == "none": 
            seed = np.random.rand()
        np.random.seed(seed)

        self.Nrealz = Nrealz
        if self.checkNUmpyFileExistence("random_variables"):
            print("Loading random variables"); sys.stdout.flush()
            self.X = self.loadNumpyFile("random_variables")
            if( not self.X.shape[1] == self.Nrealz):
                raise ValueError("Error: required %d realizations, file %s contains %d realizations"%(self.Nrealz,"random_variables"+self.giveNumpyExt(), self.X.shape[1]))
        else:
            print("Generating random variables"); sys.stdout.flush()
            if self.sampling_type=="MC": 
                self.X = np.random.rand(self.Neig,self.Nrealz)
                self.X = norm.ppf(self.X, loc=0., scale=1.)
            elif self.sampling_type=="LHS": 
                self.X = np.zeros([self.Neig,self.Nrealz])
                row = (np.arange(self.Nrealz)+0.5)/self.Nrealz
                for i in range(self.Neig): self.X[i,:]= np.random.permutation(row)
                self.X = norm.ppf(self.X, loc=0., scale=1.)
            elif self.sampling_type=='LHS_RAND':
                self.X = np.zeros([self.Neig,self.Nrealz])
                row = np.arange(self.Nrealz)
                for i in range(self.Neig): self.X[i,:]= (np.random.permutation(row) + np.random.rand(self.Nrealz))/self.Nrealz
                self.X = norm.ppf(self.X, loc=0., scale=1.)
            elif self.sampling_type=='LHS_MED':
                self.X = np.zeros([self.Neig,self.Nrealz])                                
                int_sep = 100
                row = np.zeros(self.Nrealz)
                for i in range(self.Nrealz):     
                    delta = 1./float(self.Nrealz)
                    vals = np.linspace((i+1./(2*int_sep))*delta, (i+1-1./(2*int_sep))*delta, num=int_sep, endpoint=True)
                    vals = norm.ppf(vals)
                    row[i] = np.sum(vals)/int_sep
                for i in range(self.Neig): 
                    self.X[i,:]= np.random.permutation(row)
            elif self.sampling_type=='Freet':
                fin = open(os.path.join(self.folder,"FreetInput.fre"),"w")
                fin.write("[General]\nCountOfSimulations=%d\n"%self.Nrealz)
                fin.write("TypeOfCorrCoef=0\nTypeOfSampling=%d\n\n"%0)
                fin.write("[Category]\nName=X%d\n\n"%self.Nrealz)
                for i in range(len(self.lam)): fin.write("[Variable]\nName=%04d\nDistribution=NORM\nMean=0\nStd=1\nSkew=0\nKurt=0\n\n"%i)
                fin.write("[Category]\nName=Comparative values\n\n") 
                fin.write("[CorrelationMatrix]\n") 
                fin.close()

                curpath = os.getcwd()
                os.chdir(self.folder)
                os.system("FreetInput.fre")
                os.chdir(curpath)

                with open(os.path.join(self.folder,"FreetInput.fre"), "r") as fout: content = fout.read().splitlines()
                conent = np.array(content)
                ind = [i for i,c in enumerate(content) if "[Values]" in content[i]]
                self.X = np.zeros([self.Neig,self.Nrealz])
                for i in  range(self.Neig): 
                    self.X[i,:] = [float(val) for val in content[ind[i]+1:ind[i]+1+self.Nrealz]]   
            elif self.sampling_type=='Sobol':

                #this code is needed to install the randtoolbox package
                """
                # import rpy2's package module
                import rpy2.robjects.packages as rpackages

                # import R's utility package
                utils = rpackages.importr('utils')

                # select a mirror for R packages
                utils.chooseCRANmirror(ind=1) # select the first mirror in the list

                packnames = ('randtoolbox')
                from rpy2.robjects.vectors import StrVector
                utils.install_packages(StrVector(packnames))
                """

                # Import packages
                from rpy2.robjects.packages import importr
                randtoolbox = importr('randtoolbox') # Import Functions

                if (self.Neig>1111):
                    raise ValueError("Sorry, R project can generate Sobol sequence only up to dimension 1111, you are requesting dimension ", self.Neig, " - terminating")
                    exit(1)
                Rmatrix = randtoolbox.sobol(self.Nrealz, dim = self.Neig, scrambling = 3, seed = seed)
                self.X = np.array(tuple(Rmatrix)).astype(float).reshape((self.Neig, self.Nrealz))
                self.X = norm.ppf(self.X, loc=0., scale=1.)
            else: 
                raise ValueError("Sampling type ", self.sampling_type, " not implemented - terminating")
                exit(1)
            self.saveRandomVariables()
            print("[DONE]"); sys.stdout.flush()

    #############################################################################
    def generateFieldOnGrid(self):  
        load = True
        for i in range(self.Nvar):
            if not self.checkNUmpyFileExistence("grid_rf_values_%d"%i): load = False
        if load: 
            print("Loading random field on grid"); sys.stdout.flush()
            GF = np.zeros((self.Nvar,self.grid.shape[0],self.Nrealz))
            for i in range(self.Nvar):

                GF[i] = self.loadNumpyFile("grid_rf_values_%d"%i)
        else:
            GF = self.getGridGaussField();
            GF = self.backNatafTransformation(GF)
            self.saveGridNodesTXT(GF)

    #############################################################################
    def getNodes(self, nodefilename= "none"):    
        
        dmin = np.min(self.corr_l[:self.dim])/6.
        #[specimen,distribution,corrfunction,Nrealzold,ngrid,neig,samtypeold]...
        #= ReadReport(fieldname);

        if nodefilename == "none":
            print("Generating random nodes",); sys.stdout.flush()
            #RANDOM STRUCTURE
            maxiter = 1000; d2min = dmin**2
            iteration = 0
            origin = np.array([self.x_range[0],self.y_range[0],self.z_range[0]])
            size = np.array([self.x_range[1]-self.x_range[0],self.y_range[1]-self.y_range[0],self.z_range[1]-self.z_range[0]])
            nodes = np.expand_dims(np.random.rand(3)*size+origin,axis=0)
            npoints = 1
            while iteration<maxiter:
                node = np.random.rand(3)*size+origin
                d2 = np.copy(nodes)
                d2[:,0] -= node[0]; d2[:,1] -= node[1]; d2[:,2] -= node[2]
                d2 = np.sum(np.square(d2),axis=1)
            
                if min(d2)<d2min: 
                    iteration += 1
                else: 
                    iteration = 0
                    nodes = np.vstack([nodes, node])
                    npoints += 1

            print("[DONE] generated %d nodes"%nodes.shape[0]); sys.stdout.flush()

        elif os.path.isfile(nodefilename):
            print("Loading random nodes from file '%s'"%nodefilename,); sys.stdout.flush()
            if (nodefilename.endswith(".npy")):
                nodes = np.load(nodefilename)[:,range(self.dim)]
            else:
                nodes = np.loadtxt(nodefilename, usecols=range(self.dim))
            for i in range(3-self.dim):
                nodes = np.column_stack((nodes,np.zeros(len(nodes))))                           
            print("[DONE]"); sys.stdout.flush()
        else: raise ValueError("Error: File with nodes '%s' not found."%(nodefilename))
        self.saveNumpyFile('nodes',nodes);
        return nodes

    #############################################################################
    def collectEigenValueAndEigenVectors(self,var):
        mod = self.nataf_interp_codes[var]
        if self.spat_sep:
            #collect eigevalues 
            nlam = len(self.ijk)
            lam = self.eigenValsXYZ[mod][0][self.ijk[:,0]]*self.eigenValsXYZ[mod][1][self.ijk[:,1]]*self.eigenValsXYZ[mod][2][self.ijk[:,2]]
            #collect eigenshapes
            EV = np.zeros((self.grid.shape[0],nlam))
            for i in range(nlam): 
                EVX = np.einsum("i,j,k->ijk",self.eigenVecsXYZ[mod][0][:,self.ijk[i,0]] , self.eigenVecsXYZ[mod][1][:,self.ijk[i,1]],self.eigenVecsXYZ[mod][2][:,self.ijk[i,2]])
                EV[:,i] = EVX.flatten()
        else:
            lam = self.lam[mod]
            EV = self.EV[mod]
        return lam, EV

    """
    #############################################################################
    def getGridGaussField(self):
        print("Generating random field on the GRID"); sys.stdout.flush()
        GF = np.zeros([self.Nvar,self.grid.shape[0],self.Nrealz])

        for var in range(self.Nvar):
            print("Variable %d out of %d"%(var+1, self.Nvar)); sys.stdout.flush()
            lam,EV = self.collectEigenValueAndEigenVectors(var)
            nlam = len(lam)       
            for varx in range(self.Nvar):
                X = self.X[nlam*var:nlam*(var+1),:]*self.eigenVecsC[varx,var]*np.sqrt(self.eigenValsC[var])
                GF[varx] += np.einsum("ji,i,ik->jk",EV,np.sqrt(lam),X) 
        print("[DONE]"); sys.stdout.flush()
        return GF 
    """   

    #############################################################################
    def getGridGaussField(self):
        print("Generating random field on the GRID"); sys.stdout.flush()
        GF = np.zeros([self.Nvar,self.grid.shape[0],self.Nrealz])

        for var in range(self.Nvar):
            print("Variable %d out of %d"%(var+1, self.Nvar)); sys.stdout.flush()
            if self.spat_sep and self.memory_eff:
                    mod = self.nataf_interp_codes[var]  
                    nlam = len(self.ijk)
                    lam = self.eigenValsXYZ[mod][0][self.ijk[:,0]]*self.eigenValsXYZ[mod][1][self.ijk[:,1]]*self.eigenValsXYZ[mod][2][self.ijk[:,2]]
                    for varx in range(self.Nvar):
                        X = self.X[nlam*var:nlam*(var+1),:]*self.eigenVecsC[varx,var]*np.sqrt(self.eigenValsC[var])
                        for i in range(nlam): 
                            EVX = np.einsum("i,j,k->ijk",self.eigenVecsXYZ[mod][0][:,self.ijk[i,0]] , self.eigenVecsXYZ[mod][1][:,self.ijk[i,1]],self.eigenVecsXYZ[mod][2][:,self.ijk[i,2]])
                            EVX = EVX.flatten()
                            GF[varx] += np.einsum("j,k->jk",EVX,X[i,:])*np.sqrt(lam[i])
            else:    
                lam,EV = self.collectEigenValueAndEigenVectors(var)
                nlam = len(lam)       
                for varx in range(self.Nvar):
                    X = self.X[nlam*var:nlam*(var+1),:]*self.eigenVecsC[varx,var]*np.sqrt(self.eigenValsC[var])
                    GF[varx] += np.einsum("ji,i,ik->jk",EV,np.sqrt(lam),X)  
        print("[DONE]"); sys.stdout.flush()
        return GF  

    """
    #############################################################################
    def getGaussFieldEOLE(self,nodes, realizations = "all"):

        if type(realizations) == str and realizations == "all": realizations = range(self.Nrealz)

        n = nodes.shape[0]
        GF = np.zeros([self.Nvar,n,len(realizations)])

        print("Generating field on nodes"); sys.stdout.flush()
        D = self.generateSpatialCovarianceMatrixCompact(nodes)       

        for var in range(self.Nvar):
            print("Variable %d out of %d"%(var+1, self.Nvar)); sys.stdout.flush()
            lam,EV = self.collectEigenValueAndEigenVectors(var)
            nlam = len(lam)    
            lamrec = np.reciprocal(np.sqrt(lam))  
            if self.sparse:
                DD = D.copy()
                DD.data = self.nataf_interp[self.nataf_interp_codes[var]](D.data)                 
            else:
                DD = self.nataf_interp[self.nataf_interp_codes[var]](D) 
            for varx in range(self.Nvar):
                X = self.X[nlam*var:nlam*(var+1),realizations]*self.eigenVecsC[varx,var]*np.sqrt(self.eigenValsC[var])
                A = np.einsum("ji,i,ik->jk",EV,lamrec,X) #EQ. 27
                GF[varx] += DD.dot(A)                 #EQ. 27
        print("[DONE]"); sys.stdout.flush()
        return GF
    """    

    #############################################################################
    def getGaussFieldEOLE(self,nodes, realizations = "all"):

        if type(realizations) == str and realizations == "all": realizations = range(self.Nrealz)

        n = nodes.shape[0]
        GF = np.zeros([self.Nvar,n,len(realizations)])

        print("Generating field on nodes"); sys.stdout.flush()

        max_per_chunk = 5000
        nchunks = max(1, (n + max_per_chunk - 1) // max_per_chunk)
        chunk_size = (n + nchunks - 1) // nchunks
        if nchunks > 1:
            print("dividing calculation into", nchunks, "chunks")
        
        for chunk in range(nchunks):
            if chunk>0: print("evaluating chunk number", chunk+1, "out of", nchunks)        
            bot = chunk*chunk_size
            top = min((chunk+1)*chunk_size,n)
            chunk_nodes = nodes[bot:top]            
            D = self.generateSpatialCovarianceMatrixCompact(chunk_nodes)       

            for var in range(self.Nvar):
                print("Variable %d out of %d"%(var+1, self.Nvar)); sys.stdout.flush()
                if self.sparse:
                    DD = D.copy()
                    DD.data = self.nataf_interp[self.nataf_interp_codes[var]](D.data)                 
                else:
                    DD = self.nataf_interp[self.nataf_interp_codes[var]](D) 

                if self.spat_sep and self.memory_eff:
                    for varx in range(self.Nvar):            
                        nlam = len(self.ijk)   
                        X = self.X[nlam*var:nlam*(var+1),realizations]*self.eigenVecsC[varx,var]*np.sqrt(self.eigenValsC[var])
                        mod = self.nataf_interp_codes[var]
                        lam = self.eigenValsXYZ[mod][0][self.ijk[:,0]]*self.eigenValsXYZ[mod][1][self.ijk[:,1]]*self.eigenValsXYZ[mod][2][self.ijk[:,2]]
                        A = np.zeros((self.grid.shape[0], X.shape[1]))
                        for i in range(nlam): 
                            EVX = np.einsum("i,j,k->ijk",self.eigenVecsXYZ[mod][0][:,self.ijk[i,0]] , self.eigenVecsXYZ[mod][1][:,self.ijk[i,1]],self.eigenVecsXYZ[mod][2][:,self.ijk[i,2]])
                            EVX = EVX.flatten()
                            A += np.einsum("j,k->jk",EVX,X[i,:])/np.sqrt(lam[i])
                        GF[varx,bot:top] += DD.dot(A)                 #EQ. 27
                else:  
                    lam,EV = self.collectEigenValueAndEigenVectors(var)
                    nlam = len(lam)    
                    lamrec = np.reciprocal(np.sqrt(lam))                  
                    for varx in range(self.Nvar):               
                        X = self.X[nlam*var:nlam*(var+1),realizations]*self.eigenVecsC[varx,var]*np.sqrt(self.eigenValsC[var])          
                        A = np.einsum("ji,i,ik->jk",EV,lamrec,X) #EQ. 27
                        GF[varx,bot:top] += DD.dot(A)                 #EQ. 27

        print("[DONE]"); sys.stdout.flush()
        return GF

    #############################################################################
    def saveFieldNodesTXT(self,GF):
        for var in range(self.Nvar):
            if self.save_separated:
                for i in range(GF.shape[2]):
                    self.saveNumpyFile("rf_values_%d_%04d"%(var,i), GF[var,:,i])    
            else:
                self.saveNumpyFile("rf_values_%d"%var, GF[var])    
    #############################################################################
    def saveFieldNodesDifferentiationTXT(self,GF,direction):
        for var in range(self.Nvar):
            if self.save_separated:
                for i in range(GF.shape[2]):
                    self.saveNumpyFile("rf_diff%d_%d_%04d"%(direction,var,i), GF[var,:,i])  
            else:
                self.saveNumpyFile("rf_diff%d_%d"%(direction,var), GF[var,:,i])   

    #############################################################################
    def saveGridNodesTXT(self,GF):
        for var in range(self.Nvar):
            if self.save_separated:
                for i in range(GF.shape[2]):
                    self.saveNumpyFile("grid_rf_values_%d_%04d"%(var,i), GF[var,:,i])  
            else:
                self.saveNumpyFile("grid_rf_values_%d"%var, GF[var])      

    #############################################################################
    def saveFieldNodesVTKVoronoi(self, realizations = "all"):

        print('Generating Voronoi tessellation'); sys.stdout.flush()
        if type(realizations) == str and realizations == "all": realizations = range(self.Nrealz)

        nodes = self.loadNumpyFile("nodes")

        gap = 0.00001;
        mirrorfactor = 0.8
        supernodes = np.copy(nodes)
        nnodes = nodes.shape[0]    
    
        tomirror = np.where(nodes[:,0]<self.x_range[0]+mirrorfactor*(self.x_range[1]-self.x_range[0]))[0]
        newnodes0 = nodes[tomirror,:]
        newnodes0[:,0] = 2.*self.x_range[0] - newnodes0[:,0] - gap
        tomirror = np.where(nodes[:,0]>self.x_range[1]-mirrorfactor*(self.x_range[1]-self.x_range[0]))[0]
        newnodes1 = nodes[tomirror,:]
        newnodes1[:,0] = 2.*self.x_range[1] - newnodes1[:,0] + gap        
        supernodes = np.vstack((supernodes,newnodes0,newnodes1))
        
        tomirror = np.where(nodes[:,1]<self.y_range[0]+mirrorfactor*(self.y_range[1]-self.y_range[0]))[0]
        newnodes0 = nodes[tomirror,:]
        newnodes0[:,1] = 2.*self.y_range[0] - newnodes0[:,1] - gap
        tomirror = np.where(nodes[:,1]>self.y_range[1]-mirrorfactor*(self.y_range[1]-self.y_range[0]))[0]
        newnodes1 = nodes[tomirror,:]
        newnodes1[:,1] = 2.*self.y_range[1] - newnodes1[:,1] + gap        
        supernodes = np.vstack((supernodes,newnodes0,newnodes1))

        tomirror = np.where(nodes[:,2]<self.z_range[0]+mirrorfactor*(self.z_range[1]-self.z_range[0]))[0]
        newnodes0 = nodes[tomirror,:]
        newnodes0[:,2] = 2.*self.z_range[0] - newnodes0[:,2] - gap
        tomirror = np.where(nodes[:,2]>self.z_range[1]-mirrorfactor*(self.z_range[1]-self.z_range[0]))[0]
        newnodes1 = nodes[tomirror,:]
        newnodes1[:,2] = 2.*self.z_range[1] - newnodes1[:,2] + gap        
        supernodes = np.vstack((supernodes,newnodes0,newnodes1))

        vor = Voronoi(supernodes)

        vnodes = np.zeros(0).astype(int)
        nv = vor.vertices.shape[0]
        indexes = np.zeros(0).astype(int)
        tetras = np.zeros((0,4)).astype(int)

        for i in range(nodes.shape[0]): # range(10):
            cell = np.array(vor.regions[vor.point_region[i]]).astype(int)
            cellnodes = np.vstack((nodes[i,:],vor.vertices[cell,:]))
            tri = Delaunay(cellnodes)
            for k in range(tri.simplices.shape[0]):    
                tetras = np.vstack((tetras,tri.simplices[k,:]+len(vnodes)))
                indexes = np.hstack((indexes,i))
            vnodes = np.hstack((vnodes,np.hstack((nv+i,cell))))
        vnodes, retindices = np.unique(vnodes, return_inverse=True)
        tetras = retindices[tetras]

        print('Saving VTK Voronoi files'); sys.stdout.flush()
        for var in range(self.Nvar):
            if self.save_separated:
                GF = np.zeros((self.grid.shape[0], self.Nrealz))
                for i in range(self.Nrealz):
                    GF[:,i] = self.saveNumpyFile("grid_rf_values_%d_%04d"%(var,i))  
            else:
                GF = self.loadNumpyFile("rf_values_%d"%var) 

            output= open(os.path.join(self.folder,"VTK_Voronoi_%d.vtk"%var),'w')
            output.write("# vtk DataFile Version 2.0\n")
            output.write("Field %s\n"%self.name)
            output.write("ASCII\n\n")

            allvertices = np.vstack((vor.vertices,nodes))    
            
            output.write("DATASET UNSTRUCTURED_GRID\n")
            output.write("POINTS %d double \n"%len(vnodes))
            for i in range(len(vnodes)): output.write("%.5e\t%.5e\t%.5e\n"%(allvertices[vnodes[i],0],allvertices[vnodes[i],1],allvertices[vnodes[i],2]))
            
            output.write("\nCELLS %d %d\n"%(tetras.shape[0],tetras.shape[0]*5))
            for i in range(tetras.shape[0]): output.write("%d\t%d\t%d\t%d\t%d\n"%(4, tetras[i,0], tetras[i,1], tetras[i,2], tetras[i,3]))

            output.write("\nCELL_TYPES %d\n"%tetras.shape[0])
            for i in range(tetras.shape[0]): output.write("10\n")

            output.write("CELL_DATA %d\n"%tetras.shape[0]) 
            for i in realizations:
                field = GF[:,i]
                field = field[indexes]
                output.write("\nSCALARS field_%04d_realz_%04d double 1\n"%(c,i))
                output.write("LOOKUP_TABLE default\n")
                for h in field: output.write("%.5e\n"%h)
            output.close()

    #############################################################################
    def saveFieldNodesVTKDots(self, realizations = "all"):

        print('Saving VTK dots files'); sys.stdout.flush()
        if type(realizations) == str and realizations == "all": realizations = range(self.Nrealz)

        nodes = self.loadNumpyFile("nodes")  

        n = nodes.shape[0]

        for var in range(self.Nvar):
            if self.save_separated:
                GF = np.zeros((n, self.Nrealz))
                for i in range(self.Nrealz):
                    GF[:,i] = self.saveNumpyFile("rf_values_%d_%04d"%(var,i))  
            else:
                GF = self.loadNumpyFile("rf_values_%d"%var) 



            output= open(os.path.join(self.folder,"VTK_dots_%d.vtk"%var),'w')
            output.write("# vtk DataFile Version 2.0\n")
            output.write("Field %s\n"%self.name)
            output.write("ASCII\n\n")

            output.write("DATASET UNSTRUCTURED_GRID\n")
            output.write("POINTS %d double \n"%n)
            for i in range(n): output.write("%.5e\t%.5e\t%.5e\n"%(nodes[i,0],nodes[i,1],nodes[i,2]))
            
            output.write("\nCELLS %d %d\n"%(n,n*2))
            for i in range(n): output.write("%d\t%d\n"%(1, i))

            output.write("\nCELL_TYPES %d\n"%n)
            for i in range(n): output.write("1\n")

            output.write("CELL_DATA %d\n"%n) 
            for i in realizations:
                field = GF[:,i]
                output.write("\nSCALARS realz_%04d double 1\n"%(i))
                output.write("LOOKUP_TABLE default\n")
                for h in field: output.write("%.5e\n"%h)
            output.close()

    #############################################################################
    
    def saveGridNodesVTKDots(self, realizations = "all"):
        GF = self.getGridGaussField();
        GF = self.backNatafTransformation(GF); 
        print('Saving VTK dots files of GRID'); sys.stdout.flush()
        if type(realizations) == str and realizations == "all": realizations = range(self.Nrealz)

        n = self.grid.shape[0]
        for var in range(self.Nvar):
            output= open(os.path.join(self.folder,"VTK_dots_GRID_%d.vtk"%var),'w')
            output.write("# vtk DataFile Version 2.0\n")
            output.write("Field %s\n"%self.name)
            output.write("ASCII\n\n")

            output.write("DATASET UNSTRUCTURED_GRID\n")
            output.write("POINTS %d double \n"%n)
            for i in range(n): output.write("%.5e\t%.5e\t%.5e\n"%(self.grid[i,0],self.grid[i,1],self.grid[i,2]))
            
            output.write("\nCELLS %d %d\n"%(n,n*2))
            for i in range(n): output.write("%d\t%d\n"%(1, i))

            output.write("\nCELL_TYPES %d\n"%n)
            for i in range(n): output.write("1\n")

            output.write("CELL_DATA %d\n"%n) 
            for i in realizations:
                field = GF[var,:,i]
                output.write("\nSCALARS realz_%04d double 1\n"%(i))
                output.write("LOOKUP_TABLE default\n")
                for h in field: output.write("%.5e\n"%h)
            output.close()

    #############################################################################
    
    def saveGridVTKVoronoi(self, realizations = "all"):
        GF = self.getGridGaussField();
        GF = self.backNatafTransformation(GF); 

        print('Saving VTK Voronoi files of GRID'); sys.stdout.flush()
        if type(realizations) == str and realizations == "all": realizations = range(self.Nrealz)
        
        GX = self.loadNumpyFile("grid_nodesX")
        GY = self.loadNumpyFile("grid_nodesY")
        GZ = self.loadNumpyFile("grid_nodesZ")
        nx = len(GX); ny = len(GY); nz = len(GZ);        

        sx = GX[1]-GX[0]
        GX = np.arange(GX[0]-sx/2.,GX[-1]+sx/1.9,sx)
        sy = GY[1]-GY[0]
        GY = np.arange(GY[0]-sy/2.,GY[-1]+sx/1.9,sy)
        sz = GZ[1]-GZ[0]
        GZ = np.arange(GZ[0]-sz/2.,GZ[-1]+sz/1.9,sz)

        X, Y, Z = np.meshgrid(GX,GY,GZ, indexing="ij");
        X = np.reshape(X,[-1,1]); Y = np.reshape(Y,[-1,1]); Z = np.reshape(Z,[-1,1])
        grid = np.hstack([X,Y,Z])

        n = self.grid.shape[0]
        for var in range(self.Nvar):
            output= open(os.path.join(self.folder,"VTK_Voronoi_GRID_%d.vtk"%var),'w')
            output.write("# vtk DataFile Version 2.0\n")
            output.write("Field %s\n"%self.name)
            output.write("ASCII\n\n")

            output.write("DATASET UNSTRUCTURED_GRID\n")
            output.write("POINTS %d double \n"%(len(grid)))
            for i in range(len(grid)): output.write("%.5e\t%.5e\t%.5e\n"%(grid[i,0],grid[i,1],grid[i,2]))
            
            output.write("\nCELLS %d %d\n"%(n,n*9))
            for i in range(n): 
                ix = int(i/(ny*nz))
                iy = int((i-ix*ny*nz)/nz)
                iz = int(i-ix*ny*nz-nz*iy)
                a = ix*(ny+1)*(nz+1) + iy*(nz+1) + iz

                output.write("%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n"%(8, a, a + (ny+1)*(nz+1), a+nz+1 + (ny+1)*(nz+1), a+nz+1, a + 1, a + (ny+1)*(nz+1) + 1, a+nz+1 + (ny+1)*(nz+1) + 1, a+nz+2))

            output.write("\nCELL_TYPES %d\n"%n)
            for i in range(n): output.write("12\n")

            output.write("CELL_DATA %d\n"%n) 
            for i in realizations:
                field = GF[var,:,i]
                output.write("\nSCALARS realz_%04d double 1\n"%(i))
                output.write("LOOKUP_TABLE default\n")
                for h in field: output.write("%.5e\n"%h)
            output.close()

    #############################################################################
    def getFieldEOLE(self,nodes, realizations = "all"):

        if type(realizations) == str and realizations == "all": realizations = range(self.Nrealz)
        limits_max = np.max(nodes,axis =0)
        limits_min = np.min(nodes,axis =0)
        eps = 1e-2
        nodes_in_box = True
        if (limits_min[0]<self.x_range[0]-eps or limits_max[0]>self.x_range[1]+eps):
            print("RF x limits: ", self.x_range, "min and max x coordintes of points:", [limits_min[0], limits_max[0]])
            nodes_in_box = False
        if (limits_min[1]<self.y_range[0]-eps or limits_max[1]>self.y_range[1]+eps):
            print("RF y limits: ", self.y_range, "min and max y coordintes of points:", [limits_min[1], limits_max[1]])
            nodes_in_box = False
        if (limits_min[2]<self.z_range[0]-eps or limits_max[2]>self.z_range[1]+eps):
            print("RF z limits: ", self.z_range, "min and max z coordintes of points:", [limits_min[2], limits_max[2]])
            nodes_in_box = False
        if not nodes_in_box:
            raise ValueError(
                "Facet/sample points exceed the RF domain box. "
                f"RF x={self.x_range}, y={self.y_range}, z={self.z_range}; "
                f"points min={limits_min}, max={limits_max}."
            )

        GF = self.getGaussFieldEOLE(nodes, realizations = realizations)
        GF = self.backNatafTransformation(GF)     
        return GF
    
    #############################################################################
    def generateFieldEOLE(self,nodefile = "none", realizations = "all"):

        nodes = self.getNodes(nodefilename = nodefile)
        GF = self.getFieldEOLE(nodes,realizations = realizations)
        self.saveFieldNodesTXT(GF)
        return GF

    #############################################################################
    def generateFieldDifferentiationEOLE(self, direction, nodefile = "none"):

        nodes = self.getNodes(nodefilename = nodefile)
        limits_max = np.max(nodes,axis =0)
        limits_min = np.min(nodes,axis =0)
        nodes_in_box = True
        if (limits_min[0]<self.x_range[0] or limits_max[0]>self.x_range[1]):
            print("RF x limits: ", self.x_range, "min and max x coordintes of points:", [limits_min[0], limits_max[0]])
            nodes_in_box = False
        if (limits_min[1]<self.y_range[0] or limits_max[1]>self.y_range[1]):
            print("RF y limits: ", self.y_range, "min and max y coordintes of points:", [limits_min[1], limits_max[1]])
            nodes_in_box = False
        if (limits_min[2]<self.z_range[0] or limits_max[2]>self.z_range[1]):
            print("RF z limits: ", self.z_range, "min and max z coordintes of points:", [limits_min[2], limits_max[2]])
            nodes_in_box = False
        if not nodes_in_box:
            print("ERROR: submitted points exceed the box in which random field was generated. Termination is strongly suggested as the results will be most likely biased.")
        
        dx = self.corr_l[direction]/1e6
        dd = np.zeros(nodes.shape)
        dd[:,direction] = dx
        GF0 = self.getGaussFieldEOLE(nodes)
        GF0 = self.backNatafTransformation(GF0)
        GF1 = self.getGaussFieldEOLE(nodes+dd)
        GF1 = self.backNatafTransformation(GF1)
        diffGF = (GF1-GF0)/dx    
        self.saveFieldNodesDifferentiationTXT(diffGF,direction)
        return diffGF

    #############################################################################
    def errorEvaluation(self, max_node_num = 5e3, grid_data = False):

        if grid_data: 
            print("error evaluation on grid data"); sys.stdout.flush()
            prefix = "grid_"
        else: 
            print("error evaluation"); sys.stdout.flush()
            prefix = ""
            
        GF = []
        nodes = self.loadNumpyFile(prefix+"nodes")

        n = nodes.shape[0]
        param = int(max_node_num) 
        randint = []
        
        if n>param: randint = np.random.randint(0,high=n,size=(param))
        else: randint = np.arange(0,n)
        param = len(randint)
        nodesX = nodes[randint,:]

        sizes = np.array([self.x_range[1]-self.x_range[0],self.y_range[1]-self.y_range[0],self.z_range[1]-self.z_range[0]])

        for var in range(self.Nvar):
            print("Variable %d out of %d"%(var+1, self.Nvar)); sys.stdout.flush()            

            if self.save_separated:
                GF.append(np.zeros((n, self.Nrealz)))
                for i in range(self.Nrealz):
                    GF[var][:,i] = self.loadNumpyFile(prefix+"rf_values_%d_%04d"%(var,i))  
            else:
                GF.append (self.loadNumpyFile(prefix+"rf_values_%d"%var) )           


            
            
            
            GFX = GF[var][randint,:]

            plt.rcParams.update({'font.size': 18})
            plt.rcParams.update({'axes.linewidth': 2})
            plt.rcParams.update({'font.family' : 'serif'})
            plt.rcParams.update({'font.serif' : 'Times New Roman'})
            plt.rcParams.update({'text.usetex':False})
    
            ################# AUTOCORRELATION

            identical_lcorr = True
            for i in range(self.dim-1):
                if not self.corr_l[0]==self.corr_l[i+1]: identical_lcorr = False

            if identical_lcorr:
                fig = plt.figure()
                ax = fig.add_axes([0.15,0.15,0.8,0.8])

                if self.rank_corr:
                    corr,pval = spearmanr(GFX,axis=1) 
                    ax.set_ylabel("Spearman's correlation"); 
                else:
                    n = len(GFX)
                    corr = np.corrcoef(GFX)
                    ax.set_ylabel("Pearson's correlation"); 

                for i in range(param):
                    d2 = np.copy(nodesX)
                    for dim in range(self.dim):
                        d2[:,dim] -= nodesX[i,dim]
                        if self.periodic[dim]:
                            d2[:,dim] = np.abs(d2[:,dim])
                            d2[:,dim] = np.minimum(d2[:,dim],sizes[dim]-d2[:,dim])
                    d2 = np.sum(np.square(d2),axis=1)
                    ax.plot(np.sqrt(d2),corr[i,:],'ok',ms=1)
                ax.set_xlabel("distance")        
                
                xlim = ax.get_xlim()
                ax.set_xlim([0,xlim[1]])
                x = np.linspace(0,xlim[1],num =100)
                x2 = np.zeros((len(x),3))
                x2[:,0] = np.square(x)
                y = self.getCorrelation(x2)
                ax.plot(x,y,'-r',lw=2)

                fig.savefig(os.path.join(self.folder,prefix+'corr_error_%d.png'%var))
                #plt.show()
                plt.close(fig)

            ################# DISTRIBUTION
        
            GFXX = np.reshape(GFX,[-1,1])

            hist, bins = np.histogram(GFXX, density=True, bins = int(np.sqrt(len(GFXX)/10.)))    

            fig = plt.figure()
            ax = fig.add_axes([0.15,0.15,0.8,0.8])
            ax.bar((bins[1:]+bins[:-1])/2., hist, color="k", alpha=0.5, width = (bins[1]-bins[0])*0.8)
            xlim = ax.get_xlim()
            x = np.linspace(xlim[0],xlim[1],num =100)
            y = self.dist[var].pdf(x)
            ax.plot(x,y,'-r',lw=2)
            fig.savefig(os.path.join(self.folder,prefix+'dist_error_%d.png'%var))
            #plt.show()
            ax.set_ylabel("pdf"); ax.set_xlabel("variable %d"%var)
            plt.close(fig)        

        
        if self.Nvar>1:
            crosscorr = np.zeros((int((self.Nvar**2-self.Nvar)/2+0.5),4))
            t = 0
            for var1 in range(self.Nvar):
                for var2 in range(var1+1,self.Nvar):
                    if self.rank_corr:
                        correlation = spearmanr(GF[var1].flatten(),GF[var2].flatten())[0]
                    else: 
                        correlation = pearsonr(GF[var1].flatten(),GF[var2].flatten())[0]
                    crosscorr[t,:] = np.array([var1,var2,correlation,self.cross_correlation_matrix[var1,var2]])
                    t += 1
                    
            np.savetxt(os.path.join(self.folder,prefix+"output_cross_correlations.dat"),crosscorr)
        
        print("[DONE]"); sys.stdout.flush()

if __name__ == '__main__':
    pass
    
