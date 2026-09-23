from pydoc import visiblename
from re import search
import dash_leaflet as dl
import dash_leaflet.express as dlx
import pandas as pd
from dash import Dash, html, dcc, Input, Output, dash_table, ctx
import requests
import urllib3
urllib3.disable_warnings()
import base64
import time
import io
import plotly.express as px
import flask
from plotly.colors import n_colors
import numpy as np
import math 
import random
from flask import send_from_directory
from flask import Flask, request
import dash_bootstrap_components as dbc
import warnings
import os
warnings.filterwarnings('ignore')

server = Flask(__name__)

APP_SUBPATH = (os.environ.get('APP_SUBPATH') or '').strip('/')
subpath_prefix = f"/{APP_SUBPATH}" if APP_SUBPATH else ""

DASHBOARD_ROUTES_PATHNAME_PREFIX = (
    os.environ.get('DASHBOARD_ROUTES_PATHNAME_PREFIX')
    or os.environ.get('DASHBOARD_PATHNAME_PREFIX')
    or '/dashboard/'
)
if not DASHBOARD_ROUTES_PATHNAME_PREFIX.startswith('/'):
    DASHBOARD_ROUTES_PATHNAME_PREFIX = f"/{DASHBOARD_ROUTES_PATHNAME_PREFIX}"
if not DASHBOARD_ROUTES_PATHNAME_PREFIX.endswith('/'):
    DASHBOARD_ROUTES_PATHNAME_PREFIX = f"{DASHBOARD_ROUTES_PATHNAME_PREFIX}/"

default_requests_prefix = f"{subpath_prefix}{DASHBOARD_ROUTES_PATHNAME_PREFIX}"
DASHBOARD_REQUESTS_PATHNAME_PREFIX = (
    os.environ.get('DASHBOARD_REQUESTS_PATHNAME_PREFIX')
    or default_requests_prefix
)
if not DASHBOARD_REQUESTS_PATHNAME_PREFIX.startswith('/'):
    DASHBOARD_REQUESTS_PATHNAME_PREFIX = f"/{DASHBOARD_REQUESTS_PATHNAME_PREFIX}"
if not DASHBOARD_REQUESTS_PATHNAME_PREFIX.endswith('/'):
    DASHBOARD_REQUESTS_PATHNAME_PREFIX = f"{DASHBOARD_REQUESTS_PATHNAME_PREFIX}/"

# Backward compatibility alias
DASHBOARD_PATHNAME_PREFIX = DASHBOARD_REQUESTS_PATHNAME_PREFIX

# If APP_SUBPATH is provided, use it as default static site URL unless STATIC_SITE_BASE_URL is explicitly non-default
configured_static = (os.environ.get('STATIC_SITE_BASE_URL') or '').strip()
if APP_SUBPATH and (not configured_static or configured_static == 'http://localhost:8000'):
    STATIC_SITE_BASE_URL = subpath_prefix
else:
    STATIC_SITE_BASE_URL = (configured_static or 'https://app-siagro.conabio.gob.mx/maices').rstrip('/')

#Query para obtener cada uno de los distintos taxones
my_query= """{
  taxons(pagination:{limit:200} search:{field:estatus value:"aceptado" operator:eq} order:{field:taxon order:ASC}){
    taxon
    taxon_id
    categoria
    estatus
  }
}
"""
url="https://maices-siagro.conabio.gob.mx/graphql"
statusCode = 200

def run_query(uri, query, statusCode, retries=5, backoff_seconds=2):
    # Retries absorb transient DNS/network hiccups seen at container startup (e.g. aardvark-dns).
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            request = requests.post(uri, json={'query': query}, verify=False, timeout=(5, 30))
        except requests.exceptions.RequestException as exc:
            last_error = exc
        else:
            if request.status_code == statusCode:
                return request.json()
            last_error = Exception(f"Unexpected status code returned: {request.status_code}")
        if attempt < retries:
            time.sleep(backoff_seconds * attempt)
    raise last_error


