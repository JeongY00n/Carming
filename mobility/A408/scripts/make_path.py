#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import rospkg
import sys
import os
import copy
import numpy as np
import json ## 문자열을 dictionary로 변환할 때 사용

from math import cos, sin, sqrt, pow, atan2, pi
from geometry_msgs.msg import Point32, PoseStamped, PoseWithCovarianceStamped
from nav_msgs.msg import Odometry, Path
from morai_msgs.msg import GPSMessage
#좌표변환에 사용될 모듈
import pyproj
from pyproj import Proj
# 레디스 client실행
import redis

redis_client = redis.Redis(host='j8a408.p.ssafy.io', port=6379, db=0, password='carming123')

# 파일의 상대 경로 출력
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)

from lib.mgeo.class_defs import *


# 노드 실행 순서
# 0. 필수 학습 지식
# 1. Mgeo data 읽어온 후 데이터 확인
# 2. 시작 Node 와 종료 Node 정의
# 3. weight 값 계산
# 4. Dijkstra Path 초기화 로직
# 5. Dijkstra 핵심 코드
# 6. node path 생성
# 7. link path 생성
# 8. Result 판별
# 9. point path 생성
# 10. dijkstra 경로 데이터를 ROS Path 메세지 형식에 맞춰 정의
# 11. dijkstra 이용해 만든 Global Path 정보 Publish



