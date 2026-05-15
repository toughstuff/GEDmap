import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap
import streamlit.components.v1 as components
import gdown
import os

if not os.path.exists('GEDevent.csv'):
  gdown.download('https://drive.google.com/uc?id=1q1qUNHFD6ab0P0pE0019HVo-QVjSKsP9', 'GEDevent.csv', quiet=False)
df = pd.read_csv('GEDevent.csv')

country_name = st.selectbox('Select a country', sorted(df['country'].unique()))

filtered = df[df['country'] == country_name]

# Fatalities over time
st.subheader('Fatalities by Year')
by_year = filtered.groupby('year')['best'].sum()
fig, ax = plt.subplots()
ax.plot(by_year.index, by_year.values, marker='o')
ax.set_xlabel('Year')
ax.set_ylabel('Fatalities')
st.pyplot(fig)

# Heatmap
st.subheader('Conflict Heatmap')
year_min = int(filtered['year'].min())
year_max = int(filtered['year'].max())
selected_year = st.slider('Select Year', year_min, year_max, year_max)

map_data = filtered[filtered['year'] <= selected_year][['latitude', 'longitude', 'best']].dropna()
m = folium.Map(location=[map_data['latitude'].mean(), map_data['longitude'].mean()], zoom_start=6)
HeatMap(
    [[r['latitude'], r['longitude'], r['best']] for _, r in map_data.iterrows()],
    max_val=50,
    radius=10,
    blur=8
).add_to(m)
components.html(m._repr_html_(), height=500)