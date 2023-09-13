from settings import configuration
import os

bool_options=[False,True]
load_type_options = {   
                        'Osquery':['ControlPlane', 'SingleCustomer', 'MultiCustomer'],
                        'CloudQuery':['AWS_MultiCustomer','GCP_MultiCustomer'],
                        "Combined":['Osquery+CloudQuery'],
                        'KubeQuery':['kubequery_SingleCustomer'] 
                     }

all_files = os.listdir(configuration().base_stack_config_path)
test_env_path_options = sorted([file for file in all_files if file.endswith('.json') and '_nodes' in file])

def create_input_form():
    details = {
            "test_env_file_name":'s1_nodes.json',
            "load_type":"Osquery",
            "load_name": "SingleCustomer",
            "start_time_str_ist":  "2023-08-12 23:08",
            "load_duration_in_hrs": 10,
            "sprint": 111,
            "build": 111111,
            "add_extra_time_for_charts_at_end_in_min": 10,
            "add_screenshots": True,
            "make_cpu_mem_comparisions": True,
            "fetch_node_parameters_before_generating_report" :  False,
            }

    print("Please enter the following load details ...")
    for key,value in details.items():
        Type =type(value)
        if Type == str:            
            if key == "load_type":
                helper_text=''
                for i,val in enumerate(load_type_options.keys()):
                    helper_text += f"\n {i} : {val}"
                helper_text += "\n select one option " 
                input_index = int(input(f"Enter : {' '.join(str(key).split('_')).title()} {helper_text} : ").strip())
                input_value = list(load_type_options.keys())[input_index]
            elif key == "load_name":
                helper_text=''
                for i,val in enumerate(load_type_options[details["load_type"]]):
                    helper_text += f"\n {i} : {val}"
                helper_text += "\n select one option "
                input_index = int(input(f"Enter : {' '.join(str(key).split('_')).title()} {helper_text} : ").strip())
                input_value = load_type_options[details["load_type"]][input_index]
            elif key == "test_env_file_name":
                helper_text=''
                for i,val in enumerate(test_env_path_options):
                    helper_text += f"\n {i} : {val}"
                helper_text += "\n select one option " 
                input_index = int(input(f"Enter : {' '.join(str(key).split('_')).title()} {helper_text} : ").strip())
                input_value = test_env_path_options[input_index]
            else:
                input_value=str(input(f"Enter : {' '.join(str(key).split('_')).title()}  (example: {value}) : ").strip())
        
        elif Type==bool:
            helper_text=''
            for i,val in enumerate(bool_options):
                helper_text += f"\n {i} : {val}"
            helper_text += "\n select one option " 
            input_index = int(input(f"Enter : {' '.join(str(key).split('_')).title()} {helper_text} : ").strip())
            input_value = bool_options[input_index]
        elif Type == int:
            input_value=int(input(f"Enter : {' '.join(str(key).split('_')).title()}  (example: {value}) : ").strip())

        details[key] = Type(input_value)

    print("The details you entered are : ")
    for key,val in details.items():
        print(f"{key} : {val}")

    user_input = input("Are you sure you want to continue with these details (y/n): ").strip().lower()

    if user_input =='y':
        print("Continuing ...")
        prom_con_obj = configuration(test_env_file_name=details['test_env_file_name'] , fetch_node_parameters_before_generating_report=details['fetch_node_parameters_before_generating_report'])
        return details,prom_con_obj
    elif user_input =='n':
        print("OK! Enter the details again ...")
        return create_input_form()
    

if __name__ == "__main__":
    details = create_input_form()
    print(details) 