from marshmallow import Schema, fields, validate


class LoginRequest(Schema):
    PO_Number=fields.Int(required=True,)
    Passwd=fields.Str(required=True,validate=[validate.Length(min=4,max=4)],)

class OrderAdjustment(Schema):
    Purchase_Order_Number=fields.List(fields.Str(validate=[validate.Length(min=10,max=10)]))

class UpdateUser(Schema):
    PO_Number=fields.Str(validate=[validate.Length(min=7,max=7)],require=True)
    Passwd=fields.Str(validate=[validate.Length(min=4,max=4)])
    Team=fields.Str(validate=[validate.Length(max=1)])
    Dept=fields.Str(validate=[validate.Length(max=5)])
    PO_Name=fields.Str()
    Role=fields.Str()

class AddUser(Schema):
    PO_Name=fields.Str(require=True)
    Team=fields.Str(validate=[validate.Length(max=1)],require=True)
    Dept=fields.Str(validate=[validate.Length(max=20)],require=True)
    Email=fields.Email(reqired=True)
    Role=fields.Str()

class DeleteUser(Schema):
    PO_Number=fields.List(fields.Str(validate=[validate.Length(min=7,max=7)]), required=True)

class Upload_orders(Schema):
    file = fields.Raw(type="file")

class Select_orders(Schema):
    Start=fields.Str(validate=[validate.Length(max=10)])
    End=fields.Str(validate=[validate.Length(max=10)])
    Name=fields.Str(required=True)
    Reseller=fields.Str(required=True)

class Vague_search(Schema):
    PO_Name=fields.Str(required=True)
    PO_Number=fields.Str(required=True)
    Team=fields.Str(validate=[validate.Length(max=1)],require=True)
    Role=fields.Str(required=True)

class Search_user(Schema):
    PO_Name=fields.Str()
    PO_Number=fields.Str()