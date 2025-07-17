import pandas as pd

# CSV 파일 읽기
df = pd.read_csv("preprocess/csv/ml_ready_data.csv", encoding='utf-8-sig')

# 엑셀 파일로 저장
df.to_excel("preprocess/csv/ml_ready_data.xlsx", index=False)

print("엑셀 파일로 변환 완료: preprocess/csv/ml_ready_data.xlsx")