import pandas as pd
import os
import openpyxl
from openpyxl.worksheet.table import Table

def clean_and_save_data(input_file, output_folder):
    # Get the base name of the file without extension
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # Load the workbook
    workbook = openpyxl.load_workbook(input_file, read_only=True, data_only=True)
    
    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
        
        # Find tables in the sheet
        tables = [t for t in sheet._tables if isinstance(t, Table)]
        
        if not tables:
            print(f"No table found in sheet '{sheet_name}' of {input_file}")
            continue
        
        for table in tables:
            # Get the table range
            table_range = sheet[table.ref]
            
            # Extract data from the table
            data = [[cell.value for cell in row] for row in table_range]
            
            # Create DataFrame
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Check if 'Column1' is in the columns
            if 'Column1' not in df.columns:
                print(f"Skipping table in sheet '{sheet_name}' of {input_file} - no 'Column1' found")
                continue
            
            # Rename "Column1" to "Municipality"
            df.rename(columns={'Column1': 'Municipality'}, inplace=True)
            
            # Set "Municipality" as index
            df.set_index('Municipality', inplace=True)
            
            # Drop any rows or columns that are entirely NaN
            df.dropna(axis=0, how='all', inplace=True)
            df.dropna(axis=1, how='all', inplace=True)
            
            # Convert column names to strings
            df.columns = df.columns.astype(str)
            
            # Convert data to numeric, replacing non-numeric values with NaN
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Special handling for 'forbrydelser.xlsx' (aggregate to yearly data)
            if 'forbrydelser' in input_file.lower():
                df = aggregate_quarterly_to_yearly(df)
            
            # Create output filename
            output_file = os.path.join(output_folder, f"{base_name}_{sheet_name}_{table.name}.csv")
            
            # Save the cleaned DataFrame to a CSV file
            df.to_csv(output_file)
            print(f"Saved {output_file} successfully.")
    
    workbook.close()

def aggregate_quarterly_to_yearly(df):
    # Identify year and quarter columns
    year_quarter_cols = [col for col in df.columns if 'K' in col]
    
    # Create a dictionary to store yearly data
    yearly_data = {}
    
    # Group columns by year and sum the quarters
    for year in set([col.split(' ')[0] for col in year_quarter_cols]):
        year_cols = [col for col in year_quarter_cols if col.startswith(year)]
        yearly_data[year] = df[year_cols].sum(axis=1)
    
    # Create a new DataFrame with the yearly data
    return pd.DataFrame(yearly_data)

if __name__ == "__main__":
    datasets = [
        'dst_data/forbrydelser.xlsx',
        'dst_data/fuldtidsledige.xlsx',
        'dst_data/gnms_alder.xlsx',
        'dst_data/job.xlsx',
        'dst_data/ginikoeff.xlsx',
        'dst_data/kommuneskat.xlsx',
        'dst_data/befolkning og indvandre.xlsx',
        'dst_data/uddannelse.xlsx'
    ]

    output_folder = 'data/cleaned'
    os.makedirs(output_folder, exist_ok=True)

    # Process and save each dataset
    for input_file in datasets:
        try:
            clean_and_save_data(input_file, output_folder)
        except Exception as e:
            print(f"Error processing {input_file}: {str(e)}")