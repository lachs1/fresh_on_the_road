from datetime import datetime
import os
import configparser
from enum import Enum
import json

from si7021 import Si7021
from smbus import SMBus

from simulated_sensor import get_sensor_data
from tasks import TASK_TYPE


# folder structure:
'''
log_data/
    20221030_121212.txt
    20221130_131200.txt
    20221230_010922.txt

threshold_profiles/
    milk.ini
    fruits.ini

settings.ini (logging_interval, default threshold_profile)
'''


class ALARM_TYPE(Enum):
    LOW = 1
    HIGH = 2
    NORMAL = 3


class DataLogger:

    def __init__(self):
        # Get the sensor at I2C bus 1.
        self.sensor = Si7021(SMBus(1))

        # latest measured sensor data
        self.latest_values = {'temperature': 10000, 'humidity': 10000}
        # Largest and smallest sensor values during lifetime of the class
        self.extreme_values = {'temperature': [10000, -10000],
                               'humidity': [100, 0]}

        # Thershold values for alarm conditions
        # (min, max, hysteresis)
        self.thresholds = {'profile_name': None,
                           'temperature': (None, None, None),
                           'humidity': (None, None, None)}

        # Keeps track of alarms to prevent repeating the same alarm
        self.alarm_state = {'temperature': [False, False],
                            'humidity': [False, False]}

        # File for storing settings
        self.settings = configparser.ConfigParser()
        self.settings.read('settings.ini')
        self.use_threshold_profile(self.settings.get('DEFAULT',
                                                     'threshold_profile'))

        self.log_interval = self.settings.getint('DEFAULT', 'log_interval')

        self.alarm_numbers = json.loads(
            self.settings.get('DEFAULT', 'numbers'))

        # New log data file every time program run
        self.log_fpath = None
        self.create_log_file()

        self.tasks = []

    # Create new log file. For initializing and
    # when future data is wanted in a separate file
    def create_log_file(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fpath = os.path.join('./log_data', timestamp + '.txt')

        with open(fpath, 'w') as f:
            f.write('time\ttemperature\thumidity\n')
        self.log_fpath = fpath
        return timestamp

    # For collecting data and updating related variables
    def log_data(self):
        # get sensor data
        # temp, hum = get_sensor_data()  # Remove this later
        hum, temp = self.sensor.read()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # log data to file
        with open(self.log_fpath, 'a') as f:
            f.write(f'{timestamp}\t{round(temp,2)}\t{round(hum, 2)}\n')

        # update latest values
        self.latest_values['temperature'] = temp
        self.latest_values['humidity'] = hum

        # update extreme values
        temp_min = self.extreme_values['temperature'][0]
        temp_max = self.extreme_values['temperature'][1]
        hum_min = self.extreme_values['humidity'][0]
        hum_max = self.extreme_values['humidity'][1]
        if temp_min is None or temp < temp_min:
            self.extreme_values['temperature'][0] = temp
        if temp_min is None or temp > temp_max:
            self.extreme_values['temperature'][1] = temp
        if temp_min is None or hum < hum_min:
            self.extreme_values['humidity'][0] = hum
        if temp_min is None or hum > hum_max:
            self.extreme_values['humidity'][1] = hum

        # check threshold conditions and
        # set alarm if needed and same condition has not yet been alarmed

        # For temperature

        # (min, max, hysteresis)
        temp_th = self.thresholds['temperature']

        if temp < temp_th[0] and not self.alarm_state['temperature'][0]:
            self.send_alarm('temperature', ALARM_TYPE.LOW)
            self.alarm_state['temperature'][0] = True

        elif temp > temp_th[1] and not self.alarm_state['temperature'][1]:
            self.send_alarm('temperature', ALARM_TYPE.HIGH)
            self.alarm_state['temperature'][1] = True

        if temp > (temp_th[0] + temp_th[2]) and self.alarm_state['temperature'][0]:
            if not self.alarm_state['temperature'][1]:
                self.send_alarm('temperature', ALARM_TYPE.NORMAL)
            self.alarm_state['temperature'][0] = False

        elif temp < (temp_th[1] - temp_th[2]) and self.alarm_state['temperature'][1]:
            if not self.alarm_state['temperature'][0]:
                self.send_alarm('temperature', ALARM_TYPE.NORMAL)
            self.alarm_state['temperature'][1] = False

        # For humidity

        # (min, max, hysteresis)
        hum_th = self.thresholds['humidity']

        if hum < hum_th[0] and not self.alarm_state['humidity'][0]:
            self.send_alarm('humidity', ALARM_TYPE.LOW)
            self.alarm_state['humidity'][0] = True

        elif hum > hum_th[1] and not self.alarm_state['humidity'][1]:
            self.send_alarm('humidity', ALARM_TYPE.HIGH)
            self.alarm_state['humidity'][1] = True

        if hum > (hum_th[0] + hum_th[2]) and self.alarm_state['humidity'][0]:
            if not self.alarm_state['humidity'][1]:
                self.send_alarm('humidity', ALARM_TYPE.NORMAL)
            self.alarm_state['humidity'][0] = False

        elif hum < (hum_th[1] - hum_th[2]) and self.alarm_state['humidity'][1]:
            if not self.alarm_state['humidity'][0]:
                self.send_alarm('humidity', ALARM_TYPE.NORMAL)
            self.alarm_state['humidity'][1] = False

        # print logger state
        print('sensors:', self.latest_values)
        print()
        print(self.get_state())

    # For reading alarm thershold data by threshold profile name
    def read_threshold_profile(self, profile_name):
        profile = configparser.ConfigParser()
        profile.read(os.path.join(
            './threshold_profiles', profile_name + '.ini'))
        min_temp = profile.getint('TEMPERATURE', 'min')
        max_temp = profile.getint('TEMPERATURE', 'max')
        hyst_temp = profile.getint('TEMPERATURE', 'hysteresis')

        min_hum = profile.getint('HUMIDITY', 'min')
        max_hum = profile.getint('HUMIDITY', 'max')
        hyst_hum = profile.getint('HUMIDITY', 'hysteresis')

        return {'profile_name': profile_name,
                'temperature': (min_temp, max_temp, hyst_temp),
                'humidity': (min_hum, max_hum, hyst_hum)}

    def update_setting_file(self):
        try:
            with open('settings.ini', 'w') as configfile:
                self.settings.write(configfile)
            return True

        except Exception:
            return False

    # Start using alarm threhold data of defined profile name and
    # save the profile name to settings to use same profile at next run
    def use_threshold_profile(self, profile_name):
        try:
            self.thresholds = self.read_threshold_profile(profile_name)
        except Exception:
            raise ValueError(
                f'Reading threshold profile failed: {profile_name}')

        self.settings['DEFAULT']['threshold_profile'] = profile_name
        self.update_setting_file()

    # Set log interval to settings. The interval will be applied at next run
    def set_log_interval(self, interval):
        if not isinstance(interval, int) or interval <= 0:
            return False

        self.settings['DEFAULT']['log_interval'] = str(interval)
        self.update_setting_file()
        return True

    def add_number(self, number):
        if number not in self.alarm_numbers:
            self.alarm_numbers.append(number)

            self.settings['DEFAULT']['numbers'] = json.dumps(
                self.alarm_numbers)
            self.update_setting_file()

    def remove_number(self, number):
        try:
            self.alarm_numbers.remove(number)
            self.settings['DEFAULT']['numbers'] = json.dumps(
                self.alarm_numbers)
            self.update_setting_file()
            return True
        except ValueError:
            return False

    # Get list of existing alarm threhold profile files
    def get_threshold_profiles(self):
        return [fn.rsplit('.', 1)[0] for fn in os.listdir('./threshold_profiles')]

    def get_extreme_values(self):
        return self.extreme_values

    def get_values(self):
        return self.latest_values

    def get_log_interval(self):
        return self.log_interval

    def get_thresholds(self):
        return self.thresholds

    # if ignore_hysteresis: alarms will be disabled if they are depending on hysteresis
    def get_alarms(self, ignore_hysteresis=False):
        if ignore_hysteresis:
            temp = self.latest_values['temperature']
            if temp > self.thresholds['temperature'][0] and self.alarm_state['temperature'][0]:
                self.send_alarm('temperature', ALARM_TYPE.NORMAL)
                self.alarm_state['temperature'][0] = False
            elif temp < self.thresholds['temperature'][1] and self.alarm_state['temperature'][1]:
                self.send_alarm('temperature', ALARM_TYPE.NORMAL)
                self.alarm_state['temperature'][1] = False

            hum = self.latest_values['humidity']
            if hum > self.thresholds['humidity'][0] and self.alarm_state['humidity'][0]:
                self.send_alarm('humidity', ALARM_TYPE.NORMAL)
                self.alarm_state['humidity'][0] = False
            elif hum < self.thresholds['humidity'][1] and self.alarm_state['humidity'][1]:
                self.send_alarm('humidity', ALARM_TYPE.NORMAL)
                self.alarm_state['humidity'][1] = False

        return self.alarm_state

    # variable: 'temperature' or 'humidity'
    # type: ALARM_TYPE.LOW or ALARM_TYPE.HIGH or ALARM_TYPE.NORMAL
    def send_alarm(self, variable, type):
        task_params = {'numbers': self.alarm_numbers,
                       'variable': variable,
                       'type': type}
        task = {'type': TASK_TYPE.SEND_ALARM, 'data': task_params}
        self.tasks.append(task)

    def get_state(self):
        profile_name = self.thresholds['profile_name']
        min_temp = self.thresholds['temperature'][0]
        max_temp = self.thresholds['temperature'][1]
        min_hum = self.thresholds['humidity'][0]
        max_hum = self.thresholds['humidity'][1]

        log_interval = self.get_log_interval()

        num_str = ''
        for num in self.alarm_numbers:
            num_str += num + '\n'

        alarm_str = 'Alarms:\n'
        alarms = self.get_alarms()
        if alarms['temperature'][0]:
            alarm_str += 'Low temperature\n'
        elif alarms['temperature'][1]:
            alarm_str += 'High temperature\n'

        if alarms['humidity'][0]:
            alarm_str += 'Low humidity\n'
        elif alarms['humidity'][1]:
            alarm_str += 'High humidity\n'

        ret = f'Logger state:\n' \
              f'\n' \
              f'Threshold profile:\n' \
              f'name: {profile_name}\n' \
              f'Temp range: {min_temp} - {max_temp}\n' \
              f'Hum range: {min_hum} - {max_hum}\n' \
              f'\n' \
              f'logging interval: {log_interval} min\n' \
              f'\n' \
              f'Alarm numbers:\n' \
              f'{num_str}' \
              f'\n' \
              f'{alarm_str}\n'

        return ret

    def get_tasks(self):
        # clear and return self.tasks
        ret = self.tasks.copy()
        self.tasks.clear()
        return ret
