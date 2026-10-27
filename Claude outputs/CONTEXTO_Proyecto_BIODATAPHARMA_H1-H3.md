# Contexto para continuar con H4 y H5 — Proyecto BIODATAPHARMA (grupo JAA)

> Documento de traspaso. Resume todo lo hecho en el chat anterior (H1, H2, H3, documento de entrega y repo) y cómo quiere Alberto que se trabaje. **Léelo entero antes de empezar.**

---

## 0. Cómo debes trabajar con Alberto (MUY IMPORTANTE)

Alberto cursa el Máster Universitario en Inteligencia Artificial Aplicada (ICAI, Comillas). Quiere un **tutor técnico y académico**, no un generador de soluciones. Preferencias explícitas (reafirmadas muchas veces):

- **Nunca le des el código terminado sin más.** Quiere entender qué hace cada línea y por qué, para poder explicarlo después.
- Avanza **paso a paso ("poco a poco")**, confirmando que entiende cada paso. Explica conceptos de forma clara, sencilla y progresiva.
- **No añadas complejidad innecesaria** (ni librerías, ni arquitecturas más avanzadas de lo que pida el ejercicio). Código simple, legible, al nivel visto en clase.
- **Prioriza siempre el enunciado y el material del profesor.** No inventes requisitos de entrega. Si algo no aparece en el material, dilo claramente en vez de asumirlo.
- **Ayúdale a detectar errores y entender su causa antes de darle la solución.**
- Si hay varias alternativas, explica brevemente las diferencias y recomienda la más adecuada para el contexto académico.
- Distingue claramente entre teoría, ejemplo didáctico y código que se usa de verdad en la entrega.
- Sé eficiente con los créditos/tokens.
- Se frustra (con razón) cuando le das comandos sueltos sin explicación o respuestas vagas, o cuando le haces esperar. Cuando tiene poco tiempo, sé directo y decisivo: decide tú y dile qué hacer, sin pedirle que piense lo que no hace falta.
- Escribe en español, tono cercano. Él escribe informal.
- En el documento de entrega quería **lenguaje sencillo, parecido al suyo**, "que parezca escrito por mí".

**Qué NO está en este contexto:** el enunciado de H4 y H5. No sé qué piden. Pídele que te pase el enunciado (o léelo del proyecto de Claude "Ingeniería del dato", que tiene PDFs, entre ellos `4. Loading data .pdf` y `3_Transformation_Session_1.pdf`, que probablemente tengan relación con las siguientes HU, pero **no lo he comprobado**). No asumas qué piden.

---

## 1. Entorno técnico de Alberto

- **macOS**, MacBook Air 13" Apple M5 (arm64), 16 GB RAM. Descarga versiones ARM.
- **VS Code** (terminal integrada zsh + notebooks de Jupyter dentro de VS Code). Tiene la extensión de Claude Code.
- **Python 3.10** en entorno virtual `.venv` dentro del proyecto (usa **uv** en vez de conda, aunque la guía oficial del máster recomienda conda). El prompt muestra `(proyecto_1_ingenieria_dato)` cuando el venv está activo; si una terminal nueva no lo muestra: `source .venv/bin/activate`.
- Librerías: pandas, requests, BeautifulSoup (bs4), openpyxl, xlrd (para `.xls` antiguo).
- **Git/GitHub** con repo de equipo.
- Ruta del proyecto en su Mac: `/Users/albertorey/dev/proyecto_1_ingenieria_dato` (`~/dev/proyecto_1_ingenieria_dato`).
- Repo remoto: https://github.com/adriancalderoncan/proyecto_1_ingenieria_dato (rama `main`).
- Equipo (grupo **JAA**): Alberto Rey (de la Fe), Adrián Calderón, Jorge Montoyo. Enfermedad asignada: **diabetes**.
- Asignatura: Ingeniería del Dato (el proyecto es el sistema **BIODATAPHARMA**: recolección y análisis de datos de medicamentos por enfermedad).

### Estructura del repo

```
proyecto_1_ingenieria_dato/
├── .venv/                (no se versiona)
├── data/
│   ├── HU1_medicamentos_diabetes.xlsx   (1569 filas, 23 cols)
│   ├── HU2_medicamentos_diabetes.xlsx   (1569 filas, 26 cols)
│   ├── HU3_medicamentos_diabetes.xlsx   (1569 filas, 32 cols)
│   └── nomenclator.xls                  (descarga del Ministerio, regenerable)
├── documentacion_api/
├── enunciado/
├── src/
│   ├── h1.py
│   ├── h2webscraping.py
│   ├── h3.py
│   ├── pruebah1.ipynb
│   ├── pruebah2.ipynb
│   └── pruebah3.ipynb
├── .gitignore
├── README.md
└── requirements.txt
```

