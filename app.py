import os
import json
import urllib.parse
import requests
import pandas as pd
import streamlit as st

# Graceful check for the 'openai' library
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

# =====================================================================
# CONFIGURATION & DATA STORAGE (8 FULLY INDEXED ZONES)
# =====================================================================
# Your OpenAI key is split to prevent Windows clipboard clipping
OPENAI_API_KEY = (
    "sk-proj-E4AjMSD74F94Kgu"
    "7rjObEYGsMFye4Et6R1GBJoJsTB4UT"
    "9jNhGQQ9eR1paq5NgWPu9kWlh8M19T3BlbkFJtoW_1_zly1jU0H3e"
    "qniv4aOHq-eoivumqp34MLtYRCpaNztRgUzMlRMKwng-E2Sa7AC4Y"
    "_gycA"
)

AUP_KNOWLEDGE_BASE = {
    "Single House": {
        "chapter": "Chapter H3",
        "height": "8m (up to 2 storeys)",
        "hirb": "2.5m + 45° recession plane", 
        "front": "3.0m",
        "side_rear": "1.0m",
        "coverage": "35% max",
        "impervious": "60% max",
        "desc": "Suburban standalone houses, low density.",
        "activities": {
            "1 Standalone Dwelling": (
                "Permitted (P)"
            ),
            "2 or more Dwellings": (
                "Non-Complying (NC)"
            ),
            "Minor Dwelling (up to 65m²)": (
                "Permitted (P) (Max 1 per site)"
            ),
            "Accessory Buildings": (
                "Permitted (P) (Must meet yard rules)"
            )
        }
    },
    "Mixed Housing Suburban": {
        "chapter": "Chapter H4",
        "height": "8m (up to 2 storeys)",
        "hirb": "2.5m + 45° recession plane", 
        "front": "3.0m",
        "side_rear": "1.0m",
        "coverage": "40% max",
        "impervious": "60% max",
        "desc": "Suburban duplexes, standalone, terraces.",
        "activities": {
            "1 to 3 Dwellings": (
                "Permitted (P) (If standards met)"
            ),
            "4 or more Dwellings": (
                "Restricted Discretionary (RD)"
            ),
            "Minor Dwelling": (
                "Permitted (P)"
            ),
            "Accessory Buildings": (
                "Permitted (P) (Must meet yard rules)"
            )
        }
    },
    "Mixed Housing Urban": {
        "chapter": "Chapter H5",
        "height": "11m (up to 3 storeys)",
        "hirb": "3.0m + 45° recession plane", 
        "front": "2.5m",
        "side_rear": "1.0m",
        "coverage": "45% max",
        "impervious": "60% max",
        "desc": "Urban terraces and low-rise apartments.",
        "activities": {
            "1 to 3 Dwellings": (
                "Permitted (P) (If standards met)"
            ),
            "4 or more Dwellings": (
                "Restricted Discretionary (RD)"
            ),
            "Minor Dwelling": (
                "Permitted (P)"
            ),
            "Accessory Buildings": (
                "Permitted (P) (Must meet yard rules)"
            )
        }
    },
    "Terraced Housing and Apartment Buildings": {
        "chapter": "Chapter H6",
        "height": "16m (up to 4 to 5 storeys)",
        "hirb": "3.0m + 45° (or 0m on shared boundary)", 
        "front": "1.5m",
        "side_rear": "1.5m (or 0m shared wall)",
        "coverage": "50% max",
        "impervious": "70% max",
        "desc": "High-density terraces/apartments.",
        "activities": {
            "1 to 3 Dwellings": (
                "Permitted (P) (If standards met)"
            ),
            "4 or more Dwellings": (
                "Restricted Discretionary (RD)"
            ),
            "Minor Dwelling": (
                "Not typical / NC"
            ),
            "Accessory Buildings": (
                "Permitted (P)"
            )
        }
    },
    "Large Lot": {
        "chapter": "Chapter H1",
        "height": "8m (up to 2 storeys)",
        "hirb": "N/A (low intensity boundary buffer)", 
        "front": "10m",
        "side_rear": "6m",
        "coverage": "20% or 400m² (whichever is less)",
        "impervious": "10% or 400m² (whichever is less)",
        "desc": "Spacious residential on urban peripheries.",
        "activities": {
            "1 Standalone Dwelling": (
                "Permitted (P)"
            ),
            "Minor Dwelling": (
                "Restricted Discretionary (RD) (Max 65m²)"
            ),
            "Accessory Buildings": (
                "Permitted (P) (Must meet yard rules)"
            )
        }
    },
    "Rural and Coastal Settlement": {
        "chapter": "Chapter H2",
        "height": "8m (up to 2 storeys)",
        "hirb": "N/A (coastal/rural township scale)", 
        "front": "5m",
        "side_rear": "1.0m to 1.5m",
        "coverage": "20% or 200m² (whichever is less)",
        "impervious": "10% or 200m² (whichever is less)",
        "desc": "Spacious living in coastal/rural townships.",
        "activities": {
            "1 Standalone Dwelling": (
                "Permitted (P)"
            ),
            "Minor Dwelling": (
                "Restricted Discretionary (RD) (Max 65m²)"
            ),
            "Accessory Buildings": (
                "Permitted (P) (Must meet yard rules)"
            )
        }
    },
    "Future Urban": {
        "chapter": "Chapter H18",
        "height": "9m (dwellings and accessory)",
        "hirb": "N/A (rural transition holding zone)", 
        "front": "10m",
        "side_rear": "12m",
        "coverage": "No general limit (controlled by setbacks)",
        "impervious": "No general limit (controlled by setbacks)",
        "desc": "Holding zone for future urban master plans.",
        "activities": {
            "1 Standalone Dwelling": (
                "Permitted (P)"
            ),
            "Minor Dwelling": (
                "Restricted Discretionary (RD) (Site must be > 1ha)"
            ),
            "Accessory Buildings": (
                "Permitted (P) (Must meet yard rules)"
            ),
            "Subdivision": (
                "Non-Complying (NC) (Awaiting live zoning)"
            )
        }
    },
    "Countryside Living": {
        "chapter": "Chapter H19",
        "height": "9m (dwellings and accessory)",
        "hirb": "N/A (lifestyle smallholding buffers)", 
        "front": "10m (20m adjoining arterial roads)",
        "side_rear": "12m",
        "coverage": "No general limit (controlled by setbacks)",
        "impervious": "No general limit (controlled by setbacks)",
        "desc": "Rural lifestyle living and low-density holdings.",
        "activities": {
            "1 Standalone Dwelling": (
                "Permitted (P)"
            ),
            "Minor Dwelling": (
                "Permitted (P) (Site > 1ha, max 65m²)"
            ),
            "Accessory Buildings": (
                "Permitted (P) (Sheds/Garages)"
            ),
            "Farming/Grazing": (
                "Permitted (P) (Low-intensity agriculture)"
            )
        }
    }
}

