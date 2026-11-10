# Contexto del proyecto BIODATAPHARMA (grupo JAA, diabetes) — HU-1 a HU-7

> Documento de traspaso para cualquier miembro del equipo y su Claude. Resume qué pide cada Historia de Usuario (HU), qué archivo la resuelve, qué decisiones tomamos y qué queda pendiente.
> **Actualizado: 10 de noviembre de 2026** (commit `02f0df5`). Sustituye a `CONTEXTO_Proyecto_BIODATAPHARMA_H1-H3.md`, que se queda solo como histórico.
> Si algo de aquí no coincide con el código del repo, **manda el código**: compruébalo antes de fiarte.

---

## 0. Cómo usar este documento con Claude

- Pásale este archivo al empezar un chat y dile en qué HU estás.
- Los enunciados oficiales están en `enunciado/`. **El enunciado y lo que diga el profesor mandan** sobre cualquier cosa escrita aquí. Si algo no aparece en el material, hay que decirlo en vez de inventarlo.
- Forma de trabajar que usa Alberto (cada uno puede adaptarla): Claude como tutor, paso a paso, explicando cada comando y por qué se usa; código sencillo, al nivel de clase, sin librerías ni arquitecturas extra; comentarios en el código que expliquen "qué hacemos y por qué".
- No guardar contraseñas en el repo ni en este documento.

---

## 1. Datos básicos

- **Asignatura:** Ingeniería del Dato / Tecnología de Procesamiento de Big Data, MUIAAp (ICAI, Comillas). Profesor: Guillermo Gallego.
- **Proyecto:** BIODATAPHARMA, sistema que recoge, limpia y analiza datos de medicamentos según una enfermedad.
- **Grupo:** JAA — Alberto Rey, Adrián Calderón, Jorge Montoyo. **Enfermedad asignada: diabetes.**
- **Repo:** https://github.com/adriancalderoncan/proyecto_1_ingenieria_dato (rama `main`).
- **Entorno:** Python 3.10 en un entorno virtual `.venv` dentro del proyecto (creado con uv). Librerías en `requirements.txt`: pandas, requests, beautifulsoup4, scikit-learn, matplotlib, seaborn, openpyxl, xlrd, ipykernel, lxml, mysql-connector-python.
- **Base de datos:** MySQL en local (`localhost`), base de datos `biodatapharma`.
- En el equipo hay Mac y Windows: ojo con los comandos que cambian entre sistemas (variables de entorno, Crontab frente a Programador de Tareas).

### Estructura del repo

```
proyecto_1_ingenieria_dato/
├── Claude outputs/      documentos de contexto (este archivo)
├── data/                ficheros que genera cada HU
├── documentacion_api/   documentación de la API de CIMA
├── entregas/            documentos entregados en cada sprint
├── enunciado/           PDFs oficiales de las HU y plantilla de entrega
├── reportes/figuras/    gráficas de HU-4 y HU-5
├── src/                 código
├── README.md
└── requirements.txt
```

### Archivos de `src/`

| Archivo | Qué es |
|---|---|
| `HU1_HU3.py`, `HU-4.py`, `HU-5.py`, `HU-6.py` | **Scripts definitivos** que llamará el archivo maestro de la HU-7 |
| `h1.py`, `h2webscraping.py`, `h3.py` | Scripts originales de HU-1 a HU-3 (se conservan; `HU1_HU3.py` los junta y mejora) |
| `h4.ipynb`, `h5.ipynb`, `h6.ipynb` | Notebooks originales de HU-4 a HU-6, con el análisis y las explicaciones |
| `prueba*.ipynb` | Notebooks de pruebas de cada miembro |
| `queries.txt` | SQL de la HU-6 explicado paso a paso |
| `cambios.txt` | Resumen de las decisiones de HU-4 y HU-5 |

---

## 2. El flujo completo (pipeline)

Cada HU genera un fichero que necesita la siguiente. Por eso el orden importa.

