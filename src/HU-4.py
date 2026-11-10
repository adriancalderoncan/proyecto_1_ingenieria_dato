# HU-4: limpieza de datos y EDA
# Version en script del cuaderno h4.ipynb, para poder llamarlo desde el archivo maestro (H7).
# Entrada: data/HU3_medicamentos_diabetes.xlsx
# Salida:  data/HU4_medicamentos_diabetes_limpio.csv y graficas en reportes/figuras/

from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # dibuja las graficas sin abrir ventanas (el script se ejecuta solo, sin nadie delante)
import matplotlib.pyplot as plt
import pandas as pd

# Rutas a partir de la carpeta del proyecto, asi el script funciona se lance desde donde se lance
# __file__ es este archivo (src/HU-4.py), .parent es src y otro .parent es la carpeta del proyecto
RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "data" / "HU3_medicamentos_diabetes.xlsx"
SALIDA = RAIZ / "data" / "HU4_medicamentos_diabetes_limpio.csv"
FIGURAS = RAIZ / "reportes" / "figuras"


# 1. CARGA
df = pd.read_excel(ENTRADA)
print("Datos de HU-3:", df.shape)


# 2. FILAS Y COLUMNAS QUE QUITAMOS
# Quitamos los medicamentos que no cruzan con el Nomenclator (Codigo Nacional nulo) porque no tienen precio
df_clean = df.copy()
df_clean = df_clean.dropna(subset=["Código Nacional"])
print("Tras quitar los que no tienen precio:", df_clean.shape)

# El precio de referencia nunca existe sin el de venta, y cuando existe es igual a el, asi que lo quitamos
df_clean = df_clean.drop(columns=["Precio de referencia"])

# Renombrar columnas
df_clean = df_clean.rename(columns={
    "Código Nacional": "codigo_nacional_nomenclator",
    "Estado": "estado",
    "Precio de venta al público con IVA": "precio_pvp_iva",
    "Tratamiento de larga duración": "tratamiento_larga_duracion",
    "Especial control médico": "especial_control_medico",
})

# codigo_nacional_nomenclator es igual que cn, asi que dejamos solo cn
print("cn igual al codigo del Nomenclator:", (df_clean["cn"] == df_clean["codigo_nacional_nomenclator"]).all())
df_clean = df_clean.drop(columns=["codigo_nacional_nomenclator"])

# Estas columnas tienen siempre el mismo valor tras limpiar el dataset, asi que no aportan nada
df_clean = df_clean.drop(columns=[
    "requiere_receta", "medicamento_huerfano", "triangulo_negro", "especial_control_medico",
])


# 3. NULOS
# estado_rev tiene un 88 % de nulos: guardamos solo si el medicamento tiene revision (1) o no (0)
df_clean["tiene_revision"] = 0
df_clean.loc[df_clean["estado_rev"].notna(), "tiene_revision"] = 1

# Con url_foto_materiales pasa lo mismo: solo nos interesa saber si existe o no
df_clean["tiene_foto_materiales"] = 0
df_clean.loc[df_clean["url_foto_materiales"].notna(), "tiene_foto_materiales"] = 1

df_clean = df_clean.drop(columns=["estado_rev", "url_foto_materiales"])

# La url de la ficha tecnica la tienen todos y solo actua como identificador
df_clean = df_clean.drop(columns=["url_html_ficha_tecnica"])


# 4. TIPOS DE DATOS
# Identificadores a texto. cn viene como decimal, asi que primero a int para quitar el .0
df_clean["nregistro"] = df_clean["nregistro"].astype(str)
df_clean["cn"] = df_clean["cn"].astype(int).astype(str)

# estado_aut son milisegundos desde el 1 de enero de 1970: lo pasamos a fecha
df_clean["estado_aut"] = pd.to_datetime(df_clean["estado_aut"], unit="ms")

