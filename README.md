---
title: "NTCCalibration"
author: "Fabian Friederichs"
date: '2022-12-31'
bibliography: references/references.bib
output: html_document
---

# NTCCalibration
This is a python script for calibrating NTC thermistors as they are found in 3D printer hotends.
The user supplies some measured temperature / ADC value pairs and some meta information.
A Steinhart-Hart model [@steinhart1968calibration] is fitted to the data points and a lookup table over temperatures and
ADC values is extrapolated from this.

Optionally, it also works directly with resistance values instead of ADC readings.

### Features
- Least squares fit to an arbitrary number of data points
- Supports arbitrary powers of the Steinhart-Hart model
- Spits out ADC LUTs compatible with Marlin, working directly with raw ADC readings from Marlin, no manual conversion required
- Optional resistance-only mode which generates LUTs with temp/resistance entries, given
temp/resistance data points instead of ADC readings

### Prerequisites
- Python $\geq$ 3.7
- Packages: numpy, matplotlib + GUI backend (e.g. pyqt5)

## How to get Data?
In case of the [Marlin](https://marlinfw.org/) firmware, you can query current ADC readings
using the gcode commands `M105` or `M155`. In the advanced configuration header (*Configuration_adv.h*),
`SHOW_TEMP_ADC_VALUES` must be defined to get raw ADC readings along with the temperatures.

For temperature data, a thermocouple-based thermometer is a good option.
To get the most accurate readings, drill a small hole into the side of your nozzle and place
the thermocouple in there. I also had luck with simply holding it firmly into the nozzle orifice.

3 temperature / ADC pairs are enough in theory, but the more data points you acquire, the better
the fit of the model will be. Currently the model is fitted using a simple least squares approach,
therefore it is beneficial to filter out any obvious outliers.

A fairly quick procedure to generate enough data points I found is the following:
1. Start at room temperature and set the extruder temperature to the highest, safe value for your setup.
2. Record temperature and ADC values in 5 or 10 degree steps
3. When the target temperature is reached, turn off heating and again record data points every 5 or 10 degrees
    until a temperature close to room temp is reached
4. Average the results from step 2 and 3 to reduce the error due to temperature lag in the system.

Alternatively, resistance values can be used in resistance mode instead of ADC readings.

## Steinhart-Hart Model
The general Steinhart-Hart equation is used to model the dependency between an NTC thermistor's
resistance and the temperature in Kelvin:

$$
  T\left(R\right) = \frac{1}{\sum\limits_{i}^{\infty}a_{i}\ln\left(R\right)^{i}}
$$

The powers (i) actually used can vary, but 0 (constant), 1 (linear) and 3 (cubic) is the most common
configuration:

$$
  T\left(R\right) \approx \frac{1}{a_{0} + a_{1}\ln\left(R\right) + a_{3}\ln\left(R\right)^{3}}
$$

This script supports any configuration of coefficients and defaults to 0,1,3.

## Running the Script
The main python script is *generate_ntc_lut.py*.
Here is an example command line for creating a LUT from the values in *volcano_thermistor_measurements.csv*:
```
python generate_ntc_lut.py --input_file volcano_thermistor_measurements.csv --output_file volcano_thermistor_table.csv --source_adc_res 12 --target_adc_res 10 --reference_voltage 3.3 --pull_up_resistance 4700 --sample_temp_start 0 --sample_temp_end 300 --sample_temp_step 10
```

In resistance mode, instead of ADC readings and LUTs we use resistance values directly:
```
python generate_ntc_lut.py --input_file volcano_thermistor_measurements_res.csv --output_file volcano_thermistor_table_res.csv --resistance_mode --sample_temp_start 0 --sample_temp_end 300 --sample_temp_step 10
```

The resulting Steinhart-Hart coefficients and the lookup table gets printed to the console and the lookup table is stored
into the given CSV file if applicable.

If plotting is not disabled, the resulting plot should look somewhat like this:
![Example Output Plot](img/example_plot.svg)

## Command Line Parameters

**--input_file** [req] Two-column CSV file with temperature values in the first and ADC (or resistance values in resistance mode) readings in the second    column.

**--output_file** [opt] Two-column CSV file with sampled temperature values in the first and corresponding ADC (or resistance values in resistance mode) values in the second column. If this argument is not given, no output is saved and the LUT is printed in the console.

**--resistance_mode** [opt] Enables resistance-only mode. Inputs are raw temperature/resistance pairs and the output LUT contains
resistance values instead of ADC values.

**--source_adc_res** [opt] (Required in ADC mode) Resolution of the input ADC values in bits. When using Marlin, this can be looked up in the corresponding *HAL.h* header below the respective directory for your platform (e.g. *Marlin/src/HAL/LPC1768/HAL.h*). Search for `HAL_ADC_RESOLUTION`.

**--target_adc_res** [opt] (Required in ADC mode) Resolution in bits of the ADC values stored in the final LUT. For Marlin this is usually 10.

**--reference_voltage** [opt] (Required in ADC mode) Reference voltage of the ADC. When using Marlin, this can be looked up in the corresponding *HAL.h* header below the respective directory four your platform (e.g. *Marlin/src/HAL/LPC1768/HAL.h*). Search for `HAL_ADC_VREF`. Usually 3.3V or 5.0V.

**--pull_up_resistance** [opt] (Required in ADC mode) Pullup resistor value of the voltage divider used to measure the thermistor voltage. Can be found in the schematic of the board in question. 4700 (Ohms) seems to be a typical value.

**--sample_temp_start** [opt] Lowest temperature entry in the final LUT. Defaults to 0 °C.

**--sample_temp_end** [opt] Highest temperature entry in the final LUT. Defaults to 300 °C.

**--sample_temp_step** [opt] Step size of the final LUT. Defaults to 10 °C.

**--steinhart_hart_powers** [opt] Comma separated list of powers to use in the Steinhart-Hart Model. Defaults to *0,1,3*

**--temp_in_kelvin** [opt] Flag that specifies that temperatures are given in Kelvin instead of °C.

**--extrapolation_max_iterations** [opt] Maximum number of iterations to use when doing numerical inversion of the model for building the LUT. Defaults to 1000.

**--extrapolation_tolerance** [opt] Maximum allowable temperature error when doing numerical inversion of the model for building the LUT. Defaults to 1e-6.

**--noplot** [opt] Flag that disables a plot being shown at the end of the model fitting.

## Adding a Custom Thermistor to Marlin (successfully tested with 2.1.1)

1. Copy one of the named thermistor headers, e.g. *Marlin/src/module/thermistor/thermistor_5.h* and give it a new number, e.g. *Marlin/src/module/thermistor/thermistor_**3000**.h*.
2. In the new header file, change the name of the LUT accordingly, e.g. `temptable_5` -> `temptable_3000`.
3. Add entries from the ouput CSV file.
4. In the header file *Marlin/src/module/thermistor/thermistors.h* add an entry like this:
```C++
#if ANY_THERMISTOR_IS(3000) // Entry for the new thermistor
  #include "thermistor_3000.h" // Include the corresponding header file containing the LUT
#endif
```
5. In *Marlin/src/lcd/thermistornames.h* add the new thermistor name:
```C++
#elif THERMISTOR_ID == 3000
  #define THERMISTOR_NAME "New Thermistor Name"
```
6. Recompile and flash the modified firmware.