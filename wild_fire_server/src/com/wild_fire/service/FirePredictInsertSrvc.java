//package com.wild_fire.service;
//
//import com.wild_fire.DAO.WildfireFeaturesDAO;
//
//import java.util.Map;
//
//public class FirePredictInsertSrvc {
//
//    public FirePredictInsertSrvc() {}
//
//    /**
//     * 예측/피처 데이터를 WILDFIRE_FEATURES 테이블에 insert
//     * @param featureMap - insert할 컬럼명/값 map (String -> Object)
//     * @return 성공 여부 (true: 1 row 삽입됨)
//     */
//    public boolean insertWildfireFeatures(Map<String, Object> featureMap) {
//        try {
//            WildfireFeaturesDAO dao = WildfireFeaturesDAO.getInstance();
//            return dao.insertFeatures(featureMap);
//        } catch (Exception e) {
//            e.printStackTrace();
//            return false;
//        }
//    }
//}