import pandas as pd

# CSV 파일 읽기
df = pd.read_csv("fire_with_forest_type_mode5x5_filled.csv", encoding='utf-8-sig')

# 엑셀 파일로 저장
df.to_excel("fire_with_forest_type_mode5x5_filled.xlsx", index=False)

print("엑셀 파일로 변환 완료: fire_with_forest_type_mode5x5_filled.xlsx")