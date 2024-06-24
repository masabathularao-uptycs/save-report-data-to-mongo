import requests
import json

from config_vars import *


class DB_OPERATIONS_TIME:
    def __init__(self,stack_obj):
        self.curr_ist_start_time=stack_obj.start_timestamp
        self.PROMETHEUS = stack_obj.prometheus_path
        self.API_PATH = prom_point_api_path

                
        self.query = "sort_desc(sum(curr_state_db_op_sec_bucket) by(le))"
        #self.query2 = "sort_desc(rate(curr_state_db_op_sec_sum{ job="cloudquery"}[5m])/rate(curr_state_db_op_sec_count{ job="cloudquery"}[5m])) > 0.1"

    def extract_data(self,query,timestamp):
        PARAMS = {
            'query': query,
            'time' : timestamp
        }
        response = requests.get(self.PROMETHEUS + self.API_PATH, params=PARAMS)
        self.stack_obj.log.info(f"Excecuting query : {query} at timestamp {timestamp} , Status code : {response.status_code}")
        if response.status_code != 200:self.stack_obj.log.error("ERROR : Request failed")
        result = response.json()['data']['result']
        return result
    
        
    def db_operations(self):
        result = self.extract_data(self.query,self.curr_ist_start_time)
        save_dict={}
        for item in result:
            le_value = item['metric']['le']
            value = int(item['value'][1])
            save_dict[str(item['metric'])] = value
        self.stack_obj.log.info(save_dict)
        return save_dict
    
    
