import schedule
import time
import os
import sys

from tasks import TASK_TYPE
from data_logger import ALARM_TYPE
from data_logger import DataLogger
from communication import Communication


def restart():
    os.execl(sys.executable, sys.executable, *sys.argv)

if __name__ == '__main__':

    logger = DataLogger()
    communication = Communication()

    # Scheduling for sensor data logging
    log_interval = logger.get_log_interval()
    schedule.every(log_interval).minutes.at(':00').do(logger.log_data)
    # schedule.every(10).seconds.do(logger.log_data)

    # New log data file when new day starts
    schedule.every().day.at('00:00').do(logger.create_log_file)

    print(logger.get_state())

    while True:
        # Check scheduled tasks
        schedule.run_pending()

        communication.check_recieved_messages()

        # get tasks from DataLogger and communication classes
        tasks = logger.get_tasks() + communication.get_tasks()

        # handling tasks
        for task in tasks:
            task_params = task['data']

            if task['type'] == TASK_TYPE.SEND_SENSOR_DATA:
                target_number = task_params['number']

                latest_values = logger.get_values()
                temp = round(latest_values['temperature'], 2)
                hum = round(latest_values['humidity'], 2)

                ext_v = logger.get_extreme_values()
                ext_temp_l = round(ext_v['temperature'][0], 2)
                ext_temp_h = round(ext_v['temperature'][1], 2)
                ext_hum_l = round(ext_v['humidity'][0], 2)
                ext_hum_h = round(ext_v['humidity'][1], 2)

                msg = f'Latest:\n' \
                      f'Temp: {temp} C\n' \
                      f'Hum: {hum} RH\n' \
                      f'\n' \
                      f'Extreme:\n' \
                      f'temp: {ext_temp_l} - {ext_temp_h}\n' \
                      f'hum: {ext_hum_l} - {ext_hum_h}\n' \


                communication.send_message(target_number, msg)
                print('sending:')
                print(msg)

            elif task['type'] == TASK_TYPE.SEND_ALARM_STATE:
                target_number = task_params['number']

                msg = 'Alarms:\n'
                alarms = logger.get_alarms()
                if alarms['temperature'][0]:
                    msg += 'Low temperature\n'
                elif alarms['temperature'][1]:
                    msg += 'High temperature\n'

                if alarms['humidity'][0]:
                    msg += 'Low humidity\n'
                elif alarms['humidity'][1]:
                    msg += 'High humidity\n'

                communication.send_message(target_number, msg)
                print(msg)


            elif task['type'] == TASK_TYPE.SEND_LOGGER_STATE:
                target_number = task_params['number']

                thresholds = logger.get_thresholds()
                profile_name = thresholds['profile_name']
                min_temp = thresholds['temperature'][0]
                max_temp = thresholds['temperature'][1]
                min_hum = thresholds['humidity'][0]
                max_hum = thresholds['humidity'][1]

                log_interval = logger.get_log_interval()

                num_str = ''
                for num in logger.alarm_numbers:
                    num_str += num + '\n'

                msg = f'Profile:\n' \
                      f'{profile_name}\n' \
                      f'Temp range: {min_temp} - {max_temp}\n' \
                      f'Hum range: {min_hum} - {max_hum}\n' \
                      f'\n' \
                      f'log interval: {log_interval} min\n' \
                      f'\n' \
                      f'Alarm receivers:\n' \
                      f'{num_str}' \

                communication.send_message(target_number, msg)
                print(msg)

            elif task['type'] == TASK_TYPE.SEND_PROFILES:
                target_number = task_params['number']

                msg = 'Existing threshold profiles: \n'
                for profile in logger.get_threshold_profiles():
                    print(profile)
                    msg += profile + '\n'

                communication.send_message(target_number, msg)
                print(msg)

            elif task['type'] == TASK_TYPE.SET_PROFILE:
                target_number = task_params['number']
                profile = task_params['profile']
                ret = None
                try:
                    logger.use_threshold_profile(profile)
                    ret = True
                except ValueError:
                    ret = False

                if ret:
                    msg = f'Used profile changed to {profile}'
                else:
                    msg = 'Changing profile failed'

                communication.send_message(target_number, msg)
                print(msg)

            elif task['type'] == TASK_TYPE.SET_LOGGING_INTERVAL:
                target_number = task_params['number']
                interval = task_params['interval']

                ret = logger.set_log_interval(interval)

                if ret:
                    msg = f'Logging interval changed to {interval}.\n' \
                          f'New interval will be applied after restart'
                else:
                    msg = 'Changing logging interval failed'

                communication.send_message(target_number, msg)
                print(msg)

            elif task['type'] == TASK_TYPE.NEW_LOG_FILE:
                target_number = task_params['number']
                timestamp = logger.create_log_file()

                msg = f'Created new log file with timestamp {timestamp}'

                communication.send_message(target_number, msg)
                print(msg)

            elif task['type'] == TASK_TYPE.SET_NUMBER:
                target_number = task_params['number']
                logger.add_number(target_number)
                msg = f'Number {target_number} is added to alarm number list'

                communication.send_message(target_number, msg)
                print(msg)

            elif task['type'] == TASK_TYPE.REMOVE_NUMBER:
                target_number = task_params['number']

                ret = logger.remove_number(target_number)
                if ret:
                    msg = f'Number {target_number} is removed from alarm number list'
                else:
                    msg = f'Number {target_number} was not found in the alarm number list'

                communication.send_message(target_number, msg)
                print(msg)

            elif task['type'] == TASK_TYPE.HELP:
                target_number = task_params['number']

                with open('help.txt', 'r') as help_file:
                    msg = help_file.read()

                communication.send_message(target_number, msg)
                print(msg)

            elif task['type'] == TASK_TYPE.RESTART:
                restart()




            elif task['type'] == TASK_TYPE.SEND_ALARM:
                target_numbers = task_params['numbers']
                variable = task_params['variable']
                type = task_params['type']

                if type == ALARM_TYPE.LOW:
                    msg = 'ALARM!:\n' \
                          f'Low {variable}'

                elif type == ALARM_TYPE.HIGH:
                    msg = 'ALARM!:\n' \
                          f'High {variable}'

                elif type == ALARM_TYPE.NORMAL:
                    msg = f'{variable} back in the normal range'

                for num in target_numbers:
                    communication.send_message(num, msg)
                print(msg)




        #time.sleep(30)
