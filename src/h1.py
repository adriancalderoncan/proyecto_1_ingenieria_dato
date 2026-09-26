import requests
import json
import pandas as pd

url_1 = "https://cima.aemps.es/cima/rest/buscarEnFichaTecnica?pagina="
url_2 = "https://cima.aemps.es/cima/rest/medicamento?nregistro="

payload = json.dumps([
  {
    "seccion": "4.1",
    "texto": "diabetes",
    "contiene": 1
  }
])
headers = {
  'Content-Type': 'application/json'
}

medicamentos = []

for i in range(1, 9):
    print("Obteniendo medicamentos de la página: ", i)
    response = requests.request("POST", url_1 + str(i), headers=headers, data=payload)
    pagina_medicamentos = json.loads(response.text)
    medicamentos.extend(pagina_medicamentos.get('resultados', []))

nregistros = []
for dat in medicamentos:
    nregistro = dat.get('nregistro')
    nregistros.append(nregistro)

print("Números de registro obtenidos: ", len(nregistros))

infomedslis = []

for i in nregistros:
    url = url_2 + i
    response = requests.request("GET", url, timeout=60)
    infomeds = json.loads(response.text)
    infomedslis.append(infomeds)


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