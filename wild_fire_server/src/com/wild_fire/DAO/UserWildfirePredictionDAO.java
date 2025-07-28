package com.wild_fire.DAO;

import com.wild_fire.util.DBUtil;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.Timestamp;
import java.util.Map;

public class UserWildfirePredictionDAO {

    public boolean insertPrediction(Map<String, Object> params) throws Exception {
        String sql = "INSERT INTO USER_WILDFIRE_PREDICTIONS "
                + "(PRED_ID, U_ID, FIRE_DATETIME, LATITUDE, LONGITUDE, FEATURES_JSON, AREA_PRED, FWI_PRED, DIR_PRED, DISTANCE_PRED) "
                + "VALUES (USER_WILDFIRE_PRED_SEQ.NEXTVAL, ?, ?, ?, ?, ?, ?, ?, ?, ?)";

        try (Connection conn = DBUtil.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {

            // --- U_ID (NUMBER) ---
            Object uIdObj = params.get("U_ID");
            Long uId = null;
            if (uIdObj instanceof Long) {
                uId = (Long) uIdObj;
            } else if (uIdObj instanceof Integer) {
                uId = ((Integer) uIdObj).longValue();
            } else if (uIdObj instanceof String) {
                uId = Long.valueOf((String) uIdObj);
            } else {
                throw new IllegalArgumentException("Invalid U_ID type: " + uIdObj);
            }
            pstmt.setLong(1, uId);

            // --- FIRE_DATETIME (DATE / Timestamp) ---
            Object fireDtObj = params.get("FIRE_DATETIME");
            Timestamp fireDt = null;
            if (fireDtObj instanceof Timestamp) {
                fireDt = (Timestamp) fireDtObj;
            } else if (fireDtObj instanceof java.util.Date) {
                fireDt = new Timestamp(((java.util.Date) fireDtObj).getTime());
            } else if (fireDtObj instanceof String) {
                fireDt = Timestamp.valueOf((String) fireDtObj);
            } else {
                throw new IllegalArgumentException("Invalid FIRE_DATETIME type: " + fireDtObj);
            }
            pstmt.setTimestamp(2, fireDt);

            // --- LATITUDE (NUMBER, Double) ---
            Object latObj = params.get("LATITUDE");
            Double latitude = null;
            if (latObj instanceof Double) {
                latitude = (Double) latObj;
            } else if (latObj instanceof Float) {
                latitude = ((Float) latObj).doubleValue();
            } else if (latObj instanceof String) {
                latitude = Double.parseDouble((String) latObj);
            } else {
                throw new IllegalArgumentException("Invalid LATITUDE type: " + latObj);
            }
            pstmt.setDouble(3, latitude);

            // --- LONGITUDE (NUMBER, Double) ---
            Object lngObj = params.get("LONGITUDE");
            Double longitude = null;
            if (lngObj instanceof Double) {
                longitude = (Double) lngObj;
            } else if (lngObj instanceof Float) {
                longitude = ((Float) lngObj).doubleValue();
            } else if (lngObj instanceof String) {
                longitude = Double.parseDouble((String) lngObj);
            } else {
                throw new IllegalArgumentException("Invalid LONGITUDE type: " + lngObj);
            }
            pstmt.setDouble(4, longitude);

            // --- FEATURES_JSON (CLOB/String) ---
            Object featuresJsonObj = params.get("FEATURES_JSON");
            if (featuresJsonObj == null) {
                pstmt.setString(5, null);
            } else {
                pstmt.setString(5, featuresJsonObj.toString());
            }

            // --- AREA_PRED (NUMBER, Double) ---
            Object areaPredObj = params.get("AREA_PRED");
            Double areaPred = parseDoubleOrNull(areaPredObj);
            if (areaPred == null) {
                pstmt.setNull(6, java.sql.Types.DOUBLE);
            } else {
                pstmt.setDouble(6, areaPred);
            }

            // --- FWI_PRED (NUMBER, Double) ---
            Object fwiPredObj = params.get("FWI_PRED");
            Double fwiPred = parseDoubleOrNull(fwiPredObj);
            if (fwiPred == null) {
                pstmt.setNull(7, java.sql.Types.DOUBLE);
            } else {
                pstmt.setDouble(7, fwiPred);
            }

            // --- DIR_PRED (VARCHAR2(10)) ---
            Object dirPredObj = params.get("DIR_PRED");
            if (dirPredObj == null) {
                pstmt.setString(8, null);
            } else {
                pstmt.setString(8, dirPredObj.toString());
            }

            // --- DISTANCE_PRED (NUMBER, Double) ---
            Object distPredObj = params.get("DISTANCE_PRED");
            Double distPred = parseDoubleOrNull(distPredObj);
            if (distPred == null) {
                pstmt.setNull(9, java.sql.Types.DOUBLE);
            } else {
                pstmt.setDouble(9, distPred);
            }

            // 실행
            int rowsAffected = pstmt.executeUpdate();
            return rowsAffected == 1;
        }
    }

    private Double parseDoubleOrNull(Object obj) {
        if (obj == null) return null;
        if (obj instanceof Double) return (Double) obj;
        if (obj instanceof Float) return ((Float) obj).doubleValue();
        if (obj instanceof Integer) return ((Integer) obj).doubleValue();
        if (obj instanceof Long) return ((Long) obj).doubleValue();
        if (obj instanceof String) {
            try {
                return Double.parseDouble((String) obj);
            } catch (NumberFormatException e) {
                return null;
            }
        }
        return null;
    }
}