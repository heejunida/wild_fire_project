import pandas as pd
import numpy as np

df = pd.read_csv("final_data.csv")

target_vars = [
    "T2M", "RH2M", "WS2M", "WS10M", "WD2M", "WD10M",
    "PRECTOTCORR", "PS", "ALLSKY_SFC_SW_DWN"
]

point_tags = ["start"] + [f"pt{i}" for i in range(1, 60)] + ["end"]

for var in target_vars:
    col_list = [f"{var}_{tag}" for tag in point_tags if f"{var}_{tag}" in df.columns]
    if var == "T2M":
        df["T2M_mean"] = df[col_list].astype(float).mean(axis=1)
        df["T2M_max"] = df[col_list].astype(float).max(axis=1)
        df["T2M_min"] = df[col_list].astype(float).min(axis=1)
        df["T2M_std"] = df[col_list].astype(float).std(axis=1)
    elif var == "RH2M":
        df["RH2M_mean"] = df[col_list].astype(float).mean(axis=1)
        df["RH2M_min"] = df[col_list].astype(float).min(axis=1)
        df["RH2M_std"] = df[col_list].astype(float).std(axis=1)
    elif var in ["WS2M", "WS10M"]:
        df[f"{var}_mean"] = df[col_list].astype(float).mean(axis=1)
        df[f"{var}_max"] = df[col_list].astype(float).max(axis=1)
        df[f"{var}_std"] = df[col_list].astype(float).std(axis=1)
    elif var in ["WD2M", "WD10M"]:
        df[f"{var}_mean"] = df[col_list].astype(float).mean(axis=1)
    elif var == "PRECTOTCORR":
        df["PRECTOTCORR_sum"] = df[col_list].astype(float).sum(axis=1)
        df["PRECTOTCORR_max"] = df[col_list].astype(float).max(axis=1)
    elif var == "PS":
        df["PS_mean"] = df[col_list].astype(float).mean(axis=1)
        df["PS_std"] = df[col_list].astype(float).std(axis=1)
    elif var == "ALLSKY_SFC_SW_DWN":
        df["ALLSKY_SFC_SW_DWN_mean"] = df[col_list].astype(float).mean(axis=1)
        df["ALLSKY_SFC_SW_DWN_max"] = df[col_list].astype(float).max(axis=1)

df.to_csv("final_data_features.csv", index=False, encoding='utf-8-sig')
print("구간 집계치 feature 저장 완료: final_data_features.csv")