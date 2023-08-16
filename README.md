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
   - the typical daily electrical usage. Average of last x days
   - estimated electrical solar generation
     - using an average of the last x days
     - cloud cover forecast 
   - remaining battery energy
 - Compare against cheapest half hour electrical price. Check that it will charge battery to sufficient level

Data will need to be requested from the GivEnergy, Octopus and MetOffices DataPoint API's.

Currently, this is a proof of concept.
Once functional this project can be made into a microservice, it would be nice if it were to communicate its logic daily
to the user. So the user understands when and why the battery will be charged that day.

