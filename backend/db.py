from pymongo import MongoClient
from dotenv import load_dotenv
import os
from pathlib import Path
from bson.objectid import ObjectId


basedir = Path(__file__).resolve().parent.parent
env_path = basedir / '.env'
load_dotenv(dotenv_path=env_path)

class DB:
    def __init__(self,db_name):
        uri = os.getenv("uri")
        client = MongoClient(uri)
        self.db_name = db_name
        self.conection = client[db_name] # connection to the mongo database
    
    def getlogs(self):
        # get the connection read the stuff and put it in a list for each data entry
        collection = self.conection['Attendance-Logs']
        return list(collection.find())

    def post_student(self,data):
        # 1. Select the collection (matches your attendance project)
        collection = self.conection["Attendance-Logs"] 
        
        # 2. Insert the dictionary data into MongoDB
        result = collection.insert_one(data)
        
        # 3. Return the ID of the new document so Flask knows it worked
        return result.inserted_id

    def delete_student(self,student_id):
        collection = self.conection["Attendance-Logs"]
        result = collection.delete_one({"_id": ObjectId(student_id)})
        return result.acknowledged


