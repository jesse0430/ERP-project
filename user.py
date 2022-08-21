from flask_restful import Resource, request
from flask import json, Response
from flask_apispec import use_kwargs
from flask_jwt_extended import create_access_token, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine
from typing import Any, Dict, Optional
from datetime import datetime,timedelta
import pymysql, sqlalchemy, io
import pandas as pd

from model import *

def get_access_token(account):
    token = create_access_token(
        identity= account,
        expires_delta=timedelta(days=1)
    )
    return token

def db_init():
    db = pymysql.connect(
        host='*****',
        user='*****',
        password='*****',
        db='sales'
    )
    cursor = db.cursor(pymysql.cursors.DictCursor)
    return db, cursor

data_list=[]
def get_data(target): #抓名字或員編
    db, cursor=db_init()
    sql=f"SELECT DISTINCT {target} FROM `me_IT`;"
    cursor.execute(sql)
    all=cursor.fetchall()
    db.close()
    for x in range(len(all)):
        data_list.append(all[x][target])
    return data_list


#設置headers配置及生成文件名稱
def generate_download_headers(extension:str, filename: Optional[str]=None) -> Dict[str,Any]:
    filename=filename if filename else datetime.now().strftime('%Y%m%d_%H%M%S')
    content_disp=f"attachment; filename={filename}.{extension}"
    headers={'Content-Disposition': content_disp}
    return headers

#登入對po_number跟password核對
class Login(Resource):
    @use_kwargs(LoginRequest, location='json')
    def post(self, **kwargs):
        db, cursor = db_init()
        account, password = kwargs["PO_Number"], kwargs["Passwd"]
        token = get_access_token(account)
        try:
            if account in get_data('PO_Number'):
                sql = f"SELECT Passwd , Role ,Team FROM `me_IT` where PO_Number='{account}';"
                cursor.execute(sql)
                user = cursor.fetchall()
                if len(user)==0:
                    return {'message':'password not exists in database'}
                else:
                    passwd=user[0]['Passwd']
                    sql = f"SELECT PO_Name FROM `me_IT` WHERE PO_Number='{account}';"
                    cursor.execute(sql)
                    name = cursor.fetchall()[0]['PO_Name']
                    role = user[0]['Role']
                    team=user[0]['Team']
                    db.close()
                    result = check_password_hash(passwd, password)
                    if result==1:
                        return {'status':'01',
                                'user':name,
                                'token':token,
                                'role':role,
                                'team':team}, 200
                    else:
                        return {'message':'Password invalid'}, 404
            else:
                return {'message': 'PO_Number not found'}, 404    
        except Exception as e:
            return {'message':str(e)}


