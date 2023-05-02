import RPi.GPIO as GPIO
import time
import redis

redis_client = redis.Redis(host='j8a408.p.ssafy.io', port=6379, db=0, password='carming123')


def openclose():
    GPIO.setwarnings(False)

    # GPIO 핀 모드 설정
    GPIO.setmode(GPIO.BCM)

    # GPIO 핀 번호 지정
    PWM_PIN = 22

    # PWM 주파수 설정
    PWM_FREQ = 50

    # 모터 출력
    GPIO.setup(PWM_PIN, GPIO.OUT)

    # PWM 신호 생성
    pwm = GPIO.PWM(PWM_PIN, PWM_FREQ)

    # PWM 신호 출력 시작
    pwm.start(0)

    # duty cycle 변경 함수
    def set_duty_cycle(duty_cycle):
        pwm.ChangeDutyCycle(duty_cycle)

    try:
        # 0도에서 95도로 3초간 문 열림
        for angle in range(0, 96, 1):
            # 각도를 duty cycle로 변환하여 PWM 출력, 일정한 속도로 동작
            duty_cycle = 2.5 + (angle / 18.0)
            set_duty_cycle(duty_cycle)
            time.sleep(0.03)

        # 승객이 하차, 승차 함을 확인 후
        while True:
            get_off = redis_client.get('get_off')
            get_in = redis_client.get('get_in')
            if get_off == b'1' or get_in == b'1':

                # 95도에서 0도로 3초간 문 닫힘
                for angle in range(96, 0, -1):
                    # 각도를 duty cycle로 변환하여 PWM 출력, 일정한 속도로 동작
                    duty_cycle = 2.5 + (angle / 18.0)
                    set_duty_cycle(duty_cycle)
                    time.sleep(0.03)
                break;

    except KeyboardInterrupt:
        pass

    # PWM 신호 출력 종료
    pwm.stop()

    # GPIO 모드 초기화
    GPIO.cleanup()

