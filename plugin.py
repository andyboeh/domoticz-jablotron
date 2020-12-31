"""
<plugin key="jablotron-sia" name="Jablotron SIA" author="andyboeh" version="0.0.1" wikilink="https://github.com/andyboeh/domoticz-jablotron" externallink="https://www.domoticz.com/forum/">
    <params>
        <param field="Address" label="Listen Address, empty for all" width="110px" required="false" default=""/>
        <param field="Port" label="Listen port" width="50px" required="true" default="8125"/>
        <param field="Mode1" label="PIR sensor device creation" width="230px" required="true">
            <options>
                <option label="Off" value="False"/>
                <option label="On" value="True" default="true"/>
            </options>
        </param>
        <param field="Mode2" label="Account ID" width="100px" required="true" default="12345"/>
        <param field="Mode6" label="Debug mode" width="75px" required="true">
            <options>
                <option label="Off" value="False" default="true"/>
                <option label="On" value="True"/>
            </options>
        </param>
    </params>
</plugin>
"""


import Domoticz
import re
from pysiaalarm import SIAAccount, SIAUDPClient, SIAEvent

event_regex = r"""
[\^](?P<section>.*)[\^]
[\/]
(?P<device>.*)[\^]
(?P<name>.*)[\^]
"""
EVENT_MATCHER = re.compile(event_regex, re.X)

class BasePlugin:
    enabled = False
    def __init__(self):
        self.account = None
        self.client = None
        self.reset = []
        return

    def onSIAMotion(self, deviceid):
        Domoticz.Debug("onSIAMotion")
        if Devices:
            for DOMDevice in Devices:
                if Devices[DOMDevice].DeviceID == deviceid:
                    Devices[DOMDevice].Update(nValue=1, sValue="1")
                    Domoticz.Debug("Updated motion sensor.")
                    self.reset.append(deviceid)
                    return True
        return False
                        
    def onSIAMessage(self, event: SIAEvent):
        Domoticz.Debug("Received SIA Event: " + event.message)
        if event.message:
            parsed_event = EVENT_MATCHER.match(event.message)
            if not parsed_event:
                Domoticz.Debug("Could not parse event.")
                return
            content = parsed_event.groupdict()
            deviceid = content["device"]
            if not deviceid.startswith("RC"):
                Domoticz.Debug("Not a motion event.")
                return

            found = self.onSIAMotion(deviceid)

            if not found and Parameters["Mode1"] == "True":
                availableID = 1
                if Devices:
                    for device in Devices:
                        if device > availableID: break
                        else: availableID += 1            

                Domoticz.Device(Name=content["name"], Unit=availableID, DeviceID=deviceid, Type=244, Subtype=62, Switchtype=8, Used=1).Create()
                if availableID in Devices:
                    Domoticz.Log("Successfully created device: " + content["name"])
                    self.onSIAMotion(deviceid)
                else:
                    Domoticz.Log("Error creating device: " + content["name"])
                

    def onStart(self):
        # Set heartbeat
        Domoticz.Heartbeat(5)

        # Set debugging
        if Parameters["Mode6"] == "True": 
            Domoticz.Debugging(2)
            Domoticz.Debug("Debugging mode activated")
        
        config = {
            "account_id" : Parameters["Mode2"],
            "key" : "",
            "dialect" : "jablo",
            "port" : int(Parameters["Port"]),
            "host" : Parameters["Address"],
        }
        
        self.account = [SIAAccount(config["account_id"], config["key"], config["dialect"])]
        self.client = SIAUDPClient(config["host"], config["port"], self.account, function=self.onSIAMessage)
        self.client.start()
        Domoticz.Debug("Jablotron SIA plugin started.")

    def onStop(self):
        if self.client:
            self.client.stop()
        Domoticz.Debug("Jablotron SIA plugin stopped.")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat")
        if Devices:
            for DOMDevice in Devices:
                if Devices[DOMDevice].DeviceID in self.reset:
                    Devices[DOMDevice].Update(nValue=0, sValue="0")
                    Domoticz.Debug("Motion sensor " + Devices[DOMDevice].DeviceID + " reset")
        self.reset = []

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()