result = run_query(url, my_query, statusCode)

taxons = [taxon for taxon in result['data']['taxons']]
# for i in range (len(result['data']['taxons'])):
#     taxons.append(result['data']['taxons'][i])

df_taxons=pd.DataFrame.from_dict(taxons)
complete_csv = pd.read_csv('./assets/data/occurrence.csv')
# Se eliminan taxones repetidos
df_taxons = df_taxons.drop(df_taxons['taxon'].loc[df_taxons['taxon']=='Zea mays'].index)
df_taxons = df_taxons.drop(df_taxons['taxon'].loc[df_taxons['taxon']=='Zea mays subsp. mays'].index)
df_taxons = df_taxons.drop(df_taxons['taxon'].loc[df_taxons['taxon']=='Zea mays subsp. mexicana raza Durango'].index)
df_taxons = df_taxons.reset_index(drop=True)

def change_taxon (x):
    if x.startswith('Zea mays subsp. mays'):
        start = 'Zea mays subsp. mays'
        y = 'maíz' + x[len(start):]
    elif x.startswith('Zea mays subsp. mexicana'):
        start = 'Zea mays subsp. mexicana'
        y = 'teocintle subespecie mexicana' + x[len(start):]
    elif x.startswith('Zea mays subsp. parviglumis'):
        start = 'Zea mays subsp. parviglumis'
        y = 'teocintle subespecie parviglumis' + x[len(start):]
    return y

df_taxons['taxon simple']=df_taxons['taxon'].apply(change_taxon)
df_taxons = df_taxons.drop(df_taxons['taxon simple'].loc[df_taxons['taxon simple']=='teocintle subespecie mexicana'].index)
df_taxons = df_taxons.drop(df_taxons['taxon simple'].loc[df_taxons['taxon simple']=='teocintle subespecie parviglumis'].index)
df_taxons = df_taxons.reset_index(drop=True)

# Número de tablas de localidad a mostrar por taxón (por defecto 10, ver TAXON_TABLE_LIMITS.get abajo).
TAXON_TABLE_LIMITS = {
    '79259ANGIO': 2,
    '79268ANGIO': 6,
}


def categorize_altitud(x):
    if x < 1200:
        return 'bajas'
    elif x < 1800:
        return 'mediana altitud'
    return 'altas'


def categorize_temperatura(x):
    if x < 18:
        return 'fría'
    elif x <= 21:
        return 'templada'
    elif x <= 25:
        return 'semi-caliente'
    elif x <= 27:
        return 'caliente'
    return 'muy caliente'


def categorize_precipitacion(x):
    if x < 450:
        return 'escasas'
    elif x <= 650:
        return 'poco abundantes'
    elif x <= 850:
        return 'intermedias'
    elif x <= 1360:
        return 'abundantes'
    return 'muy abundantes'


def resolve_taxon_id(value, pathname, df_taxons_local, pathname_prefix):
    if value is not None:
        return df_taxons_local.loc[df_taxons_local['taxon simple'] == value, 'taxon_id'].values[0]
    if pathname and "id=" in pathname:
        taxon_id = pathname.split("id=", 1)[1]
    else:
        taxon_id = pathname.replace(f"{pathname_prefix}id=", "") if pathname else ""
    print(f"Resolved taxon_id from pathname: {taxon_id}")
    return taxon_id


def compute_condition_stats(series, categorize_fn):
    """Devuelve (categoria_media, mínimo, máximo); '(no disponible)' si la serie está vacía."""
    if series.isnull().sum() == len(series):
        return '(no disponible)', '(no disponible)', '(no disponible)'
    return categorize_fn(series.mean()), round(series.min()), round(series.max())


def compute_promedio(df, column):
    valid = df[df[column] != 'no disponible'].copy()
    valid[column] = pd.to_numeric(valid[column], errors='coerce')
    if len(valid) != 0:
        return round(valid[column].mean())
    return '(no disponible)'


