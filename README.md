# domoticz-jablotron

A simple SIA plugin for Domoticz and Jablotron alarm systems based on SIA over UDP.

The SIA parser backend is based on https://github.com/eavanvalkenburg/pysiaalarm.

In order to receive SIA message, you need to configure an ARC in F-Link and set
it to report SIA events. Currently, only PG reports and motion sensors are
tested, all other events are ignored. The motion sensors need to be attached
to PG outputs, otherwise no SIA event is generated.

Set the port in the plugin to the same port as defined in F-Link.

Devices will appear automatically as they are triggered if device generation
is enabled. Otherwise, no new devices are added to the system.
