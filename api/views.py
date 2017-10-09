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
import tempfile
import shutil

BASE_URL = ['https://sentinel-s2-l1c.s3.amazonaws.com', 'tiles']

@csrf_exempt
def image_view(request):
    data = json.loads(request.body.decode('utf-8'))
    geometry = pygeoj.load(data=data['area'])[0].geometry
    coordinates = geometry.coordinates[0]

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

    response = requests.get(url)

    with rasterio.open(url) as src:
        features = [data['area']['features'][0]['geometry']]
        # trying this out, but getting Input shapes do not overlap raster
        # maybe features format is bad?
        # https://mapbox.github.io/rasterio/topics/masking-by-shapefile.html

        out_image, out_transform = rasterio.mask.mask(src, features, crop=True)
        out_meta = src.meta.copy()

        # Maybe use jp2 driver if there is one?
        out_meta.update({"driver": "GTiff",
                 "height": out_image.shape[1],
                 "width": out_image.shape[2],
                 "transform": out_transform})

        with rasterio.open("RGB.byte.masked.tif", "w", **out_meta) as dest:
            dest.write(out_image)

    return JsonResponse({
        'success': True,
    }, safe=False)
