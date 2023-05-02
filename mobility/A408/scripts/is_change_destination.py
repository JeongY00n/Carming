#!/usr/bin/env python

import redis
import os
import time

redis_client = redis.StrictRedis(host='j8a408.p.ssafy.io', port=6379, db=0, password='carming123')

# get the value of 'destination_coordinate' key
destination = redis_client.get('destination_coordinate')

while True:
    # get the value of 'destination_coordinate' key
    now_destination = redis_client.get('destination_coordinate')
    if now_destination != destination:
        redis_client.set('is_destination', 0)
        os.system("pkill -9 -ef Adaptive_Cruise_Control.launch")
        destination = now_destination
        os.system("roslaunch ssafy_2 Adaptive_Cruise_Control.launch")
    
    time.sleep(1)


