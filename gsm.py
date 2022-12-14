import time
from dataclasses import dataclass

import serial


"""
GSM Python module for sending/reading/deleting SMS messages.

Reference: https://www.waveshare.com/wiki/SIM800C_GSM/GPRS_HAT

Usage: 

Sending messages:

    gsm = GSM()
    gsm.send_message(to='<NUMBER>', message='')

Reading messages:

    gsm = GSM()
    messages = gsm.get_messages()
    for message in messages:
        print(message.number, message.body)

Deleting messages:

    gsm = GSM()
    gsm.delete_messages()


"""


@dataclass
class SMS:
    number: str
    mid: str = ''  # Message ID
    date: str = ''
    status: str = ''
    mtime: str = ''  # Message time
    body: str = ''


class GSM:
    def __init__(self):
        self.ser = serial.Serial("/dev/ttyS0", 115200)
        self.ser.flushInput()

    def delete_messages(self):
        """
        Deletes all messages stored on the GSM module.
        """
        self.ser.write('AT\n'.encode())
        time.sleep(1)
        self.ser.write('AT+CMGD=1,4\n'.encode())
        time.sleep(1)
        self.ser.write('AT+CMGL=\"ALL\"\n'.encode())
        time.sleep(1)
        self.ser.flushInput()
        time.sleep(1)

    def send_message(self, to, message):
        """
        Sends a message to the phone number 'to'.

        If the message is longer than 153 characters
        the message will be split and sent as separate messages.

        Note: takes about 5 seconds to send one message.

        """
        self.ser.write('AT\n'.encode())
        time.sleep(1)
        self.ser.write('AT+CMGF=1\n'.encode())
        time.sleep(1)
        self.ser.write(f'AT+CMGS=\"{to}\"\n'.encode())
        time.sleep(1)
        self.ser.write(message.encode())
        time.sleep(1)
        self.ser.write(b"\x1a\n")  # Send
        time.sleep(5)
        self.ser.flushInput()
        time.sleep(1)

    def get_messages(self):
        """
        Returns a list of available SMS messages.
        """

        self.ser.flushInput()
        time.sleep(1)
        self.ser.write('AT\n'.encode())
        time.sleep(1)
        sms_list = []
        try:
            self.ser.write('AT+CMGL=\"ALL\"\n'.encode())
            time.sleep(2)
            data = self.ser.read(self.ser.inWaiting()).decode()

            time.sleep(2)
            # String operations
            _, messages = data.split('AT+CMGL="ALL"')
            messages = messages.replace('\n', '')
            messages = messages.replace('\r', '')
            messages = messages[:-2]  # Remove OK from the end
            messages = messages.split('+CMGL: ')

            for message in messages:
                if not message:
                    continue
                # More string operations...
                parts = message.split(',')
                idx = int(parts[0])
                status = parts[1].replace('"', '')
                sender = parts[2].replace('"', '')
                date = parts[4].replace('"', '')
                mtime = parts[5].split('"')[0]
                body = message.split(',', 1)[1]
                _, body = body.rsplit('"', 1)

                sms = SMS(mid=idx, status=status, number=sender,
                          date=date, mtime=mtime, body=body)
                sms_list.append(sms)
            return sms_list
        except (IndexError, ValueError, UnicodeDecodeError):
            print(data)
            return sms_list


if __name__ == '__main__':

    gsm = GSM()
    gsm.send_message(to='<NUMBER>', message='Temperature too high')
    messages = gsm.get_messages()
    for message in messages:
        print(message)
