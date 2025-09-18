import netCDF4 as nc
import numpy as np
from datetime import datetime, timedelta
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

def parse_netcdf(file_path):
    """Parse ARGO NetCDF file and extract relevant data"""
    data = nc.Dataset(file_path)
    
    # Extract metadata
    platform_number = getattr(data, 'PLATFORM_NUMBER', 'Unknown').strip()
    date_created = parse_date(getattr(data, 'DATE_CREATION', ''))
    juld = parse_juld(getattr(data, 'JULD', 0), getattr(data, 'REFERENCE_DATE_TIME', '19500101000000'))
    
    # Extract position data
    latitude = float(data.variables['LATITUDE'][0]) if 'LATITUDE' in data.variables else None
    longitude = float(data.variables['LONGITUDE'][0]) if 'LONGITUDE' in data.variables else None
    
    # Create geometry point
    location = from_shape(Point(longitude, latitude)) if latitude and longitude else None
    
    # Extract profile data
    profile_data = extract_profile_data(data)
    
    # Extract parameters
    parameters = []
    if 'STATION_PARAMETERS' in data.variables:
        params = data.variables['STATION_PARAMETERS'][:]
        for param in params:
            param_name = ''.join([x.decode('utf-8') for x in param if x != b' ']).strip()
            if param_name:
                parameters.append(param_name)
    
    return {
        'platform_number': platform_number,
        'date_created': date_created,
        'juld': juld,
        'latitude': latitude,
        'longitude': longitude,
        'location': location,
        'parameters': parameters,
        'profile_data': profile_data,
        'cycle_number': int(data.variables['CYCLE_NUMBER'][0]) if 'CYCLE_NUMBER' in data.variables else None,
        'data_mode': getattr(data, 'DATA_MODE', 'Unknown')
    }

def extract_profile_data(data):
    """Extract profile data from NetCDF file"""
    profile_data = {}
    
    # Extract PRES, TEMP, PSAL data if available
    for param in ['PRES', 'TEMP', 'PSAL']:
        if param in data.variables:
            values = data.variables[param][:]
            # Handle fill values and quality control
            if '_FillValue' in data.variables[param].ncattrs():
                fill_value = data.variables[param]._FillValue
                values = np.ma.masked_equal(values, fill_value)
            
            profile_data[param] = {
                'values': values.compressed().tolist() if hasattr(values, 'compressed') else values.tolist(),
                'units': getattr(data.variables[param], 'units', ''),
                'long_name': getattr(data.variables[param], 'long_name', '')
            }
    
    return profile_data

def parse_date(date_str):
    """Parse date string from NetCDF attributes"""
    try:
        return datetime.strptime(date_str, '%Y%m%d%H%M%S')
    except:
        return None

def parse_juld(juld, reference_date):
    """Convert Julian day to datetime"""
    try:
        ref_date = datetime.strptime(reference_date, '%Y%m%d%H%M%S')
        return ref_date + timedelta(days=float(juld))
    except:
        return None