# =====================================================================
# 1. CORE HELPER FUNCTIONS
# =====================================================================
def geocode_auckland_address(address):
    clean = urllib.parse.quote(address + ', Auckland, NZ')
    url = (
        f"https://nominatim.openstreetmap.org/search?"
        f"q={clean}&format=json&limit=1"
    )
    headers = {'User-Agent': 'AUP_Feasibility_v3.6'}
    try:
        res = requests.get(url, headers=headers, timeout=5).json()
        if res:
            return (
                float(res[0]['lat']), 
                float(res[0]['lon']), 
                res[0]['display_name']
            )
    except Exception as e:
        print(f"[Error] Geocoder: {e}")
    return None, None, None

def translate_zone_id_to_name(zone_id):
    metadata_url = (
        "https://services1.arcgis.com/n4yPwebTjJCmXB6W/"
        "arcgis/rest/services/Unitary_Plan_Base_Zone/"
        "FeatureServer/0?f=json"
    )
    try:
        types = requests.get(metadata_url, timeout=5).json().get('types', [])
        for t in types:
            if str(t.get('id')) == str(zone_id):
                return t.get('name')
    except Exception:
        pass
    
    fallbacks = {
        8: (
            "Residential - Terrace Housing and "
            "Apartment Buildings Zone"
        ),
        18: "Residential - Mixed Housing Suburban Zone",
        19: "Residential - Single House Zone",
        20: (
            "Residential - Rural and Coastal "
            "Settlement Zone"
        ),
        23: "Residential - Large Lot Zone",
        60: "Residential - Mixed Housing Urban Zone",
        61: "Future Urban Zone",
        68: "Rural - Countryside Living Zone"
    }
    return fallbacks.get(zone_id, f"Zone {zone_id}")

