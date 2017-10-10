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

    response = requests.get(url)

    with rasterio.open(url) as raster_file:
        # print(raster_file.transform)
        # print(raster_file.transform)
        # print(fwd)
        # print(fwd * (0, 0))
        # print(fwd * (raster_file.width, raster_file.height))
        # print(raster_file.crs)
        # print(raster_file.indexes)

        shape = geojson['features'][0]['geometry']
        geo_shape = shapely.geometry.shape(shape)
        lon_min, lat_min, lon_max, lat_max = geo_shape.bounds
        # print(geo_shape.bounds)

        # print(raster_file.bounds)
        # print(raster_file.crs)
        # print(loaded_geojson.crs)
        # print(loaded_geojson.crs.name)
        transformed_geojson = rasterio.warp.transform_geom(raster_file.crs, 'EPSG:4326', shape)
        print(geometries)
        print(transformed_geojson)
        # print(a)
        fwd = Affine.from_gdal(*tuple(raster_file.transform))
        print(fwd)
        out_image, out_transform = rasterio.mask.mask(raster_file, [transformed_geojson], crop=True)

        # print(raster_file.index(lon_min, lat_min))

        # raster_file.read(1, window=Window(
        # print(raster_file.read(1))
        # print(raster_file.read(1)[raster_file.height // 2, raster_file.width // 2])
        # x, y = (raster_file.bounds.left + 100000, raster_file.bounds.top - 50000)
        # print(x)
        # print(y)
        # row, col = raster_file.index(x, y)
        # print(raster_file.read(1)[row, col])
        # print(rasterio.transform.xy(raster_file.transform, row, col))

        # bottom, left = raster_file.index(lon_min, lat_min)
        # top, right = raster_file.index(lon_max, lat_max)
        # # print(bottom)
        # raster_window = ((top, bottom+1), (left, right+1))
        # mask_bounds = [top, bottom, left, right]
        # window = raster_file.window(*mask_bounds)
        # # print(mask_bounds)
        # # print(window)
        # # print(raster_window)
        # bounding_box_array = raster_file.read(indexes=1, window=window)
        # # print(raster_file.read())
        # # print(bounding_box_array)
        #
        # rfa = raster_file.affine
        # bounding_box_affine = Affine(
        #     rfa.a, rfa.b, lon_min,
        #     rfa.d, rfa.e, lat_max
        # )
        # print(rfa)
        # print(bounding_box_affine)

        # inclusion_mask = rasterio.features.rasterize(
        #     shapes=[(geo_shape, 0)],
        #     out_shape=bounding_box_array.shape,
        #     transform=bounding_box_affine,
        #     fill=1,
        #     dtype=np.uint8,  # this is the smallest available dtype
        # )
        #
        # masked_data = np.ma.array(
        #     data=bounding_box_array,
        #     mask=inclusion_mask,
        # )
        #
        # print(masked_data)

        # print(src.crs)
        # print(src.affine)
        # print(geo_shape)

        # print(geometries)
        # features = [data['area']['features'][0]['geometry']]
        # trying this out, but getting Input shapes do not overlap raster
        # maybe features format is bad?
        # https://mapbox.github.io/rasterio/topics/masking-by-shapefile.html

        # out_image, out_transform = rasterio.mask.mask(src, geometries, crop=True)
        # out_meta = src.meta.copy()
        #
        # # Maybe use jp2 driver if there is one?
        # out_meta.update({
        #     'driver': 'JP2OpenJPEG',
        #      'height': out_image.shape[1],
        #      'width': out_image.shape[2],
        #      'transform': out_transform,
        #  })
        #
        # with rasterio.open('out.jp2', 'w', **out_meta) as dest:
        #     dest.write(out_image)

    return JsonResponse({
        'success': True,
    }, safe=False)
