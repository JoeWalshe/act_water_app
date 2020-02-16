import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pandas as pd
from sodapy import Socrata
import plotly.express as px
#import plotly.io as pio
#pio.templates.default = 'plotly_dark'

# unauthenticated connection to Open Data Portal
# use app token as second argument to avoid throttling
client = Socrata("www.data.act.gov.au", None)

# Read monitoring site information from open data platform
results = client.get("tsq4-63ge", limit=100)
sites_df = pd.DataFrame.from_records(results)
sites_df[['latitude','longitude','elevation']] = sites_df[['latitude','longitude','elevation']].apply(pd.to_numeric, errors='coerce')
sites_df['type'] = [number[:3] for number in sites_df['siteid']]

sensor_data = pd.read_csv('2019_ACT_Daily_Rainfall_and_Streamflow.csv')
sensor_data.DatetimeAEST = pd.to_datetime(sensor_data.DatetimeAEST)

streamflow_data = sensor_data[sensor_data.VariableName=='Stream Discharge Ml/Day']
#streamflow_sites = streamflow_data.SiteID.unique()
streamflow_sites = sites_df[sites_df['type']=='410']
streamflow_options = [{'label':sitename, 'value':site} for sitename,site in streamflow_sites[['sitename','siteid']].values]

rainfall_data = sensor_data[sensor_data.VariableName=='Rainfall']
#rainfall_sites = rainfall_data.SiteID.unique()
rainfall_sites = sites_df[sites_df['type']=='570']
rainfall_options = [{'label':sitename, 'value':site} for sitename,site in rainfall_sites[['sitename','siteid']].values]

px.set_mapbox_access_token(open('mapbox_token.txt').read())

site_map = px.scatter_mapbox(
    sites_df,
    lat = 'latitude',
    lon = 'longitude',
    hover_name = 'sitename',
    #size = 'elevation' #must use df.dropna()
    color = 'type',
    height = 800
)

line_graph_height = 400

streamflow_line = px.line(title='Streamflow', height=line_graph_height)
rainfall_line = px.line(title='Rainfall', height=line_graph_height)


#external_stylesheets = ['https://codepen.io/anon/pen/mardKv.css']
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#theme = {'dark':True}
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div(children=[
    # Heading across the whole page
    html.H1(children='ACT Government Water Monitoring Sites'),
    html.A("Code available on GitHub", href='https://github.com/JoeWalshe/act_water_app', target="_blank"),
    
    # Div to set up two columns
    html.Div(children=[
        # Div to contain first column
        html.Div(children=[
            dcc.Graph(
                id='site-map',
                figure=site_map
            )
        ], className="six columns"),#,style={'width': '48%', 'display': 'inline-block'}),
        #Div to contain second column
        html.Div(children=[
            dcc.Dropdown(
                id='streamflow_dropdown',
                options=streamflow_options,
                value=streamflow_options[0]['value'],
                multi=True
            ),
            dcc.Graph(
                id='streamflow_line',
                figure=streamflow_line
            ),
            dcc.Dropdown(
                id='rainfall_dropdown',
                options=rainfall_options,
                value=rainfall_options[0]['value'],
                multi=True
            ),
            dcc.Graph(
                id='rainfall_line',
                figure=rainfall_line
            )
        ], className="six columns")#,style={'width': '48%', 'display': 'inline-block'})
    ], className="row") #style={'columnCount': 2, 'width': '99%'})

    
])#, style={'width': "100%"})

@app.callback(
    Output('streamflow_line', 'figure'),
    [Input('streamflow_dropdown', 'value')]
)
def update_streamflow(dropdown_value):
    return update_line(dropdown_value, 'Streamflow')

@app.callback(
    Output('rainfall_line', 'figure'),
    [Input('rainfall_dropdown', 'value')]
)
def update_streamflow(dropdown_value):
    return update_line(dropdown_value, 'Rainfall')

def update_line(dropdown_value, variable):
    if not isinstance(dropdown_value, list): 
        dropdown_value = [dropdown_value]
    data = sensor_data[sensor_data.SiteID.isin(dropdown_value)]
    if len(data) > 0: 
        unit = data.Unit.values[0] # assume by now all rows have the same unit
    else:
        unit = ''
    fig = px.line(
        data,
        x='DatetimeAEST', 
        y='Value',
        color='SiteID',
        title=variable + ' at site ' + ', '.join(dropdown_value),
        height=line_graph_height
    )
    fig.update_layout(legend_orientation="h")
    fig.update_layout(yaxis_title=variable + ', ' + unit)
    
    return fig

if __name__=='__main__':
    app.run_server(debug=True)
