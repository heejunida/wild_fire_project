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
    # 풍속 단위 변환 m/s → km/h
    W_kmh = max(W * 3.6, 0)  # 음수 방지

    # FFMC (Fine Fuel Moisture Code)
    m = 147.2 * (101.0 - FFMC0) / (59.5 + FFMC0)
    if P > 0.5:
        rf = P - 0.5
        if m > 250:
            m = 250
        mo = m + 42.5 * rf * np.exp(-100.0 / (251.0 - m)) * (1.0 - np.exp(-6.93 / rf))
        if mo > 250:
            mo = 250
        m = mo
    
    ed = (0.942 * (RH ** 0.679) +
          11.0 * np.exp((RH - 100.0) / 10.0) +
          0.18 * (21.1 - T) * (1.0 - 1.0 / np.exp(0.115 * RH)))
    
    if m < ed:
        kl = 0.424 * (1.0 - (RH / 100.0) ** 1.7) + (0.0694 * np.sqrt(W_kmh)) * (1.0 - (RH / 100.0) ** 8)
        kw = kl * 0.581 * np.exp(0.0365 * T)
        m = ed - (ed - m) * np.exp(-kw)
    else:
        kl = 0.424 * (1.0 - ((100.0 - RH) / 100.0) ** 1.7) + (0.0694 * np.sqrt(W_kmh)) * (1.0 - ((100.0 - RH) / 100.0) ** 8)
        kw = kl * 0.581 * np.exp(0.0365 * T)
        m = ed + (m - ed) * np.exp(-kw)

    FFMC = (59.5 * (250.0 - m)) / (147.2 + m)
    FFMC = min(max(FFMC, 0), 101)

    # DMC (Duff Moisture Code)
    Le = [6.5, 7.5, 9.0, 12.8, 13.9, 13.9, 12.4, 10.9, 9.4, 8.0, 7.0, 6.0]
    daylength = Le[month-1]
    
    T_eff = max(T, -1.1)

    rk = 1.894 * (T_eff + 1.1) * (100.0 - RH) * daylength * 0.0001
    
    if P > 1.5:
        ra = P
        rw = 0.92 * ra - 1.27
        wmi = 20.0 + 280.0 / np.exp(0.023 * DMC0)

        if DMC0 <= 33:
            b = 100.0 / (0.5 + 0.3 * DMC0)
        elif DMC0 > 65:
            b = 6.2 * np.log(DMC0)
            b = b - 17.2
        else:
            b = 14.0 - 1.3 * np.log(DMC0)

        denom = 48.77 + b * rw
        denom = max(denom, 1e-6)  # 분모 0 방지

        wmr = wmi + (1000 * rw) / denom

        arg_log = wmr - 20.0
        arg_log = max(arg_log, 1e-6)  # 로그 음수/0 방지

        pr = 43.43 * (5.6348 - np.log(arg_log))
        pr = max(pr, 0.0)

        DMC = pr + rk
    else:
        DMC = DMC0 + rk

    DMC = max(DMC, 0)

    # DC (Drought Code)
    Lf = [-1.6, -1.6, -1.6, 0.9, 3.8, 5.8, 6.4, 5.0, 2.4, 0.4, -1.6, -1.6]
    daylength_dc = Lf[month-1]

    T_eff_dc = max(T, -2.8)
        
    V = 0.36 * (T_eff_dc + 2.8) + daylength_dc
    V = max(V, 0)

    if P > 2.8:
        ra = P
        rw = 0.83 * ra - 1.27

        smi = 800.0 * np.exp(-DC0 / 400.0)

        denom = 1.0 + 3.937 * rw / smi
        denom = max(denom, 1e-6)  # 로그 인자 방지

        pr = DC0 - 400.0 * np.log(denom)
        pr = max(pr, 0)

        DC = pr + V
    else:
        DC = DC0 + V

    DC = max(DC, 0)

    # ISI (Initial Spread Index)
    mo = 147.2 * (101.0 - FFMC) / (59.5 + FFMC)

    ff = 19.115 * np.exp(-0.1386 * mo) * (1.0 + (mo**5.31) / 4.93e7)

    ISI = ff * np.exp(0.05039 * W_kmh)

    # BUI (Build Up Index)
    if DMC <= 0.4 * DC:
        BUI = (0.8 * DC * DMC) / (DMC + 0.4 * DC)
    else:
        BUI = DMC - (1.0 - 0.8 * DC / (DMC + 0.4 * DC)) * (0.92 + (0.0114 * DMC)**1.7)
    BUI = max(BUI, 0)

    # FWI (Fire Weather Index)
    if BUI <= 80.0:
        fD = 0.6 * BUI
    else:
        exp_val = np.exp(0.023 * BUI)
        fD = 1000.0 / (25.0 + 108.64 / exp_val)
        
    B = 0.1 * ISI * fD

    if B > 1:
        FWI = np.exp(2.72 * (0.434 * np.log(B))**0.647)
    else:
        FWI = B
        
    return {
        "FFMC": FFMC,
        "DMC": DMC,
        "DC": DC,
        "ISI": ISI,
        "BUI": BUI,
        "FWI": FWI
    }