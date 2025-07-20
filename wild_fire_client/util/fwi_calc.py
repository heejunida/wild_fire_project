import numpy as np

def fwi_calc(T, RH, W, P, month, FFMC0=85, DMC0=6, DC0=15):
    """
    캐나다 FWI 시스템 기반 산불 위험지수 계산 함수 (필수 입력: T, RH, W, P, month)
    - T: 기온(℃)
    - RH: 상대습도(%)
    - W: 풍속(m/s)
    - P: 강수량(mm)
    - month: 월(1~12)
    - FFMC0, DMC0, DC0: 초기값(보통 기본값 사용)
    """
    # FFMC (Fine Fuel Moisture Code)
    m = 147.2 * (101.0 - FFMC0) / (59.5 + FFMC0)
    if P > 0.5:
        rf = P - 0.5
        mo = m + 42.5 * rf * np.exp(-100.0 / (251.0 - m)) * (1 - np.exp(-6.93 / rf))
        if mo > 250:
            mo = 250
        m = mo
    ed = 0.942 * (RH ** 0.679) + (11.0 * np.exp((RH - 100.0) / 10.0)) + 0.18 * (21.1 - T) * (1 - 1 / np.exp(0.115 * RH))
    if m < ed:
        kl = 0.424 * (1.0 - (RH / 100.0) ** 1.7) + (0.0694 * np.sqrt(W)) * (1.0 - (RH / 100.0) ** 8)
        kw = kl * 0.581 * np.exp(0.0365 * T)
        m = ed - (ed - m) * np.exp(-kw)
    else:
        kl = 0.424 * (1.0 - ((100 - RH) / 100.0) ** 1.7) + (0.0694 * np.sqrt(W)) * (1.0 - ((100 - RH) / 100.0) ** 8)
        kw = kl * 0.581 * np.exp(0.0365 * T)
        m = ed + (m - ed) * np.exp(-kw)
    FFMC = (59.5 * (250.0 - m)) / (147.2 + m)
    if FFMC > 101:
        FFMC = 101
    if FFMC < 0:
        FFMC = 0

    # DMC (Duff Moisture Code)
    if month in [4, 5, 6, 7, 8, 9]:
        el = [6.5, 5.4, 5.4, 5.8, 6.4, 6.2]  # 4~9월
        daylength = el[month-4]
    else:
        daylength = 4.7  # 10~3월
    rk = 1.894 * (T + 1.1) * (100.0 - RH) * daylength * 0.0001
    DMC = DMC0 + rk
    if P > 1.5:
        ra = P
        rw = 0.92 * ra - 1.27
        wmi = 20.0 + np.exp(5.6348 - DMC0 / 43.43)
        b = DMC0 / 43.43
        wmr = wmi + 1000 * rw / (48.77 + rk * rw)
        DMC = 43.43 * (5.6348 - np.log(wmr - 20.0))

    # DC (Drought Code)
    fl = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    if month in [4, 5, 6, 7, 8, 9]:
        fl = [9.0, 8.0, 7.0, 7.0, 7.0, 8.0]
        Lf = fl[month-4]
    else:
        Lf = 6.0
    V = 0.36 * (T + 2.8) + Lf
    DC = DC0 + 0.5 * V
    if P > 2.8:
        ra = P
        rw = 0.83 * ra - 1.27
        smi = 800.0 * np.exp(-DC0 / 400.0)
        smr = smi + 3.937 * rw
        DC = 400.0 * np.log(800.0 / smr)

    # ISI (Initial Spread Index)
    mo = 147.2 * (101.0 - FFMC) / (59.5 + FFMC)
    ff = 91.9 * np.exp(-0.1386 * mo) * (1.0 + mo ** 5.31 / (4.93e7))
    ISI = ff * np.exp(0.05039 * W)
    
    # BUI (Build Up Index)
    if DMC <= 0.4 * DC:
        BUI = (0.8 * DMC * DC) / (DMC + 0.4 * DC)
    else:
        BUI = DMC - (1.0 - (0.8 * DC) / (DMC + 0.4 * DC)) * (0.92 + (0.0114 * DMC))
    if BUI < 0:
        BUI = 0

    # FWI (Fire Weather Index)
    bb = 0.1 * ISI * BUI
    if bb <= 1:
        FWI = bb
    else:
        FWI = np.exp(2.72 * (bb ** 0.647))
    
    return {
        "FFMC": FFMC,
        "DMC": DMC,
        "DC": DC,
        "ISI": ISI,
        "BUI": BUI,
        "FWI": FWI
    }