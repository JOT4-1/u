import streamlit as st
import pandas as pd
import requests
import pydeck as pdk # Pydeck es una biblioteca para crear mapas interactivos y visualizaciones geoespaciales en Python, usada con Streamlit.
import numpy as np
from datetime import datetime, timedelta

# Título de la aplicación
st.title('Aplicación Sismos :D')

# Descripción de los datos presentados
st.header('Descripción de los datos')
st.write("""
    Esta aplicación muestra los últimos sismos ocurridos, obtenidos de una API pública. 
    Los datos incluyen la magnitud de los sismos, su ubicación, fecha y hora, entre otros detalles.
    La fuente de los datos proviene de la API pública de sismos: [https://api.gael.cloud/general/public/sismos](https://api.gael.cloud/general/public/sismos).
""")

# URL de la API
URL = 'https://api.gael.cloud/general/public/sismos'
respuesta = requests.get(URL)

# Comprobar si la API responde correctamente
if respuesta.status_code == 200:
    st.write('Conexión exitosa con la API.')
    datos_sismos = respuesta.json()
    
    # Crear el DataFrame a partir de los datos obtenidos
    df_sismos = pd.DataFrame(datos_sismos)

    # Verificar si las columnas de latitud y longitud existen; si no, crearlas con valores aleatorios en Chile
    if 'lat' not in df_sismos.columns or 'lon' not in df_sismos.columns:
        st.warning("No se encontraron las columnas de latitud y longitud en los datos. Creando ubicaciones aleatorias dentro de Chile.")
        
        # Rango aproximado de Chile en términos de latitud y longitud
        lat_min, lat_max = -55.0, -17.5
        lon_min, lon_max = -75.0, -66.0
        
        # Generar ubicaciones aleatorias
        df_sismos['Latitud'] = np.random.uniform(lat_min, lat_max, df_sismos.shape[0])
        df_sismos['Longitud'] = np.random.uniform(lon_min, lon_max, df_sismos.shape[0])
    else:
        # Renombrar las columnas de latitud y longitud si es necesario
        df_sismos.rename(columns={'lat': 'Latitud', 'lon': 'Longitud'}, inplace=True)

    # Convertir la columna de Magnitud a formato numérico
    df_sismos['Magnitud'] = pd.to_numeric(df_sismos['Magnitud'], errors='coerce')

    # Asegurar que la columna de fecha esté en formato de fecha; generar fechas recientes si no existen
    if 'Fecha' not in df_sismos.columns:
        st.warning("No se encontró la columna de fecha. Generando fechas recientes aleatorias para los sismos.")
        start_date = datetime.now() - timedelta(days=30)
        df_sismos['Fecha'] = [start_date + timedelta(days=np.random.randint(0, 30)) for _ in range(df_sismos.shape[0])]
    else:
        df_sismos['Fecha'] = pd.to_datetime(df_sismos['Fecha'], errors='coerce')
    
    # Formatear la fecha para que sea legible en el tooltip
    df_sismos['Fecha'] = df_sismos['Fecha'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Mostrar las primeras filas del DataFrame
    st.write('Últimos sismos registrados:')
    st.write(df_sismos.head())

    # Estadísticas generales de los datos
    st.header('Estadísticas Generales')
    st.write(df_sismos.describe())

    # Filtros interactivos
    magnitud_min = st.slider('Selecciona una magnitud mínima para visualizar los sismos', 0.0, 10.0, 4.0)
    sismos_filtrados = df_sismos[df_sismos['Magnitud'] >= magnitud_min]

    # Filtramos solo las columnas necesarias para el mapa: latitud, longitud y magnitud
    sismos_filtrados = sismos_filtrados.dropna(subset=['Latitud', 'Longitud'])

    # Gráfica interactiva 3D
    st.header("Visualización en 3D de Sismos")
    deck = pdk.Deck(
        layers=[ 
            pdk.Layer(
                'ColumnLayer',
                sismos_filtrados,
                get_position='[Longitud, Latitud]',
                get_color='[255, (1 - Magnitud / 10) * 255, 0]',
                get_elevation='[Magnitud * 5000]',  # Altura de cada punto según magnitud
                elevation_scale=10,
                radius=30000,
                pickable=True,
                auto_highlight=True,
                opacity=0.7,
            )
        ],
        initial_view_state=pdk.ViewState(
            latitude=-33.46,
            longitude=-70.65,
            zoom=4,
            pitch=50,
        ),
        tooltip={
            "html": "<b>Magnitud:</b> {Magnitud} <br/> <b>Lugar:</b> {RefGeografica} <br/> <b>Fecha:</b> {Fecha}",
            "style": {"backgroundColor": "steelblue", "color": "white"}
        },
        map_style='mapbox://styles/mapbox/light-v9'
    )

    st.pydeck_chart(deck)

    # Gráficas adicionales con Streamlit Charts

    # Gráfico de barras de frecuencia por magnitud
    st.header("Distribución de Frecuencia por Magnitud")
    magnitud_counts = df_sismos['Magnitud'].dropna().value_counts().sort_index()
    st.bar_chart(magnitud_counts)

    # Gráfico de líneas para magnitudes a lo largo del tiempo
    st.header("Magnitud de Sismos a lo Largo del Tiempo")
    df_sismos.sort_values('Fecha', inplace=True)
    magnitudes_por_fecha = df_sismos.groupby('Fecha')['Magnitud'].mean()
    st.line_chart(magnitudes_por_fecha)

    # Gráfico de dispersión de magnitud y ubicación
    st.header("Ubicaciones de Sismos con Magnitud")
    scatter_data = pd.DataFrame({
        'Longitud': df_sismos['Longitud'],
        'Latitud': df_sismos['Latitud'],
        'Magnitud': df_sismos['Magnitud']*10  # Ajuste para tamaño de puntos
    })
    st.scatter_chart(scatter_data)

    # Análisis de las gráficas
    st.header('Análisis de las Gráficas')
    st.write("""
        - **Mapa 3D de Columnas:** El mapa 3D muestra la ubicación de los sismos en Chile, y la altura de cada columna representa la magnitud del sismo.
        - **Distribución de Frecuencia:** La mayoría de los sismos presentan magnitudes entre los valores de menor riesgo, pero hay algunos eventos significativos.
        - **Magnitud a lo Largo del Tiempo:** Se observa la magnitud de los sismos con el tiempo, lo cual puede indicar tendencias en las ocurrencias de estos eventos.
        - **Ubicaciones de Sismos y sus Magnitudes:** Este gráfico permite observar la dispersión geográfica de los sismos en Chile.
    """)

    # Conclusiones
    st.header("Conclusiones")
    st.write("""
        - Los sismos ocurren con frecuencia en todo el territorio de Chile.
        - Existe una variedad en la magnitud de los sismos, con la mayoría de ellos concentrándose en niveles bajos y moderados.
        - La visualización 3D y los gráficos de dispersión proporcionan una perspectiva más clara sobre la distribución de la actividad sísmica.
    """)
else:
    st.error("Error al conectar con la API.")
