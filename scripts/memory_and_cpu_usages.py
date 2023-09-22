import requests
import json

HOST = 'Host'
memory_tag = "Memory"
cpu_tag = "CPU"
memory_unit = "GB"
cpu_unit = "cores"

app_names={
            "sum":[ ".*osqLogger.*", "kafka",".*ruleEngine.*","tls","eventsDbIngestion"  , "trino" , "osqueryIngestion"],
            "avg":[]
          }

memory_queries = {f"{HOST}" : 'avg((uptycs_memory_used/uptycs_total_memory) * 100)  by (host_name)',}
memory_queries.update(dict([(app,f"{key}(uptycs_app_memory{{app_name=~'{app}'}}) by (host_name)") for key,app_list in app_names.items() for app in app_list]))

cpu_queries = {f"{HOST}" : 'avg(100-uptycs_idle_cpu) by (host_name)',}
cpu_queries.update(dict([(app,f"{key}(uptycs_app_cpu{{app_name=~'{app}'}}) by (host_name)") for key,app_list in app_names.items() for app in app_list]))

container_memory_queries = {'container' : "sum(uptycs_docker_mem_used{}/(1000*1000*1000)) by (container_name)",}
container_cpu_queries = {'container' : "sum(uptycs_docker_cpu_stats{}) by (container_name)",}

all_queries_to_execute={
    "memory_queries":memory_queries,
    "cpu_queries":cpu_queries,
    "container_memory_queries":container_memory_queries,
    "container_cpu_queries":container_cpu_queries
}

class MC_comparisions:
    def __init__(self,prom_con_obj,start_timestamp,end_timestamp):
        self.curr_ist_start_time=start_timestamp
        self.curr_ist_end_time=end_timestamp
        self.prom_con_obj=prom_con_obj
        self.PROMETHEUS = self.prom_con_obj.prometheus_path
        self.API_PATH = self.prom_con_obj.prom_api_path
        self.test_env_file_path=prom_con_obj.test_env_file_path
        with open(self.test_env_file_path, 'r') as file:
            self.nodes_data = json.load(file)

    def extract_data(self,queries,tag,unit):
        final=dict()
        return_overall = dict()

        for query in queries:
            final[query] = {}
            PARAMS = {
                'query': queries[query],
                'start': self.curr_ist_start_time,
                'end': self.curr_ist_end_time,
                'step':15
            }
            response = requests.get(self.PROMETHEUS + self.API_PATH, params=PARAMS)
            print(f"-------processing {tag} for {query} (timestamp : {self.curr_ist_start_time} to {self.curr_ist_end_time}), Status code : {response.status_code}")
            if response.status_code != 200:print("ERROR : Request failed")
            result = response.json()['data']['result']
            if query==HOST:
                print("All hosts : ", [r['metric']['host_name'] for r in result])
            for res in result:
                hostname = res['metric']['host_name']
                print(f"Processing node-level {tag} usage for {query} : {hostname}")
                if str(hostname).endswith('v') and len(hostname)>1:
                    hostname = str(hostname)[:-1]
                values = [float(i[1]) for i in res['values']]   
                avg = sum(values) / len(values)
                minimum = min(values)
                maximum = max(values)
                final[query][hostname] = {"percentage":{"average":avg , "minimum":minimum , "maximum":maximum}}
                final[query][hostname][unit]={}
                if tag == memory_tag:
                    final[query][hostname][unit]={
                        'average':avg * float(self.nodes_data[hostname]['ram']) / 100,
                        'minimum':minimum * float(self.nodes_data[hostname]['ram']) / 100,
                        'maximum':maximum * float(self.nodes_data[hostname]['ram']) / 100
                    }
                else:
                    if query == HOST:
                        final[query][hostname][unit]={
                            'average':avg * float(self.nodes_data[hostname]['cores']) / 100,
                            'minimum':minimum * float(self.nodes_data[hostname]['cores']) / 100,
                            'maximum':maximum * float(self.nodes_data[hostname]['cores']) / 100
                        }
                    else:
                        final[query][hostname][unit]={
                            'average':avg/100,
                            'minimum': minimum/100,
                            'maximum': maximum/100
                        }

        #calculate overall pnodes,dnodes,pgnodes usage
        new_data = final[HOST]
        for node_type in ["pnodes" , "dnodes" , "pgnodes"]:
            print(f"Calculating overall {tag} usages for node-type : {node_type}")
            new_sum=0
            for node in self.nodes_data[node_type]:
                try:
                    new_sum+=new_data[node][unit]["average"]
                except KeyError as e:
                    print(f"ERROR : key {node} not found in : {new_data}")
            return_overall[node_type] = {f"{unit}":new_sum}
            print(f"{node_type} : {new_sum} {unit}")
        return final,return_overall

    def extract_container_data(self,queries,tag,unit):
        final=dict()
        for query in queries:
            final[query] = {}
            PARAMS = {
                'query': queries[query],
                'start': self.curr_ist_start_time,
                'end': self.curr_ist_end_time,
                'step':15
            }
            response = requests.get(self.PROMETHEUS + self.API_PATH, params=PARAMS)
            print(f"----------processing {tag} for {query} (timestamp : {self.curr_ist_start_time} to {self.curr_ist_end_time}), Status code : {response.status_code}")
            if response.status_code != 200:print("ERROR : Request failed")
            result = response.json()['data']['result']
            for res in result:
                container_name = res['metric']['container_name']
                print(f"Processing container-level {tag} usage for {query} : {container_name}")
                values = [float(i[1]) for i in res['values']]   
                avg = sum(values) / len(values)
                minimum = min(values)
                maximum = max(values)
                if tag == cpu_tag:
                    avg = avg/100
                    minimum = minimum/100
                    maximum = maximum/100
                final[query][container_name] = {f"{unit}":{"average":avg , "minimum":minimum , "maximum":maximum}}
        return final 
    
    def make_comparisions(self):
        print("All usage queries to be executed are : ")
        print(json.dumps(all_queries_to_execute, indent=4))
        memory_data,overall_memory_data = self.extract_data(memory_queries,memory_tag,memory_unit)
        cpu_data,overall_cpu_data = self.extract_data(cpu_queries,cpu_tag,cpu_unit)
        container_memory_data =  self.extract_container_data(container_memory_queries,memory_tag,memory_unit)
        container_cpu_data =  self.extract_container_data(container_cpu_queries,cpu_tag,cpu_unit)
        
        current_build_data={
            "node_level_resource_utilization": {
                "memory":memory_data,
                "cpu" : cpu_data,
            },
            "container_level_resource_utilization":{
                "memory":container_memory_data,
                "cpu" : container_cpu_data,
            }
        }
        return current_build_data,{ "node_level_total_average_resource_utilization":{
                                        "memory":overall_memory_data,
                                        "cpu":overall_cpu_data
                                    }}