# https://www.online-python.com/
# https://stackoverflow.com/questions/4142151/how-to-import-the-class-within-the-same-directory-or-sub-directory

from enum import Enum
import time
from datetime import datetime, timedelta
import requests
import logging
import threading

# encapsulates data retrieved from the can bus. 
class CanBusData:
    def __init__(self, hcvdec, lcvdec, pvdec, sodec):
        self.hcvdec = hcvdec
        self.lcvdec = lcvdec
        self.pvdec = pvdec
        self.sodec = sodec
    
    @classmethod
    def from_bytearray(cls, test):
        hc = int.from_bytes(test[0:2], byteorder='big') * 0.0001
        lc = int.from_bytes(test[2:4], byteorder='big') * 0.0001
        pv = int.from_bytes(test[4:6], byteorder='big') * 0.01
        so = int.from_bytes(test[6:7], byteorder='big') * 0.5
        return cls(hc, lc, pv, so)
    
    def to_bytearray():
        hva = (int)(self.hvvdec / 0.0001).to_bytes(2, 'big')
        lva = (int)(self.lvcdev / 0.0001).to_bytes(2, 'big')
        pva = (int)(self.pvdec / 0.01).to_bytes(2, 'big')
        soa = (int)(self.sodec / 0.5).to_bytes(1, 'big')
        return bytearray([hva[0],hva[1],lva[0],lva[1], pva[0], pva[1], soa[0]])
        
# base class for a can bus service. For testing, a mock class should be create
# which extends this base class
class CanBusService:
    def get_message(self):
        return CanBusData(1,2,3,4)

# Service that uses a pyhsical or virtual can bus
class CanBusServiceImpl(CanBusService):
    pass

# Stores the state of the battery health
class BatteryCellHealth:
    States = Enum('States', 'Over Under Ok')
    state = States.Ok
    
    def is_okay(self):
	    return self.state == self.States.Ok
    
# Stores the state of the battery pack charge    
class BatteryPackCharge:
    States = Enum('States', 'NeedsCharge Ok')
    state = States.Ok

    def is_okay(self):
	    return self.state == self.States.Ok

# Base class that stores the state of the relay
class RelayState:
    States = Enum('States', 'On Off')
    state = States.Off
    
    def on(self):
        self.state = self.States.On
        
    def off(self):
        self.state = self.States.Off
        
    def is_off(self):
        return self.state == self.States.Off
        
    def is_on(self):
        return self.state == self.States.On

# Class that interacts with the GPIO pins of the rpi.
class RelayStateImpl(RelayState):
    pass

# Base class that all weather services should extend
class WeatherService:
    
    def tomorrow_sunny():
        return False

# Batter balancer class that runs inside its own thread.
class BatteryBalancer:

    def __init__(self, canBusService, batteryCellHealth, relayState):
        self.batteryCellHealth = batteryCellHealth
        self.relayState = relayState
        self.canBusService = canBusService

    def balance_battery_pack(self, stop):
        while True:
            if stop():
                break
           # print('balancing bs= ', self.batteryCellHealth.state, ', rs=', self.relayState.state)
            can_bus_data = self.canBusService.get_message()
            if can_bus_data.lcvdec < 2.7 and self.relayState.is_off():
                self.relayState.on()
            if can_bus_data.hcvdec > 3.7 and self.relayState.is_on():
                self.relayState.off()
           
    def start(self):
        self.stop_thread = False;
        print('starting battery balancer')
        self.thread = threading.Thread(target=self.balance_battery_pack,args=(lambda: self.stop_thread,));
        self.thread.start();

    def stop(self):
        print('stopping battery balancer')
        self.stop_thread = True;
        self.thread.join();
        
# Mains charger class that runs inside its own thread.
# Business logic for this needs to be fleshed out a bit more.
class ForceMainsCharge:

    def __init__(self, canBusService, batteryCellHealth, batteryPackCharge, relayState, weatherService, dateProvider):
        self.batteryCellHealth = batteryCellHealth
        self.relayState = relayState
        self.batteryPackCharge = batteryPackCharge
        self.weatherService = weatherService
        self.dateProvider = dateProvider
        self.canBusService = canBusService

    def midnight(self, stop):
    	if self.batteryCellHealth.is_okay():
    	#   print('checking pack voltage', self.dateProvider.now())
    	# if tomorrow is sunny, no need to mains charge the battter
    	# if tomorrow is cloudy, charge battery using night cheap electricity
            if not self.weatherService.tomorrow_sunny() and not self.batteryPackCharge.is_okay():
                print('charging battery')
                self.relayState.on()
    	# start a new timer for tomorrow.
    	self.start()

    def get_delta(self, datetime):
    	x = datetime.today()
    	y = x.replace(day=x.day, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    	delta_t = y-x
    	return delta_t.total_seconds()
    
    def start(self):
    	secs = self.get_delta(self.dateProvider)
    	t = threading.Timer(secs, self.midnight)
    	t.start()
    
    def stop(self):
        pass
        
# Main method
if __name__ == "__main__":
    cbs = CanBusServiceImpl();
    rs = RelayStateImpl()
    bs = BatteryCellHealth()
    bpc = BatteryPackCharge()
    bb = BatteryBalancer(cbs, bs, rs)
    fmc = ForceMainsCharge(cbs, bs, bpc, rs, WeatherService, datetime)
    bb.start()
    fmc.start()
   # bb.stop()
   # fmc.stop()
    
