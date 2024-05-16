from bs4 import BeautifulSoup
import pandas as pd
import re

def convert_to_seconds(string):
    pattern = r'\d+[a-zA-Z]+'
    substrings = re.findall(pattern, string)
    if substrings:
        # print(f"Substrings found in '{string}': {substrings}")
        days,hours,millisec,seconds,minutes=0,0,0,0,0
        for i in substrings:
            if 'd' in  i:
                days=int(i[:-1])
            elif 'h' in i:
                hours = int(i[:-1])
            elif 'ms' in i:
                millisec = int(i[:-2])
            elif 's' in i:
                seconds = int(i[:-1])
            elif 'm' in i:
                minutes = int(i[:-1])
            else:
                print(f"Unknown pattern found  in {string} : {i}")
                return -1
        total_seconds = (days * 86400) + (hours * 3600) + (minutes * 60) + seconds + (millisec / 1000)
        return total_seconds
    else:
        # print(f"No substrings found in '{string}'")
        return string
      
def get_pgbadger_tables_schema():
    return {
        "Queries by Application" : {
            "html_id" : "queries-by-application",
            "sort_by": "Avg Duration",
            "limit":100,
            "schema":{
                    "merge_on_cols" : ["Application","Request type"],
                    "compare_cols":["Count","Avg Duration"]
                },
            "type_cast":{
                "Count":int
            }
        },
        "Queries by Type" : {
            "html_id" : "queries-by-type",
            "sort_by": "Count",
            "limit":100,
            "schema":{
                    "merge_on_cols" : ["Type"],
                    "compare_cols":["Count"]
                },
            "type_cast":{
                "Count":int
            }
        },
        "Queries by Database" : {
            "html_id" : "queries-by-database",
            "sort_by": "Avg Duration",
            "limit":100,
            "schema":{
                    "merge_on_cols" : ["Request type"],
                    "compare_cols":["Count","Avg Duration"]
                },
            "type_cast":{
                "Count":int
            }
        },
        "Queries by User" : {
            "html_id" : "queries-by-user",
            "sort_by": "Avg Duration",
            "limit":100,
            "schema":{
                    "merge_on_cols" : ["User","Request type"],
                    "compare_cols":["Count","Avg Duration"]
                },
            "type_cast":{
                "Count":int
            }
        },
        "Queries by host" : {
            "html_id" : "queries-by-host",
            "sort_by": "Avg Duration",
            "limit":100,
            "schema":{
                    "merge_on_cols" : ["Host","Request type"],
                    "compare_cols":["Count","Avg Duration"]
                },
            "type_cast":{
                "Count":int
            }
        },
        "Histogram of Query Times" : {
            "html_id" : "histogram-query-times",
            "schema":{
                    "merge_on_cols" : ["Range"],
                    "compare_cols":["Count"]
                },
            "type_cast":{
                "Count":int
            }
        },
        "General Activity Queries" : {
            "html_id" : "general-activity-queries",
            "sort_by": "Avg duration",
            "limit":200,
            "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[]
                },
            "type_cast":{
                "Count":int
            }
        },
        "General Activity Read Queries" : {
            "html_id" : "general-activity-select-queries",
            "sort_by": "Average Duration",
            "limit":200,
            "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[]
                },
            "type_cast":{
                "SELECT":int
            }
        },
        
        "General Activity Write Queries" : {
            "html_id" : "general-activity-write-queries",
            "sort_by": "Average Duration",
            "limit":200,
            "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[]
                },
            "type_cast":{
                "INSERT":int,
                "UPDATE":int,
                "DELETE":int
            }
        },
        "Log Levels" : {
            "html_id" : "log-levels",
            "schema":{
                    "merge_on_cols" : ["Type"],
                    "compare_cols":["Count"]
                },
            "type_cast":{
                "Count":int
            }
        },
        
    }

def fill_null(df):
    columns = df.columns
    for col in columns:
        series = df[col]
        prev=None
        for n,i in enumerate(series):
            if i!="":
                prev=i
            else:
                series[n]=prev
        df[col]=series
    return df

def scrape_func(path,db):
    with open(path, 'r') as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    total_result={}
    all_tables = get_pgbadger_tables_schema()
    for heading,value in all_tables.items():
        print(f"************************** {heading} : {db} **************************")
        try:
            div_element = soup.find('div', id=value["html_id"])
            table_element = div_element.find('table')
            tbody = table_element.find('tbody')
            if not tbody:
                continue

            # Extract table headers
            headers = [header.text.strip() for header in table_element.find_all('th')]
            if not headers:
                print(f"Skipping table without headers")
                continue

            # Extract table rows
            rows = []
            for row in tbody.find_all('tr'):
                row_data = [val.text.strip() for val in row.find_all('td')]
                if len(row_data) == len(headers):  # Check if number of columns matches headers
                    rows.append(row_data)
                else:
                    print(f"Number of columns not mathcing number of headers for {heading}")

            if rows:
                df = pd.DataFrame(rows, columns=headers)
                if df.empty : continue
                df = fill_null(df)
                for column in df.columns:
                    df[column]=df[column].apply(convert_to_seconds)
                for col,typ in value["type_cast"].items():
                    df[col] = df[col].apply(lambda x: int(x.replace(',', '')))
                    df[col] = df[col].astype(typ)

                if "Duration" in df.columns and "Count" in df.columns:
                    try:
                        df["Avg Duration"] = df["Duration"]/df["Count"]
                    except Exception as e:
                        print(f"Error while calculating avg duration for {heading}:{db}. {e}")
                        print(df)
                        df["Avg Duration"] = df["Duration"]/1
                try:
                    df=df.sort_values(by=value["sort_by"],ascending=False)
                    df=df.head(value["limit"])
                except Exception as e:
                    print(f"sort and limit params not found for {heading}:{db}")
                print(df)
                total_result[db+" : "+heading] = {
                    "schema":value["schema"],
                    "table":df.to_dict(orient="records")
                }
            else:
                print(f"No valid rows found in table {heading}")
        except Exception as e:
            print("Error : " ,e)
    return total_result

if __name__=="__main__":
    path = "/Users/masabathulararao/Documents/Loadtest/pgbadger_im/pgbadger_report_configdb.html"
    scrape_func(path,"configdb")
    