class Orders(Resource):
    @jwt_required()
    def get(self,action):
        if action=='Orders': #supervisor&boss查看所有訂單(with profit and cost)
            try:
                db, cursor=db_init()
                sql="SELECT * FROM `sales` where not delete_by_sales='YES';"
                cursor.execute(sql)
                orders=cursor.fetchall()
                db.close()
                message = json.dumps(orders,ensure_ascii=False)
                return Response(message, status=200,mimetype='application/json')
            except Exception as e:
                return {'message':str(e)}
        if action=='Order': #sales查看所有訂單(without profit and cost)
            try:
                db, cursor=db_init()
                sql="SELECT * FROM `sales` where not delete_by_sales='YES';"
                cursor.execute(sql)
                orders=cursor.fetchall()
                for x in range(len(orders)):
                    del orders[x]['Profit(USD)'] 
                    del orders[x]['cost(USD)']
                db.close()
                message = json.dumps(orders,ensure_ascii=False)
                return Response(message, status=200,mimetype='application/json')
            except Exception as e:
                return {'message':str(e)}
        if action=='Count': #老闆看訂單總數
            try:
                db, cursor=db_init()
                sql="SELECT COUNT(Purchase_Order_Number) FROM `sales` WHERE NOT delete_by_sales='YES';"
                cursor.execute(sql)
                all=cursor.fetchall()[0]["COUNT(Purchase_Order_Number)"]
                db.close()
                message = json.dumps({'all_order_count':all},ensure_ascii=False)
                return Response(message, status=200,mimetype='application/json')
            except Exception as e:
                return {'message':str(e)}

        if action=='A_count' or action=='B_count': #查看team的總訂單數
            try:
                team=action[0]
                db, cursor=db_init()
                sql=f"SELECT COUNT(Purchase_Order_Number) FROM `sales` WHERE Team='{team}' and NOT delete_by_sales='YES';"
                cursor.execute(sql)
                number=cursor.fetchall()[0]["COUNT(Purchase_Order_Number)"]
                db.close()
                mess={"team_count":number}
                message = json.dumps(mess,ensure_ascii=False)
                return Response(message, status=200,mimetype='application/json')
            except Exception as e:
                return {'message':str(e)}

        if action=="A_order" or action=='B_order': #看team的總訂單
            try:
                team=action[0]
                db, cursor=db_init()
                sql=f"SELECT * FROM `sales` WHERE Team='{team}' AND NOT delete_by_sales='YES';"
                cursor.execute(sql)
                A=cursor.fetchall()
                db.close()
                message = json.dumps(A,ensure_ascii=False)
                return Response(message, status=200,mimetype='application/json')
            except Exception as e:
                return {'message':str(e)}
        if action=="A_status" or action=="B_status": #team的三種狀態數量
            try:
                team=action[0]
                db, cursor=db_init()
                sql=(f"SELECT Status, COUNT(Status) FROM `sales` WHERE Team='{team}' AND NOT delete_by_sales='YES' GROUP BY Status;")
                cursor.execute(sql)
                data=cursor.fetchall()
                if len(data)==3:
                    status=[{data[0]['Status']:data[0]['COUNT(Status)']},{data[1]['Status']:data[1]['COUNT(Status)']},{data[2]['Status']:data[2]['COUNT(Status)']}]
                elif len(data)==2:
                    for a in three:
                        for b in range(len(data)):
                            if data[b]['Status']==a:
                                status.append({a:data[b]['COUNT(Status)']})
                            else:
                                pass
                    for x in range(len(status)):
                        key=status[x].keys()
                        for y in three:
                            if y in key:
                                three.remove(y)
                    status.append({three[0]:0})

                else:
                    three=['ACTIVE','OVERDUE','EXPIRED']
                    for a in three:
                        if data[0]['Status']==a:
                            status.append({a:data[0]['COUNT(Status)']})
                            three.remove(a)
                    for x in range(len(three)):
                        status.append({three[x]:0})
                db.close()
                message = json.dumps(status,ensure_ascii=False)
                return Response(message, status=200,mimetype='application/json')
            except Exception as e:
                return {'message':str(e)}
    @use_kwargs(Vague_search, location='json')
    def post(self,action,**kwargs):
        if action=='Search': #訂單模糊查詢
            try:
                Team=kwargs['Team']
                PO_Name=kwargs['PO_Name']
                PO_Number=kwargs['PO_Number']
                Role=kwargs['Role']
                if Role=='Boss' or Role=='supervisor_a' or Role=='supervisor_b':
                    db, cursor=db_init()
                    sql=f"SELECT * FROM `sales` where PO_Name='{PO_Name}' AND Team='{Team}' AND Purchase_Order_Number LIKE '%{PO_Number}%';"
                    cursor.execute(sql)
                    order=cursor.fetchall()
                    if len(order)!=0:
                        db.close()
                        message = json.dumps(order,ensure_ascii=False)
                        return Response(message, status=200,mimetype='application/json')
                    else:
                        return {'message':'no data'}
                if Role=='staff': #原編模糊查詢
                    db, cursor=db_init()
                    sql=f"SELECT * FROM `sales` where PO_Name='{PO_Name}' AND Team='{Team}' AND Purchase_Order_Number LIKE '%{PO_Number}%';"
                    cursor.execute(sql)
                    order=cursor.fetchall()
                    for x in range(len(order)):
                        del order[x]['Profit(USD)'] 
                        del order[x]['cost(USD)']
                    if len(order)!=0:
                        db.close()
                        message = json.dumps(order,ensure_ascii=False)
                        return Response(message, status=200,mimetype='application/json')
                    else:
                        return {'message':'no data'}
            except Exception as e:
                return {'message':str(e)}
