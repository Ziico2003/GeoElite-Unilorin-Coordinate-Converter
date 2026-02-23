from flask import Flask, render_template, request, jsonify
from converters import wgs84_to_minna, minna_to_wgs84, minna_to_utm, utm_to_wgs84, to_dms, parse_dms, wgs84_to_utm_wgs84

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert():
    data = request.json
    conv_type = data.get("type")

    try:
        # 1. WGS84 -> Minna
        if conv_type == "wgs_to_minna":
            lat = parse_dms(data["lat"])
            lon = parse_dms(data["lon"])
            m_lat, m_lon = wgs84_to_minna(lat, lon)
            return jsonify({
                "success": True, 
                "lat": round(m_lat, 6), "lon": round(m_lon, 6),
                "lat_dms": to_dms(m_lat, True), "lon_dms": to_dms(m_lon, False)
            })

        # 2. WGS84 -> UTM (Minna)
        elif conv_type == "wgs_to_utm":
            lat = parse_dms(data["lat"])
            lon = parse_dms(data["lon"])
            m_lat, m_lon = wgs84_to_minna(lat, lon)
            zone, e, n, epsg = minna_to_utm(m_lat, m_lon)
            return jsonify({
                "success": True, 
                "zone": zone, 
                "easting": round(e, 3), "northing": round(n, 3)
            })

        # 3. Minna (Geo) -> WGS84
        elif conv_type == "minna_to_wgs":
            lat = parse_dms(data["lat"])
            lon = parse_dms(data["lon"])
            w_lat, w_lon = minna_to_wgs84(lat, lon)
            return jsonify({
                "success": True, 
                "lat": round(w_lat, 6), "lon": round(w_lon, 6),
                "lat_dms": to_dms(w_lat, True), "lon_dms": to_dms(w_lon, False)
            })

        # 4. Minna (Geo) -> Minna UTM (+ Map Coords)
        elif conv_type == "minna_to_utm":
            lat = parse_dms(data["lat"])
            lon = parse_dms(data["lon"])
            # Get Minna UTM
            zone, e, n, epsg = minna_to_utm(lat, lon)
            # Get approx WGS84 for map plotting
            w_lat, w_lon = minna_to_wgs84(lat, lon)
            
            return jsonify({
                "success": True, 
                "zone": zone, 
                "easting": round(e, 3), "northing": round(n, 3),
                "map_lat": w_lat, "map_lon": w_lon
            })

        # 5. Minna (UTM) -> WGS84 (Geo & UTM)
        elif conv_type == "utm_to_wgs":
            e = float(data["easting"])
            n = float(data["northing"])
            zone = int(data["zone"])
            
            # A. Get WGS84 Geographic (Lat/Lon)
            lat, lon = utm_to_wgs84(e, n, zone)
            
            # B. Get WGS84 UTM (Zone/E/N)
            w_zone, w_e, w_n = wgs84_to_utm_wgs84(lat, lon)
            
            return jsonify({
                "success": True, 
                "lat": round(lat, 6), "lon": round(lon, 6),
                "lat_dms": to_dms(lat, True), "lon_dms": to_dms(lon, False),
                "wgs_utm_zone": w_zone,
                "wgs_utm_e": round(w_e, 3),
                "wgs_utm_n": round(w_n, 3)
            })

        return jsonify({"success": False, "error": "Unknown Type"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)