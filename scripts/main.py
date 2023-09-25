import sys
import time
import pymongo
from datetime import datetime, timedelta
import json
from datetime import datetime
from memory_and_cpu_usages import MC_comparisions
from osquery.add_kafka_topics import kafka_topics
from disk_space import DISK
from input import create_input_form
from capture_charts_data import Charts
from gridfs import GridFS
from compaction_status import take_screenshots
from trino_queries import TRINO

if __name__ == "__main__":
    s_at = time.perf_counter()
    variables , prom_con_obj =create_input_form()
    if not variables or not prom_con_obj : 
        print("Received NoneType objects, terminating the program ...")
        sys.exit()
    TEST_ENV_FILE_PATH   = prom_con_obj.test_env_file_path
    print("Test environment file path is : " + TEST_ENV_FILE_PATH)
    #---------------------start time and endtime (timestamps) for prometheus queries-------------------
    format_data = "%Y-%m-%d %H:%M"
    start_time = datetime.strptime(variables["start_time_str_ist"], format_data)
    end_time = start_time + timedelta(hours=variables["load_duration_in_hrs"])

    start_time_str = variables["start_time_str_ist"]
    end_time_str = end_time.strftime(format_data)
    start_timestamp = int(start_time.timestamp())
    end_timestamp = int(end_time.timestamp())

    print("------ starttime and endtime strings in IST are : ", start_time_str , end_time_str)
    print("------ starttime and endtime unix time stamps are : ", start_timestamp , end_timestamp)
    #-------------------------------------------------------------------------------------------------
    with open(TEST_ENV_FILE_PATH , 'r') as file:
        test_env_json_details = json.load(file)
    skip_fetching_data=False
    #---------------------Check for previous runs------------------------------------
    mongo_connection_string=prom_con_obj.mongo_connection_string
    client = pymongo.MongoClient(mongo_connection_string)
    database_name = variables['load_type']+"_LoadTests"
    collection_name = variables["load_name"]
    db=client[database_name]
    collection = db[collection_name]

    documents_with_same_load_time_and_stack = collection.find({"load_details.sprint":variables['sprint'] ,"load_details.stack":test_env_json_details["stack"] , "load_details.load_start_time_ist":f"{variables['start_time_str_ist']}" , "load_details.load_duration_in_hrs":variables['load_duration_in_hrs']})
    if len(list(documents_with_same_load_time_and_stack)) > 0:
        print(f"ERROR! A document with load time ({variables['start_time_str_ist']}) - ({end_time_str}) on {test_env_json_details['stack']} for this sprint for {database_name}-{collection_name} load is already available.")
        skip_fetching_data=True
    if skip_fetching_data == False:
        run=1
        documents_with_same_sprint = list(collection.find({"load_details.sprint":variables['sprint']}))
        if len(documents_with_same_sprint)>0:
            max_run = 0
            for document in documents_with_same_sprint :
                max_run = max(document['load_details']['run'] , max_run)
            run=max_run+1
            print(f"you have already saved the details for this load in this sprint, setting run value to {run}")
        #-------------------------disk space--------------------------
        disk_space_usage_dict=None
        if variables["load_name"] != "ControlPlane":
            print("Performing disk space calculations ...")
            calc = DISK(start_timestamp=start_timestamp,end_timestamp=end_timestamp,prom_con_obj=prom_con_obj)
            disk_space_usage_dict=calc.make_calculations()
        #--------------------------------- add kafka topics ---------------------------------------
        kafka_topics_list=None
        if variables["load_type"]=="Osquery":
            print("Add kafka topics ...")
            kafka_obj = kafka_topics(prom_con_obj=prom_con_obj)
            kafka_topics_list = kafka_obj.add_topics_to_report()

        #-------------------------Trino Queries--------------------------

        if variables["load_type"] != "KubeQuery":
            print("Performing trino queries ...")
            calc = TRINO(curr_ist_start_time=variables["start_time_str_ist"],curr_ist_end_time=end_time_str,prom_con_obj=prom_con_obj)
            trino_queries = calc.make_calculations()

        #--------------------------------cpu and mem node-wise---------------------------------------
        print("Fetching resource usages data ...")
        comp = MC_comparisions(start_timestamp=start_timestamp,end_timestamp=end_timestamp,prom_con_obj=prom_con_obj)
        mem_cpu_usages_dict,overall_usage_dict=comp.make_comparisions()
        #--------------------------------Capture charts data---------------------------------------
        fs = GridFS(db)
        print("Fetching charts data ...")
        charts_obj = Charts(start_timestamp=start_timestamp,end_timestamp=end_timestamp,prom_con_obj=prom_con_obj,
                add_extra_time_for_charts_at_end_in_min=variables["add_extra_time_for_charts_at_end_in_min"],fs=fs)
        complete_charts_data_dict,all_gridfs_fileids=charts_obj.capture_charts_and_save()
        #--------------------------------take screenshots---------------------------------------
        print("Capturing compaction status screenshots  ...")
        cp_obj = take_screenshots(start_time=start_time,end_time=end_time,fs=fs,elk_url=test_env_json_details["elk_url"])
        compaction_status_image=cp_obj.get_compaction_status()
        #-------------------------- Saving the json data to mongo -------------------------
        print("Saving data to mongoDB ...")
        load_details =  {
            "stack":test_env_json_details["stack"],
            "sprint": variables['sprint'],
            "build": variables['build'],
            "load_name":f"{variables['load_name']}",
            "load_type":f"{variables['load_type']}",
            "load_duration_in_hrs":variables['load_duration_in_hrs'],
            "load_start_time_ist" : f"{variables['start_time_str_ist']}",
            "load_end_time_ist" : f"{end_time_str}",
            "run":run,
            }
        with open(f"{prom_con_obj.base_stack_config_path}/load_specific_details.json" , 'r') as file:
            load_specific_details = json.load(file)
        load_details.update(load_specific_details[variables['load_name']])

        final_data_to_save = {
            "load_details":load_details,
            "test_environment_details":test_env_json_details
        }

        final_data_to_save.update(overall_usage_dict)

        if disk_space_usage_dict:
            final_data_to_save.update({"disk_space_usages":disk_space_usage_dict})
        if kafka_topics_list:
            final_data_to_save.update({"kafka_topics":kafka_topics_list})
        if trino_queries:
            final_data_to_save.update({"Trino_queries":trino_queries})

        final_data_to_save.update({"charts":complete_charts_data_dict})
        final_data_to_save.update({"images":compaction_status_image})
        final_data_to_save.update(mem_cpu_usages_dict)

        try:
            inserted_id = collection.insert_one(final_data_to_save).inserted_id
            print(f"Document pushed to mongo successfully into database:{database_name}, collection:{collection_name} with id {inserted_id}")
        except Exception as e:
            print(f"ERROR : Failed to insert document into database {database_name}, collection:{collection_name} , {str(e)}")
            print("Deleting stored chart data ...")
            for file_id in all_gridfs_fileids:
                print("deleting ", file_id)
                db.fs.chunks.delete_many({'files_id': file_id})
                db.fs.files.delete_one({'_id': file_id})
        client.close()
        #-----------------------------------------------------------------
        f3_at = time.perf_counter()
        print(f"Collecting the report data took : {round(f3_at - s_at,2)} seconds in total")
    