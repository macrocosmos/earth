from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

import json
import scipy
import pygeoj
import mgrs
import numpy as np
from dateutil import parser
import requests
import rasterio
import rasterio.tools
import rasterio.mask
import rasterio.warp
import rasterio.merge

BASE_URL = ['https://sentinel-s2-l1c.s3.amazonaws.com']
REQUEST_URL = BASE_URL.append('tiles')
QUERY_URL = BASE_URL.appen('#tiles')

@csrf_exempt
def image_view(request):
    data = json.loads(request.body.decode('utf-8'))
    geojson = data['area']
    loaded_geojson = pygeoj.load(data=geojson)
    geometry = loaded_geojson[0].geometry
    coordinates = geometry.coordinates[0]

    if 'features' in geojson:
        geometries = [f['geometry'] for f in geojson['features']]
    elif 'geometry' in geojson:
        geometries = (geojson['geometry'], )

    tiles = []

    for coordinate in coordinates:
        exact_tile = mgrs.MGRS().toMGRS(coordinate[1], coordinate[0]).decode('ascii')
        tiles.append(exact_tile[0:5])

    raster_files = []
    for tile in tiles:
        utm_code = tile[0:2]
        latitude_band = tile[2:3]
        square = tile[3:5]

        TILE_PART = [utm_code, latitude_band, square]
        DATE_PART = ['{dt.year}/{dt.month}/{dt.day}'.format(dt = parser.parse(data['date']))]
        TAKE_PART = [data['take']]
        BAND_PART = ['B' + data['band'] + '.jp2']

        url = '/'.join(np.concatenate((REQUEST_URL, TILE_PART, DATE_PART, TAKE_PART, BAND_PART)))
        print('Requesting:', url)

        with rasterio.open(url) as raster_file:
            raster_files.append(raster_file)

    raster_file = rasterio.merge(raster_files)

    shape = geojson['features'][0]['geometry']
    transformed_geojson = rasterio.warp.transform_geom('epsg:4326', raster_file.crs, shape)
    out_image, out_transform = rasterio.mask.mask(raster_file, [transformed_geojson], crop=True)

    out_meta = raster_file.meta.copy()

    out_meta.update({
        'driver': 'JP2OpenJPEG',
         'height': out_image.shape[1],
         'width': out_image.shape[2],
         'transform': out_transform,
     })

    with rasterio.open('out.jp2', 'w', **out_meta) as dest:
        dest.write(out_image)

    fsock = open('out.jp2', 'rb')
    response = HttpResponse(fsock, content_type='image/jp2')
    return response
