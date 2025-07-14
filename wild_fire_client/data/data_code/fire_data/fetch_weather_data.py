# fetch_weather_data.py
import requests
import csv
import datetime
import os
import sys
import json
import traceback

# 인자: 위도, 경도, (선택)yyyymmdd
try:
    lat = sys.argv[1]
    lng = sys.argv[2]
    if len(sys.argv) > 3:
        yyyymmdd = sys.argv[3]
    else:
        today = datetime.date.today()
        three_days_ago = today - datetime.timedelta(days=4)
        yyyymmdd = three_days_ago.strftime("%Y%m%d")
except Exception:
    print(
        json.dumps(
            {
                "success": False,
                "error": "인자 부족! 사용법: python fetch_weather_data.py lat lng [yyyymmdd]",
                "traceback": traceback.format_exc(),
            }
        )
    )
    sys.exit(2)


def fetch_nasa_power_weather(lat, lon, yyyymmdd):
    url = f"https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=T2M,RH2M,WS2M,WD2M,PRECTOTCORR,PS,ALLSKY_SFC_SW_DWN&community=RE&longitude={lon}&latitude={lat}&start={yyyymmdd}&end={yyyymmdd}&format=JSON"
    try:
        res = requests.get(url)
        res.raise_for_status()
        j = res.json()
        # 🚩 KeyError/TypeError 안전하게 처리!
        data = j.get("properties", {}).get("parameter", None)
        if data is None:
            print(
                json.dumps(
                    {
                        "success": False,
                        "error": "NASA 응답에 parameter 없음",
                        "lat": lat,
                        "lng": lon,
                        "yyyymmdd": yyyymmdd,
                        "response": j,
                    }
                )
            )
            return
    except Exception as e:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": f"NASA API 요청 실패: {str(e)}",
                    "lat": lat,
                    "lng": lon,
                    "yyyymmdd": yyyymmdd,
                    "traceback": traceback.format_exc(),
                }
            )
        )
        sys.exit(2)
        return

    filename = f"nasa_power_weather_{yyyymmdd}_{lat}_{lon}.csv"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    hours = [f"{yyyymmdd}{str(h).zfill(2)}" for h in range(24)]

    with open(filepath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "hour",
                "T2M",
                "RH2M",
                "WS2M",
                "WD2M",
                "PRECTOTCORR",
                "PS",
                "ALLSKY_SFC_SW_DWN",
            ]
        )
        for hour in hours:
            writer.writerow(
                [
                    hour,
                    data.get("T2M", {}).get(hour, ""),
                    data.get("RH2M", {}).get(hour, ""),
                    data.get("WS2M", {}).get(hour, ""),
                    data.get("WD2M", {}).get(hour, ""),
                    data.get("PRECTOTCORR", {}).get(hour, ""),
                    data.get("PS", {}).get(hour, ""),
                    data.get("ALLSKY_SFC_SW_DWN", {}).get(hour, ""),
                ]
            )
    print(
        json.dumps(
            {
                "success": True,
                "file": filepath,
                "lat": lat,
                "lng": lon,
                "yyyymmdd": yyyymmdd,
            }
        )
    )


if __name__ == "__main__":
    fetch_nasa_power_weather(lat, lng, yyyymmdd)
