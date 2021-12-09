from flask import Flask, render_template, request, jsonify
from pymysql import connections
import os
import boto3
import pymysql
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    #creating variable for connection
    cursor=db_conn.cursor(pymysql.cursors.DictCursor)

    sql = "SELECT E.employeeId, E.firstName, E.lastName, E.gender, E.email, E.phoneNo, E.location, E.hireDate, P.positionName, D.departmentName from employee E INNER JOIN position P ON E.positionId = P.positionId INNER JOIN department D ON E.departmentId = D.departmentId"

    #executing query
    cursor.execute(sql)

    #fetching all records from database
    data=cursor.fetchall()
   
    return render_template('ManageEmp.html', data=data)

@app.route("/deleteEmp", methods=['POST'])
def deleteEmp():
    if request.form['delete']:
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM employee WHERE employeeId = %s", request.form['employee_id'])
        db_conn.commit()
        cursor.close()

    return jsonify({ 'response': '1'}) 

@app.route("/userProfile", methods=['GET', 'POST'])
def userProfile():
    if request.args.get("employee_id") is not None:
        #creating variable for connection
        cursor=db_conn.cursor(pymysql.cursors.DictCursor)

        sql = "SELECT E.employeeId, E.firstName, E.lastName, E.gender, E.email, E.phoneNo, E.location, E.hireDate, E.salary, E.primarySkill, E.imageUrl, P.positionName, D.departmentName from employee E INNER JOIN position P ON E.positionId = P.positionId INNER JOIN department D ON E.departmentId = D.departmentId WHERE E.employeeId = %s"

        #executing query
        cursor.execute(sql, (request.args.get("employee_id")))

        #fetching all records from database
        data=cursor.fetchall()

    return render_template('GetEmpOutput.html', data=data)

@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')

@app.route("/getemp", methods=['GET', 'POST'])
def getEmp():
    return render_template('GetEmp.html')

@app.route("/editEmp", methods=['GET','POST'])
def editEmp():
    if request.method == 'GET':
        if request.args.get("employee_id") is not None:
            #creating variable for connection
            cursor=db_conn.cursor(pymysql.cursors.DictCursor)

            sql = "SELECT E.employeeId, E.firstName, E.lastName, E.age, E.gender, E.email, E.phoneNo, E.location, E.hireDate, E.salary, E.primarySkill, E.imageUrl, P.positionName, D.departmentName from employee E INNER JOIN position P ON E.positionId = P.positionId INNER JOIN department D ON E.departmentId = D.departmentId WHERE E.employeeId = %s"

            #executing query
            cursor.execute(sql, (request.args.get("employee_id")))

            #fetching all records from database
            data=cursor.fetchall()

            return render_template('EditEmp.html', data=data)
    else
        employeeId = request.args.get("employee_id")
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        age = request.form['age']
        phoneNo = request.form['phoneNo']
        gender = request.form['gender_choice']
        email = request.form['email']
        address = request.form['address']
        primarySkill = request.form['primarySkill']
        department = request.form['department']
        position = request.form['position']
        dateHired = request.form['dateHired']
        salary = request.form['salary']
        profileImage = request.form['upload_image']

        print(employeeId)
        print(firstName)
        print(lastName)
        print(age)
        print(phoneNo)
        print(gender)
        print(email)
        print(address)
        print(primarySkill)
        print(department)
        print(position)
        print(dateHired)
        print(salary)
        print(profileImage)

        return render_template('ManageEmp.html')
            

@app.route("/deleteImg", methods=['GET','POST'])
def deleteImg():
    #creating variable for connection
    cursor=db_conn.cursor(pymysql.cursors.DictCursor)

    sql = "SELECT imageUrl from employee WHERE employeeId = %s"

    #executing query
    cursor.execute(sql, 4)

    #fetching all records from database
    data=cursor.fetchall()

    imageUrl = ""

    for item in data:
        imageUrl = item["imageUrl"]

    imageUrl = imageUrl.split("/")
    print(imageUrl)
    print(imageUrl[3])
    s3 = boto3.client('s3')
    s3.delete_object(Bucket=custombucket, Key=imageUrl[3])

    return render_template('ManageEmp.html')

@app.route("/fetchdata", methods=['POST'])
def getEmpInfo():
    emp_id = request.form['emp_id']
    first_name = ""
    last_name = ""
    location = ""

    cursor = db_conn.cursor()
    read_sql = "SELECT * FROM employee WHERE emp_id = %s"
    cursor.execute(read_sql, (emp_id))
    results = cursor.fetchall()

    for row in results:
        first_name = row[1]
        last_name = row[2]
        location = row[4]
        
    return render_template('GetEmpOutput.html', id=emp_id, fname=first_name, lname=last_name, interest=0, location=location)    

@app.route("/addemp", methods=['GET', 'POST'])
def AddEmp():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        pri_skill = request.form['pri_skill']
        location = request.form['location']
        emp_image_file = request.files['emp_image_file']
        value = None

        insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()

        if emp_image_file.filename == "":
            return "Please select a file"

        try:
            emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file.jpg"
            emp_name = "" + first_name + " " + last_name
            # Uplaod image file in S3 #
            s3 = boto3.resource('s3')

            try:
                print("Data inserted in MySQL RDS... uploading image to S3...")
                s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                s3_location = (bucket_location['LocationConstraint'])

                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location

                object_url = "https://{1}.s3{0}.amazonaws.com/{2}".format(
                    s3_location,
                    custombucket,
                    emp_image_file_name_in_s3)

                print(object_url)
                cursor.execute(insert_sql, (emp_id, 1, 1, first_name, last_name, value, value, value, value, pri_skill, location, object_url, value, value))
                db_conn.commit()

            except Exception as e:
                return str(e)

        finally:
            cursor.close()

        print("all modification done...")
        return render_template('AddEmpOutput.html', name=emp_name)
 
    return render_template('AddEmp.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
