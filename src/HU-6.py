# HU-6: carga en MySQL y vista con los KPIs
# Version en script del cuaderno h6.ipynb, para poder llamarlo desde el archivo maestro (H7).
# Entrada: data/HU5_medicamentos_diabetes_clusters.csv
# Salida:  tabla medicamentos_diabetes y vista kpis_medicamentos en la base de datos biodatapharma
#
# IMPORTANTE: la contrasena ya no se pide con input(), porque una tarea programada no tiene a nadie
# que la escriba. Se lee de la variable de entorno MYSQL_PASSWORD. En Windows se crea una vez con:
#     setx MYSQL_PASSWORD "vuestra_clave"
# (y hay que abrir una terminal nueva para que se vea).

import os
from pathlib import Path

import mysql.connector
import pandas as pd

# Rutas a partir de la carpeta del proyecto, asi el script funciona se lance desde donde se lance
RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "data" / "HU5_medicamentos_diabetes_clusters.csv"


# 1. CARGAR EL CSV DE HU-5
df = pd.read_csv(ENTRADA, encoding="utf-8-sig")
print("Datos de HU-5:", df.shape)


# 2. CONECTAR CON MYSQL
# os.environ.get lee la variable de entorno; si no existe devuelve el segundo valor
usuario = os.environ.get("MYSQL_USER", "root")
clave = os.environ.get("MYSQL_PASSWORD")
if clave is None:
    # Paramos con un error claro en vez de quedarnos esperando
    raise RuntimeError("Falta la variable de entorno MYSQL_PASSWORD con la contraseña de MySQL")

# Nos conectamos sin elegir base de datos, porque puede que todavia no exista en este ordenador
conexion = mysql.connector.connect(
    host="localhost",
    user=usuario,
    password=clave,
)
cursor = conexion.cursor()
print("Conectado:", conexion.is_connected())

# Creamos la base de datos si no existe y la elegimos (USE) para el resto de queries
cursor.execute("CREATE DATABASE IF NOT EXISTS biodatapharma")
cursor.execute("USE biodatapharma")


# 3. CREAR LA TABLA (la borramos antes para que cada ejecucion empiece de cero)
cursor.execute("DROP TABLE IF EXISTS medicamentos_diabetes")
create_sql = """
CREATE TABLE IF NOT EXISTS medicamentos_diabetes (
    nregistro INT PRIMARY KEY,
    nombre VARCHAR(150),
    pactivos VARCHAR(64),
    labtitular VARCHAR(64),
    labcomercializador VARCHAR(64),
    cn INT,
    dosis VARCHAR(64),
    forma_farmaceutica_simplificada VARCHAR(64),
    estado_aut DATETIME,
    comercializado INT,
    generico INT,
    afecta_conduccion INT,
    biosimilar INT,
    num_registros_atc INT,
    num_principios_activos INT,
    num_excipientes INT,
    vias_administracion VARCHAR(64),
    palabras_seccion_4_4 INT,
    numero_tablas INT,
    indicador_riesgo_severo INT,
    estado VARCHAR(64),
    precio_pvp_iva DOUBLE,
    tratamiento_larga_duracion INT,
    tiene_revision INT,
    tiene_foto_materiales INT,
    dosis_por_ml INT,
    dosis_numero_2 DOUBLE,
    dosis_numero DOUBLE,
    cluster INT,
    perfil VARCHAR(64)
)
"""
cursor.execute(create_sql)
print("Tabla creada")


# 4. INSERTAR LAS FILAS
# Un %s por columna: son los huecos que el conector rellena con los valores de cada fila
huecos = ", ".join(["%s"] * len(df.columns))
insert_sql = f"INSERT INTO medicamentos_diabetes VALUES ({huecos})"

# astype(object) + tolist() convierte los numeros de numpy en numeros normales de Python
filas = df.astype(object).values.tolist()
cursor.executemany(insert_sql, filas)
conexion.commit()   # sin commit los datos no se quedan guardados
print("Filas insertadas:", cursor.rowcount)


# 5. VISTA CON LOS 5 KPIs
# NOTA SOBRE KPIs 4 y 5: el enunciado usa el PR (precio de referencia), pero lo eliminamos en HU4 porque
# era igual al PVP y las formulas darian 0. Por eso los sustituimos por la diferencia con el minimo del
# grupo y la desviacion respecto a la media del grupo.
# KPI 1: total_componentes = principios activos + excipientes
# KPI 2: densidad_ficha_tecnica = palabras de la seccion 4.4 entre numero de tablas (NULL si no hay tablas)
# KPI 3: ranking_precio_grupo = posicion por precio dentro de su forma farmaceutica (1 = el mas caro)
# KPI 4: diferencia_precio_minimo_grupo = precio menos el precio del mas barato de su grupo
# KPI 5: desviacion_precio_grupo = % que se aleja el precio de la media de su grupo
vista_sql = """
CREATE OR REPLACE VIEW kpis_medicamentos AS
SELECT
    nregistro,
    nombre,
    forma_farmaceutica_simplificada,
    precio_pvp_iva,
    num_principios_activos,
    num_excipientes,
    num_principios_activos + num_excipientes AS total_componentes,
    palabras_seccion_4_4,
    numero_tablas,
    palabras_seccion_4_4 / numero_tablas AS densidad_ficha_tecnica,
    ROW_NUMBER() OVER (
        PARTITION BY forma_farmaceutica_simplificada
        ORDER BY precio_pvp_iva DESC
    ) AS ranking_precio_grupo,
    ROUND(precio_pvp_iva - MIN(precio_pvp_iva) OVER (PARTITION BY forma_farmaceutica_simplificada), 2) AS diferencia_precio_minimo_grupo,
    ROUND(
        (precio_pvp_iva - AVG(precio_pvp_iva) OVER (PARTITION BY forma_farmaceutica_simplificada))
        / AVG(precio_pvp_iva) OVER (PARTITION BY forma_farmaceutica_simplificada) * 100,
        2
    ) AS desviacion_precio_grupo
FROM medicamentos_diabetes
"""
cursor.execute(vista_sql)
print("Vista creada")


# 6. COMPROBACION: la vista tiene que tener tantas filas como el CSV
cursor.execute("SELECT COUNT(*) FROM kpis_medicamentos")
print("Filas en la vista kpis_medicamentos:", cursor.fetchone()[0])

cursor.close()
conexion.close()
print("Conexion cerrada")
