import numpy as np
import steinhart_hart_ntc as sh

# convert adc values to resistance values
def adc_to_resistance(
    adc_values,
    adc_resolution,
    reference_voltage,
    pull_up_resistance
):
    # convert to numpy array if not already
    if type(adc_values) is not np.ndarray:
        adc_values = np.array(adc_values)
    # convert adc values to voltages
    voltages = adc_values * reference_voltage / (2 ** adc_resolution - 1)
    # convert voltages to resistances
    resistances = voltages * pull_up_resistance / (reference_voltage - voltages)
    # return the resistances
    return resistances

# convert resistance values to adc values
def resistance_to_adc(
    resistances,
    adc_resolution,
    reference_voltage,
    pull_up_resistance
):
    # convert to numpy array if not already
    if type(resistances) is not np.ndarray:
        resistances = np.array(resistances)
    # convert resistances to voltages
    voltages = resistances * reference_voltage / (pull_up_resistance + resistances)
    # convert voltages to adc values
    adc_values = (voltages / reference_voltage) * (2 ** adc_resolution - 1)
    # round to nearest integer
    adc_values = np.round(adc_values)
    # return the adc values
    return adc_values

# given a set of steinhart-hart coeffients, return a LUT of ADC value to temperature pairs
def steinhart_hart_to_adc_lut(
    sample_temps,
    adc_resolution,
    reference_voltage,
    pull_up_resistance,
    coefficients,
    terms = [0, 1, 3],
    temp_in_celsius = True,
    max_iterations = 1000,
    tolerance = 1e-6
):
    # assert that the number of coefficients is at least 1
    assert len(coefficients) >= 1, "Number of coefficients must be at least 1"
    # assert that the ADC resolution is at least 1
    assert adc_resolution >= 1, "ADC resolution must be at least 1"
    # assert that the reference voltage is at least 0
    assert reference_voltage > 0, "Reference voltage must be positive"
    # assert that the pull-up resistance is at least 0
    assert pull_up_resistance > 0, "Pull-up resistance must be positive"
    # assert that the number of sample temperatures is at least 1
    assert len(sample_temps) > 0, "Number of sample temperatures must be at least 1"
    # get resistance values for each sample temperature
    sample_resistances = np.array([sh.inverse_steinhart_hart(sample_temps[i], coefficients, terms, 1.0, True, 1e-6, max_iterations, tolerance) for i in range(len(sample_temps))])    
    # convert sample resistances to ADC values
    sample_adc_values = resistance_to_adc(sample_resistances, adc_resolution, reference_voltage, pull_up_resistance)
    # return the LUT
    return np.array([sample_temps, sample_adc_values]).T

# given a set of steinhart-hart coeffients, return a LUT of resistance to temperature pairs
def steinhart_hart_to_resistance_lut(
    sample_temps,
    coefficients,
    terms = [0, 1, 3],
    temp_in_celsius = True,
    max_iterations = 1000,
    tolerance = 1e-6
):
    # assert that the number of coefficients is at least 1
    assert len(coefficients) >= 1, "Number of coefficients must be at least 1"
    # assert that the number of sample temperatures is at least 1
    assert len(sample_temps) > 0, "Number of sample temperatures must be at least 1"
    # get resistance values for each sample temperature
    sample_resistances = np.array([sh.inverse_steinhart_hart(sample_temps[i], coefficients, terms, 1.0, True, 1e-6, max_iterations, tolerance) for i in range(len(sample_temps))])    
    # return the LUT
    return np.array([sample_temps, sample_resistances]).T

# given raw ADC values and measured temperatures, return a new LUT and the fitted steinhart-hart coefficients
def fit_adc_lut(
    measured_temps,
    sample_temps,
    adc_values,
    source_adc_resolution,
    target_adc_resolution,
    reference_voltage = 3.3,
    pull_up_resistance = 4700.0,
    steinhart_hart_powers = [0, 1, 3],
    temp_in_celsius = True,
    extrapolation_max_iterations = 1000,
    extrapolation_tolerance = 1e-6
):
    # assert that the number of measured temperatures is at least 1
    assert len(measured_temps) > 0, "Number of measured temperatures must be at least 1"
    # assert that number of measured temps and ADC values are equal
    assert len(measured_temps) == len(adc_values), "Number of measured temperatures and ADC values must be equal"
    # assert that steinhart-hart powers is at least 1
    assert len(steinhart_hart_powers) > 0, "Number of steinhart-hart powers must be at least 1"

    # convert temps and ADC values to numpy arrays
    if type(measured_temps) is not np.ndarray:
        measured_temps = np.array(measured_temps)
    if type(sample_temps) is not np.ndarray:
        sample_temps = np.array(sample_temps)
    if type(adc_values) is not np.ndarray:
        adc_values = np.array(adc_values)

    # convert adc values to resistances
    resistances = adc_to_resistance(adc_values, source_adc_resolution, reference_voltage, pull_up_resistance)

    # fit steinhart-hart coefficients
    sh_coeffs = sh.fit_steinhart_hart(measured_temps, resistances, steinhart_hart_powers, temp_in_celsius)

    # convert steinhart-hart model to LUT
    lut = steinhart_hart_to_adc_lut(
        sample_temps,
        target_adc_resolution,
        reference_voltage,
        pull_up_resistance,
        sh_coeffs,
        steinhart_hart_powers,
        temp_in_celsius,
        extrapolation_max_iterations,
        extrapolation_tolerance
    )

    # return the LUT and the fitted steinhart-hart coefficients
    return lut, sh_coeffs

# given raw resistance values and measured temperatures, return a new LUT and the fitted steinhart-hart coefficients
def fit_resistance_lut(
    measured_temps,
    sample_temps,
    resistance_values,
    steinhart_hart_powers = [0, 1, 3],
    temp_in_celsius = True,
    extrapolation_max_iterations = 1000,
    extrapolation_tolerance = 1e-6
):
    # assert that the number of measured temperatures is at least 1
    assert len(measured_temps) > 0, "Number of measured temperatures must be at least 1"
    # assert that number of measured temps and ADC values are equal
    assert len(measured_temps) == len(resistance_values), "Number of measured temperatures and ADC values must be equal"
    # assert that steinhart-hart powers is at least 1
    assert len(steinhart_hart_powers) > 0, "Number of steinhart-hart powers must be at least 1"

    # convert temps and ADC values to numpy arrays
    if type(measured_temps) is not np.ndarray:
        measured_temps = np.array(measured_temps)
    if type(sample_temps) is not np.ndarray:
        sample_temps = np.array(sample_temps)
    if type(resistance_values) is not np.ndarray:
        resistance_values = np.array(resistance_values)

    # fit steinhart-hart coefficients
    sh_coeffs = sh.fit_steinhart_hart(measured_temps, resistance_values, steinhart_hart_powers, temp_in_celsius)

    # convert steinhart-hart model to LUT
    lut = steinhart_hart_to_resistance_lut(
        sample_temps,
        sh_coeffs,
        steinhart_hart_powers,
        temp_in_celsius,
        extrapolation_max_iterations,
        extrapolation_tolerance
    )

    # return the LUT and the fitted steinhart-hart coefficients
    return lut, sh_coeffs