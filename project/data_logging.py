from geopy.geocoders import Nominatim
import pandas as pd
import pvlib


def calc_sun_data(latitude, longitude, tz):
    # Define your latitude, longitude, altitude, and the timezone
    latitude, longitude, tz = 52.5200, 13.4050, 'Europe/Berlin'  # Berlin as an example

    # Define the date and time you're interested in
    time = pd.Timestamp('2022-06-21 12:00:00').tz_localize(tz)  # Solstice at noon

    # Calculate solar azimuth and elevation
    solar_position = pvlib.solarposition.get_solarposition(time, latitude, longitude)
    azimuth = solar_position['azimuth'].values[0]
    elevation = solar_position['elevation'].values[0]

    print(f"Sun Azimuth: {azimuth} degrees")
    print(f"Sun Elevation: {elevation} degrees")

# calc_sun_data()

def get_lat_lon(place_name: str) -> tuple:
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode(place_name)
    if location:
        return (location.latitude, location.longitude)
    else:
        return (None, None)


if __name__ == '__main__':
    # Example usage:
    place = "Lancaster, England"
    lat, lon = get_lat_lon(place)
    print(f"{place} - Latitude: {lat}, Longitude: {lon}")

    calc_sun_data(lat, lon)