# smartPower

A project that aims to fix the issue of manually choosing multiple time windows daily to charge a domestic electrical battery from
the grid when on a flexible rate tariff.

The solar - battery controller is a GivEnergy unit. The electrical supplier is Octopus energy

On a flexible rate tariff, where each half an hour represents a different electrical price point, pence per kwh.

The GivEnergy app only allows you to select a single window of time to choose the battery, sometimes you may want to 
select multiple windows.

There are a number of 'smart' charge options, however through testing they do not seem to select the cheapest or most 
sensible times to charge the battery

There are multiple factors the device needs to consider in order to select the correct charge window. I believe these
are;
 - Estimate time to battery depletion by;
   - the typical daily electrical usage. Average of last x same week days
   - estimated electrical solar generation
     - using an average of the last x days
     - cloud cover forecast 
   - remaining battery energy
 - Compare against cheapest half hour electrical price. Check that it will charge battery to sufficient level

Data will need to be requested from the GivEnergy, Octopus and MetOffices DataPoint API's.

Currently, this is a proof of concept.
Once functional this project can be made into a microservice, it would be nice if it were to communicate its logic daily
to the user. So the user understands when and why the battery will be charged that day.

Todo list:
[] - Validate aws, givenergy and octopus timezones. Find new solution for managing these
    - Rather than saving +1, -1 etc. Save data as UTC, UTC+1..
[] - Organise requested data ready for saving to AWS S3 as .csv files
    - Two sections of data. Historic and future;
    - Historic: GivEnergy solar generation, battery and home usage. Solar angle and height data
    - Future: Octopus agile rates. MetOffice cloud cover forecast
    
[] - Request solar angle and height data
[] - Graph / table data for daily sending from gmail

agile api data says 5pm which matches the 6pm time on the app. So (api +1 == now)
it calculated the charge time as 2pm, whereas it should have set 3pm. So. (charge_time + 1 = actual)

London now = 8am
UTC = 7am
CET = 9am
agile api data says 5pm which matches the 6pm time on the app. So (api +1 == now)
it calculated the charge time as 2pm, whereas it should have set 3pm. So. (charge_time + 1 = actual)

the agile api data has not been offset
Giv energy = London time
Octopus = UTC
AWS = UTC

Difference between giv and octopus = -1
difference between octopus and giv = 1

So
would recive time from octopus at 7am
this would equate to 8am on giv energy
and 7am on aws


In the UK the clocks go forward 1 hour at 1am on the last Sunday in March, and back 1 hour at 2am on the last Sunday in October. 

the agile api data has not been offset
