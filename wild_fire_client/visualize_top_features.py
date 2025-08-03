
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Constants ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "final_cleaned_for_modeling.csv")
DISTRIBUTION_PLOT_FILE = os.path.join(BASE_DIR, "eda_analysis_plots/top20_feature_distributions.png")
CORRELATION_PLOT_FILE = os.path.join(BASE_DIR, "eda_analysis_plots/top20_feature_correlation_heatmap.png")

# 최종 20개 피처 목록
TOP_20_FEATURES = [
    'potential_spread_index', 'fuel_combo', 'dry_windy_combo', 'FWI_0h', 'DC_0h',
    'BUI_0h', 'ws10m_max_past_24h', 'consecutive_dry_days_start', 'ISI_0h', 'DMC_0h',
    'slope_max', 't2m_max_past_24h', 'rh2m_min_past_24h', 'elevation_std',
    'dry_days_90d_start', 'FFMC_0h', 'WS10M_0h', 'slope_mean', 'ndvi_before',
    'treecover_pre_fire_5x5'
]

def main():
    # --- 데이터 로드 ---
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: 데이터 파일을 찾을 수 없습니다. -> '{DATA_FILE}'")
        return

    # 최종 20개 피처만 선택
    df_top20 = df[TOP_20_FEATURES].copy()
    print("데이터 로드 및 최종 20개 피처 선택 완료.")

    # --- 1. 피처 분포 시각화 (Histograms) ---
    print("피처 분포 히스토그램 생성 중...")
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(5, 4, figsize=(20, 22))
    fig.suptitle('Distribution of Top 20 Features', fontsize=24, y=1.02)
    axes = axes.flatten()

    for i, col in enumerate(df_top20.columns):
        sns.histplot(df_top20[col], kde=True, ax=axes[i], bins=30)
        axes[i].set_title(col, fontsize=14)
        axes[i].set_xlabel('')
        axes[i].set_ylabel('')

    plt.tight_layout()
    plt.savefig(DISTRIBUTION_PLOT_FILE)
    plt.close()
    print(f"피처 분포 그래프 저장 완료: {DISTRIBUTION_PLOT_FILE}")

    # --- 2. 상관관계 분석 (Correlation Heatmap) ---
    print("상관관계 히트맵 생성 중...")
    correlation_matrix = df_top20.corr()

    plt.figure(figsize=(18, 15))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=.5)
    plt.title('Correlation Matrix of Top 20 Features', fontsize=20)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(CORRELATION_PLOT_FILE)
    plt.close()
    print(f"상관관계 히트맵 저장 완료: {CORRELATION_PLOT_FILE}")

if __name__ == '__main__':
    # 시각화 결과 저장 디렉토리 생성
    os.makedirs(os.path.join(BASE_DIR, "eda_analysis_plots"), exist_ok=True)
    main()
