import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap
import streamlit.components.v1 as components
import gdown
import os
import duckdb

if not os.path.exists('GEDevent_slim.csv'):
    gdown.download('https://drive.google.com/uc?id=1q1qUNHFD6ab0P0pE0019HVo-QVjSKsP9', 'GEDevent_slim.csv', quiet=False)

con = duckdb.connect()

st.title('Global Conflict Explorer')

# Filters
region_options = ['All'] + sorted(con.execute("SELECT DISTINCT region FROM 'GEDevent_slim.csv' ORDER BY region").df()['region'].tolist())
selected_region = st.selectbox('Select a region', region_options)

if selected_region != 'All':
    country_options = ['All'] + sorted(con.execute(f"SELECT DISTINCT country FROM 'GEDevent_slim.csv' WHERE region = '{selected_region}' ORDER BY country").df()['country'].tolist())
else:
    country_options = ['All'] + sorted(con.execute("SELECT DISTINCT country FROM 'GEDevent_slim.csv' ORDER BY country").df()['country'].tolist())

country_name = st.selectbox('Select a country', country_options)

country_name = st.selectbox('Select a country', ['All'] + sorted(region_df['country'].unique().tolist()))

if country_name != 'All':
    filtered = region_df[region_df['country'] == country_name]
else:
    filtered = region_df

# Actor filter
all_actors = sorted(set(filtered['side_a'].dropna().tolist() + filtered['side_b'].dropna().tolist()))
selected_actor = st.selectbox('Filter by actor (optional)', ['All'] + all_actors)

if selected_actor != 'All':
    filtered = filtered[(filtered['side_a'] == selected_actor) | (filtered['side_b'] == selected_actor)]

# Violence type filter
violence_map = {1: 'State-based conflict', 2: 'Non-state conflict', 3: 'One-sided violence'}
descriptions = {
    'State-based conflict': 'Armed conflict between a government and another party.',
    'Non-state conflict': 'Armed conflict between non-governmental groups such as militias or clans.',
    'One-sided violence': 'Deliberate attacks by a government or armed group against unarmed civilians.'
}
selected_violence = st.multiselect('Type of violence', options=list(violence_map.values()), default=list(violence_map.values()))
for v in selected_violence:
    st.caption(f'**{v}:** {descriptions[v]}')
selected_codes = [k for k, v in violence_map.items() if v in selected_violence]
filtered = filtered[filtered['type_of_violence'].isin(selected_codes)]

# Fatalities over time
st.subheader('Total Fatalities by Year')
by_year = filtered.groupby('year')['best'].sum()
fig, ax = plt.subplots()
ax.plot(by_year.index, by_year.values, marker='o', color='red')
ax.set_xlabel('Year')
ax.set_ylabel('Fatalities')
st.pyplot(fig)

# Civilian deaths over time
st.subheader('Civilian Deaths by Year')
civ_by_year = filtered.groupby('year')['deaths_civilians'].sum()
fig2, ax2 = plt.subplots()
ax2.plot(civ_by_year.index, civ_by_year.values, marker='o', color='orange')
ax2.set_xlabel('Year')
ax2.set_ylabel('Civilian Deaths')
st.pyplot(fig2)

# Map
st.subheader('Conflict Map')
year_min = int(filtered['year'].min())
year_max = int(filtered['year'].max())
selected_year = st.slider('Show data up to year', year_min, year_max, year_max)

map_data = filtered[filtered['year'] <= selected_year].dropna(subset=['latitude', 'longitude'])

map_mode = st.radio('Map mode', ['Heatmap', 'Dot map'])

center_lat = map_data['latitude'].mean()
center_lon = map_data['longitude'].mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=5)

if map_mode == 'Heatmap':
    heat_data = [[r['latitude'], r['longitude'], r['best']] for _, r in map_data.iterrows()]
    HeatMap(heat_data, max_val=50, radius=10, blur=8).add_to(m)

else:
    dot_data = map_data.nlargest(100, 'best')
    for _, r in dot_data.iterrows():
        popup_html = f"""
        <b>Conflict:</b> {r['conflict_name']}<br>
        <b>Dyad:</b> {r['dyad_name']}<br>
        <b>Location:</b> {r['where_description']}<br>
        <b>Date:</b> {r['date_start']}<br>
        <b>Fatalities:</b> {r['best']}<br>
        <b>Civilian deaths:</b> {r['deaths_civilians']}<br>
        <b>Side A:</b> {r['side_a']}<br>
        <b>Side B:</b> {r['side_b']}
        """
        folium.CircleMarker(
            location=[r['latitude'], r['longitude']],
            radius=5,
            color='red',
            fill=True,
            fill_opacity=0.6,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)

components.html(m._repr_html_(), height=500)