# palabras_seccion_4_4 tiene 3 filas con el texto "no tiene sección 4.4": las pasamos a 0 palabras
df_clean["palabras_seccion_4_4"] = pd.to_numeric(df_clean["palabras_seccion_4_4"], errors="coerce")
print("Filas sin seccion 4.4:", df_clean["palabras_seccion_4_4"].isna().sum())
df_clean["palabras_seccion_4_4"] = df_clean["palabras_seccion_4_4"].fillna(0)
df_clean["palabras_seccion_4_4"] = df_clean["palabras_seccion_4_4"].astype(int)


# 5. LIMPIEZA DE LA COLUMNA DOSIS
# Queremos que todas las dosis queden igual: un numero, un espacio y la unidad (por ejemplo "50 mg").
# Luego nos quedamos solo con el numero.

# PASO 1: corregimos a mano las filas que tienen la dosis mal o sin saber (la dosis buena sale del nombre)
correcciones_por_fila = {
    "150001": "15 mg",               # ACTOS 15 mg (ponia "Desconocido")
    "150009": "15 mg",               # ACTOS 15 mg (ponia "Desconocido")
    "150004": "30 mg",               # ACTOS 30 mg (ponia "Desconocido")
    "150010": "30 mg",               # ACTOS 30 mg (ponia "Desconocido")
    "98070001": "75 mg",             # ISCOVER 75 MG (ponia "Desconocido")
    "134006": "100 UI/ml",           # LANTUS 100 UNIDADES/ML (ponia "Desconocida")
    "1181265011": "2,5 mg/1000 mg",  # SEGLUROMET 2,5 MG/1.000 MG (ponia "2.5 - REVISAR mg")
    "1181265025": "7,5 mg/1000 mg",  # SEGLUROMET 7,5 MG/1.000 MG (ponia "7.5 - REVISAR mg")
    "86341": "50 mg/1000 mg",        # SITAGLIPTINA/METFORMINA STADA 50 MG/1.000 MG (ponia "50 - REVISAR mg")
    "86283": "50 mg/1000 mg",        # VILDAGLIPTINA/METFORMINA STADA 50 MG/1000 MG (ponia "50 - REVISAR mg")
    "86284": "50 mg/850 mg",         # VILDAGLIPTINA/METFORMINA STADA 50 MG/850 MG (ponia "50 - REVISAR mg")
    "9529002": "6 mg/ml",            # VICTOZA 6 MG/ML (ponia "60 mg", en la ficha tecnica pone 6 mg por ml)
    "1161146005": "10 mg/5 mg",      # GLYXAMBI 10 MG/5 MG (estaba al reves, ponia "5 mg/10 mg")
    "6362003": "0,01 mg",            # BYETTA 10 MICROGRAMOS (ponia 0.25 mg, que es la concentracion por ml)
    "6362001": "0,005 mg",           # BYETTA 5 MICROGRAMOS (ponia 0.25 mg, que es la concentracion por ml)
    "10621014": "100 mg",            # RISTABEN 100 MG (ponia 128.9 mg, que es lo que pesa la sal fosfato)
    "10621015": "100 mg",            # RISTABEN 100 MG (ponia 128.9 mg, que es lo que pesa la sal fosfato)
}
for nregistro, dosis_correcta in correcciones_por_fila.items():
    df_clean.loc[df_clean["nregistro"] == nregistro, "dosis"] = dosis_correcta

# PASO 2: minusculas y sin espacios de sobra
df_clean["dosis"] = df_clean["dosis"].str.lower()
df_clean["dosis"] = df_clean["dosis"].str.split().str.join(" ")

# PASO 3: quitamos los nombres de los principios activos y otros textos que sobran.
# Primero van los textos largos: si quitaramos antes "losartan", en "losartan potasico" se quedaria "potasico" suelto.
quitar = [
    "como hidrogenosulfato",
    "metformina hidrocloruro",
    "glucagón hidrocloruro",
    "losartan potasico",
    "losartan potasio",
    "losartan",
    "lisinopril dihidrato",
    "lisinopril",
    "simvastatina",
    "irbesartan",
    "telmisartan",
    "rivaroxaban",
    "pioglitazona",
    "glimepirida",
    "captopril",
    "clopidogrel",
    "clopidrogel",                         # viene mal escrito en los datos
    "clortalidona",
    "ramipril,",                           # en "Ramipril, 2,5 mg" tambien hay que quitar la coma
    "ramipril",
    "acarbosa",
    "sitagliptina",
    "linagliptina",
    "linagiptina",                         # viene mal escrito en los datos
    "saxagliptina",
    "(empagliflozin/linagliptin) mg/mg",
    "/ comprimido",
    "/comprimido",
    "comprimidos",
    " de ",                                # "30 mg de pioglitazona" -> "30 mg"
]
for texto in quitar:
    df_clean["dosis"] = df_clean["dosis"].str.replace(texto, " ", regex=False)
