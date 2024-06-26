import requests
import pandas as pd
from config_vars import *
databases = ["configdb","statedb"]



class pg_stats_class:
    def __init__(self,stack_obj):
        self.curr_ist_start_time=stack_obj.start_timestamp
        self.curr_ist_end_time=stack_obj.end_timestamp
        self.load_duration=stack_obj.hours
        self.PROMETHEUS = stack_obj.prometheus_path
        self.API_PATH = PROM_API_PATH
        self.stack_obj=stack_obj
        
    def get_data(self,db):
        query = f'uptycs_pg_stats{{db=~"{db}"}}'
        params = {
            'query': query,
            'start': self.curr_ist_start_time,
            'end': self.curr_ist_end_time,
            'step': self.load_duration * 3600              
        }
        response = requests.get(self.PROMETHEUS + self.API_PATH, params=params)
        self.stack_obj.log.info(f"-------processing PG STATS for {query} (timestamp : {self.curr_ist_start_time} to {self.curr_ist_end_time}), Status code : {response.status_code}")
        if response.status_code != 200:self.stack_obj.log.error(f"Request failed status code {response.status_code}")
        result = response.json()['data']['result']

        return result
            
    def process_output(self):
        table_dict = {}
        for db in databases:
            data_dict = self.get_data(db)

            # Create empty DataFrames
            df_table = pd.DataFrame(columns=['TableName', 'StartTableSize', 'EndTableSize', 'Delta'])
            df_index = pd.DataFrame(columns=['TableName', 'StartIndexSize', 'EndIndexSize', 'Delta'])
            df_tuples = pd.DataFrame(columns=['TableName', 'StartLiveTuples', 'EndLiveTuples', 'Delta'])
            
            for dict in data_dict:
                if dict['metric']['stat'] in ['table_size_bytes','index_size_bytes','live_tuples']:
                    table_name = dict['metric']['table_name']
                    start_value=None
                    end_value=None
                    diff=None
                    if len(dict['values'])==1:
                        if dict['values'][0][0] == self.curr_ist_start_time:
                            start_value=int(dict['values'][0][1])
                        else:
                            end_value=int(dict['values'][0][1])
                    elif len(dict['values'])==2:
                        start_value=int(dict['values'][0][1])
                        end_value=int(dict['values'][1][1])
                        diff = end_value-start_value
                    if dict['metric']['stat'] == 'table_size_bytes':
                        df_table.loc[len(df_table)] = [table_name,start_value,end_value,diff]
                    elif dict['metric']['stat'] == 'index_size_bytes':
                        df_index.loc[len(df_index)] = [table_name,start_value,end_value,diff]
                    elif dict['metric']['stat'] == 'live_tuples':
                        df_tuples.loc[len(df_tuples)] =[table_name,start_value,end_value,diff] 

            df_table[['StartTableSize','EndTableSize','Delta']] = df_table[['StartTableSize','EndTableSize','Delta']].div(1024)
            df_index[['StartIndexSize','EndIndexSize','Delta']] = df_index[['StartIndexSize','EndIndexSize','Delta']].div(1024)

            df_table.sort_values('Delta',ascending=False,inplace=True)
            df_index.sort_values('Delta',ascending=False,inplace=True)
            df_tuples.sort_values('Delta',ascending=False,inplace=True)
            
            table_json = df_table.to_json()
            index_json = df_index.to_json()
            tuples_json = df_tuples.to_json()

            obj = {
                "{}_tablesize".format(db) : table_json,
                "{}_indexsize".format(db) : index_json,
                "{}_tuples".format(db) : tuples_json
            }
            
            table_dict.update(obj)
        
        return table_dict

# from settings import stack_configuration
# cls  = pg_stats_class(1702926000,1702947600,6,stack_configuration("longevity_nodes.json"))
# print("FINAL O/P : " ,cls.process_output())