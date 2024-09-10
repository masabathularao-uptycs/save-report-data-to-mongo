import sys
sys.path.append('cloudquery/') 
from .api_func import *
from .configs import *
from pathlib import Path
from datetime import datetime
import os
import json
import jwt
import requests
import urllib3
import multiprocessing
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent

class STS_RECORDS:
    def __init__(self,start_timestamp,end_timestamp,stack_obj,variables):
        self.load_start=start_timestamp
        self.load_end=end_timestamp
        self.api_path=None
        self.load_name = variables['load_name']

    def global_query(self,data,query):
        # test_result = TestResult()
        # log.info(str(PROJECT_ROOT))
        
        stack_keys = open_js_safely(self.api_path)
        mglobal_query_api = query_api.format(data['domain'],data['domainSuffix'],data['customerId'])
        pl=query.format(self.load_start,self.load_end)
        payload["query"]=pl
        
        output2 = post_api(data,mglobal_query_api,payload)
        job_id= output2['id']
        n_result_api =result_api.format(data['domain'], data['domainSuffix'], data['customerId'],job_id)
        payload["query"]=""

        if output2['status']=="FINISHED":
            return response
        else:
            while output2['status'] not in ['FINISHED', 'ERROR']:
                time.sleep(10)
                n_api=mglobal_query_api+'/'+job_id
                output2=get_api(data,n_api)
            if output2['status'] == 'ERROR':
                print('global query failed' )
            else :
                response=get_api(data,n_result_api)
                return response
                
    def execute_query(self,customer, query,event_count):
        
        resp = self.global_query(customer,query)
        
        
        with event_count.get_lock():
            event_count.value += resp["items"][0]["rowData"]["_col0"]
        
    def format_count(self,count):
        if count >= 10**6:
            return f"{count / 10**6:.2f} million"
        elif count >= 10**3:
            return f"{count // 10**3}k"
        else:
            return count

    def assume_role(self,data):
        query = "select count(*) from aws_cloudtrail_events where upt_time >= timestamp '{}' and upt_time <= timestamp '{}' and upt_day > 20230728 and event_name='AssumeRole';"
        processes = []
        event_count = multiprocessing.Value('i', 0)
        for customer in json.loads(data):
                p = multiprocessing.Process(target=self.execute_query, args=(customer, query,event_count))
                p.start()
                processes.append(p)
        for p in processes:
            p.join(timeout=20)
        
        
        print(f"Total assume role records: {self.format_count(event_count.value)}")
        print(f"Total assume role records/hour: {self.format_count(event_count.value / 12)}")





    def akia(self,data):
        query = "select count(*) from aws_cloudtrail_events where upt_time >= timestamp '{}' and upt_time <= timestamp '{}' and upt_day > 20230728 and event_name='AssumeRole' and user_identity_access_key_id like 'AKIA%';"
        processes = []
        event_count = multiprocessing.Value('i', 0)
        unique = multiprocessing.Value('i', 0)
        for customer in json.loads(data):
                p = multiprocessing.Process(target=self.execute_query, args=(customer, query,event_count))
                p.start()
                processes.append(p)
        for p in processes:
            p.join(timeout=20)
        
        
        

        query = "SELECT COUNT(DISTINCT user_identity_access_key_id) FROM aws_cloudtrail_events WHERE upt_time >= TIMESTAMP '{}' AND upt_time <= TIMESTAMP '{}'AND upt_day > 20230728 AND event_name = 'AssumeRole' AND user_identity_access_key_id LIKE 'AKIA%';"

        for customer in json.loads(data):
                p = multiprocessing.Process(target=self.execute_query, args=(customer, query,unique))
                p.start()
                processes.append(p)
        for p in processes:
            p.join(timeout=20)
        
        
        print(f"\nAssumeRole generated by AKIA: {self.format_count(event_count.value)} with unique AKIA keys: {unique.value}")
        print(f"AssumeRole generated by AKIA/hour: {self.format_count(event_count.value / 12)}")

    def asia(self,data):
        query = "select count(*) from aws_cloudtrail_events where upt_time >= timestamp '{}' and upt_time <= timestamp '{}' and upt_day > 20230728 and event_name='AssumeRole' and user_identity_access_key_id like 'ASIA%';"
        processes = []
        event_count = multiprocessing.Value('i', 0)
        
        for customer in json.loads(data):
                p = multiprocessing.Process(target=self.execute_query, args=(customer, query,event_count))
                p.start()
                processes.append(p)
        for p in processes:
            p.join(timeout=20)
        
        print(f"\nAssumeRole generated by ASIA: {self.format_count(event_count.value)}")
        print(f"AssumeRole generated by ASIA/hour: {self.format_count(event_count.value/12)}")

    def services(self,data):
        query = "select count(*) from aws_cloudtrail_events where upt_time >= timestamp '{}' and upt_time <= timestamp '{}' and upt_day > 20230728 and event_name='AssumeRole' and user_identity_access_key_id is NULL;"
        processes = []
        event_count = multiprocessing.Value('i', 0)
        for customer in json.loads(data):
                p = multiprocessing.Process(target=self.execute_query, args=(customer, query,event_count))
                p.start()
                processes.append(p)
        for p in processes:
            p.join(timeout=20)
        
        
        print(f"\nAssumeRole generated by services: {self.format_count(event_count.value)}")
        print(f"AssumeRole generated by services/hour: {self.format_count(event_count.value / 12)}")

    def calc_stsrecords(self):
        fs = open(api_path_multi_mercury)
        file = fs.read()
        save_dict= {}
        save_dict["Assume_Role"]=self.assume_role(file)
        save_dict["Akia"]=self.akia(file)
        save_dict["Asia"]=self.asia(file)
        save_dict["Services"]=self.services(file)

# if __name__=="__main__":
#     fs = open(api_path)
#     file = fs.read()

    
#     assume_role(file)
#     akia(file)
#     asia(file)
#     services(file)