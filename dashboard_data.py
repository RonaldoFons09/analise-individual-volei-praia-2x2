import pandas as pd
import numpy as np

def load_data(file_path):
    """
    Loads and cleans data from the Excel file.
    """
    try:
        # Load the specific sheet 'Página1' and skip the first row (header is on line 2 in 0-indexed terms)
        # Based on inspection: Row 0 is mostly NaN, Row 1 has headers.
        df = pd.read_excel(file_path, sheet_name='Página1', header=1)
        
        # Clean column names (strip whitespace)
        df.columns = df.columns.str.strip()
        
        # Drop rows where 'Data' or 'Fundamentos' is missing
        df = df.dropna(subset=['Data', 'Fundamentos'])
        
        # Convert Data to datetime
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        
        # Numeric columns to clean
        numeric_cols = ['Quantidade correta', 'Quantidade errada', 'Quantidade total']
        
        for col in numeric_cols:
                # Convert to numeric, forcing errors (like '-') to NaN, then fill with 0
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # --- Specific Data Corrections ---
        
        # Helper to safely get float value
        def get_val(row, col):
            try:
                return float(row[col])
            except:
                return 0.0

        # Normalizing 'Levantamento' special rows where Correct/Wrong columns are empty ('-') 
        # but Total implies the count of that specific outcome.
        
        # Levantamento - Bom -> Is actually 100% correct count
        mask_lev_good = df['Fundamentos'] == 'Levantamento - Bom (não considere manchete)'
        df.loc[mask_lev_good, 'Quantidade correta'] = df.loc[mask_lev_good, 'Quantidade total']
        df.loc[mask_lev_good, 'Quantidade errada'] = 0

        # Levantamento - Erros -> Is actually 100% wrong count
        lev_errors = [
            'Levantamento - Bola não permite ataque (Erro)', 
            'Levantamento - Dois toque (Erro)', 
            'Levantamento - Condução (Erro)'
        ]
        mask_lev_err = df['Fundamentos'].isin(lev_errors)
        df.loc[mask_lev_err, 'Quantidade correta'] = 0
        df.loc[mask_lev_err, 'Quantidade errada'] = df.loc[mask_lev_err, 'Quantidade total']

        # --- Categorization ---
        def categorize(fundament):
            fundament = str(fundament).strip()
            if fundament.startswith('Ataque'):
                return 'Ataque'
            if 'Levantamento' in fundament:
                return 'Levantamento'
            if 'Recepção' in fundament:
                return 'Recepção'
            if 'Saque' in fundament:
                return 'Saque'
            return 'Outros'

        df['Categoria'] = df['Fundamentos'].apply(categorize)

        # Recalculate 'Quantidade total' after corrections
        df['Total Calculated'] = df['Quantidade correta'] + df['Quantidade errada']
        
        # Calculate Efficiency (0 to 1 scale)
        df['Eficiencia'] = df.apply(
            lambda x: x['Quantidade correta'] / x['Total Calculated'] if x['Total Calculated'] > 0 else 0, 
            axis=1
        )
        
        return df
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame() # Return empty on error