def format_landslide_data(attributes):
    if not attributes:
        return "- *Low / No landslide susceptibility recorded.*"
    
    sus = attributes.get('SusceptibilityValue', 'Unknown')
    conf = attributes.get('Confidence', 'Unknown')
    slope = attributes.get('SUSlope', 0)
    aspect = attributes.get('AspectDirection', 'Unknown')
    zone = attributes.get('Zone', 'Unknown')
    score = attributes.get('TotalScore', 0)
    count = attributes.get('LandslideCount', 0)
    
    summary = [
        f"- **Risk Rating:** {sus.upper()}",
        f"- **Confidence:** {conf}",
        f"- **Slope:** {slope:.1f}° facing {aspect}",
        f"- **Geology:** {zone}",
        f"- **Score:** {score:.1f}",
        f"- **Landslides:** {count}",
        "", # Spacer before guidance header
        "**Town Planning Guidance Note:**"
    ]
    if sus.lower() in ['low', 'very low']:
        summary.extend([
            "- *'Low/Very Low' rating is favorable. "
            "Standard foundations fine.*",
            "- *CPEng stability letter "
            "may be requested by council.*"
        ])
    elif sus.lower() in ['medium', 'moderate']:
        summary.extend([
            "- *'Medium' rating indicates soil movement risk.*",
            "- *GIR Report and specialized foundations required.*"
        ])
    elif sus.lower() in ['high', 'very high']:
        summary.extend([
            "- *WARNING: High landslide risk. "
            "Structural retaining required.*",
            "- *Natural Hazards Resource Consent "
            "(Chapter E36) is triggered.*"
        ])
    return "\n".join(summary)

def query_council_gis_layer(lat, lon, service_name):
    url = (
        f"https://services1.arcgis.com/n4yPwebTjJCmXB6W/"
        f"arcgis/rest/services/{service_name}/FeatureServer/0/query"
    )
    params = {
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'false',
        'where': '1=1',
        'f': 'json',
        'geometry': f"{lon},{lat}"
    }
    try:
        res = requests.get(url, params=params, timeout=5).json()
        if 'features' in res and len(res['features']) > 0:
            return [feat['attributes'] for feat in res['features']]
    except Exception:
        pass
    return []

def query_unitary_overlays(lat, lon):
    url = (
        "https://services1.arcgis.com/n4yPwebTjJCmXB6W/"
        "arcgis/rest/services/NonCouncil/"
        "UnitaryPlanManagementLayers/MapServer/identify"
    )
    delta = 0.001
    extent = f"{lon-delta},{lat-delta},{lon+delta},{lat+delta}"
    params = {
        'geometry': f"{lon},{lat}",
        'geometryType': 'esriGeometryPoint',
        'sr': '4326',
        'layers': 'all',
        'tolerance': '2',
        'mapExtent': extent,
        'imageDisplay': '800,800,96',
        'f': 'json'
    }
    
    found = []
    try:
        res = requests.get(url, params=params, timeout=5).json()
        for r in res.get('results', []):
            layer = r.get('layerName')
            attrs = r.get('attributes', {})
            val = attrs.get('NAME') or r.get('value')
            if layer and "address" not in layer.lower():
                if "coastline" not in layer.lower():
                    if layer.lower() != "precincts":
                        if layer not in [o['layer'] for o in found]:
                            found.append({"layer": layer, "val": val})
    except Exception:
        pass
    return found

