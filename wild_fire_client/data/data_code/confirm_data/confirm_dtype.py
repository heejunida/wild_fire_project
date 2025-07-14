import pandas as pd

df = pd.read_csv('preprocess/csv/datetime_changed_end.csv', encoding='utf-8-sig')
print(df[['start_datetime', 'end_datetime']].head())
print(df['start_datetime'].dtype, df['end_datetime'].dtype)
print(df['start_datetime'].isna().sum(), df['end_datetime'].isna().sum())

print(df['start_datetime'].iloc[0])  # 첫 행 실제 값이 "2021-06-13 14:00:00" 이런지 확인