def build_colores_text(color_grano_series):
    colores = []
    for raw in color_grano_series:
        cleaned = raw.replace("['", "").replace("']", "").replace("', '", ",")
        colores.extend(cleaned.split(","))

    colores_maices = 'los colores: '
    for color in set(colores):
        if color == 'no disponible' or len(color) < 4:
            continue
        colores_maices = colores_maices + color + ', '
    colores_maices = colores_maices[:-2]
    return colores_maices, len(colores_maices) != 11


def build_mazorca_texto(colores_maices, has_colores, promedio_hileras, promedio_longitud):
    hileras_disponible = promedio_hileras != '(no disponible)'
    longitud_disponible = promedio_longitud != '(no disponible)'

    if not has_colores and not hileras_disponible and not longitud_disponible:
        return ''
    if not has_colores and hileras_disponible and longitud_disponible:
        return f'En esta raza se han encontrado mazorcas que en promedio tienen {promedio_hileras} hileras por mazorca y una longitud de {promedio_longitud} cm.'
    if has_colores and hileras_disponible and longitud_disponible:
        return f'En esta raza se han encontrado {colores_maices}; en mazorcas que en promedio tienen {promedio_hileras} hileras por mazorca y una longitud de {promedio_longitud} cm.'
    if has_colores and not hileras_disponible and longitud_disponible:
        return f'En esta raza se han encontrado {colores_maices} y una longitud de {promedio_longitud} cm.'
    if has_colores and not hileras_disponible and not longitud_disponible:
        return f'En esta raza se han encontrado {colores_maices}.'
    return ''


def build_summary_texto(value, escala_altitud, min_altitud, max_altitud,
                         escala_temperatura, min_temperatura, max_temperatura,
                         escala_precipitacion, min_precipitacion, max_precipitacion):
    verbo = 'crece' if 'teocintle' in value else 'se cultiva'
    verbo_cap = 'Crece' if 'teocintle' in value else 'Se cultiva'
    return f'''El {value} {verbo} en general en tierras {escala_altitud} desde {min_altitud:,} hasta {max_altitud:,} metros sobre el nivel del mar (msnm). 
            {verbo_cap} en lugares donde durante la época de temporal la temperatura es {escala_temperatura}, con temperaturas que van desde {min_temperatura} °C hasta {max_temperatura} 
            ºC y donde las lluvias son {escala_precipitacion}, con cantidades que van desde {min_precipitacion} mm hasta {max_precipitacion} mm.'''


def build_locality_row(df, i):
    encabezado = df['estado'][i] + ", " + df['municipio'][i] + ", " + df['localidad'][i].upper()
    fila = pd.DataFrame({
        "Condición": ["Altitud", "Temperatura", "Precipitación"],
        "Medida": [[df['altitud'][i], " msnm"], [df['temperatura'][i], " °C"], [df['precipitacion'][i], " mm"]],
        "Categoría": [df['cat_altitud'][i], df['cat_temperatura'][i], df['cat_precipitacion'][i]],
    })
    return encabezado, fila


def build_localidad_components(lista, encabezados, taxon_id):
    limite = min(TAXON_TABLE_LIMITS.get(taxon_id, 10), len(lista))
    children = []
    for i in range(limite):
        children.append(dcc.Markdown(f'''**{encabezados[i]}**'''))
        children.append(dbc.Table.from_dataframe(lista[i], striped=True, bordered=True, hover=True, style={'background-color':'white'}))
    return tuple(children)


