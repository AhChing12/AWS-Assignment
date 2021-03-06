from flask import Flask, render_template, request, jsonify,redirect
from pymysql import connections
from datetime import datetime
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

    #retrieve all employees information
    sql = "SELECT E.employeeId, E.firstName, E.lastName, E.gender, E.email, E.phoneNo, E.location, E.hireDate, P.positionName, D.departmentName from employee E INNER JOIN position P ON E.positionId = P.positionId INNER JOIN department D ON E.departmentId = D.departmentId"

    #executing query
    cursor.execute(sql)

    #fetching all records from database
    data=cursor.fetchall()
   
    return render_template('ManageEmp.html', data=data)

@app.route("/deleteEmp", methods=['POST'])
def deleteEmp():
    if request.form['delete']:
        employeeId = request.form['employee_id']

        #creating variable for connection
        cursor = db_conn.cursor(pymysql.cursors.DictCursor)

        #retrieve employee's image url
        cursor.execute("SELECT imageUrl from employee WHERE employeeId = %s", employeeId)

        #fetching all records from database
        data=cursor.fetchall()

        imageUrl = ""

        for item in data:
            imageUrl = item["imageUrl"]        

        #delete profile image from S3 bucket
        if imageUrl != None:
            imageUrl = imageUrl.split("/")
            s3 = boto3.client('s3')
            s3.delete_object(Bucket=custombucket, Key=imageUrl[3])

        #delete employee's record from database
        cursor.execute("DELETE FROM employee WHERE employeeId = %s", employeeId)
        db_conn.commit()

        cursor.close()

    return jsonify({ 'response': '1'}) 

@app.route("/userProfile", methods=['GET', 'POST'])
def userProfile():
    if request.args.get("employee_id") is not None or request.form['emp_id'] is not None:
        #creating variable for connection
        cursor=db_conn.cursor(pymysql.cursors.DictCursor)

        #retrieve employee information based on given employeeId
        sql = "SELECT E.employeeId, E.firstName, E.lastName, E.gender, E.email, E.phoneNo, E.location, E.hireDate, E.salary, E.primarySkill, E.imageUrl, P.positionName, D.departmentName from employee E INNER JOIN position P ON E.positionId = P.positionId INNER JOIN department D ON E.departmentId = D.departmentId WHERE E.employeeId = %s"

        #executing query
        if request.args.get("employee_id") is not None:
        	cursor.execute(sql, (request.args.get("employee_id")))
        else:
        	cursor.execute(sql, (request.form['emp_id']))

        #fetching all records from database
        data=cursor.fetchall()

    return render_template('GetEmpOutput.html', data=data)

@app.route("/getemp", methods=['GET', 'POST'])
def getEmp():
    return render_template('GetEmp.html')

