import pandas as pd
import requests
import time

# ====== 설정 ======
CSV_FILE = 'preprocess/csv/datetime_changed_end.csv'
VAR_KEYS = ['T2M', 'RH2M', 'WS2M', 'WD2M', 'PRECTOTCORR', 'PS', 'ALLSKY_SFC_SW_DWN']
PT_MAX = 20
API_SLEEP = 1.5

df = pd.read_csv(CSV_FILE)

def get_date_hour_from_datetime(dt_str):
    try:
        dt = pd.to_datetime(dt_str)
        return dt.strftime('%Y%m%d'), dt.strftime('%H')
    except:
        return None, None

def fetch_nasa(lat, lng, yyyymmdd, hour_str):
    url = (
        f"https://power.larc.nasa.gov/api/temporal/hourly/point?"
        f"parameters={','.join(VAR_KEYS)}"
        f"&community=RE&longitude={lng}&latitude={lat}&start={yyyymmdd}&end={yyyymmdd}&format=JSON"
    )
    try:
        res = requests.get(url, timeout=30)
        res.raise_for_status()
        data = res.json().get("properties", {}).get("parameter", {})
        hour_key = f"{yyyymmdd}{hour_str.zfill(2)}"
        return {k: data.get(k, {}).get(hour_key, None) for k in VAR_KEYS}
    except Exception as e:
        print("NASA API ERROR:", e)
        return {k: None for k in VAR_KEYS}

def is_float_equal(val1, val2, tol=0.01):
    try:
        f1, f2 = float(val1), float(val2)
        return abs(f1 - f2) < tol
    except:
        return str(val1).strip() == str(val2).strip()

def get_duration(row):
    try:
        s = pd.to_datetime(row['start_datetime'])
        e = pd.to_datetime(row['end_datetime'])
        return (e - s).total_seconds() / 3600
    except:
        return 0

df['duration_hr'] = df.apply(get_duration, axis=1)
df_4h = df[df['duration_hr'] >= 4].copy()

print(f"\n[전체 {len(df_4h)}개 4시간 이상 row 검증 시작]\n")

for idx, row in df_4h.iterrows():
    lat, lng = row['lat'], row['lng']
    print(f"\n=== [{idx}] {row['fire_date']} {lat:.6f},{lng:.6f} | {row['start_datetime']} ~ {row['end_datetime']} ===")
    points = []
    start_yyyymmdd, start_hour = get_date_hour_from_datetime(row['start_datetime']) if not pd.isnull(row.get('start_datetime')) else (None, None)
    # start
    if start_yyyymmdd and start_hour:
        points.append(('start', start_yyyymmdd, start_hour))
    # end
    end_yyyymmdd, end_hour = get_date_hour_from_datetime(row['end_datetime']) if not pd.isnull(row.get('end_datetime')) else (None, None)
    if end_yyyymmdd and end_hour:
        points.append(('end', end_yyyymmdd, end_hour))
    # mid
    if not pd.isnull(row.get('date_mid')) and not pd.isnull(row.get('hour_mid')):
        yyyymmdd = str(row['date_mid'])[:8].replace('.0', '')
        hour_str = str(int(row['hour_mid'])).zfill(2)
        points.append(('mid', yyyymmdd, hour_str))
    # pt1~ptN
    pt1_yyyymmdd, pt1_hour_str = None, None
    for i in range(1, PT_MAX+1):
        dcol, hcol = f'date_pt{i}', f'hour_pt{i}'
        if dcol in row and hcol in row and not (pd.isnull(row[dcol]) or pd.isnull(row[hcol])):
            yyyymmdd = str(row[dcol])[:8].replace('.0', '')
            hour_str = str(int(row[hcol])).zfill(2)
            points.append((f'pt{i}', yyyymmdd, hour_str))
            if i == 1:
                pt1_yyyymmdd, pt1_hour_str = yyyymmdd, hour_str
    # === pt1과 start 시각 비교해서 경고 ===
    if pt1_yyyymmdd and pt1_hour_str and start_yyyymmdd and start_hour:
        if (pt1_yyyymmdd == start_yyyymmdd) and (pt1_hour_str == start_hour):
            print(f"\n⚠️  [경고] pt1이 start와 같은 시각입니다! (start={start_yyyymmdd} {start_hour}, pt1={pt1_yyyymmdd} {pt1_hour_str})")
            print("    → 이 row는 'start'가 pt1에 중복 저장된 옛날 방식일 가능성이 있습니다. 전처리 코드를 반드시 다시 점검하세요.\n")

    # ==== 포인트별 비교 ====
    for tag, yyyymmdd, hour_str in points:
        nasa_vals = fetch_nasa(lat, lng, yyyymmdd, hour_str)
        csv_vals = {k: row.get(f"{k}_{tag}", None) for k in VAR_KEYS}
        ok = True
        for k in VAR_KEYS:
            equal = is_float_equal(csv_vals[k], nasa_vals[k])
            mark = "" if equal else "❌"
            if not equal:
                ok = False
            print(f"  [{tag}] {k}: CSV={csv_vals[k]} | NASA={nasa_vals[k]} {mark}")
        if ok:
            print(f"    → [{tag}] ALL OK")
        else:
            print(f"    → [{tag}] 불일치 있음!")
        time.sleep(API_SLEEP)

print("\n[검증 완료] (불일치는 '❌', pt1= start 중복은 '⚠️'로 경고)")