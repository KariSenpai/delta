import dash
import pandas as pd
import plotly.express as px
from dash import dcc, html
from .get_data import get_transport_pollution_eu
from urllib.request import urlopen
import json

axisX=html.Div(
[
    html.Div("Catégorie"),
    dcc.RadioItems(
        id="pol-choice",
        options=[
            {"label": "Marque", "value": "Marque"},
            {
                "label": "Hybride",
                "value": "Hybride",
            },
            {"label": "Carburant", "value": "Carburant"},
        ],
        value="Marque",
        labelStyle={"display": "block"},
    ),
],
style={"width": "9em", "padding": "0px 0px 0px 10em"},
)

class Polution:
    years = [x for x in range(1990, 2020)]
    def get_pollution_per_vehicules_in_france(self):
        df = pd.read_csv(
            "data/vehicules_polluant_france_2015.csv", sep=";", encoding="latin1"
        )

        columns_to_keep = [
            "lib_mrq_doss",
            "hc",
            "nox",
            "hcnox",
            "ptcl",
            "co2_mixte",
            "co_typ_1",
            "hybride",
            "energ",
        ]
        df = df[columns_to_keep]
        df.columns = [
            "Marque",
            "Emission HC",
            "Emission NOx",
            "Emission HC et NOx",
            "Emission Particules",
            "Emission CO2",
            "Emission CO type1",
            "Hybride",
            "Carburant",
        ]
        df = transform_energ_names(df, "Carburant")
        df["Hybride"].replace({"non ": False, "oui ": True}, inplace=True)
        return df

    def __init__(self, application=None):
        self.df = self.get_pollution_per_vehicules_in_france()
        self.pollution_eu = get_transport_pollution_eu()

        self.main_layout = html.Div(children=[
                            html.H3(
                    children="Éjection de différents gaz en fonction de la marque en France en 2015"
                ),
                html.Div(
                    [
                        dcc.Graph(id="pol-main-graph"),
                    ],
                    style={
                        "width": "100%",
                    },
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div("Type de gaz"),
                                dcc.RadioItems(
                                    id="pol-type-gaz",
                                    options=[
                                        {"label": "Oxyde d'azote", "value": "NOx"},
                                        {
                                            "label": "Hydrocarbure et Oxyde d'azote",
                                            "value": "HC et NOx",
                                        },
                                        {"label": "Hydrocarbure", "value": "HC"},
                                        {
                                            "label": "Particules fine",
                                            "value": "Particules",
                                        },
                                        {"label": "CO2", "value": "CO2"},
                                        {"label": "CO type1", "value": "CO type1"},
                                    ],
                                    value="NOx",
                                    labelStyle={"display": "block"},
                                    #'Hybride', 'Carburant',
                                ),
                            ],
                            style={"width": "9em"},
                        ),
                        axisX,
                    ],
                    style={
                        "padding": "10px 50px",
                        "display": "flex",
                        "flexDirection": "row",
                        "justifyContent": "flex-start",
                    },
                ),
    html.Br(),
