import bcrypt
import sys
import os
from flask import Flask, request, jsonify, session, render_template
from flask_session import Session
import bcrypt
import oracledb
import json

# --- Add client directory to path to import the pipeline ---
# This allows us to import modules from the 'wild_fire_client' directory
CLIENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'wild_fire_client'))
sys.path.insert(0, CLIENT_DIR)

from api.pipeline import run_feature_pipeline
from db import get_db_connection

app = Flask(__name__)

# Session configuration
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Page rendering routes
@app.route('/')
def main_page():
    return render_template('main.html', user=session.get('user'))

@app.route('/detail')
def detail():
    return render_template('detail.html', user=session.get('user'))

@app.route('/about-us')
def about_us():
    return render_template('aboutUs.html')

# API routes
@app.route('/fire-predict', methods=['POST'])
def fire_predict():
    if 'user' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    lat_str = request.form.get('lat')
    lng_str = request.form.get('lng')
    fire_date = request.form.get('fireDate')
    fire_time = request.form.get('fireTime')

    if not all([lat_str, lng_str, fire_date, fire_time]):
        return jsonify({"status": "error", "message": "Missing required parameters"}), 400

    try:
        lat = float(lat_str)
        lng = float(lng_str)
        
        # Call the pipeline function directly
        _, final_prediction = run_feature_pipeline(lat, lng, fire_date, fire_time)
        
        return jsonify(final_prediction)

    except ValueError:
        return jsonify({"status": "error", "message": "Invalid latitude or longitude format."}), 400
    except Exception as e:
        # The pipeline already prints detailed errors, so we can return a generic message
        print(f"An error occurred during the prediction pipeline: {e}")
        # Include the error message in the response for better debugging on the client
        return jsonify({"status": "error", "message": "An error occurred during prediction.", "details": str(e)}), 500

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    user_id = data.get('user_id')
    user_raw_pw = data.get('user_pw')
    user_name = data.get('user_name')

    if not all([user_id, user_raw_pw, user_name]):
        return jsonify({"result": "fail", "message": "모든 필드를 입력해주세요."}), 400

    user_hashed_pw = bcrypt.hashpw(user_raw_pw.encode('utf-8'), bcrypt.gensalt())

    conn = get_db_connection()
    if not conn:
        return jsonify({"result": "error", "message": "데이터베이스 연결에 실패했습니다."}), 500
    
    cursor = conn.cursor()
    sql = "INSERT INTO users (u_id, user_id, user_pw, user_name) VALUES (users_seq.NEXTVAL, :1, :2, :3)"
    
    try:
        cursor.execute(sql, [user_id, user_hashed_pw.decode('utf-8'), user_name])
        conn.commit()
        return jsonify({"result": "success"})
    except oracledb.IntegrityError:
        conn.rollback()
        return jsonify({"result": "fail", "message": "이미 존재하는 아이디입니다."}), 409
    except oracledb.DatabaseError as e:
        conn.rollback()
        print(f"Database error: {e}")
        return jsonify({"result": "error", "message": "서버 오류가 발생했습니다."}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('user_id')
    password = data.get('user_pw')

    if not user_id or not password:
        return jsonify({"status": "error", "message": "아이디와 비밀번호를 모두 입력해주세요."}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "데이터베이스 연결 실패"}), 500
        
    cursor = conn.cursor()
    sql = "SELECT u_id, user_pw FROM users WHERE user_id = :1"
    
    try:
        cursor.execute(sql, [user_id])
        result = cursor.fetchone()
        
        if result:
            u_id, db_password_hash = result
            if bcrypt.checkpw(password.encode('utf-8'), db_password_hash.encode('utf-8')):
                session["user"] = user_id
                session["u_id"] = u_id
                return jsonify({"status": "success", "message": "로그인 성공"})
            else:
                return jsonify({"status": "fail", "message": "아이디 또는 비밀번호가 일치하지 않습니다."})
        else:
            return jsonify({"status": "fail", "message": "아이디 또는 비밀번호가 일치하지 않습니다."})
            
    except oracledb.DatabaseError as e:
        print(f"Database error: {e}")
        return jsonify({"status": "error", "message": "로그인 처리 중 오류가 발생했습니다."}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user', None)
    session.pop('u_id', None)
    return jsonify({"result": "logout"})

@app.route('/findId', methods=['POST'])
def find_id():
    data = request.get_json()
    user_name = data.get('user_name')

    conn = get_db_connection()
    if not conn:
        return jsonify({"result": "fail", "message": "DB 연결 실패"}), 500

    cursor = conn.cursor()
    sql = "SELECT user_id FROM users WHERE user_name = :1"
    try:
        cursor.execute(sql, [user_name])
        result = cursor.fetchone()
        if result:
            return jsonify({"result": "success", "user_id": result[0]})
        else:
            return jsonify({"result": "fail"})
    except oracledb.DatabaseError as e:
        print(f"Database error: {e}")
        return jsonify({"result": "fail", "message": "오류 발생"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/findPw', methods=['POST'])
def find_pw():
    data = request.get_json()
    user_id = data.get('user_id')
    user_name = data.get('user_name')

    conn = get_db_connection()
    if not conn:
        return jsonify({"result": "fail", "message": "DB 연결 실패"}), 500

    cursor = conn.cursor()
    sql = "SELECT COUNT(*) FROM users WHERE user_id = :1 AND user_name = :2"
    try:
        cursor.execute(sql, [user_id, user_name])
        result = cursor.fetchone()
        if result and result[0] > 0:
            return jsonify({"result": "success"})
        else:
            return jsonify({"result": "fail"})
    except oracledb.DatabaseError as e:
        print(f"Database error: {e}")
        return jsonify({"result": "fail", "message": "오류 발생"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/resetPw', methods=['POST'])
def reset_pw():
    data = request.get_json()
    user_id = data.get('user_id')
    old_pw = data.get('old_pw')
    new_pw = data.get('new_pw')

    conn = get_db_connection()
    if not conn:
        return jsonify({"result": "fail", "msg": "DB 연결 실패"}), 500

    cursor = conn.cursor()
    try:
        # 1. DB에서 기존 해시값 가져오기
        cursor.execute("SELECT user_pw FROM users WHERE user_id = :1", [user_id])
        result = cursor.fetchone()
        if not result:
            return jsonify({"result": "fail", "msg": "비밀번호 정보가 없습니다."})
        
        db_hash = result[0]
        if not bcrypt.checkpw(old_pw.encode('utf-8'), db_hash.encode('utf-8')):
            return jsonify({"result": "wrongpw"})

        # 2. 새 비번 해시해서 업데이트
        new_hash = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("UPDATE users SET user_pw = :1 WHERE user_id = :2", [new_hash, user_id])
        conn.commit()
        
        session.pop('user', None)
        session.pop('u_id', None)
        return jsonify({"result": "success"})

    except oracledb.DatabaseError as e:
        conn.rollback()
        print(f"Database error: {e}")
        return jsonify({"result": "fail", "msg": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/resetPwWithoutOld', methods=['POST'])
def reset_pw_without_old():
    data = request.get_json()
    user_id = data.get('user_id')
    new_pw = data.get('new_pw')

    if not user_id or not new_pw:
        return jsonify({"result": "fail", "msg": "필수값 누락"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"result": "fail", "msg": "DB 연결 실패"}), 500
        
    cursor = conn.cursor()
    try:
        new_hash = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("UPDATE users SET user_pw = :1 WHERE user_id = :2", [new_hash, user_id])
        conn.commit()
        return jsonify({"result": "success"})
    except oracledb.DatabaseError as e:
        conn.rollback()
        print(f"Database error: {e}")
        return jsonify({"result": "fail", "msg": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
