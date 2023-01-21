from earthquakes.usgs_api import build_api_url, build_api_query_parameters
import pytest
import datetime

# --- build_api_url - Unit Tests ---
@pytest.mark.parametrize("method", [
    ('query'),
    ('toto'),
    (-1)
])
def test_build_api_url_no_params(method):
  # Arrange
  # Act
  res = build_api_url(method)
  # Assert
  assert res == "https://earthquake.usgs.gov/fdsnws/event/1/"+str(method)

@pytest.mark.parametrize("method, parameters, parameter_string", [
    ('query', {'start_date': '2022-01-01'}, 'start_date=2022-01-01'),
    ('query', {'start_date': '2022-01-01 22:23:24', 'end_date':'2023-11-25'}, 'start_date=2022-01-01+22%3A23%3A24&end_date=2023-11-25'),
    ('query', {'end_date': datetime.datetime(year=2021, month=10, day=21)}, f'end_date=2021-10-21+00%3A00%3A00'),
    ('toto', {'format': 'csv', 'end_date': datetime.datetime(year=1, month=10, day=21)}, 'format=csv&end_date=0001-10-21+00%3A00%3A00')
])
def test_build_api_url_with_params(method,parameters,parameter_string):
  # Arrange
  # Act
  res = build_api_url(method, parameters)
  # Assert
  assert res == "https://earthquake.usgs.gov/fdsnws/event/1/"+str(method)+'?'+parameter_string

def test_build_api_url_with_empty_params():
  # Arrange
  # Act
  res = build_api_url('query', {})
  # Assert
  assert res == "https://earthquake.usgs.gov/fdsnws/event/1/"+str('query')

# --- build_api_query_parameters - Unit Tests ---
@pytest.mark.parametrize("latitude, longitude, radius, minimum_magnitude, end_date, format", [
    (1,2,3,None,None,None),
    (-1,5,23,1,None,None),
    (0.001, 1000000, 1e24,-1,None,None),
    (0.001, 100, 7 ,10,'2022-01-01',None),
    (0.001, 100, 7 ,10,datetime.datetime(year=2021, month=10, day=21),None),
    (0.001, 100, 7 ,None,datetime.datetime(year=2021, month=10, day=21),'csv'),
    (0.001, 100, 7 ,None,None,'csv')
])
def test_build_api_query_parameters(latitude, longitude, radius, minimum_magnitude, end_date, format):
  # Arrange
  expected = {"maxradiuskm": radius, "longitude": longitude, "latitude": latitude, "starttime": datetime.datetime.now() - datetime.timedelta(days=200*365)}
  if minimum_magnitude:
    expected["minmagnitude"]=minimum_magnitude

  if end_date:
    expected["endtime"]=end_date

  if format:
    expected["format"]=format

  # Act
  res = build_api_query_parameters(latitude, longitude, radius, minimum_magnitude, end_date, format)
  # Assert
  assert abs(res["starttime"] - expected["starttime"]) < datetime.timedelta(hours=1)
  del res["starttime"] ; del expected["starttime"]
  assert res == expected
