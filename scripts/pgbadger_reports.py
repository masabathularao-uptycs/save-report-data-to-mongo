import json
import requests
import re
class pgbadger:
    def __init__(self,base_url,start_time,end_time,load_name):
        self.base_url=base_url
        self.start_time=start_time,
        self.end_time=end_time,
        self.load_name=load_name
        
    def get_pg_badger_report(self):
        url = self.base_url+"/ondemand"
        resp = requests.get(url, verify=False)
        report_name=self.load_name+'.txt'
        report_link=""
        if resp.status_code == 200:
            form_data = {
                'start':self.start_time, 
                'end': self.end_time,
                'filename': report_name
            }
            response = requests.post(url, data=form_data, verify=False)

            if response.status_code == 200:
                report_link=self.base_url+f'/reports/view?file=/opt/uptycs/etc/elk/ondemand_reports/{report_name}/postgres.html'
                print("generated link:",report_link)
            else:
                print(f"Error generating report: {response.status_code}")
        else:
            print(f"Error accessing the page: {resp.status_code}")
            
        return report_link

