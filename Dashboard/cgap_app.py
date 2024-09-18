# Import required libraries
import pandas as pd
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import base64
from io import BytesIO
import dash_bootstrap_components as dbc
import urllib.parse
from dash.exceptions import PreventUpdate

import openpyxl 

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
# Define the layout of the app
app.layout = dbc.Container(
    fluid=True,
    style={'backgroundColor': '#48A0E8'},
    children=[
        dbc.Row(
            dbc.Col(html.H1('cGAP APP', className='text-center mb-4'), width=10)
        ),
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        dcc.Markdown('''
                          This app takes as input the excel file "*Master GAP Table with revised GAPs*" provided by the regional regulatory managers,
                                      in which there are each of the requested GAPs by country, crop and product. 
                                     
                            This app identifies among all these GAPs, the most critical GAP 
                                     by formulation (J-neck) / by regulatory zone (G-collar) / by crop (O-collar). 
                                     
                             As for crops, for cereals, we disgard rye, triticale, spelt, oat , and we group together the some crops (eg Barley: spring & winter) and  (eg wheat : durum, spring, winter).
                                      The crop groups include 'Barley' , 'Wheat', 'Cabbage' , 'Onion' and 'Rape'.
                                     
                            Here are the 5 criteria used to define the most critical GAP:
                                     
                                        - 1 - Application rate PTZ (g/ha), higher is the most critical
                                        - 2 - Nb of application , the highest is the most critical #(the g/ha for multiple Nb of app in not yet evaluated)
                                        - 3 - BBCH stage the latest, max is the most critical
                                        - 4 - The shortest PHI (PHI): smaller  is the most critical
                                        - 5 - Interval between applications, the smallest interval is the most critical     
                                                                ''') ,
                    ]),
                    className="mb-3",
                    style={'backgroundColor': '#61ADEB'} 
                ),
                #width={'size': 8, 'offset': 3}  # Center the card on the page
            )
        ),


        dbc.Row(
            dbc.Col(
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center'
                    },
                    multiple=False
                ),
                width=12
            )
        ),
        dbc.Row(
            dbc.Col(
                html.Div(id='filtered-table', style={'marginTop': '30px'}),
                #width={'size': 8, 'offset': 3}
            )
        ),
         # Add the download button and link container
        html.Div([
            dbc.Button('Download Data', id='download-button', color='primary', className='mt-3'),
            dcc.Download(id='download-dataframe-csv'),
            html.Div(id='download-link-container')
        ])


    ]
)


# Callback to handle the file upload and display the data
@app.callback(
    Output('filtered-table', 'children'),
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_output(contents, filename):
    global critical_values
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Read the Excel file into a pandas DataFrame, selecting the specified sheet and skipping rows
        df = pd.read_excel(BytesIO(decoded), sheet_name='MasterGAP', skiprows=6)
        # Update the column name to replace '\n' with a space
        
        # Select specific columns from the dataframe
        cgap_df = df[['Product\n(PLT short)','Regulatory Zone','Crop','applicationn timing BBCH end','Max # of applns.\n(per block)','Application rate PTZ (g/ha)',
                        'PHI', 'Minimum appl. interval\n(days)','Maximum appl. interval\n(days)']]
        cgap_df.columns = cgap_df.columns.str.replace('\n', '')


        print(cgap_df.columns)
        # Remove rows containing specific crops
        cgap_df['Crop'] = cgap_df['Crop'].fillna('') 
        cgap_df = cgap_df[~cgap_df['Crop'].str.contains('rye|triticale|spelt|oat', case=False)]

        # Define a function to simplify crop names
        def simplify_crops(crop):
            crop_list = ['Barley', 'Wheat','Cabbage','Onion','Rape']  # Uppercase sensitive
            for item in crop_list:
                if item in crop:
                    return item
            return crop

        # Apply the simplify_crops function to the 'Crop' column
        cgap_df['Crop'] = cgap_df['Crop'].apply(simplify_crops)
        print(cgap_df['Crop'].unique())
        try:
             # Group the dataframe to find critical values
            critical_values = cgap_df.groupby(['Regulatory Zone','Product(PLT short)','Crop','Max # of applns.(per block)']).agg({'Application rate PTZ (g/ha)': 'max',
                                                                                        'applicationn timing BBCH end':'max',
                                                                                        'PHI':'min',
                                                                                        'Minimum appl. interval(days)':'min'}).reset_index()
            #critical_values.columns = critical_values.columns.str.replace('[^\w\s]', '').str.replace(' ', '_')


            # Display the filtered dataframe using dash_table.DataTable
            return dash_table.DataTable(
                id='filtered-table',
                columns=[{'name': col, 'id': col} for col in critical_values.columns],
                data=critical_values.to_dict('records'),
                style_table={
                    'overflowX': 'scroll',
                    'overflowY': 'scroll',
                    'maxHeight': '100vh',
                    'height': '80%',
                    'minWidth': '100%'
                },
                style_cell={
                    'minWidth': '80px', 'maxWidth': '180px', 'whiteSpace': 'normal',
                    'fontSize': '10px'
                },
                style_header={
                    'backgroundColor':'#f9f9f9',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'textAlign': 'center',
                    'maxWidth': '200px',
                    'fontSize': '12px'
                },
                page_action='none',
                fixed_rows={'headers': True}
            )
        except Exception as e:
            return html.Div([
                'There was an error processing this file.'
            ])
    else:
        return html.Div([
            'Please upload an Excel file. and wait for 5 sec'
        ])


# Callback to generate the download link
@app.callback(
    Output('download-link-container', 'children'),
    Input('download-button', 'n_clicks'),
    prevent_initial_call=True
)
def generate_download_link(n_clicks):
    global critical_values  # Access the global variable
    if n_clicks is not None and n_clicks > 0:
        # Assume 'filtered_df' is the filtered dataframe you want to download
        csv_string = critical_values.to_csv(index=False, encoding='utf-8-sig')
        csv_string = "data:text/csv;charset=utf-8-sig," + urllib.parse.quote(csv_string)
        return html.A('Download Filtered CSV', href=csv_string, download="filtered_data.csv", target='_blank', style={'font-weight': 'bold', 'color': 'red'})
    return no_update
if __name__ == '__main__':
    app.run_server(debug=True)