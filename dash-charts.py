import pandas as pd
from influxdb_client import InfluxDBClient 
import seaborn as sns
import matplotlib.pyplot as plt

import dash
import dash_bootstrap_components as dbc  # installed dash_bootstrap_templates too
from dash import dcc, html
from dash import dash_table as dt
import plotly.express as px
from dash.dependencies import Input, Output


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
    df = pd.DataFrame(client.query_api().query_data_frame('from(bucket: "esp2nred") |> range(start: -4d) |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'))
    df = df.drop(columns=['result', 'table', '_start', '_stop', '_measurement', 'device'])
    df.to_csv('dht11-temp-data.csv')

# CREATE TABLES/GRAPHS THAT ARE NOT CREATED WITH CALLBACK (not interactive)
# Create summary dataframe with statistics
dfsummary = df.groupby('location')['tempf'].describe()  # describe outputs a dataframe
dfsummary = dfsummary.reset_index()  # this moves the index (locations 1,2,3,4) into a regular column so they show up in the dash table
'''dfsummary.style.format({   # this would work if the values were floats. However they
    "mean": "{:.1f}",         # were strings after the describe functions so had to use
    "std": "{:.1f}",          # the map function below
})'''
dfsummary.loc[:, "mean"] = dfsummary["mean"].map('{:.1f}'.format)
dfsummary.loc[:, "std"] = dfsummary["std"].map('{:.1f}'.format)
dfsummary.loc[:, "50%"] = dfsummary["50%"].map('{:.1f}'.format)
table = dbc.Table.from_dataframe(dfsummary, striped=True, bordered=True, hover=True)

histogram1 = px.histogram(df, x="tempf", nbins=30)

# START DASH AND CREATE LAYOUT OF TABLES/GRAPHS
# Use dash bootstrap components (dbc) for styling
dbc_css = "assets/dbc.css"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR, dbc_css])
# available themes: BOOTSTRAP, CERULEAN, COSMO, CYBORG, DARKLY, FLATLY, JOURNAL, LITERA, LUMEN, LUX, MATERIA, MINTY, MORPH, PULSE, QUARTZ, SANDSTONE, SIMPLEX, SKETCHY, SLATE, SOLAR, SPACELAB, SUPERHERO, UNITED, VAPOR, YETI, ZEPHYR

# Layout of the dash graphs, tables, drop down menus, etc
# Using dbc container for styling/formatting
app.layout = dbc.Container(html.Div([
    html.Div(["Home Temp Data from DHT11 (units are F)",table], style={'display': 'inline-block', 'width': '50%'}),
    html.Div('Sensor location 1:IndoorA 2:Basement 3:IndoorB 4:Outdoors'),
    dcc.Checklist(
        id="checklist",  # id names will be used by the callback to identify the components
        options=["1", "2", "3","4"],
        value=["1", "2", "3", "4"], # default selections
        inline=True),
    html.Div([dcc.Graph(figure={}, id='graph')], style={'display': 'inline-block', 'width': '50%'}),  # figure is blank dict because created in callback below
    html.Div([dcc.Graph(figure=histogram1, id='hist1')], style={'display': 'inline-block', 'width': '50%'}),
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
    ])
]), fluid=True, className="dbc dbc-row-selectable")

# CREATE INTERACTIVE GRAPHS
@app.callback(
    Output("graph", "figure"),    # args are component id and then component property
    Input("checklist", "value"))  # args are component id and then component property
def update_line_chart(sensor):    # callback function arg 'sensor' refers to the component property of the input or "value" above. If there are multiples it's in order
    mask = df.location.isin(sensor)
    fig = px.line(df[mask], 
        x="_time", y="tempf", color='location')
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
