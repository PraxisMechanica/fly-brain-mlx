def model_parameters() -> dict[str, float]:
    return {
        'tauSyn': 5.0,  # ms
        'tDelay': 1.8,  # ms
        'v0': -52.0,  # mV
        'vReset': -52.0,  # mV
        'vRest': -52.0,  # mV
        'vThreshold': -45.0,  # mV
        'tauMem': 20.0,  # ms
        'tRefrac': 2.2,  # ms
        'scalePoisson': 250,
        'wScale': 0.275,
    }
