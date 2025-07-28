//package com.wild_fire.DAO;
//
//import java.sql.*;
//import java.util.ArrayList;
//import java.util.HashMap;
//import java.util.List;
//import java.util.Map;
//
//public class WildfireFeaturesDAO {
//    private static WildfireFeaturesDAO instance = null;
//    private Connection conn;
//
//    // 실제로는 DataSource 또는 커넥션풀 사용 권장!
//    public WildfireFeaturesDAO() throws SQLException, ClassNotFoundException {
//        Class.forName("oracle.jdbc.driver.OracleDriver");
//        // 수정: 본인 환경에 맞게!
//        this.conn = DriverManager.getConnection(
//                "jdbc:oracle:thin:@localhost:1521:xe", "YOUR_ID", "YOUR_PW");
//    }
//
//    public static WildfireFeaturesDAO getInstance() throws SQLException, ClassNotFoundException {
//        if (instance == null) instance = new WildfireFeaturesDAO();
//        return instance;
//    }
//
//    // 1. Insert
//    public boolean insertFeatures(Map<String, Object> featureMap) throws SQLException {
//        String sql = "INSERT INTO USER_WILDFIRE_PREDICTIONS (U_ID, LATITUDE, LONGITUDE, FIRE_DATETIME, FEATURES_JSON, PREDICTION_JSON) "
//                + "VALUES (?, ?, ?, ?, ?, ?)";
//        try (PreparedStatement pstmt = conn.prepareStatement(sql)) {
//            pstmt.setObject(1, featureMap.get("U_ID")); // 유저 없으면 null
//            pstmt.setObject(2, featureMap.get("LATITUDE"));
//            pstmt.setObject(3, featureMap.get("LONGITUDE"));
//            // fireDateTimeStr은 "2025-07-25 13:00:00" 형식 String이라고 가정
//            String dtStr = (String) featureMap.get("FIRE_DATETIME");
//            pstmt.setTimestamp(4, Timestamp.valueOf(dtStr));
//            pstmt.setString(5, (String) featureMap.get("FEATURES_JSON")); // feature engineering json
//            pstmt.setString(6, (String) featureMap.get("PREDICTION_JSON")); // prediction json
//
//            int affected = pstmt.executeUpdate();
//            return affected == 1;
//        }
//    }
//
//    // 2. 컬럼명 리스트 반환
//    public List<String> getColumnNames() throws SQLException {
//        List<String> columns = new ArrayList<>();
//        String sql = "SELECT COLUMN_NAME FROM USER_TAB_COLUMNS WHERE TABLE_NAME = 'WILDFIRE_FEATURES' ORDER BY COLUMN_ID";
//        try (PreparedStatement pstmt = conn.prepareStatement(sql);
//             ResultSet rs = pstmt.executeQuery()) {
//            while (rs.next()) columns.add(rs.getString(1));
//        }
//        return columns;
//    }
//
//    // 3. (선택) 모든 데이터 조회 (LIMIT 100)
//    public List<Map<String, Object>> selectAll() throws SQLException {
//        List<Map<String, Object>> results = new ArrayList<>();
//        String sql = "SELECT * FROM WILDFIRE_FEATURES FETCH FIRST 100 ROWS ONLY";
//        try (PreparedStatement pstmt = conn.prepareStatement(sql);
//             ResultSet rs = pstmt.executeQuery()) {
//            ResultSetMetaData meta = rs.getMetaData();
//            int colCount = meta.getColumnCount();
//            while (rs.next()) {
//                Map<String, Object> row = new HashMap<>();
//                for (int i = 1; i <= colCount; i++) {
//                    row.put(meta.getColumnName(i), rs.getObject(i));
//                }
//                results.add(row);
//            }
//        }
//        return results;
//    }
//
//    // (선택) 커넥션 닫기
//    public void close() throws SQLException {
//        if (conn != null && !conn.isClosed()) conn.close();
//    }
//}
