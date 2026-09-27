import pandas as pd
import requests
from bs4 import BeautifulSoup

#1. : Volumen Informativo de Seguridad: Contar cuántas palabras hay exactamente dentro de la sección 4.4 de cada medicamento
#2. :Complejidad del Desglose Clínico: Contar cuántas etiquetas de tablas (<table>) aparecen en todo el documento HTML.
#3. :Indicador de Riesgo Severo: Buscar y contar cuántas veces aparece la palabra "grave" (o "graves") en todo el texto. Al ser un término regulatorio estándar  para alertas máximas, nos sirve como un medidor rápido del nivel de riesgo clínico.

df = pd.read_excel("data/HU1_medicamentos_diabetes.xlsx")       #guardamos el excel como dataframe

palabras_seccion_4_4 = [] 
numero_tablas_medicamentos = []
indicador_riesgo_severo = []

for i in range (0, len(df["url_html_ficha_tecnica"])):         
    url = df["url_html_ficha_tecnica"].iloc[i]                  #recorremos todas las filas de la columna de las urls
    response = requests.get(url, timeout=30)                    #accedemos a la url
    html_parseado = BeautifulSoup(response.text, "html.parser") #convertimos el texto plano de la url(response.text) a formato html ordenado

    #1
    apartado_4_4 = html_parseado.find(id="4.4")                 #nos quedamos con el apartado que nos pide el enunciado
    try:                                                         #hay que hacer un try,except ya que si no tiene seccion 4.4,nos devuelve "None",y al hacer None.find_next_sibling da error
        contenido_4_4 = apartado_4_4.find_next_sibling()         #vamos a la etiqueta hermana (<div>) de la que contiene el id(<h..>),porque es la que contiene el texto(verlo entrando a la url y dandole a inspeccionar)
        texto_4_4 = contenido_4_4.get_text(" ",strip=True)       #nos quedamos con el texto quitando los espacios
        numero_palabras = len(texto_4_4.split())                 #recordamos que .split() parte el texto por cualquier espacio en blanco incluidos saltos de linea
    except AttributeError:
        print(f"El medicamento {i} no tiene seccion 4.4")
        numero_palabras ="no tiene sección 4.4"

    #print(f"el medicamento {i} tiene {numero_palabras} palabras)
    palabras_seccion_4_4.append(numero_palabras)


    #2
    numero_tablas = len(html_parseado.find_all("table"))        # find_all("table") busca en todo el documento y devuelve una lista con TODAS las etiquetas <table> que encuentre (a diferencia de find(), que solo daba la primera). len() cuenta cuántos elementos tiene esa lista, es decir, cuántas tablas hay en total
    numero_tablas_medicamentos.append(numero_tablas)
   

    #3
    contador_graves = 0
    texto_completo_html = html_parseado.get_text(" ", strip=True)       #nos quedamos con todo el texto del html,no solo con el de la 4.4
    for palabra in texto_completo_html.lower().split():                
        palabra_limpia = palabra.strip(".,;:()")                         #le quitamos los signos de puntuación pegados al principio o al final
        if palabra_limpia == "grave" or palabra_limpia == "graves":
            contador_graves += 1
    indicador_riesgo_severo.append(contador_graves)
    


print("Se han contado las palabras de la sección 4.4 de todos los medicamentos \n")
print("Se ha contado el número de secciones <table> en el html de cada medicamento \n")
print("Se ha encontrado el indice de riesgo para los medimcamentos")

#Ahora incluimos todo lo que hemos calculado en un excel

df["palabras_seccion_4_4"] = palabras_seccion_4_4
df["numero_tablas"] = numero_tablas_medicamentos
df["indicador_riesgo_severo"] = indicador_riesgo_severo

df.to_excel("data/HU2_medicamentos_diabetes.xlsx", index=False)
print("Dataset del HU2 guardado")

    

