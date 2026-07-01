import cdstoolbox as ct

layout = {
    'input_ncols': 2,
    'output_align': 'bottom'
}

variables = {
    'Near-Surface Air Temperature': '2m_temperature',
}

tip = 'Changing value will restart the processing.'


@ct.application(title='Calculate Time Mean and Standard Deviation', layout=layout)
@ct.input.dropdown('variable', label='Variable', values=variables.keys(), help=tip)
@ct.input.dropdown('year', label='Year', values=range(2008, 2018), help=tip)
@ct.input.text('lon', type=float, label='Longitude', default=-1, help=tip)
@ct.input.text('lat', type=float, label='Latitude', default=51.5, help=tip)
@ct.output.livefigure()
def mean_standard_deviation(
        variable,
        year,
        lon,
        lat,
):
    """
    Application main steps:

    - set application layout
    - retrieve a variable over a defined time range
    - select a subset of the time range (year) and location, defined by longitude and latitude
      coordinates
    - compute monthly and daily averages and their respective standard deviations
    - compare the results as timeseries using the same interactive chart

    """

    data = ct.catalogue.retrieve(
        'reanalysis-era5-single-levels',
        {
            'variable': variables[variable],
            'grid': ['3', '3'],
            'product_type': 'reanalysis',
            'year': [
                '2002', '2003', '2004',
                '2005', '2006', '2007',
                '2008', '2009', '2010',
                '2011', '2012'
            ],
            'month': [
                '01', '02', '03', '04', '05', '06',
                '07', '08', '09', '10', '11', '12'
            ],
            'day': [
                '01', '02', '03', '04', '05', '06',
                '07', '08', '09', '10', '11', '12',
                '13', '14', '15', '16', '17', '18',
                '19', '20', '21', '22', '23', '24',
                '25', '26', '27', '28', '29', '30',
                '31'
            ],
            'time': ['12:00'],
        }
    )
    data_location = ct.geo.extract_point(ct.cube.select(data, time=year), lon=lon, lat=lat)

    monthly_mean = ct.climate.monthly_mean(data_location)
    monthly_std = ct.climate.monthly_std(data_location)
    daily_mean = ct.climate.daily_mean(data_location)
    daily_std = ct.climate.daily_std(data_location)

    fig = ct.chart.line(daily_mean, error_y=daily_std, scatter_dict=dict(name='Daily'),
                        layout_dict={'title': 'Monthly/Daily mean with standard deviation'})
    fig = ct.chart.line(monthly_mean, fig=fig, error_y=monthly_std, scatter_dict=dict(name='Monthly'))
    return fig
