# iRail (Belgium trains) API example

This is an example using a real API with PyBuses. This example uses the iRail API,
which serves information about the train schedules in Belgium.

- [About iRail](https://hello.irail.be/)
- [iRail documentation](https://docs.irail.be/#stations-stations-api-get)

## Useful endpoints

- Get all available stations: https://api.irail.be/stations/?format=json&lang=en
- Get departures on the station ID `BE.NMBS.008892007`: 
http://api.irail.be/liveboard/?id=BE.NMBS.008892007&arrdep=departure&lang=en&format=json
- Get arrivals on the station ID `BE.NMBS.008892007`: 
http://api.irail.be/liveboard/?id=BE.NMBS.008892007&arrdep=arrival&lang=en&format=json
- Liveboard Frontend: https://www.b-europe.com/EN/Real-time

## Useful knowledge

- All Stop IDs start with `BE.NMBS.00` and then more numbers,
so we can work with the integer StopID format that PyBuses use
In example, the (full-official) Stop ID `BE.NMBS.008008094` would be (integer) `8008094` on PyBuses
- A "Station" equals to "Stop" on PyBuses
- A "Train" equals to "Bus" on PyBuses
- Stations have the "name" (English version of the name) and the "standardname" (original version of the name),
so we are using the "standardname" as the Stop name
- The Liveboard (the trains that arrive to a station) can show Arriving trains or Departuring trains.
Since PyBuses does not differentiate between these two possibilities, we will be using Arriving trains on our Bus Getter
- The Liveboard of Arriving trains can show trains that have already arrived, and will show a negative time 
when getting the remaining time.
