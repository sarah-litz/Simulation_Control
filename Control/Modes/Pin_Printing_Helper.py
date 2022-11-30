'''
unsure if we need this longterm. Not an experiment script, just writing a function so I can see pin values. 
'''
import time 
import RPi.GPIO as GPIO
from tabulate import tabulate



    

#
# Testing this for Lever1 Pin which has the following configurations in Configuration/lever.json: 
'''
    "lever1": 
    {
        "id":1,
        "hardware_specs": {
            "signalPin":19, 
            "numPresses":2, 
            "extended_angle":30, 
            "retracted_angle":105, 
            "pullup_pulldown":"pullup", 
            "servo_type":"positional"
        },  
        "threshold_condition": { "attribute": "pressed", "initial_value":0, "goal_value": 4 }
    }
'''


# Setup Pin 
GPIO.setmode(GPIO.BCM)
for channel in range(0,20): 
    GPIO.setup(channel, GPIO.IN, pull_up_down = GPIO.PUD_UP)

# Event Detection 
GPIO.add_event_detect(19, GPIO.RISING, bouncetime=200)
cont = False 
while not cont: 
    if GPIO.event_detected(19): 
        print("channel 19 event!")
        cont = True 


# Check value with .input method
while(True):

    try: 
        status = []
        for channel in range(0,20): 
            print("\033c", end="")
            status += [[channel, GPIO.input(channel)]] # pressed_val == 0 
        print(tabulate(status, headers = ['pin', 'status']))
        time.sleep(0.05)

    except KeyboardInterrupt:
        print('\n bye!')
        exit()