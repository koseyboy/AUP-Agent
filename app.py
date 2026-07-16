import streamlit as st
import pandas as pd
import json

# Import the functions we already wrote in our script
from aup_agent import (
    geocode_auckland_address,
    translate_zone_id_to_name,
    format_landslide_data,
    query_council_gis_layer,
    query_unitary_overlays,
    query_unitary_precincts,
    query_nz_legal_description,
    resolve_iwi_interests,
    ask_ai_planning_expert,
    AUP_KNOWLEDGE_BASE,
    OPENAI_AVAILABLE,
    OPENAI_API_KEY  # Imported from aup_agent as fallback
)

# Set up the browser tab and page layout
st.set_page_config(
    page_title="AUP Feasibility Agent", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("Auckland Unitary Plan Agent")
st.markdown("Zoning, legal, and hazard data.")

# Set up the OpenAI API Key input in the sidebar
with st.sidebar:
    st.header("Credentials")
    user_api_key = st.text_input(
        "OpenAI API Key (Optional)", 
        type="password",
        help="If left blank, the app will use the hardcoded key."
    )

# The address search box
address_input = st.text_input(
    "Enter an Auckland address to analyze:", 
    placeholder="e.g., 16 Laly Haddon Place"
).strip()

if address_input:
    # 1. Geocoding
    with st.spinner("Geocoding address..."):
        lat, lon, full_address = geocode_auckland_address(address_input)
        
    if not lat:
        st.error("Address not found inside New Zealand.")
    else:
        # Create an interactive map at the top of the page
        st.subheader("Property Location")
        map_df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        st.map(map_df, zoom=17, size=20)
        
        st.success(f"**Standardized Address:** {full_address}")
        st.info(f"**Coordinates:** Lat {lat:.6f}, Lon {lon:.6f}")
        
        # 2. Querying Databases
        with st.spinner("Gathering live Council & LINZ GIS records..."):
            # Zone Lookup
            zone_data = query_council_gis_layer(lat, lon, "Unitary_Plan_Base_Zone")
            zone_name = "Non-Standard / Non-Residential"
            if zone_data:
                raw_zone = zone_data[0].get("ZONE")
                if isinstance(raw_zone, int):
                    zone_name = translate_zone_id_to_name(raw_zone)
                else:
                    zone_name = raw_zone
                    
            # Legal, Lot Size & Title
            legal_desc, title_no, lot_size = query_nz_legal_description(lat, lon)
            
            # Hazards & Overlays
            flow_data = query_council_gis_layer(lat, lon, "Overland_Flow_Paths")
            landslide_data = query_council_gis_layer(
                lat, lon, "Large_Scale_Landslide_Susceptibility"
            )
            mana_whenua_data = query_council_gis_layer(
                lat, lon, "Sites_and_Places_of_Significance_to_Mana_Whenua_Overlay"
            )
            overlays = query_unitary_overlays(lat, lon)
            precincts = query_unitary_precincts(lat, lon)
            
            # Matakana backup
            if not precincts and "matakana" in full_address.lower():
                if "single house" in zone_name.lower():
                    precincts.append("Matakana 1 (Sub-precinct B) [Local Match]")
                elif "countryside living" in zone_name.lower():
                    precincts.append("Matakana 1 (Sub-precinct A) [Local Match]")
            
            # Format Hazards
            interpreted_landslide = format_landslide_data(
                landslide_data[0] if landslide_data else None
            )
            hazards = {
                "overland_flow": (
                    "No active Overland Flow Path detected directly on site." 
                    if not flow_data else "ALERT: Overland Flow Path detected."
                ),
                "landslide": interpreted_landslide
            }
            
            mana_status = (
                "No scheduled significance sites directly on coordinate" 
                if not mana_whenua_data 
                else f"ALERT: Scheduled Site! (Name: {mana_whenua_data[0].get('NAME')})"
            )
            
            iwi_profile = resolve_iwi_interests(lat, lon, full_address)
            
            # Match rules and deep copy
            rules_orig = None
            for key, r in AUP_KNOWLEDGE_BASE.items():
                if key.lower() in str(zone_name).lower():
                    rules_orig = r
                    break
            rules = json.loads(json.dumps(rules_orig)) if rules_orig else None
            
            # Apply Matakana overrides
            if precincts and rules:
                for p in precincts:
                    p_lower = p.lower()
                    if "matakana 1 (sub-precinct b)" in p_lower:
                        rules["chapter"] = "Chapter I521 (Matakana 1 Precinct)"
                        rules["front"] = (
                            "5.0m (or average setback of existing adjacent "
                            "buildings, whichever is less) "
                            "[Overridden by Matakana 1 Precinct]"
                        )
                        rules["impervious"] = (
                            "50% max [Overridden by Matakana 1 Precinct]"
                        )
                        rules["desc"] += (
                            " Note: Front fence height limited to 1.2m. "
                            "Front yard requires a tree reaching 5m."
                        )
                        rules["activities"]["2 or more Dwellings"] = (
                            "Restricted Discretionary (RD) if within 200m "
                            "of local centre, otherwise NC"
                        )
                    elif "matakana 1 (sub-precinct a)" in p_lower:
                        rules["chapter"] = "Chapter I521 (Matakana 1 Precinct)"
                        rules["coverage"] = (
                            "500m² max building coverage "
                            "[Overridden by Matakana 1 Precinct]"
                        )
                        rules["impervious"] = (
                            "15% max [Overridden by Matakana 1 Precinct]"
                        )
            
        # =================================================================
        # INTERFACE LAYOUT
        # =================================================================
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.header("Raw Property Details")
            st.metric(label="Official Zoning", value=zone_name)
            
            st.subheader("LINZ Cadastral Details")
            st.write(f"**Legal Description:** {legal_desc}")
            st.write(f"**Certificate of Title:** {title_no}")
            st.write(f"**Lot Size:** {lot_size}")
            
            st.subheader("Base Development Rules")
            if rules:
                st.write(f"**Section:** {rules['chapter']}")
                st.write(f"**Max Height Limit:** {rules['height']}")
                st.write(f"**HIRB Boundary Limit:** {rules['hirb']}")
                st.write(f"**Front Yard Setback:** {rules['front']}")
                st.write(f"**Side/Rear Setback:** {rules['side_rear']}")
                st.write(f"**Building Coverage:** {rules['coverage']}")
                st.write(f"**Impervious Coverage:** {rules['impervious']}")
                st.write(f"**Zone Objective:** {rules['desc']}")
                
                st.write("**Activity Status Table:**")
                for act, status in rules['activities'].items():
                    st.write(f"  • {act}: `{status}`")
            else:
                st.warning("Zoning rules are not pre-indexed.")
                
            st.subheader("Precincts & Overlays")
            if precincts:
                for p in precincts:
                    st.success(f"**Precinct:** {p}")
            else:
                st.write("• No Precincts Detected.")
                
            if overlays:
                for o in overlays:
                    st.warning(f"**Overlay:** {o['layer']} ({o['val']})")
            else:
                st.write("• No Special Overlays Detected.")

        with col2:
            st.header("Geotech, Hazards & Cultural")
            st.subheader("Environmental Hazards")
            st.write(f"**Overland Flow Paths:** {hazards['overland_flow']}")
            st.text(f"Geotechnical Assessment:\n{hazards['landslide']}")
            
            st.subheader("Mana Whenua & Treaty Settlements")
            st.write(f"**Mana Whenua Site Status:** {mana_status}")
            st.write(f"**AUP Appendix 21 District:** {iwi_profile['district']}")
            st.write(f"**Applicable Settlement Acts:** {', '.join(iwi_profile['acts'])}")
            st.write(f"**Statutory Iwi consulted:** {', '.join(iwi_profile['iwi_list'])}")
            
            # AI Report Generator Button
            st.header("AI Town Planning Synthesis")
            
            # Dynamic API key resolution
            api_key_to_use = None
            if user_api_key:
                api_key_to_use = user_api_key
            elif "OPENAI_API_KEY" in st.secrets:
                api_key_to_use = st.secrets["OPENAI_API_KEY"]
            else:
                api_key_to_use = OPENAI_API_KEY
            
            if not api_key_to_use:
                st.warning("Please configure an OpenAI API key.")
            else:
                if st.button("Synthesize Planning Report"):
                    with st.spinner("Analyzing parameters..."):
                        report = ask_ai_planning_expert(
                            api_key_to_use, full_address, zone_name, rules or {}, 
                            hazards, mana_status, iwi_profile, overlays, precincts,
                            legal_desc, title_no, lot_size
                        )
                        st.subheader("AI Planner's Report")
                        st.markdown(report)
