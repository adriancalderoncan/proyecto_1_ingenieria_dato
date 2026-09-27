import pandas as pd
import requests
from bs4 import BeautifulSoup

url = "https://www.sanidad.gob.es/profesionales/nomenclator.do?metodo=nomenclatorExcel"     #es el link de decarga del excel directamente,en vez del del enunciado
response = requests.get(url)

with open("data/nomenclator.xls","wb") as archivo:  #abre(en este caso como no existe,lo crea) un archivo en esa ruta."wb" es que es en modo "write" y "binary",es decir,vamos a meter en este archivo bytes tal cual,no texto,y no lo stoques ni interpretes
    archivo.write(response.content)     #usamos response.content porque son bytes,antes hemos usado response.text porque era texto

df_precios = pd.read_excel("data/nomenclator.xls")  
print(df_precios.columns) #para ver el nombre de las columnas del excel

df_hu2 = pd.read_excel("data/HU2_medicamentos_diabetes.xlsx")
print(df_hu2.columns)   #lo mismo pero con el excel que hicimos en el hu2

df_precios_columnas_añadir = df_precios[["Código Nacional", "Estado", "Precio de venta al público con IVA","Precio de referencia","Tratamiento de larga duración", "Especial control médico" ]]
# IMPORTANTE: doble corchete = selecciono varias columnas a la vez (lista de nombres)del excel df_precios y me sigue devolviendo una tabla, no una sola columna
df_precios_columnas_añadir["Código Nacional"] = df_precios_columnas_añadir["Código Nacional"].astype("float64")
#tenemos que convertir la columna de Codigo Nacional del excel nuevo a float(son int),ya que la columna "cn" de nuestro excel del HU2 esta en float

df_hu3 = df_hu2.merge(df_precios_columnas_añadir, left_on="cn", right_on="Código Nacional",how="left")
#cojo mi tabla principal(df_hu2,es la que tiene todo hasta ahora) y le pego las columnas de la ptra tabla (df_precios_columnas_añadir).Con how=left nos quedamos con todas las filas del de la izq pase lo que pase(df_hu2)

#print(df_hu3.shape)
#print(df_hu3.columns)

df_hu3.to_excel("data/HU3_medicamentos_diabetes.xlsx",index=False)