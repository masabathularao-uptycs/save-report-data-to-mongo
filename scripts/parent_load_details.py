import copy
from collections import defaultdict

class parent:
    @classmethod
    @property
    def common_app_names(cls):
        return  {"sum":["orc-compaction" ,"uptycs-configdb",  ".*osqLogger.*", "kafka","spark-worker",".*ruleEngine.*",
                        "data-archival",".*redis-server.*","/opt/uptycs/cloud/go/bin/complianceSummaryConsumer","tls",".*airflow.*",
                        "trino","pgbouncer","spark-master","/usr/local/bin/pushgateway" , "auditLogsIngestion","alertsIngestion",
                        "prestoLogsIngestion","queryPackIngestion","osqueryIngestion"],
                "avg":[]
                }
    

    @classmethod
    @property
    def hostname_types(cls):
        return ["process","data","pg","airflow"]
    
    @classmethod
    @property
    def mon_spark_topic_names(cls):
        return ['event','audit','prestoquerylogs']
    
    @classmethod
    @property
    def kafka_group_names(cls):
        return ['db-alerts','ruleengine','debeziumconsumer','db-incidents']
    
    @classmethod
    @property
    def list_of_observations_to_make(cls):
        return [
                    'Check for Ingestion lag',
                    'Check for Rule engine Lag',
                    'Check for db-events Lag',
                    'Data loss check for raw tables like processes, process_env etc (accuracy)',
                    'Data loss check for processed data like events, alerts and incidents etc (accuracy)',
                    "Check if CPU/memory utilisation in line with previous sprints. If not, are the differences expected?",
                    'Check for variations in the Count of queries executed on presto',
                    'Triage bugs and check for blockers',
                    'Check if PG master is in sync with replica',
                    'Check for memory leaks',
                    'Check for variation in HDFS disk usage',
                    'Check for variation in PG disk usage',
                    'Check for variation in Kafka disk usage',
                    'Check for new kafka topics',
                    'Check for steady state of live assets count'
                ]
    

    @staticmethod
    def get_basic_chart_queries():
        return {"Live Assets Count":("sum(uptycs_live_count)" , []),
                "Kafka Lag for all groups":("uptycs_kafka_group_lag{group!~'db-events|cloudconnectorsgroup'} or uptycs_mon_spark_lag{ topic='event'} or uptycs_mon_spark_lag{topic!~'event|cloudconnectorsink|agentosquery'}",['cluster_id','topic','group']),
                }
    
    @classmethod
    def get_node_level_RAM_used_percentage_queries(cls):
        return dict([(f"{node} node RAM used percentage",(f"((uptycs_memory_used{{node_type='{node}'}}/uptycs_total_memory{{node_type='{node}'}})*100)" , ["host_name"] , '%') ) for node in cls.hostname_types])
    
    @classmethod
    def get_app_level_RAM_used_percentage_queries(cls):
        app_level_RAM_used_percentage_queries= dict([(f"Memory Used by {app}",(f"{key}(uptycs_app_memory{{app_name=~'{app}'}}) by (host_name)" , ["host_name"], '%') ) for key,app_list in cls.common_app_names.items() for app in app_list])
        more_memory_queries={
            "Kafka Disk Used Percentage":("uptycs_percentage_used{partition=~'/data/kafka'}" , ["host_name"], '%'),
            "Debezium memory usage":("uptycs_docker_mem_used{container_name='debezium'}" , ["host_name"],'bytes'),
        }
        app_level_RAM_used_percentage_queries.update(more_memory_queries)
        return app_level_RAM_used_percentage_queries

    @classmethod
    def get_node_level_CPU_busy_percentage_queries(cls):
        return dict([(f"{node} node CPU busy percentage",(f"100-uptycs_idle_cpu{{node_type='{node}'}}",["host_name"], '%') ) for node in cls.hostname_types])
    
    @classmethod
    def get_app_level_CPU_used_cores_queries(cls):
        app_level_CPU_used_cores_queries=dict([(f"CPU Used by {app}", (f"{key}(uptycs_app_cpu{{app_name=~'{app}'}}) by (host_name)" , ["host_name"], '%') ) for key,app_list in cls.common_app_names.items() for app in app_list])
        more_cpu_queries={
            "Debezium CPU usage":("uptycs_docker_cpu_stats{container_name='debezium'}" , ["host_name"]),
        }

        app_level_CPU_used_cores_queries.update(more_cpu_queries)
        return app_level_CPU_used_cores_queries
    

    @staticmethod
    def get_inject_drain_and_lag_uptycs_mon_spark(topic):
        return {
            f"Spark Inject Rate for {topic} topic":(f"uptycs_mon_spark_inject_rate{{topic='{topic}'}}",["__name__","cluster_id","topic"]),
            f"Spark Drain Rate for {topic} topic":(f"uptycs_mon_spark_drain_rate{{topic='{topic}'}}",["__name__","cluster_id","topic"]),
            f"Spark lag for {topic} topic":(f"uptycs_mon_spark_lag{{topic='{topic}'}}",["__name__","cluster_id","topic"]),
        }
    
    @staticmethod
    def get_inject_drain_and_lag_uptycs_kafka_group(group):
        return {
            f"Kafka Inject Rate for {group} group":(f"uptycs_kafka_group_inject_rate{{group='{group}'}}",["__name__","cluster_id","group"]),
            f"Kafka Drain Rate for {group} group":(f"uptycs_kafka_group_drain_rate{{group='{group}'}}",["__name__","cluster_id","group"]),
            f"Kafka lag for {group} group":(f"uptycs_kafka_group_lag{{group='{group}'}}",["__name__","cluster_id","group"]),
        }
        
    @classmethod
    def get_inject_drain_rate_and_lag_chart_queries(cls):
        queries={}
        queries['Debezium Replication Lag']=('sum(uptycs_pg_logical_replication_lag{slot_name=~".*debezium.*"}) by (database,lag_type,slot_name,slot_type)' , ['slot_name','lag_type'] , 'bytes' )
        for topic in cls.mon_spark_topic_names:
            queries.update(cls.get_inject_drain_and_lag_uptycs_mon_spark(topic))
        for group in cls.kafka_group_names:
            queries.update(cls.get_inject_drain_and_lag_uptycs_kafka_group(group))
        return copy.deepcopy(queries)

    @staticmethod
    def get_connections_chart_queries():
        return {
            "No.of active connections group by application for configdb on master":("uptycs_pg_idle_active_connections_by_app{state=\"active\",db=\"configdb\",role=\"master\"}" , ["application_name"]),
            "Active Client Connections":("uptycs_pgb_cl_active" , ["host_name","db","db_user"]),
            "Waiting Client Connections":("uptycs_pgb_cl_waiting", ["db" , "db_user"]),
            "Uptycs pg Connections by app":("sum(uptycs_pg_connections_by_app)" , []),
            "Uptycs redis Connections":("sum(uptycs_redis_connection)" , []),
            "Redis client connections for tls":("sum(uptycs_app_redis_clients{app_name='/opt/uptycs/cloud/tls/tls.js'}) by (host_name)" , ["host_name"]),
            "Top 10 redis client connections by app":("sort(topk(9,sum(uptycs_app_redis_clients{}) by (app_name)))" , ["app_name"]),
            "Active Server Connections":("uptycs_pgb_sv_active", ["db" , "db_user"]),
            "Idle server connections":("uptycs_pgb_sv_idle", ["db" , "db_user"]),
        }

    @staticmethod
    def get_other_chart_queries():
        return {
            "Configdb Pg wal folder size":("configdb_wal_folder",["host_name"]),
            "Configdb number of wal files":("configdb_wal_file{}" , ["host_name"]),
            "Configdb folder size":("configdb_size" , ["host_name"]),
            "Average records in pg bouncer":("uptycs_pbouncer_stats{col=~'avg.*', col!~'.*time'}" , ["col"]),
            "Average time spent by pg bouncer":("uptycs_pbouncer_stats{col=~'avg.*time'}" , ["col"] , 'μs'),
            "iowait time":("uptycs_iowait{}" , ["host_name"]),
            "iowait util%":("uptycs_iowait_util_percent{}" , ["host_name" , "device"]),
            "Disk read wait time":("uptycs_r_await{}" , ["host_name" , "device"],'ms'),
            "Disk write wait time":("uptycs_w_await{}", ["host_name" , "device"],'ms'),
            "Disk blocks in configdb":("uptycs_configdb_stats{col =~ \"blks.*\"}",["col"]),
            "Transaction count in configdb":("uptycs_configdb_stats{col =~ \"xact.*\"}",["col"]),
            "Row count in configdb":("uptycs_configdb_stats{col =~ \"tup.*\"}",["col"]),
            "Assets table stats":("uptycs_psql_table_stats",["col"]),
            "pg and data partition disk usage" : ("uptycs_used_disk_bytes{node_type=\"pg\",partition=\"/data\"} or uptycs_used_disk_bytes{node_type=\"pg\",partition=\"/pg\"}" , ["partition","host_name"],'bytes'),
            "configdb partition disk usage" : ("uptycs_used_disk_bytes{node_type=\"pg\",partition=\"/data/pgdata/configdb\"}" , ["partition","host_name"],'bytes'),
            "statedb partition disk usage" :  ("uptycs_used_disk_bytes{node_type=\"pg\",partition=\"/data/pgdata/statedb\"}" , ["partition","host_name"],'bytes'),
            "StateDB errors":("sum(curr_state_db_errors) by (error,table_name)" , ["error" , "table_name"])
        }
    
    @staticmethod
    def get_pg_charts():
        return {
            "Configb PG table size per table":('uptycs_pg_stats{db=~"configdb",stat="table_size_bytes"}',["table_name"]),
            "Configb PG index size per table":('uptycs_pg_stats{db=~"configdb",stat="index_size_bytes"}',["table_name"]),
            "Configb PG live tuples per table":('uptycs_pg_stats{db=~"configdb",stat="live_tuples"}',["table_name"]),
            "Configb PG connections by state":('sum(uptycs_pg_connections_by_state{db=~"configdb"}) by (state)',["state"]),
            "Configb PG connections by application":('sum(uptycs_pg_connections_by_app{db=~"configdb"}) by (application_name)',["application_name"]),
            "Statedb PG table size per table":('uptycs_pg_stats{db=~"statedb",stat="table_size_bytes"}',["table_name"]),
            "Statedb PG index size per table":('uptycs_pg_stats{db=~"statedb",stat="index_size_bytes"}',["table_name"]),
            "Statedb PG live tuples per table":('uptycs_pg_stats{db=~"statedb",stat="live_tuples"}',["table_name"]),
            "Statedb PG connections by state":('sum(uptycs_pg_connections_by_state{db=~"statedb"}) by (state)',["state"]),
            "Statedb PG connections by application":('sum(uptycs_pg_connections_by_app{db=~"statedb"}) by (application_name)',["application_name"]),
        }
    
    @staticmethod
    def get_restart_count_charts():
        return {
            "Uptycs containers restart count":('sum(uptycs_container_restart_count) by (container_name)' , ["container_name"]),
            }
    
    @classmethod
    def get_all_chart_queries(cls):
        return {
            "Live Assets and Kafka lag for all groups":cls.get_basic_chart_queries(),
            "Node-level Memory Charts":cls.get_node_level_RAM_used_percentage_queries(),
            "Node-level CPU Charts":cls.get_node_level_CPU_busy_percentage_queries(),
            "Application-level Memory Charts":cls.get_app_level_RAM_used_percentage_queries(),
            "Application-level CPU Charts":cls.get_app_level_CPU_used_cores_queries(),
            "Inject-Drain rate and Lag Charts":cls.get_inject_drain_rate_and_lag_chart_queries(),
            "Pg Stats Charts": cls.get_pg_charts(),
            "Restart count Charts": cls.get_restart_count_charts(),
            "Connection Charts": cls.get_connections_chart_queries(),
            "Other Charts":cls.get_other_chart_queries()
        }


    load_specific_details=defaultdict(lambda:{})

    @classmethod
    def get_load_specific_details(cls,load_name):
        return cls.load_specific_details[load_name]
    
    
    @classmethod
    def get_dictionary_of_observations(cls):
        observations_dict=dict([(observation,{"Status":"" , "Comments":""}) for observation in cls.list_of_observations_to_make])
        return observations_dict
    
    @classmethod
    @property
    def trino_details_commands(cls):
        return {
            "Total number of trino queries executed from each source" : {
                "query" :  "SELECT\
                                source,\
                                COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
                                COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
                                COUNT(*) as total_count\
                            FROM presto_query_logs\
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            GROUP BY 1\
                            ORDER BY 1;",
                "columns":['source','success_count','failure_count','total_count'],
                "schema":{
                    "merge_on_cols" : ["source"],
                    "compare_cols":["total_count"]
                }
            },
            "Total number of trino queries executed from each source grouped by query_operation" : {
                "query" :  "SELECT\
                                source,\
                                query_operation,\
                                COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
                                COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
                                COUNT(*) as total_count\
                            FROM presto_query_logs\
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            GROUP BY 1,2\
                            ORDER BY 1,2;",
                "columns":['source','query_operation','success_count','failure_count','total_count'],
                "schema":{
                    "merge_on_cols" : ["source","query_operation"],
                    "compare_cols":["total_count"]
                }
            },
            "Total number of failed queries grouped by failure message" : {
                "query" :  "select \
                                source,\
                                query_operation,\
                                failure_message,\
                                failure_type,\
                                count(*) as failure_count \
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            and query_status='FAILURE' \
                            group by 1,2,3,4 \
                            order by 1,2;",
                "columns":['source','query_operation','failure_message','failure_type','failure_count'],
                "schema":{
                    "merge_on_cols" : ['source','query_operation','failure_message','failure_type'],
                    "compare_cols":["failure_count"]
                }
            }
          }