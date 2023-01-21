# --- IMPORTS --- 
import math
import datetime 

# --- CONSTANT DEFINITIONS ---
EARTH_RADIUS = 6378
EARTHQUAKE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"

# DATA MODEL DEFINITION
TIME_COLUMN = "time"
PAYOUT_COLUMN = "payout"
MAGNITUDE_COLUMN = "mag"
DISTANCE_COLUMN = "distance"
LATITUDE_COLUMN = "latitude"
LONGITUDE_COLUMN = "longitude"

# EARTHQUAKE EVENT DATA MODEL DEFINITION
EARTHQUAKE_EVENT_MAGNITUDE = "magnitude"
EARTHQUAKE_EVENT_DISTANCE = "distance"
EARTHQUAKE_EVENT_YEAR = "year"

# PAYOUT STRUCTURE DATA MODEL DEFINITION
PAYOUT_RADIUS = "Radius"
PAYOUT_MAGNITUDE = "Magnitude"
PAYOUT_PERCENTAGE = "Payout"

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
    
def compute_payouts(earthquake_data, payout_structure):
    """This function computes the payout for each year for which earthquake data is available, based on a list of earthquake events and a payout structure.
    It uses "compute_payout_item" for payout computation rules (see there for description)

    Parameters
    ---------- 
        earthquake_data: DataFrame
            DataFrame of earthquakes to take into account. Mandatory columns: 'time' (see "EARTHQUAKE_TIME_FORMAT" for format), 'mag', 'distance'.
        payout_structure: DataFrame
            DataFrame containing the payout structure. See "compute_payout_item" doc for description

    Returns
    -------
        dict
            key: year, value: payout applied on this year according to the payout structure (in %)
    """
    
    #Initialize the dict to gather results
    res = dict()

    #Iterate over each earthquake to see its impact on payout
    for index, earthquake_item in earthquake_data.iterrows():
        
        #Extract data about the earthquake that is relevant for payout computation.
        earthquake_event = {
            EARTHQUAKE_EVENT_YEAR: datetime.datetime.strptime(earthquake_item[TIME_COLUMN], EARTHQUAKE_TIME_FORMAT).year,
            EARTHQUAKE_EVENT_MAGNITUDE: earthquake_item[MAGNITUDE_COLUMN],
            EARTHQUAKE_EVENT_DISTANCE: earthquake_item[DISTANCE_COLUMN]
        }

        #Compute the payout linked to this earthquake
        payout_value = compute_payout_item(earthquake_event, payout_structure)

        if payout_value > 0: #If the earthquake gives right to a payout
            #Compare this payout to the ones on the same year. Only the highest one should be kept.
            if earthquake_event[EARTHQUAKE_EVENT_YEAR] in res:
                res[earthquake_event[EARTHQUAKE_EVENT_YEAR]] = max(res[earthquake_event[EARTHQUAKE_EVENT_YEAR]], payout_value)
            else:
                res[earthquake_event[EARTHQUAKE_EVENT_YEAR]] = payout_value
    return res


def compute_payout_item(earthquake_event, payout_structure):
    """This function computes the payout for a given earthquake within a given payout structure.
    Payout computation rules are:
        - earthquake must be within the radius criteria
        - earthquake magnitude must be above the magnitude criteria

    Parameters
    ---------- 
        earthquake_data: dict
            Dict containing data on the earthquake. List of mandatory keys:
                EARTHQUAKE_EVENT_MAGNITUDE: float - Magnitude of the earthquake
                EARTHQUAKE_EVENT_DISTANCE: float - Distance of the earthquake from the point of interest, in km.
        payout_structure: DataFrame
            DataFrame containing the payout structure. See "compute_payout_item" doc for description List of mandatory columns:
                PAYOUT_RADIUS: float - Radius criteria, in km.
                PAYOUT_MAGNITUDE: float - Magnitude criteria
                PAYOUT_PERCENTAGE: float - Payout value applied for those criteria, in percent

    Returns
    -------
        float
            payout applied for this earthquake, in percent
    """
    #By default, applied payout is 0.
    res = 0

    #For each set of criteria, check if the earthquake matches or not
    for index, payout_item in payout_structure.iterrows():
        #Radius criteria
        if  earthquake_event[EARTHQUAKE_EVENT_DISTANCE] <= payout_item[PAYOUT_RADIUS] and \
            earthquake_event[EARTHQUAKE_EVENT_MAGNITUDE] >= payout_item[PAYOUT_MAGNITUDE]: # Magnitude criteria
            res = max(res, payout_item[PAYOUT_PERCENTAGE]) #If the earthquake matches several criteria set, we keep the highest payout.
    return res
    
def compute_burning_cost(payouts, start_year, end_year):
    """This function computes the burning cost over a time range from a list of payouts.
    The burning cost is the average of payouts over a time range. It is computed as follows: "sum of payouts per year" / "number of years"
    Parameters
    ---------- 
        payouts: dict
            key: year, value: payout applied on this year according to the payout structure (in %)
        start_year: int
            first year of the time frame (included)
        end_year: int
            last yeaf of the time frame (included)

    Returns
    -------
        float
            burning rate in percent
    """
    #Compute the sum of payouts per years within the time range
    payout_sum = 0
    for year, payout in payouts.items():
        if start_year <= year and year <= end_year:
            payout_sum += payout
    #Divide by the number of years in the time range
    res = payout_sum / (end_year - start_year + 1)
    return res