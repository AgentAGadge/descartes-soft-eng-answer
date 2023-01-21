# --- IMPORTS --- 
import math

# --- CONSTANT DEFINITIONS ---
EARTH_RADIUS = 6378

# DATA MODEL DEFINITION
TIME_COLUMN = "time"
PAYOUT_COLUMN = "payout"
MAGNITUDE_COLUMN = "mag"
DISTANCE_COLUMN = "distance"
LATITUDE_COLUMN = "latitude"
LONGITUDE_COLUMN = "longitude"


def get_haversine_distance(blist_lat,blist_lon,a_lat,a_lon):
    """This function computes the haversine distance between point A and a list of points B.
    The haversine distance is the distance between two point on the surface of the earth, along a great circle.
    Refer to https://en.wikipedia.org/wiki/Haversine_formula 

    Parameters
    ---------- 
        blist_lat: list of float
            List of latitude of all points B, in decimal degrees. Must be of the same length as blist_lon
        blist_lon: list of float
            List of longitude of all points B, in decimal degrees. Must be of the same length as blist_lat
        a_lat: float
            Latitude of point A, in decimal degrees.
        a_lon: float, optional
            Longitude of point A, in decimal degrees.

    Returns
    -------
        list of float
            List of haversine distances between A and each points B, in km.
    """
    #Initialize the list of results
    res = []

    #Convert lat/lon of point A from decimal degrees to radians
    a_lambda = math.radians(a_lon)
    a_phi = math.radians(a_lat)

    for b_lat, b_lon in zip(blist_lat, blist_lon): #For each point B
        #Convert lat/lon of point B from decimal degrees to radians
        b_lambda = math.radians(b_lon)
        b_phi = math.radians(b_lat)

        #Compute haversine distance (see wikipeadia reference above)
        res.append(2*EARTH_RADIUS*math.asin( \
            math.sqrt( \
                math.sin((b_phi - a_phi)/2) ** 2 + math.cos(a_phi)*math.cos(b_phi)*math.sin((b_lambda - a_lambda)/2) ** 2
            )
        ))

    return res
    