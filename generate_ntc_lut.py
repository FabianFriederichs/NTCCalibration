import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import csv
import argparse
import ntc_lut
import steinhart_hart_ntc as sh

# config
c_plot_resolution = 0.1 # degrees C

# main function
def main(argv):
    # parse arguments
    parser = argparse.ArgumentParser(description="Generate lookup tables for NTC thermistors using measured temperature and ADC values")
    parser.add_argument("--input_file", required = True, type=argparse.FileType('r'), help="Input file containing measured temperature and ADC values (2-column CSV)")
    parser.add_argument("--output_file", required = False, type=str, help="Output file containing lookup table (2-column CSV)")
    parser.add_argument("--source_adc_res", required = True, type=int, help="Source ADC resolution (bits)")
    parser.add_argument("--target_adc_res", required = True, type=int, help="Target ADC resolution (bits)")
    parser.add_argument("--reference_voltage", required = True, type=float, help="Reference voltage (V)")
    parser.add_argument("--pull_up_resistance", required = True, type=float, help="Pull-up resistance (ohms)")
    parser.add_argument("--sample_temp_start", required = False, type = float, help="Sample temperature start (Celsius)", default = 0.0)
    parser.add_argument("--sample_temp_end", required = False, type = float, help="Sample temperature end (Celsius)", default = 350.0)
    parser.add_argument("--sample_temp_step", required = False, type = float, help="Sample temperature step (Celsius)", default = 10.0)
    parser.add_argument("--steinhart_hart_powers", help="Steinhart-hart powers (comma separated)", default = "0,1,3")
    parser.add_argument("--temp_in_kelvin", help="Temperature in Kelvin instead of °C", action="store_true")
    parser.add_argument("--extrapolation_max_iterations", help="Extrapolation max iterations", default = 1000, type=int)
    parser.add_argument("--extrapolation_tolerance", help="Extrapolation tolerance", default = 1e-6, type=float)
    parser.add_argument("--noplot", help="Disables plotting of fitted model", action="store_true")
    args = parser.parse_args(argv)

    # read input file
    with args.input_file as f:
        reader = csv.reader(f)
        input_data = list(reader)
    measured_temps = [float(row[0]) for row in input_data]
    adc_values = [float(row[1]) for row in input_data]

    # calculate resistances
    measured_resistances = ntc_lut.adc_to_resistance(adc_values, args.source_adc_res, args.reference_voltage, args.pull_up_resistance)

    # get steinhart-hart powers
    powers = [int(p) for p in args.steinhart_hart_powers.split(",")]

    # sample temperatures (if specified, otherwise use measured temperatures)
    if args.sample_temp_start is not None and args.sample_temp_end is not None and args.sample_temp_step is not None:
        sample_temps = np.arange(args.sample_temp_start, args.sample_temp_end + args.sample_temp_step, args.sample_temp_step)
    else:
        sample_temps = measured_temps

    # fit lut
    lut, sh_coeffs = ntc_lut.fit_lut(
        measured_temps,
        sample_temps,
        adc_values,
        args.source_adc_res,
        args.target_adc_res,
        args.reference_voltage,
        args.pull_up_resistance,
        powers,
        not args.temp_in_kelvin,
        args.extrapolation_max_iterations,
        args.extrapolation_tolerance
    )

    # print steinhart-hart coefficients
    print("Steinhart-Hart coefficients:")
    for i, p in enumerate(powers):
        print("a{} = {}".format(p, sh_coeffs[i]))
    # print lut
    print("Lookup table:")
    print(lut)

    # plot fitted model and data points if plotting is enabled.
    # two plots, one with ADC vs. temperature and one with resistance vs. temperature
    if not args.noplot:        
        fig = plt.figure()
        ax1, ax2 = fig.subplots(2, 1)

        # calculate points for fitted model
        model_temps = np.arange(min(measured_temps), max(measured_temps), c_plot_resolution)
        model_resistances = np.array([sh.inverse_steinhart_hart(model_temps[i], sh_coeffs, powers, 1.0, args.temp_in_celsius, 1e-6, args.extrapolation_max_iterations, args.extrapolation_tolerance) for i in range(len(model_temps))])
        model_adc_values = ntc_lut.resistance_to_adc(model_resistances, args.source_adc_res, args.reference_voltage, args.pull_up_resistance)

        # resistance vs. temperature
        ax1.set_title("Resistance vs. Temperature")
        ax1.scatter(measured_resistances, measured_temps, label="Measured data points")
        ax1.plot(model_resistances, model_temps, label="Fitted model")
        ax1.set_ylabel(f"Temperature ({'°C' if args.temp_in_celsius else 'K'})")
        ax1.set_xlabel("Resistance (ohms)")
        ax1.legend()

        # adc vs. temperature
        ax2.set_title(f"ADC value (0-{2**args.source_adc_res - 1}) vs. Temperature")
        ax2.scatter(adc_values, measured_temps, label="Measured data points")
        ax2.plot(model_adc_values, model_temps, label="Fitted model")
        ax2.set_ylabel(f"Temperature ({'°C' if args.temp_in_celsius else 'K'})")
        ax2.set_xlabel(f"ADC value (0-{2**args.source_adc_res - 1})")
        ax2.legend()

        fig.tight_layout()
        plt.show(block = True)

    # write output file if specified
    if args.output_file is not None:
        with open(args.output_file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(lut)

# entry point
if __name__ == "__main__":
    main(sys.argv[1:])