from parent_load_details import parent

class all_combined_child(parent):
    load_specific_details={
                "Osquery(multi)_CloudQuery(aws_gcp_multi)_KubeQuery(single)_and_SelfManaged(single)":{
                    "test_title": "Multiple Customer Rule Engine, Control Plane, CloudQuery, KubeQuery and SelfManaged Load",
                    "total_number_of_customers": 100,
                    "number_of_customers_with_auto_exception_enabled": 0,
                    "total_assets": "32K Control Plane +  6K Multi customer",
                    "records_sent_per_hour_per_customer": "38,88,000",
                    "records_sent_per_hour" : "38,88,00,000",
                    "assets_per_cust":60,
                    "input_file": "rhel7-6tab_12rec.log",
                    "events_table_name": "dns_lookup_events, socket_events, process_events, process_file_events"
                }
    }

class osquery_cloudquery_combined_child(parent):
    load_specific_details={
                "Osquery(multi)_CloudQuery(aws_gcp_multi)":{
                    "test_title": "Multiple Customer Rule Engine, Control Plane and CloudQuery Load",
                    "total_number_of_customers": 120,
                    "number_of_customers_with_auto_exception_enabled": 0,
                    "total_assets": "52k (12k Multicustomer + 40 k Control plane)",
                    "records_sent_per_hour_per_customer": "6,480,000",
                    "records_sent_per_hour" : "77,76,00,000",
                    "assets_per_cust":100,
                    "input_file": "rhel7-6tab_12rec.log",
                    "events_table_name": "dns_lookup_events, socket_events, process_events, process_file_events"
                }
    }