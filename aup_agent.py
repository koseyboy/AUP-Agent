import os
import json
import urllib.parse
import requests

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
    "sk-proj-E4AjMSD74F94Kgu7rjObEYGsMFye4Et6R1GBJoJsTB4UT"
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
# 1. GEOLOCATION & GEOTECHNICAL TOOLS
# =====================================================================
def geocode_auckland_address(address):
    clean = urllib.parse.quote(address + ', Auckland, NZ')
    url = (
        f"https://nominatim.openstreetmap.org/search?"
        f"q={clean}&format=json&limit=1"
    )
    headers = {'User-Agent': 'AUP_Feasibility_v3.3'}
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
        return "Low / No landslide susceptibility recorded."
    
    sus = attributes.get('SusceptibilityValue', 'Unknown')
    conf = attributes.get('Confidence', 'Unknown')
    slope = attributes.get('SUSlope', 0)
    aspect = attributes.get('AspectDirection', 'Unknown')
    zone = attributes.get('Zone', 'Unknown')
    score = attributes.get('TotalScore', 0)
    count = attributes.get('LandslideCount', 0)
    
    summary = [
        f"Risk Rating: {sus.upper()}",
        f"Confidence:  {conf}",
        f"Slope:       {slope:.1f}° facing {aspect}",
        f"Geology:     {zone}",
        f"Score:       {score:.1f}",
        f"Landslides:  {count}"
    ]
    summary.append("\n  [Town Planning Guidance Note]:")
    if sus.lower() in ['low', 'very low']:
        summary.append(
            "  - 'Low/Very Low' rating is favorable. "
            "Standard foundations fine."
        )
        summary.append(
            "  - CPEng stability letter "
            "may be requested by council."
        )
    elif sus.lower() in ['medium', 'moderate']:
        summary.append(
            "  - 'Medium' rating indicates soil movement risk."
        )
        summary.append(
            "  - GIR Report and specialized foundations required."
        )
    elif sus.lower() in ['high', 'very high']:
        summary.append(
            "  - WARNING: High landslide risk. "
            "Structural retaining required."
        )
        summary.append(
            "  - Natural Hazards Resource Consent "
            "(Chapter E36) is triggered."
        )
    return "\n".join(summary)

