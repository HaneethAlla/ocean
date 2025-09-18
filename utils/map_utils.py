import os
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from utils.netcdf_parser import parse_netcdf

def plot_trajectory_for_day(data_dir, target_date):
    """
    Plot the trajectory of floats for a specific day using .nc files in data_dir.
    Returns: response string and shows the plot.
    """
    lats, lons = [], []
    for year in ['2024', '2025']:
        year_dir = os.path.join(data_dir, year)
        if not os.path.exists(year_dir):
            continue
        for month in os.listdir(year_dir):
            month_dir = os.path.join(year_dir, month)
            if not os.path.isdir(month_dir):
                continue
            for fname in os.listdir(month_dir):
                if fname.endswith('.nc'):
                    data = parse_netcdf(os.path.join(month_dir, fname))
                    file_date = data.get('juld')
                    if file_date and file_date.strftime('%Y-%m-%d') == target_date:
                        if data['latitude'] is not None and data['longitude'] is not None:
                            lats.append(data['latitude'])
                            lons.append(data['longitude'])
    if lats and lons:
        fig = plt.figure(figsize=(6, 4))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        ax.coastlines()
        ax.add_feature(cfeature.BORDERS, linestyle=":")
        ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
        lon_center = (np.nanmin(lons) + np.nanmax(lons)) / 2
        lat_center = (np.nanmin(lats) + np.nanmax(lats)) / 2
        global_extent = 90
        ax.set_extent([
            lon_center - global_extent, lon_center + global_extent,
            lat_center - global_extent/2, lat_center + global_extent/2
        ], crs=ccrs.PlateCarree())
        ax.plot(lons, lats, "bo-", markersize=4, transform=ccrs.PlateCarree())
        ax.set_title(f"Float Trajectory on {target_date}")
        plt.show()
        return "📍 Showing trajectory map (half-global view)"
    else:
        return "⚠️ No trajectory data for this date."
from typing import Dict, Any, List

def generate_map_data(question: str, context: Dict[str, Any], db) -> Dict[str, Any]:
    """Generate map data based on the query and context"""
    map_data = {
        "center": [20, 80],  # Default center (Arabian Sea)
        "zoom": 4,
        "markers": []
    }
    
    # Add markers for each float in context
    for float_data in context.get('floats', []):
        if float_data['latitude'] and float_data['longitude']:
            marker = {
                "position": [float_data['latitude'], float_data['longitude']],
                "popup": f"Float {float_data['platform_number']}",
                "data": {
                    "platform_number": float_data['platform_number'],
                    "date": float_data['date'],
                    "parameters": float_data['parameters']
                }
            }
            map_data["markers"].append(marker)
    
    # If no specific floats in context, show all floats
    if not map_data["markers"]:
        from models import ArgoFloat
        all_floats = db.query(ArgoFloat).all()
        for float_obj in all_floats:
            if float_obj.latitude and float_obj.longitude:
                marker = {
                    "position": [float_obj.latitude, float_obj.longitude],
                    "popup": f"Float {float_obj.platform_number}",
                    "data": {
                        "platform_number": float_obj.platform_number,
                        "date": float_obj.juld.isoformat() if float_obj.juld else None,
                        "parameters": float_obj.parameters
                    }
                }
                map_data["markers"].append(marker)
    
    return map_data