Último commit empujado: `2b701b1` "Actualiza datos y notebooks de H1-H3, elimina scripts obsoletos". Se borraron `src/H1Post.py` y `src/nomenclator.py` (código muerto), y se eliminaron duplicados de pruebas (`*_alberto.*`) y una carpeta `Claude outputs/` que no pertenecía al proyecto. El árbol quedó limpio y sincronizado con `origin/main`.

---

## 2. Concepto clave que se repite: rutas relativas

Fuente recurrente de errores. Las rutas relativas dependen del **directorio de trabajo (cwd)**, no de dónde esté el `.py`:

- **Scripts** (`python3 src/h1.py`, lanzados **desde la raíz del proyecto**): usan `"data/..."`. El cwd es la raíz aunque el script esté en `src/`.
- **Notebooks** (en `src/`): el cwd es `src/`, así que usan `"../data/..."`.
- Para ejecutar un script hay que indicar la ruta hasta él (`python3 src/h1.py`); si no, Python dice "No such file or directory" (eso es sobre dónde está el `.py`, no sobre las rutas internas).

---

## 3. Qué se hizo en cada HU

### HU-1 — Extracción desde la API de CIMA (`src/h1.py`)
- Endpoint POST `https://cima.aemps.es/cima/rest/buscarEnFichaTecnica?pagina=N` con payload JSON `[{"seccion": "4.1", "texto": "diabetes", "contiene": 1}]`, páginas 1–8 → lista de medicamentos (`resultados`).
- Se extraen los `nregistro` y, por cada uno, GET `https://cima.aemps.es/cima/rest/medicamento?nregistro=<n>` → JSON completo con `timeout=60` y `try/except`.
- Se construye una fila por medicamento con 23 columnas: `nregistro, nombre, pactivos, labtitular, labcomercializador, cn, dosis, forma_farmaceutica_simplificada, estado_aut, estado_rev, comercializado, requiere_receta, generico, afecta_conduccion, triangulo_negro, medicamento_huerfano, biosimilar, url_html_ficha_tecnica, url_foto_materiales, num_registros_atc, num_principios_activos, num_excipientes, vias_administracion`.
- `cn` (Código Nacional) se coge de la primera presentación. Los booleanos se pasan a int (0/1).
- Resultado: `Números de registro obtenidos: 1569`, `(1569, 23)`, guarda `data/HU1_medicamentos_diabetes.xlsx`.

### HU-2 — Web scraping de fichas técnicas (`src/h2webscraping.py`)
Lee el Excel de HU-1, y para cada fila hace `requests.get(url_html_ficha_tecnica, timeout=30)` + `BeautifulSoup(response.text, "html.parser")`. Añade 3 columnas:
1. `palabras_seccion_4_4`: `find(id="4.4")` → `.find_next_sibling()` (el texto está en el `<div>` hermano del `<h2>`) → `.get_text(" ", strip=True)` → `len(texto.split())`. Si no hay sección 4.4, `None.find_next_sibling()` da `AttributeError`, que se captura con `try/except` y se guarda `"no tiene sección 4.4"` (ocurre en 3 medicamentos: 360, 361, 362).
2. `numero_tablas`: `len(html.find_all("table"))`.
3. `indicador_riesgo_severo`: cuenta las palabras "grave"/"graves" en todo el texto (minúsculas, quitando puntuación `.,;:()`).
- Guarda `data/HU2_medicamentos_diabetes.xlsx` (26 cols).
- **Ojo:** tarda **muchos minutos** (1569 peticiones HTTP reales, secuenciales). Durante el bucle solo imprime en el `except`, así que parece colgado pero no lo está. Se aprendió esto en el chat.
- Un bug corregido antes: `numero_tablas` salía igual en todos los medicamentos (se verificó con `value_counts()` que ya no).

### HU-3 — Enriquecer con datos económicos del Ministerio de Sanidad (`src/h3.py`)
Versión de Alberto (la que quedó como `h3.py` en el repo, según la captura de VS Code; **verifícalo con `git log`/`cat` si te importa**):

