#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   fwi.py
#
#   Python implementation of the Canadian Forest Fire Weather Index System
#
#   This program is a re-implementation of the CFFDRS FWI System, as described
#   in the following publications:
#
#   Development and Structure of the Canadian Forest Fire Weather Index System
#   (Forestry Canada Fire Danger Group, 1992)
#
#   and
#
#   A guide to operational use of the Canadian Forest Fire Weather Index System
#   (Lawson and Armitage, 1997)
#
#   This program was written by and is maintained by the University of Utah
#   Mesowest program.
#
#   Author:            Brian J. Wight
#   Contact:           brian.wight@utah.edu
#   Copyright:         2020, University of Utah
#
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Version: 1.0.1
#
#   Last Updated: 20 April 2021
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Change Log
#
#   1.0.1
#   - Corrected an issue with the numpy implementation of the ISI calculation
#     where the fine fuel moisture code was not being properly masked for the
#     ISI calculation. This was causing ISI to be computed with the FFMC value
#     instead of the fine fuel moisture content.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import math
import numpy as np

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Main FWI System Calculation Function
#
# # # # # # # # # a# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def fwi(ffmc_y, dmc_y, dc_y, temp, rh, ws, pr, mon, lat, use_numpy=False):
    """
    Function to compute the Canadian Forest Fire Weather Index System
    This function will compute the 6 standard components of the CFFDRS FWI
    system, as well as the daily severity rating. This function can compute
    the FWI system components for a single observation, or for a series of
    observations. The use_numpy argument controls which implementation is
    used. The numpy implementation is faster for large datasets.

    Parameters
    ----------
    ffmc_y : float or numpy array
        The fine fuel moisture code from the previous day
    dmc_y : float or numpy array
        The duff moisture code from the previous day
    dc_y : float or numpy array
        The drought code from the previous day
    temp : float or numpy array
        The temperature at noon local standard time (LST) in Celsius
    rh : float or numpy array
        The relative humidity at noon LST in percent
    ws : float or numpy array
        The wind speed at noon LST in km/h
    pr : float or numpy array
        The 24-hour rainfall total, ending at noon LST, in mm
    mon : int or numpy array
        The month of the observation (1-12)
    lat : float or numpy array
        The latitude of the observation in decimal degrees
    use_numpy : bool
        A boolean to control which implementation is used. If True, the
        numpy implementation is used. If False, the standard python
        implementation is used.

    Returns
    -------
    dict or pandas DataFrame
        A dictionary or pandas DataFrame containing the 6 standard FWI
        system components, as well as the daily severity rating.
    """
    if use_numpy:
        return _fwi_numpy(ffmc_y, dmc_y, dc_y, temp, rh, ws, pr, mon, lat)
    else:
        return _fwi_standard(ffmc_y, dmc_y, dc_y, temp, rh, ws, pr, mon, lat)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Standard Python Implementation
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def _fwi_standard(ffmc_y, dmc_y, dc_y, temp, rh, ws, pr, mon, lat):
    """
    Standard Python implementation of the FWI system. This function is
    intended to be used for a single observation.
    """
    # Fine Fuel Moisture Code
    ffmc = _ffmc(ffmc_y, temp, rh, ws, pr)
    # Duff Moisture Code
    dmc = _dmc(dmc_y, temp, rh, pr, mon, lat)
    # Drought Code
    dc = _dc(dc_y, temp, pr, mon, lat)
    # Initial Spread Index
    isi = _isi(ffmc, ws)
    # Buildup Index
    bui = _bui(dmc, dc)
    # Fire Weather Index
    fwi = _fwi_calc(isi, bui)
    # Daily Severity Rating
    dsr = _dsr(fwi)
    return {'ffmc': ffmc, 'dmc': dmc, 'dc': dc, 'isi': isi, 'bui': bui,
            'fwi': fwi, 'dsr': dsr}

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Numpy Implementation
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def _fwi_numpy(ffmc_y, dmc_y, dc_y, temp, rh, ws, pr, mon, lat):
    """
    Numpy implementation of the FWI system. This function is intended to
    be used for a series of observations.
    """
    # Fine Fuel Moisture Code
    ffmc = _ffmc_numpy(ffmc_y, temp, rh, ws, pr)
    # Duff Moisture Code
    dmc = _dmc_numpy(dmc_y, temp, rh, pr, mon, lat)
    # Drought Code
    dc = _dc_numpy(dc_y, temp, pr, mon, lat)
    # Initial Spread Index
    isi = _isi_numpy(ffmc, ws)
    # Buildup Index
    bui = _bui_numpy(dmc, dc)
    # Fire Weather Index
    fwi = _fwi_calc_numpy(isi, bui)
    # Daily Severity Rating
    dsr = _dsr_numpy(fwi)
    return {'ffmc': ffmc, 'dmc': dmc, 'dc': dc, 'isi': isi, 'bui': bui,
            'fwi': fwi, 'dsr': dsr}

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Fine Fuel Moisture Code (FFMC)
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def _ffmc(ffmc_y, temp, rh, ws, pr):
    """
    Function to compute the Fine Fuel Moisture Code (FFMC)
    """
    # Eq. 1
    mo = (147.2 * (101 - ffmc_y)) / (59.5 + ffmc_y)
    # Eq. 2
    if pr > 0.5:
        rf = pr - 0.5
        # Eq. 3a
        if mo > 150:
            mo = (mo + 42.5 * rf * math.exp(-100 / (251 - mo)) *
                  (1 - math.exp(-6.93 / rf))) + 0.0015 * (mo - 150)**2 * math.sqrt(rf)
        # Eq. 3b
        elif mo <= 150:
            mo = mo + 42.5 * rf * math.exp(-100 / (251 - mo)) * (1 - math.exp(-6.93 / rf))
        if mo > 250:
            mo = 250
    # Eq. 4
    ed = 0.942 * rh**0.679 + 11 * math.exp((rh - 100) / 10) + 0.18 * (21.1 - temp) * (1 - math.exp(-0.115 * rh))
    # Eq. 5
    ew = 0.618 * rh**0.753 + 10 * math.exp((rh - 100) / 10) + 0.18 * (21.1 - temp) * (1 - math.exp(-0.115 * rh))
    # Eq. 6a
    if mo > ed:
        # Eq. 7a
        m = ed + (mo - ed) * 10**-0.434
    # Eq. 6b
    elif mo < ew:
        # Eq. 7b
        m = ew - (ew - mo) * 10**-0.434
    # Eq. 6c
    else:
        m = mo
    # Eq. 8
    ffmc = (59.5 * (250 - m)) / (147.2 + m)
    if ffmc > 101:
        ffmc = 101
    if ffmc < 0:
        ffmc = 0
    return ffmc