```
HU1_HU3.py → data/HU1_...xlsx → data/HU2_...xlsx → data/HU3_medicamentos_diabetes.xlsx
HU-4.py    → data/HU4_medicamentos_diabetes_limpio.csv   (+ gráficas en reportes/figuras)
HU-5.py    → data/HU5_medicamentos_diabetes_clusters.csv (+ gráficas h5_*.png)
HU-6.py    → MySQL: tabla medicamentos_diabetes y vista kpis_medicamentos
HU-7       → archivo maestro que ejecuta los cuatro en orden, con log y programado
```

Los cuatro scripts definitivos calculan sus rutas con `Path(__file__)` (la carpeta donde está el propio script), así que **funcionan se lancen desde donde se lancen**. Los originales (`h1.py`, etc.) usan rutas relativas `data/...` y solo funcionan lanzados desde la raíz del proyecto; los notebooks usan `../data/...`.

**Los números de este documento (1569, 827, etc.) son de las ejecuciones de octubre y principios de noviembre.** Las fuentes cambian con el tiempo, así que cada ejecución nueva puede dar cifras distintas.

---

## 3. Qué se hizo en cada HU

### HU-1 — Extracción desde la API de CIMA
- POST a `https://cima.aemps.es/cima/rest/buscarEnFichaTecnica?pagina=N` con el payload `[{"seccion": "4.1", "texto": "diabetes", "contiene": 1}]` para sacar los `nregistro`.
- GET a `https://cima.aemps.es/cima/rest/medicamento?nregistro=<n>` por cada uno, y se monta una fila con 23 columnas (las que lista el enunciado). `cn` es el Código Nacional de la primera presentación. Los campos verdadero/falso se guardan como 1/0.
- Salida: `data/HU1_medicamentos_diabetes.xlsx` (1569 filas × 23 columnas en la ejecución original).
- **Mejora en `HU1_HU3.py`:** el número de páginas ya no es fijo (`range(1, 9)`), se calcula con `totalFilas` y `tamanioPagina`, como pide la nota del enunciado.

### HU-2 — Web scraping de las fichas técnicas
Por cada medicamento se descarga su ficha técnica en HTML y se añaden 3 columnas:
- `palabras_seccion_4_4`: palabras de la sección 4.4. Si la ficha no tiene esa sección se guarda el texto `"no tiene sección 4.4"` (pasó en 3 medicamentos).
- `numero_tablas`: número de etiquetas `<table>` del documento.
- `indicador_riesgo_severo`: veces que aparece "grave" o "graves".
- Salida: `data/HU2_medicamentos_diabetes.xlsx` (26 columnas). **Tarda muchos minutos** (una petición por medicamento).

### HU-3 — Precios del Nomenclátor (Ministerio de Sanidad)
- **La descarga está automatizada** (el profesor lo exige para que los precios estén actualizados): el script baja el Excel desde `https://www.sanidad.gob.es/profesionales/nomenclator.do?metodo=nomenclatorExcel` y lo guarda en `data/nomenclator.xls` en cada ejecución. No hay que descargarlo a mano.
- Se añaden 6 columnas (Código Nacional, Estado, Precio de venta al público con IVA, Precio de referencia, Tratamiento de larga duración, Especial control médico) cruzando por `cn` con un `merge` de tipo `left`.
- Detalle importante: `cn` es decimal (`float64`) y el Código Nacional del Nomenclátor es entero; hay que igualar los tipos antes de cruzar o el cruce no encuentra nada.
- Salida: `data/HU3_medicamentos_diabetes.xlsx` (1569 × 32). **742 medicamentos no cruzan** con el Nomenclátor: 632 son no comercializados y 110 comercializados que no supimos explicar del todo.

### Mejoras comunes de `HU1_HU3.py`
- Función `pedir()`: hace cada petición con hasta 3 intentos y 5 segundos de espera entre ellos. Si falla tras 3 intentos, lanza el error.
- Usa una `requests.Session()` para reutilizar la conexión.
- Imprime el avance cada 200 fichas, para que se vea en el log que no está colgado.

