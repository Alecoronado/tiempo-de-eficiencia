import streamlit as st
import pandas as pd
import re
from datetime import datetime

# Configuración inicial de la página
st.set_page_config(page_title="Análisis de Eficiencia Operativa", page_icon="📊")

# Asegúrate de reemplazar 'SheetName' con el nombre real de tu hoja
sheet_url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTG0WVV5FQNxYyOz0UM0YEkT9u8vGnzrwfUt7pVmJUHKGjDyKas_scI6XhY_ce_sTxRPtwVZw1Ggfyi/pub?output=csv"
sheet_operaciones_url_csv="https://docs.google.com/spreadsheets/d/e/2PACX-1vTG0WVV5FQNxYyOz0UM0YEkT9u8vGnzrwfUt7pVmJUHKGjDyKas_scI6XhY_ce_sTxRPtwVZw1Ggfyi/pub?gid=1958213072&single=true&output=csv"
sheet_desembolsos_url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTG0WVV5FQNxYyOz0UM0YEkT9u8vGnzrwfUt7pVmJUHKGjDyKas_scI6XhY_ce_sTxRPtwVZw1Ggfyi/pub?gid=1839704968&single=true&output=csv"


# Función para cargar los datos desde la URL
def load_data_from_url(url):
    try:
        return pd.read_csv(url, header=0)
    except Exception as e:
        st.error("Error al cargar los datos: " + str(e))
        return None

# Función para convertir las fechas del formato español al formato estándar
def convert_spanish_date(date_str):
    months = {
        'ENE': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'ABR': 'Apr', 'MAY': 'May', 'JUN': 'Jun',
        'JUL': 'Jul', 'AGO': 'Aug', 'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DIC': 'Dec'
    }
    match = re.match(r"(\d{2}) (\w{3}) (\d{2})", date_str)
    if match:
        day, spanish_month, year = match.groups()
        english_month = months.get(spanish_month.upper())
        if english_month:
            return datetime.strptime(f"{day} {english_month} 20{year}", "%d %b %Y").strftime("%d/%m/%Y")
    return date_str

# Función para manejar diferentes formatos de fechas y valores nulos
def convert_dates(date_str):
    if pd.isnull(date_str):
        return None

    if not isinstance(date_str, str):
        return date_str

    months = {
        'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05', 'jun': '06',
        'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'
    }

    try:
        # Formato '15-ago-14' o '1-dic-17'
        day, month, year = date_str.split('-')
        if len(year) == 2: year = f"20{year}"
        month = months.get(month[:3].lower(), '00')
        return f"{day.zfill(2)}/{month}/{year}"
    except ValueError:
        pass

    try:
        # Formato 'martes, 17 de noviembre de 2015'
        parts = date_str.split(' ')
        day = parts[1]
        month = parts[3].lower()[:3]
        year = parts[5]
        return f"{day.zfill(2)}/{months[month]}/{year}"
    except (ValueError, IndexError):
        pass

    try:
        # Formato '13-abr-20'
        return datetime.strptime(date_str, '%d-%b-%y').strftime('%d/%m/%Y')
    except ValueError:
        pass

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
            data[col] = data[col].apply(lambda x: convert_spanish_date(x) if isinstance(x, str) else x)
        data['NO. OPERACION'] = data['NO. OPERACION'].str.replace('-', '', regex=False)
        data['NÚMERO'] = data['NÚMERO'].str.replace('-', '', regex=False)
        data.rename(columns={'NÚMERO': 'NoProyecto'}, inplace=True)
        data.rename(columns={'NO.OPERACION': 'NoOperacion'}, inplace=True)

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

        # Convertir las fechas en las columnas seleccionadas usando la nueva función
        for col in ['FechaElegibilidad', 'FechaVigencia', 'FechaEfectiva']:
            filtered_df[col] = filtered_df[col].apply(convert_dates)
        
        # Mostrar el nuevo DataFrame filtrado
        st.write(filtered_df)

if __name__ == "__main__":
    main()


