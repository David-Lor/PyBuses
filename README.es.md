# PyBuses

PyBuses es un framework creado en Python y diseñado para facilitar el desarrollo de aplicaciones y herramientas que trabajen con autobuses de transporte y otros medios similares, especialmente al trabajar con un bot de Telegram.

Los dos tipos de objetos fundamentales con los que se trabaja son las paradas de autobus (Stop) y los propios autobuses (Bus) que pasan por estas paradas. PyBuses debe "conectarse" con otros scripts, librerías o frameworks externos que obtengan los datos necesarios (información de las paradas y buses) para aportarlos a los objetos que gestiona este framework.

PyBuses utiliza SQLite3 tanto para almacenar su información como para almacenar los logs. Se utilizan los módulos propios [Python-SQLite-DBManager](https://github.com/EnforcerZhukov/Python-SQLite-DBManager) y [Python-Custom-Logging](https://github.com/EnforcerZhukov/Python-Custom-Logging).

## Principios de funcionamiento

* Todo se gestiona desde el objeto PyBuses.
* Un objeto PyBuses se inicializa con una serie de funciones externas que obtienen la información de paradas y autobuses desde fuentes externas. Se pueden definir múltiples funciones para crear backups (en caso de que falle una fuente, se utiliza otra, aunque todas deberán aportar la misma información).
* Las dos entidades fundamentales existentes son Stop (paradas de autobus) y Bus (autobuses que pasan por paradas). Estos dos objetos son simples y no contienen apenas métodos (por ejemplo, para buscar los autobuses de una parada hay que utilizar un método de PyBuses).
* Los autobuses pasan por las paradas, manejando listados de autobuses con una estimación en tiempo real de los minutos que faltan para que lleguen a una parada.

## Componentes del proyecto

### PyBuses

Es el objeto base elemental desde el que se trabaja. Contiene todos los métodos eficaces (buscar paradas, guardar paradas, buscar autobuses, etc.). Se inicializa con las funciones (denominadas _getters_) que permiten consultar la información de las paradas y los autobuses que pasan por una parada.

PyBuses también se enlaza con una base de datos donde se guardarán las paradas consultadas, para tener acceso a las mismas sin necesidad de consultar a las fuentes externas si la parada fue consultada con anterioridad.

El objeto PyBuses cuenta internamente con otros objetos (aunque no formen parte del mismo módulo):

#### Database

Es una base de datos SQLite3 creada a partir del módulo Databases.DBManager (objeto Database). En esta base de datos se guardan las paradas consultadas con anterioridad, así como las imágenes StreetView y Google Maps consultadas previamente (realmente no se guardan las imágenes, sino las ID de archivo enviado a Telegram).

#### StopsCache

Actúa como primer _getter_ de Stops predeterminado. En él se guardan temporalmente las paradas consultadas, para tener acceso a las mismas rápidamente. A sus métodos accede PyBuses cuando se requiere buscar o guardar alguna parada en la lista local.

#### StopsDB

Actúa como segundo _getter_ de Stops predeterminado. Se inicializa con el objeto Database generado en PyBuses, y accede a los métodos de lectura y escritura de la base de datos. A sus métodos accede PyBuses cuando se requiere buscar, guardar o modificar alguna parada guardada en la base de datos.

### Assets

#### Stop

Objeto que corresponde a una parada. Se identifica siempre por un ID o número de parada (numérico, que suele corresponder con el número de parada real) y tiene un nombre (a menudo es el nombre y número de la calle, o una ubicación descriptiva). Adicionalmente tiene una ubicación (latitud y longitud como dos floats).

* stopid (int, obligatorio)
* name (string, obligatorio)
* lat (float, opcional)
* lon (float, opcional)

#### Bus

Objeto que corresponde a un bus (que pasa por una parada, aunque el objeto no tiene referencia a dicha parada). Información que contiene: línea, ruta, tiempo que falta para que llegue a una parada, y distancia entre bus y parada (opcional).

* line (string, obligatorio)
* route (string, obligatorio)
* time (int, obligatorio)
* distance (float, opcional)

### GoogleStreetView

Este objeto gestiona las imágenes de Google StreetView para las paradas, es decir, permite obtener imágenes desde la API de StreetView mostrando el aspecto de la parada, a partir de su ubicación (lat. y lon.).

El método principal para obtener una imagen de StreetView para una parada concreta es get_streetview con el objeto Stop que se quiere consultar como parámetro. Sin embargo, este objeto está diseñado para ser utilizado desde un bot de Telegram que permita enviar una imagen tanto desde un objeto Bytes (la propia imagen) como desde una ID de archivo previamente enviado.

Queremos evitar descargar imágenes de paradas que ya fueron consultadas anteriormente y cuya imagen de StreetView ya fue enviada con anterioridad mediante Telegram, proceso que siempre devuelve la ID de archivo enviado. Posteriormente, la imagen se puede volver a enviar a cualquier usuario de Telegram con su ID, sin necesidad de pedirle a la API de Google nuevamente la imagen, ni descargarla.

Por tanto, el método get_streetview buscará primero si la imagen de StreetView está guardada en la base de datos local (realmente no guardamos la imagen en sí, sino el ID de archivo enviado en Telegram), y si no es así, se descarga. El método puede devolver arbitrariamente tanto un objeto Bytes con la imagen descargada como el ID de archivo, por lo que el método que va a enviar la imagen a Telegram debe aceptar ambas posibilidades (por ejemplo, el método send_photo de pyTelegramBotApi).

Cuando una imagen que no había sido registrada en la base de datos se envía por primera vez, es necesario ejecutar el método save_streetview_db(stopid, fileid) manualmente desde la función externa que envía la imagen a Telegram.

Los métodos disponibles para este objeto son:

* get_streetview(stop): devuelve una imagen StreetView de la parada indicada como parámetro. La parada debe tener siempre los valores lat y lon cubiertos y correctos, pues se usarán para determinar la ubicación de la misma. El método devuelve, o bien un objeto Bytes con la imagen que devuelve la API de Google, o bien la ID de archivo de Telegram, si la parada ya se había enviado con anterioridad y está registrada en la base de datos local.
* save_streetview_db(stopid, fileid): guarda en la base de datos una imagen de StreetView que fue enviada por Telegram. De la imagen se guarda el ID de archivo devuelto por la API de Telegram al enviar la imagen.
* search_streetview_db(self, stopid): busca una parada (identificada por su ID) en la base de datos de imágenes de StreetView. Si la encuentra, devuelve la ID de imagen enviada por Telegram. Si no está, devuelve None.
* get_streetview_live(stop, sizeX, sizeY): obtiene la imagen de StreetView desde la API de Google. Devuelve la imagen como un objeto Bytes. Si la consulta sale mal, requests levantará una excepción propia que debe ser interpretada por la función externa que llama al método, ya sea este o el geńerico get_streetview(stop). Los parámetros sizeX y sizeY hacen referencia al tamaño de la imagen; si no se indican, se usan por defecto los tamaños especificados en el propio módulo GoogleStreetView.py.

### GoogleMaps

El objeto GoogleMaps funciona, en general, igual que GoogleStreetView. Cuenta con los mismos métodos y trabaja de la misma forma (consulta previamente si una imagen fue descargada por anterioridad para recuperar su ID de archivo y reenviarla por Telegram, en lugar de descargarla nuevamente). Sin embargo, los mapas tienen unos cuantos parámetros adicionales que cambian las cosas, como la orientación de la imagen o el tipo de mapa (satelital o normal).

## Uso general

### 1) Crear objeto PyBuses

El objeto PyBuses se inicializará en nuestro proyecto base. En el constructor es necesario declarar, al menos, una función para obtener la información de las paradas, y otra para obtener la de los autobuses. Es posible declarar varias funciones (en forma de lista o tupla) y así crear funciones de refuerzo (en caso de que una falle se pasa a la siguiente).

Ejemplo utilizando una librería externa llamada "LST" que contiene dos funciones para obtener información de paradas y otras dos para obtener autobuses:

```python
>>> from LST import get_stop1, get_stop2, get_buses1, get_buses2 #Funciones externas que obtienen paradas y buses
>>> from PyBuses import PyBuses
>>> pybuses = PyBuses([get_stop1, get_stop2], [get_buses1, get_buses2], db_name="Databases/LST_Stops.db")
```

### 2) Obtener información de una parada

Para obtener información sobre una parada se utiliza el método PyBuses.find_stop, indicando como parámetro la ID/Número de parada. El método buscará la parada en todos los _getters_ (nativos y externos), y si existe, la devolverá como un objeto Stop con toda la información que se pudiese obtener cubierta (como mínimo se debe recuperar el nombre, siendo la ubicación en lat. y lon. opcional). El método realiza las siguientes acciones:

* Se buscará la parada en la cache local y base de datos de paradas guardadas localmente.
* Si no se encuentra ahí, se buscará mediante todos los _getters_ designados en el objeto PyBuses.
* Si alguno de los _getters_ declara que la parada no existe, se dejará de buscar en los siguientes, generando la excepción propia StopNotFound. Los _getters_ genéricos nunca declaran que la parada no existe, siendo algo que sólo los _getters_ externos deberían hacer.
* Si ninguno de los _getters_ obtuvo la parada y todos ellos reportaron fallos (por ejemplo debido a errores en el servidor remoto o conexión propia) se levantará la excepción genérica ConnectionError.

```python
>>> stop = pybuses.find_stop(1234) #Parada que existe
>>> print(stop.name)
Pillbox North

>>> stop = pybuses.find_stop(1000) #Parada que no existe
Traceback (most recent call last):
[...]
__main__.StopNotFound: Stop #1000 not found!

>>> stop = pybuses.find_stop(1234) #Servidor de consulta caído
Traceback (most recent call last):
[...]
ConnectionError: Could not retrieve Stop #1234 info from any of the getters
```

### 3) Obtener buses de una parada

El objeto PyBuses tiene el método get_buses(stopid) que buscará los autobuses de la parada indicada (por ID) y devolverá los resultados. Este método no verifica si la parada existe o no existe, por lo que es necesario asegurar de antemano que se opera sobre una parada válida. También es posible llamar al método get_buses() desde un objeto Stop creado.

```python
>>> STOP_ID = 5800
>>> stop = pybuses.find_stop(STOP_ID)
>>> buses = pybuses.get_buses(STOP_ID)
>>> for bus in buses:
...     print("{} - {} - {} min".format(
...             bus.line,
...             bus.route,
...             bus.time
...     )
...
9A - P. INDUSTRIA por TORRECEDEIRA - 0 min
15C - SAMIL por PI MARGALL - 10 min
4A - COIA por CASTELAO - 10 min
27 - BEADE - 10 min
15A - COIA - SAMIL - 19 min
11 - SAN MIGUEL por FLORIDA - 21 min
9A - P. INDUSTRIA por PI MARGALL - 27 min
24 - ESTACION TREN - 27 min
6 - PRAZA DE ESPAÑA (Kiosco) - 29 min
15B - SAMIL por BEIRAMAR - 40 min
28 - AREAL - 43 min
9B - GARCIA BARBÓN - 44 min
25 - PRAZA DE ESPAÑA (Kiosco) - 53 min
```

## Funciones para obtener paradas

Las funciones que obtienen la información de las paradas deben ser creadas externamente, y al construir el objeto PyBuses se indican como parámetros del constructor. Estas funciones consultan el servidor o fuente de datos pertinentes para obtener la información de la parada a partir de la ID, único dato que se conoce de antemano. Estas funciones, cuyo funcionamiento interno es irrelevante para PyBuses, debe cumplir las siguientes indicaciones:

* La función recibe como parámetro el ID/número de parada (int).
* Si la función encuentra la parada, debe devolver un objeto Stop inicializado con toda la información pertinente.
* Siempre que se devuelve la parada, el objeto Stop debe estar inicializado al menos con el nombre de parada (la ubicación es opcional). Si el nombre es None, se interpretará que hubo un error al encontrar la parada. Si no se puede incluir el nombre, deberá ser un string vacío.
* Si la parada no ha sido encontrada, debe devolver False.
* Si hubo un error técnico al encontrar la parada, debe devolver None. También se devolverá None si la función no puede asegurar la no-existencia de una parada (por ejemplo, la función que busca paradas en la base de datos, porque el que una parada no esté en la BD no tiene por qué significar que no exista, sino que no la hemos registrado).
* Es importante diferenciar los errores de parada no encontrada de otros errores, pues estos escenarios se tratarán de forma diferente. Si en una función no se puede asegurar que la parada no existe, se debe devolver None y no False.

Así mismo, en PyBuses existen funciones predeterminadas que se utilizan antes de las especificadas, para localizar paradas que ya fueron consultadas con anterioridad sin tener que acceder a los servicios en línea:

* Búsqueda en listado/caché local (StopsCache)
* Búsqueda en base de datos local (StopDB)

## Funciones para obtener buses

Las funciones que obtienen buses funcionan de forma similar a las que obtienen paradas, pero su principal característica es que tratan información más dinámica, pues la información de los buses cambia cada poco tiempo. Estas funciones, cuyo funcionamiento interno es irrelevante para PyBuses, debe cumplir las siguientes indicaciones:

* La función recibe como parámetro el ID/número de parada a consultar (int).
* Si la función logra obtener el listado de autobuses, devuelve una lista de objetos Bus con toda su información cubierta (como mínimo la línea, ruta y tiempo restante). Si en ese momento no hay autobuses, devuelve una lista vacía.
* No es necesario devolver los autobuses ordenados, pues el método find_buses de PyBuses ordenará los autobuses por orden de tiempo (se mostrarán antes los que lleguen antes a la parada).
* Si hubo un error técnico al localizar los autobuses, debe devolver None.
* Es importante diferenciar cuándo una parada no tiene autobuses en un momento dado (lista vacía) de cuando surgió un error que imposibilita el obtener ese listado (None).

## Almacenamiento de paradas y otros datos

### Cache local

Las paradas consultadas son guardadas de forma temporal en una lista local, desde el módulo StopsCache, que contiene un objeto StopsCache con una lista y métodos para localizar, guardar y actualizar paradas. El objeto PyBuses utiliza el método de buscar paradas de StopsCache como primer función getter.

### Base de datos

PyBuses almacenará ciertos datos en una base de datos SQLite3. De esta forma se evita tener que acceder a servicios en línea para acceder a cierta información que fue buscada con anterioridad, ahorrando tiempo y conexión. Los datos que se guardan son:

* Todas las paradas que se han buscado (concretamente se guardan: ID, nombre, ubicación, fecha y hora en la que se añadió a la BD, fecha y hora de la última actualización)
* Imágenes (Google Maps y StreetView) de paradas, enviadas con anterioridad (pensado para ser utilizado con un bot de Telegram, almacenando las ID de archivo enviado a Telegram)

#### Estructura de la base de datos

La base de datos Stops contiene las siguientes tablas:

##### stops

Aquí se guardan todas las paradas que han sido solicitadas por los usuarios, cuya información es consultada en el servicio o servicios online designados. De esta forma, cuando se necesita obtener información de una parada (nombre y ubicación) se consulta en esta tabla antes de consultar en el servicio online.

Campos de la tabla:

* stopid (unsigned integer, primary key) - ID/número de parada (identificador único)
* name (text, not null) - Nombre de la parada (requerido)
* lat (text) - Latitud de la parada (opcional)
* lon (text) - Longitud de la parada (opcional)
* registered (text) - Fecha y hora en la que se registró la parada por primera vez (opcional)
* updated (text) - Fecha y hora en la que se actualizó la parada por última vez (opcional) - coincide con "registered" si nunca se actualizó

##### streetview

Esta tabla almacena todas las imágenes de StreetView consultadas. Las imágenes se guardan con el ID de archivo enviado por Telegram, y se referencian por la ID de parada a la que corresponden. Por último, se guarda la fecha y hora en la que se guardó originalmente esa imagen.

Campos de la tabla:

* stopid (unsigned integer, primary key) - ID de la parada a la que corresponde esta imagen
* fileid (text, not null) - ID del archivo original enviado a Telegram
* created (text) - Fecha y hora en la que se guardó la parada por primera vez (opcional)

##### maps

Esta tabla almacena todas las imágenes de Google Maps consultadas. Las imágenes se guardan con el ID de archivo enviado por Telegram, y se referencian por la ID de parada a la que corresponden y sus dos atributos según el tipo de mapa (terrenal/mapa y vertical/horizontal). Por último, se guarda la fecha y hora en la que se guardó originalmente esa imagen.

Campos de la tabla:

* stopid (unsigned integer, primary key) - ID de la parada a la que corresponde esta imagen
* fileid (text, not null) - ID del archivo original enviado a Telegram
* vertical (boolean, primary key) - 1=imagen es vertical; 0=imagen es horizontal
* terrain (boolean, primary key) - 1=imagen es vista satélite; 0=imagen es tipo mapa
* created (text) - Fecha y hora en la que se guardó la parada por primera vez (opcional)
