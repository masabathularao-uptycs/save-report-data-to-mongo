import requests
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from time import sleep
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime, timedelta
import os
import pytz
from helper import save_html_page
from scrape_pgbadger_tables import scrape_func
from config_vars import LOCAL_PGBADGER_REPORT_PORT, PGBADGER_PORT
import socket

current_time = datetime.now()
current_time = current_time.strftime("%Y-%m-%d_%H:%M:%S")
print("Formatted current time:", current_time)

def get_links(elastic_url,start_time_ist_str, end_time_ist_str,pgbadger_reports_mount,check,stack_obj):
    url = f"http://{elastic_url}:{PGBADGER_PORT}/ondemand"

    resp = requests.get(url, verify=False)
    return_links={}
    if resp.status_code == 200:
        if check:
            dbs={"configdb"}
        else:
            dbs={"configdb","statedb","metastoredb","vaultdb"}#,"threatdb","rangerdb","prestogatewaydb"}
        for db in dbs :
            start_end_string=f"{current_time}_{start_time_ist_str.replace('T','_')}_to_{end_time_ist_str.replace('T','_')}"
            report_name=f"{start_end_string}_{db}"
            # report_name=f"sprint_{db}"
            stack_obj.log.info(report_name)
            form_data={
                    "start": start_time_ist_str,
                    "end": end_time_ist_str,
                    "filename": report_name,
                    "database": db
                    }
            response = requests.post(url, data=form_data, verify=False)

            if response.status_code == 200:
                sleep(10)
                report_link=f'http://{elastic_url}:{PGBADGER_PORT}/reports/view?file=/{pgbadger_reports_mount}/ondemand_reports/{report_name}/postgres.html'
                stack_obj.log.info(report_link)   
                return_links[db]=report_link
            else:
                stack_obj.log.error(f"Error generating report for db {db}: {response.status_code}")
    else:
        stack_obj.log.error(f"Error accessing the page: {resp.status_code}")
    return return_links


def take_screenshots_and_save(report_links,BASE_PGBADGER_IMAGES_PATH):
    return_res={}
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--window-size=9999,9999')
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--enable-javascript")

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--dns-prefetch-disable")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--enable-features=NetworkServiceInProcess")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-features=VizDisplayCompositorAnxious")
    chrome_options.add_argument("--disable-features=VizDisplayCompositorGL")
    chrome_options.add_argument("--disable-features=NetworkService")
    chrome_options.add_argument("--disable-features=NetworkServiceInProcess")
    chrome_options.add_argument("--disable-features=NetworkServiceInProcess")
    chrome_options.add_argument("--disable-features=UseSurfaceLayerForVideo")

    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    for db,report_link in report_links.items():
        driver.get(report_link)
        partial_id = "menu"
        elements = driver.find_elements(by=By.XPATH, value=f"//ul[@class='nav navbar-nav']//li[contains(@id, '{partial_id}')]")
        stats_dict = {"Global Stats": "global-stats", "SQL Traffic": "sql-traffic", "Select Traffic": "select-traffic", "Write Traffic": "write-traffic", "Queries duration": "duration-traffic", "Prepared queries ratio": "prepared-queries-ratio", "General Activity": "general-activity", "Established connections": "established-connections", "Connections per database": "connections-per-database", "Connections per user": "connections-per-user", "Connections per host": "connections-per-host", "Simultaneous sessions": "simultaneous-sessions", "Histogram of sessions times": "histogram-session-times", "Sessions per database": "sessions-per-database", "Sessions per user": "sessions-per-user", "Sessions per host": "sessions-per-host", "Sessions per application": "sessions-per-app", "Checkpoints buffers": "checkpoints-buffers", "Checkpoints files": "checkpoints-files", "Checkpoints distance": "checkpoints-distance", "Checkpoint activity": "checkpoint-activity", "Checkpoint causes": "checkpoints-cause", "Size of temporary files": "tempfiles-size", "Number of temporary files": "tempfiles-number", "Temporary files activity": "tempfiles-activity", "Vacuums distribution": "vacuums-count", "Vacuums activity": "vacuums-activity", "Analyzes per Tables": "analyzes-per-table", "Vacuums per Tables": "vacuums-per-table", "Tuples removed": "tuples-removed-per-table", "Page removed": "pages-removed-per-table", "Locks by type": "locks-type", "Most frequent waiting queries (N)": "queries-most-frequent-waiting", "Queries that waited the most": "queries-that-waited-most", "Queries by type": "queries-by-type", "Queries by database": "queries-by-database", "Queries by user": "queries-by-user", "Duration by user": "duration-by-user", "Queries by host": "queries-by-host", "Queries by application": "queries-by-application", "Number of cancelled queries": "queries-cancelled-number", "Histogram of query times": "histogram-query-times", "Slowest individual queries": "slowest-individual-queries", "Time Consuming queries (N)": "time-consuming-queries", "Most frequent queries (N)": "most-frequent-queries", "Normalized slowest queries": "normalized-slowest-queries", "Time consuming prepare": "time-consuming-prepare", "Time consuming bind": "time-consuming-bind", "Log levels": "log-levels", "Events distribution": "minutes-errors-levels", "Most frequent errors/events (keys)": "most-frequent-errors-events"}
        for element in elements:
            try:
                ul_element = WebDriverWait(element, 10).until(
                    EC.presence_of_element_located((By.XPATH, ".//ul[@class='dropdown-menu'][li/a[@href]]"))
                )
                element.click()

                dropdown_options = ul_element.find_elements(By.TAG_NAME, 'li')
                option_texts = [option.text for option in dropdown_options if option.text != ""]
                
                for option_text in option_texts:
                    option = ul_element.find_element(By.XPATH, f"./li[a[text()='{option_text}']]")
                    try:
                        option.click()
                    except:
                        print("this block is interactive")
                    sleep(2)

                    if option_text in stats_dict:
                        print("Extracting details for : " , option_text)
                        id = stats_dict[option_text]
                        try:
                            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, id)))
                            # Additional strategies for headless mode
                            driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            actions = ActionChains(driver)
                            actions.move_to_element(element).click().perform()
                        except Exception as e:
                            print(f"Error clicking element: {e}")
                            element = driver.find_element_by_id(id)
                        sleep(2)
                        screenshot_path = f'{BASE_PGBADGER_IMAGES_PATH}/{id}_{db}.png'
                        return_res[f"{id}_{db}"]={}
                        # print(f"Saving '{option_text}' details to path {screenshot_path}")
                        element.screenshot(screenshot_path)
                    else:
                        print("not found", option_text)

            except TimeoutException:
                print("Dropdown menu not found within the specified time.")
    driver.quit()

    return return_res

