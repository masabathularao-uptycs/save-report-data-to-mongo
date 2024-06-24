import os
#ports
api_report_port = 8001
pgbadger_report_port = 8000
prometheus_port = 9090
kube_prometheus_port = 31090
ssh_port = 22

#ips
perf_prod_dashboard = "192.168.146.69"

#int and strings
prom_api_path = "/api/v1/query_range"
prom_point_api_path = "/api/v1/query"
abacus_username = 'abacus'  
abacus_password = 'abacus' 
mongo_connection_string = "mongodb://localhost:27017"
# api_loads_folder_path = "/home/abacus/apache-jmeter-5.6.2/bin/reports/"
presto_loads_folder_path = "/home/abacus/benchto_reports/"

#other types
kube_metrics = ["container_memory_working_set_bytes","container_cpu_usage_seconds_total"]

#dynamic
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
STACK_JSONS_PATH = f"{ROOT_PATH}/stacks"
BASE_GRAPHS_PATH = os.path.join(os.path.dirname(ROOT_PATH),'graphs')
BASE_HTMLS_PATH = os.path.join(os.path.dirname(ROOT_PATH),'htmls')
BASE_PDFS_PATH = os.path.join(os.path.dirname(ROOT_PATH),'pdfs')
BASE_LOGS_PATH = os.path.join(ROOT_PATH,'logs')


