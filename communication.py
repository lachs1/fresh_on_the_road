from gsm import GSM
from tasks import TASK_TYPE

class Communication:
    def __init__(self):
        self.gsm = GSM()

        self.tasks = []

    def check_recieved_messages(self):
        messages = self.gsm.get_messages()
        self.gsm.delete_messages()
        # assumed messages list of following type dicts
        # {'number': 'xxxx', 'body': 'some text'}

        print('checking received messages. found:', len(messages))

        for msg in messages:
            num = msg.number
            body = msg.body

            if body.startswith('sensor'):
                task_params = {'number': num}
                print(num, 'sensor')
                task = {'type': TASK_TYPE.SEND_SENSOR_DATA, 'data': task_params}
                self.tasks.append(task)

            elif body.startswith('get alarms'):
                task_params = {'number': num}
                print(num, 'get alarms')
                task = {'type': TASK_TYPE.SEND_ALARM_STATE, 'data': task_params}
                self.tasks.append(task)

            elif body.startswith('state'):
                task_params = {'number': num}
                print(num, 'state')
                task = {'type': TASK_TYPE.SEND_LOGGER_STATE, 'data': task_params}
                self.tasks.append(task)

            elif body.startswith('get profiles'):
                task_params = {'number': num}
                print(num, 'get profiles')
                task = {'type': TASK_TYPE.SEND_PROFILES, 'data': task_params}
                self.tasks.append(task)

            elif body.startswith('set profile,'):
                task_params = {'number': num, 'profile': body[2:]}
                print(num, 'set profile')
                task = {'type': TASK_TYPE.SET_PROFILE, 'data': task_params}
                self.tasks.append(task)

            elif body.startswith('interval,'):
                task_params = {'number': num, 'interval': body[2:]}
                print(num, 'interval')
                task = {'type': TASK_TYPE.SET_LOGGING_INTERVAL, 'data': task_params}
                self.tasks.append(task)

            elif body.startswith('new logfile'):
                task_params = {'number': num}
                print(num, 'new logfile')
                task = {'type': TASK_TYPE.NEW_LOG_FILE, 'data': task_params}
                self.tasks.append(task)

            elif body.startswith('alarms,receive'):
                task_params = {'number': num}
                print(num, 'alarms')
                task = {'type': TASK_TYPE.SET_NUMBER, 'data': task_params}
                self.tasks.append(task)

            elif body.startswith('alarms,mute'):
                task_params = {'number': num}
                print(num, 'alarms')
                task = {'type': TASK_TYPE.REMOVE_NUMBER, 'data': task_params}
                self.tasks.append(task)

            elif body.startswith('help'):
                task_params = {'number': num}
                print(num, 'help')
                task = {'type': TASK_TYPE.HELP, 'data': task_params}
                self.tasks.append(task)

            elif body.startswith('restart'):
                task_params = {}
                print(num, 'restart')
                task = {'type': TASK_TYPE.RESTART, 'data': task_params}
                self.tasks.append(task)

            else:
                print(num, 'unknown command')
                self.send_message(num, 'Unknown command')



    def send_message(self, number, message):
        self.gsm.send_message(number, message)

    def get_tasks(self):
        ret = self.tasks.copy()
        self.tasks.clear()
        return ret