def _ffmc_numpy(ffmc_y, temp, rh, ws, pr):
    """
    Numpy implementation of the FFMC calculation
    """
    # Eq. 1
    mo = (147.2 * (101 - ffmc_y)) / (59.5 + ffmc_y)
    # Eq. 2
    rf = np.where(pr > 0.5, pr - 0.5, 0)
    # Eq. 3a
    mo = np.where((pr > 0.5) & (mo > 150),
                  (mo + 42.5 * rf * np.exp(-100 / (251 - mo)) *
                   (1 - np.exp(-6.93 / rf))) + 0.0015 * (mo - 150)**2 * np.sqrt(rf), mo)
    # Eq. 3b
    mo = np.where((pr > 0.5) & (mo <= 150),
                  mo + 42.5 * rf * np.exp(-100 / (251 - mo)) * (1 - np.exp(-6.93 / rf)), mo)
    mo = np.where(mo > 250, 250, mo)
    # Eq. 4
    ed = 0.942 * rh**0.679 + 11 * np.exp((rh - 100) / 10) + 0.18 * (21.1 - temp) * (1 - np.exp(-0.115 * rh))
    # Eq. 5
    ew = 0.618 * rh**0.753 + 10 * np.exp((rh - 100) / 10) + 0.18 * (21.1 - temp) * (1 - np.exp(-0.115 * rh))
    # Eq. 6a & 7a
    m = np.where(mo > ed, ed + (mo - ed) * 10**-0.434, mo)
    # Eq. 6b & 7b
    m = np.where(mo < ew, ew - (ew - mo) * 10**-0.434, m)
    # Eq. 8
    ffmc = (59.5 * (250 - m)) / (147.2 + m)
    ffmc = np.where(ffmc > 101, 101, ffmc)
    ffmc = np.where(ffmc < 0, 0, ffmc)
    return ffmc

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Duff Moisture Code (DMC)
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def _dmc(dmc_y, temp, rh, pr, mon, lat):
    """
    Function to compute the Duff Moisture Code (DMC)
    """
    # Day length adjustment
    dl = _day_length(mon, lat)
    # Eq. 16
    k = 1.894 * (temp + 1.1) * (100 - rh) * dl * 10**-6
    # Eq. 11
    if pr > 1.5:
        ra = pr
        rw = 0.92 * ra - 1.27
        # Eq. 12
        wmi = 20 + 280 / math.exp(0.023 * dmc_y)
        # Eq. 13a
        if dmc_y <= 33:
            b = 100 / (0.5 + 0.3 * dmc_y)
        # Eq. 13b
        elif dmc_y > 33 and dmc_y <= 65:
            b = 14 - 1.3 * math.log(dmc_y)
        # Eq. 13c
        else:
            b = 6.2 * math.log(dmc_y) - 17.2
        # Eq. 14
        wmr = wmi + (1000 * rw) / (48.77 + b * rw)
        # Eq. 15
        pr = 43.43 * (5.6348 - math.log(wmr - 20))
    else:
        pr = dmc_y
    # Eq. 17
    dmc = pr + k
    if dmc < 0:
        dmc = 0
    return dmc