```python
import pandas as pd
import requests

url = "https://www.sanidad.gob.es/profesionales/nomenclator.do?metodo=nomenclatorExcel"
response = requests.get(url)
with open("data/nomenclator.xls", "wb") as archivo:
    archivo.write(response.content)          # content = bytes (text sería para texto)

df_precios = pd.read_excel("data/nomenclator.xls")
df_hu2 = pd.read_excel("data/HU2_medicamentos_diabetes.xlsx")

df_precios_columnas_añadir = df_precios[["Código Nacional", "Estado",
    "Precio de venta al público con IVA", "Precio de referencia",
    "Tratamiento de larga duración", "Especial control médico"]]   # doble corchete = DataFrame
df_precios_columnas_añadir["Código Nacional"] = df_precios_columnas_añadir["Código Nacional"].astype("float64")

df_hu3 = df_hu2.merge(df_precios_columnas_añadir, left_on="cn", right_on="Código Nacional", how="left")
df_hu3.to_excel("data/HU3_medicamentos_diabetes.xlsx", index=False)
```

- Resultado: `(1569, 32)`. 6 columnas nuevas (incluye `Código Nacional` duplicando a `cn`). **Alberto decidió usar SU versión (32 cols) en vez de la de Adrián (31 cols, que hace `df.drop(columns=["Código Nacional"])`).** Ambas dan exactamente los mismos matches; el documento de entrega dice 32.
- **Problema del tipo de dato (clave didáctica):** `cn` en HU2 es `float64` (p. ej. `662260.0`) porque una sola celda vacía (1 NaN) obliga a pandas a pasar toda la columna a float (int64 no admite NaN), mientras que `Código Nacional` del nomenclátor es `int64` (`140001`). Un merge entre tipos distintos falla en silencio. Solución: igualar tipos antes (Alberto convierte a float64; Adrián convierte ambos a `str`, que también funciona — se verificó empíricamente).
- `SettingWithCopyWarning` al asignar sobre el recorte: es benigno aquí.
- **742 de 1569 (47%) sin datos económicos** (`Estado` NaN). Investigación: `df_hu2["comercializado"].value_counts()` → 790 no comercializados / 779 comercializados; `pd.crosstab(df_hu2["comercializado"], df_hu3["Estado"].isna())`:
  - no comercializados: 158 con dato / **632** sin dato
  - comercializados: 669 con dato / **110** sin dato
  - Conclusión: la mayoría (632) se explica porque el nomenclátor solo lista medicamentos que se financian/facturan; quedan **110 comercializados sin match que NO se han podido explicar del todo** (hipótesis: diferencias de fecha entre fuentes, o un medicamento con varios Códigos Nacionales — el script solo usa el `cn` de la primera presentación). Está comunicado así en el documento: no era un bug, pero sí un punto abierto.
- El nomenclátor real tiene 20 columnas (`Código Nacional, Nombre del producto farmacéutico, Tipo de fármaco, …, Estado, Fecha de alta/baja, …, Precio de venta al público con IVA, Precio de referencia, …, Tratamiento de larga duración, Especial control médico, Medicamento huérfano`) y ~20547 filas. Para `.xls` antiguo puede hacer falta `engine="xlrd"`.

---

## 4. Documento de entrega (Moodle)

- Plantilla oficial: `Plantilla_Entregas_Sprints_MUIAAP.docx` con portada (Sprint / Grupo / asignatura / máster), Índice y 4 secciones, cada una con guía literal:
  - **Introducción:** Contexto / Descripción del problema y objetivos del sprint / Justificación
  - **Metodología:** Descripción del entorno de desarrollo (herramientas) / Diseño de la solución / Pruebas realizadas
  - **Resultados:** Descripción de los resultados / **Pantallazos de la ejecución (IMPORTANTE, en rojo)** — capturas de la ejecución en terminal o entorno de pruebas / Discusión de los resultados
  - **Conclusión:** Resumen del proceso / Principales logros