class Sales(Resource):
    @jwt_required()
    def get(self, username, action):
        if action=="orders": #查看該使用者總潛在訂單
            try:
                if username in get_data('PO_Name'):
                    db, cursor=db_init()
                    sql=(f"SELECT * FROM `sales` where PO_Name='{username}' AND NOT delete_by_sales='YES';")
                    cursor.execute(sql)
                    order=cursor.fetchall()
                    for x in range(len(order)):
                        del order[x]['Profit(USD)'] 
                        del order[x]['cost(USD)']
                    db.close()
                    message = json.dumps(order,ensure_ascii=False)
                    return Response(message, status=200,mimetype='application/json')
                return {'message': 'user not found'}, 404
            except Exception as e:
                return {'message':str(e)}
        if action=="count": #查看該使用者總潛在訂單數
            try:
                if username in get_data('PO_Name'):
                    db, cursor=db_init()
                    sql=(f"SELECT COUNT(Purchase_Order_Number) FROM `sales` WHERE PO_Name = '{username}' AND NOT delete_by_sales='YES';")
                    cursor.execute(sql)
                    order_count=cursor.fetchall()[0]['COUNT(Purchase_Order_Number)']
                    db.close()
                    return {'order_count':order_count}, 200
                return {'message': 'user not found'}, 404
            except Exception as e:
                return {'message':str(e)}
        if action=="amount": #查看該使用者總潛在訂單金額
            try:
                if username in get_data('PO_Name'):
                    db, cursor=db_init()
                    sql=(f"SELECT SUM(`Price(USD)`) FROM `sales` WHERE PO_Name= '{username}' AND NOT delete_by_sales='YES';")
                    cursor.execute(sql)
                    amount=cursor.fetchall()[0]['SUM(`Price(USD)`)']
                    db.close()
                    message = json.dumps({'amount':amount},ensure_ascii=False)
                    return Response(message, status=200,mimetype='application/json')
                elif username=='A' or username=='B': #當為A或B team時查看總金額
                    db, cursor=db_init()
                    sql=f"SELECT SUM(`Price(USD)`) FROM `sales` WHERE Team='{username}' AND NOT delete_by_sales='YES';"
                    cursor.execute(sql)
                    amount=cursor.fetchall()[0]['SUM(`Price(USD)`)']
                    db.close()
                    message = json.dumps({'amount':amount},ensure_ascii=False)
                    return Response(message, status=200,mimetype='application/json')
                elif username=='Boss': #老闆查看總金額
                    db, cursor=db_init()
                    sql=(f"SELECT SUM(`Price(USD)`) FROM `sales` WHERE NOT delete_by_sales='YES';")
                    cursor.execute(sql)
                    amount=cursor.fetchall()[0]['SUM(`Price(USD)`)']
                    db.close()
                    message = json.dumps({'total_amount':amount},ensure_ascii=False)
                    return Response(message, status=200,mimetype='application/json')
                else:
                    return {'message':'user not fount'}
            except Exception as e:
                return {'message':str(e)}
        if action=='status': #查看該使用者總潛在訂單三種狀態數量
            status=[]
            three=['ACTIVE','OVERDUE','EXPIRED']
            try:
                if username in get_data('PO_Name'):
                    db, cursor=db_init()
                    sql=(f"SELECT Status, COUNT(Status) FROM `sales` WHERE PO_Name='{username}' AND NOT delete_by_sales='YES' GROUP BY Status;")
                    cursor.execute(sql)
                    data=cursor.fetchall()
                    if len(data)==3:
                        status=[{data[0]['Status']:data[0]['COUNT(Status)']},{data[1]['Status']:data[1]['COUNT(Status)']},{data[2]['Status']:data[2]['COUNT(Status)']}]
            
                    elif len(data)==2:
                        for a in three:
                            for b in range(len(data)):
                                if data[b]['Status']==a:
                                    status.append({a:data[b]['COUNT(Status)']})
                                else:
                                    pass
                        for x in range(len(status)):
                            key=status[x].keys()
                            for y in three:
                                if y in key:
                                    three.remove(y)
                        status.append({three[0]:0})
                    else:
                        three=['ACTIVE','OVERDUE','EXPIRED']
                        for a in three:
                            if data[0]['Status']==a:
                                status.append({a:data[0]['COUNT(Status)']})
                                three.remove(a)
                        for x in range(len(three)):
                            status.append({three[x]:0})
                    db.close()
                    message = json.dumps(status,ensure_ascii=False)
                    return Response(message, status=200,mimetype='application/json')
                return {'message': 'user not found'}, 404
            except Exception as e:
                return {'message':str(e)}
        if action.upper()=='ACTIVE' or action.upper()=='OVERDUE' or action.upper()=='EXPIRED': #查看該使用者三種狀態訂單明細
            try:
                action2=action.upper()
                if username in get_data('PO_Name'):
                    db, cursor=db_init()
                    sql=(f"SELECT * FROM `sales` WHERE PO_Name= '{username}' AND Status='{action2}' AND NOT delete_by_sales='YES';")
                    cursor.execute(sql)
                    active=cursor.fetchall()
                    db.close()
                    for x in range(len(active)):
                        del active[x]['Profit(USD)'] 
                        del active[x]['cost(USD)']
                    if len(active)==0:
                        return {'message':f"no {action} order"}
                    else:
                        message = json.dumps(active,ensure_ascii=False)
                        return Response(message, status=200,mimetype='application/json')

                elif username =='All': #三種狀態的訂單明細
                    db, cursor=db_init()
                    sql=(f"SELECT * FROM `sales` where Status='{action2}';")
                    cursor.execute(sql)
                    orders=cursor.fetchall()
                    db.close()
                    message = json.dumps(orders,ensure_ascii=False)
                    return Response(message, status=200,mimetype='application/json')

                elif username =='TeamA' or username=='TeamB': #team各狀態的訂單
                    team=username[-1]
                    db, cursor=db_init()
                    sql=(f"SELECT * FROM `sales` WHERE Team='{team}' and Status='{action2}' and NOT delete_by_sales='YES';")
                    cursor.execute(sql)
                    orders=cursor.fetchall()
                    db.close()
                    message = json.dumps(orders,ensure_ascii=False)
                    return Response(message, status=200,mimetype='application/json')
            except Exception as e:
                return {'message':str(e)}
   
        if username=='Boss' and action=='profit': #老闆看利潤
            try:
                db, cursor=db_init()
                sql=(f"SELECT SUM(`Profit(USD)`) FROM `sales` WHERE NOT delete_by_sales='YES';")
                cursor.execute(sql)
                profit=cursor.fetchall()[0]['SUM(`Profit(USD)`)']
                db.close()
                message = json.dumps({'total_profit':profit},ensure_ascii=False)
                return Response(message, status=200,mimetype='application/json')
            except Exception as e:
                    return {'message':str(e)}

        if username=='A' or username=='B' and action=="profit": #查看team的利潤
            try:
                db, cursor=db_init()
                sql=(f"SELECT SUM(`Profit(USD)`) FROM `sales` WHERE Team='{username}' and NOT delete_by_sales='YES';")
                cursor.execute(sql)
                profit=cursor.fetchall()[0]['SUM(`Profit(USD)`)']
                db.close()
                message = json.dumps({'team_profit':profit},ensure_ascii=False)
                return Response(message, status=200,mimetype='application/json')
            except Exception as e:
                    return {'message':str(e)}

