import pandas as pd

# 전체 데이터에서 앞에서 10개만 샘플로 추출
INPUT_CSV = "gangwon_fire_ml_input.csv"
OUTPUT_CSV = "gangwon_fire_ml_input_test.csv"

# 원본 데이터 읽기
df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")

# 샘플 10개 추출 (처음 10개, 또는 임의로 뽑으려면 df.sample(10, random_state=42))
df_test = df.head(10)

# 저장
df_test.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
print(f"테스트용 10개 샘플 추출 완료: {OUTPUT_CSV}")