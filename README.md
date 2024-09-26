# smartPower

## Overview

An AWS Lambda project that automates the selection of an inverters charge windows. When on a Octopus Agile flexible tarrif with a GivEnergy Inverter and Battery system.

Currently this produces a x2 saving over GivEnergys best charging algorithm (June 2024).


## About the project

The Octopus Agile tarrif provides half hour time windows that represent a different electrical price point, in pence per kwh.

The GivEnergy app only allows you to select a single window of time to charge the battery, sometimes you may want to 
select multiple windows.

There are a number of 'smart' charge options, however through testing they do not seem to select the cheapest or most 
sensible times to charge the battery

There are multiple factors the device needs to consider in order to select the correct charge window. I believe these
are;
 - Estimate time to battery depletion by;
   - the typical daily electrical usage. Average of last x same week days
   - estimated electrical solar generation
     - using an average of the last x days
     - multiplied by a cloud cover forecast bias
   - remaining battery energy
 - Compare against cheapest half hour electrical price. Check that it will charge battery to sufficient level

Data will need to be requested from the GivEnergy, Octopus and MetOffices DataPoint API's.


## Data integrations & API's

- GivEnergy API for solar and house usage data plus controlling the charge times of the inverter.
- Octopus Energy API for the half hourly price point data.
- MetOffice CloudWatch API for cloud forecast data.
- AWS SNS for sending charge updates via email.
- AWS CloudWatch for scheduling future charge window.

## Todo list;
[] - Unit and integration tests

[] - Organise requested data ready for saving to AWS S3 as .csv files
    - Two sections of data. Historic and future;
    - Historic: GivEnergy solar generation, battery and home usage. Solar angle and height data
    - Future: Octopus agile rates. MetOffice cloud cover forecast
    
[] - Request solar angle and height data
[] - Graph / table data for daily sending from gmail


