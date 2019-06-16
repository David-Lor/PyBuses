# PyBuses

**_The development of this idea of PyBuses is stopped_**
_Instead, PyBuses will be [PyBuses-Entities](https://github.com/David-Lor/PyBuses/tree/pybuses-entities), with a simpler project focused on only defining data classes and minimal logic._

PyBuses is a Python framework that helps working with public transport - related data when building 
frontend applications that provide such data to final users.

To give a real-use example, this project was made parallelly to be used by the 
[VigoBus-TelegramBot](https://github.com/David-Lor/VigoBus-TelegramBot), a Telegram Bot that provides 
real-time information about the buses arriving to the different available stops on the metropolitan bus network 
of the city of Vigo (Galicia - Spain), as well as the [VigoBus-API](https://github.com/David-Lor/Python_VigoBusAPI), 
an API to fetch the data required by that bot. 
This means the development of PyBuses and its functionalities are mostly driven by these mentioned projects.

The main goal of PyBuses is to act like a "Controller" to manage all the operations required to provide 
the information to the users. This allows using multiple functions to fetch information from. This allows , for example,
to store all the Stop data (which is not supposed to change with the time, or at least to change in real-time 
like the timetables) on local databases, to reduce the ammounts of queries to the remote API that provides all the 
required, real information.

PyBuses works with two basic assets:

* Buses: moving vehicles that arrive to Stops
* Stops: where people wait for buses, and buses arrive

You will notice that PyBuses is mainly planned to work with buses, but is compatible with other public transportation 
services that work the same way (with vehicles arriving to a Stop, having an API that provides Stop information and the 
real-time liveboard of vehicles arriving to a certain Stop). 
An [example using the iRail API](examples/belgium_trains) (Belgium trains) is available.

## TODO

- Getters/Setters for saving Stops/Buses on cache
- MySQL/SQLAlchemy Getters/Setters for Stops
- Access map APIs to fetch static images, Streetview-like pictures...
- Search locally stored stops by name
- Manage static Bus routes

## Changelog & features

### v0.1

- Initial release
- Native Stop getters, setters, deleters for MongoDB and Sqlite, with tests

## Requirements

* Python 3.7
* requests
* pymongo
