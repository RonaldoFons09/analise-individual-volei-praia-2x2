import pandas as pd
import numpy as np
import streamlit as st
from streamlit_gsheets import GSheetsConnection

def load_data(file_path=None):
    """
    Loads and cleans data from Google Sheets.
    """
    try:
        # Load data using Streamlit Google Sheets Connection
        # Uses credentials from .streamlit/secrets.toml
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Read the spreadsheet (default is first sheet, which matches 'Página1' usually)
        # header=1 implies row 1 is header (0-indexed), similar to read_excel behavior.
        # However, st.connection might read everything. Let's try reading as is.
        # If the structure matches Excel, we might need to skip rows.
        # But 'read()' usually infers headers. Let's assume standard tabular data first.
        # Specify the worksheet 'Página1' explicitly, as the first sheet is likely documentation/criteria
        df = conn.read(worksheet='Página1', header=1) 



        
        # Clean column names (strip whitespace)
        df.columns = df.columns.str.strip()
        
        # Drop rows where 'Data' or 'Fundamentos' is missing
        df = df.dropna(subset=['Data', 'Fundamentos'])
        
        # Convert Data to datetime
        # Enforce dayfirst=True because source is typically DD/MM/YYYY
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        
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
        st.error(f"Erro detalhado na conexão: {e}")
        return pd.DataFrame() # Return empty on error
