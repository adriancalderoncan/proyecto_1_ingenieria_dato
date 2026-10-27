import requests
import json
import pandas as pd

url_1 = "https://cima.aemps.es/cima/rest/buscarEnFichaTecnica?pagina="    #POST
url_2 = "https://cima.aemps.es/cima/rest/medicamento?nregistro="          #GET

payload = json.dumps([
  {
    "seccion": "4.1",
    "texto": "diabetes",
    "contiene": 1
  }
])
"""¿Qué hace json.dumps?(dumps = dump string)

Convierte un objeto de Python (lista, diccionario...) en un texto (string) en formato JSON.
Lo necesitas porque, cuando envías una petición por internet, no viaja un “objeto de Python”. Viaja texto, y el servidor,
que puede estar programado en cualquier lenguaje, solo entiende ese texto estándar. JSON es ese formato común."""
headers = {
  'Content-Type': 'application/json'
}

medicamentos = []

for i in range(1, 9):
    print("Obteniendo medicamentos de la página: ", i)
    response = requests.request("POST", url_1 + str(i), headers=headers, data=payload)
    #es lo mismo request.request("POST",url...) que request.post(url_1 +str(i),...)
    pagina_medicamentos = json.loads(response.text)
    medicamentos.extend(pagina_medicamentos.get('resultados', []))

"""response es un objeto que guarda todo lo que contestó el servidor. No es solo el texto. Tiene varias partes, y las que nos
importan son estas:

response
 ├── .status_code   →  200            (número: 200 = todo OK)
 ├── .headers       →  {...}          (cabeceras de la respuesta)
 └── .text          →  '{"pagina":1, "resultados":[...]}'   ← un STRING

Lo importante: response.text es un texto, aunque parezca un diccionario. No puedes hacer response.text['resultados'],
porque para Python es una cadena de caracteres, no una estructura con claves

json.loads: pasar de texto a algo manejable
response.text  (STRING)                      pagina_medicamentos  (DICCIONARIO)
───────────────────────────                  ─────────────────────────────────
'{"pagina": 1,                               {
  "resultados": [                              "pagina": 1,
     {"nregistro": "A1"},        json.loads    "resultados": [
     {"nregistro": "B2"}    ──────────────►       {"nregistro": "A1"},
  ]}'                                             {"nregistro": "B2"}
                                                ]
                                               }
Antes de loads es texto y después es un diccionario de Python, con sus claves y su lista dentro.                          
"""   

nregistros = []
for dat in medicamentos:
    nregistro = dat.get('nregistro')
    nregistros.append(nregistro)

print("Números de registro obtenidos: ", len(nregistros))

infomedslis = []

for i in nregistros:
    url = url_2 + i
    try:
      response = requests.request("GET", url, timeout=60)
      infomeds = json.loads(response.text)
      infomedslis.append(infomeds)
    except Exception as e:
        print(f"Error al obtener el medicamento {i}")
"""
-infomeds: response.text es un string y json.loads lo convierte en un diccionario. 
Esta vez el diccionario es la ficha completa de un solo medicamento

-infomedslis es una lista plana donde cada elemento es el diccionario completo de un medicamento distinto
ejemplo:
 infomedslis = [
    {"nregistro": "51347", "nombre": "MEDICAMENTO UNO 500 mg", ...},
    {"nregistro": "62001", "nombre": "MEDICAMENTO DOS 10 mg", ...},
]
"""

"""
En cada vuelta, med es el diccionario completo de un medicamento. Este es el de ejemplo:
med = {
    "nregistro": "51347",
    "nombre": "MEDICAMENTO UNO 500 mg",
    "pactivos": "METFORMINA",
    "labtitular": "LAB UNO",
    "labcomercializador": "LAB UNO",
    "dosis": "500 mg",
    "presentaciones": [{"cn": "654321"}, {"cn": "654322"}],
    "formaFarmaceuticaSimplificada": {"id": 1, "nombre": "Comprimido"},
    "estado": {"aut": 1100000000000, "rev": 1700000000000},
    "comerc": True, "receta": True, "generico": False,
    "conduc": False, "triangulo": False, "huerfano": False, "biosimilar": False,
    "docs": [
        {"tipo": 1, "url": "a.pdf", "urlHtml": "a.html"},
        {"tipo": 2, "url": "b.pdf", "urlHtml": "b.html"},
    ],
    "fotos": [{"tipo": "materialas", "url": "foto.jpg"}],
    "atcs": [{"codigo": "A10BA02"}],
    "principiosActivos": [{"nombre": "METFORMINA"}],
    "excipientes": [{"nombre": "ESTEARATO"}, {"nombre": "POVIDONA"}],
    "viasAdministracion": [{"id": 48, "nombre": "VIA ORAL"}],
}"""
filas = []
for med in infomedslis:
    # el codigo nacional se coge de la primera presentacion
    presentaciones = med.get('presentaciones', [])
    if len(presentaciones) > 0:
        cn = presentaciones[0].get('cn')
    else:
        cn = None

    forma = med.get('formaFarmaceuticaSimplificada')
    if forma:
        forma_farmaceutica_simplificada = forma.get('nombre')
    else:
        forma_farmaceutica_simplificada = None

    estado = med.get('estado', {})
    estado_aut = estado.get('aut')
    estado_rev = estado.get('rev')

    # en docs el tipo 1 es la ficha tecnica, urlHtml es la version html (url es el pdf)
    url_ficha = None
    for doc in med.get('docs', []):
        if doc.get('tipo') == 1 and doc.get('urlHtml', '').endswith('.html'):
            url_ficha = doc.get('urlHtml')

    url_foto = None
    for foto in med.get('fotos', []):
        if 'material' in foto.get('tipo', '') and foto.get('url', '').endswith('.jpg'):
            url_foto = foto.get('url')

    vias = []
    for via in med.get('viasAdministracion', []):
        vias.append(via.get('nombre'))

    fila = {
        'nregistro': med.get('nregistro'),
        'nombre': med.get('nombre'),
        'pactivos': med.get('pactivos'),
        'labtitular': med.get('labtitular'),
        'labcomercializador': med.get('labcomercializador'),
        'cn': cn,
        'dosis': med.get('dosis'),
        'forma_farmaceutica_simplificada': forma_farmaceutica_simplificada,
        'estado_aut': estado_aut,
        'estado_rev': estado_rev,
        'comercializado': int(med.get('comerc', False)),
        'requiere_receta': int(med.get('receta', False)),
        'generico': int(med.get('generico', False)),
        'afecta_conduccion': int(med.get('conduc', False)),
        'triangulo_negro': int(med.get('triangulo', False)),
        'medicamento_huerfano': int(med.get('huerfano', False)),
        'biosimilar': int(med.get('biosimilar', False)),
        'url_html_ficha_tecnica': url_ficha,
        'url_foto_materiales': url_foto,
        'num_registros_atc': len(med.get('atcs', [])),
        'num_principios_activos': len(med.get('principiosActivos', [])),
        'num_excipientes': len(med.get('excipientes', [])),
        'vias_administracion': ", ".join(vias)
    }
    filas.append(fila)

df = pd.DataFrame(filas)
print(df.shape)

df.to_excel("data/HU1_medicamentos_diabetes.xlsx", index=False)
print("Dataset guardado")