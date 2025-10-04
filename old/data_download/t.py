import cdsapi

c = cdsapi.Client()

c.retrieve(
    'reanalysis-era5-land',
    {
        'variable': [
            '10m_u_component_of_wind', '10m_v_component_of_wind', '2m_temperature',
            'leaf_area_index_high_vegetation', 'leaf_area_index_low_vegetation', 'skin_temperature',
            'soil_temperature_level_1', 'surface_net_solar_radiation', 'surface_net_thermal_radiation',
            'surface_pressure', 'surface_solar_radiation_downwards', 'surface_thermal_radiation_downwards',
            'total_precipitation', 'volumetric_soil_water_layer_1',
        ],
        'year': '2017',
        'month': '07',
        'day': [
            '01', '02', '03',
            '04', '05', '06',
            '07', '08', '09',
            '10', '11', '12',
            '13', '14', '15',
            '16', '17', '18',
            '19', '20', '21',
            '22', '23', '24',
            '25', '26', '27',
            '28', '29', '30',
            '31',
        ],
        'time': [
            '06:00', '07:00', '08:00',
            '09:00', '10:00', '11:00',
            '12:00', '13:00', '14:00',
            '15:00', '16:00', '17:00',
            '18:00',
        ],
        'format': 'netcdf',
    },
    'download.nc')