@app.route("/attendance", methods=['GET','POST'])
def attendance():
    if request.method == 'GET':
        #creating variable for connection
        cursor=db_conn.cursor(pymysql.cursors.DictCursor)

        #retrieve attendance information based on given date
        sql = "SELECT * from attendance WHERE date = %s"

        #Check if date is given
        if request.args.get("date") != None and request.args.get("date") != "":
            cursor.execute(sql, request.args.get("date"))
        else:   
            #executing query
            cursor.execute(sql, datetime.now().strftime('%Y-%m-%d'))

        #fetching all records from database
        data=cursor.fetchall()

        if data:
        	#retrieve all employee's attendance information
            sql2 = "SELECT E.employeeId, E.firstName, E.lastName, E.gender, E.email, E.phoneNo, E.location, E.hireDate, P.positionName, D.departmentName, A.present, A.date from employee E INNER JOIN position P ON E.positionId = P.positionId INNER JOIN department D ON E.departmentId = D.departmentId INNER JOIN attendance A ON E.employeeId = A.employeeId WHERE A.date = %s"

            #Check if date is given
            if request.args.get("date") != None and request.args.get("date") != "":
                cursor.execute(sql2, request.args.get("date"))
            else:
                cursor.execute(sql2, datetime.now().strftime('%Y-%m-%d'))

            #fetching all records from database
            data=cursor.fetchall()

        else:
        	#retrieve all employees' id
            sql2 = "SELECT employeeId from employee"

            cursor.execute(sql2)

            data=cursor.fetchall()

            #Insert employee's attendance information
            sql3 = "INSERT INTO attendance VALUES (%s, %s, %s, %s)"

            for item in data:
                if request.args.get("date") != None and request.args.get("date") != "":
                    cursor.execute(sql3, (None, item["employeeId"], 0, request.args.get("date")))
                else:
                    cursor.execute(sql3, (None, item["employeeId"], 0, datetime.now().strftime('%Y-%m-%d')))

                db_conn.commit()

            #retrieve employees' attendance information based on given date
            sql4 = "SELECT E.employeeId, E.firstName, E.lastName, E.gender, E.email, E.phoneNo, E.location, E.hireDate, P.positionName, D.departmentName, A.present, A.date from employee E INNER JOIN position P ON E.positionId = P.positionId INNER JOIN department D ON E.departmentId = D.departmentId INNER JOIN attendance A ON E.employeeId = A.employeeId WHERE A.date = %s"

            #Check if date is given
            if request.args.get("date") != None and request.args.get("date") != "":
                cursor.execute(sql4, request.args.get("date"))
            else:
                cursor.execute(sql4, datetime.now().strftime('%Y-%m-%d'))
                    
            data=cursor.fetchall()

        return render_template('Attendance.html', data=data)

    else:
    	#check if filter by date is pressed
        if request.form['date'] != None and request.form['date'] != "":
            date = request.form['date']
            url = "/attendance?date=" + date

            return redirect(url)

        else:
            attendanceDate = request.form['attendance_date']

            #creating variable for connection
            cursor=db_conn.cursor(pymysql.cursors.DictCursor)

            checkBox = request.form.getlist('check')

            #Update selected employee's attendance status
            sql2 = "UPDATE attendance SET present = %s WHERE employeeId = %s AND date = %s"

            for x in checkBox:
                cursor.execute(sql2, (1, x, attendanceDate))
                db_conn.commit()

            #retrieve employees' attendance information based on given date
            sql3 = "SELECT E.employeeId, E.firstName, E.lastName, E.gender, E.email, E.phoneNo, E.location, E.hireDate, P.positionName, D.departmentName, A.present, A.date from employee E INNER JOIN position P ON E.positionId = P.positionId INNER JOIN department D ON E.departmentId = D.departmentId INNER JOIN attendance A ON E.employeeId = A.employeeId WHERE A.date = %s"
            cursor.execute(sql3, attendanceDate)
            data=cursor.fetchall()

            return render_template('Attendance.html', data=data)



        

@app.route("/manageEmp", methods=['GET', 'POST'])
def manageEmp():
    #creating variable for connection
    cursor=db_conn.cursor(pymysql.cursors.DictCursor)

    #retrieve all employees information
    sql = "SELECT E.employeeId, E.firstName, E.lastName, E.gender, E.email, E.phoneNo, E.location, E.hireDate, P.positionName, D.departmentName from employee E INNER JOIN position P ON E.positionId = P.positionId INNER JOIN department D ON E.departmentId = D.departmentId"

    #executing query
    cursor.execute(sql)

    #fetching all records from database
    data=cursor.fetchall()
   
    return render_template('ManageEmp.html', data=data)    