def _dmc_numpy(dmc_y, temp, rh, pr, mon, lat):
    """
    Numpy implementation of the DMC calculation
    """
    # Day length adjustment
    dl = _day_length_numpy(mon, lat)
    # Eq. 16
    k = 1.894 * (temp + 1.1) * (100 - rh) * dl * 10**-6
    # Eq. 11
    ra = np.where(pr > 1.5, pr, 0)
    rw = np.where(pr > 1.5, 0.92 * ra - 1.27, 0)
    # Eq. 12
    wmi = np.where(pr > 1.5, 20 + 280 / np.exp(0.023 * dmc_y), 0)
    # Eq. 13a
    b = np.where((pr > 1.5) & (dmc_y <= 33), 100 / (0.5 + 0.3 * dmc_y), 0)
    # Eq. 13b
    b = np.where((pr > 1.5) & (dmc_y > 33) & (dmc_y <= 65), 14 - 1.3 * np.log(dmc_y), b)
    # Eq. 13c
    b = np.where((pr > 1.5) & (dmc_y > 65), 6.2 * np.log(dmc_y) - 17.2, b)
    # Eq. 14
    wmr = np.where(pr > 1.5, wmi + (1000 * rw) / (48.77 + b * rw), 0)
    # Eq. 15
    pr = np.where(pr > 1.5, 43.43 * (5.6348 - np.log(wmr - 20)), dmc_y)
    # Eq. 17
    dmc = pr + k
    dmc = np.where(dmc < 0, 0, dmc)
    return dmc

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Drought Code (DC)
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def _dc(dc_y, temp, pr, mon, lat):
    """
    Function to compute the Drought Code (DC)
    """
    # Day length adjustment
    dl = _day_length(mon, lat)
    # Eq. 22
    v = 0.36 * (temp + 2.8) + dl
    # Eq. 18
    if pr > 2.8:
        ra = pr
        rw = 0.83 * ra - 1.27
        # Eq. 19
        smi = 800 * math.exp(-dc_y / 400)
        # Eq. 20
        pr = 400 * math.log(1 + (3.937 * rw) / smi)
        # Eq. 21
        dc = dc_y - pr
    else:
        dc = dc_y
    # Eq. 23
    dc = dc + v
    if dc < 0:
        dc = 0
    return dc