html.H3(children='Pollution des Transports en Europe de 1990 à 2020'),
    html.Div([dcc.Graph(id='pol-main-europe-graph'), ], style={'width' : '100%'}),
    html.Div([
            html.Div([html.Div('Type de Pollution'),
                dcc.RadioItems(
                id='pol-europe-type',
                options=[{'label':'Oxyde d\'azote', 'value':"NOX"}, 
                        {'label':'Composés organiques volatils autre que le méthane','value':"NMVOC"},
                        {'label':'Particules < 10 nanomètres','value':"PM10"}],
                        value="NOX",
                        labelStyle={'display':'block'},
                ),]),
            html.Br(),
            html.Button(
                'Start',
                id='pol-button-start-stop', 
                style={'display':'inline-block'}
                ),
            html.Div()

    ]),
    html.Div([
                html.Div(
                    dcc.Slider(
                            id='pol-europe-year-slider',
                            min=1990,
                            max=2020,
                            step = 1,
                            value=1990,
                            marks={str(year): str(year) for year in self.years[::2]},
                    ),
                    style={'display':'inline-block', 'width':"90%"}
                ),
                dcc.Interval(            # fire a callback periodically
                    id='pol-auto-stepper',
                    interval=1500,       # in milliseconds
                    max_intervals = -1,  # start running
                    n_intervals = 0
                ),
                ], style={
                    'padding': '0px 50px', 
                    'width':'100%'
                }),
    ], style={
            'backgroundColor': 'white',
             'padding': '10px 50px 10px 50px',
             }
        )

        if application:
            self.app = application
        else:
            self.app = dash.Dash(__name__)
            self.app.layout = self.main_layout

        # European Pollution graph
        self.app.callback(
                    dash.dependencies.Output('pol-main-europe-graph', 'figure'),
                    [ dash.dependencies.Input('pol-europe-type', 'value'),
                    dash.dependencies.Input('pol-europe-year-slider', 'value')
                    ])(self.update_graph_poll_eu)
        
        # Button start/stop for europe map
        self.app.callback(
            dash.dependencies.Output('pol-button-start-stop', 'children'),
            dash.dependencies.Input('pol-button-start-stop', 'n_clicks'),
            dash.dependencies.State('pol-button-start-stop', 'children'))(self.button_on_click)
        self.app.callback(
            dash.dependencies.Output('pol-auto-stepper', 'max_interval'),
            [dash.dependencies.Input('pol-button-start-stop', 'children')])(self.run_time)
        self.app.callback(
            dash.dependencies.Output('pol-europe-year-slider', 'value'),
            dash.dependencies.Input('pol-auto-stepper', 'n_intervals'),
            [dash.dependencies.State('pol-europe-year-slider', 'value'),
             dash.dependencies.State('pol-button-start-stop', 'children')])(self.on_interval)
 
        # Cars graph
        self.app.callback(
            dash.dependencies.Output("pol-main-graph", "figure"),
            [
                dash.dependencies.Input("pol-type-gaz", "value"),
                dash.dependencies.Input("pol-choice", "value"),
            ],
        )(self.update_graph_cars)

    def update_graph_cars(self, name, axis):
        col = f"Emission {name}"
        agg = (
            self.df.copy()[[axis, col]]
            .groupby([axis])
            .mean()
            .reset_index()
            .sort_values(by=[col, axis])
            # .replace(np.NaN,0)
        )

        fig = px.bar(
            agg, y=col, x=axis, title=f"Moyenne d'{col} pour les modèles par marque"
        )
        fig.update_traces(
            textfont_size=12, textangle=0, textposition="outside", cliponaxis=False
        )
        return fig

    ## EUROPEAN POLLUTION GRAPH
    # Update function for the European map of pollution
    def update_graph_poll_eu(self, name="NMVOC", year=1990):
        dfg = self.pollution_eu[1]
        dfg = dfg.loc[dfg['Type de pollution'] == name]
        dfg = dfg.loc[dfg['Année'] == year]
        
        countries = json.load(open('SG_AH_emission_de_CO2_des_transports/data/europe_geoson.json'))

        fig = px.choropleth_mapbox(dfg, geojson=countries, 
                           locations='Pays', featureidkey = 'properties.name', # join keys
                           color='Taux de pollution', color_continuous_scale="matter",
                           mapbox_style="carto-positron",
                           zoom=2.5, center = {"lat": 53, "lon": 3},
                           opacity=0.5,
                           labels={'Taux de pollution':'Taux de pollution en %'}
                          )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        return fig
    
    # start and stop the time
    def button_on_click(self, n_clicks, text):
        if text == 'Start':
            return 'Stop'
        else:
            return 'Start'
    
    def run_time(self, text):
        if text == 'Start':
            return 0
        else:
            return -1

    # intervals for years
    def on_interval(self, n_intervals, year, text):
        if text == 'Stop':  # we run
            if year == self.years[-1]:
                return self.years[0]
            else:
                return year + 1
        else:
            return year
    ## END OF FUNCTIONS FOR EUROPEAN POLLUTION GRAPH


def transform_energ_names(df, col):
    energ_name = {
        "ES ": "Essence",
        "GO ": "Gazole",
        "ES/GP ": "Essence ou Gaz de Pétrole Liquéfié",
        "GP/ES ": "Essence ou Gaz de Pétrole Liquéfié",
        "EE ": "Essence Hybride rechargeable",
        "EL ": "Electricité",
        "EH ": "Essence Hybride non rechargeable",
        "GH ": "Gazole Hybride non rechargeable",
        "ES/GN ": "Essence ou Gaz Naturel",
        "GN/ES ": "Essence ou Gaz Naturel",
        "FE ": "Superéthanol",
        "GN ": "Gaz Naturel",
        "GL ": "Gazole Hybride rechargeable",
    }
    df[col].replace(energ_name, inplace=True)
    return df


if __name__ == "__main__":
    pol = Energies()
    pol.app.run_server(debug=True, port=8051)
