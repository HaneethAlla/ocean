from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, List

from database import get_db
from models import ArgoFloat, UserQuery
from schemas import QueryRequest, QueryResponse
from utils.llm_integration import generate_response
from utils.map_utils import generate_map_data

router = APIRouter(prefix="/queries", tags=["queries"])

import os
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from utils.netcdf_parser import parse_netcdf

def plot_trajectory_for_day(data_dir, target_date):
    lats, lons = [], []
    # Loop through all files for the year/month
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

# Example usage:
# plot_trajectory_for_day('e:/sih/demo/data/', '2024-01-15')