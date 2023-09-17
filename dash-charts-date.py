import pandas as pd
from influxdb_client import InfluxDBClient 
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import statsmodels.stats.multicomp as multi
import numpy as np

import dash
import dash_bootstrap_components as dbc  # installed dash_bootstrap_templates too
from dash import dcc, html
from dash import dash_table as dt
import plotly.express as px
from dash.dependencies import Input, Output

# Dash apps are Flask apps

# https://dash.plotly.com/tutorial
# https://bootswatch.com/
# https://hellodash.pythonanywhere.com/
# https://hellodash.pythonanywhere.com/adding-themes/datatable
# https://community.plotly.com/t/styling-dash-datatable-select-rows-radio-button-and-checkbox/59466/3

#  IMPORT DATA
# Get offline data for box plot comparison
dfbox = pd.read_csv('dht11-temp-data-boxplot.csv')

# Get data from RPi influxdb server
url = 'http://192.168.254.89:8086'
token = 'root:root'
org = ''
bucket = 'esp2nred'

with InfluxDBClient(url=url, token=token, org=org) as client:
    query_api = client.query_api()
    df = pd.DataFrame(client.query_api().query_data_frame('from(bucket: "esp2nred") |> range(start: -5d) |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'))
    df = df.drop(columns=['result', 'table', '_start', '_stop', '_measurement', 'device'])
    df = df.assign(date=df['_time'].dt.strftime('%Y-%m-%d'))
    df['date'] = pd.to_datetime(df['date'])
    #df.to_csv('dht11-temp-data.csv')

sensor = [i for i in range(4)]
for i in range(4):
    sensor[i] = df[(df['location'] == str(i+1))]

stats_temp = [[x for x in range(2)] for x in range(4)]

'''for i in range(1,4):
    print(stats.levene(sensor[0]['tempf'], sensor[i]['tempf']))
    print(stats.ttest_ind(sensor[0]['tempf'], sensor[i]['tempf'], equal_var=False))'''

Results = multi.pairwise_tukeyhsd(df['tempf'], df['location'], alpha= 0.05)
dftukey = pd.DataFrame(data=Results._results_table.data[1:], columns=Results._results_table.data[0])
dftukey['reject'] = dftukey['reject'].astype(str)
table_tukey = dbc.Table.from_dataframe(dftukey, striped=True, bordered=True, hover=True) # use bootstrap formatting on table
#dt.DataTable(data=dfsummary.to_dict('records'), page_size=10),
#table_tukey = dt.DataTable(data=dftukey.to_dict('records'), columns=[{"name": i, "id": i} for i in df.columns]),


# CREATE TABLES/GRAPHS THAT ARE NOT CREATED WITH CALLBACK (not interactive)
# Create summary dataframe with statistics
dfsummary = df.groupby('location')['tempf'].describe()  # describe outputs a dataframe
dfsummary = dfsummary.reset_index()  # this moves the index (locations 1,2,3,4) into a regular column so they show up in the dash table
'''dfsummary.style.format({   # this would work if the values were floats. However they
    "mean": "{:.1f}",         # were strings after the describe functions so had to use
    "std": "{:.1f}",          # the map function below
})'''
dfsummary.loc[:, "mean"] = dfsummary["mean"].map('{:.1f}'.format)  # format as float. see comment above
dfsummary.loc[:, "std"] = dfsummary["std"].map('{:.1f}'.format)
dfsummary.loc[:, "50%"] = dfsummary["50%"].map('{:.1f}'.format)
dfsummary = dfsummary.set_index('location').T.rename_axis('location')
dfsummary = dfsummary.reset_index()
print(dfsummary)
table_summary = dbc.Table.from_dataframe(dfsummary, striped=True, bordered=True, hover=True) # use bootstrap formatting on table

histogram1 = px.histogram(df, x="tempf", nbins=30)  # create histogram figure

