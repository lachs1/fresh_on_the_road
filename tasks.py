from enum import Enum

class TASK_TYPE(Enum):
    # Communication

    # number
    SEND_SENSOR_DATA = 1

    # number
    SEND_ALARM_STATE = 2

    # number
    SEND_LOGGER_STATE = 3

    # number
    SEND_PROFILES = 4

    # number, profile
    SET_PROFILE = 5

    # number, interval
    SET_LOGGING_INTERVAL = 6

    # number
    NEW_LOG_FILE = 7

    # number
    SET_NUMBER = 8

    # number
    REMOVE_NUMBER = 9

    # number
    HELP = 10

    # _
    RESTART = 11


    # DataLogger

    # numbers, variable, type
    SEND_ALARM = 12