#業務刪除或完成取消訂單
class Adjustment(Resource):
    @use_kwargs(OrderAdjustment, location='json')
    @jwt_required()
    def post(self, order,**kwargs):
        if order=='Delete':
            try:
                db, cursor = db_init()
                Purchase_Order_Number = kwargs["Purchase_Order_Number"]
                for x in Purchase_Order_Number:
                    sql=f"UPDATE sales SET delete_by_sales='YES' WHERE Purchase_Order_Number='{x}';"
                    result=cursor.execute(sql)
                    db.commit()
                    if result!=1:
                        return {'message':f"{x} deletion failure 02"}
                db.close()
                return {'status':"01"}, 200
            except Exception as e:
                return {'message':str(e)}
        if order=='Move':
            try:
                db, cursor = db_init()
                order_number = kwargs["Purchase_Order_Number"]
                for x in order_number:
                    sql=f"INSERT INTO `sales_can` SELECT * FROM `sales` WHERE Purchase_Order_Number='{x}';"
                    cursor.execute(sql)
                    db.commit()
                db.close()
                return {'status':"01"}, 200
            except Exception as e:
                return {'message':str(e)}
    #獲取業務編輯的訂單
class Select(Resource):
    @use_kwargs(Select_orders, location='json')
    @jwt_required()
    def post(self,**kwargs):
        db, cursor = db_init()
        if kwargs.get('Start') !=None:
            try:
                Start=kwargs.get('Start')
                End=kwargs.get('End')
                Name=kwargs['Name']
                Reseller=kwargs['Reseller']
                sql=f"SELECT * FROM `test` where PO_Name='{Name}' and Reseller='{Reseller}' and '{Start}'<=Renewal_Date and Renewal_Date <= '{End}';"
                cursor.execute(sql)
                users=cursor.fetchall()
                for x in range(len(users)):
                        del users[x]['Profit(USD)'] 
                        del users[x]['cost(USD)']
                if len(users)==0:
                    return {"message":"no data"}
                else:
                    message = json.dumps(users,ensure_ascii=False)
                    return Response(message, status=200,mimetype='application/json')
            except Exception as e:
                return {'message':str(e)}
        else:
            try:
                Name=kwargs['Name']
                Reseller=kwargs['Reseller']
                sql=f"SELECT * FROM `test` where PO_Name='{Name}' and Reseller='{Reseller}';"
                cursor.execute(sql)
                users=cursor.fetchall()
                if len(users)==0:
                    return {"message":"no data"}
                else:
                    message = json.dumps(users,ensure_ascii=False)
                    return Response(message, status=200,mimetype='application/json')
            except Exception as e:
                return {'message':str(e)}

