from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import json
import scipy
import pygeoj
import mgrs
import numpy as np
import datetime
from dateutil import parser
import requests
import rasterio
import rasterio.tools
import rasterio.mask
import rasterio.warp
import tempfile
import shutil
import shapely.geometry
import shapely.affinity
from affine import Affine

BASE_URL = ['https://sentinel-s2-l1c.s3.amazonaws.com', 'tiles']

@csrf_exempt
def image_view(request):
    data = json.loads(request.body.decode('utf-8'))
    geojson = data['area']
    loaded_geojson = pygeoj.load(data=geojson)
    geometry = loaded_geojson[0].geometry
    # print(geojson)
    coordinates = geometry.coordinates[0]

    # print(loaded_geojson.crs)
    # print(loaded_geojson.crs.name)
    # print(geo_shape.bounds)

    if 'features' in geojson:
        geometries = [f['geometry'] for f in geojson['features']]
    elif 'geometry' in geojson:
        geometries = (geojson['geometry'], )

    tiles = []

    for coordinate in coordinates:
        exact_tile = mgrs.MGRS().toMGRS(coordinate[1], coordinate[0]).decode('ascii')
        tiles.append(exact_tile[0:5])

    if len(np.unique(tiles)) != 1:
        return JsonResponse({
            'error': 'not_supported',
            'message': 'Not supported: Shapefile spans multiple MGRS tiles',
        }, safe=False)

    tile = tiles[0]

    utm_code = tile[0:2]
    latitude_band = tile[2:3]
    square = tile[3:5]

    TILE_PART = [utm_code, latitude_band, square]
    DATE_PART = ['{dt.year}/{dt.month}/{dt.day}'.format(dt = parser.parse(data['date']))]
    TAKE_PART = [data['take']]
    BAND_PART = ['B' + data['band'] + '.jp2']

    url = '/'.join(np.concatenate((BASE_URL, TILE_PART, DATE_PART, TAKE_PART, BAND_PART)))
    print(url)

    with rasterio.open(url) as raster_file:
        shape = geojson['features'][0]['geometry']
        transformed_geojson = rasterio.warp.transform_geom('epsg:4326', raster_file.crs, shape)
        out_image, out_transform = rasterio.mask.mask(raster_file, [transformed_geojson], crop=True)

    return JsonResponse({
        'success': True,
    }, safe=False)