- Lo rellenamos cubriendo **todos** los sub-puntos literalmente. Alberto lo maquetó y entregó él mismo (Sprint 1, grupo JAA, H1–H3), nombre del fichero `AlbertoReydelaFe_JAA_H1_3` (el formato exacto del nombre no consta en la plantilla; viene de las instrucciones de Moodle, que no he visto).
- Lecciones del documento:
  - Las capturas de ejecución deben mostrar **código + terminal con la salida** (no solo tablas sueltas). Lo que se incluyó: ejecución de `h1.py` (progreso de páginas 1–8, `1569`, `(1569, 23)`, "Dataset guardado"), de `h2webscraping.py` (mensajes "no tiene sección 4.4" y "Dataset del HU2 guardado") y de `h3.py`. Las pruebas en notebook (dtype float64 vs int64, crosstab, `(1569, 32)`) van en Metodología → Pruebas realizadas.
  - Errores de última hora detectados: un pie de foto del H3 decía "h2.py" por copiar y pegar, y en la captura del H3 el `print(df_hu3.shape)` seguía comentado, así que no mostraba el resultado del merge. **Para H4/H5: ejecutar el script con prints de verificación activos antes de capturar, y revisar los pies de foto.**
  - Para editar un `.docx` existente la técnica fue desempaquetar el zip, editar `word/document.xml` y reempaquetar (orden estricto de elementos en `<w:pPr>`: `keepNext` → `spacing` → `jc` → `rPr`; evitar `<w:rPr>` anidados; imágenes en `word/media/` + relación en `document.xml.rels` + bloque `<w:drawing>`), validar con `validate.py` y revisar visualmente pasando a PDF. Si Alberto vuelve a pedir esto, mejor que edite él mismo en Word las cosas pequeñas.

---

## 5. Git: lecciones del flujo de trabajo

- **Haced `git pull` antes de empezar a trabajar** y antes de subir, para no pisar el trabajo de Adrián/Jorge.
- Error "los siguientes archivos sin seguimiento serían sobrescritos al fusionar": se resuelve renombrando (`mv`) tus ficheros locales antes del pull.
- No usar `git add -A` ni `git add .` (arrastra basura: `.venv`, `.DS_Store`, carpetas de otras herramientas). Añadir ficheros por nombre.
- Los borrados se confirman haciendo `git add <ruta del borrado>`.
- No se versiona `.venv`, `__pycache__`, `.DS_Store`; ni ficheros externos regenerables salvo que el enunciado los pida.
- Secuencia usada: `git add <ficheros>` → `git status` → `git commit -m "..."` → `git push`.

---

## 6. Otras lecciones técnicas a recordar (nivel pandas/Python)

- `response.text` (texto) vs `response.content` (bytes); `open(ruta, "wb")` para escribir binario.
- `df[["a","b"]]` devuelve DataFrame; `df["a"]` devuelve Serie.
- `.isna().sum()` suma los True; `.value_counts()`, `pd.crosstab()` para cruzar dos variables.
- `df.merge(otro, left_on=, right_on=, how="left")` = BUSCARV de Excel; `how="left"` conserva todas las filas de la izquierda.
- `.shape` → (filas, columnas): comprobarlo tras **cada** operación para no perder ni duplicar filas.
- Revisar `dtype` de las columnas clave **antes** de cruzar.
- `try/except AttributeError` para fichas sin la sección esperada.

---

## 7. Enunciado de HU-4 y HU-5 (fuente: `Historias Usuario_HU4_HU5.pdf`, el PDF oficial)

> El PDF original manda: pídele a Alberto que lo adjunte también. Aquí va el resumen fiel de lo que pone, sin añadir nada.

### HU-4 — EDA y limpieza
Alberto/consultoras deben:
- Usar el conjunto de datos consolidado hasta ahora (API CIMA + métricas de fichas técnicas + precios del Nomenclátor), es decir, el resultado de HU-3.
- Hacer un **Análisis Exploratorio de Datos (EDA)** con **gráficas y visualizaciones claras** para entender distribuciones y el comportamiento general de las variables.
- Hacer una **limpieza básica**: tratar valores nulos, corregir tipos de datos y revisar valores atípicos o anomalías evidentes, para dejar el dataset preparado.
- Hacer un **reporte final** con las conclusiones principales y las gráficas más importantes.
- Documentación adicional que cita el enunciado (GeeksforGeeks: EDA en Python; Towards Data Science: EDA con Python; GeeksforGeeks: detectar y eliminar outliers; GeeksforGeeks: convertir datos categóricos string a numéricos).
- **Entregable ("Para"):** un **fichero CSV** con los datos limpios y preparados para la siguiente etapa.

### HU-5 — Clustering K-Means
- Cargar el **CSV limpio de HU-4** en Python y preparar las columnas numéricas que se vayan a usar.
- Desarrollar un modelo **K-Means con scikit-learn**.
- **Analizar y poner nombre a los clústeres** resultantes: qué perfiles/tipologías de medicamentos agrupa cada grupo.
- Documentación adicional: tutorial de K-Means de DataCamp.
- **Entregable ("Para"):** un **CSV** con los datos limpios **más una nueva columna con el clúster asignado por el modelo**.

