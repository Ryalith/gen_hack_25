import rasterio

from ..data import get_main_data_folder
from ..utils import quarter2timeperiod

def open_from_timeperiod(year, quarter) -> rasterio.DatasetReader:
    timeperiod = quarter2timeperiod(year, quarter)
    filepath = get_main_data_folder() / "sentinel2_ndvi" / f"ndvi_{timeperiod}.tif"

    return rasterio.open(filepath)