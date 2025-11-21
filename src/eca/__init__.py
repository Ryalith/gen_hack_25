from ..data import get_main_data_folder
from ..utils import dms_to_decimal, quarter2dates

import pandas as pd

def from_timeperiod(year, quarter):
    if quarter not in [1, 2, 3, 4]:
        raise ValueError("quarter must be in {1, 2, 3, 4}")
    
    eca_tx_datafolder = get_main_data_folder() / "ECA_blend_tx"
    station_data_per_quarter_filepath = eca_tx_datafolder / f"stations_{year}_{quarter}.csv"

    if station_data_per_quarter_filepath.exists():
        print(f"Found data for {year=}, {quarter=}, loading Dataframe ...")
        df = pd.read_csv(station_data_per_quarter_filepath)
    else:
        print(f"No data for {year=}, {quarter=}, building Dataframe ...")
        df = _build_stations_data_per_quarter(year, quarter)

    return df

def meta_from_timeperiod(year, quarter):

    eca_tx_datafolder = get_main_data_folder() / "ECA_blend_tx"
    stations_filepath = eca_tx_datafolder / "stations.txt"

    stations_df = pd.read_csv(
        stations_filepath,
        skiprows=17,
        skipinitialspace=True
    )

    stations_df['LAT_decimal'] = stations_df['LAT'].apply(dms_to_decimal)
    stations_df['LON_decimal'] = stations_df['LON'].apply(dms_to_decimal)

    return stations_df


def _build_stations_data_per_quarter(year, quarter):

    eca_tx_datafolder = get_main_data_folder() / "ECA_blend_tx"
    stations_filepath = eca_tx_datafolder / "stations.txt"

    stations_df = pd.read_csv(
        stations_filepath,
        skiprows=17,
        skipinitialspace=True
    )

    stations_df['LAT_decimal'] = stations_df['LAT'].apply(dms_to_decimal)
    stations_df['LON_decimal'] = stations_df['LON'].apply(dms_to_decimal)

    dfs = []

    date_min, date_max = quarter2dates(year, quarter)

    # Loop through each ID, read the corresponding CSV, and add it to the list
    for id_ in stations_df['STAID'].to_list():

        # Construct the file path for each ID
        file_path = eca_tx_datafolder / f"TX_STAID{id_:06d}.txt"
        
        # Read the CSV file into a DataFrame
        df = pd.read_csv(
            file_path,
            skiprows=20,
            skipinitialspace=True
        )
        df = df[df['Q_TX'] == 0]
        
        df['DATE'] = pd.to_datetime(df['DATE'], format='%Y%m%d')
        
        df = df[(df['DATE'] >= date_min) & (df['DATE'] < date_max)]
        
        # Append the DataFrame to the list
        dfs.append(df)

    stations_data_df = pd.concat(dfs, axis=0, ignore_index=True)

    stations_data_df = stations_data_df[stations_data_df['Q_TX'] == 0]
    stations_data_df['DATE'] = pd.to_datetime(stations_data_df['DATE'], format='%Y%m%d')
    stations_data_df['TX_kelvin'] = stations_data_df['TX'] / 10 + 273.15 # Convert temperature to °K (originally stored in 0.1°C unit)
    stations_data_df = pd.merge(stations_data_df, stations_df[['STAID', 'LON_decimal', 'LAT_decimal']], on='STAID', how='left')

    station_data_per_quarter_filepath = eca_tx_datafolder / f"stations_{year}_{quarter}.csv"
    stations_data_df.to_csv(station_data_per_quarter_filepath)

    print(f'Done building Dataframe, found {len(stations_data_df)} rows of data.')
    return stations_data_df