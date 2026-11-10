# HU-1, HU-2 y HU-3 en un solo script, para poder llamarlo desde el archivo maestro (H7).
# Junta h1.py, h2webscraping.py y h3.py (los originales se quedan como estaban).
#   HU-1: API REST de CIMA            -> data/HU1_medicamentos_diabetes.xlsx
#   HU-2: web scraping fichas tecnicas -> data/HU2_medicamentos_diabetes.xlsx
#   HU-3: precios del Nomenclator      -> data/HU3_medicamentos_diabetes.xlsx

import json
import math
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Rutas a partir de la carpeta del proyecto, asi el script funciona se lance desde donde se lance
RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
SALIDA_HU1 = DATA / "HU1_medicamentos_diabetes.xlsx"
SALIDA_HU2 = DATA / "HU2_medicamentos_diabetes.xlsx"
SALIDA_HU3 = DATA / "HU3_medicamentos_diabetes.xlsx"
NOMENCLATOR = DATA / "nomenclator.xls"

ENFERMEDAD = "diabetes"

# Una Session reutiliza la misma conexion con el servidor en todas las peticiones, asi va mas rapido
sesion = requests.Session()


def pedir(metodo, url, **opciones):
    """Hace una peticion y, si falla (corte de red, error del servidor...), lo reintenta hasta 3 veces.
    Si despues de 3 intentos sigue fallando, lanza el error para que se vea en el log."""
    for intento in range(1, 4):
        try:
            response = sesion.request(metodo, url, timeout=60, **opciones)
            response.raise_for_status()   # si el servidor responde con error (404, 500...) lo tratamos como fallo
            return response
        except requests.RequestException as error:
            print(f"Intento {intento} fallido para {url}: {error}")
            if intento == 3:
                raise
            time.sleep(5)   # esperamos un poco antes de volver a intentarlo


# =====================================================================
# HU-1: medicamentos de la enfermedad desde la API de CIMA
# =====================================================================
print("===== HU-1: API de CIMA =====")

url_1 = "https://cima.aemps.es/cima/rest/buscarEnFichaTecnica?pagina="    # POST
url_2 = "https://cima.aemps.es/cima/rest/medicamento?nregistro="          # GET

payload = json.dumps([
    {
        "seccion": "4.1",
        "texto": ENFERMEDAD,
        "contiene": 1
    }
])
headers = {
    "Content-Type": "application/json"
}

# Pedimos la primera pagina para saber cuantos registros hay en total (totalFilas)
# y cuantos vienen en cada pagina (tamanioPagina). Asi calculamos cuantas paginas hay que pedir
# en vez de dejar el numero de paginas fijo.
primera = json.loads(pedir("POST", url_1 + "1", headers=headers, data=payload).text)
total_filas = primera["totalFilas"]
tamanio_pagina = primera["tamanioPagina"]
num_paginas = math.ceil(total_filas / tamanio_pagina)   # ceil redondea hacia arriba (1582/200 = 7,9 -> 8)
print("Total de registros:", total_filas, "| paginas:", num_paginas)

medicamentos = []
medicamentos.extend(primera.get("resultados", []))
for i in range(2, num_paginas + 1):
    print("Obteniendo medicamentos de la pagina:", i)
    response = pedir("POST", url_1 + str(i), headers=headers, data=payload)
    pagina_medicamentos = json.loads(response.text)
    medicamentos.extend(pagina_medicamentos.get("resultados", []))

nregistros = []
for dat in medicamentos:
    nregistros.append(dat.get("nregistro"))
print("Numeros de registro obtenidos:", len(nregistros))

# Una peticion GET por cada nregistro para sacar su ficha completa
infomedslis = []
errores_hu1 = 0
for i in nregistros:
    try:
        response = pedir("GET", url_2 + i)
        infomedslis.append(json.loads(response.text))
    except Exception:
        # Si un medicamento falla incluso tras los reintentos, lo saltamos y seguimos con el resto
        print(f"Error al obtener el medicamento {i}")
        errores_hu1 += 1
print("Medicamentos descargados:", len(infomedslis), "| errores:", errores_hu1)

filas = []
for med in infomedslis:
    # el codigo nacional se coge de la primera presentacion
    presentaciones = med.get("presentaciones", [])
    if len(presentaciones) > 0:
        cn = presentaciones[0].get("cn")
    else:
        cn = None

    forma = med.get("formaFarmaceuticaSimplificada")
    if forma:
        forma_farmaceutica_simplificada = forma.get("nombre")
    else:
        forma_farmaceutica_simplificada = None

    estado = med.get("estado", {})
    estado_aut = estado.get("aut")
    estado_rev = estado.get("rev")

    # en docs el tipo 1 es la ficha tecnica, urlHtml es la version html (url es el pdf)
    url_ficha = None
    for doc in med.get("docs", []):
        if doc.get("tipo") == 1 and doc.get("urlHtml", "").endswith(".html"):
            url_ficha = doc.get("urlHtml")

    url_foto = None
    for foto in med.get("fotos", []):
        if "material" in foto.get("tipo", "") and foto.get("url", "").endswith(".jpg"):
            url_foto = foto.get("url")

    vias = []
    for via in med.get("viasAdministracion", []):
        vias.append(via.get("nombre"))

    fila = {
        "nregistro": med.get("nregistro"),
        "nombre": med.get("nombre"),
        "pactivos": med.get("pactivos"),
        "labtitular": med.get("labtitular"),
        "labcomercializador": med.get("labcomercializador"),
        "cn": cn,
        "dosis": med.get("dosis"),
        "forma_farmaceutica_simplificada": forma_farmaceutica_simplificada,
        "estado_aut": estado_aut,
        "estado_rev": estado_rev,
        "comercializado": int(med.get("comerc", False)),
        "requiere_receta": int(med.get("receta", False)),
        "generico": int(med.get("generico", False)),
        "afecta_conduccion": int(med.get("conduc", False)),
        "triangulo_negro": int(med.get("triangulo", False)),
        "medicamento_huerfano": int(med.get("huerfano", False)),
        "biosimilar": int(med.get("biosimilar", False)),
        "url_html_ficha_tecnica": url_ficha,
        "url_foto_materiales": url_foto,
        "num_registros_atc": len(med.get("atcs", [])),
        "num_principios_activos": len(med.get("principiosActivos", [])),
        "num_excipientes": len(med.get("excipientes", [])),
        "vias_administracion": ", ".join(vias),
    }
    filas.append(fila)