df_clean["dosis"] = df_clean["dosis"].str.split().str.join(" ")

# PASO 4: casos sueltos que no siguen ninguna regla
casos_concretos = {
    "75 mh": "75 mg",                    # errata: mh -> mg
    "30 gm + 2 mg": "30 mg/2 mg",        # errata: gm -> mg (TANDEMACT 30 mg/2 mg)
    "1000/50 mg/mg": "50 mg/1000 mg",    # estaba al reves (RISTFOR, VELMETIA, ZOMARIST 50 MG/1000 MG)
    "850/50 mg/mg": "50 mg/850 mg",      # estaba al reves (ZOMARIST 50 mg/850 mg)
    "50/1000 mg": "50 mg/1000 mg",       # le faltaba la unidad al primer numero
    "50/850 mg": "50 mg/850 mg",         # le faltaba la unidad al primer numero
    "15": "15 mg",                       # no tenia unidad (RIXACAM 15 MG)
    "20": "20 mg",                       # no tenia unidad (RIXACAM 20 MG)
    "0,5 mg desmopresina acetato/ 0,5 ml": "0,1 mg/ml",  # en el nombre del medicamento pone 0,1 mg/ml
    "10 microgramos": "0,01 mg",         # 1 mg son 1000 microgramos
    "20 microgramos": "0,02 mg",
    "120 microgramos": "0,12 mg",
    "4 µg/ml": "0,004 mg/ml",
}
df_clean["dosis"] = df_clean["dosis"].replace(casos_concretos)

# PASO 5: espacio entre el numero y mg ("15mg" -> "15 mg")
for numero in "0123456789":
    df_clean["dosis"] = df_clean["dosis"].str.replace(numero + "mg", numero + " mg", regex=False)

# PASO 6: usamos siempre "/" para separar las dosis de los medicamentos con dos principios activos
separadores = {
    " + ": "/",     # "30 mg + 4 mg"    -> "30 mg/4 mg"
    " y ": "/",     # "50 mg y 1000 mg" -> "50 mg/1000 mg"
    "-": "/",       # "15 mg-850 mg"    -> "15 mg/850 mg"
    " / ": "/",     # "15 mg / 850 mg"  -> "15 mg/850 mg"
    "/ ": "/",      # "50 mg/ 850 mg"   -> "50 mg/850 mg"
    " /": "/",      # "5 mg /850 mg"    -> "5 mg/850 mg"
}
for viejo, nuevo in separadores.items():
    df_clean["dosis"] = df_clean["dosis"].str.replace(viejo, nuevo, regex=False)

# PASO 7: punto como separador decimal. Primero quitamos el punto de "1.000" porque es mil
df_clean["dosis"] = df_clean["dosis"].str.replace("1.000", "1000", regex=False)
df_clean["dosis"] = df_clean["dosis"].str.replace(",", ".", regex=False)
df_clean["dosis"] = df_clean["dosis"].str.replace("0.50 mg", "0.5 mg", regex=False)

# PASO 8: en las insulinas "U/ml", "UI/ml" y "unidades/ml" significan lo mismo, dejamos solo "UI/ml"
df_clean["dosis"] = df_clean["dosis"].str.replace("unidades/ml", "UI/ml", regex=False)
df_clean["dosis"] = df_clean["dosis"].str.replace("ui/ml", "UI/ml", regex=False)
df_clean["dosis"] = df_clean["dosis"].str.replace("u/ml", "UI/ml", regex=False)

