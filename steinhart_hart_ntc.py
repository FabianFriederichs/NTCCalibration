import numpy as np
import math

# steinhart-hart polynomial terms
def sh_p(resistance, coefficients, terms):
    inv_temp = 0.0
    for (c, p) in zip(coefficients, terms):
        inv_temp += c * np.log(resistance) ** p
    return inv_temp

# derivative of steinhart-hart polynomial terms
def sh_dp_dr(resistance, coefficients, terms):
    df_dr = 0.0
    for (c, p) in zip(coefficients, terms):
        if p > 0:
            df_dr += c * p * (np.log(resistance) ** (p - 1)) * (1.0 / resistance)
    return df_dr

# general steinhart-hart equation
def steinhart_hart(resistance, coefficients, terms = [0, 1, 3], temp_in_celsius=True):
    # assert that number of coefficients and terms have the same length
    assert len(coefficients) == len(terms), "Number of coefficients and terms must have the same length"
    # calculate the temperature
    temp = 1.0 / sh_p(resistance, coefficients, terms)
    # return the temperature in celsius if requested
    return temp - 273.15 if temp_in_celsius else temp

# first derivative of steinhart-hart equation
def steinhart_hart_derivative(resistance, coefficients, terms = [0, 1, 3], temp_in_celsius=True):
    # assert that number of coefficients and terms have the same length
    assert len(coefficients) == len(terms), "Number of coefficients and terms must have the same length"
    # calculate inner derivative
    dp_dr = sh_dp_dr(resistance, coefficients, terms)
    # polynomial terms
    p = sh_p(resistance, coefficients, terms)
    # return derivative
    return -dp_dr / (p ** 2)

# inverse steinhart-hart equation
def inverse_steinhart_hart(
    temperature,
    coefficients,
    terms = [0, 1, 3],
    initial_guess = 1.0,
    temp_in_celsius=True,
    min_resistance = 1e-6,
    max_iterations = 500,
    tolerance = 1e-6
):
    # assert that number of coefficients and terms have the same length
    assert len(coefficients) == len(terms), "Number of coefficients and terms must have the same length"
    # find numerical inverse of steinhart-hart equation using newton's method (f(r) = sh(r) - temperature)
    r = initial_guess
    for i in range(max_iterations):
        # calculate f(r) and f'(r)
        f = steinhart_hart(r, coefficients, terms, temp_in_celsius) - temperature
        df_dr = steinhart_hart_derivative(r, coefficients, terms, temp_in_celsius)
        # update r
        r = max(r - f / df_dr, min_resistance)
        # check for convergence
        if np.abs(f) < tolerance:
            break
    # return the resistance
    return r

# solve for N steinhart-hart coefficients given a set of temperature and resistance pairs
def fit_steinhart_hart(temperature, resistance, powers, temp_in_celsius=True):
    # assert that the number of temperature and resistance pairs is the same
    assert len(temperature) == len(resistance), "Number of temperature and resistance pairs must be the same"
    # assert that the number of pairs is at least N
    assert len(temperature) >= len(powers), "Number of temperature and resistance pairs must be at least the number of coefficients + 1 (constant + number of polynomial terms)"
    # assert that the number of coefficients is at least 1
    assert len(powers) >= 1, "Number of coefficients must be at least 1"

    # convert to numpy arrays
    if type(temperature) is not np.ndarray:
        temperature = np.array(temperature)
    if type(resistance) is not np.ndarray:
        resistance = np.array(resistance)

    # build the system of equations
    # log resistances
    log_res = np.log(resistance)
    # inverse temperatures (convert to kelvin)
    inv_temp = 1.0 / (temperature + 273.15 if temp_in_celsius else temperature)

    # build the matrix
    A = np.zeros((temperature.shape[0], len(powers)))
    # polynomial terms
    for i in range(len(powers)):
        A[:, i] = log_res ** powers[i]
    
    # solve the system of equations in the least squares sense
    x, _, _, _ = np.linalg.lstsq(A, inv_temp, rcond=None)

    # return the coefficients
    return x