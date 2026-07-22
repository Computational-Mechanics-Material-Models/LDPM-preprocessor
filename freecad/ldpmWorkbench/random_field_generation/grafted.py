#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# created by Jan Elias
# jan.elias@vut.cz
# Brno University of Technology,
# 2020

import numpy as np
from scipy.stats import norm

############################################################################################################
############################################################################################################

class GD():
    def __init__(self,m,s1,dg,ksigr):
        self.dgn = dg/s1
        self.mgn = ksigr+self.dgn*np.sqrt(-2*np.log(np.sqrt(2*np.pi)*m*self.dgn*ksigr**(m-1.)*np.exp(-ksigr**m)))
        self.mg = self.mgn*s1
        self.rf = 1/(1.-norm.cdf(ksigr,self.mgn,self.dgn)+(1.-np.exp(-(ksigr)**m)))
        self.dg = dg
        self.m = m
        self.s1 = s1    
        self.xgr = ksigr*s1
        self.ksigr = ksigr
        self.Pgr = self.rf*(1.-np.exp(-(self.xgr/self.s1)**self.m))
        xmin = self.ppf(1E-10)
        xmax = self.ppf(1.-1E-10)   
        x = np.linspace(xmin,xmax,num=10000)
        y = self.pdf(x)
        self.m0 = np.dot(x,y)*(x[1]-x[0])
        self.d0 = np.sqrt(np.dot(np.square(x-self.m0),y)*(x[1]-x[0]))
        self.w = self.d0/self.m0

    def gaussianCDF(self,x):
        return  self.Pgr + self.rf*(norm.cdf(x,self.mg,self.dg)-norm.cdf(self.xgr,self.mg,self.dg))


    def ppf(self,x):
        scal = False
        if np.isscalar(x):
            scal = True
            x = np.array([x])
        y = np.zeros(x.shape)
        ind1 = np.where(x<=self.Pgr)[0]
        if len(ind1)>0: 
            y[ind1] = (-np.log(1.-x[ind1]/self.rf))**(1/self.m)*self.s1
        ind2 = np.where(x>self.Pgr)[0]
        if len(ind2)>0:
            #here we need to proceed by step, the norm.ppf has some memory leaks
            limit = 100000
            t=0
            while t<len(ind2):
                t1 = min(t+limit,len(ind2))
                y[ind2[t:t1]] = norm.ppf( ( x[ind2[t:t1]]-self.Pgr+self.rf*norm.cdf(self.xgr,self.mg,self.dg) )/self.rf ,self.mg,self.dg)
                t = t1
        return y if not scal else y[0]

    def cdf(self,x):
        scal = False
        if np.isscalar(x):
            scal = True
            x = np.array([x])
        y = x*0.
        ind1 = np.where(x<=self.xgr)[0]
        if len(ind1)>0: y[ind1] = self.rf*(1.-np.exp(-(np.maximum(x[ind1]/self.s1,0.))**self.m))
        ind2 = np.where(x>self.xgr)[0]
        if len(ind2)>0:  y[ind2] = 1. - self.rf + self.rf*norm.cdf(x[ind2],self.mg,self.dg)
        return y if not scal else y[0]

    def pdf(self, x):
        scal = False
        if np.isscalar(x):
            scal = True
            x = np.array([x])
        y = x*0.
        ind1 = np.where(x<=self.xgr)[0]
        if len(ind1)>0: 
            y[ind1] = self.rf*(self.m/self.s1)*(np.maximum(x[ind1],0.)/self.s1)**(self.m-1.)*np.exp(-(np.maximum(x[ind1],0.)/self.s1)**self.m)
        ind2 = np.where(x>self.xgr)[0]
        if len(ind2)>0:     
            y[ind2] = self.rf*norm.pdf(x[ind2],self.mg,self.dg)
        return y if not scal else y[0]

    def stats(self):
        return self.m0, self.d0**2

    def printAll(self):
        print("dgn:",self.dgn)
        print("mgn:",self.mgn)
        print("mg:",self.mg)
        print("rf:",self.rf)
        print("dg:",self.dg)
        print("m:",self.m)
        print("s1:",self.s1    )
        print("xgr:",self.xgr)
        print("ksigr:",self.ksigr)
        print("Pgr:",self.Pgr)

        print("MEAN, m0:",self.m0)
        print("STD, d0:",self.d0)
        print("CoV, w:",self.w)


def findGD(Pgr =5e-4 , m = 30, mean = 1.0, std = 0.25):
    params = [m,0.551821,std,0.7765]    
    gd = GD(params[0],params[1],params[2],params[3])
    while abs(gd.m0-mean)>1e-10 or abs(gd.Pgr-Pgr)>1e-10 or abs(gd.d0-std)>1e-10:
        params[1] = params[1]/gd.m0*mean
        params[2] -= (gd.d0-std)/std/100.
        params[3] = ((-np.log(1.-Pgr/gd.rf))**(1./gd.m))
        gd =  GD(params[0],params[1],params[2],params[3])
        if gd.d0<1E-5: exit()
    return gd



if __name__ == '__main__':
    params = [24,2.115,0.1501,0.6813]
    gd = GD(params[0],params[1],params[2],params[3])
    gd.printAll()
    exit(1)    

    #params = [30,0.551821,0.201,0.7765]
    #gd = GD(params[0],params[1],params[2],params[3])
    #while gd.m0>1.00001 or gd.m0 < 0.99999:
    #params[1] = params[1]/gd.m0
    #gd =  GD(params[0],params[1],params[2],params[3])

    gd =  findGD(Pgr = 0.001, m =24, mean = 2.381 , std = 0.58685)
    #gd2 =  findGD(Pgr = 0.001, m =24, mean = 1, std = 0.58685/2.381)

    


    #gd = findGD()
    gd.printAll()

    #"""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    x = np.arange(0,4,step=0.01)
    ax.plot(x,gd.pdf(x),"-k")
    #ax.plot(x,gd2.pdf(x/2.381)/2.381,":r")
    ax.set_xlabel("x")
    ax.set_ylabel("pdf")
    plt.show()
    #"""


#GaussianMean 2.381 MPa
#GaussianStandardDeviation 0.58685 MPa
#GraftingPoint 0.84593
#CdfScalingFactor 1.0035
#WeibullScaleParameter 1.1282

