from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
app = Flask(__name__) # 앱 객체를 여기서 바로 생성

def create_app():
    # TODO: 실제 운영에 맞는 Oracle DB 연결 정보로 수정해야 합니다.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'oracle+cx_oracle://wildfire:1234@localhost:1521/xe'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # db 초기화
    db.init_app(app)

    # 뷰 함수들을 임포트하여 라우트를 앱에 등록
    from .views import predict_views

    # 앱 컨텍스트 내에서 데이터베이스 테이블 생성
    with app.app_context():
        db.create_all()

    return app
