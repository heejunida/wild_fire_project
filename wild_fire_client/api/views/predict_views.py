from flask import request, jsonify
import json

# 앱 팩토리에서 생성된 app과 db 객체를 임포트합니다.
from .. import app, db
from ..models import PredictionLog
from ..pipeline import run_feature_pipeline # 새로 만든 파이프라인 함수를 임포트

@app.route('/predict', methods=['POST'])
def do_prediction():
    data = request.get_json()
    lat = data.get('lat')
    lng = data.get('lng')
    fire_date_str = data.get('fireDate')
    fire_time_str = data.get('fireTime')

    if not all([lat, lng, fire_date_str, fire_time_str]):
        return jsonify({"status": "error", "message": "Missing required parameters"}), 400

    try:
        # 파이프라인 함수를 한 번만 호출하여 모든 데이터를 처리하고 예측까지 수행
        engineered_features, final_prediction = run_feature_pipeline(
            float(lat), float(lng), fire_date_str, fire_time_str
        )

        # 데이터베이스에 결과 저장
        if final_prediction.get("status") == "success":
            try:
                new_log = PredictionLog(
                    latitude=float(lat),
                    longitude=float(lng),
                    area_pred_high=final_prediction.get("area_pred_high"),
                    area_pred_median=final_prediction.get("area_pred_median"),
                    area_pred_low=final_prediction.get("area_pred_low"),
                    dir_pred=final_prediction.get("dir_pred"),
                    fwi_pred=final_prediction.get("fwi_pred"),
                    distance_pred=final_prediction.get("distance_pred"),
                    features_json=json.dumps(engineered_features)
                )
                db.session.add(new_log)
                db.session.commit()
            except Exception as db_error:
                print(f"Database logging failed: {db_error}")
                db.session.rollback()
        
        return jsonify(final_prediction)

    except Exception as e:
        print(f"An error occurred in the prediction pipeline: {e}")
        # 클라이언트에게 더 친절한 에러 메시지를 반환할 수 있습니다.
        return jsonify({"status": "error", "message": "An internal error occurred during prediction."}), 500