def make_layout ():
    host = flask.request.host_url if flask.has_request_context() else ''
    return html.Div([
        dcc.Location(id='url', refresh=False),
        dbc.NavbarSimple(
            
            children=[
                dbc.NavItem(dbc.NavLink("Home", href=f"{STATIC_SITE_BASE_URL}/" if STATIC_SITE_BASE_URL else "/", style={'padding-left':'10px','margin-top':'5px','margin-bottom':'5px'})),
                dbc.NavItem(dbc.NavLink("Mapa", href=f"{DASHBOARD_REQUESTS_PATHNAME_PREFIX}", active=True, style={'padding-left':'10px','margin-top':'5px','margin-bottom':'5px',})),
                dbc.NavItem(dbc.NavLink("Ayuda", href=f"{STATIC_SITE_BASE_URL}/#ayuda" if STATIC_SITE_BASE_URL else "/#ayuda", style={'padding-left':'10px','margin-top':'5px','margin-bottom':'5px'})),
                dbc.NavItem(dbc.NavLink("Créditos", href=f"{STATIC_SITE_BASE_URL}/#creditos" if STATIC_SITE_BASE_URL else "/#creditos", style={'padding-left':'10px','margin-top':'5px','margin-bottom':'5px'})),
                
            ],
            color="dark",
            dark=True,
            fixed= "top",
            class_name="pill",
            links_left=True,
        ),
        html.Div([
            html.H2('Condiciones climáticas de las razas de maíz nativo y teocintles en México', style={'textAlign': 'center', 'color': '#343a40', 'font-family': ['system-ui','-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol']}),
            html.Div(dcc.Dropdown(df_taxons['taxon simple'].unique(), id='pandas-dropdown-2', placeholder='Selecciona un tipo de maiz'),style={'margin-top':'20px','cursor':'pointer'}),
            dcc.RadioItems(
                options=[
                {'label' : ' Altitud ', 'value' : 'altitud'},
                {'label' : ' Temperatura ', 'value' : 'temperatura'},
                {'label' : ' Precipitación ', 'value' : 'precipitacion'},
                ], value='altitud', id='radio-conditions', style={'textAlign':'center','margin-top':'20px'}),
            dcc.Graph(id='mapa'),
            html.H3('Distribución de los puntos de colecta sobre las condiciones ambientales:', style={'textAlign': 'center', 'color': '#343a40','margin-top':'20px','font-family': ['system-ui','-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol']}),
            dcc.Graph(id='strip'),
        ],style={'background-color':'rgba(254, 254, 255, 0.7)','padding':'30px'}),
        
    dcc.Loading(id= 'loading-1', type='dot', 
    children=html.Div(id='loading-output-1',style={'background-color':'#2A3C24','padding':'30px', 'color': 'white'}), 
    fullscreen= True),
    html.Div([
                'Aquí presentamos algunas localidades con sus condiciones, pero puedes descargar las localidades completas dando clic en el botón: ',
                html.Br(),
                html.Br(),
                html.Div(dbc.Button("Descargar tabla completa", id="btn_csv", className="me-1", n_clicks=0, style={'background-color':'#6F8A67','border-color':'#6F8A67'}), className="d-grid gap-2 col-6 mx-auto"),
                dcc.Store(id='intermediate-value'),
                dcc.Download(id="download-dataframe-csv"),],id='divButton', style={'background-color':'#2A3C24','padding':'30px','padding-top':'0px', 'color': 'white', 'display': 'none' }),
    
    html.Div(id='pandas-output-container-2',style={'background-color':'#2A3C24','padding':'30px', 'padding-top':'0px','color': 'white'}),
    html.Div([
                'Aquí presentamos algunas localidades con sus condiciones, pero puedes descargar las localidades completas dando clic en el botón: ',
                html.Br(),
                html.Br(),
                html.Div(dbc.Button("Descargar tabla completa", id="btn_csv_down", className="me-1", n_clicks=0, style={'background-color':'#6F8A67','border-color':'#6F8A67'}), className="d-grid gap-2 col-6 mx-auto"),
                #dcc.Store(id='intermediate-value'),
                #dcc.Download(id="download-dataframe-csv"),
                ],id='divDown', style={'background-color':'#2A3C24','padding':'30px','padding-top':'0px', 'color': 'white', 'display': 'none' }),    
    dcc.Loading(id= 'loading-2', type='dot', 
    children=html.Div(id='loading-output-2',style={'background-color':'#2A3C24','padding':'30px', 'color': 'rgb(42, 60, 36)'}), 
    fullscreen= True)
    
],style={'background-image':f'url("{app.get_asset_url("images/focales.jpg")}")','width':'102%','height':'100%','background-attachment': 'fixed','margin-top':'5px','margin-left':'-10px','margin-bottom':'-10px', 'padding-top':'50px'})

