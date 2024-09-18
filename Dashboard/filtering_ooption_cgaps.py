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
import os
import openpyxl 
import io

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
# Define the layout of the app

# Load the image
image_filename =  os.path.join(os.path.dirname(__file__),'Logo.png')  # Path to your image file
encoded_image = base64.b64encode(open(image_filename, 'rb').read()).decode('ascii')
app.layout = dbc.Container(
    fluid=True,
    style={'backgroundColor': '#80c3d8'},
    children=[
        dbc.Row(
            dbc.Col(
                html.Img(src=f'data:image/png;base64,{encoded_image}',
                          style={'height': '250px', 'margin': 'auto', 'display': 'block'}), 
                width=12
            ),
        ),
        #dbc.Row(
        #    dbc.Col(html.H1('c.GAP identifier', className='text-center mb-4'), width=10)
        #),
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        dcc.Markdown('''
                          This app takes as input the excel file "*Master GAP Table with revised GAPs*" provided by the regional regulatory
                           managers,in which there are each of the requested GAPs by country, crop and product. 
                                     
                             
                                     
                             As for crops we discarded rye, triticale, spelt, oat and we group together the some crops eg: Barley (spring & winter) and  
                              wheat (durum, spring, winter), Cabbage, Onion, Rape.
                             
                                     
                            This app identifies among all these GAPs, the most critical GAP by formulation (J-neck) / by regulatory zone (G-collar)
                            / by crop (O-collar).
                                     Here are the 5 criteria used to define the most critical GAP:
                                     
                                        - 1 - Application rate  (g/ha), higher is the most critical        
                                        - 2 - BBCH stage the latest, max is the most critical
                                        - 3 - The shortest PHI (PHI): smaller  is the most critical
                                        - 4 - Interval between applications: the smallest interval is the most critical     
                                        - 5 - Nb of application: the higher Application rate x Nb of application is the most critical
                                                                ''') ,
                    ]),
                    className="mb-3",
                    style={'backgroundColor': '#b1dae7'} 
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
                    html.Div(id='msg_table', style={'marginTop': '30px'}),
                    #width={'size': 8, 'offset': 3}
                )
            ),
    

            

            dbc.Row(
            dbc.Col(
                dcc.Loading(  # Add the Loading component here
                    id="loading",
                    type="default",  # You can choose 'default', 'circle', or 'square'
                    
                    children=[
                        
                        dcc.Dropdown(
                            id='regulatory-filter',
                            options=[],
                            multi=False,
                            placeholder='Select Regulatory Region for the GAP',
                            style={'width': '500px', 'margin': '10px', 'color': '#000', 'background-color': '#fff', 'border': '1px solid #ccc'},
                            className='dropdown-custom'
                        ),
                        dcc.Dropdown(
                            id='ApplicationRate-filter',
                            options=[],
                            multi=False,
                            placeholder='Select ApplicationRate for the GAP',
                            style={'width': '500px', 'margin': '10px', 'color': '#000', 'background-color': '#fff', 'border': '1px solid #ccc'},
                            className='dropdown-custom'
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
                        html.Div(
                            id='filtered-table',
                            style={'marginTop': '30px'}
                        ),



                    ]
                ),
                # width={'size': 8, 'offset': 3}
            )
        ),
        
            # Add the download button and link container
            html.Div([
                html.Div(id='download-link-container'),
                dbc.Button('Export Data', id='download-button', color='primary', className='mt-3'),
                dcc.Download(id='download-dataframe-csv')
                
            ])
      

    ]
)

# Callback to handle the loading state and apply blur effect
@app.callback(
    Output('loading', 'style'),
    Input('loading', 'loading_state')
)
def update_loading_style(loading_state):
    print('loading ...')
    if loading_state and loading_state['is_loading']:
        return {'filter': 'blur(2px)', 'transition': 'filter 0.3s ease'}  # Apply blur when loading
    return {'filter': 'blur(0px)', 'transition': 'filter 0.3s ease'}  # No blur when not loading