def _dc_numpy(dc_y, temp, pr, mon, lat):
    """
    Numpy implementation of the DC calculation
    """
    # Day length adjustment
    dl = _day_length_numpy(mon, lat)
    # Eq. 22
    v = 0.36 * (temp + 2.8) + dl
    # Eq. 18
    ra = np.where(pr > 2.8, pr, 0)
    rw = np.where(pr > 2.8, 0.83 * ra - 1.27, 0)
    # Eq. 19
    smi = np.where(pr > 2.8, 800 * np.exp(-dc_y / 400), 0)
    # Eq. 20
    pr = np.where(pr > 2.8, 400 * np.log(1 + (3.937 * rw) / smi), 0)
    # Eq. 21
    dc = np.where(pr > 2.8, dc_y - pr, dc_y)
    # Eq. 23
    dc = dc + v
    dc = np.where(dc < 0, 0, dc)
    return dc

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Initial Spread Index (ISI)
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def _isi(ffmc, ws):
    """
    Function to compute the Initial Spread Index (ISI)
    """
    # Eq. 24
    mo = 147.2 * (101 - ffmc) / (59.5 + ffmc)
    # Eq. 25
    fw = math.exp(0.05039 * ws)
    # Eq. 26
    sf = 19.115 * math.exp(-0.1386 * mo) * (1 + (mo**5.31) / 4.93e7)
    # Eq. 27
    isi = sf * fw
    return isi

def _isi_numpy(ffmc, ws):
    """
    Numpy implementation of the ISI calculation
    """
    # Eq. 24
    mo = 147.2 * (101 - ffmc) / (59.5 + ffmc)
    # Eq. 25
    fw = np.exp(0.05039 * ws)
    # Eq. 26
    sf = 19.115 * np.exp(-0.1386 * mo) * (1 + (mo**5.31) / 4.93e7)
    # Eq. 27
    isi = sf * fw
    return isi

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Buildup Index (BUI)
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def _bui(dmc, dc):
    """
    Function to compute the Buildup Index (BUI)
    """
    # Eq. 28
    if dmc <= 0.4 * dc:
        bui = (0.8 * dc * dmc) / (dmc + 0.4 * dc)
    else:
        bui = dmc - (1 - 0.8 * dc / (dmc + 0.4 * dc)) * (0.92 + (0.0114 * dmc)**1.7)
    if bui < 0:
        bui = 0
    return bui

def _bui_numpy(dmc, dc):
    """
    Numpy implementation of the BUI calculation
    """
    # Eq. 28
    bui = np.where(dmc <= 0.4 * dc,
                   (0.8 * dc * dmc) / (dmc + 0.4 * dc),
                   dmc - (1 - 0.8 * dc / (dmc + 0.4 * dc)) * (0.92 + (0.0114 * dmc)**1.7))
    bui = np.where(bui < 0, 0, bui)
    return bui

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Fire Weather Index (FWI)
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def _fwi_calc(isi, bui):
    """
    Function to compute the Fire Weather Index (FWI)
    """
    # Eq. 29
    if bui > 80:
        f = 0.6 + 0.02 * (bui - 80)
    else:
        f = 0.6
    # Eq. 30
    bb = 0.1 * isi * (f * bui)**0.5
    # Eq. 31
    if bb <= 1:
        fwi = bb
    else:
        fwi = math.exp(2.72 * (0.434 * math.log(bb))**0.647)
    return fwi

def _fwi_calc_numpy(isi, bui):
    """
    Numpy implementation of the FWI calculation
    """
    # Eq. 29
    f = np.where(bui > 80, 0.6 + 0.02 * (bui - 80), 0.6)
    # Eq. 30
    bb = 0.1 * isi * (f * bui)**0.5
    # Eq. 31
    fwi = np.where(bb <= 1, bb, np.exp(2.72 * (0.434 * np.log(bb))**0.647))
    return fwi

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Daily Severity Rating (DSR)
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def _dsr(fwi):
    """
    Function to compute the Daily Severity Rating (DSR)
    """
    # Eq. 32
    dsr = 0.0272 * fwi**1.77
    return dsr

