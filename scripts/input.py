from settings import configuration
import os
from parent_load_details import parent
from osquery.osquery_child_class import osquery_child
from cloudquery.cloudquery_child_class import cloudquery_child
from kubequery.kubequery_child_class import kubequery_child

bool_options=[False,True]
load_type_options = {   
                        'Osquery':{
                                        'subtypes':['ControlPlane', 'SingleCustomer', 'MultiCustomer'],
                                        'class':osquery_child
                                  },
                        'CloudQuery':{
                                        'subtypes':['AWS_MultiCustomer','GCP_MultiCustomer','AWS_SingleCustomer'],
                                        'class':cloudquery_child
                                     },
                        'KubeQuery_and_SelfManaged':{
                                        'subtypes':['KubeQuery_SingleCustomer','SelfManaged_SingleCustomer'],
                                        'class':kubequery_child
                                    } 
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
            # "fetch_node_parameters_before_generating_report" :  False,
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
                for i,val in enumerate(load_type_options[details["load_type"]]['subtypes']):
                    helper_text += f"\n {i} : {val}"
                helper_text += "\n select one option "
                input_index = int(input(f"Enter : {' '.join(str(key).split('_')).title()} {helper_text} : ").strip())
                input_value = load_type_options[details["load_type"]]['subtypes'][input_index]
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

    user_input = input("Are you sure you want to continue with these details? This will make permenant changes in the database (y/n): ").strip().lower()

    if user_input =='y':
        print("Continuing ...")
        try:
            load_cls = load_type_options[details["load_type"]]['class']
            print(f"Using load class : {load_cls}")
        except:
            print(f"WARNING: load class for {load_type_options[details['load_type']]} is not found , hence using the parent class : {parent}")
            load_cls = parent
        prom_con_obj = configuration(test_env_file_name=details['test_env_file_name'] , fetch_node_parameters_before_generating_report=True)
        return details,prom_con_obj,load_cls
    elif user_input =='n':
        print("OK! Enter the modified details ...")
        return create_input_form()
    else:
        print("INVALID INPUT!")
        return None,None,None

if __name__ == "__main__":
    details = create_input_form()
    print(details) 