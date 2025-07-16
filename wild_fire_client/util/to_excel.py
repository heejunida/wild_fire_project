import pandas as pd

# CSV 파일 읽기
df = pd.read_csv("data/csv/fire_csv/gangwon_fire_ml_input.csv", encoding='utf-8-sig')

# 엑셀 파일로 저장
df.to_excel("data/csv/fire_csv/gangwon_fire_ml_input.xlsx", index=False)

print("엑셀 파일로 변환 완료: wildfire_data_duration_final.xlsx")