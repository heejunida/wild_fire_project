import requests
import csv
import datetime
import os
import sys
import json

lat = sys.argv[1]
lng = sys.argv[2]

def fetch_nasa_power_weather(lat, lon):
    # 오늘 날짜에서 하루 전 날짜 구하기
    today = datetime.date.today()
    three_days_ago = today - datetime.timedelta(days=3)
    yyyymmdd = three_days_ago.strftime("%Y%m%d")

    url = f"https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=T2M,RH2M,WS2M,WD2M,PRECTOTCORR,PS,ALLSKY_SFC_SW_DWN&community=RE&longitude={lon}&latitude={lat}&start={yyyymmdd}&end={yyyymmdd}&format=JSON"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()["properties"]["parameter"]
    except Exception as e:
        print(json.dumps({"success": False, "error": f"NASA API 요청 실패: {str(e)}"}))
        return

    # 저장할 파일 경로
    filename = f"nasa_power_weather_{yyyymmdd}_{lat}_{lon}.csv"
    filepath = os.path.join(os.path.dirname(__file__), filename)

    # 시간대 리스트 (0~23시)
    hours = [f"{yyyymmdd}{str(h).zfill(2)}" for h in range(24)]

    with open(filepath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # 헤더
        writer.writerow(["hour", "T2M", "RH2M", "WS2M", "WD2M", "PRECTOTCORR", "PS", "ALLSKY_SFC_SW_DWN"])

        for hour in hours:
            writer.writerow([
                hour,
                data["T2M"].get(hour, ""),
                data["RH2M"].get(hour, ""),
                data["WS2M"].get(hour, ""),
                data["PRECTOTCORR"].get(hour, ""),
                data["PS"].get(hour, ""),
                data["ALLSKY_SFC_SW_DWN"].get(hour, "")
            ])

    print(json.dumps({
        "success": True,
        "file": filepath,
        "lat": lat,
        "lng": lon,
        "yyyymmdd": yyyymmdd
    }))


if __name__ == "__main__":
    # ⬇️ 위/경도 인자를 함수에 그대로 전달!
    fetch_nasa_power_weather(lat, lng)