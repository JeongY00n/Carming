#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import rospkg
from math import cos,sin,pi,sqrt,pow
from geometry_msgs.msg import Point32,PoseStamped
from nav_msgs.msg import Odometry,Path

# local_path_pub 은 global Path (전역경로) 데이터를 받아 Local Path (지역경로) 를 만드는 예제입니다.
# Local Path (지역경로) 는 global Path(전역경로) 에서 차량과 가장 가까운 포인트를 시작으로 만들어 집니다.

# 노드 실행 순서 
# 1. Global Path 와 Odometry 데이터 subscriber 생성 
# 2. Local Path publisher 선언
# 3. Local Path 의 Size 결정
# 4. 콜백함수에서 처음 메시지가 들어오면 초기 위치를 저장
# 5. Global Path 에서 차량 위치와 가장 가까운 포인트(Currenty Waypoint) 탐색
# 6. 가장 가까운 포인트(Currenty Waypoint) 위치부터 Local Path 생성 및 예외 처리 
# 7. Local Path 메세지 Publish


class local_path_pub :
    def __init__(self):
        rospy.init_node('local_path_pub', anonymous=True)
        #TODO: (1) Global Path 와 Odometry 데이터 subscriber 생성 
        
        # Global Path 와 Odometry 데이터 subscriber 를 생성한다.
        # 콜백 함수의 이름은 self.global_path_callback, self.odom_callback 로 한다.
        rospy.Subscriber('/odom', Odometry, self.global_path_callback)
        rospy.Subscriber('/global_path', Path, self.odom_callback)
        
        #TODO: (2) Local Path publisher 선언
        # local Path 데이터를 Publish 하는 변수를 선언한다.
        self.local_path_pub = rospy.Publisher('/local_path',Path, queue_size=1)

                
        # 초기화
        self.is_odom = False
        self.is_path = False

        #TODO: (3) Local Path 의 Size 결정
        
        # Local Path 의 크기를 지정한다.
        # 차량이 주행 시 Local Path 의 크기 만큼의 정보를 가지고 주행하게 된다
        # 너무 작지도 크기지도 않은 값을 사용한다 (50 ~ 200)
        self.local_path_size = 100

        
        rate = rospy.Rate(20) # 20hz
        while not rospy.is_shutdown():
   
            if self.is_odom == True and self.is_path == True:
                local_path_msg=Path()
                local_path_msg.header.frame_id='/map'
                
                x=self.x
                y=self.y

                #TODO: (5) Global Path 에서 차량 위치와 가장 가까운 포인트(current Waypoint) 탐색
                
                # global Path 에서 차량의 현재 위치를 찾습니다.
                # 현재 위치는 WayPoint 로 기록하며 현재 차량이 Path 에서 몇번 째 위치에 있는지 나타내는 값이 됩니다.
                # 차량의 현재 위치는 Local Path 를 만드는 시작 위치가 됩니다.
                # 차량의 현재 위치를 탐색하는 반복문은 작성해 current_waypoint 찾습니다.
                min_dis = float('inf')  # 최소값 infinte로 초기화
                current_waypoint = -1   # 가장 가까운 waypoint의 idx 초기화

                # 거리를 계산해서 최솟값이 되는 waypoint의 idx를 찾자. mid_dis갱신
                # enumerate() 인자로 넘어온 목록을 기준으로 인덱스와 원소를 차례대로 접근하게 해주는 반복자 객체 반환 함수
                for idx, pose in enumerate(self.global_path_msg.poses):
                    dx = pose.pose.position.x - x
                    dy = pose.pose.position.y - y
                    dist = sqrt(pow(dx,2)+ pow(dy,2))

                    if dist < min_dis:
                        min_dis = dist
                        current_waypoint = idx
                
                
                #TODO: (6) 가장 가까운 포인트(current Waypoint) 위치부터 Local Path 생성 및 예외 처리
                
                # 차량의 현재 위치 부터 local_path_size 로 지정한 Path 의 크기 만큼의 Path local_path 를 생성합니다.
                if current_waypoint != -1 :

                    # 차량에 남은 Path 의 길이가 local_path_size 보다 작은 경우
                    if current_waypoint + self.local_path_size < len(self.global_path_msg.poses):

                        # 현재 차량의 위치부터 지정한 local_path큐의 사이즈만큼 
                        for idx in range(current_waypoint, current_waypoint + self.local_path_size):
                            
                            read_pose = PoseStamped()  # 좌표를 담을 객체 생성
                            
                            # 앞에서 확인한 가장 가까운 좌표의 x, y값 저장
                            read_pose.pose.position.x = float(self.global_path_msg.poses[idx].pose.position.x)
                            read_pose.pose.position.y = float(self.global_path_msg.poses[idx].pose.position.y)
                            read_pose.pose.position.z = 1
                            local_path_msg.poses.append(read_pose)
                    else :

                

                print(x,y)
                #TODO: (7) Local Path 메세지 Publish
                '''
                # Local Path 메세지 를 전송하는 publisher 를 만든다.
                self.local_path_pub.
                
                '''

            rate.sleep()

    def odom_callback(self,msg):
        self.is_odom = True
        #TODO: (4) 콜백함수에서 처음 메시지가 들어오면 초기 위치를 저장

        '''
        # gpsimu_parser.py 예제에서 Publish 해주는 Odometry 메세지 데이터를 Subscrib 한다.
        # Odometry 메세지 에 담긴 물체의 위치 데이터를 아래 변수에 넣어준다.
        self.x = 물체의 x 좌표 
        self.y = 물체의 y 좌표

        '''

    def global_path_callback(self,msg):
        self.is_path = True
        self.global_path_msg = msg        

if __name__ == '__main__':
    try:
        test_track=local_path_pub()
    except rospy.ROSInterruptException:
        pass