@app.route("/editEmp", methods=['GET','POST'])
def editEmp():
    if request.method == 'GET':
        if request.args.get("employee_id") is not None:
            #creating variable for connection
            cursor=db_conn.cursor(pymysql.cursors.DictCursor)

            #retrieve selected employee's information
            sql = "SELECT E.employeeId, E.firstName, E.lastName, E.age, E.gender, E.email, E.phoneNo, E.location, E.hireDate, E.salary, E.primarySkill, E.imageUrl, P.positionName, P.positionId, D.departmentName, D.departmentId from employee E INNER JOIN position P ON E.positionId = P.positionId INNER JOIN department D ON E.departmentId = D.departmentId WHERE E.employeeId = %s"

            #executing query
            cursor.execute(sql, (request.args.get("employee_id")))

            #fetching all records from database
            data=cursor.fetchall()

            return render_template('EditEmp.html', data=data)
    else:
    	#check if employee has changed the profile image
        if request.files['upload_image'].filename != '':
            employeeId = request.form['employee_id']
            firstName = request.form['first_name']
            lastName = request.form['last_name']
            age = request.form['age']
            phoneNo = request.form['phone_number']
            gender = request.form['gender_choice']
            email = request.form['email']
            address = request.form['address']
            primarySkill = request.form['pri_skill']
            department = request.form['department']
            position = request.form['position']
            dateHired = request.form['date_hired']
            salary = request.form['salary']
            profileImage = request.files['upload_image']
            departmentId = request.form['department_id']
            positionId = request.form['position_id']

            #change date format
            dateHired = datetime.strptime(dateHired, '%Y-%m-%d') 

            #creating variable for connection
            cursor=db_conn.cursor(pymysql.cursors.DictCursor)

            #check if the profile image is stored at S3
            if request.form['profile_image'] == 'yes_profile_image':
                #delete old profile image from S3 bucket
                imageUrl = request.form['old_image'].split("/")
                s3 = boto3.client('s3')
                s3.delete_object(Bucket=custombucket, Key=imageUrl[3])

            #update employee's information
            sql = "UPDATE employee SET firstName = %s, lastName = %s, age = %s, gender = %s, email = %s, phoneNo = %s, location = %s, hireDate = %s, salary = %s, primarySkill = %s, imageUrl = %s WHERE employeeId = %s"

            try:
                emp_image_file_name_in_s3 = "emp-id-" + str(employeeId) + "_image_file.jpg"

                # Uplaod image file in S3 #
                s3 = boto3.resource('s3')

                try:
                    print("Data inserted in MySQL RDS... uploading image to S3...")
                    s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=profileImage)
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
                    cursor.execute(sql, (firstName, lastName, age, gender, email, phoneNo, address, dateHired, salary, primarySkill, object_url, employeeId))
                    db_conn.commit()

                except Exception as e:
                    return str(e)

            except Exception as e:
                return str(e)        

            #update employee's department information
            sql2 = "UPDATE department SET departmentName = %s WHERE departmentId = %s"
            cursor.execute(sql2, (department, departmentId))
            db_conn.commit()

            #update employee's position information
            sql3 = "UPDATE position SET positionName = %s WHERE positionId = %s"
            cursor.execute(sql3, (position, positionId))
            db_conn.commit()
                            
            cursor.close()

        else:
            employeeId = request.form['employee_id']
            firstName = request.form['first_name']
            lastName = request.form['last_name']
            age = request.form['age']
            phoneNo = request.form['phone_number']
            gender = request.form['gender_choice']
            email = request.form['email']
            address = request.form['address']
            primarySkill = request.form['pri_skill']
            department = request.form['department']
            position = request.form['position']
            dateHired = request.form['date_hired']
            salary = request.form['salary']
            departmentId = request.form['department_id']
            positionId = request.form['position_id']

            #change date format
            dateHired = datetime.strptime(dateHired, '%Y-%m-%d') 

            #creating variable for connection
            cursor=db_conn.cursor(pymysql.cursors.DictCursor)

            #update employee's information
            sql = "UPDATE employee SET firstName = %s, lastName = %s, age = %s, gender = %s, email = %s, phoneNo = %s, location = %s, hireDate = %s, salary = %s, primarySkill = %s WHERE employeeId = %s"

            cursor.execute(sql, (firstName, lastName, age, gender, email, phoneNo, address, dateHired, salary, primarySkill, employeeId))
            db_conn.commit()

            #update employee's department information
            sql2 = "UPDATE department SET departmentName = %s WHERE departmentId = %s"
            cursor.execute(sql2, (department, departmentId))
            db_conn.commit()

            #update employee's position information
            sql3 = "UPDATE position SET positionName = %s WHERE positionId = %s"
            cursor.execute(sql3, (position, positionId))
            db_conn.commit()
                            
            cursor.close()

    return redirect("/manageEmp")

    
@app.route("/addempoutput", methods=['GET', 'POST'])
def addEmpOutput():
    return render_template('AddEmpOutput.html')


@app.route("/addemp", methods=['GET', 'POST'])
def AddEmp():
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
        data = cursor.fetchall()
        for item in data:
            emp_id = item["employeeId"] + 1
        #       End - Get last row's employeeId


        insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()

        if upload_image.filename == "":
            return "Please select a file"

        #hardcoded departmentId assignment
        if(department == "IT"):
            departmentId = 1
        elif (department == "HR"):
            departmentId = 2
        elif (department == "Finance"):
            departmentId = 3
        elif (department == "Marketing"):
            departmentId = 4

        #hardcoded positionId assignment
        if(position == "Programmer"):
            positionId = 1
        elif (position == "SE"):
            positionId = 2
        elif (position == "Technician"):
            positionId = 3
        elif (position == "HR Coordinator"):
            positionId = 4
        elif (position == "HR Specialist"):
            positionId = 5
        elif (position == "Recruiter"):
            positionId = 6
        elif (position == "Accountants"):
            positionId = 7
        elif (position == "Auditor"):
            positionId = 8
        elif (position == "Treasurer"):
            positionId = 9
        elif (position == "Marketing Analyst"):
            positionId = 10
        elif (position == "Marketing Coordinator"):
            positionId = 11
        elif (position == "Content Strategist"):
            positionId = 12

        try:
            emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file.jpg"
            
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
            phone_no=phone_no, gender=gender, img_src=object_url, email=email, address=address, pri_skill=pri_skill, 
            department=department, position=position, date_hired=date_hired, salary=float(salary), employeeId=emp_id)

    #if not POST or submit(Add) button
    return render_template('AddEmp.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
