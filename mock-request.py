import json
import requests

API_ENDPOINT = 'http://0.0.0.0:8000/api/v1/images/'
SHAPEFILE = './raseiniai.geojson'

data = {
    'area': json.loads(open(SHAPEFILE).read()),
    'date': '2017-8-21',
    'take': '0',
    'band': '08',
}

request = requests.post(url = API_ENDPOINT, data = json.dumps(data))
print(request.text)