# Callback to handle the file upload and display the data
@app.callback(
    [Output('msg_table', 'children'),
     Output('regulatory-filter', 'options'),
     Output('ApplicationRate-filter', 'options')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)

def import_data(contents,filename):
    print('---- am in function 1 ---- ')
    global cgap_df 


    if contents is not None:
        print('----file not empty------------')
         # Process the uploaded file and extract data
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Read the Excel file into a pandas DataFrame, selecting the specified sheet and skipping rows
        df = pd.read_excel(BytesIO(decoded), sheet_name='MasterGAP', skiprows=6)
        # Update the column name to replace '\n' with a space
        print('------ df imported_-_-')
        rate_columns = [{'label': col, 'value': col} for col in df.columns if col.startswith("Application rate") and col.endswith("(g/ha)")]
        print(rate_columns)
        zone_list= [col for col in df.columns if col.lower() in [name.lower() for name in ['Regulatory Zone', 'Residues region']]]
        rest_columns= [col for col in df.columns if col.lower() in [name.lower() for name in ['Product\n(PLT short)',
                                                                                              'Crop',
                                                                                              'applicationn timing BBCH end','application timing BBCH end',
                                                                                              'Max # of applns.\n(per block)',
                                                                                             'PHI', 
                                                                                             'Minimum appl. interval\n(days)',
                                                                                             'Maximum appl. interval\n(days)']]]

        region_columns= [{'label': col, 'value': col} for col in zone_list]
        print(region_columns)
        print('###')
        print(rest_columns)
        # Select specific columns from the dataframe
        cgap_df = df[rest_columns+zone_list+[col for col in df.columns if col.startswith("Application rate") and col.endswith("(g/ha)")]]
        cgap_df.columns = cgap_df.columns.str.replace('\n', '')
        # Rename columns based on conditions
        
        # Create a new list for the updated column names
        new_columns = []

        for col in cgap_df.columns:
            if 'Product' in col and 'PLT' in col:
                new_columns.append('Product(PLT short)')
            elif 'Crop' in col:
                new_columns.append('Crop')
            elif 'BBCH' in col and 'end' in col:
                new_columns.append('Application timing BBCH end')
            else:
                new_columns.append(col)  # Keep the original name if no conditions are met

        # Assign the new column names to the DataFrame
        cgap_df.columns = new_columns



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
        
        
        
        
        print('----- function 1 over-------')

        # Return the msg-table with the HTML message and the dropdown options
        return (
            html.Div(['Excel file imported. Select the cGap columns you wish to use for the calculations'],style={'color': 'grey'} ),
        
            region_columns,
            rate_columns

        )

    else:
        return(
            html.Div(['Please upload an Excel file and wait for 5 seconds']),  # Return a tuple for the msg_table
            [],  # Return an empty list for the  options
            []
        )



@app.callback(
    Output('crop-filter', 'options'),
     Output('product-filter', 'options'),
     Output('region-filter', 'options'),
    [Input('regulatory-filter', 'value')],
     [State('upload-data', 'contents'),
     State('upload-data', 'filename')]
)
def update_filter_dropdown(region_columns,contents, filename):
    
    global cgap_df

    if contents is not None and region_columns is not None:
        print('---- updating filter dropdown ---- ')
        print('region_columns is :  ',region_columns)

        print(cgap_df.columns)
        print(cgap_df['Product(PLT short)'].unique())
    

        # Define the options for the dropdowns with the "All" option
        crop_options = [{'label': 'All', 'value': 'All'}] + [{'label': crop, 'value': crop} for crop in cgap_df['Crop'].unique()]
        product_options = [{'label': 'All', 'value': 'All'}] + [{'label': product, 'value': product} for product in cgap_df['Product(PLT short)'].dropna().unique()]
        region_options = [{'label': 'All', 'value': 'All'}] + [{'label': region, 'value': region} for region in cgap_df[region_columns].unique()]
        print(region_options)
        return (
                crop_options,
                product_options,
                region_options,
        )
    else:
        return(
            [],
            [],  # Return an empty list for the  options
            []
        )




@app.callback(
    Output('filtered-table', 'children'),
    [Input('regulatory-filter', 'value'),
     Input('ApplicationRate-filter', 'value'),
     Input('product-filter', 'value'),
     Input('crop-filter', 'value'),
     Input('region-filter', 'value')],
    [State('upload-data', 'contents'),
     State('upload-data', 'filename')]
)

def display_data(region_columns,rate_columns,product_options, crop_options, region_options, contents, filename):
    global critical_values
    global cgap_df 
    print('----- function display data triggered-------')

    if contents is not None:


       
           
        if rate_columns is not None and region_columns is not None:
            critical_values = cgap_df.groupby([region_columns,'Product(PLT short)','Crop','Max # of applns.(per block)']).agg({rate_columns: 'max',
                                                                                        'Application timing BBCH end':'max',
                                                                                        'PHI':'min',
                                                                                         'Minimum appl. interval(days)':'min'}).reset_index()

            print('----- columns selected -------')

            # Define the options for the dropdowns with the "All" option
            
            # Process the uploaded file and extract options for product and application filters
            print('++++++region_columns++++',region_columns)
            print('++++++rate_columns++++',rate_columns)
            # Update the options for the dropdowns
            print('+++++product_options+++++',product_options)
            print('+++++crop_options+++++',crop_options)
            print('+++++region_options+++++',region_options)
            filtered_values = critical_values
            # Apply filtering based on product and application filters
          
            if product_options is not None:
                if product_options == ['All'] or product_options == []:
                    # Include all available crop options in the filtering process
                    filtered_values = filtered_values[filtered_values['Product(PLT short)'].isin(filtered_values['Product(PLT short)'].unique())]
                else:
                    filtered_values = filtered_values[filtered_values['Product(PLT short)'].isin(product_options)]
            if region_options is not None:
                if region_options == ['All'] or  region_options == [] :
                    # Include all available crop options in the filtering process
                    filtered_values = filtered_values[filtered_values[region_columns].isin(filtered_values[region_columns].unique())]
                else:

                    filtered_values = filtered_values[filtered_values[region_columns].isin(region_options)]
            if crop_options is not None:
                if crop_options == ['All'] or crop_options == []  :
                    # Include all available crop options in the filtering process
                    filtered_values = filtered_values[filtered_values['Crop'].isin(filtered_values['Crop'].unique())]
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
        
        return(
            html.Div(
        ['Select the right columns for the appropriate calculations to be performed.'],
        style={'color': 'red'}  # Set the color to red),  # Return a tuple for the msg_table
            
        ))
        
    
  




# Callback to generate the download link
@app.callback(
    Output('download-link-container', 'children'),
    Input('download-button', 'n_clicks'),
    prevent_initial_call=True
)
def generate_download_link(n_clicks):
    global critical_values  # Access the global variable
    if n_clicks is not None and n_clicks > 0:
        # Assume 'critical_values' is the DataFrame you want to download
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            critical_values.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        
        # Encode the Excel file to a base64 string
        excel_string = base64.b64encode(output.getvalue()).decode()
        excel_href = f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{excel_string}"
        
        return html.A('Download Filtered Excel', href=excel_href, download="filtered_data.xlsx", target='_blank', style={'font-weight': 'bold', 'color': 'red'})
    return no_update




if __name__ == '__main__':
    app.run_server(debug=True)