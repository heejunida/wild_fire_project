import pandas as pd

df = pd.read_csv('all_data_merged_with_treecover.csv', encoding='utf-8-sig')

# 데이터 기본 정보 확인
print(df.info())

# 컬럼별 결측치 확인
print(df.isnull().sum())

# 주요 컬럼 일부 미리보기
print(df.head())

# treecover_pre_fire_5x5 컬럼 통계(결측 포함)
print(df['treecover_pre_fire_5x5'].describe())
print(df['treecover_pre_fire_5x5'].isnull().sum())