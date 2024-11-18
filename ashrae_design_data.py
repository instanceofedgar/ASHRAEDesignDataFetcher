import requests
import json
from enum import Enum

class ASHRAE_VERSION(Enum):
    v2009 = '2009'
    v2013 = '2013'
    v2017 = '2017'
    v2021 = '2021'

def remove_bom(text: str)->str:
    '''
    Removes Byte Order Mark (BOM) at the beginning (common in some UTF-8 encoded files)
    '''
    if text.startswith('\ufeff'):
        text = text[1:]
    return text

class FetchStationError(Exception):
    '''
    Custom exception for fetch station errors
    '''
    pass

class StationJSONDecodeError(FetchStationError):
    '''
    Custom exception for JSON decoding errors
    '''
    pass

def fetch_meteo_station_data(
        lat: float, 
        lng: float, 
        ashrae_version: ASHRAE_VERSION
    )->dict:
    '''
    Returns an ASHRAE meteo station dict
    Parameters: lat, ln (float) and ashrae_version (ASHRAE_VERSION enum)
    '''
    request_params = {
        'lat': lat,
        'long': lng,
        'number': '10',
        'ashrae_version': ashrae_version.value
    }
    url = 'https://ashrae-meteo.info/v2.0/request_places.php'
    resp = requests.post(url, data=request_params)
    if resp.status_code != 200:
        raise FetchStationError(f'Error: received status code {resp.status_code}, response body: {resp.text}')
    
    try:
        cleaned_text = remove_bom(resp.text)
        resp_json = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        raise StationJSONDecodeError(f'JSON decoding error: {e}, response body: {resp.text}')
    
    stations = resp_json.get('meteo_stations', [])
    if not stations:
        raise FetchStationError('Error: No stations found')
    
    return stations[0]

def fetch_ashrae_design_data(
        lat: float, 
        lng: float, 
        ashrae_version: ASHRAE_VERSION
    )->dict:
    '''
    Returns dictionary with ASHRAE design data for heating and cooling
    'heating_DB_99.6' and 'cooling_DB_MCWB_0.4_DB'
    '''
    station_data = fetch_meteo_station_data(lat, lng, ashrae_version)

    if not station_data:
        return None
    
    request_params = {
        'wmo': station_data.get('wmo'),
        'ashrae_version': ashrae_version.value,
        'si_ip': 'SI'
    }
    url = 'https://ashrae-meteo.info/v2.0/request_meteo_parametres.php'
    
    resp = requests.post(url, data=request_params)
    if resp.status_code != 200:
        raise FetchStationError(f'Error: received status code {resp.status_code}, response body: {resp.text}')
    
    try:
        cleaned_text = remove_bom(resp.text)
        resp_json = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        raise StationJSONDecodeError(f'JSON decoding error: {e}, response body: {resp.text}')
    
    # Extract weather data
    stations = resp_json.get('meteo_stations', [])
    if not stations:
        raise FetchStationError('Error: No stations found')
    
    station = stations[0]
    weather_data = {
        'heating_DB_99.6': float(station.get('heating_DB_99.6', 'n/a')),
        'cooling_DB_0.4': float(station.get('cooling_DB_MCWB_0.4_DB', 'n/a'))
    }
    
    return weather_data
