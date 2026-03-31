from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
from datetime import date
import glob
import os
import shutil
from datetime import datetime
from dotenv import load_dotenv

print(load_dotenv())
uri = os.environ.get("uri")
print(uri)


# Send a ping to confirm a successful connection
# try:
#     client.admin.command('ping')
#     print("Pinged your deployment. You successfully connected to MongoDB!")
# except Exception as e:
#     print(e)


# In Pandas, for x in df only loops through the Column Names (Name, Status, Time).
# By adding .iterrows(), you tell Pandas: "I want the data inside the rows, not the headers."
# index is the address or the label for each row.

# 等级：
# MongoDB:      Term:	                    Real-World Analogy	Access-Lite Example:
# Database	    The entire Office	        attendance_db
# Collection	A Drawer in the cabinet	    activity_logs
# Document	    A single piece of paper	    {"name": "jiaqi-7", "status": "Arrived"...}


# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["attendence"]
collection = db["Attendance-Logs"]

path = './CSVs/attendence_*.csv'
CSV_files = glob.glob(path)

for csv in CSV_files:
    print(f"Processing: {csv}")
    today = datetime.now().strftime('%Y-%m-%d')
    file_name = os.path.basename(csv)                               # getting actual date form the filename
    log_date = file_name.split('_')[1].replace('.csv', '')          # 把 date 从 file_name 里面摘出来
    try:
        df = pd.read_csv(csv)
        result = None

        current_date = date.today()
        for index, row in df.iterrows(): 
             
                document = {
                    "name": row["Name"],
                    "status": row["Status"],
                    "time": row["Time"],
                    "date": log_date                                    # 这里就可以用 log_date 了
                }
                if collection.count_documents(document) == 0:
                    result = collection.insert_one(document)
            
        if log_date != today:
            archive_folder = ('./Uploaded_Archive')
            os.makedirs(archive_folder, exist_ok=True)
            shutil.move(csv, os.path.join(archive_folder, file_name))
            print(f"Archived {file_name}")

        if result is None:
            print("No data was found in the CSV to upload.")
            
        else:
            print(f"Last record acknowledged: {result.acknowledged}")
            
    
    except Exception as e:
        raise Exception(
            "The following error occurred: ", e)
    
client.close()