def return_pgbadger_results(start_time_utc,end_time_utc,elastic_url,images_path):
    format_data = "%Y-%m-%dT%H:%M"

    start_time = start_time_utc - timedelta(minutes=10)
    start_time = start_time.strftime(format_data)
    end_time = end_time_utc + timedelta(minutes=10) + timedelta(hours=1)
    end_time = end_time.strftime(format_data)

    print("Converted start time UTC string is : " , start_time)
    print("Converted end time UTC string is : " , end_time)
    links=get_links(elastic_url , start_time, end_time)
    res=take_screenshots_and_save(links,images_path)
    return res

def get_and_save_pgb_html(stack_obj,elastic_url,base_save_path,pgbadger_tail_path,pgbadger_reports_mount,check=False):
    start_time_utc=stack_obj.start_time_UTC
    end_time_utc=stack_obj.end_time_UTC
    format_data = "%Y-%m-%dT%H:%M"
    return_file_names={}
    start_time = start_time_utc + timedelta(hours=1)
    start_time = start_time.strftime(format_data)
    end_time = end_time_utc + timedelta(hours=1)
    end_time = end_time.strftime(format_data)
    extracted_tables={}
    stack_obj.log.info(f"Converted start time UTC string is : {start_time}")
    stack_obj.log.info(f"Converted end time UTC string is : {end_time}")

    # Create a dummy socket connection
    # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # local_ip_address = "not_found"
    # try:
    #     # Connect to a remote host; doesn't need to be reachable
    #     s.connect(("8.8.8.8", 80))
    #     local_ip_address = s.getsockname()[0]
    # finally:
    #     s.close()

    local_ip_address = os.getenv('LOCAL_IP_ADDRESS')

    # Use the environment variable
    print(f"Local IP Address: {local_ip_address}")

    links=get_links(elastic_url , start_time, end_time,pgbadger_reports_mount,check,stack_obj)
    for db,link in links.items():
        stack_obj.log.info(f"Processing pgbadger report for database : {db}")
        save_path = os.path.join(base_save_path,f"pgbadger_report_{db}.html")
        status=save_html_page(link,save_path,check,stack_obj)
        if not status:
            if check :
                stack_obj.log.error(f"Could not save pgbadger html page for database {db}.")
                return False,link
            stack_obj.log.error("Saving this webpage failed, hence saving the direct link of pgbadger UI !")
            return_file_names[db] = link
        
        if status:
            if check:return True,"nothing"
            scraped_res = scrape_func(save_path,db,stack_obj)
            if scraped_res!={}:
                extracted_tables.update(scraped_res)
            return_file_names[db] = os.path.join(f"http://{local_ip_address}:{LOCAL_PGBADGER_REPORT_PORT}",pgbadger_tail_path,f"pgbadger_report_{db}.html")
    stack_obj.log.info(f"Returning pgbadger links dict : {return_file_names}")
    return return_file_names,extracted_tables

   

if __name__=="__main__":
    elastic_url="192.168.129.52"

    BASE_PGBADGER_IMAGES_PATH = os.path.join("/Users/masabathulararao/Documents/Loadtest",'pgbadger_im')
    os.makedirs(BASE_PGBADGER_IMAGES_PATH,exist_ok=True)
    from settings import stack_configuration
    
    variables = {
        "start_time_str_ist":"2024-08-17 22:13",
        "load_duration_in_hrs":10,
        "test_env_file_name":'s1_nodes.json'
    }
    stack_obj = stack_configuration(variables)

    pgbadger_links,extracted_tables= get_and_save_pgb_html(stack_obj,elastic_url,BASE_PGBADGER_IMAGES_PATH,"custom_path/sample","data")

    print(pgbadger_links)
    from pymongo import MongoClient
    # Create a sample DataFrame
    client = MongoClient('mongodb://localhost:27017/')
    db = client['Osquery_LoadTests']  # Replace 'your_database_name' with your actual database name
    collection = db['Testing']  # Replace 'your_collection_name' with your actual collection name

    collection.insert_one({"data":extracted_tables})
   