def query_unitary_precincts(lat, lon):
    url = (
        "https://services1.arcgis.com/n4yPwebTjJCmXB6W/"
        "arcgis/rest/services/NonCouncil/"
        "UnitaryPlanManagementLayers/MapServer/7/query"
    )
    geom = {
        "x": lon,
        "y": lat,
        "spatialReference": {"wkid": 4326}
    }
    params = {
        'geometry': json.dumps(geom),
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'false',
        'f': 'json'
    }
    precincts = []
    try:
        res = requests.post(url, data=params, timeout=5).json()
        for f in res.get('features', []):
            attrs = f.get('attributes', {})
            val = None
            sub = None
            for k, v in attrs.items():
                k_upper = k.upper()
                if "PRECINCT" in k_upper and "SUB" not in k_upper:
                    if v and not val:
                        val = v
                elif "SUB" in k_upper and "PRECINCT" in k_upper:
                    if v:
                        sub = v
            if not val:
                val = attrs.get('PRECINCT') or attrs.get('NAME')
            if not sub:
                sub = attrs.get('SUBPRECINCT')
            if val:
                p_name = str(val)
                if (
                    sub and 
                    str(sub).lower() not in ["null", "none", "nan"]
                ):
                    p_name += f" (Sub-precinct {sub})"
                if p_name not in precincts:
                    precincts.append(p_name)
    except Exception:
        pass
    return precincts

def query_nz_legal_description(lat, lon):
    url = (
        "https://services.arcgis.com/xdsHIIxuCWByZiCB/"
        "arcgis/rest/services/LINZ_NZ_Primary_Parcels/"
        "FeatureServer/0/query"
    )
    geom = {
        "x": lon,
        "y": lat,
        "spatialReference": {"wkid": 4326}
    }
    params = {
        'geometry': json.dumps(geom),
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': 'appellation,titles,calc_area',
        'returnGeometry': 'false',
        'f': 'json'
    }
    try:
        res = requests.post(url, data=params, timeout=5).json()
        features = res.get('features', [])
        if features:
            attrs = features[0].get('attributes', {})
            legal = attrs.get('appellation') or "Unknown Lot/DP"
            title = attrs.get('titles') or "Unknown Title"
            area_val = attrs.get('calc_area')
            area_str = "Unknown"
            if area_val:
                try:
                    area_str = f"{int(float(area_val)):,} m²"
                except Exception:
                    area_str = str(area_val)
            return legal, title, area_str
    except Exception:
        pass
    return "Unknown Lot/DP", "Unknown Title", "Unknown"

def resolve_iwi_interests(lat, lon, address_str):
    profile = {
        "district": "Central Tāmaki", 
        "acts": [], 
        "iwi_list": []
    }
    addr = address_str.lower()
    if lat > -36.60 or "warkworth" in addr or "rodney" in addr:
        profile = {
            "district": "Rodney / North Auckland",
            "acts": [
                "Ngāti Manuhiri Claims Settlement Act 2012", 
                "Te Kawerau ā Maki Claims Settlement Act 2015"
            ],
            "iwi_list": [
                "Ngāti Manuhiri (Warkworth local)", 
                "Te Kawerau ā Maki", 
                "Ngāti Whātua o Kaipara", 
                "Ngāti Wai"
            ]
        }
    elif lon < 174.66 or "waitakere" in addr or "west" in addr:
        profile = {
            "district": "Waitākere / West Auckland",
            "acts": ["Te Kawerau ā Maki Claims Settlement Act 2015"],
            "iwi_list": [
                "Te Kawerau ā Maki (Primary local)", 
                "Ngāti Whātua", 
                "Te Ākitai Waiohua", 
                "Ngāti Te Ata Waiohua"
            ]
        }
    elif lat < -36.95 or "manukau" in addr or "papakura" in addr or "frank" in addr:
        profile = {
            "district": "Manukau / South Auckland",
            "acts": [
                "Ngāti Tamaoho Claims Settlement Act 2018", 
                "Ngāi Tai ki Tāmaki Claims Settlement Act 2018"
            ],
            "iwi_list": [
                "Ngāti Tamaoho", 
                "Ngāti Te Ata Waiohua", 
                "Te Ākitai Waiohua", 
                "Ngāi Tai ki Tāmaki", 
                "Ngāti Paoa"
            ]
        }
    else:
        profile = {
            "district": "Tāmaki Makaurau Isthmus & East",
            "acts": [
                "Ngāti Whātua Ōrākei Claims Settlement Act 2015", 
                "Ngāi Tai ki Tāmaki Claims Settlement Act 2018"
            ],
            "iwi_list": [
                "Ngāti Whātua o Ōrākei", 
                "Ngāi Tai ki Tāmaki", 
                "Ngāti Paoa", 
                "Ngāti Maru", 
                "Te Patukirikiri"
            ]
        }
    return profile