def _dsr_numpy(fwi):
    """
    Numpy implementation of the DSR calculation
    """
    # Eq. 32
    dsr = 0.0272 * fwi**1.77
    return dsr

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Day Length Factor
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def _day_length(mon, lat):
    """
    Function to compute the day length factor
    """
    day_length_options = {
        1: [6.5, 7.5, 9.0, 12.8, 13.9, 15.0, 16.1, 17.2, 18.7, 20.0],
        2: [7.5, 8.5, 9.2, 11.5, 12.4, 13.3, 14.3, 15.3, 16.4, 17.5],
        3: [9.0, 9.2, 9.5, 10.5, 11.2, 11.8, 12.5, 13.2, 13.8, 14.5],
        4: [11.8, 11.5, 10.5, 9.2, 8.5, 7.5, 6.5, 5.5, 4.5, 3.5],
        5: [13.9, 12.4, 11.2, 9.5, 8.5, 7.5, 6.5, 5.5, 4.5, 3.5],
        6: [15.0, 13.3, 11.8, 10.5, 9.2, 8.5, 7.5, 6.5, 5.5, 4.5],
        7: [16.1, 14.3, 12.5, 11.2, 9.5, 8.5, 7.5, 6.5, 5.5, 4.5],
        8: [17.2, 15.3, 13.2, 11.8, 10.5, 9.2, 8.5, 7.5, 6.5, 5.5],
        9: [18.7, 16.4, 13.8, 12.5, 11.2, 9.5, 8.5, 7.5, 6.5, 5.5],
        10: [20.0, 17.5, 14.5, 13.2, 11.8, 10.5, 9.2, 8.5, 7.5, 6.5],
        11: [18.7, 16.4, 13.8, 12.5, 11.2, 9.5, 8.5, 7.5, 6.5, 5.5],
        12: [17.2, 15.3, 13.2, 11.8, 10.5, 9.2, 8.5, 7.5, 6.5, 5.5]
    }
    lat_indices = {
        20: 0, 30: 1, 40: 2, 50: 3, 60: 4, 70: 5, 80: 6, 90: 7,
        -20: 8, -30: 9, -40: 10, -50: 11
    }
    lat_index = lat_indices[round(lat / 10) * 10]
    return day_length_options[mon][lat_index]

def _day_length_numpy(mon, lat):
    """
    Numpy implementation of the day length factor
    """
    day_length_options = {
        1: [6.5, 7.5, 9.0, 12.8, 13.9, 15.0, 16.1, 17.2, 18.7, 20.0],
        2: [7.5, 8.5, 9.2, 11.5, 12.4, 13.3, 14.3, 15.3, 16.4, 17.5],
        3: [9.0, 9.2, 9.5, 10.5, 11.2, 11.8, 12.5, 13.2, 13.8, 14.5],
        4: [11.8, 11.5, 10.5, 9.2, 8.5, 7.5, 6.5, 5.5, 4.5, 3.5],
        5: [13.9, 12.4, 11.2, 9.5, 8.5, 7.5, 6.5, 5.5, 4.5, 3.5],
        6: [15.0, 13.3, 11.8, 10.5, 9.2, 8.5, 7.5, 6.5, 5.5, 4.5],
        7: [16.1, 14.3, 12.5, 11.2, 9.5, 8.5, 7.5, 6.5, 5.5, 4.5],
        8: [17.2, 15.3, 13.2, 11.8, 10.5, 9.2, 8.5, 7.5, 6.5, 5.5],
        9: [18.7, 16.4, 13.8, 12.5, 11.2, 9.5, 8.5, 7.5, 6.5, 5.5],
        10: [20.0, 17.5, 14.5, 13.2, 11.8, 10.5, 9.2, 8.5, 7.5, 6.5],
        11: [18.7, 16.4, 13.8, 12.5, 11.2, 9.5, 8.5, 7.5, 6.5, 5.5],
        12: [17.2, 15.3, 13.2, 11.8, 10.5, 9.2, 8.5, 7.5, 6.5, 5.5]
    }
    lat_indices = {
        20: 0, 30: 1, 40: 2, 50: 3, 60: 4, 70: 5, 80: 6, 90: 7,
        -20: 8, -30: 9, -40: 10, -50: 11
    }
    lat_index = np.vectorize(lat_indices.get)(np.round(lat / 10) * 10)
    dl = np.vectorize(lambda m, i: day_length_options[m][i])(mon, lat_index)
    return dl
