# https://www.online-python.com/
# https://stackoverflow.com/questions/4142151/how-to-import-the-class-within-the-same-directory-or-sub-directory

import can
import RPi.GPIO as GPIO
from enum import Enum
import time
from datetime import datetime, timedelta
import requests
import logging
import threading

logging.basicConfig(filename='montini.log', format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)

# encapsulates data retrieved from the can bus. 
class CanBusData:
    def __init__(self, hcvdec, lcvdec, pvdec, sodec, arbitration_id):
        self.hcvdec = hcvdec
        self.lcvdec = lcvdec
        self.pvdec = pvdec
        self.sodec = sodec
        self.arbitration_id = arbitration_id
    
    @classmethod
    def from_bytearray(cls, test, arbitration_id):
        hc = int.from_bytes(test[0:2], byteorder='big') * 0.0001
        lc = int.from_bytes(test[2:4], byteorder='big') * 0.0001
        pv = int.from_bytes(test[4:6], byteorder='big') * 0.01
        so = int.from_bytes(test[6:7], byteorder='big') * 0.5
        return cls(hc, lc, pv, so, arbitration_id)
    
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

    def __init__(self):
        #self.bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
        self.bus = can.ThreadSafeBus(channel='can0', bustype='socketcan_native')
        self.last_message = None

    def get_message(self):
        while True:
            msg = self.bus.recv(1)
            if msg is not None and msg.arbitration_id == 1537:
                return CanBusData.from_bytearray(msg.data, msg.arbitration_id )

        return None

# Stores the state of the battery health
class BatteryCellHealth:
    States = Enum('States', 'Nok Ok')
    state = States.Ok

    def ok():
        self.state = States.Ok
    
    def nok():
        self.state = States.Nok
    
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

# gpio setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
switchon = 23
GPIO.setup(switchon, GPIO.OUT)
GPIO.output(switchon, False)


# Class that interacts with the GPIO pins of the rpi.
class RelayStateImpl(RelayState):

    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        switchon = 23
        GPIO.setup(switchon, GPIO.OUT)
        GPIO.output(switchon, False)

    def on(self):
        self.state = self.States.On
        GPIO.output(switchon, True)
        
    def off(self):
        self.state = self.States.Off
        GPIO.output(switchon, False)
        
    def is_off(self):
        return self.state == self.States.Off
        
    def is_on(self):
        return self.state == self.States.On


# Base class that all weather services should extend
class WeatherService:
    
    def tomorrow_sunny():
        return False

class WeatherServiceImpl(WeatherService):
    
    def tomorrow_sunny():
        dublin = requests.get('http://api.openweathermap.org/data/2.5/onecall?lat=53.349722&lon=-6.260278&exclude=alerts,minutely,hourly,current&appid=489d0ec288c646a028285da15ab17895')
        today_uvi = dublin.json()['daily'][0]['uvi']
        today_clouds = dublin.json()['daily'][0]['clouds']
        sunshinetoday = ((today_uvi * 10) + (100 - today_clouds))/2
        logging.info(f'UVI = {today_uvi} Clouds = {today_clouds} Sunshine Today = {sunshinetoday}')
        return sunshinetoday >= 50


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
            logging.info('balancing battery cell health = %s relay state = %s', self.batteryCellHealth.state, self.relayState.state)
            can_bus_data = self.canBusService.get_message()
            logging.info('lv:%s hv:%s soc:%s', can_bus_data.lcvdec, can_bus_data.hcvdec, can_bus_data.sodec)
            if can_bus_data is not None :
                if can_bus_data.lcvdec < 2.7 and self.relayState.is_off():
                    self.batteryCellHealth.nok()
                    logging.info('starting balancing battery ', can_bus_data.lcvdec, can_bus_data.hcvdec)
                    self.relayState.on()
                if ( can_bus_data.hcvdec > 3.7 or can_bus_data.lcvdec > 3.2 ) and self.relayState.is_on():
                    logging.info('finished balancing battery ', can_bus_data.lcvdec, can_bus_data.hcvdec)
                    self.batteryCellHealth.ok()
                    self.relayState.off()
                time.sleep(30)
           
    def start(self):
        self.stop_thread = False;
        logging.info('starting battery balancer')
        self.thread = threading.Thread(target=self.balance_battery_pack,args=(lambda: self.stop_thread,));
        self.thread.start();

    def stop(self):
        logging.info('stopping battery balancer')
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

    def midnight(self):
        if self.batteryCellHealth.is_okay():
            message = self.canBusService.get_message()
            logging.info('checking pack voltage')
            if message.sodec < 50 and not self.weatherService.tomorrow_sunny() and self.relayState.is_off():
                logging.info('charging battery')
                self.relayState.on()
            if message.sodec >= 80 and self.relayState.is_on():
                logging.info('stopping charge')
                self.relayState.off()

        # start a new timer for tomorrow.
        logging.info('start new timer')
        self.start()

    def get_delta(self, datetime):
        x = datetime.today()
        y = x.replace(day=x.day, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        delta_t = y-x
        logging.info('next run at delta %s', delta_t.total_seconds())
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
    weatherService = WeatherServiceImpl
    print(weatherService.tomorrow_sunny())
    fmc = ForceMainsCharge(cbs, bs, bpc, rs, WeatherService, datetime)
    bb.start()
    fmc.start()
   # bb.stop()
   # fmc.stop()
    