df = pd.DataFrame(filas)
df.to_excel(SALIDA_HU1, index=False)
print("Dataset de HU-1 guardado:", df.shape)

# Volvemos a leer el excel igual que hacia h2webscraping.py, asi los tipos de las columnas
# (por ejemplo cn como numero) son exactamente los mismos que en los scripts originales
df = pd.read_excel(SALIDA_HU1)


# =====================================================================
# HU-2: web scraping de las fichas tecnicas
# =====================================================================
print("===== HU-2: web scraping de las fichas tecnicas =====")
# 1. Volumen Informativo de Seguridad: palabras de la seccion 4.4
# 2. Complejidad del Desglose Clinico: numero de etiquetas <table> en todo el HTML
# 3. Indicador de Riesgo Severo: veces que aparece "grave" o "graves" en todo el texto

palabras_seccion_4_4 = []
numero_tablas_medicamentos = []
indicador_riesgo_severo = []

for i in range(0, len(df["url_html_ficha_tecnica"])):
    url = df["url_html_ficha_tecnica"].iloc[i]
    response = pedir("GET", url)
    html_parseado = BeautifulSoup(response.text, "html.parser")

    # 1. Si no tiene seccion 4.4, find devuelve None y find_next_sibling da AttributeError
    apartado_4_4 = html_parseado.find(id="4.4")
    try:
        contenido_4_4 = apartado_4_4.find_next_sibling()
        texto_4_4 = contenido_4_4.get_text(" ", strip=True)
        numero_palabras = len(texto_4_4.split())
    except AttributeError:
        print(f"El medicamento {i} no tiene seccion 4.4")
        numero_palabras = "no tiene sección 4.4"
    palabras_seccion_4_4.append(numero_palabras)

    # 2. find_all devuelve todas las tablas y len las cuenta
    numero_tablas_medicamentos.append(len(html_parseado.find_all("table")))

    # 3. contamos "grave" y "graves" quitando los signos de puntuacion pegados
    contador_graves = 0
    texto_completo_html = html_parseado.get_text(" ", strip=True)
    for palabra in texto_completo_html.lower().split():
        palabra_limpia = palabra.strip(".,;:()")
        if palabra_limpia == "grave" or palabra_limpia == "graves":
            contador_graves += 1
    indicador_riesgo_severo.append(contador_graves)

    # Cada 200 fichas lo decimos, para ver en el log que el proceso avanza
    if (i + 1) % 200 == 0:
        print("Fichas procesadas:", i + 1, "de", len(df))

df["palabras_seccion_4_4"] = palabras_seccion_4_4
df["numero_tablas"] = numero_tablas_medicamentos
df["indicador_riesgo_severo"] = indicador_riesgo_severo

df.to_excel(SALIDA_HU2, index=False)
print("Dataset de HU-2 guardado:", df.shape)

# Igual que en h3.py, partimos del excel de HU-2 leido desde disco
df_hu2 = pd.read_excel(SALIDA_HU2)


# =====================================================================
# HU-3: precios del Nomenclator del Ministerio de Sanidad
# =====================================================================
print("===== HU-3: Nomenclator =====")

# Enlace de descarga directa del excel (en vez de la pagina de busqueda del enunciado)
url = "https://www.sanidad.gob.es/profesionales/nomenclator.do?metodo=nomenclatorExcel"
response = pedir("GET", url)
with open(NOMENCLATOR, "wb") as archivo:   # "wb": escribimos los bytes tal cual
    archivo.write(response.content)

df_precios = pd.read_excel(NOMENCLATOR)
print("Nomenclator descargado:", df_precios.shape)

# .copy() para trabajar con una tabla nueva y no con un trozo de df_precios (evita un aviso de pandas)
df_precios_columnas_añadir = df_precios[[
    "Código Nacional",
    "Estado",
    "Precio de venta al público con IVA",
    "Precio de referencia",
    "Tratamiento de larga duración",
    "Especial control médico",
]].copy()
# cn en nuestro excel es decimal, asi que pasamos el Codigo Nacional a decimal para poder cruzar
df_precios_columnas_añadir["Código Nacional"] = df_precios_columnas_añadir["Código Nacional"].astype("float64")

# how="left": nos quedamos con todos los medicamentos de HU-2 aunque no esten en el Nomenclator
df_hu3 = df_hu2.merge(df_precios_columnas_añadir, left_on="cn", right_on="Código Nacional", how="left")
print("Medicamentos con precio:", df_hu3["Código Nacional"].notna().sum(), "de", len(df_hu3))

df_hu3.to_excel(SALIDA_HU3, index=False)
print("Dataset de HU-3 guardado:", df_hu3.shape)
