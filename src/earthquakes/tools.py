# --- IMPORTS --- 
import math
import datetime 
import numpy as np
import pandas as pd

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
YEAR_COLUMN = "year"

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
    #Convert lat/lon of point A from decimal degrees to radians
    a_lambda = np.deg2rad(a_lon)
    a_phi = np.deg2rad(a_lat)

    #Convert lat/lon of point B from decimal degrees to radians
    b_lambda = np.deg2rad(blist_lon)
    b_phi = np.deg2rad(blist_lat)

    #Compute haversine distance (see wikipeadia reference above)
    res = (2*EARTH_RADIUS*np.arcsin( \
        np.sqrt( \
            np.sin((b_phi - a_phi)/2) ** 2 + np.cos(a_phi)*np.cos(b_phi)*np.sin((b_lambda - a_lambda)/2) ** 2
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
    #Initialize a dataframe matching each earthquake year to the eligible payout
    df_earthquake_payouts = pd.DataFrame()
    #For each earthquake, compute the applicable payout
    df_earthquake_payouts[PAYOUT_COLUMN] = earthquake_data.apply(compute_payout_item,args=(payout_structure,), axis=1)
    #For each earthquake, retrieve the year
    df_earthquake_payouts[YEAR_COLUMN] = earthquake_data[TIME_COLUMN].apply(datetime.datetime.strptime, args=(EARTHQUAKE_TIME_FORMAT,)).dt.year
    #For each year, get the maximum applicable payout
    df_yearly_payout = df_earthquake_payouts.groupby(YEAR_COLUMN, as_index=False)[PAYOUT_COLUMN].max()
    #Remove years with no payout (payout = 0) for clarity
    df_yearly_payout.drop(df_yearly_payout[df_yearly_payout[PAYOUT_COLUMN] == 0].index, inplace = True)
    #Format the output as a dict key/value = year/payout
    return dict(zip(df_yearly_payout[YEAR_COLUMN], df_yearly_payout[PAYOUT_COLUMN]))


def compute_payout_item(earthquake_event, payout_structure):
    """This function computes the payout for a given earthquake within a given payout structure.
    Payout computation rules are:
        - earthquake must be within the radius criteria
        - earthquake magnitude must be above the magnitude criteria

    Parameters
    ---------- 
        earthquake_event: Row of a Dataframe with columns: 'distance', 'mag'
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
    #For each possible payout, keep its value only if applicable, otherwise 0. Then get the maximum of remaining payouts.
    return (1*(earthquake_event[DISTANCE_COLUMN] <= payout_structure[PAYOUT_RADIUS]) * \
           1*(earthquake_event[MAGNITUDE_COLUMN] >= payout_structure[PAYOUT_MAGNITUDE]) * \
           payout_structure[PAYOUT_PERCENTAGE]).max()
    
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
    #Validate inputs
    res = 0
    valid_inputs = True
    if end_year < start_year:
        valid_inputs = False
        print("compute_burning_cost - Warning: end_year must be above or equal to start_year")

    if valid_inputs:
        #Compute the sum of payouts per years within the time range
        payout_sum = sum(payout for year, payout in payouts.items() if start_year <= year and year <= end_year)
        #Divide by the number of years in the time range
        res = payout_sum / (end_year - start_year + 1)
    return res