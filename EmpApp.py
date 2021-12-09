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
        print(123)
        #creating variable for connection
        cursor=db_conn.cursor(pymysql.cursors.DictCursor)

        sql = "SELECT E.employeeId, E.firstName, E.lastName, E.gender, E.email, E.phoneNo, E.location, E.hireDate, E.salary, E.primarySkill, P.positionName, D.departmentName from employee E INNER JOIN position P ON E.positionId = P.positionId INNER JOIN department D ON E.departmentId = D.departmentId WHERE E.employeeId = %s"

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

#            BELOW IS ADDED CODE

@app.route("/addempoutput", methods=['GET', 'POST'])
def addEmpOutput():
    return render_template('AddEmpOutput.html')


@app.route("/addempbackup", methods=['GET', 'POST'])
def addEmpBackup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        age = request.form['age']
        phone_no = request.form['phone_number']
        gender = request.form['gender_choice']
        img_src = request.form['img_src']
        upload_image = request.files['upload_image']
        email = request.form['email']
        address = request.form['address']
        pri_skill = request.form['pri_skill']
        department = request.form['department']
        position = request.form['position']
        date_hired = request.form['date_hired']
        salary = request.form['salary']


        #       Begin - Get last row's employeeId
        cursor = db_conn.cursor(pymysql.cursors.DictCursor)
        #gets the last row's employeeId
        read_sql = "SELECT employeeId FROM employee ORDER BY employeeId DESC LIMIT 1"
        # cursor.execute(read_sql, (args=None))
        cursor.execute(read_sql)
        emp_id = cursor.fetchall()
        emp_id += 1
        #       End - Get last row's employeeId


        insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()

        if upload_image.filename == "":
            return "Please select a file"

        if(department == "IT"):
            departmentId = 1

        if(position == "Programmer"):
            positionId = 1

        try:
            emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file.jpg"
            # emp_name = "" + first_name + " " + last_name
            # Uplaod image file in S3 #
            s3 = boto3.resource('s3')

            try:
                print("Data inserted in MySQL RDS... uploading image to S3...")
                s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=upload_image)
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
                cursor.execute(insert_sql, (None, departmentId, positionId, first_name, last_name, age, gender, 
                    email, phone_no, pri_skill, address, object_url, date_hired, salary))
                db_conn.commit()

            except Exception as e:
                return str(e)

        finally:
            cursor.close()

        print("all modification done...")
        return render_template('AddEmpOutput.html', first_name=first_name, last_name=last_name, age=age, 
            phone_no=phone_no, gender=gender, img_src=img_src, email=email, address=address, pri_skill=pri_skill, 
            department=department, position=position, date_hired=date_hired, salary=salary)

    #if not POST or submit(Add) button
    
    return render_template('AddEmp(backUp).html')



#            END OF ADDED CODE



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

