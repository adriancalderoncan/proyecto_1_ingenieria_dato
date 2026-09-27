import pandas as pd
import requests


url_nomenclator = "https://www.sanidad.gob.es/profesionales/nomenclator.do?metodo=nomenclatorExcel"
response = requests.get(url_nomenclator, timeout=120)

ruta_nomenclator = "data/nomenclator.xls"
# creo un ficher nuevo en el directorio y le escribo el contenido del response.content
with open(ruta_nomenclator, "wb") as fichero:
    fichero.write(response.content)

print("Nomenclator descargado")

# el cn lo leemos como texto, si no pandas lo convierte en decimal (662260.0) y luego no cruza
df = pd.read_excel("data/HU2_medicamentos_diabetes.xlsx", dtype={"cn": str})

# el nomenclator es un .xls antiguo, necesita la libreria xlrd para poder leerse
nomenclator = pd.read_excel(ruta_nomenclator, engine="xlrd")
print("Filas del nomenclator: ", len(nomenclator))

# de las 20 columnas que trae el fichero nos quedamos solo con las que pide el enunciado
columnas = ["Código Nacional",
            "Estado",
            "Precio de venta al público con IVA",
            "Precio de referencia",
            "Tratamiento de larga duración",
            "Especial control médico"]
nomenclator = nomenclator[columnas]

# en el nomenclator el codigo nacional es un numero y en nuestro excel es texto, hay que cambiarlo
nomenclator["Código Nacional"] = nomenclator["Código Nacional"].astype(str)


# hacemos el merge para juntar los datos
df = df.merge(nomenclator, how="left", left_on="cn", right_on="Código Nacional")


# Código Nacional es la misma columna que cn
df = df.drop(columns=["Código Nacional"])

print(df.shape)

df.to_excel("data/HU3_medicamentos_diabetes.xlsx", index=False)
print("Dataset del HU3 guardado")