### HU-4 — Limpieza y EDA (`HU-4.py`, análisis en `h4.ipynb`)
Entrada: Excel de HU-3. Salida: `data/HU4_medicamentos_diabetes_limpio.csv` (**827 filas × 28 columnas, 0 nulos**) y gráficas en `reportes/figuras/`. Decisiones:
- **Filas:** se quitan las 742 que no cruzan con el Nomenclátor, porque no tienen precio.
- **Precio de referencia eliminado:** cuando existe es siempre igual al precio de venta. *Esto afecta a los KPIs de la HU-6.*
- **Otras columnas eliminadas:** el Código Nacional repetido, las que tenían un solo valor tras limpiar (`requiere_receta`, `medicamento_huerfano`, `triangulo_negro`, `especial_control_medico`) y la URL de la ficha.
- **Nulos:** `estado_rev` y `url_foto_materiales` pasan a columnas 1/0 (`tiene_revision`, `tiene_foto_materiales`). Las 3 fichas sin sección 4.4 quedan con 0 palabras.
- **Tipos:** `nregistro` y `cn` a texto, `estado_aut` a fecha (venía en milisegundos desde 1970), `tratamiento_larga_duracion` a 1/0.
- **Columnas renombradas:** `estado`, `precio_pvp_iva`, `tratamiento_larga_duracion`.
- **Categorías:** forma farmacéutica en 4 grupos (COMPRIMIDO, CAPSULA, INYECTABLE, OTRA) y vía de administración en 3 (ORAL, INYECTABLE, NASAL), con diccionarios y `.map`.
- **Dosis:** estandarizada a "número mg", con correcciones a mano por `nregistro` y un diccionario de equivalencias para insulinas. Columnas nuevas `dosis_numero`, `dosis_numero_2` y `dosis_por_ml`.
- **Outliers:** revisados con IQR y boxplots. No se elimina ninguno porque los valores altos son reales.

### HU-5 — K-Means (`HU-5.py`, análisis en `h5.ipynb`)
Entrada: CSV de HU-4. Salida: `data/HU5_medicamentos_diabetes_clusters.csv` (827 × 30: las de HU-4 más `cluster` y `perfil`).
- 13 columnas numéricas: `precio_pvp_iva`, `palabras_seccion_4_4`, `numero_tablas`, `indicador_riesgo_severo`, `num_excipientes`, `dosis_numero`, `num_principios_activos`, `antiguedad_anios`, `generico`, `comercializado`, `afecta_conduccion`, `tratamiento_larga_duracion`, `es_inyectable`.
- Escalado con `StandardScaler`. Se prueba K de 2 a 10 (inercia y silhouette) y se elige **K = 6** (`random_state=42`, `n_init=50`, silhouette 0,292).
- Perfiles: comprimidos genéricos de uso general (335), baratos de larga duración (227), combinaciones de dos principios activos (108), anticoagulantes con ficha compleja (77), inyectables no genéricos (51), metformina barata de dosis alta (29).

### HU-6 — Carga en MySQL y KPIs (`HU-6.py`, SQL explicado en `queries.txt`)
- Crea la base de datos `biodatapharma` si no existe, crea la tabla `medicamentos_diabetes` (30 columnas) e inserta las filas del CSV de HU-5.
- **Contraseña de MySQL:** `HU-6.py` ya no la pide con `input()`; la lee de la variable de entorno `MYSQL_PASSWORD` (y el usuario de `MYSQL_USER`, por defecto `root`). Cada miembro tiene que crearla en su ordenador. Si no existe, el script para con un error claro.
- Vista `kpis_medicamentos` con 5 KPIs:
  1. `total_componentes` = principios activos + excipientes.
  2. `densidad_ficha_tecnica` = palabras de la sección 4.4 / número de tablas (NULL si no hay tablas).
  3. `ranking_precio_grupo` = `ROW_NUMBER()` con `PARTITION BY forma_farmaceutica_simplificada` ordenado por precio de mayor a menor.
  4. `diferencia_precio_minimo_grupo` = precio menos el precio más barato de su grupo.
  5. `desviacion_precio_grupo` = % que se aleja el precio de la media de su grupo.
