import xarray as xr
from ..utils import era5_variables, variable2statistic, variable2datavar
from ..data import get_main_data_folder

def from_timeperiod_variable(year, variable: str):
    """
    variable must be one of:
    "2m_temperature",
    "total_precipitation",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    """
    assert variable in era5_variables

    era5_data_folder = get_main_data_folder() / "derived-era5-land-daily-statistics/"
    filepath = era5_data_folder / f"{year}_{variable}_{variable2statistic[variable]}.nc"
    ds = xr.open_dataset(filepath)
    return ds[variable2datavar[variable]]