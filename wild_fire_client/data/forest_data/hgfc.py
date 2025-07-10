import ee
import pandas as pd

# 1. Earth Engine 인증 및 초기화
ee.Authenticate()
ee.Initialize(project='deep-theorem-456805-p2')

# 2. 산불이력 데이터 불러오기
in_csv = "gangwon_fire_ml_input.csv"
df = pd.read_csv(in_csv, encoding='utf-8-sig')

treecover_vals = []
for idx, row in df.iterrows():
    lat, lng = float(row['lat']), float(row['lng'])
    # 대부분 treecover2000(%) 사용, 연도별 갱신 필요시 추가 코드 필요
    try:
        img = ee.Image("UMD/hansen/global_forest_change_2023_v1_10")
        val = img.select('treecover2000').reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=ee.Geometry.Point(lng, lat),
            scale=30  # 30m 해상도
        ).get('treecover2000').getInfo()
        treecover = float(val) if val is not None else None
    except Exception as e:
        print(f"[{idx+1}] 임목밀도 추출 실패: {lat}, {lng} - {e}")
        treecover = None

    treecover_vals.append(treecover)
    if (idx + 1) % 100 == 0:
        print(f"[Hansen] {idx+1}건 처리 완료")

# 3. 결과 컬럼 추가/저장
df['treecover'] = treecover_vals
out_csv = "fire_with_treecover.csv"
df.to_csv(out_csv, index=False, encoding='utf-8-sig')
print(f"최종 저장 완료: {out_csv} ({len(df)}건)")