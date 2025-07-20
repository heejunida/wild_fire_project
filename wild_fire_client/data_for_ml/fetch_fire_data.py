import requests
import xml.etree.ElementTree as ET
import pandas as pd

# --- 구글맵 주소 변환 ---
def get_coords_from_google(address, google_api_key):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": google_api_key,
        "language": "ko"
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        result = res.json()
        if result["status"] == "OK":
            best = result["results"][0]
            lat = best["geometry"]["location"]["lat"]
            lng = best["geometry"]["location"]["lng"]
            formatted_address = best["formatted_address"]
            return lat, lng, formatted_address
    except Exception as e:
        print(f"[구글맵 변환 실패] '{address}' → {e}")
    return None, None, None

# --- 명칭 자동 보정 함수 ---
def auto_suffix(val, suffix):
    val = str(val).strip()
    if not val:
        return ""
    if val.endswith(suffix):
        return val
    return val + suffix

# --- 시군구가 없을 때 보정 ---
def fill_gungu_if_missing(gungu, eupmyeon_or_dongri, address_name):
    if gungu and gungu.strip():
        return gungu
    addr_parts = address_name.strip().split()
    if len(addr_parts) >= 3:
        return addr_parts[1]
    return gungu

# --- 연도별 화재 데이터 가져오기 ---
def fetch_gangwon_fire_data_by_year_with_eupmyeon(year):
    url = "http://apis.data.go.kr/1400000/forestStusService/getfirestatsservice"
    service_key = "2bsTJckwIyQ5JxI/yhR1H1C6a9cxoUiG16soNk7rVk0iyXtsyjxHPeXcMqpxDBNGO7yM0sBei3knC5A1QOxWxw=="
    start_ymd = f"{year}0101"
    end_ymd = f"{year}1231"
    params = {
        "serviceKey": service_key,
        "searchStDt": start_ymd,
        "searchEdDt": end_ymd,
        "pageNo": "1",
        "numOfRows": "1000",
        "type": "xml",
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.encoding = "utf-8"
        print(f"== {year} 응답 샘플 ==\n", res.text[:800])
        if res.status_code != 200:
            print(f"{year} 요청 실패 (status {res.status_code})")
            return []
        root = ET.fromstring(res.content)
    except Exception as e:
        print(f"{year} 요청 중 오류 발생: {e}")
        return []

    fire_list = []
    for item in root.findall(".//item"):
        locsi = item.findtext("locsi", "").strip()
        if locsi != "강원":
            continue
        startyear = item.findtext("startyear", "")
        startmonth = item.findtext("startmonth", "").zfill(2)
        startday = item.findtext("startday", "").zfill(2)
        starttime = item.findtext("starttime", "").zfill(8)
        endyear = item.findtext("endyear", "")
        endmonth = item.findtext("endmonth", "").zfill(2)
        endday = item.findtext("endday", "").zfill(2)
        endtime = item.findtext("endtime", "").zfill(8)
        fire_date = f"{startyear}-{startmonth}-{startday}"
        gungu = item.findtext("locgungu", "").strip()
        eupmyeon = item.findtext("locmenu", "").strip()
        dongri = item.findtext("locdong", "").strip()
        # 다양한 지번 필드 대응
        jibun = (item.findtext("locbunji", "") or
                 item.findtext("발생장소_지번", "") or
                 item.findtext("bunji", "") or
                 "").strip()
        area_str = item.findtext("damagearea", "0").strip()
        try:
            area = float(area_str)
        except ValueError:
            area = 0.0

        fire_list.append({
            "fire_date": fire_date,
            "startyear": startyear,
            "startmonth": startmonth,
            "startday": startday,
            "starttime": starttime,
            "endyear": endyear,
            "endmonth": endmonth,
            "endday": endday,
            "endtime": endtime,
            "gungu": gungu,
            "eupmyeon": eupmyeon,
            "dongri": dongri,
            "jibun": jibun,
            "fire_area": area,
            "locsi": locsi,
        })
    return fire_list

# --- 주소 후보 생성 및 검색 ---
def get_best_coords_from_address(gungu, eupmyeon, dongri, jibun, google_api_key):
    addr_candidates = []
    g = gungu.strip() if gungu else ""
    e = eupmyeon.strip() if eupmyeon else ""
    d = dongri.strip() if dongri else ""
    j = jibun.strip() if jibun else ""

    # --- 자동 Suffix 보정 ---
    g = auto_suffix(g, "군") if g and not (g.endswith("군") or g.endswith("시")) else g
    e = auto_suffix(e, "면") if e and not (e.endswith("읍") or e.endswith("면")) else e
    d = auto_suffix(d, "리") if d and not d.endswith("리") else d

    # 주소 후보 생성
    if g and e and d and j:
        addr_candidates.append(f"강원도 {g} {e} {d} {j}")
    if g and e and d:
        addr_candidates.append(f"강원도 {g} {e} {d}")
    if g and e and j:
        addr_candidates.append(f"강원도 {g} {e} {j}")
    if g and d and j:
        addr_candidates.append(f"강원도 {g} {d} {j}")
    if e and d and j:
        addr_candidates.append(f"강원도 {e} {d} {j}")
    if g and d:
        addr_candidates.append(f"강원도 {g} {d}")
    if e and d:
        addr_candidates.append(f"강원도 {e} {d}")
    if d and j:
        addr_candidates.append(f"강원도 {d} {j}")
    if d:
        addr_candidates.append(f"강원도 {d}")
    if e and j:
        addr_candidates.append(f"강원도 {e} {j}")
    if e:
        addr_candidates.append(f"강원도 {e}")
    if g and j:
        addr_candidates.append(f"강원도 {g} {j}")
    if g:
        addr_candidates.append(f"강원도 {g}")
    if j:
        addr_candidates.append(j)

    for addr in addr_candidates:
        lat, lng, address_name = get_coords_from_google(addr, google_api_key)
        if lat and lng:
            fixed_gungu = fill_gungu_if_missing(gungu, eupmyeon or dongri, address_name)
            matched_addr = addr
            return lat, lng, matched_addr, fixed_gungu
        else:
            print(f"[주소 검색 실패] {addr}")
    return None, None, None, gungu

# --- 메인 실행부 ---
if __name__ == "__main__":
    google_api_key = "AIzaSyABXxiXwFO_FQFijA_mVbHX8a-z_PLk5bA"  # 본인 키로!
    all_fires = []
    for year in range(2011, 2025):
        yearly_fires = fetch_gangwon_fire_data_by_year_with_eupmyeon(year)
        print(f"{year}년: {len(yearly_fires)}건 수집됨")
        for fire in yearly_fires:
            gungu = fire.get("gungu", "")
            eupmyeon = fire.get("eupmyeon", "")
            dongri = fire.get("dongri", "")
            jibun = fire.get("jibun", "")
            lat, lng, matched_addr, fixed_gungu = get_best_coords_from_address(
                gungu, eupmyeon, dongri, jibun, google_api_key
            )
            fire["lat"] = lat
            fire["lng"] = lng
            fire["matched_address"] = matched_addr
            fire["gungu"] = fixed_gungu  # 자동 보정
        all_fires.extend(yearly_fires)

    df = pd.DataFrame(all_fires)
    for col in ["lat", "lng", "matched_address"]:
        if col not in df.columns:
            df[col] = None

    # 좌표가 매칭된 것만!
    df_clean = df.dropna(subset=["lat", "lng"])
    df_clean.to_csv("gangwon_fire_ml_input.csv", index=False, encoding="utf-8-sig")
    print(f"ML 입력용: {len(df_clean)}건 저장 완료!")