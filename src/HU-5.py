# HU-5: agrupar medicamentos con K-Means
# Version en script del cuaderno h5.ipynb, para poder llamarlo desde el archivo maestro (H7).
# Entrada: data/HU4_medicamentos_diabetes_limpio.csv
# Salida:  data/HU5_medicamentos_diabetes_clusters.csv y graficas h5_*.png en reportes/figuras/

from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # dibuja las graficas sin abrir ventanas (el script se ejecuta solo, sin nadie delante)
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

# Rutas a partir de la carpeta del proyecto, asi el script funciona se lance desde donde se lance
RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "data" / "HU4_medicamentos_diabetes_limpio.csv"
SALIDA = RAIZ / "data" / "HU5_medicamentos_diabetes_clusters.csv"
FIGURAS = RAIZ / "reportes" / "figuras"
FIGURAS.mkdir(parents=True, exist_ok=True)


# 1. CARGAR LOS DATOS
# nregistro y cn son texto porque son codigos, no cantidades
df = pd.read_csv(ENTRADA, dtype={"nregistro": str, "cn": str})

# Al leer un CSV las fechas llegan como texto, asi que volvemos a pasar estado_aut a fecha
df["estado_aut"] = pd.to_datetime(df["estado_aut"])

print("Datos de HU-4:", df.shape)
print("Nulos:", df.isna().sum().sum())


# 2. PREPARAR LAS COLUMNAS NUMERICAS
# Anos desde la autorizacion y 1/0 si es inyectable
df["antiguedad_anios"] = 2026 - df["estado_aut"].dt.year
df["es_inyectable"] = 0
df.loc[df["forma_farmaceutica_simplificada"] == "INYECTABLE", "es_inyectable"] = 1

columnas_modelo = [
    "precio_pvp_iva",
    "palabras_seccion_4_4",
    "numero_tablas",
    "indicador_riesgo_severo",
    "num_excipientes",
    "dosis_numero",
    "num_principios_activos",
    "antiguedad_anios",
    "generico",
    "comercializado",
    "afecta_conduccion",
    "tratamiento_larga_duracion",
    "es_inyectable",
]
X = df[columnas_modelo]
print("Tabla del modelo:", X.shape, "| nulos:", X.isna().sum().sum())


# 3. ESCALAR (media 0 y desviacion 1 en cada columna, para que todas pesen igual en las distancias)
escalador = StandardScaler()
X_escalado = escalador.fit_transform(X)


# 4. ELEGIR K: probamos de 2 a 10 y miramos inercia (codo) y silhouette
valores_k = [2, 3, 4, 5, 6, 7, 8, 9, 10]
inercias = []
silhouettes = []
for k in valores_k:
    modelo_prueba = KMeans(n_clusters=k, random_state=42, n_init=50)
    grupos = modelo_prueba.fit_predict(X_escalado)
    inercia = modelo_prueba.inertia_
    silhouette = silhouette_score(X_escalado, grupos)
    inercias.append(inercia)
    silhouettes.append(silhouette)
    print("K =", k, "| inercia:", round(inercia), "| silhouette:", round(silhouette, 3))

# Grafica del codo
plt.figure(figsize=(8, 4))
plt.plot(valores_k, inercias, marker="o", color="steelblue")
plt.axvline(6, color="black", linestyle="--", label="K elegido: 6")
plt.title("Método del codo")
plt.xlabel("Número de grupos (K)")
plt.ylabel("Inercia")
plt.legend()
plt.savefig(FIGURAS / "h5_codo.png", dpi=150, bbox_inches="tight")
plt.close()

# Grafica de silhouette
plt.figure(figsize=(8, 4))
plt.plot(valores_k, silhouettes, marker="o", color="steelblue")
plt.axvline(6, color="black", linestyle="--", label="K elegido: 6")
plt.title("Silhouette según el número de grupos")
plt.xlabel("Número de grupos (K)")
plt.ylabel("Silhouette")
plt.legend()
plt.savefig(FIGURAS / "h5_silhouette.png", dpi=150, bbox_inches="tight")
plt.close()


# 5. MODELO FINAL CON K = 6
modelo = KMeans(n_clusters=6, random_state=42, n_init=50)
df["cluster"] = modelo.fit_predict(X_escalado)
print("Silhouette final:", round(silhouette_score(X_escalado, df["cluster"]), 3))


