
import pandas as pd
import folium 
import streamlit as st
from streamlit_folium import st_folium


# --- Load Data ---
@st.cache_data
def load_data():
    return pd.read_csv("VolOpp2.csv")  # Use your CSV with Latitude/Longitude

df = load_data()

st.set_page_config(layout="wide")
st.title("🗺️ Volunteer Opportunities")

# --- Sidebar Filters ---
with st.sidebar:
    st.header("🔍 Filter Options")

    # Text filters
    text_filter_cols = ["Organization",  "About"]
    text_inputs = {}
    for col in text_filter_cols:
        text_inputs[col] = st.text_input(f"Search '{col}'", key=col)

    # Dropdown filters
    dropdown_filter_cols = ["Region", "County"]
    dropdown_inputs = {}
    for col in dropdown_filter_cols:
        unique_vals = df[col].dropna().unique()
        dropdown_inputs[col] = st.multiselect(f"Filter by '{col}'", sorted(unique_vals), key=col)

    # Checkbox filters for focus areas
    checkbox_filter_cols = ["Stewardship", "Education", "Citizen Science"]
    st.markdown("### 🏷️ Focus Areas")
    checkbox_inputs = {}
    for col in checkbox_filter_cols:
        checkbox_inputs[col] = st.checkbox(f"{col}", value=False, key=col)

# --- Apply Filters ---
filtered_df = df.copy()

for col, val in text_inputs.items():
    if val:
        filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(val, case=False, na=False)]

for col, selected in dropdown_inputs.items():
    if selected:
        filtered_df = filtered_df[filtered_df[col].isin(selected)]

for col, checked in checkbox_inputs.items():
    if checked:
        filtered_df = filtered_df[filtered_df[col] == True]

st.markdown(f"### {len(filtered_df)} matching organization(s)")

# --- Download CSV ---
csv_download = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download Filtered Results", data=csv_download, file_name="filtered_organizations.csv", mime="text/csv")

# --- View toggle ---
view_option = st.selectbox("Choose view:", ["Card View", "Map View"])

if view_option == "Map View":
        
    # Prepare the filtered dataframe for mapping
    map_df = filtered_df.dropna(subset=["latitude", "longitude", "Organization", "City", "OrgURL"]).copy()
    
    # Create Folium map centered on Wisconsin
    m = folium.Map(location=[44.5, -89.5], zoom_start=7)
    m.fit_bounds([[42.49, -92.89], [47.31, -86.25]])  # Southwest and Northeast corners of Wisconsin
    
    # Add markers
    for _, row in map_df.iterrows():
        # Clean popup HTML — remove extra spacing and format clearly
        popup_html = f"""
        <div style="font-size: 14px;">
            <b>{row['Organization']}</b><br>
            <i>{row['City']}</i><br>
            <a href="{row['OrgURL']}" target="_blank">Visit Website</a>
        </div>
        """
    
        # Optional: choose icon color dynamically, or use a better default
        icon = folium.Icon(icon='leaf', prefix='fa', color='darkgreen')
    
        # Add the marker
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_html, max_width=250),
            icon=icon
        ).add_to(m)
    
    # Display the map in Streamlit (no st.write() or debug output)
    st_folium(m, width=700, height=500)

       # st.map(map_df[['latitude', 'longitude']])

elif view_option == "Card View":
    if filtered_df.empty:
        st.info("No matching organizations found. Try adjusting your filters.")
    else:
        for _, row in filtered_df.iterrows():
            with st.container():
                st.markdown("---")
                cols = st.columns([1, 2])
                with cols[0]:
                    st.subheader(f"{row['Organization']}")
                    st.caption(f"{row['City']}, {row['County']}")
                    if pd.notna(row['OrgURL']):
                        st.markdown(f"[🌐 Website]({row['OrgURL']})", unsafe_allow_html=True)
                    if pd.notna(row['VolunteerListing']):
                        st.markdown(f"[🤝 Volunteer Listing]({row['VolunteerListing']})", unsafe_allow_html=True)
                with cols[1]:
                    st.markdown(f"**About:** {row['About']}")
                    tags = []
                    for col in checkbox_filter_cols:
                        val = row[col]
                        if val is True:
                            tags.append(f"`{col}`")
                    
                    if tags:
                        st.markdown("**Focus Areas:** " + " ".join(tags))
