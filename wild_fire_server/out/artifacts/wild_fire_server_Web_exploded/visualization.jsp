<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ page import="org.json.simple.JSONObject" %>
<%
    // Get the prediction data object passed from the servlet
    JSONObject data = (JSONObject) request.getAttribute("predictionData");

    // Set default values if data is null (for testing or direct access)
    double lat = 37.7976;
    double lng = 128.2218;
    double distance = 50.0;
    double direction = 270.0;

    if (data != null) {
        lat = ((Number) data.getOrDefault("lat", lat)).doubleValue();
        lng = ((Number) data.getOrDefault("lng", lng)).doubleValue();
        distance = ((Number) data.getOrDefault("predicted_distance_m", distance)).doubleValue();
        direction = ((Number) data.getOrDefault("wind_direction_deg", direction)).doubleValue();
    }
%>
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Wildfire Spread Visualization</title>
    <style>
        html, body, #map {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
        }
    </style>
</head>
<body>
<div id="map"></div>

<script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey=YOUR_APP_KEY&libraries=services"></script>
<script>
    // --- Data is now passed dynamically from the JSP scriptlet ---
    const predictionData = {
        lat: <%= lat %>,
        lng: <%= lng %>,
        predicted_distance_m: <%= distance %>,
        wind_direction_deg: <%= direction %>
    };

    // Initialize the map when the page loads
    document.addEventListener("DOMContentLoaded", function() {
        // Check if a valid direction was provided
        if (predictionData.wind_direction_deg <= -999.0) {
            // Handle case with no wind data
            alert("Wind direction data is not available. Only the potential area will be shown.");
        }
        initMap(
            predictionData.lat,
            predictionData.lng,
            predictionData.predicted_distance_m,
            predictionData.wind_direction_deg
        );
    });

    function initMap(lat, lng, distance, direction) {
        const mapContainer = document.getElementById('map');
        const centerPosition = new kakao.maps.LatLng(lat, lng);

        const map = new kakao.maps.Map(mapContainer, {
            center: centerPosition,
            level: 6
        });

        // 1. Marker at the origin
        new kakao.maps.Marker({ map: map, position: centerPosition });

        // 2. Circle for the potential area
        new kakao.maps.Circle({
            map: map,
            center: centerPosition,
            radius: distance,
            strokeWeight: 2,
            strokeColor: '#FF0000',
            strokeOpacity: 0.8,
            strokeStyle: 'solid',
            fillColor: '#FF0000',
            fillOpacity: 0.2
        });

        // 3. Polyline for the direction (only if direction is valid)
        if (direction > -999.0) {
            const arrowEndpoint = getEndpoint(lat, lng, direction, distance);
            new kakao.maps.Polyline({
                map: map,
                path: [centerPosition, new kakao.maps.LatLng(arrowEndpoint.lat, arrowEndpoint.lng)],
                strokeWeight: 4,
                strokeColor: '#0000FF',
                strokeOpacity: 0.8,
                endArrow: true
            });
        }
    }

    function getEndpoint(lat, lng, bearing, distance) {
        const R = 6371000; // Earth's radius in meters
        const bearingRad = toRadians(bearing);
        const latRad = toRadians(lat);
        const lngRad = toRadians(lng);

        const newLatRad = Math.asin(Math.sin(latRad) * Math.cos(distance / R) +
                          Math.cos(latRad) * Math.sin(distance / R) * Math.cos(bearingRad));
        const newLngRad = lngRad + Math.atan2(Math.sin(bearingRad) * Math.sin(distance / R) * Math.cos(latRad),
                                     Math.cos(distance / R) - Math.sin(latRad) * Math.sin(newLatRad));
        return { lat: toDegrees(newLatRad), lng: toDegrees(newLngRad) };
    }

    function toRadians(degrees) { return degrees * Math.PI / 180; }
    function toDegrees(radians) { return radians * 180 / Math.PI; }

</script>
</body>
</html>