class dijkstra_path_pub:
    def __init__(self):
        rospy.init_node('dijkstra_path_pub', anonymous=True)

        self.gps_sub = rospy.Subscriber("/gps", GPSMessage, self.navsat_callback)
        self.global_path_pub = rospy.Publisher('/global_path', Path, queue_size=1)
        self.proj_UTM = Proj(proj='utm', zone=52, ellps='WGS84', preserve_units=False)


        ## Mgeo data 읽어온 후 데이터 확인
        load_path = os.path.normpath(os.path.join(current_path, 'lib/mgeo_data/R_KR_PG_K-City'))
        mgeo_planner_map = MGeo.create_instance_from_json(load_path)

        node_set = mgeo_planner_map.node_set
        link_set = mgeo_planner_map.link_set

        self.nodes = node_set.nodes
        self.links = link_set.lines

        self.global_planner = Dijkstra(self.nodes, self.links)

        self.is_goal_pose = False
        self.is_init_pose = False

        ## 탑승자의 위치 정보 가져오기
        call_coordinate = redis_client.get('call_coordinate')
        call_coordinate = eval(call_coordinate)
        self.init_state(call_coordinate)
        print(call_coordinate)
        
        ## ---------------------

        ## redis에서 목적지 정보 가져오기
        destination_coordinate = redis_client.get('destination_coordinate')
        destination_coordinate = json.loads(destination_coordinate)
        self.goal_state(destination_coordinate)


        
        while True:
            if self.is_goal_pose == True and self.is_init_pose == True:
                break
            else:
                rospy.loginfo('Waiting goal pose data')
                rospy.loginfo('Waiting init pose data')

        self.global_path_msg = Path()
        self.global_path_msg.header.frame_id = '/map'

        self.lat = 0
        self.lon = 0
        self.x = 0
        self.y = 0
        self.get_global_path=[]

        self.global_path_msg = self.calc_dijkstra_path_node(self.start_node, self.end_node)

        rate = rospy.Rate(10)  # 10hz

        '''
        위도(lat) : -90 ~ 90
        경도(lon) : -180 ~ 180
        '''

        self.utm_x=0
        self.utm_y=0

        while not rospy.is_shutdown():
            # TODO: (11) dijkstra 이용해 만든 Global Path 정보 Publish
            # global_path_msg에서 받은 pose들 중 현재 위치에서 가장 가까운 좌표를 찾아서 min_dist와 waypoint에 저장

            self.global_path_pub.publish(self.global_path_msg)
            rate.sleep()

        ## redis에 생성된 경로에 대한 위도, 경도 저장
        redis_client.set('global_path', str(self.get_global_path))


    def navsat_callback(self, gps_msg):
        self.lat = gps_msg.latitude
        self.lon = gps_msg.longitude
        self.e_o = gps_msg.eastOffset
        self.n_o = gps_msg.northOffset

        self.is_gps=True

    ## 탑승 위치에서 가까운 노드 확인
    def init_state(self, start_gps):

        xy_zone = self.proj_UTM(start_gps['lon'], start_gps['lat'])

        #xy_zone = self.proj_UTM(126.7734230193396, 37.23963047324451)

        x = xy_zone[0]-self.e_o
        y = xy_zone[1]-self.n_o


        min_dis = float('inf')
        node_id = -1
        # print((msg.pose.pose.position))

        for from_node_id, from_node in list(self.nodes.items()):
            dx = from_node.point[0] - x
            dy = from_node.point[1] - y
            dist = sqrt(dx * dx + dy * dy)

            if dist < min_dis:
                min_dis = dist
                node_id = from_node_id

        self.start_node = node_id
        self.is_init_pose = True


    ## 목적지에서 가까운 노드 확인
    def goal_state(self, end_gps):
        
        xy_zone = self.proj_UTM(end_gps['lon'], end_gps['lat'])
        # xy_zone = self.proj_UTM(126.77451868834234, 37.241549847536525)

        x = xy_zone[0]-self.e_o
        y = xy_zone[1]-self.n_o

        min_dis = float('inf')
        node_id = -1

        for from_node_id, from_node in list(self.nodes.items()):
            dx = from_node.point[0] - x
            dy = from_node.point[1] - y
            dist = sqrt(dx * dx + dy * dy)

            if dist < min_dis:
                min_dis = dist
                node_id = from_node_id

        self.end_node = node_id
        self.is_goal_pose = True

    def calc_dijkstra_path_node(self, start_node, end_node):

        result, path = self.global_planner.find_shortest_path(start_node, end_node)

        # TODO: (10) dijkstra 경로 데이터를 ROS Path 메세지 형식에 맞춰 정의
        out_path = Path()
        out_path.header.frame_id = '/map'

        # 아래에서 반환된 point_path key정보를 pose 객체에 저장, w값은 그냥 null값으로 저장해도 됨
        if result:
            for point in path['point_path']:
                read_pose = PoseStamped()
                read_pose.pose.position.x = point[0]
                read_pose.pose.position.y = point[1]
                read_pose.pose.orientation.w = 1
                out_path.poses.append(read_pose)

            ## 생성된 node경로 좌표들을 gps 좌표로 변환
            for path_node in path['node_path']:
                for id, node in list(self.nodes.items()):
                    if id == path_node:
                        utm_x = node.point[0] + self.e_o
                        utm_y = node.point[1] + self.n_o

                        ## 변환된 utm좌표를 gps로 변환
                        ## 좌표 변환
                        self.proj_UTM = Proj(proj='utm', zone=52, ellps='WGS84', preserve_units=False)
                        lon, lat = self.proj_UTM(utm_x, utm_y, inverse=True)               
    
                        dic = {}
                        dic['lat'] = lat
                        dic['lon'] = lon

                        ## 리스트에 딕셔너리 추가
                        self.get_global_path.append(dic)
                        break
            
        return out_path


