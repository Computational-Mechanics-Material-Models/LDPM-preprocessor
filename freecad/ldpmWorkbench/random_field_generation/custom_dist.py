#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# created by Jan Elias
# jan.elias@vut.cz
# Brno University of Technology,
# 2023

import numpy as np

############################################################################################################
############################################################################################################

class pointDist():
    def __init__(self,points):
        area = 0
        for p in range(len(points)-1):
            area += 0.5*(points[p,1] + points[p+1,1])*(points[p+1,0] - points[p,0])
        self.data = np.zeros((len(points),3))
        self.data[:,0] = points[:,0]
        self.data[:,1] = points[:,1]/area
        self.mean = 0.
        area = 0
        for p in range(len(self.data)-1):
            d = self.data[p+1,0] - self.data[p,0]
            self.mean += 0.5*(self.data[p+1,0] + self.data[p,0])*d*self.data[p,1] + 0.5*(self.data[p,0] + 2./3.*d)*d*(self.data[p+1,1]-self.data[p,1])
            area += 0.5*(self.data[p,1] + self.data[p+1,1])*d
            self.data[p+1,2] = area 
        self.std = 0.
        for p in range(len(self.data)-1):
            d = self.data[p+1,0] - self.data[p,0]
            self.std += -(self.data[p+1,1] - self.data[p,1])/(self.data[p+1,0] - self.data[p,0])*(-self.data[p,0]**4/12.+self.data[p,0]**3*self.mean/3.-self.data[p,0]**2*self.mean**2/2.-self.data[p+1,0]**4/4.-self.mean**2*self.data[p+1,0]**2/2.+2./3.*self.data[p+1,0]**3*self.mean+self.data[p+1,0]**3*self.data[p,0]/3.+self.mean**2*self.data[p+1,0]*self.data[p,0]-self.data[p+1,0]**2*self.data[p,0]*self.mean) + self.data[p,1]*(self.data[p+1,0]**3/3.+self.data[p+1,0]*self.mean**2-self.data[p+1,0]**2*self.mean-self.data[p,0]**3/3.-self.data[p,0]*self.mean**2+self.data[p,0]**2*self.mean)
        self.std = np.sqrt(self.std)

        """
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        x = np.linspace(0,1,num=500)
        ax.plot(self.ppf(x),x,"-k")
        x = np.linspace(0,250,num=500)
        ax.plot(x,self.cdf(x),":")
        ax.set_xlabel("x")
        ax.set_ylabel("cdf")
        self.printAll()
        plt.show()
        """

    def ppf(self,x):
        scal = False
        if np.isscalar(x):
            scal = True
            x = np.array([x])
        xshape = x.shape
        x = np.matrix.flatten(x)
        y = x*0.
        for k in range(len(x)): 
            if x[k]>=1: y[k] = self.data[-1,0]
            elif x[k]<=0: y[k] = self.data[0,0]
            else:
                ind1 = np.where(x[k]<=self.data[:,2])[0][0]
                #This is wrong, only linear, should be quadratic
                #y[k] = self.data[ind1-1,0] + (self.data[ind1,0] - self.data[ind1-1,0])/(self.data[ind1,2]-self.data[ind1-1,2])*(x[k]-self.data[ind1-1,2])
                #correct quadratic eq.
                Adiff = x[k]-self.data[ind1-1,2]
                a = (self.data[ind1,1]-self.data[ind1-1,1])/(self.data[ind1,0] - self.data[ind1-1,0])
                if (abs(a)<1e-15):
                    #linear
                    y[k] = self.data[ind1-1,0] + (self.data[ind1,0] - self.data[ind1-1,0])/(self.data[ind1,2]-self.data[ind1-1,2])*(x[k]-self.data[ind1-1,2])
                else:
                    b = 2.*self.data[ind1-1,1]
                    c = -Adiff*2.
                    y[k] = self.data[ind1-1,0] + (-b+np.sqrt(b**2-4.*a*c))/(2.*a)
        return y.reshape(xshape) if not scal else y[0]
        

    def cdf(self,x):
        scal = False
        if np.isscalar(x):
            scal = True
            x = np.array([x])
        y = x*0.
        for k in range(len(x)): 
            if x[k]<self.data[0,0]: y[k] = 0
            elif x[k]>self.data[-1,0]: y[k] = 1
            else:
                ind1 = np.where(x[k]<=self.data[:,0])[0][0]
                pdf = self.data[ind1-1,1] + (self.data[ind1,1] - self.data[ind1-1,1])/(self.data[ind1,0]-self.data[ind1-1,0])*(x[k]-self.data[ind1-1,0])
                y[k] = self.data[ind1-1,2] + 0.5*(pdf + self.data[ind1-1,1])*(x[k]-self.data[ind1-1,0])
        return y if not scal else y[0]

    def pdf(self, x):
        scal = False
        if np.isscalar(x):
            scal = True
            x = np.array([x])
        y = x*0.
        for k in range(len(x)): 
            if x[k]<self.data[0,0]: y[k] = 0
            elif x[k]>self.data[-1,0]: y[k] = 0
            else: 
                ind1 = np.where(x[k]<=self.data[:,0])[0][0]
                y[k] = self.data[ind1-1,1] + (self.data[ind1,1] - self.data[ind1-1,1])/(self.data[ind1,0]-self.data[ind1-1,0])*(x[k]-self.data[ind1-1,0])
        return y if not scal else y[0]


    def stats(self):
        return self.mean, self.std**2

    def printAll(self):
        print("mean:",self.mean)
        print("std:",self.std)

 
