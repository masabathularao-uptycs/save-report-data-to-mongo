from pathlib import Path

#json_directory = ""
PROJECT_ROOT = Path(__file__).resolve().parent


tables = ['kubernetes_nodes','kubernetes_pods','kubernetes_namespaces','kubernetes_pod_containers','kubernetes_events','kubernetes_secrets','kubernetes_pod_volumes','kubernetes_role_policy_rules','kubernetes_cluster_role_policy_rules','kubernetes_role_binding_subjects','kubernetes_cluster_role_binding_subjects','kubernetes_service_accounts','vulnerabilities_scanned_images', 'vulnerabilities','process_events','socket_events', 'process_file_events']

final_data = {
    "kubernetes_nodes": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_pods": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_namespaces": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_pod_containers": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_events": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_secrets": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_pod_volumes": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_role_policy_rules": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_cluster_role_policy_rules": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_role_binding_subjects": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_cluster_role_binding_subjects": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "kubernetes_service_accounts": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "vulnerabilities_scanned_images": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "vulnerabilities": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "process_events": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "socket_events": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    },
    "process_file_events": {
        "Expected Records": 0,
        "Actual Records": 0,
        "Accuracy": 0
    }
}

asset_count = 40

kubesim_ports = [1201,1202,1203,1204,1205,1206,1207,1208,1209,1210]
osquery_ports = [28001,28002,28003,28004,28005,28006,28007,28008,28009,28010]
# In Minutes
deltaTime = 60 

kube_data = {0:0,1:0,2:0,3:0,5:0,6:0,7:0,8:0,9:0,10:0,11:0,12:0}
kube_index_map = {
                0:'kubernetes_nodes',
                1:'kubernetes_pods',
                2:'kubernetes_namespaces',
                3:'kubernetes_pod_containers',
                12:'kubernetes_service_accounts',
                8:'kubernetes_role_policy_rules',
                10:'kubernetes_role_binding_subjects',
                9:'kubernetes_cluster_role_policy_rules',
                11:'kubernetes_cluster_role_binding_subjects',
                5:'kubernetes_events',
                6:'kubernetes_secrets',
                7:'kubernetes_pod_volumes'}

cvd_data = {"VulnerabilitiesScannedImages_Count": 0, 
            "Vulnerabilities_Count": 0, 
            "Compliance_Count":0, 
            "ProcessEvents_Count": 0, 
            "SocketEvents_Count": 0, 
            "ProcessFileEvents_Count": 0
            }

key_mapping = {
    'VulnerabilitiesScannedImages_Count': 'vulnerabilities_scanned_images',
    'Vulnerabilities_Count': 'vulnerabilities',
    'Compliance_Count': 'compliance',
    'ProcessEvents_Count': 'process_events',
    'SocketEvents_Count': 'socket_events',
    'ProcessFileEvents_Count': 'process_file_events'
}