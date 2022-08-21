from flask import Flask,jsonify
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException
from flask_cors import CORS

from user import *
#----------------------------------------------------
# import pymysql
# from flask_mail import Mail,Message
# from flask_apscheduler import APScheduler
# from apscheduler.schedulers.background import BackgroundScheduler
# from flask import current_app 
# import time
# from threading import Thread
# import smtplib
# import ssl
# from email.message import EmailMessage
# from user import *
#----------------------------------------------------

app=Flask(__name__)
JWTManager().init_app(app)
api=Api(app)
CORS(app)
app.config['Debug']=True
app.config['JWT_SECRET_KEY']='secret_key'
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['JSON_AS_ASCII'] = False
#----------------------------------------------------
# app.config.update(
#     MAIL_SERVER = 'smtp.gmail.com',
#     MAIL_PORT = '465',
#     MAIL_USE_SSL = True,
#     MAIL_USERNAME = '*****0@gmail.com',
#     MAIL_PASSWORD=  '*****',
#     MAIL_DEFAULT_SENDER= '*****0@gmail.com'
# )
# mail = Mail(app)
# email_sender='*****@gmail.com'
# email_password='*****'
# def db_init():
#     with app.app_context():
#       db = pymysql.connect(
#         host = '*****',
#         user = '*****',
#         password = '*****',
#         database='*****',
#         port = 3306
#     )
#       cursor = db.cursor(pymysql.cursors.DictCursor)
#       return db, cursor

# class Config(object):
#     SCHEDULER_API_ENABLED = True
#     SCHEDULER_TIMEZONE = 'Asia/Taipei'
# app.config.from_object(Config())
# scheduler = APScheduler(BackgroundScheduler(timezone='Asia/Taipei'))


# def send_async_email(app, msg):
#     with app.app_context():
#         mail.send(msg)
 
# def send_mail():
#     try:
#         with app.app_context():
#             db,cursor=db_init()
#             cursor.execute('SELECT`me_IT`.`Email`,`me_IT`.`PO_Number`,`sales`.`Purchase_Order_Number`,TIMESTAMPDIFF(DAY, now(),`sales`.`Renewal_Date`) AS daytype FROM `sales` INNER JOIN `me_IT` ON `me_IT`.`PO_Number`=`sales`.`PO_Number`HAVING daytype<=30 AND daytype>0;')
#             context = ssl.create_default_context()
#             with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
#                 smtp.login(email_sender, email_password)
#                 detail = cursor.fetchall()
#                 db.commit()
#                 for i in detail:
#                     msg = Message(subject='ERP',body='Hello ' + str(i['PO_Number'])+'Your purchase order number is '+str(i['Purchase_Order_Number'])+' Thanks For using our services.',recipients=[str(i['Email'])])
#                     Thread(target=mail.send(msg)).start() 
#             cursor.close()
#             db.close()    
#             print('job_cron1 executed') 
#     except Exception as e:
#         return {"message":str(e)}


# def UPDATE():
#     # with app.app_context():
#     db,cursor=db_init()
#     cursor.execute('UPDATE `me_boss`,`sales` SET `me_boss`.`PO_Number`=`sales`.`PO_Number`, `me_boss`.`PO_Name`=`sales`.`PO_Name`, `me_boss`.`Team`=`sales`.`Team`, `me_boss`.`Reseller`=`sales`.`Reseller`, `me_boss`.`End_Customer`=`sales`.`End_Customer`, `me_boss`.`type`=`sales`.`type`, `me_boss`.`Status`=`sales`.`Status`, `me_boss`.`delete_by_sales`=`sales`.`delete_by_sales`, `me_boss`.`Renewal_Date`=`sales`.`Renewal_Date`, `me_boss`.`Auto_Renewal_Term`=`sales`.`Auto_Renewal_Term`, `me_boss`.`Profit(USD)`=`sales`.`Profit(USD)`, `me_boss`.`cost(USD)`=`sales`.`cost(USD)`, `me_boss`.`take_a_cut(%)`=`sales`.`take_a_cut(%)`, `me_boss`.`Price(USD)`=`sales`.`Price(USD)` WHERE `me_boss`.`Purchase _Order_Number`=`sales`.`Purchase_Order_Number`;')
#     db.commit()
#     cursor.close()
#     db.close()    
#     print('job_cron2 executed') 
#----------------------------------------------------

#登入
api.add_resource(Login,'/Login') 

#業務操作訂單
api.add_resource(Adjustment,'/Adjust/<string:order>') 
api.add_resource(Select,'/Select') 


#IT操作
api.add_resource(AllUser,'/Users')
api.add_resource(Add_user,'/Add_user')
api.add_resource(Update_user,'/Update_user') #IT更新使用者資料
api.add_resource(Delete_user,'/Delete_user') #IT刪除使用者資料


api.add_resource(Orders,'/<string:action>')
api.add_resource(Sales,'/<string:username>/<string:action>') 
api.add_resource(Search_user,'/Search_user')

#訂單匯出匯入
api.add_resource(Upload_order,'/Upload_order') #匯入訂單
api.add_resource(Export_order,'/Export_order') #匯出訂單


@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    print(err)
    headers = err.data.get("headers", None)
    print(headers)
    messages = err.data.get("messages", ["Invalid request."])
    print(messages)
    if headers:
        return jsonify({"errors": messages}), err.code, headers
    else:
        return jsonify({"errors": messages}), err.code

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
#----------------------------------------------------
    # scheduler.add_job(func=send_mail,id='job_cron1', trigger='cron', day='*', hour=8 )
    # scheduler.add_job(func=UPDATE,id='job_cron2', trigger='cron', day='*', hour=8 )
    # # scheduler.add_job(func=UPDATE,id='job_cron2', trigger='interval', seconds=30, misfire_grace_time=900)
    # app.config.from_object(Config())
    # scheduler.init_app(app)
    # scheduler.start()
