from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
import pymysql
import sys
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
    print(request.form['delete'])
    return 1



@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')

@app.route("/getemp", methods=['GET', 'POST'])
def getEmp():
    return render_template('GetEmp.html')

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

@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
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

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
