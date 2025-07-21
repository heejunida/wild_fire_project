import pandas as pd

# CSV 파일 읽기
df = pd.read_csv("final_merged_feature_engineered.csv", encoding='utf-8-sig')

# 엑셀 파일로 저장
df.to_excel("final_merged_feature_engineered.xlsx", index=False)

print("엑셀 파일로 변환 완료: fire_weather_merged_final.xlsx")