# =====================================================================
# 2. GIS & OVERLAY/PRECINCT/CADASTRAL ENGINES
# =====================================================================
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
    """
    Queries environmental overlays.
    """
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
    """
    Performs an upgraded direct spatial query on Layer 7 (Precincts).
    Uses a POST payload with outFields=* to fetch all properties,
    safely bypassing mapping scale and field name variations.
    """
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
        'inSR': '4326', # Bypasses Transverse Mercator defaults
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',  # Capture all attributes dynamically
        'returnGeometry': 'false',
        'f': 'json'
    }
    precincts = []
    try:
        res = requests.post(url, data=params, timeout=5).json()
        for f in res.get('features', []):
            attrs = f.get('attributes', {})
            
            # Dynamic attribute scanner
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
            
            # Backups if scanner found no matches
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
    """
    Performs a direct spatial boundary lookup against the unrestricted
    public LINZ NZ Primary Parcels FeatureServer database.
    Returns the appellation (Lot/DP), associated Title, and calculated m2.
    """
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
                "Te Kawerau ā Maki", 
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
# 3. OPENAI AGENT FEASIBILITY NARRATOR
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
# 4. MASTER COORDINATOR
# =====================================================================
def run_agent(address_input, api_key):
    print(f"\n[Agent] Analyzing: {address_input}...")
    lat, lon, full_address = geocode_auckland_address(address_input)
    if not lat:
        print("[Agent Error] Address not found inside New Zealand.")
        return
    print(f"[Agent] Coordinates: Lat {lat:.6f}, Lon {lon:.6f}")
    print(f"[Agent] Address: {full_address}")
    
    print("[Agent] Gathering live Council GIS data...")
    zone_data = query_council_gis_layer(lat, lon, "Unitary_Plan_Base_Zone")
    zone_name = "Non-Standard / Non-Residential"
    if zone_data:
        raw_zone = zone_data[0].get("ZONE")
        if isinstance(raw_zone, int):
            zone_name = translate_zone_id_to_name(raw_zone)
        else:
            zone_name = raw_zone
            
    # Query LINZ Database for legal Lot & DP details + calculated Area
    print("[Agent] Gathering official land parcel cadastre...")
    legal_desc, title_no, lot_size = query_nz_legal_description(lat, lon)
    
    flow_data = query_council_gis_layer(lat, lon, "Overland_Flow_Paths")
    landslide_data = query_council_gis_layer(
        lat, lon, "Large_Scale_Landslide_Susceptibility"
    )
    mana_whenua_data = query_council_gis_layer(
        lat, lon, "Sites_and_Places_of_Significance_to_Mana_Whenua_Overlay"
    )
    
    # Query environmental overlays and precincts separately using optimized methods
    overlays = query_unitary_overlays(lat, lon)
    precincts = query_unitary_precincts(lat, lon)
    
    # Geographic local backup engine for Matakana Precinct Plan
    if not precincts:
        addr_lower = full_address.lower()
        if "matakana" in addr_lower:
            if "single house" in zone_name.lower():
                precincts.append(
                    "Matakana 1 (Sub-precinct B) "
                    "[Local Plan Match]"
                )
            elif "countryside living" in zone_name.lower():
                precincts.append(
                    "Matakana 1 (Sub-precinct A) "
                    "[Local Plan Match]"
                )
            elif "light industry" in zone_name.lower():
                precincts.append(
                    "Matakana 1 (Sub-precinct C) "
                    "[Local Plan Match]"
                )
            elif "local centre" in zone_name.lower():
                precincts.append(
                    "Matakana 1 (Sub-precinct D) "
                    "[Local Plan Match]"
                )
    
    hazards = {
        "overland_flow": (
            "No active Overland Flow Path detected directly on site." 
            if not flow_data else "ALERT: Overland Flow Path detected."
        ),
        "landslide": format_landslide_data(
            landslide_data[0] if landslide_data else None
        )
    }
    
    mana_status = (
        "No scheduled significance sites directly on coordinate" 
        if not mana_whenua_data 
        else f"ALERT: Scheduled Site! (Name: {mana_whenua_data[0].get('NAME')})"
    )
    
    iwi_profile = resolve_iwi_interests(lat, lon, full_address)
    
    # Inlined Zoning Lookup matching logic with safe memory copy
    rules_orig = None
    if zone_name:
        for key, r in AUP_KNOWLEDGE_BASE.items():
            if key.lower() in str(zone_name).lower():
                rules_orig = r
                break
                
    # Create an independent memory copy of rules to prevent lookup leakages
    rules = json.loads(json.dumps(rules_orig)) if rules_orig else None
                
    # =================================================================
    # 5. DYNAMIC PRECINCT OVERRIDES ENGINE
    # =================================================================
    # Intercepts base zone rules and applies Chapter I rules
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
                    "50% max "
                    "[Overridden by Matakana 1 Precinct]"
                )
                rules["desc"] += (
                    " Note: Front fence height limited to 1.2m "
                    "with 25% visual permeability. Front yard "
                    "requires a tree capable of reaching 5m."
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
                    "15% max "
                    "[Overridden by Matakana 1 Precinct]"
                )
                rules["desc"] += (
                    " Note: Accessways must use coloured concrete "
                    "and have visual screening landscaping on both sides."
                )
    
    print("\n" + "="*20 + " RAW GIS DATA CAPTURED " + "="*20)
    print(f"Address:      {full_address}")
    print(f"Legal Desc:   {legal_desc} (Title: {title_no})")
    print(f"Lot Area:     {lot_size}")
    print(f"GIS Zone:     {zone_name}")
    if rules:
        print(f"AUP Section:  {rules['chapter']}")
        print(f"Max Height:   {rules['height']}")
        print(f"HIRB:         {rules['hirb']}")
        print(f"Front Yard:   {rules['front']}")
        print(f"Side/Rear:    {rules['side_rear']}")
        print(f"Building Cov: {rules['coverage']}")
        print(f"Impervious:   {rules['impervious']}")
        print(f"Objective:    {rules['desc']}")
        print("\n--- Activity Statuses (AUP Activity Table) ---")
        for act, status in rules['activities'].items():
            print(f"  {act:<38}: {status}")
    else:
        print("AUP Section:  Residential rules not indexed.")
        
    if precincts:
        print("\n--- AUP Precincts Detected ---")
        for p in precincts:
            print(f"  • {p}")
    else:
        print("\n--- AUP Precincts: None Detected ---")
        
    if overlays:
        print("\n--- Special AUP Overlays Detected ---")
        for o in overlays:
            print(f"  • {o['layer']}: {o['val']}")
    else:
        print("\n--- Special AUP Overlays: None Detected ---")
        
    print(f"\nOverland Flow: {hazards['overland_flow']}")
    print(f"Landslide:    \n{hazards['landslide']}")
    print(f"\nMana Whenua:  {mana_status}")
    print(f"AUP App 21:   District: {iwi_profile['district']}")
    print(f"Relevant iwi: {', '.join(iwi_profile['iwi_list'])}")
    print("="*63 + "\n")
    
    if api_key:
        print("[Agent] Synthesizing Planning Report via AI Planner...")
        report = ask_ai_planning_expert(
            api_key, full_address, zone_name, rules or {}, hazards, 
            mana_status, iwi_profile, overlays, precincts,
            legal_desc, title_no, lot_size
        )
        print(
            "\n================ AI PLANNERS REPORT ================\n" 
            + report + 
            "\n====================================================="
        )
    else:
         print(
             "\n[System Note] OpenAI API key not supplied. "
             "Configure 'OPENAI_API_KEY' for AI brief."
         )

if __name__ == "__main__":
    print("=====================================================")
    print("      Auckland Unitary Plan Feasibility Agent v3.3   ")
    print("=====================================================")
    api_key_to_use = OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
    if not api_key_to_use and OPENAI_AVAILABLE:
        choice = input("Enter OpenAI API Key (or press Enter): ").strip()
        if choice: api_key_to_use = choice
    print("\nType 'exit' or 'quit' to close the program.\n")
    while True:
        user_address = input("Enter an Auckland address: ").strip()
        if user_address.lower() in ['exit', 'quit']: break
        if not user_address: continue
        try:
            run_agent(user_address, api_key_to_use)
        except Exception as e:
            print(f"[System Error] Something went wrong: {e}")
        print("\n" + "="*53 + "\n")