# PASO 9: columna que indica si la dosis es por ml (1) o no (0), antes de quitar el "/ml" en el paso 11
df_clean["dosis_por_ml"] = 0
df_clean.loc[df_clean["dosis"].str.contains("/ml"), "dosis_por_ml"] = 1

# PASO 10: pasamos las insulinas de UI/ml a mg/ml (mg que hay en 100 UI, sacado de la seccion 2 de cada ficha)
mg_por_100_ui = {
    "INSULINA ASPARTA": 3.5,                                                   # Fiasp, NovoRapid
    "INSULINA ASPARTA, INSULINA ASPARTA PROTAMINA+": 3.5,                      # NovoMix
    "INSULINA DEGLUDEC": 3.66,                                                 # Tresiba
    "INSULINA DETEMIR": 14.2,                                                  # Levemir
    "INSULINA GLARGINA": 3.64,                                                 # Lantus, Abasaglar, Semglee, Toujeo
    "INSULINA GLULISINA": 3.49,                                                # Apidra
    "INSULINA LISPRO": 3.5,                                                    # Humalog
    "INSULINA LISPRO, INSULINA LISPRO PROTAMINA": 3.5,                         # Humalog Mix
    "INSULINA HUMANA": 3.5,                                                    # Humulina Regular, Humulina 30:70
    "INSULINA HUMANA ISOFANA": 3.5,                                            # Insulatard
    "INSULINA ISOFANA HUMANA PRB": 3.5,                                        # Humulina NPH
    "INSULINA SOLUBLE NEUTRA": 3.5,                                            # Actrapid
    "INSULINA SOLUBLE NEUTRA HUMANA PRB, INSULINA ISOFANA HUMANA PRB": 3.5,    # Mixtard
}
es_insulina = df_clean["dosis"].str.contains("UI/ml")
ui_por_ml = df_clean.loc[es_insulina, "dosis"].str.split(" ").str[0].astype(float)
factor = df_clean.loc[es_insulina, "pactivos"].map(mg_por_100_ui)
print("Insulinas sin equivalencia en el diccionario:", factor.isna().sum())   # tiene que salir 0

# Regla de tres: si 100 UI son "factor" mg, entonces ui_por_ml UI son ui_por_ml * factor / 100
mg_por_ml = (ui_por_ml * factor / 100).round(2)
df_clean.loc[es_insulina, "dosis"] = mg_por_ml.astype(str) + " mg/ml"
df_clean["dosis"] = df_clean["dosis"].str.replace(".0 mg/ml", " mg/ml", regex=False)

# PASO 11: quitamos el "/ml" para que todas acaben en "mg" (el dato ya esta en dosis_por_ml)
df_clean["dosis"] = df_clean["dosis"].str.replace("mg/ml", "mg", regex=False)

# PASO 12: guardamos el segundo numero de los medicamentos con dos dosis ("50 mg/1000 mg" -> 1000)
segunda_parte = df_clean["dosis"].str.split("/").str[1]
segundo_numero = segunda_parte.str.split(" ").str[0]
df_clean["dosis_numero_2"] = pd.to_numeric(segundo_numero, errors="coerce").fillna(0)

# PASO 13: dejamos solo la primera dosis ("100 mg/1000 mg" -> "100 mg")
df_clean["dosis"] = df_clean["dosis"].str.split("/").str[0]

# COMPROBACION: estos dos numeros tienen que salir 0
print("Filas que no acaban en mg:", (~df_clean["dosis"].str.endswith(" mg")).sum())
print("Filas que todavia tienen una barra:", df_clean["dosis"].str.contains("/").sum())

# PASO 14: nos quedamos con el numero de la dosis ("50 mg" -> 50)
df_clean["dosis_numero"] = df_clean["dosis"].str.split(" ").str[0].astype(float)


# 6. CATEGORIAS
# tratamiento_larga_duracion de SI/NO a 1/0
df_clean["tratamiento_larga_duracion"] = df_clean["tratamiento_larga_duracion"].map({"SI": 1, "NO": 0})

