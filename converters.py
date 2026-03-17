from pyproj import Transformer, CRS
import re

# --- BUG 1 FIX: Explicitly add the 3-Parameter Datum Shift for Nigeria ---
# Instead of CRS.from_epsg(4263) which often fails to shift, we use the PROJ string
crs_wgs84 = CRS.from_epsg(4326)
crs_minna = CRS.from_string("+proj=longlat +ellps=clrk80 +towgs84=-92,-93,122,0,0,0,0 +no_defs")

# --- 1. SMART INPUT PARSER ---
def parse_dms(value):
    """Extracts numbers from any format (decimal or DMS) and converts to decimal degrees."""
    if not value: return 0.0
    
    parts = re.findall(r'-?\d+\.?\d*', str(value))
    
    if not parts:
        return 0.0

    try:
        if len(parts) == 1:
            return float(parts[0]) 
        elif len(parts) >= 2:
            d = float(parts[0])
            m = float(parts[1])
            s = float(parts[2]) if len(parts) >= 3 else 0.0
            
            # Safely handle negative coordinates
            sign = -1 if d < 0 or str(value).strip().startswith('-') else 1
            return sign * (abs(d) + (m / 60.0) + (s / 3600.0))
    except ValueError:
        return 0.0
        
    return 0.0

# --- 2. OUTPUT HELPER ---
def to_dms(deg, is_lat=True):
    """Converts decimal degrees to a clean DMS string."""
    if deg is None: return ""
    
    direction = 'N' if is_lat else 'E'
    if deg < 0:
        direction = 'S' if is_lat else 'W'
        deg = abs(deg)
    
    d = int(deg)
    m_float = (deg - d) * 60
    m = int(m_float)
    s = (m_float - m) * 60
    
    # Prevent the weird "60.0000 seconds" rounding error
    if s >= 59.9999:
        s = 0.0
        m += 1
    if m >= 60:
        m = 0
        d += 1
        
    return f"{d}° {m}' {s:.4f}\" {direction}"

# --- 3. CONVERSION LOGIC ---

def wgs84_to_minna(lat, lon):
    transformer = Transformer.from_crs(crs_wgs84, crs_minna, always_xy=True)
    m_lon, m_lat = transformer.transform(lon, lat)
    return m_lat, m_lon

def minna_to_wgs84(lat, lon):
    transformer = Transformer.from_crs(crs_minna, crs_wgs84, always_xy=True)
    w_lon, w_lat = transformer.transform(lon, lat)
    return w_lat, w_lon

def minna_to_utm(lat, lon):
    # Determine Nigeria UTM zone based on longitude bounds
    if lon <= 6: zone = 31
    elif lon <= 12: zone = 32
    else: zone = 33
    
    # --- BUG 2 FIX: Ensure exact UTM projections with Datum Shift ---
    epsg_code = 26300 + zone
    proj_str = f"+proj=utm +zone={zone} +ellps=clrk80 +towgs84=-92,-93,122,0,0,0,0 +units=m +no_defs"
    crs_minna_utm = CRS.from_string(proj_str)
    
    transformer = Transformer.from_crs(crs_minna, crs_minna_utm, always_xy=True)
    easting, northing = transformer.transform(lon, lat)
    return zone, easting, northing, epsg_code

def utm_to_wgs84(easting, northing, zone):
    # Use explicit string to ensure it successfully shifts back to WGS84
    proj_str = f"+proj=utm +zone={zone} +ellps=clrk80 +towgs84=-92,-93,122,0,0,0,0 +units=m +no_defs"
    crs_minna_utm = CRS.from_string(proj_str)
    
    transformer = Transformer.from_crs(crs_minna_utm, crs_wgs84, always_xy=True)
    lon, lat = transformer.transform(easting, northing)
    return lat, lon

def wgs84_to_utm_wgs84(lat, lon):
    # Takes WGS84 Lat/Lon -> WGS84 UTM (Zone 31/32/33N)
    zone = int((lon + 180) / 6) + 1
    
    # EPSG for WGS84 UTM North is 326xx
    epsg = 32600 + zone
    
    transformer = Transformer.from_crs(crs_wgs84, CRS.from_epsg(epsg), always_xy=True)
    e, n = transformer.transform(lon, lat)
    return zone, e, n
