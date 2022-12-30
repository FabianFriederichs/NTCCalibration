import matplotlib.pyplot as plt
import numpy as np

import steinhart_hart_ntc as sh

# config
a0 = 0.000859559
a1 = 0.000225764
a2 = -5.679844e-8

# measured temperature and resistance pairs
measured_temps = [
    20, 
    30, 
    40, 
    50, 
    60, 
    70, 
    80, 
    90, 
    100,
    110,
    120,
    130,
    140,
    150,
    160,
    170,
    180,
    190,
    200,
    210,
    220,
    230,
    240,
    250
]

measured_resistances = [
    121921.7105,
    70189.10506,
    42472.79412,
    26903.44828,
    15495.6978,
    11232.53311,
    6824.850299,
    5074.758761,
    3671.683341,
    2716.763006,
    1945.890884,
    1435.32037,
    1121.68784,
    840.1554404,
    661.1420613,
    522.9308005,
    421.4741884,
    344.9541284,
    279.6895213,
    219.8619632,
    179.9442191,
    152.8744327,
    122.47557,
    106.8181818
]

# main function
def main():
    # fit steinhart-hart coefficients
    powers = [0, 1, 3]
    coeffs = sh.fit_steinhart_hart(measured_temps, measured_resistances, powers)

    # plot steinhart-hart equation and derivative
    r = np.linspace(1, 100000, 1000)
    t = np.zeros_like(r)
    dt_dr = np.zeros_like(r)

    # test implementation of steinhart-hart equation
    for i in range(r.shape[0]):
        t[i] = sh.steinhart_hart(r[i], coeffs, powers)

    for i in range(r.shape[0]):
        dt_dr[i] = sh.steinhart_hart_derivative(r[i], coeffs, powers)

    plt.plot(r, t, label= "Model Fit")
    plt.plot(r, dt_dr, label = "Model Fit Derivative")
    plt.scatter(measured_resistances, measured_temps, label = "Measured Data")
    plt.xlabel("Resistance (Ohm)")
    plt.ylabel("Temperature (°C)")
    

    # plot inverse steinhart-hart equation
    r_inv = np.zeros_like(r)
    for i in range(r.shape[0]):
        r_inv[i] = sh.inverse_steinhart_hart(t[i], coeffs, powers)

    plt.plot(r_inv, t, label = "Inverse Model Fit")
    plt.legend()

    plt.show(block = True)

# run main function
if __name__ == "__main__":
    main()