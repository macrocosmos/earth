## Earth API

### What is this?

This is an API that returns an image of a certain location in earth cropped from Sentinel satellites.

An example request:
```python
requests.post(url = 'http://0.0.0.0:8000/api/v1/images/', {
  'area': { 
    # example geojson
    "type": "FeatureCollection",
    "features": [
      "geometry": {
        "coordinates": [
          [
            [23.136831521987915,
            55.38409627064378],
    # ...
  },
  'date': '2017-10-05',
  'take': '0', # which photo of the same day (usually 0),
  'band': '01',
})

# => This would return a cropped image:
# of that certain polygon
# of that date
# of that band (red, blue, and 10 other)
# of that "take"
```

### How to run / develop:

1. Install docker
2. This builds the docker container - handles installing dependencies, builds the project and runs the server:
```sh
# in project root container
docker-compose up --build
```
You can check if the server is running correctly by opening: http://0.0.0.0:8000

If that says page not found, its good!

3. To test the service, run:
```sh
# in project root container
python3 mock-request.py
```

4. If you get something like, then its good. Its just how far I've managed to get:
```python
# in the mock-request log
> You're seeing this error because you have

# in the server log
> ValueError: Input shapes do not overlap raster.
```

5. Check file `api/views.py` for logic.