- **Los KPIs 4 y 5 son propios.** El enunciado pedía "Desviación de precio (%)" y "Margen económico absoluto" con el precio de referencia, pero lo eliminamos en HU-4 (era igual al PVP y darían siempre 0). El profesor dijo que podíamos crear KPIs propios si explicábamos qué calculan y por qué.
- **Estado actual del código:** hace `DROP TABLE` y vuelve a crear la tabla en cada ejecución. **Esto hay que cambiarlo** (ver sección 5).

---

## 4. HU-7 — Orquestación (en curso)

### Qué pide el enunciado (`enunciado/Historias Usuario_HU7.pdf`)
1. **Archivo maestro** en Python llamado `NombreEquipo_enfermedad.py` (el nuestro: `JAA_diabetes.py`) que llame en orden a `HU1_HU3.py`, `HU-4.py`, `HU-5.py` y `HU-6.py`.
2. **Programarlo** con Crontab (Linux; en Mac también se usa Crontab) o con el Programador de Tareas (Windows).
3. **Registrar con la librería `logging`** todas las trazas, éxitos y errores en un fichero `NombreEquipo_enfermedad_fecha.log` (el nuestro: `JAA_diabetes_<fecha>.log`).

### Conceptos
- **Orquestación:** coordinar de forma automática la ejecución de varios scripts que dependen unos de otros. Si el paso A falla, el B no arranca.
- **`logging`:** como un `print`, pero el mensaje se guarda en un fichero con fecha, hora y nivel (INFO, ERROR, CRITICAL).
- **`subprocess.run`:** lanza otro programa desde Python, igual que escribir `python HU-4.py` en la terminal. Devuelve un `returncode`: 0 si fue bien, otro número si falló.
- **Crontab:** lista de tareas programadas del sistema. `crontab -e` la edita, `crontab -l` la muestra, `crontab -r` la borra. Cada línea tiene 5 campos de tiempo (minuto, hora, día del mes, mes, día de la semana) y el comando.

### Código base del profesor (clase "Orquestación de Ficheros y Automatización de Procesos", diapositiva 8)

```python
import logging, subprocess, sys, os

LOG_FILE = "NombreEquipo_enfermedad.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def ejecutar_proceso(script_name):
    logging.info(f"Iniciando ejecución de: {script_name}")
    result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)
    if result.returncode == 0:
        logging.info(f"ÉXITO al ejecutar {script_name}")
    else:
        logging.error(f"ERROR en {script_name}: {result.stderr}")
        raise Exception(f"Fallo crítico en {script_name}")

if __name__ == "__main__":
    scripts = ["HU1_HU3.py", "HU-4.py", "HU-5.py", "HU-6.py"]
    for script in scripts:
        try:
            ejecutar_proceso(script)
        except Exception as e:
            logging.critical("Flujo interrumpido.")
            sys.exit(1)
```

Ejemplo de Crontab de clase: `30 07 * * 1-5 /usr/bin/python3 /ruta/proyecto/NombreEquipo_enfermedad.py` (lunes a viernes a las 07:30).

Airflow y Control-M se vieron en clase como teoría; **la HU-7 no los pide**.

### Lo que hay que adaptar del código del profesor
- **Nombre del log con fecha:** la diapositiva usa `NombreEquipo_enfermedad.log`, pero el enunciado pide `..._fecha.log`. Manda el enunciado. El formato exacto de la fecha no lo dice ningún documento.
- **Rutas de los scripts:** el ejemplo los llama por su nombre a secas, y eso solo funciona si la terminal está en la misma carpeta que ellos. Conviene que el maestro construya la ruta a partir de su propia carpeta, como hacen ya los cuatro scripts.
- **Crontab:** hay que usar el Python del entorno virtual (`.venv/bin/python`), no `/usr/bin/python3`, porque las librerías están en el entorno virtual. Además cron no carga las variables de entorno de la terminal, así que `MYSQL_PASSWORD` hay que dársela también a la tarea programada.

