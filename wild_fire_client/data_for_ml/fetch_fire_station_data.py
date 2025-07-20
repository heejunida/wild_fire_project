import pandas as pd
import requests
import geopy.distance
import time
import re

# 1. 네이버 지도(Reverse Geocoding)용 키 (좌표→지역명)
NAVER_MAP_CLIENT_ID = "u9o8rfer96"
NAVER_MAP_CLIENT_SECRET = "n9K5W5Vmt7s9BhmoDg7BA4oL8n3m95x5IvwVujX6"

# 2. 네이버 검색(로컬/지역) API용 키 (업체 검색)
NAVER_SEARCH_CLIENT_ID = "_KTZNqpFVXmxJ_PJIrxf"
NAVER_SEARCH_CLIENT_SECRET = "qCTrDjYgkQ"

# (1) 좌표 → 시군구명 변환
def get_area_from_coords(lat, lng, matched_address=None):
    url = "https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_MAP_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_MAP_CLIENT_SECRET
    }
    params = {
        "coords": f"{lng},{lat}",
        "orders": "admcode",
        "output": "json"
    }
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        res.raise_for_status()
        results = res.json().get("results", [])
        if results:
            region = results[0]["region"]
            area2 = region["area2"]["name"]
            return area2
    except Exception:
        pass
    # fallback: address 컬럼에서 시/군/구 추출
    if matched_address:
        m = re.search(r'([가-힣]+(시|군|구))', str(matched_address))
        if m:
            return m.group(1)
    return ""

# (2) 네이버 지역검색 API로 소방서 검색 (최대 10개 반환)
def search_firestations_naver(area_name, display=10):
    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": NAVER_SEARCH_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_SEARCH_CLIENT_SECRET
    }
    params = {
        "query": f"{area_name} 소방서",
        "display": display,
        "sort": "random"
    }
    res = requests.get(url, headers=headers, params=params)
    return res.json().get('items', [])

# (3) 거리계산 util
def calc_distance_km(lat1, lng1, lat2, lng2):
    return geopy.distance.distance((lat1, lng1), (lat2, lng2)).km

# (4) 메인 함수
def add_firestation_features(input_csv, output_csv):
    df = pd.read_csv(input_csv)
    # 추가할 컬럼 미리 선언
    df['nearest_firestation_name'] = None
    df['nearest_firestation_address'] = None
    df['nearest_firestation_roadAddress'] = None
    df['nearest_firestation_dist_km'] = None
    df['firestation_count_3km'] = 0
    df['firestation_count_5km'] = 0
    df['firestation_count_10km'] = 0

    for idx, row in df.iterrows():
        lat, lng = row['lat'], row['lng']
        matched_address = row.get('matched_address', None)
        area_name = get_area_from_coords(lat, lng, matched_address)
        if not area_name:
            print(f"{idx+1}/{len(df)}: 좌표/주소→지역명 변환 실패, 건너뜀")
            continue
        print(f"🔎 {idx+1}/{len(df)}: {area_name} 소방서 검색")

        stations = search_firestations_naver(area_name, display=10)
        if not stations:
            print("  └ 소방서 검색 결과 없음")
            continue

        # 네이버 mapx/y: X=경도, Y=위도 (둘 다 *1e7로 반환)
        try:
            distances = []
            for s in stations:
                s['mapx'] = float(s['mapx'])
                s['mapy'] = float(s['mapy'])
                # 위경도 원복
                slat = s['mapy'] / 1e7
                slng = s['mapx'] / 1e7
                dist = calc_distance_km(lat, lng, slat, slng)
                s['distance_km'] = dist
                distances.append(dist)

            # 최단거리 소방서
            nearest = min(stations, key=lambda s: s['distance_km'])
            df.loc[idx, 'nearest_firestation_name'] = nearest['title']
            df.loc[idx, 'nearest_firestation_address'] = nearest['address']
            df.loc[idx, 'nearest_firestation_roadAddress'] = nearest['roadAddress']
            df.loc[idx, 'nearest_firestation_dist_km'] = nearest['distance_km']

            # 반경별 카운트
            df.loc[idx, 'firestation_count_3km'] = sum(d <= 3 for d in distances)
            df.loc[idx, 'firestation_count_5km'] = sum(d <= 5 for d in distances)
            df.loc[idx, 'firestation_count_10km'] = sum(d <= 10 for d in distances)
            print(f"  └ 최단거리: {nearest['distance_km']:.2f}km / 3km:{df.loc[idx, 'firestation_count_3km']} / 5km:{df.loc[idx, 'firestation_count_5km']} / 10km:{df.loc[idx, 'firestation_count_10km']}")
        except Exception as e:
            print("  └ 거리 계산 실패:", e)
        time.sleep(0.5)  # API 과금 방지

    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"✅ 소방서 피처 추가 완료! -> {output_csv}")

if __name__ == "__main__":
    add_firestation_features("gangwon_fire_ml_input.csv", "gangwon_fire_merged_with_firestation.csv")