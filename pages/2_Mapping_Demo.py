import streamlit as st
import pandas as pd
import re
from datetime import datetime as dt

# Configuración inicial de la página
st.set_page_config(page_title="Análisis de Eficiencia Operativa", page_icon="📊")

# URLs de las hojas de Google Sheets
sheet_url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTG0WVV5FQNxYyOz0UM0YEkT9u8vGnzrwfUt7pVmJUHKGjDyKas_scI6XhY_ce_sTxRPtwVZw1Ggfyi/pub?output=csv"
sheet_operaciones_url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTG0WVV5FQNxYyOz0UM0YEkT9u8vGnzrwfUt7pVmJUHKGjDyKas_scI6XhY_ce_sTxRPtwVZw1Ggfyi/pub?gid=1958213072&single=true&output=csv"
sheet_desembolsos_url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTG0WVV5FQNxYyOz0UM0YEkT9u8vGnzrwfUt7pVmJUHKGjDyKas_scI6XhY_ce_sTxRPtwVZw1Ggfyi/pub?gid=1839704968&single=true&output=csv"

# Función para cargar los datos desde la URL
def load_data_from_url(url):
    try:
        return pd.read_csv(url, header=0)
    except Exception as e:
        st.error("Error al cargar los datos: " + str(e))
        return None

# Función para convertir varios formatos de fecha al formato dd/mm/aaaa
def convert_mixed_date_formats(date_str):
    spanish_to_english_months = {
        'enero': 'January', 'febrero': 'February', 'marzo': 'March', 'abril': 'April',
        'mayo': 'May', 'junio': 'June', 'julio': 'July', 'agosto': 'August',
        'septiembre': 'September', 'octubre': 'October', 'noviembre': 'November', 'diciembre': 'December'
    }
    try:
        if '-' in date_str and len(date_str.split('-')) == 3:
            day, month, year = date_str.split('-')
            year = f"20{year}" if len(year) == 2 else year
            month = spanish_to_english_months.get(month[:3].lower(), month)
            return dt.strptime(f"{day} {month} {year}", '%d %B %Y').strftime('%d/%m/%Y')

        if ',' in date_str:
            date_part = ' '.join(date_str.split(',')[1:]).strip()
            for es, en in spanish_to_english_months.items():
                date_part = date_part.replace(es, en)
            return dt.strptime(date_part, '%d de %B de %Y').strftime('%d/%m/%Y')

        return date_str
    except Exception as e:
        st.error(f"Error al convertir la fecha: {e}")
        return date_str

# Aplicación Streamlit
def main():
    st.title("Mi Aplicación con Datos de Google Sheets")

    # Carga los datos
    data = load_data_from_url(sheet_url_csv)
    data_operaciones = load_data_from_url(sheet_operaciones_url_csv)
    data_desembolsos = load_data_from_url(sheet_desembolsos_url_csv)

    if data is not None and data_operaciones is not None and data_desembolsos is not None:
        # Procesamiento de datos
        date_columns = ['ABSTRACTO', 'CARTA CONSULTA', 'PERFIL', 'PROPUESTA OPERATIVA', 'ACTA NEGOCIACION', 'APROBACIÓN']
        for col in date_columns:
            data[col] = data[col].apply(lambda x: convert_mixed_date_formats(x) if isinstance(x, str) else x)
        data['NO. OPERACION'] = data['NO. OPERACION'].str.replace('-', '', regex=False)
        data.rename(columns={'NÚMERO': 'NoProyecto'}, inplace=True)

        # Unión de los datos
        data_merged = pd.merge(data, data_operaciones, on='NoProyecto', how='left')
        data_merged_total = pd.merge(data_merged, data_desembolsos, on='NoOperacion', how='left')

        # Filtrar el DataFrame para conservar solo las columnas seleccionadas
        selected_columns = [
            'NoProyecto', 'NoOperacion', 'Pais', 'Alias', 'SEC', 'ARE', 
            'CARTA CONSULTA', 'APROBACIÓN', 'PERFIL', 'PROPUESTA OPERATIVA', 'FechaElegibilidad',
            'FechaVigencia', 'FechaEfectiva', 'Estado_x'
        ]
        filtered_df = data_merged_total[selected_columns]

        # Convertir formatos de fecha en las columnas específicas
        date_columns_to_convert = ['FechaElegibilidad', 'FechaVigencia', 'FechaEfectiva']
        for col in date_columns_to_convert:
            filtered_df[col] = filtered_df[col].apply(lambda x: convert_mixed_date_formats(x) if isinstance(x, str) else x)

        # Mostrar el nuevo DataFrame filtrado
        st.write(filtered_df)

# Ejecutar la aplicación
if __name__ == "__main__":
    main()

