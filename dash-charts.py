import pandas as pd
from influxdb_client import InfluxDBClient
import seaborn as sns
import matplotlib.pyplot as plt

import dash
from dash import dcc, html
import plotly.express as px

url = 'http://192.168.254.89:8086'
token = 'root:root'
org = ''
bucket = 'esp2nred'

with InfluxDBClient(url=url, token=token, org=org) as client:
    query_api = client.query_api()
    df = pd.DataFrame(client.query_api().query_data_frame('from(bucket: "esp2nred") |> range(start: -3d) |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'))

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Sample Dash Dashboard"),
    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [1, 2, 3, 4], 'y': [4, 3, 2, 1], 'type': 'bar', 'name': 'A'},
                {'x': [1, 2, 3, 4], 'y': [2, 4, 1, 3], 'type': 'bar', 'name': 'B'},
            ],
            'layout': {
                'title': 'Sample Bar Chart'
            }
        }
    )
])
