# --- IMPORTS --- 
import urllib
import pandas as pd 
import datetime
import asyncio
import aiohttp
import io

# --- CONSTANT DEFINITIONS ---
# USGS API MANAGEMENT
USGS_API_METHOD_QUERY = "query"
USGS_API_BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/"

USGS_API_PARAM_FORMAT = "format"
USGS_API_PARAM_FORMAT_CSV = "csv"
USGS_API_PARAM_FORMAT_JSON = "geojson"
USGS_API_PARAM_ENDTIME = "endtime"
USGS_API_PARAM_STARTTIME = "starttime"
USGS_API_PARAM_STARTTIME_DEFAULT = datetime.datetime.now() - datetime.timedelta(days=200*365) #datetime 200 years from now
USGS_API_PARAM_LATITUDE = "latitude"
USGS_API_PARAM_LONGITUDE = "longitude"
USGS_API_PARAM_RADIUS_KM = "maxradiuskm"
USGS_API_PARAM_MIN_MAGN = "minmagnitude"

# ASSET DATA MODEL DEFINITION
ASSET_LATITUDE_COLUMN = "latitude"
ASSET_LONGITUDE_COLUMN = "longitude"

# UTILS
HTTPCODE_OK = 200

# --- FUNCTIONS ---
def build_api_url(method,parameters=None):
    """This function build the URL to perform the desired call to USGS Earthquake API. See https://earthquake.usgs.gov/fdsnws/event/1/
    Note that no validity checks are performed.

    Parameters
    ----------  
        method: str
            Name of the method to be called. See USGS_API_METHOD_ constants
        parameters: dict, optional
            List of key/value for parameters of the call. If not set, no parameters are added to the URL

    Returns
    -------
        str
            URL for the API call
    """

    res = f"{USGS_API_BASE_URL}{method}"
    if parameters:
        res +=  f"?{urllib.parse.urlencode(parameters)}"
    return res


def build_api_query_parameters(latitude, longitude, radius, minimum_magnitude=None, end_date=None, format=None):
    """This function build a dict ready to be passed to "build_api_url" as "parameters" argument for the "query" method.
    It defines parameters to retrieve earthquakes in a circle around the point of interest in the past 200 years (not configurable).

    Parameters
    ---------- 
        latitude: float
            latitude of the center of the circle, in decimal degrees
        longitude: float
            longitude of the center of the circle, in decimal degrees
        radius: float
            radius of the circle, in km
        minimum_magnitude: float, optional
            When set, this allows to filter out earthquakes of a magnitude strictly lower than this value
        end_date: float, optional
            When set, this allows to filter out earthquakes that happened after the specified date. ISO8601 Date/Time format. Unless a timezone is specified, UTC is assumed (see API documentation)
        format: string, optional
            If set, specifies the format of the data to retrieve from the USGS API. See API documentation.
    
    Returns
    -------
        dict
            dictionnary key/value of the parameters ready to be passed to build_api_url

    """

    parameters = {
        USGS_API_PARAM_STARTTIME: USGS_API_PARAM_STARTTIME_DEFAULT,
        USGS_API_PARAM_LATITUDE: latitude,
        USGS_API_PARAM_LONGITUDE: longitude,
        USGS_API_PARAM_RADIUS_KM: radius
    }
    if minimum_magnitude: 
        parameters[USGS_API_PARAM_MIN_MAGN] = minimum_magnitude

    if end_date:
        parameters[USGS_API_PARAM_ENDTIME] = end_date

    if format:
        parameters[USGS_API_PARAM_FORMAT] = format

    return parameters

