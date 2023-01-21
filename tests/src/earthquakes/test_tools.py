from earthquakes.tools import get_haversine_distance
import pytest
import numpy

# --- build_api_url - Unit Tests ---
# Refer to https://www.vcalc.com/wiki/vCalc/Haversine+-+Distance to check computations
@pytest.mark.parametrize("blist_lat,blist_lon,a_lat,a_lon, expected", [
    ([0], [0], 0, 0, [0]),
    ([1], [2], 1, 2, [0]),
    ([1], [2], 3, 4, [314.4]),
    ([60], [-30], -1, 35, [8749.65]),
    ([60, 0, -27.6], [-30, 89, 3.7], 2.22, -12, [6607.38, 11229.77, 3717.32]),
    ([90, 0, -90, 0], [90, 0, 90, -90], 0, -90, [10007.56, 10007.56, 10007.56, 0]),
])
def test_get_haversine_distance(blist_lat,blist_lon,a_lat,a_lon,expected):
  # Arrange
  # Act
  res = get_haversine_distance(blist_lat,blist_lon,a_lat,a_lon)
  # Assert
  numpy.testing.assert_allclose(res, expected, rtol=0.01)