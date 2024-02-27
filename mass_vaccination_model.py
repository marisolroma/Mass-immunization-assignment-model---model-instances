#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 13 13:35:23 2024

@author: MarisolRoma
"""

#IMPORT PACKAGES
import gurobipy as gp
import pandas as pd
import matplotlib.pyplot as plt
import gurobipy as gp
from gurobipy import GRB

data_clients=pd.read_csv('clientes.csv')
data_clients.dropna()
data_clients.head()

#IMPORT DATAFRAMES
data_cv=pd.read_csv('vaccination centers jalisco.csv')
data_cv.fillna(0, inplace=True)
data_cv.head()

data_rutas=pd.read_csv('rutas_clientes_cv.csv')
data_rutas.fillna(0, inplace=True)
data_rutas.head()

#PARAMETERS
I = data_clients.nombre
J = data_cv.nombre
#CA = 1/5000 #d/v  velocidad promedio 5km/h 5000m/h
CA=(10/(100*1000))*3 #USD GAS WITH FUE EFF 10L PER 100 KM
CE = 486.41#8300 #pesos por enfermera al mes
PE = 28000 #por mes y por empleado
#B = 10000000000000
#B=5709000
B=5709000

dd={}
for i in range(len(I)):
    d={I[i]:data_clients.pobtot[i]}
    dd.update(d)
I,h=gp.multidict(dd)

rr={}
for i in range(len(data_rutas.origen)) :
    #alpha=1-(0.2)*(data_rutas.distancia[i]/(100*1000))
    alpha=1-(0.3)*(data_rutas.distancia[i]/(5*1000)) #porque cinsuderamos distancia caminando , por cada 5km de lejanía 
    # disminuye 30% de probabilidad de asistir a la vacuna
    #31% de la población mexicana se mueve caminando o en bici
    # https://imco.org.mx/wp-content/uploads/2019/01/Índice-de-Movilidad-Urbana_Documento.pdf
    r={(data_rutas.destino[i], data_rutas.origen[i]): [data_rutas.distancia[i],alpha]}
    rr.update(r)
IJ, d, a = gp.multidict(rr)

#MODEL
m=gp.Model("MASS")

#VARIABLES
x=m.addVars(IJ,vtype=GRB.INTEGER,name='x')
e=m.addVars(J,vtype=GRB.INTEGER,name='e')

#OBJECTIVE FUNCTION
of=(gp.quicksum(a[i,j]*x[i,j] for i,j in IJ)/gp.quicksum(h[i] for i in I).getValue())

#of=(a.sum('*','*')*x.sum('*','*')/h.sum('*').getValue())


#CONSTRAINTS
#m.addConstr(CA*d.sum('*','*')*x.sum('*','*') + CE*e.sum('*') <= B)
m.addConstr(CA*gp.quicksum(d[i,j]*x[i,j] for i,j in IJ) + CE*gp.quicksum(e[j] for j in J) <= B)

#m.addConstrs(x.sum('*',j) >= 1 for j in J)
for j in J:
    m.addConstr(gp.quicksum(x[i,j] for i in I) >=1)

#m.addConstrs(x.sum(i,'*') >= 1 for i in I) #todos los clientes son asignados a un cv
#for i in I:
#    m.addConstr(gp.quicksum(x[i,j] for j in J) >=1)

#m.addConstr(x.sum('*','*') == h.sum('*'))
#m.addConstr(gp.quicksum(x[i,j] for i,j in IJ)==gp.quicksum(h[i] for i in I))
for i in I:
    m.addConstr(gp.quicksum(x[i,j] for j in J) == h[i])    

#m.addConstrs(PE*e[j] >= x.sum('*',j) for j in J)
for j in J:
    m.addConstr(PE*e[j] >= gp.quicksum(x[i,j] for i in I))
    



#OPTIMIZATION
m.setObjective(of, GRB.MAXIMIZE)
m.optimize()


#PRINT
for v in m.getVars():
  if v.x >= 1:
    t=v.varName
    print('%s %g' % (v.varName, v.x))
    
  
of=(gp.quicksum(a[i,j]*x[i,j] for i,j in IJ)/gp.quicksum(h[i] for i in I).getValue())*100
print(f'The coverage of the mass immunization strategy is {of.getValue()} %')


#Demanda cubierta por region
cv={}
suma_1=0
for j in J:
    c0=gp.quicksum(x[i,j] for i in I).getValue()
    c={j:c0}
    if c0==1:
        suma_1=suma_1+1
        
    cv.update(c)
df_cv = pd.DataFrame(cv,index=[0])

    
#personas asignasas a cada centro de vacunación 
cliente={}
for i in I:
    c0=gp.quicksum(x[i,j] for j in J).getValue()
    c={i:c0}
    cliente.update(c)
df_c = pd.DataFrame(cliente,index=[0])