# START DASH AND CREATE LAYOUT OF TABLES/GRAPHS
# Use dash bootstrap components (dbc) for styling
dbc_css = "assets/dbc.css"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE, dbc_css])
# available themes: BOOTSTRAP, CERULEAN, COSMO, CYBORG, DARKLY, FLATLY, JOURNAL, LITERA, LUMEN, LUX, MATERIA, MINTY, MORPH, PULSE, QUARTZ, SANDSTONE, SIMPLEX, SKETCHY, SLATE, SOLAR, SPACELAB, SUPERHERO, UNITED, VAPOR, YETI, ZEPHYR


# Layout of the dash graphs, tables, drop down menus, etc
# Using dbc container for styling/formatting
app.layout = dbc.Container(html.Div([
    html.Div(["Home Temp Data from DHT11 (units are F)",table_summary], style={'display': 'inline-block', 'width': '48%'}),
    html.Div(" ", style={'display': 'inline-block', 'width': '2%'}),
    html.Div(["Tukey HSD 1:IndoorA 2:Basement 3:IndoorB 4:Outdoors",table_tukey], style={'display': 'inline-block', 'width': '48%'}),
    html.Div([
    html.P("y-axis:"),
    dcc.RadioItems(
        id='y-axis', 
        options=[{'value': x, 'label': x} 
                 for x in ['humidityi', 'tempf']],
        value='tempf', 
        labelStyle={'display': 'inline-block'}
    ),
    html.Div([dcc.Graph(figure={}, id="box-plot1")], style={'display': 'inline-block', 'width': '50%'}),
    html.Div([dcc.Graph(figure={}, id="box-plot2")], style={'display': 'inline-block', 'width': '50%'}),
    ]),
    html.Div(["Date Range",
    dcc.DatePickerRange(
        id="date-range",
        min_date_allowed=df["date"].min().date(),
        max_date_allowed=df["date"].max().date(),
        start_date=df["date"].min().date(),
        end_date=df["date"].max().date(),
    )], style={'display': 'inline-block', 'width': '33%'}),
    html.Div('Sensor location 1:IndoorA 2:Basement 3:IndoorB 4:Outdoors'),
    dcc.Checklist(
        id="checklist",  # id names will be used by the callback to identify the components
        options=["1", "2", "3","4"],
        value=["1", "2", "3", "4"], # default selections
        inline=True),
    html.Div([dcc.Graph(figure={}, id='linechart1')], style={'display': 'inline-block', 'width': '50%'}),  # figure is blank dict because created in callback below
    html.Div([dcc.Graph(figure=histogram1, id='hist1')], style={'display': 'inline-block', 'width': '50%'}),
]), fluid=True, className="dbc dbc-row-selectable")

# CREATE INTERACTIVE GRAPHS
@app.callback(
    Output("linechart1", "figure"),    # args are component id and then component property
    Input("checklist", "value"),        # args are component id and then component property. component property is passed
    Input("date-range", "start_date"),  # in order to the chart function below
    Input("date-range", "end_date"))
def update_line_chart(sensor, start_date, end_date):    # callback function arg 'sensor' refers to the component property of the input or "value" above
    filtered_data = df.query("date >= @start_date and date <= @end_date")
    mask = filtered_data.location.isin(sensor)
    fig = px.line(filtered_data[mask], 
        x='_time', y='tempf', color='location')
    return fig

@app.callback(
    Output("box-plot1", "figure"), 
    Input("y-axis", "value"))
def generate_chart(y):
    fig = px.box(dfbox, x="location", y=y, color="ventilator")
    return fig

@app.callback(
    Output("box-plot2", "figure"), 
    Input("y-axis", "value"))
def generate_chart(y):
    fig = px.box(dfbox, x="location", y=y, color="Outside-humidity")
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)

# Other ways to modify layout
    #dbc.Container([table], className="m-4 dbc"),
    #dt.DataTable(data=dfsummary.to_dict('records'), page_size=10),
    #dt.DataTable(data=df.describe(), columns=[{"name": i, "id": i} for i in df.describe().columns]),
