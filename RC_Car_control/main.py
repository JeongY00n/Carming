import time
import os
import sys
import socket
import RPi.GPIO as GPIO
from Door_ServoMotor import openclose
from DC_motor import DC_MOTOR
from servo_motor import SERVO_MOTOR
import redis
import re
import tts
import serial

ser = serial.Serial('/dev/ttyACM0', 9600, exclusive=True)
## ls /dev/ttyA* 명령 입력해서 연결된 포트 확인하기
## 통신 중에 프로그램이 종료될 경우, ACM뒤의 포트 번호가 계속 올라간다.

class main():
    def __init__(self):
        # DC_MOTOR 객체 생성
        self.dc_motor = DC_MOTOR(enable, input_1, input_2)
        self.servo_motor = SERVO_MOTOR(servo_pin)

    ## redis에서 데이터 확인
    def run(self):
        
        redis_client = redis.StrictRedis(host='j8a408.p.ssafy.io', port=6379, db=0, password='carming123')
        
        try:
            start_flag = 0
            
            while True:
                
                ## 속도 b'1.4650933742523193' 형태로 출력
                current_velocity = redis_client.get('current_velocity')
                speed = re.findall(b'\d+', current_velocity)[0]  ### 정규식으로 바이트 문자열에서 숫자만 추출
                speed = 10 * int(speed)  ## 모터의 출력율로 변환 (대충 20이하의 값이 나오므로 5배 처리)
                
                if speed >= 100:
                    speed = 100
                    
                self.dc_motor.drive(speed)  # DC_MOTOR 객체의 drive 함수 호출

                wheel_angle = redis_client.get('wheel_angle')
                wheel_angle = float(wheel_angle.decode())

                print('v : ' , current_velocity)
                ## 왼쪽 -
                ## 오른쪽 +
                ## 직진 0
                if wheel_angle <= -2:  ## left
                    num = 2
                    ser.write(num.to_bytes(1, 'little'))
                    time.sleep(0.1)
                    self.servo_motor.steering(-2)
                    time.sleep(0.3)

                elif wheel_angle >= 2:  ## right
                    num = 3
                    ser.write(num.to_bytes(1, 'little'))
                    time.sleep(0.1)
                    self.servo_motor.steering(2)
                    time.sleep(0.3)

                elif wheel_angle <= -1 and wheel_angle > -2:  ## semi left
                    num = 2
                    ser.write(num.to_bytes(1, 'little'))
                    time.sleep(0.1)
                    self.servo_motor.steering(-1)
                    time.sleep(0.3)

                elif wheel_angle >= 1 and wheel_angle < 2:  ## semi right
                    num = 3
                    ser.write(num.to_bytes(1, 'little'))
                    time.sleep(0.1)
                    self.servo_motor.steering(1)
                    time.sleep(0.3)

                else:
                    num = 1
                    ser.write(num.to_bytes(1, 'little'))
                    time.sleep(0.1)
                    self.servo_motor.steering(0)
                    time.sleep(0.3)

            
                
                time.sleep(2)
                get_in = redis_client.get('get_in')
                get_off = redis_client.get('get_off')
                is_destination = redis_client.get('is_destination')
                #print('get_in : ', get_in)
                #print('is_destination : ', is_destination)
                
                ## 차량이 사용자의 위치로 도착, 승차하기 전
                ## 승차한 후 is_destination = 0, get_in = 1
                if is_destination == b'1'  and get_in == b'0' and start_flag == 0:
                    self.dc_motor.drive(0.0)
                    self.servo_motor.steering(0)
                    time.sleep(1)
                    tts.synthesize_text("안녕하세요! 카밍카 입니다! 승차해 주세요!")
                    # 3초 뒤에 문열림
                    openclose()
                    while True:
                        num = 4
                        ser.write(num.to_bytes(1, 'little'))
                        time.sleep(1)
                        get_in = redis_client.get('get_in')
                        if get_in == b'1':
                            print("get_in")
                            tts.synthesize_text("안전벨트를 매주세요!... 출발하겠습니다~")
                            break
                    redis_client.set('is_destination', 0)
                    start_flag = 1


                
                ## 사용자가 탑승한 차량이 목적지에 도착한 경우
                elif get_in == b'1' and is_destination == b'1' and start_flag == 1:
                    self.dc_motor.drive(0.0)
                    self.servo_motor.steering(0)
                    time.sleep(1)
                    tts.synthesize_text("목적지에 도착하였습니다. 하차 준비를 하세요~")
                    # 3초 뒤에 문열림
                    openclose()
                    while True:
                        num = 4
                        ser.write(num.to_bytes(1, 'little'))
                        time.sleep(1)
                        get_off = redis_client.get('get_off')
                        if get_off == b'1':
                            break
                    start_flag = 0
                            
                ## 조향 자체가 어떻게 찍히는 지 확인해서 dutycycle 변수 입력
                ##SERVO_MOTOR.steering(dutycycle)

        except KeyboardInterrupt:
            GPIO.cleanup()



if __name__ == "__main__":

    ## dc모터 핀 번호
    input_1 = 23
    input_2 = 24
    enable = 27

    ## servo모터 핀 번호
    servo_pin = 17

    main = main()
    main.run()


