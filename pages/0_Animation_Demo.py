import streamlit as st
import pandas as pd
import re
from datetime import datetime
from dateutil import parser

# Configuración inicial de la página
st.set_page_config(page_title="Análisis de Eficiencia Operativa", page_icon="📊")

# URL del Google Sheet en formato CSV
# Asegúrate de reemplazar 'SheetName' con el nombre real de tu hoja
sheet_url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTG0WVV5FQNxYyOz0UM0YEkT9u8vGnzrwfUt7pVmJUHKGjDyKas_scI6XhY_ce_sTxRPtwVZw1Ggfyi/pub?gid=918102047&single=true&output=csv"
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

def calculate_kpi(end_date, start_date):
    try:
        # Convertir a datetime si son cadenas
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date, errors='coerce')
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date, errors='coerce')

        if pd.isnull(start_date) or pd.isnull(end_date):
            return None

        kpi_value = round(((end_date - start_date).days / 30), 2)
        if kpi_value < 0:  # Comprobar si el KPI es negativo
            return None  # Devolver None si el KPI es negativo
        return kpi_value
    except Exception as e:
        # Manejar cualquier otro error inesperado
        st.error(f"Error al calcular KPI: {e}")
        return None

def calculate_productivity(kpi):
    if kpi is None:
        return "Datos insuficientes"
    if kpi < 6:
        return "Eficiente"
    elif kpi < 8:
        return "Aceptable"
    elif kpi < 12:
        return "Con Demora"
    else:
        return "Alta Demora"

def get_year_for_operation(date_str):
    if pd.notnull(date_str):
        try:
            # Parsear la fecha y devolver el año
            return parser.parse(date_str).year
        except (ValueError, TypeError):
            # Devuelve None si hay un problema al parsear la fecha
            return None
    else:
        return None

def get_first_word(station):
    return station.split()[0] if station else None

# Función para preprocesar y estandarizar las fechas
def preprocess_date(date_str):
    try:
        # Intenta parsear la fecha con dateutil.parser que es flexible con los formatos
        dt = parser.parse(date_str)
        # Formatea la fecha al formato día/mes/año
        return dt.strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        # Devuelve None si hay un problema al parsear la fecha
        return None

def run(filtered_df):
    # Asegúrate de que 'filtered_df' contiene tus datos
    if filtered_df is not None:
        data = filtered_df.copy()

        # Convertir las columnas de fecha a datetime si aún no lo están
        date_columns = ['CARTA CONSULTA', 'APROBACIÓN', 'FechaVigencia', 'FechaEfectiva']
        for col in date_columns:
            data[col] = pd.to_datetime(data[col], errors='coerce')

        # Mapeo de estaciones a sus respectivas columnas de fecha
        operations = {
            'Vigencia - Aprobacion': ('APROBACIÓN', 'FechaVigencia'),
            'Aprobacion - Carta Consulta': ('CARTA CONSULTA', 'APROBACIÓN'),
            'Elegibilidad - Vigencia': ('FechaVigencia', 'FechaElegibilidad'),
            'PrimerDesembolso - Elegibilidad': ('FechaEfectiva', 'FechaElegibilidad')
        }

        # Lista para almacenar los resultados
        results = []

        # Procesar las filas del DataFrame
        for index, row in data.iterrows():
            for operation, (start_col, end_col) in operations.items():
                kpi = calculate_kpi(row[end_col], row[start_col])
                productividad = calculate_productivity(kpi)
                year = get_year_for_operation(row[end_col])

                # Usar strftime solo si la fecha es un objeto datetime
                indicador_principal = row[end_col].strftime('%d/%m/%Y') if pd.notnull(row[end_col]) and isinstance(row[end_col], datetime) else None
                indicador_secundario = row[start_col].strftime('%d/%m/%Y') if pd.notnull(row[start_col]) and isinstance(row[start_col], datetime) else None

                results.append({
                    'ESTACIONES': get_first_word(operation),
                    'ANO': year,
                    'PAIS': row['Pais'],
                    'CODIGO': row['NoOperacion'],
                    'APODO': row['Alias'],
                    'Indicador_Principal': indicador_principal,
                    'Indicador_Secundario': indicador_secundario,
                    'TIPO_DE_KPI': operation,
                    'KPI': kpi,
                    'Productividad': productividad
                })

        # Convertir la lista de resultados en un DataFrame
        results_df = pd.DataFrame(results)

        # Limpiar los valores negativos o None de KPI y establecerlos en None
        results_df['KPI'] = results_df['KPI'].apply(lambda x: x if x is not None and x >= 0 else None)

        # Filtrar para mantener solo las filas donde el KPI es mayor a 0
        results_df = results_df[results_df['KPI'] > 0]

        # Mostrar el DataFrame de resultados
        st.write(results_df)


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
        data_merged = pd.merge(data, data_operaciones, on='NoProyecto', how='inner')
        data_merged_total = pd.merge(data_merged, data_desembolsos, on='NoOperacion', how='inner')

        # Filtrar el DataFrame para conservar solo las columnas seleccionadas
        selected_columns = [
            'NoProyecto', 'NoOperacion', 'Pais', 'Alias', 'SEC', 'ARE', 
            'CARTA CONSULTA', 'APROBACIÓN', 'PERFIL', 'PROPUESTA OPERATIVA', 
            'FechaVigencia', 'FechaElegibilidad', 'FechaEfectiva', 'Estado_x'
        ]
        filtered_df = data_merged_total[selected_columns]

        # Preprocesar las fechas en el DataFrame filtrado
        date_columns = ['FechaVigencia', 'FechaElegibilidad', 'FechaEfectiva']
        for date_col in date_columns:
            filtered_df[date_col] = filtered_df[date_col].apply(preprocess_date)

        # Mostrar el DataFrame con las fechas preprocesadas
        st.write(filtered_df)

        # Llama a la función run para realizar el análisis adicional
        run(filtered_df)

if __name__ == "__main__":
    main()

