# Setup and Install Report Generator tool
1. set ```REPORT_GENERATOR_ROOT_PATH``` environment variable in your machine.
<br>
    example : 
     ```
     sumonkey
     mkdir report_generator_project
     export REPORT_GENERATOR_ROOT_PATH=/opt/uptycs/report_generator_project
    ```

2. Navigate to  ```REPORT_GENERATOR_ROOT_PATH``` path, and git clone this repository 

<br>

(verify/make sure that the git cloned project directonay name is ```save-report-data-to-mongo```)

 ```
cd $REPORT_GENERATOR_ROOT_PATH
git clone https://github.com/masabathularao-uptycs/save-report-data-to-mongo.git
cd save-report-data-to-mongo 
 ```


3. install the ```mongo-report``` and ```load-report-generator``` docker contaiers by running :

```
docker-compose up -d
```
 (make sure docker is installed in your machine)

NOTE : This step builds the image in your machine. We will pushing the built image to a docker hub in furture which avoids building the image locally
---

# Collect your first report
1.  Enter into interactive mode 
```
git pull origin main (optional : run this if you want to fetch the latest changes)
docker exec -it load-report-generator bash   
```

2. Run the python script and enter required details to collect the report data and save to mongo:
```
python3 scripts/main.py
```

# Generate/View your first report

1. Open <your_host_ip:8012> url in browser of your choice.
2. Select the saved report(s) data to view/publish the performance load report.

---
