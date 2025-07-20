import pandas as pd
from datetime import datetime

df = pd.read_csv("gangwon_fire_ml_input.csv")

# 인덱스 번호 + 원본 row + duration_hours만 보여줌
for idx, row in df.iterrows():
    # 시작/종료 datetime 문자열 합치기
    try:
        start_str = f"{int(row['startyear']):04d}-{int(row['startmonth']):02d}-{int(row['startday']):02d} {row['starttime']}"
        end_str = f"{int(row['endyear']):04d}-{int(row['endmonth']):02d}-{int(row['endday']):02d} {row['endtime']}"
        start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        duration_hours = (end_dt - start_dt).total_seconds() / 3600
    except Exception as e:
        print(f"[{idx+1}] 파싱 오류: {e}")
        continue

    # “이상값”만 프린트 (예: 음수/0/1000시간 초과/NaN)
    if (duration_hours < 0) or (duration_hours == 0) or (duration_hours > 1000) or pd.isna(duration_hours):
        print(f"[{idx+1}] duration_hours={duration_hours} ▶ {row.to_dict()}")

print("이상 duration_hours 기록만 모두 출력 완료!")