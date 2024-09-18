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
        
        dcc.Dropdown(
            id='product-filter',
            options=[],
            multi=True,
            placeholder='Select Product'
        ),
        dcc.Dropdown(
            id='crop-filter',
            options=[],
            multi=True,
            placeholder='Select crop'
        ),
        dcc.Dropdown(
            id='region-filter',
            options=[],
            multi=True,
            placeholder='Select region'
        ),
        dbc.Row(
            dbc.Col(
                html.Div(id='filtered-table', style={'marginTop': '30px'}),
                #width={'size': 8, 'offset': 3}
            )
        ),

        dbc.Row(
            dbc.Col(
                html.Div(id='msg_table', style={'marginTop': '30px'}),
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
    [Output('msg_table', 'children'),
     Output('crop-filter', 'options'),
     Output('product-filter', 'options'),
     Output('region-filter', 'options')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)

def import_data(contents,filename):
    print('---- am in function 1 ---- ')
    global critical_values 


    if contents is not None:
        print('__u hereeeee?????----------------')
         # Process the uploaded file and extract data
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Read the Excel file into a pandas DataFrame, selecting the specified sheet and skipping rows
        df = pd.read_excel(BytesIO(decoded), sheet_name='MasterGAP', skiprows=6)
        # Update the column name to replace '\n' with a space
        print('------ df imported_-_-')
        
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
        

       
            # Group the dataframe to find critical values
        critical_values = cgap_df.groupby(['Regulatory Zone','Product(PLT short)','Crop','Max # of applns.(per block)']).agg({'Application rate PTZ (g/ha)': 'max',
                                                                                    'applicationn timing BBCH end':'max',
                                                                                    'PHI':'min',
                                                                                    'Minimum appl. interval(days)':'min'}).reset_index()
        
        # Define the options for the dropdowns with the "All" option
        crop_options = [{'label': 'All', 'value': 'All'}] + [{'label': crop, 'value': crop} for crop in critical_values['Crop'].unique()]
        product_options = [{'label': 'All', 'value': 'All'}] + [{'label': product, 'value': product} for product in critical_values['Product(PLT short)'].unique()]
        region_options = [{'label': 'All', 'value': 'All'}] + [{'label': region, 'value': region} for region in critical_values['Regulatory Zone'].unique()]

        print('----- function 1 over-------')

        # Return the msg-table with the HTML message and the dropdown options
        return (
            html.Div(['Excel file imported']),
            crop_options,
            product_options,
            region_options
        )

    else:
        return(
            html.Div(['Please upload an Excel file and wait for 5 seconds']),  # Return a tuple for the msg_table
            [],  # Return an empty list for the crop options
            [],  # Return an empty list for the product options
            []  # Return an empty list for the region options
        )



@app.callback(
    Output('filtered-table', 'children'),
    [Input('product-filter', 'value'),
     Input('crop-filter', 'value'),
     Input('region-filter', 'value')],
    [State('upload-data', 'contents'),
     State('upload-data', 'filename')]
)


def display_data(product_options, crop_options, region_options, contents, filename):
    global critical_values 
    print('----- function 2 triggered-------')

    if contents is not None:
        print('----- function 2 begin-------')
        # Process the uploaded file and extract options for product and application filters
        
        # Update the options for the dropdowns
        print('++++++++++',product_options)
        print('++++++++++',crop_options)
        print('++++++++++',region_options)
        filtered_values = critical_values
        # Apply filtering based on product and application filters
        
       
         # Filter the critical_values based on the selected options
        filtered_values = critical_values
        if product_options is not None:
            if product_options == ['All']:
                # Include all available crop options in the filtering process
                filtered_values = filtered_values[filtered_values['Product(PLT short)'].isin(critical_values['Product(PLT short)'].unique())]
            else:
                filtered_values = filtered_values[filtered_values['Product(PLT short)'].isin(product_options)]
        if region_options is not None:
            if region_options == ['All']:
                # Include all available crop options in the filtering process
                filtered_values = filtered_values[filtered_values['Regulatory Zone'].isin(critical_values['Regulatory Zone'].unique())]
            else:
                filtered_values = filtered_values[filtered_values['Regulatory Zone'].isin(region_options)]
        if crop_options is not None:
            if crop_options == ['All']:
                # Include all available crop options in the filtering process
                filtered_values = filtered_values[filtered_values['Crop'].isin(critical_values['Crop'].unique())]
            else:
                filtered_values = filtered_values[filtered_values['Crop'].isin(crop_options)]
        
        print(filtered_values.shape)

        # Display the filtered dataframe using dash_table.DataTable
        return dash_table.DataTable(
            columns=[{'name': col, 'id': col} for col in filtered_values.columns],
            data=filtered_values.to_dict('records'),
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