# =====================================================================
# 2. OPENAI AGENT FEASIBILITY NARRATOR
# =====================================================================
def ask_ai_planning_expert(
    api_key, address, zone, rules, hazards, 
    mana, iwi, overlays, precincts, 
    legal, title, lot_size
):
    if not OPENAI_AVAILABLE:
        return "[System Note] OpenAI module not available. AI skipped."
        
    rules_dict = rules or {}
    acts = rules_dict.get('activities', {})
    acts_list = [f"  - {act}: {status}" for act, status in acts.items()]
    overl_list = [f"  - {o['layer']}: {o['val']}" for o in overlays]
    prec_list = [f"  - {p}" for p in precincts]
    
    prompt_lines = [
        "You are an expert Auckland Town Planner.",
        "Write a development brief for this property.",
        "Crucial Note: If any Precinct is detected below,",
        "the Precinct standards from AUP Chapter I override the",
        "corresponding base zone rules (e.g. setbacks, coverage).",
        f"Address: {address}",
        f"Legal Description: {legal} (Record of Title: {title})",
        f"Lot Area: {lot_size}",
        f"Zone: {zone}",
        f"Rules: Chapter={rules_dict.get('chapter', 'N/A')}",
        f"Height={rules_dict.get('height', 'N/A')}",
        f"HIRB={rules_dict.get('hirb', 'N/A')}",
        f"Front={rules_dict.get('front', 'N/A')}",
        f"Side/Rear={rules_dict.get('side_rear', 'N/A')}",
        f"Coverage={rules_dict.get('coverage', 'N/A')}",
        f"Impervious={rules_dict.get('impervious', 'N/A')}",
        "Planning Activity Table Statuses:",
        "\n".join(acts_list) if acts_list else "  - None",
        "Auckland Unitary Plan Precincts Present:",
        "\n".join(prec_list) if prec_list else "  - None",
        "Auckland Unitary Plan Overlays Present:",
        "\n".join(overl_list) if overl_list else "  - None",
        f"Overland Flow: {str(hazards.get('overland_flow', ''))}",
        f"Landslide Risk: {str(hazards.get('landslide', ''))}",
        f"Mana Whenua Site: {str(mana)}",
        f"District: {iwi.get('district', 'Unknown')}",
        f"Acts: {', '.join(iwi.get('acts', []))}",
        f"Statutory Iwi: {', '.join(iwi.get('iwi_list', []))}",
        "Structure the output as follows:",
        "- **AUP Zone & Precinct Overview & Development Potential**",
        "  (Check if any Precinct rules modify or override the base zone rules)",
        "- **Natural Hazards and Civil Challenges**",
        "- **Overlays, Cultural Context and Consultation**",
        "- **Planner's Final Recommendations**",
        "Keep your tone professional, practical, and objective."
    ]
    prompt = "\n".join(prompt_lines)
    
    try:
        response = OpenAI(api_key=api_key).chat.completions.create(
            model="gpt-4o-mini", 
            messages=[{"role": "user", "content": prompt}], 
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[Agent Error] Could not generate AI brief: {e}"

# =====================================================================
# 3. STREAMLIT INTERFACE AND MAIN CONTROLLER
# =====================================================================
st.set_page_config(
    page_title="Auckland Unitary Plan Site Info", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# INJECT COMPACT, STATIC-RENDERING, HIGH-CONTRAST DARK MODE CSS
st.markdown("""
<style>
/* Base configuration */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: #121212 !important; /* Deep dark grey */
}
/* Force headings to be Ultra-Bold, Crisp White, and tight spacing */
h1, h2, h3, .stHeading, 
[data-testid="stMarkdownContainer"] h1, 
[data-testid="stMarkdownContainer"] h2, 
[data-testid="stMarkdownContainer"] h3 {
    font-weight: 800 !important; /* Ultra-bold */
    color: #FFFFFF !important;   /* Crisp Solid White */
    line-height: 1.15 !important; /* Extremely tight heading line-height */
    margin-bottom: 0.4rem !important; /* Tight spacing below */
    margin-top: 1.0rem !important;
}
/* Main App Header Style (Bypasses browser scaling and flashing) */
.custom-app-header {
    font-size: 3.2rem !important;
    font-weight: 800 !important;
    color: #FFFFFF !important;
    line-height: 1.15 !important;
    margin-bottom: 0.6rem !important;
    margin-top: 0.5rem !important;
    display: block !important;
}
h2 {
    font-size: 1.65rem !important; /* Larger section header */
    border-bottom: 2px solid #FFFFFF; /* White underline */
    padding-bottom: 0.3rem;
}
h3 {
    font-size: 1.25rem !important; /* Larger subheader */
}
/* Unified larger body text with tight normal line-height and margins */
p, li, span, label, div, td, th {
    font-size: 1.05rem !important;    /* Larger readable body font */
    line-height: 1.35 !important;     /* Tight standard line-spacing */
    font-weight: 400 !important;      /* Regular weight */
    color: #F8FAFC !important;        /* Bright Slate White */
    margin-bottom: 0.25rem !important; /* Tight block margins */
}
/* Ensure lists are equally tight and bullets are forced to display */
ul, ol {
    margin-bottom: 0.25rem !important;
    padding-left: 1.2rem !important;
}
li {
    list-style-type: disc !important; /* Force browser bullet dots */
    margin-bottom: 0.15rem !important;
    display: list-item !important; /* Ensure standard list-item behavior */
}
/* Target bolded markdown elements */
strong {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}
/* Style Streamlit expander, sidebar, and inputs to match dark mode */
div[data-testid="stExpander"] {
    background-color: #1E1E1E !important;
    border: 1px solid #333333 !important;
}
div[class*="sidebar"] {
    background-color: #1E1E1E !important;
}
input {
    background-color: #2D2D2D !important;
    color: #FFFFFF !important;
    border: 1px solid #444444 !important;
}

/* Responsive CSS query to scale title and spacing for mobile devices */
@media (max-width: 768px) {
    .custom-app-header {
        font-size: 2.3rem !important; /* Stable mobile size, no browser clamping */
    }
    h2 {
        font-size: 1.45rem !important;
    }
    h3 {
        font-size: 1.15rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# STATIC HTML HEADER TO ELIMINATE RE-RENDERING FLASHING
st.markdown(
    "<div class='custom-app-header'>Auckland Unitary Plan Site Info</div>", 
    unsafe_allow_html=True
)
st.markdown("Zoning, legal, and hazard data.")

with st.sidebar:
    st.header("Credentials")
    user_api_key = st.text_input(
        "OpenAI API Key (Optional)", 
        type="password",
        help="If left blank, the app will use the hardcoded key."
    )

address_input = st.text_input(
    "Enter an Auckland address to analyze:", 
    placeholder="e.g., 16 Laly Haddon Place"
).strip()

if address_input:
    with st.spinner("Geocoding address..."):
        lat, lon, full_address = geocode_auckland_address(address_input)
        
    if not lat:
        st.error("Address not found inside New Zealand.")
    else:
        st.success(f"**Standardized Address:** {full_address}")
        st.info(f"**Coordinates:** Lat {lat:.6f}, Lon {lon:.6f}")
        
        # MOVE THE MAP INSIDE AN EXPANDER TO PREVENT MOBILE TOUCH SCROLL TRAPPING
        with st.expander(
            "🗺️ View Interactive Map Location", 
            expanded=False
        ):
            map_df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
            st.map(map_df, zoom=17, size=20)
        
        with st.spinner("Gathering live Council & LINZ GIS records..."):
            zone_data = query_council_gis_layer(lat, lon, "Unitary_Plan_Base_Zone")
            zone_name = "Non-Standard / Non-Residential"
            if zone_data:
                raw_zone = zone_data[0].get("ZONE")
                if isinstance(raw_zone, int):
                    zone_name = translate_zone_id_to_name(raw_zone)
                else:
                    zone_name = raw_zone
                    
            legal_desc, title_no, lot_size = query_nz_legal_description(lat, lon)
            flow_data = query_council_gis_layer(lat, lon, "Overland_Flow_Paths")
            landslide_data = query_council_gis_layer(
                lat, lon, 
                "Large_Scale_Landslide_Susceptibility"
            )
            mana_whenua_data = query_council_gis_layer(
                lat, lon, 
                "Sites_and_Places_of_Significance_"
                "to_Mana_Whenua_Overlay"
            )
            overlays = query_unitary_overlays(lat, lon)
            precincts = query_unitary_precincts(lat, lon)
            
            if not precincts and "matakana" in full_address.lower():
                if "single house" in zone_name.lower():
                    precincts.append("Matakana 1 (Sub-precinct B) [Local Match]")
                elif "countryside living" in zone_name.lower():
                    precincts.append("Matakana 1 (Sub-precinct A) [Local Match]")
            
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
            
            rules_orig = None
            for key, r in AUP_KNOWLEDGE_BASE.items():
                if key.lower() in str(zone_name).lower():
                    rules_orig = r
                    break
            rules = json.loads(json.dumps(rules_orig)) if rules_orig else None
            
            # Apply Precinct Overrides
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

        # UI Columns
        col1, col2 = st.columns([1, 1])
        
        with col1:
            raw_details = [
                "## Raw Property Details",
                f"- **Official Zoning:** **{zone_name}**",
                "",
                "### LINZ Cadastral Details",
                f"- **Legal Description:** {legal_desc}",
                f"- **Certificate of Title:** {title_no}",
                f"- **Lot Size:** {lot_size}",
                "",
                "### Base Development Rules"
            ]
            
            if rules:
                raw_details.extend([
                    f"- **Section:** {rules['chapter']}",
                    f"- **Max Height Limit:** {rules['height']}",
                    f"- **HIRB Boundary Limit:** {rules['hirb']}",
                    f"- **Front Yard Setback:** {rules['front']}",
                    f"- **Side/Rear Setback:** {rules['side_rear']}",
                    f"- **Building Coverage:** {rules['coverage']}",
                    f"- **Impervious Coverage:** {rules['impervious']}",
                    f"- **Zone Objective:** {rules['desc']}",
                    "",
                    "#### **Activity Status Table (AUP Activity Table):**",
                ])
                for act, status in rules['activities'].items():
                    raw_details.append(f"  * **{act}:** `{status}`")
            else:
                raw_details.append(
                    "*Zoning rules are not pre-indexed for this zone type.*"
                )
                
            raw_details.append("\n### Precincts & Overlays")
            if precincts:
                for p in precincts:
                    raw_details.append(f"- **Precinct:** `{p}`")
            else:
                raw_details.append("- No Precincts Detected.")
                
            if overlays:
                for o in overlays:
                    raw_details.append(
                        f"- **Overlay:** `{o['layer']}` ({o['val']})"
                    )
            else:
                raw_details.append("- No Special Overlays Detected.")
                
            # Render Column 1 as a single beautifully compiled Markdown block
            st.markdown(
                "\n".join(raw_details), 
                unsafe_allow_html=True
            )

        with col2:
            col2_details = [
                "## Geotech, Hazards & Cultural",
                "",
                "### Environmental Hazards",
                f"- **Overland Flow Paths:** {hazards['overland_flow']}",
                "",
                "**Geotechnical Assessment:**",
                f"{hazards['landslide']}",
                "", # MANDATORY BLANK LINE BEFORE HTML SPACER
                "<div style='height: 1.2rem;'></div>",
                "", # MANDATORY BLANK LINE AFTER HTML SPACER
                "### Mana Whenua & Treaty Settlements",
                f"- **Mana Whenua Site Status:** {mana_status}",
                f"- **Appendix 21 District:** {iwi_profile['district']}",
                f"- **Settlement Acts:** {', '.join(iwi_profile['acts'])}",
                f"- **Statutory Iwi:** {', '.join(iwi_profile['iwi_list'])}",
                "", # MANDATORY BLANK LINE BEFORE HTML SPACER
                "<div style='height: 1.2rem;'></div>",
                "" # MANDATORY BLANK LINE AFTER HTML SPACER
            ]
            # Render Column 2 details as a single compiled Markdown block
            st.markdown(
                "\n".join(col2_details), 
                unsafe_allow_html=True
            )
            
            # AI Report Generator (With Manual Synthesis Button)
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
                    with st.spinner("Synthesizing Planning Report..."):
                        report = ask_ai_planning_expert(
                            api_key_to_use, full_address, zone_name, rules or {}, 
                            hazards, mana_status, iwi_profile, overlays, precincts,
                            legal_desc, title_no, lot_size
                        )
                        st.subheader("AI Planner's Report")
                        st.markdown(report)
