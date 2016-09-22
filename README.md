# Metromile Data Analysis

## Guessing Gear Ratios 

### Overview

The program ```guess_car_specs.py``` guesses the gear ratios in a vehicle's transmission based on a sample of its driving data. The driving data is collected via a device plugged in the OBD-II port and warehoused by Metromile (an insurance company) and is available to customers by request. 

The program's underlying operation relies heavily on an unsupervised machine learning clustering algorithm called 'mean shift'. The values of the gear ratios correspond to the N most prominent mean shift cluster centers where N is the number of gears (non-Reverse) in the vehicle's transmission. 

### Instructions

0. Clone this directory onto your local machine and change directories into it from the command line.

1. Request (from the bottom of the Account Settings page while logged into the dashboard) and download your Metromile data. Also you will need information about your car including:
  * Tire diameter (in.)
  * Number of gears (excluding Reverse)
  * [optional] : Axle Ratio

2. Unzip your MetroMile data. The directory it creates should look like: ```123456789 all_driving_data``` (if your account number was 123456789).

3. Move (or copy) any or all of the contents (.csv files) from this directory to the ```metromile``` directory. 

4. With ```metromile``` as the current working directory, run the script from the command line:
``` python guess_car_specs.py```

For a single month of driving data of your specification the script will generate a series of visualizations then guess the gear ratios. The prompts will collect information to subset and assist the program. Here is a sample input/output from my driving history from the month 2016-08:

```
Enter month number : [1, 2, ..., 12] : 8

Enter year (e.g. 2016) : 2016

Enter number of (non-reverse) gears : 5

Enter the tire diameter in inches : 26.5

If known, enter the axle ratio. If not, hit [return] : 

Best guesses for Gear Ratios:
Gear 1 : 3.88
Gear 2 : 1.99
Gear 3 : 1.39
Gear 4 : 1.00
Gear 5 : 0.79
```

Each of the gear ratios are expressed in engine speed/axle speed. For example, the program computed 5th gear as having 0.79 engine revolutions for each 1 axle revolution.

I found a reasonably credible place to crosscheck the program output with my vehicle's specifications here: https://www.driverside.com/specs/chevrolet-tracker-2002-3705-7680-0?style_id=22075


### Further Work 

![alt text](images/201608_clusteredgears.png)

The program is also enabled to label the original dataset with the gear assumed for each datapoint. Datapoints not found to be in the clusters corresponding to the likely gear ratios are given a 0 value to denote neutral. Right now there are many datapoints sampled belonging to this class, and it's unclear about whether this is a realistic assumption.

Another potential issue is the Reverse gear being conflated with 1st gear (since it is often very close in gear-ratio value). It's unclear if the samples would have any real representation of datapoints collected while the vehicle is in reverse.