# 6. ANALIZAR LOS GRUPOS (lo dejamos en la salida para poder revisarlo en el log)
for numero in range(6):
    filas_grupo = df[df["cluster"] == numero]
    print("Grupo", numero, "- medicamentos:", len(filas_grupo),
          "- mediana del precio:", filas_grupo["precio_pvp_iva"].median())
    print(filas_grupo["pactivos"].value_counts().head(5))


# 7. NOMBRE DE CADA GRUPO (los perfiles salen del analisis del cuaderno h5.ipynb)
# En el cuaderno pusimos los nombres a mano segun el numero de grupo (0 = Metformina, 1 = ...).
# Pero si la API devuelve medicamentos nuevos, K-Means puede numerar los grupos en otro orden
# y los nombres quedarian cambiados. Por eso aqui reconocemos cada grupo por lo que le caracteriza:
# miramos la media de cada columna en cada grupo y vamos eligiendo el grupo que mas destaca.
medias = df.groupby("cluster")[columnas_modelo].mean()

# (columna en la que destaca el grupo, nombre del perfil). El orden importa: cada grupo
# elegido se quita de la tabla para que no se pueda elegir dos veces.
reglas = [
    ("es_inyectable", "Inyectables no genéricos"),                          # todos son inyectables
    ("num_principios_activos", "Combinaciones de dos principios activos"),  # casi 2 principios activos de media
    ("dosis_numero", "Metformina barata de dosis alta"),                    # dosis media de unos 900 mg
    ("numero_tablas", "Anticoagulantes con ficha compleja"),                # unas 18 tablas de media
    ("tratamiento_larga_duracion", "Baratos de larga duración"),            # todos son de larga duracion
]
nombres_grupos = {}
for columna, nombre in reglas:
    grupo = int(medias[columna].idxmax())   # idxmax da el numero de grupo con la media mas alta
    nombres_grupos[grupo] = nombre
    medias = medias.drop(index=grupo)    # lo quitamos para las siguientes reglas

# El grupo que queda es el de comprimidos con valores cerca de la media
nombres_grupos[int(medias.index[0])] = "Comprimidos genéricos de uso general"
print("Nombres asignados:", nombres_grupos)

df["perfil"] = df["cluster"].map(nombres_grupos)
print(df["perfil"].value_counts())

# Numero de medicamentos de cada grupo
conteo_perfiles = df["perfil"].value_counts().sort_values()
plt.figure(figsize=(9, 4))
barras = plt.barh(conteo_perfiles.index, conteo_perfiles.values, color="steelblue")
plt.bar_label(barras)
plt.title("Medicamentos en cada perfil")
plt.xlabel("Número de medicamentos")
plt.savefig(FIGURAS / "h5_tamano_perfiles.png", dpi=150, bbox_inches="tight")
plt.close()


# 8. GRUPOS EN UN DIBUJO CON PCA (13 columnas resumidas en 2)
pca = PCA(n_components=2)
puntos = pca.fit_transform(X_escalado)
df["pca_1"] = puntos[:, 0]
df["pca_2"] = puntos[:, 1]
informacion = pca.explained_variance_ratio_.sum() * 100
print("Informacion que conserva el dibujo:", round(informacion, 1), "%")

colores = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
marcadores = ["o", "s", "^", "D", "v", "P"]
plt.figure(figsize=(10, 6))
for numero in range(6):
    filas_grupo = df[df["cluster"] == numero]
    plt.scatter(
        filas_grupo["pca_1"],
        filas_grupo["pca_2"],
        color=colores[numero],
        marker=marcadores[numero],
        alpha=0.6,
        label=nombres_grupos[numero],
    )
plt.title("Perfiles de medicamentos resumidos en 2 dimensiones con PCA")
plt.xlabel("pca_1")
plt.ylabel("pca_2")
plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
plt.savefig(FIGURAS / "h5_pca.png", dpi=150, bbox_inches="tight")
plt.close()


# 9. GUARDAR EL CSV (sin las columnas que solo usamos dentro del script)
df_salida = df.drop(columns=["antiguedad_anios", "es_inyectable", "pca_1", "pca_2"])
df_salida.to_csv(SALIDA, index=False, encoding="utf-8-sig")
print("CSV de HU-5 guardado en", SALIDA, "-", df_salida.shape)