app = Dash(
    server=server,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    routes_pathname_prefix=DASHBOARD_ROUTES_PATHNAME_PREFIX,
    requests_pathname_prefix=DASHBOARD_REQUESTS_PATHNAME_PREFIX,
)
# WSGI entrypoint used by Gunicorn (`gunicorn app:server`).
server = app.server
app.title = 'Mapa SIAgro' 
app.layout = make_layout

@app.callback(Output("url", "pathname"), [Input("pandas-dropdown-2", "value"),Input('url', 'pathname')])
def update_url_on_dropdown_change(dropdown_value,pathname):

    if pathname != "/" and dropdown_value is None:
        pathname=pathname[0:]
        url_taxon=pathname
    if pathname=="/":
        url_taxon=''
    if dropdown_value is not None:
        taxon_id=df_taxons.loc[df_taxons['taxon simple']== dropdown_value, 'taxon_id'].values[0]
        url_taxon=f"{DASHBOARD_REQUESTS_PATHNAME_PREFIX}id={taxon_id}"
    
    return url_taxon

@app.callback(Output('intermediate-value', 'data'),Output("divButton", "style"),Output("divDown", "style"),Output('pandas-dropdown-2', 'value'),Output("loading-output-1", "children"),Output("pandas-output-container-2","children"), [Input("btn_csv", "n_clicks"),Input("btn_csv_down", "n_clicks"),Input("pandas-dropdown-2", "value"),Input('url', 'pathname')],prevent_initial_call=True,)
#Función para el texto y la tabla 
def update_output(n_clicks,n_clicks2,value,pathname):
    visible_style = {'background-color':'#2A3C24','padding':'30px','padding-top':'0px', 'color': 'white','display': 'block'}

    if (value is not None) or (value is None and pathname and "id=" in pathname):
        print(f"Dropdown value: {value}, Pathname: {pathname}")
        taxon_id = resolve_taxon_id(value, pathname, df_taxons, DASHBOARD_REQUESTS_PATHNAME_PREFIX)

        df_taxon=complete_csv.loc[complete_csv['taxon_id'] == taxon_id]
        if df_taxon.empty:
            print(f"No data found for taxon_id: {taxon_id}")
        df=df_taxon.filter(items=['taxon','altitud','estado','municipio','localidad','precipitacion','temperatura','color_grano','hileras_mazorca','longitud_promedio'])
        df=df.reset_index()
        value = df['taxon'][0]

        value = change_taxon(value)
        # value = value.replace("Zea mays subsp. mays", "maíz")
        # value = value.replace("Zea mays subsp. mexicana", "teocintle subespecie mexicana")
        # value = value.replace("Zea mays subsp. parviglumis", "teocintle subespecie parviglumis")

        df['cat_altitud'] = df['altitud'].apply(categorize_altitud)
        escala_altitud = categorize_altitud(df['altitud'].mean())
        min_altitud = df['altitud'].min()
        max_altitud = df['altitud'].max()

        df['cat_temperatura'] = df['temperatura'].apply(categorize_temperatura)
        escala_temperatura, min_temperatura, max_temperatura = compute_condition_stats(df['temperatura'], categorize_temperatura)

        df['cat_precipitacion'] = df['precipitacion'].apply(categorize_precipitacion)
        escala_precipitacion, min_precipitacion, max_precipitacion = compute_condition_stats(df['precipitacion'], categorize_precipitacion)

        promedio_hileras = compute_promedio(df, 'hileras_mazorca')
        promedio_longitud = compute_promedio(df, 'longitud_promedio')

        colores_maices, has_colores = build_colores_text(df['color_grano'])
        texto = build_mazorca_texto(colores_maices, has_colores, promedio_hileras, promedio_longitud)

        df = df.round()

        rangei = min(len(df), 10)
        lista, encabezados = [], []
        for i in range(rangei):
            encabezado, fila = build_locality_row(df, i)
            lista.append(fila)
            encabezados.append(encabezado)

        texto_se_cultiva = build_summary_texto(
            value, escala_altitud, min_altitud, max_altitud,
            escala_temperatura, min_temperatura, max_temperatura,
            escala_precipitacion, min_precipitacion, max_precipitacion,
        )

        localidad_components = build_localidad_components(lista, encabezados, taxon_id)

        return (
            df.to_json(date_format='iso', orient='split'),
            visible_style,
            visible_style,
            value,
            (dcc.Markdown(f'''{texto_se_cultiva}'''), dcc.Markdown(f'''{texto}''')),
            localidad_components,
        )
    else:
        texto="Selecciona una raza en el menú desplegable al inicio de la página"
        texto2=""
        dftest = pd.DataFrame({"a": [1, 2, 3, 4], "b": [2, 1, 5, 6], "c": ["x", "x", "y", "y"]})

        return (dftest.to_json(date_format='iso', orient='split')),{'display': 'none'},{'display': 'none'},value, dcc.Markdown(f'''{texto}'''),dcc.Markdown(f'''{texto2}''')       
    