---

## 5. Indicaciones del profesor del 10 de noviembre (afectan a HU-6 y HU-7)

Dichas en clase y apuntadas por Alberto. No están en el enunciado; si hay dudas, confirmadlas con él.

1. **Carga incremental en MySQL.** Como el maestro ejecuta todas las HU cada vez, la HU-6 se repetirá muchas veces. En vez de borrar y recrear la tabla, cada ejecución debe **añadir** sus filas (append) con una **columna con la fecha de carga**, usando el código nacional (`cn`) para identificar al medicamento.
2. **Para qué:** poder enseñar en Power BI un gráfico con cuántos registros se cargan cada día (por ejemplo 847 un día, 100 otro, 847 otro).
3. **Nomenclátor automático:** la descarga del fichero de precios debe estar automatizada para que los precios se actualicen. Ya lo está (sección 3, HU-3).

Cambios que implica en `HU-6.py` (pendientes):
- Quitar el `DROP TABLE`.
- Añadir una columna de fecha (propuesta: `fecha_carga`) y rellenarla al insertar.
- Cambiar la clave primaria: ahora es `nregistro`, que impediría insertar el mismo medicamento otro día. Propuesta: `cn` + `fecha_carga` (en el CSV actual hay 827 `cn` distintos en 827 filas, no se repiten).
- Revisar la vista de KPIs: los cálculos con `PARTITION BY` mezclarían las cargas de todos los días si no tienen en cuenta la fecha.
- Decidir qué pasa si se ejecuta dos veces el mismo día (daría error por clave repetida). Propuesta sin confirmar con el profesor: borrar antes las filas de la fecha de hoy.

---

## 6. Estado y pendientes

**Hecho:** HU-1 a HU-6 terminadas y entregadas (Sprint H1-H3, Sprint H4-H5, Sprint H6). Los cuatro scripts definitivos están en el repo.

**Pendiente de la HU-7:**
1. Crear `src/JAA_diabetes.py` a partir del código del profesor, con el log con fecha.
2. Probarlo primero con un solo script rápido (`HU-5.py`) y después con los cuatro.
3. Provocar un error a propósito para comprobar que el log lo registra y el flujo se para.
4. Cambiar `HU-6.py` a carga incremental (sección 5).
5. Crear la variable de entorno `MYSQL_PASSWORD` en cada ordenador.
6. Programar la ejecución (Crontab en Mac, Programador de Tareas en Windows). La frecuencia no la fija el enunciado.
7. Documento de entrega con capturas de la ejecución, el log y la tarea programada.

**Puntos a vigilar (no comprobados):**
- `HU-4.py` usa diccionarios escritos a mano (correcciones de dosis por `nregistro`, grupos de forma farmacéutica y de vía de administración). Si una ejecución nueva trae un medicamento o una categoría que no está en esos diccionarios, puede aparecer un nulo o fallar un paso. Hay que mirarlo cuando se ejecute el flujo completo con datos nuevos.
- El número de filas y los perfiles de K-Means pueden cambiar si cambian los datos de origen; los nombres de los perfiles en `HU-5.py` están asignados a mano a cada número de grupo.
- No se ha ejecutado todavía el flujo completo con los cuatro scripts nuevos.

---

## 7. Entregas

- Plantilla oficial en `enunciado/` (portada, Introducción, Metodología, Resultados, Conclusión). En Resultados son obligatorios los **pantallazos de la ejecución** (código y terminal con la salida).
- Antes de capturar: ejecutar con los `print` de comprobación activos y revisar los pies de foto.
- Que la HU-7 se entregue con la misma plantilla no está confirmado.

## 8. Git: normas del equipo

- `git pull` antes de empezar a trabajar y antes de subir.
- Añadir los archivos por su nombre (`git add src/archivo.py`), no con `git add .` ni `git add -A`.
- Secuencia: `git add <archivos>` → `git status` → `git commit -m "mensaje"` → `git push`.
- No se sube `.venv`, `__pycache__` ni `.DS_Store` (están en `.gitignore`).