class Dijkstra:
    def __init__(self, nodes, links):
        self.nodes = nodes
        self.links = links
        self.weight = self.get_weight_matrix()
        self.lane_change_link_idx = []

    def get_weight_matrix(self):
        # TODO: (3) weight 값 계산

        # 초기 설정
        weight = dict()
        for from_node_id, from_node in list(self.nodes.items()):
            # 현재 노드에서 다른 노드로 진행하는 모든 weight
            weight_from_this_node = dict()
            for to_node_id, to_node in list(self.nodes.items()):
                weight_from_this_node[to_node_id] = float('inf')
            # 전체 weight matrix에 추가
            weight[from_node_id] = weight_from_this_node

        for from_node_id, from_node in list(self.nodes.items()):
            # 현재 노드에서 현재 노드로는 cost = 0
            weight[from_node_id][from_node_id] = 0

            for to_node in from_node.get_to_nodes():
                # 현재 노드에서 to_node로 연결되어 있는 링크를 찾고, 그 중에서 가장 빠른 링크를 찾아준다
                shortest_link, min_cost = self.find_shortest_link_leading_to_node(from_node, to_node)
                weight[from_node_id][to_node.idx] = min_cost

        return weight

    def find_shortest_link_leading_to_node(self, from_node, to_node):
        """현재 노드에서 to_node로 연결되어 있는 링크를 찾고, 그 중에서 가장 빠른 링크를 찾아준다"""
        # TODO: (3) weight 값 계산

        shortest_link, min_cost = from_node.find_shortest_link_leading_to_node(to_node)
        return shortest_link, min_cost

    def find_nearest_node_idx(self, distance, s):
        idx_list = list(self.nodes.keys())
        min_value = float('inf')
        min_idx = idx_list[-1]

        for idx in idx_list:
            if distance[idx] < min_value and s[idx] == False:
                min_value = distance[idx]
                min_idx = idx
        return min_idx

    def find_shortest_path(self, start_node_idx, end_node_idx):
        # TODO: (4) Dijkstra Path 초기화 로직
        # Dijkstra 경로 탐색을 위한 초기화 로직 입니다.
        # 변수 s와 from_node 는 딕셔너리 형태로 크기를 MGeo의 Node 의 개수로 설정합니다.
        # Dijkstra 알고리즘으로 탐색 한 Node 는 변수 s 에 True 로 탐색하지 않은 변수는 False 로 합니다.
        # from_node 의 Key 값은 Node 의 Idx로
        # from_node 의 Value 값은 Key 값의 Node Idx 에서 가장 비용이 작은(가장 가까운) Node Idx로 합니다.
        # from_node 통해 각 Node 에서 가장 가까운 Node 찾고
        # 이를 연결해 시작 노드부터 도착 노드 까지의 최단 경로를 탐색합니다.

        s = dict()
        from_node = dict()
        for node_id in list(self.nodes.keys()):
            s[node_id] = False
            from_node[node_id] = start_node_idx

        s[start_node_idx] = True
        distance = copy.deepcopy(self.weight[start_node_idx])

        # TODO: (5) Dijkstra 핵심 코드
        for i in range(len(list(self.nodes.keys())) - 1):
            selected_node_idx = self.find_nearest_node_idx(distance, s)
            s[selected_node_idx] = True
            for j, to_node_idx in enumerate(self.nodes.keys()):
                if s[to_node_idx] == False:
                    distance_candidate = distance[selected_node_idx] + self.weight[selected_node_idx][to_node_idx]
                    if distance_candidate < distance[to_node_idx]:
                        distance[to_node_idx] = distance_candidate
                        from_node[to_node_idx] = selected_node_idx

        # TODO: (6) node path 생성
        tracking_idx = end_node_idx
        node_path = [end_node_idx]

        while start_node_idx != tracking_idx:
            tracking_idx = from_node[tracking_idx]
            node_path.append(tracking_idx)

        node_path.reverse()

        # TODO: (7) link path 생성
        link_path = []
        for i in range(len(node_path) - 1):
            from_node_idx = node_path[i]
            to_node_idx = node_path[i + 1]

            from_node = self.nodes[from_node_idx]
            to_node = self.nodes[to_node_idx]

            shortest_link, min_cost = self.find_shortest_link_leading_to_node(from_node, to_node)
            link_path.append(shortest_link.idx)

        # TODO: (8) Result 판별
        if len(link_path) == 0:
            return False, {'node_path': node_path, 'link_path': link_path, 'point_path': []}

        # TODO: (9) point path 생성
        point_path = []
        for link_id in link_path:
            link = self.links[link_id]
            for point in link.points:
                point_path.append([point[0], point[1], 0])

        return True, {'node_path': node_path, 'link_path': link_path, 'point_path': point_path}


if __name__ == '__main__':
    dijkstra_path_pub = dijkstra_path_pub()


