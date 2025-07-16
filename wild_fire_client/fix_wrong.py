import pandas as pd

# 1. 파일 불러오기
df1 = pd.read_csv("fire_duration_hours_only.csv")
dur = df1['fire_duration_hours'].reset_index(drop=True)

df2 = pd.read_csv("preprocess/csv/final_data_with_features_ready.csv")   # 파일명 바꿔줘!

# (6) (혹시 기존 duration 컬럼 있으면 삭제)
if 'fire_duration_hours' in df2.columns:
    df2 = df2.drop(columns=['fire_duration_hours'])

# (7) duration 컬럼 붙이기 (순서만 맞으면 문제 없음!)
df2['fire_duration_hours'] = dur

# (8) 결과 저장
df2.to_csv("final_data_with_features_with_correct_duration_time.csv", index=False, float_format="%.2f")

print("🎉 duration(소수점 단위) 컬럼이 새로 저장되었습니다!")