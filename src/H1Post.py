import requests
import json

url_1= "https://cima.aemps.es/cima/rest/buscarEnFichaTecnica?pagina="

payload = json.dumps([
  {
    "seccion": "4.1",
    "texto": "diabetes",
    "contiene": 1
  }
])
headers = {
  'Cookie': 'JSESSIONID=SCfKUNr_04QO-eW2ONxhtMYjEpReBvxAt-jWgt5EP8TYj88jAn2l!-1454815942',
  'Content-Type': 'application/json'
}

medicamentos = []
nregistros = []

for i in range(1, 9):
    print("Obteniendo medicamentos de la página: ", i)
    response = requests.request("POST", url_1 + str(i), headers=headers, data=payload)
    pagina_medicamentos = json.loads(response.text)
    medicamentos.append(pagina_medicamentos)


for dat in medicamentos:
    for x in dat['resultados']:
        print(x)
    #nregistro = dat['nregistro']
    #nregistros.append(nregistro)
    #print(nregistro)
    #print(nregistros)

print(dat)

infomedslis = []
url_2 = "https://cima.aemps.es/cima/rest/medicamento?nregistro="
#url = "https://cima.aemps.es/cima/rest/medicamento"


for i in nregistros:
    url = url_2 + i
    payload = {}
    headers = {
    'Cookie': 'JSESSIONID=SCfKUNr_04QO-eW2ONxhtMYjEpReBvxAt-jWgt5EP8TYj88jAn2l!-1454815942'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    infomeds = json.loads(response.text)
    infomedslis.append(infomeds)