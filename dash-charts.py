import pandas as pd
from influxdb_client import InfluxDBClient
import seaborn as sns
import matplotlib.pyplot as plt

import dash
from dash import dcc, html
import plotly.express as px
from dash.dependencies import Input, Output

url = 'http://192.168.254.89:8086'
token = 'root:root'
org = ''
bucket = 'esp2nred'

with InfluxDBClient(url=url, token=token, org=org) as client:
    query_api = client.query_api()
    df = pd.DataFrame(client.query_api().query_data_frame('from(bucket: "esp2nred") |> range(start: -3d) |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'))

#print(df)

# https://dash.plotly.com/tutorial

app = dash.Dash(__name__) # Initialize the app

                          # Layout of the graphs, tables, drop down menus, etc
app.layout = html.Div([
    dcc.Graph(figure={}, id='graph'),
    dcc.Checklist(
        id="checklist",  # id names will be used by the callback to identify the components
        options=["1", "2", "3","4"],
        value=["1", "2", "3", "4"], # default selections
        inline=True
    ),
])

@app.callback(
    Output("graph", "figure"),    # args are component id and then component property
    Input("checklist", "value"))  # args are component id and then component property
def update_line_chart(sensor):    # callback function arg 'sensor' refers to the component property of the input or "value" above
    mask = df.location.isin(sensor)
    fig = px.line(df[mask], 
        x="_time", y="tempf", color='location')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