def get_earthquake_data(latitude, longitude, radius, minimum_magnitude=None, end_date=None):
    """This function retrieves a dataframe of all earthquakes in the circle of interest, and matching the additional criteria, from the USGS API. 

    Parameters
    ---------- 
        latitude: float
            latitude of the center of the circle, in decimal degrees
        longitude: float
            longitude of the center of the circle, in decimal degrees
        radius: float
            radius of the circle, in km
        minimum_magnitude: float, optional
            When set, this allows to filter out earthquakes of a magnitude strictly lower than this value
        end_date: float, optional
            When set, this allows to filter out earthquakes that happened after the specified date. ISO8601 Date/Time format. Unless a timezone is specified, UTC is assumed (see API documentation)
    
    Returns
    -------
        DataFrame
            DataFrame with one earthquake matching the criteria per row, containing all data available from the USGS API.
    """
    
    #Build the URL to perform a query operation
    parameters = build_api_query_parameters(latitude, longitude, radius, minimum_magnitude, end_date, USGS_API_PARAM_FORMAT_CSV)
    url = build_api_url(USGS_API_METHOD_QUERY, parameters)

    #Perform the API Call and retrieve the response
    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        print(f'get_earthquake_data: An urllib.HTTPerror occurred: {e}')
    except urllib.error.URLError as e:
        print(f'get_earthquake_data: An urllib.URLerror occurred: {e}')
    except Exception as e:
        print(f'get_earthquake_data: An unknown error occurred: {e}')

    #Parse the response to a DataFrame
    data = pd.read_table(response, delimiter = ',')

    return data

async def get_earthquake_data_for_multiple_locations(assets, radius, minimum_magnitude=None, end_date=None):
    """This function retrieves a dataframe of all earthquakes in multiple circles of interest of a common radius, and matching the additional criteria, from the USGS API.
    This function uses coroutines to perform one query per circle. 

    Parameters
    ---------- 
        
    Returns
    -------
        DataFrame
            DataFrame with one earthquake matching the criteria per row, containing all data available from the USGS API.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.ensure_future( \
                get_earthquake_data_for_single_location(session, location[ASSET_LATITUDE_COLUMN], location[ASSET_LONGITUDE_COLUMN], radius, minimum_magnitude, end_date) \
            ) for index, location in assets.iterrows()]
        responses = await asyncio.gather(*tasks) #Wait for all coroutines to end and gather results.

        #Gathered results must be merged within the same DataFrame
        data_unit_list = [] #List of all unit dataframes
        for response in responses:
            data_unit = pd.read_csv(io.StringIO(response)) #Convert the response to a dataframe
            data_unit_list.append(data_unit) #Store it in the list
        data = pd.concat(data_unit_list) #Merge all unit dataframe into a single one
    return data

async def get_earthquake_data_for_single_location(session, latitude, longitude, radius, minimum_magnitude, end_date):
    """This function handles a coroutine to perform one call to USGS API. 
    It retrieves a text-csv string of all earthquakes in a circle of interest, and matching the additional criteria, from the USGS API. 

    Parameters
    ---------- 
        session: aiohttp.ClientSession
        latitude: float
            latitude of the center of the circle, in decimal degrees
        longitude: float
            longitude of the center of the circle, in decimal degrees
        radius: float
            radius of the circle, in km
        minimum_magnitude: float, optional
            When set, this allows to filter out earthquakes of a magnitude strictly lower than this value
        end_date: float, optional
            When set, this allows to filter out earthquakes that happened after the specified date. ISO8601 Date/Time format. Unless a timezone is specified, UTC is assumed (see API documentation)
    
    Returns
    -------
        str
            String in text-csv format with one earthquake matching the criteria per row, containing all data available from the USGS API.
    """

    #Build the URL to perform a query operation
    parameters = build_api_query_parameters(latitude, longitude, radius, minimum_magnitude, end_date,USGS_API_PARAM_FORMAT_CSV)
    url = build_api_url(USGS_API_METHOD_QUERY, parameters)

    #Perform the API Call and retrieve the response
    async with session.get(url) as response:
        assert response.status == HTTPCODE_OK #Ensure the call is successful
        data = await response.text()
    return data