### Lo que el enunciado NO dice (no lo inventes, pregúntale a Alberto o al profesor)
- Formato del reporte final de HU-4 (¿notebook? ¿PDF? ¿documento con la plantilla de sprint?).
- Cuántos clústeres (k) usar ni qué columnas concretas; cómo elegir k (codo, silueta…) no está especificado en el PDF.
- Si la entrega será otro sprint con la misma plantilla (probable `..._H4_5`, **no confirmado**) ni fechas.
- Nombres de los ficheros de salida CSV.

---

## 8. Observaciones del trabajo anterior que probablemente afecten a HU-4 y HU-5

> Son deducciones mías a partir del código y los resultados de H1–H3, **no requisitos del enunciado**. Verificarlas cargando el Excel.

- **Nulos en las columnas económicas:** 742 de 1569 filas no tienen datos del nomenclátor (`Estado`, precios, `Tratamiento de larga duración`, `Especial control médico` salen NaN). Decidir cómo tratarlos (imputar, dejar, filtrar) es una decisión de HU-4 que hay que justificar; ojo con que 632 son medicamentos no comercializados y 110 comercializados sin explicación completa.
- **`cn` es float64** (por 1 NaN) y existe una **columna duplicada `Código Nacional`** (en la versión de 32 columnas). Candidatas a limpieza.
- **`palabras_seccion_4_4` mezcla números y texto:** 3 medicamentos tienen el string `"no tiene sección 4.4"` en vez de un número, así que la columna es de tipo texto (`object`). Hay que decidir qué hacer con esas filas antes de analizar o hacer K-Means.
- **Fechas:** `estado_aut` y `estado_rev` son fechas (formato a revisar al cargar); `estado_rev` puede tener nulos.
- **Variables binarias 0/1** (`comercializado`, `requiere_receta`, `generico`, `afecta_conduccion`, `triangulo_negro`, `medicamento_huerfano`, `biosimilar`) y **conteos** (`num_registros_atc`, `num_principios_activos`, `num_excipientes`, `numero_tablas`, `indicador_riesgo_severo`, `palabras_seccion_4_4`) son los candidatos naturales a columnas numéricas para K-Means; las categóricas de texto (`nombre`, `pactivos`, `labtitular`, `forma_farmaceutica_simplificada`, `vias_administracion`) requerirían conversión (el enunciado de HU-4 sugiere el tema "convertir categóricas a numéricas"). K-Means es sensible a la escala: probablemente haya que escalar, pero eso es algo a explicar y confirmar con el material de clase.
- **Filas casi duplicadas:** en `pruebah2.ipynb` se ve que varios medicamentos consecutivos comparten exactamente los mismos valores (p. ej. misma ficha técnica para distintas dosis: 149/1/2 repetido), lo cual es esperable porque comparten ficha, pero conviene tenerlo en cuenta en el EDA.
- **Limitación conocida de HU-1:** el enunciado dice usar `totalFilas` para saber cuántas páginas hay que pedir; el script de Alberto usa `range(1, 9)` fijo (8 páginas), que dio los 1569 registros esperados. Funciona, pero está "a mano". Si surge en revisión, es un punto mejorable (no es parte de H4/H5).
- Los materiales del proyecto de Claude "Ingeniería del dato" incluyen `3_Transformation_Session_1.pdf`, `3_1_EDA_Technical_Transformation_Clinical_Trial_Lab.pdf` y `4. Loading data .pdf`: **son la fuente de clase que hay que priorizar** para HU-4 y HU-5 (no los he leído en detalle en este chat).

---

## 9. Estado actual y siguiente paso

- **H1, H2, H3: completadas, verificadas, entregadas y empujadas al repo.**
- **Pendiente: H4 y H5** (enunciado en la sección 7).
- Dato de partida: `data/HU3_medicamentos_diabetes.xlsx` (1569 filas × 32 columnas) — es el "conjunto consolidado hasta el momento" del enunciado de HU-4.
- Primer paso sugerido en el nuevo chat: (1) `git pull`, (2) leer el material de clase sobre EDA/transformación en el proyecto de Claude, (3) cargar el Excel y mirar `.info()`, `.isna().sum()`, `.describe()` **explicándole a Alberto qué muestra cada cosa**, (4) decidir el plan paso a paso con él, siguiendo el estilo de tutor de la sección 0. Para las gráficas, mantenerlo simple (matplotlib/seaborn si se ven en clase; no añadir librerías no vistas).
