import pandas as pd

df = pd.read_csv('preprocess/csv/datetime_changed.csv', encoding='utf-8-sig')

# end_datetime 만들기 (endyear~endtime이 있다면 우선순위로 사용)
df['end_datetime'] = pd.to_datetime(
    df['endyear'].astype(str) + '-' +
    df['endmonth'].astype(str).str.zfill(2) + '-' +
    df['endday'].astype(str).str.zfill(2) + ' ' +
    df['endtime']
)

# 만약 endyear~endtime 없고 date_end, hour_end 있다면 대체하는 로직도 가능
# (선택사항) 아래처럼 date_end, hour_end도 합쳐서 end_datetime으로 만듦
# df['end_datetime'] = pd.to_datetime(df['date_end'] + ' ' + df['hour_end'])

# 관련 컬럼 삭제
cols_to_drop = ['endyear', 'endmonth', 'endday', 'endtime', 'date_end', 'hour_end']
df.drop(columns=cols_to_drop, inplace=True)

df.to_csv('your_data_with_end_datetime.csv', index=False, encoding='utf-8-sig')