@app.callback(
    Output("download-dataframe-csv", "data"),
    [Input('intermediate-value', 'data'),Input("btn_csv", "n_clicks"),Input("btn_csv_down", "n_clicks"),Input("pandas-dropdown-2", "value"),],
    prevent_initial_call=True,
)
def func(data,n_clicks,n_clicks2,value):
    dff = pd.read_json(io.StringIO(data), orient='split')

    if "btn_csv" == ctx.triggered_id or "btn_csv_down" == ctx.triggered_id:
        dff['raza']=value
        dff = dff[['raza','estado','municipio','localidad','altitud','precipitacion','temperatura','color_grano','hileras_mazorca','longitud_promedio','cat_altitud','cat_temperatura','cat_precipitacion']]
        dff = pd.concat([dff[col].astype(str).str.lower() for col in dff.columns], axis=1)
        nombre=value+".csv"
        return (dcc.send_data_frame(dff.to_csv, nombre,index=False))

    
    

@app.callback(
    Output(component_id='mapa', component_property='figure'),
    Output(component_id='strip', component_property='figure'),
    Output(component_id='loading-output-2', component_property='children'),
    [Input(component_id='pandas-dropdown-2', component_property='value'),
    Input(component_id='radio-conditions', component_property='value'),
    Input('url', 'pathname')]
)
#Función para el mapa 
def update_map(column_chosen, condition_chosen, pathname):
    if condition_chosen == 'altitud':
        image = './assets/images/altitud.png'
        color_scale = 'turbid'
        x_max = 3400
    elif condition_chosen == 'temperatura':
        image = './assets/images/temperatura.png'
        color_scale = 'balance'
        x_max = 40
    elif condition_chosen == 'precipitacion':
        image = './assets/images/precipitacion.png'
        color_scale = 'YlGnBu'
        x_max = 1500
    x_min= 0
    fondo = base64.b64encode(open(image, 'rb').read())

    if column_chosen is None:
        print(f"Dropdown value: {column_chosen}, Pathname: {pathname}")
        #print("entro a is none")
        # complete_dict={"lat": "0","lon": "0"}
        # fig1 = px.scatter_map(lat=['21.826080'],lon=['-101.460875'],zoom=4, height=500,color_discrete_sequence=['black'])
        fig1 = px.scatter_map(center={'lat': 21.826080, 'lon': -101.460875},zoom=3, height=500,color_discrete_sequence=['black'], map_style="carto-darkmatter")
        
        # fig1.update_layout(mapbox_style="carto-darkmatter")#stamen-terrain, carto-positron, open-street-map, carto-darkmatter
        fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig1.update_layout(height= 300)
        fig1.update_coloraxes(showscale=False)
        fig2 = px.scatter(x=[0], y=[1],color_discrete_sequence=['white']) 
        fig2.update_layout(margin={"r":20,"t":40,"l":20,"b":40})
        fig2.update_layout(height= 200)
        fig2.update_yaxes(showgrid=False, zeroline=False, visible= False)
        fig2.add_layout_image(
            dict(
                source='data:image/png;base64,{}'.format(fondo.decode()),
                xref="paper", yref= 'paper',
                x=0, y=1,
                sizex=1, sizey=1, #sizex, sizey are set by trial and error
                xanchor="left",
                yanchor="top",
                sizing="stretch",
                opacity= 0.9,
                layer="below")
            )    

        return fig1, fig2, pathname

    if column_chosen is not None:
        print(f"Column value: {column_chosen}, Pathname: {pathname}")
        
        taxon_id=df_taxons.loc[df_taxons['taxon simple']== column_chosen, 'taxon_id'].values[0]
        
        complete_csv = pd.read_csv('./assets/data/occurrence.csv')
        
        df_taxon=complete_csv.loc[complete_csv['taxon_id'] == taxon_id]
        df=df_taxon.filter(items=['taxon','latitud', 'longitud', 'altitud', 'estado', 'municipio', 'localidad', 'temperatura', 'precipitacion'])
        df['temperatura']= df['temperatura'].round()
        df['precipitacion']= df['precipitacion'].round()
        fig1 = px.scatter_map(df, lat="latitud", lon="longitud", hover_data={'latitud':False, 'longitud':False, 'estado':True, 'municipio':True}, color = condition_chosen,
                                color_continuous_scale=color_scale, zoom=3, height=500, range_color = (x_min, x_max),center={'lat': 21.826080, 'lon': -101.460875}, map_style="carto-darkmatter")
        # fig1.update_layout(mapbox_style="carto-darkmatter")#stamen-terrain, carto-positron, open-street-map, carto-darkmatter
        fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig1.update_layout(height= 300)
        fig1.update_coloraxes(showscale=False)

        random_num = []
        random.seed(0)
        for i in range(len(df)):
            random_num.append(random.uniform(0.7, 1.5))

        df['random']=random_num

        fig2 = px.scatter(df, x=condition_chosen, y="random", hover_data={'random':False, 'estado':True, 'municipio':True},range_x= (x_min, x_max), range_y = (0.3, 2), color_discrete_sequence=n_colors('rgb(0, 0, 0)', 'rgb(255, 255, 255)', 4, colortype = 'rgb')) 

        #fig2 = px.strip(df, x=condition_chosen, stripmode='group', range_x= (x_min, x_max), color_discrete_sequence=n_colors('rgb(0, 0, 0)', 'rgb(255, 255, 255)', 4, colortype = 'rgb'))
        fig2.update_layout(margin={"r":20,"t":40,"l":20,"b":40})
        fig2.update_layout(height= 200)
        fig2.update_yaxes(showgrid=False, zeroline=False, visible= False)
        fig2.add_layout_image(
            dict(
                source='data:image/png;base64,{}'.format(fondo.decode()),
                xref="paper", yref= 'paper',
                x=0, y=1,
                sizex=1, sizey=1, #sizex, sizey are set by trial and error
                xanchor="left",
                yanchor="top",
                sizing="stretch",
                opacity= 0.9,
                layer="below")
            )    
        return fig1, fig2, pathname


if __name__ == "__main__":
    app.run(host=os.environ.get('HOST', '127.0.0.1'), port=int(os.environ.get('PORT', 8050)), debug=bool(os.environ.get('DASH_DEBUG')))
