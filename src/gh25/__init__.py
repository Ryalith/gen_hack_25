# TODO
# take an eca df, a ndvi DatasetReader
# order eca data by lat lon
# load chunks of the ndvi data in a cache
# find nearest
import numpy as np
import pandas as pd
import geopandas as gpd
from rasterio.windows import Window
from rasterio.warp import transform
from pathlib import Path

from .. import set_main_data_folder, get_main_data_folder
from ..utils import convert_ndvi_to_real_scale, variable2datavar
from .. import eca, ndvi, era5

set_main_data_folder(Path('/ssd2/mldata/GenHack2025/data'))

def from_timeperiod_variable(year, quarter, variable):
    """
    variable must be one of:

    "2m_temperature",
    "total_precipitation",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    """
    if quarter not in [1, 2, 3, 4]:
        raise ValueError("quarter must be in {1, 2, 3, 4}")
    
    gh25_datafolder = get_main_data_folder() / "GH25"
    gh25_datafolder.mkdir(exist_ok=True)
    gh25_csv_file = gh25_datafolder / f"GH25_{year}_{quarter}_variable.csv"

    if gh25_csv_file.exists():
        print(f"Found GH25 data for {year=}, {quarter=}, {variable=}, loading GeoDataframe ...")
        gdf = pd.read_csv(gh25_csv_file)
    else:
        print(f"No GH25 data for {year=}, {quarter=}, {variable=}, building GeoDataframe ...")
        gdf = _build_gdf_from_timeperiod_variable(year, quarter, variable)

    return gdf


def _build_gdf_from_timeperiod_variable(year, quarter, variable):

    # Load station data
    eca_meta_df = eca.meta_from_timeperiod(year, quarter)
    eca_df = eca.from_timeperiod(year, quarter)
    NDVI_values = []

    # With rasterio DatasetReader, get NDVI
    with ndvi.open_from_timeperiod(year, quarter) as src:
        lons, lats = transform('EPSG:4326', src.crs, eca_meta_df['LON_decimal'].values, eca_meta_df['LAT_decimal'].values)
        for lon, lat in zip(lons, lats):
            # lon, lat = transform_to_the_right_coordinate(lon, lat)

            # Convert the geographical coordinates to raster indices (row, col)
            row, col = src.index(lon, lat)

            # Define a window to read around the target pixel
            # Here, we read just a single pixel (window size 1x1) for the exact value
            window = Window(col, row, 1, 1)  # 1x1 window (single pixel)

            # Read the value at that window
            data = src.read(1, window=window)  # Read the single pixel in the first band

            if data.shape == (1, 1):
                value = data[0, 0]  # data is a 2D array, extract the value of the single pixel
            else:
                value = np.nan # We are out of bounds there is no data to be seen

            # Append the value to the list after converting to real scale
            NDVI_values.append(value)
    
        # Add the extracted values to the DataFrame
        eca_meta_df['NDVI'] = NDVI_values
        eca_meta_df['NDVI'] = convert_ndvi_to_real_scale(eca_meta_df['NDVI'], src.meta)
    
    era5_ds = era5.from_timeperiod_variable(year, variable)
    lons, lats, dates = eca_df['LON_decimal'].values, eca_df['LAT_decimal'].values, eca_df['DATE']
    era5_values = []
    for lon, lat, date in zip(lons, lats, dates):
        try:
            era5_values.append(era5_ds.sel(latitude=lat, longitude=lon, valid_time=date, method="nearest", tolerance=0.1).item())
        except KeyError:
            era5_values.append(np.nan)

    eca_df[variable2datavar[variable]] = era5_values

    gh25_gdf = gpd.GeoDataFrame(
        eca_df, 
        geometry=gpd.points_from_xy(eca_df['LON_decimal'], eca_df['LAT_decimal']),
        crs="EPSG:4326" # (WGS84, adequate for lat/lon coordinates)
    )

    return gh25_gdf