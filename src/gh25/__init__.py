# TODO
# take an eca df, a ndvi DatasetReader
# order eca data by lat lon
# load chunks of the ndvi data in a cache
# find nearest
import numpy as np
from rasterio.windows import Window
from rasterio.warp import transform
from pathlib import Path

from .. import set_main_data_folder, get_main_data_folder
from ..utils import convert_ndvi_to_real_scale
from .. import eca, ndvi

set_main_data_folder(Path('/ssd2/mldata/GenHack2025/data'))

def from_timeperiod(year, quarter):
    raise NotImplementedError

def _build_gdf_from_timeperiod(year, quarter):

    # Load station data
    eca_df = eca.meta_from_timeperiod(year, quarter)
    NDVI_values = []

    # With rasterio DatasetReader, get NDVI
    with ndvi.open_from_timeperiod(year, quarter) as src:
        lons, lats = transform('EPSG:4326', src.crs, eca_df['LON_decimal'].values, eca_df['LAT_decimal'].values)
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
        eca_df['NDVI'] = NDVI_values
        eca_df['NDVI'] = convert_ndvi_to_real_scale(eca_df['NDVI'], src.meta)
    
    return eca_df