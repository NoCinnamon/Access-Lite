import face_recognition
import pandas as pd
import pickle

def load_data():
    # ef ---> employee data file
    ef = pd.read_csv('./data-file/employee-log.csv')

    valid_encodings = []
    valid_ids = [] # Added this to track the IDs
    valid_firstName = []
    valid_lastName = []
    valid_statuses = []

    for index, row in ef.iterrows():
        path = row['File Name'] 
        try:
            img = face_recognition.load_image_file(path)
            encods = face_recognition.face_encodings(img)
       
        
            if len(encods) > 0:
                valid_encodings.append(encods[0])
                valid_ids.append(row['ID'])
                valid_firstName.append(row['First Name'])
                valid_lastName.append(row['Last Name'])
                valid_statuses.append(row['Status'])
            else:
                print(f"\nNo face detected in: {path}\n")

        except Exception as e:
            print(f"Error loading {path}: {e}")
    print("All faces processed. Freezing data with Pickle...")

    # Create a dictionary to hold lists
    data_to_save = {
        "encodings": valid_encodings,
        "ids": valid_ids,
        "firstName": valid_firstName,
        "lastName": valid_lastName,
        "statuses": valid_statuses
    }

    # Save the dictionary into one binary file
    with open("photo_database.pkl", "wb") as f:
        pickle.dump(data_to_save, f)

    print("photo_database.pkl saved succefully.")
    return True