from flask import Flask, request
from db import DB


app = Flask(__name__)
db = DB("test")


@app.route("/logs", methods=["GET"])
def get_logs():
    data = db.getlogs()
    # return data,status, flags
    return {"message": "Name is required"}, 400


@app.route("/students", methods=["POST"])
def add_student():
    try:
        # 1. Capture data from the front-end form
        # 'name' and 'status' must match the 'name' attribute in your HTML <input>
        student_data = {
            "name": request.form.get("name"),
            "status": request.form.get("status"),
            "time": request.form.get("time"),
            "date": request.form.get("date")
            # "studentID": request.form.get("studentID"),
            # "major": request.form.get("major"),
            # "photoPath": request.form.get("photoPath")
        }

        # 2. Basic validation: don't upload if name is missing
        if not student_data["name"]:
            return {"message": "Name is required"}, 400

        # 3. Send to your DB class
        new_id = db.post_student(student_data)

        # 4. Return success! 201 means "Created"
        return {"message": "Student added", "id": str(new_id)}, 201

    except Exception as e:
        return {"message": f"Error: {str(e)}"}, 500


@app.route("/students/<id>", methods=["DELETE"])
def delete_student(id):
    try:
        result = db.delete_student(id)
        if result:
             return {"message": f"Student {id} deleted successfully"}, 200
        else:
             return {"message": "student not found in database"}, 404

    except Exception as e:
        return {"message": f"Error: {str(e)}"}, 500
    

def main():
    app.run()

main()