class Search_user(Resource): #模糊搜尋使用者
    @use_kwargs(Search_user, location='json')
    def post(self,**kwargs):
        try:
            column=list(kwargs.keys())[0]
            word=list(kwargs.values())[0]
            db, cursor = db_init()
            sql=f"SELECT PO_Number,PO_Name,Email,Dept,Team FROM `me_IT` where {column} LIKE '%{word}%';"
            cursor.execute(sql)
            result=cursor.fetchall()
            db.commit()
            db.close()
            message = json.dumps(result,ensure_ascii=False)
            return Response(message, status=200,mimetype='application/json')
        except Exception as e:
            return {'message':str(e)}

class AllUser(Resource): #查看全部使用者資料
    def get(self):
        try:
            db, cursor = db_init()
            sql="SELECT PO_Number,PO_Name,Email,Dept,Team FROM `me_IT`;"
            cursor.execute(sql)
            users=cursor.fetchall()
            message = json.dumps(users,ensure_ascii=False)
            db.close()
            return Response(message, status=200,mimetype='application/json')
        except Exception as e:
            return {'message':str(e)}

#新增使用者
class Add_user(Resource):
    @use_kwargs(AddUser,location='json')
    def post(self,**kwargs):
        try:
            order=str(get_data('PO_Number')[-1]+1)[1:]
            hashed_password = generate_password_hash(order)
            team=kwargs["Team"]
            dept=kwargs["Dept"]
            name=kwargs["PO_Name"]
            email=kwargs["Email"]
            role=kwargs['Role']
            db, cursor = db_init()
            sql=f"INSERT INTO `me_IT` (PO_Name, Email, Passwd, Dept, Team, Role) VALUES ('{name}', '{email}', '{hashed_password}','{dept}','{team}','{role}');"
            result=cursor.execute(sql)
            db.commit()
            db.close()
            return {"status":"01","PO_Number":name}
        except Exception as e:
            return {'message':str(e)}