# Agrupamos forma_farmaceutica_simplificada en 4 grupos
grupos_forma = {
    "COMPRIMIDO": "COMPRIMIDO",
    "COMPRIMIDO LIBERACION MODIFICADA": "COMPRIMIDO",
    "COMPRIMIDO SUBLINGUAL": "COMPRIMIDO",
    "CAPSULA": "CAPSULA",
    "INYECTABLE": "INYECTABLE",
    "PRODUCTO USO NASAL": "OTRA",
    "SOLUCIÓN/SUSPENSIÓN ORAL": "OTRA",
}
df_clean["forma_farmaceutica_simplificada"] = df_clean["forma_farmaceutica_simplificada"].map(grupos_forma)

# Agrupamos vias_administracion en 3 grupos (lo que no este en el diccionario pasa a NaN)
grupos_via = {
    "VÍA ORAL": "ORAL",
    "VÍA SUBLINGUAL": "ORAL",
    "VÍA SUBCUTÁNEA": "INYECTABLE",
    "VÍA INTRAVENOSA, VÍA SUBCUTÁNEA": "INYECTABLE",
    "VÍA INTRAMUSCULAR, VÍA SUBCUTÁNEA": "INYECTABLE",
    "VÍA INTRAMUSCULAR, VÍA INTRAVENOSA, VÍA SUBCUTÁNEA": "INYECTABLE",
    "VÍA NASAL": "NASAL",
}
df_clean["vias_administracion"] = df_clean["vias_administracion"].map(grupos_via)

df_clean = df_clean.reset_index(drop=True)
print("Dataset limpio:", df_clean.shape)               # (827, 28)
print("Nulos totales:", df_clean.isna().sum().sum())   # 0


# 7. OUTLIERS (metodo IQR). Solo los contamos: no eliminamos ninguno porque los valores altos son reales
columnas_numericas = [
    "precio_pvp_iva",
    "palabras_seccion_4_4",
    "numero_tablas",
    "indicador_riesgo_severo",
    "num_excipientes",
    "dosis_numero",
]
for columna in columnas_numericas:
    q1 = df_clean[columna].quantile(0.25)
    q3 = df_clean[columna].quantile(0.75)
    iqr = q3 - q1
    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr
    outliers = df_clean[(df_clean[columna] < limite_inferior) | (df_clean[columna] > limite_superior)]
    print(columna, "-> limite superior:", limite_superior, "| outliers:", len(outliers))


# 8. GRAFICAS (se guardan en reportes/figuras)
FIGURAS.mkdir(parents=True, exist_ok=True)

# Histograma del precio
mediana_precio = df_clean["precio_pvp_iva"].median()
plt.figure(figsize=(8, 4))
plt.hist(df_clean["precio_pvp_iva"], bins=30, color="steelblue", edgecolor="white")
plt.axvline(mediana_precio, color="black", linestyle="--", label="Mediana: " + str(mediana_precio) + " €")
plt.title("Distribución del precio de venta al público con IVA")
plt.xlabel("Precio (€)")
plt.ylabel("Número de medicamentos")
plt.legend()
plt.savefig(FIGURAS / "01_distribucion_precio.png", dpi=150, bbox_inches="tight")
plt.close()   # cerramos la figura para que no se acumulen en memoria

# El mismo histograma para las columnas de la ficha tecnica
columnas_ficha = ["palabras_seccion_4_4", "numero_tablas", "indicador_riesgo_severo", "num_excipientes"]
for columna in columnas_ficha:
    mediana = df_clean[columna].median()
    plt.figure(figsize=(8, 3))
    plt.hist(df_clean[columna], bins=30, color="steelblue", edgecolor="white")
    plt.axvline(mediana, color="black", linestyle="--", label="Mediana: " + str(mediana))
    plt.title("Distribución de " + columna)
    plt.xlabel(columna)
    plt.ylabel("Número de medicamentos")
    plt.legend()
    plt.savefig(FIGURAS / ("hist_" + columna + ".png"), dpi=150, bbox_inches="tight")
    plt.close()


# 9. GUARDAR EL CSV LIMPIO
df_clean.to_csv(SALIDA, index=False, encoding="utf-8-sig")
print("CSV de HU-4 guardado en", SALIDA)