#更新使用者資料
class Update_user(Resource):
    @use_kwargs(UpdateUser, location='json')
    def patch(self,**kwargs):
        db, cursor = db_init()
        password=kwargs.get("Passwd")
        if password != None:
            hashed_password = generate_password_hash(password)
        else:
            hashed_password = None
        user={"Passwd":hashed_password,
            "Team":kwargs.get("Team"),
            "Dept":kwargs.get("Dept"),
            "PO_Name":kwargs.get("PO_Name"),
            "Role":kwargs.get("Role")
            }
        data=[]
        keys=[]
        try:
            for key, value in user.items():
                if value is not None:
                    dic={key:value}
                    keys.append(dic)
                    data.append(f"{key} = '{value}'")
            data = ",".join(data)
            number=kwargs["PO_Number"]
            sql=f"UPDATE `me_IT` SET {data} WHERE PO_Number = '{number}';"
            result = cursor.execute(sql)
            db.commit()
            db.close()
            if result==1:
                return {"status":'01','po_number':kwargs["PO_Number"]}
            else:
                return {"message":"cannot update 02"}
        except Exception as e:
            return {'message':str(e)}

#刪除使用者
class Delete_user(Resource):
    @use_kwargs(DeleteUser, location='json')
    def post(self, **kwargs):
        po_list=[]
        try:
            po_number_list=kwargs["PO_Number"]
            db, cursor = db_init()
            for x in po_number_list:
                po_list.append(x)
                sql=f"UPDATE `me_IT` SET Passwd=null, Team=null, Dept=null WHERE PO_Number= '{x}';"
                result = cursor.execute(sql)
                db.commit()
            return {"status":'01','po_number':po_list[0]}
        except Exception as e:
            return {'message':str(e)}

#上傳excel訂單
class Upload_order(Resource):
    @use_kwargs(Upload_orders,location="form")
    def post(self,**kwargs):
        try:
            file = request.files.get('file')
            result = pd.read_excel(file)
            engine = create_engine('mysql+pymysql://erp:erp@ec2-34-208-156-155.us-west-2.compute.amazonaws.com:3306/metaage_sales')
            result.to_sql('test',con=engine, index=False,if_exists='append')
            return {"status":'01'}
        except Exception as e:
            return {'message':str(e)}

# 匯出excel訂單
class Export_order(Resource):
    @use_kwargs(OrderAdjustment,location="json")
    def post(self, **kwargs):
        try:
            order_list=[]
            db, cursor = db_init()
            order_number = kwargs["Purchase_Order_Number"]
            for x in order_number:
                sql=f"SELECT * FROM `sales` where Purchase_Order_Number = '{x}';"
                cursor.execute(sql)
                order_list.append(cursor.fetchall()[0])
            df=pd.DataFrame(order_list)
            byte_file=io.BytesIO()
            writer=pd.ExcelWriter(byte_file, engine='xlsxwriter',date_format="YYYY-MM-DD")
            df.to_excel(excel_writer=writer, index=False, encoding='utf-8-sig', sheet_name='sheet1')
            writer.save()
            writer.close()
            excel_bin_data=byte_file.getvalue()
            return Response(excel_bin_data,status=200,headers=generate_download_headers('xlsx'),mimetype="application/x-xls")
        except Exception as e:
            return {'message':str(e)}
