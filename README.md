# Protovtor is a Python data conversion and validation library

[![Build Status](https://travis-ci.org/konglwbox/protovtor.svg?branch=master)](https://travis-ci.org/konglwbox/protovtor?branch=master)
[![Coverage Status](https://coveralls.io/repos/github/konglwbox/protovtor/badge.svg?branch=master)](https://coveralls.io/github/konglwbox/protovtor?branch=master)

Protovtor is a simple and flexible data conversion and validation library for Python. It is designed for converting and
validating data coming into Python such as JSON/YAML(or something else), and convert them to Python data-types.

Goals:
1. Simple to use.
2. Support complex data.
3. Provide useful error messages.

# Installation
Use pip or easy_install:  
`pip install protovtor`

Tested with Python 2.7, 3.3, 3.4, 3.5, 3.6.

# Quick start
```python
# coding: utf-8
from protovtor import (Protocol, StringField, IntegerField, FloatField, LengthLimitTextField, BooleanField,
                       DateTimeField, PlaceField, FieldList, UniqueFieldList, ProtocolField, validators)
import json

# The usage of 'Field' and 'Validator'.
# It is usually used for converting and validating fundamental type value.

f = StringField(validators=[validators.Length(min=0, max=4), validators.AnyOf(["9527", "8080"])])

value = 9527
f.process(value)

if f.validate():
    assert f.value == "9527"

value = 9090
f.process(value)

if not f.validate():
    print(f.error)  # Must be one of ['9527', '8080']


# The usage of 'Protocol'.
# It is usually used for converting and validating composite type value.

class UserProto(Protocol):
    field_username = StringField(validators=[validators.DataRequired(), validators.Length(max=100)])
    field_age = IntegerField(validators=[validators.DataRequired(), validators.NumberRange(max=28)])
    # The 'discard=True' mean that the 'email' will not in the result data if 'nullable=True'.
    field_email = StringField(validators=[validators.DataRequired()], nullable=True, discard=True)
    field_phone = StringField(validators=[validators.DataRequired()], nullable=True, discard=False)
    # The 'sex' in result data will be used the default value if 'nullable=False'.
    field_sex = StringField(validators=[validators.AnyOf(["man", "woman"])], nullable=False, default="woman")


data = {"username": "VeVe", "age": 28, "email": None, "phone": None, "sex": None}

p = UserProto(data)
if p.validate():
    print(p.data)  # {'phone': None, 'age': 28, 'sex': 'woman', 'username': 'VeVe'}

data = {"username": "VeVe", "age": 30}  # You can omit the none values.

p = UserProto(data)
if not p.validate():
    print(p.error)  # {'age': 'Can not greater then 28'}


# A complex example.
# This example has been used most of the features.

class AppProto(Protocol):
    """
    App
    """
    field_name = StringField(validators=[validators.Length(max=200), validators.DataRequired()])
    field_version = StringField(validators=[validators.DataRequired()])


class OSProto(AppProto):
    """
    OS
    """
    field_apps = FieldList(
        ProtocolField(AppProto),
        validators=[validators.DataRequired()]
    )

    def post_validate(self, fields):
        """
        Overwrite super class's method. This method will be called before the method 'validate' returned.

        If you expect to have a custom validation with the fields, you should do it in this method.
        """
        # Get the field object by the key.
        field_version = fields["version"]
        # Get the value of the field.
        field_version_value = field_version.value

        # To have a custom validation.
        if int(field_version_value.split(".")[1]) < 13:
            # Remember to set 'error'.
            field_version.error = "The version is too old"
            return False

        return True


class CPUProto(Protocol):
    """
    CPU
    """
    field_processor = StringField(validators=[validators.DataRequired()])
    field_speed = FloatField(validators=[validators.AnyOf([2.3, 3.1])])


class DisplayProto(Protocol):
    """
    Display
    """
    field_type = StringField(validators=[validators.DataRequired()])
    field_resolutions = UniqueFieldList(
        StringField(validators=[validators.Regular("[\d]+ by [\d]+")]),
        validators=[validators.Length(min=3)]
    )
    field_ppi = IntegerField(validators=[validators.DataRequired()])


class ProductProto(Protocol):
    """
    Product
    """
    field_model = StringField(validators=[validators.Length(max=200), validators.DataRequired()])
    field_touch_bar = BooleanField()
    field_size = IntegerField(validators=[validators.AnyOf([13, 15])])
    field_os = ProtocolField(OSProto)
    field_cpu = ProtocolField(CPUProto)
    field_ssd = IntegerField(validators=[validators.NumberRange(min=128, max=512)])
    field_memory = IntegerField(validators=[validators.DataRequired()])
    field_display = PlaceField(ProtocolField(DisplayProto), handler=json.loads)
    field_buy_date = DateTimeField(format="%Y-%m-%d %H:%M:%S")
    field_doc = LengthLimitTextField(limit=10)

    def post_data(self, data):
        """
        Overwrite super class's method. This method will be called before the method 'data' returned.

        If you expect to convert the data structure or something else, you should do it in this method, because
        the parameter 'data' has been converted and validated successfully.
        """
        # Add an unit of 'G'.
        data["ssd"] = str(data["ssd"]) + "G"
        # To convert from 'GB' to 'MB'.
        data["memory"] = data["memory"] * 1024

        return data


data = {
    "model": "MacBook Pro",  # str, max length: 200, required: True.
    "touch_bar": True,  # bool.
    "size": 15,  # int, one of: (13, 15).
    "os": {  # dict.
        "name": "macOS",  # str, max length: 200, required: True.
        "version": "10.13.4",  # str, required: True; We expect to validate whether the version is old.
        "apps": [{  # list, required: True.
            "name": "Numbers",  # str, max length: 200, required: True.
            "version": "5.0.1"  # str, required: True.
        }, {
            "name": "Pages",
            "version": "7.0.1"
        }]
    },
    "cpu": {
        "processor": "Intel Core i5",  # str, required: True.
        "speed": 3.1  # float, one of: (2.3, 3.1).
    },
    "ssd": "256",  # int, min: 128, max: 512; We expect to add an unit of 'G'.
    "memory": "16",  # int, required: True; We expect to convert from 'GB' to 'MB'.
    "display": json.dumps({  # str; We expect to convert it from json string to dict.
        "type": "retina",  # str, required: True.
        "resolutions": [  # list, max length: 3; We expect to remove repeated value.
            "1680 by 1050",
            "1440 by 900",
            "1440 by 900",  # A repeated value.
            "1024 by 640"
        ],
        "ppi": 227  # int, required: True.
    }),
    "doc": "A very long Directions for use",  # str; We expect to cut more than 10 chars.
    "buy_date": "2018-05-21 16:50:06"  # datetime.
}

p = ProductProto(data)
if p.validate():
    print(p.data)
    # {
    #     "cpu": {
    #         "processor": "Intel Core i5",
    #         "speed": 3.1
    #     },
    #     "display": {
    #         "ppi": 227,
    #         "resolutions": [
    #             "1680 by 1050",
    #             "1024 by 640",
    #             "1440 by 900"
    #         ],
    #         "type": "retina"
    #     },
    #     "doc": "A very lon",
    #     "memory": 16384,
    #     "model": "MacBook Pro",
    #     "os": {
    #         "apps": [
    #             {
    #                 "name": "Numbers",
    #                 "version": "5.0.1"
    #             },
    #             {
    #                 "name": "Pages",
    #                 "version": "7.0.1"
    #             }
    #         ],
    #         "name": "macOS",
    #         "version": "10.13.4"
    #     },
    #     "size": 15,
    #     "ssd": "256G",
    #     "buy_date": datetime.datetime(2018, 5, 21, 16, 50, 6),
    #     "touch_bar": True
    # }


# Custom 'Field'.
# This is an example of how to customize a 'UpperStringField'.

class UpperStringField(StringField):
    def process(self, value):
        super(UpperStringField, self).process(value)

        self.value = self.value.upper()


f = UpperStringField()

value = "test"
f.process(value)

if f.validate():
    assert f.value == "TEST"


# Custom 'Validator'.
# This is an example of how to customize a 'UpperRequired'.

class UpperRequired(validators.Validator):
    def validate(self, value):
        if not value.isupper():
            raise ValueError("The value is not upper")


f = StringField(validators=[UpperRequired()])

value = "test"
f.process(value)

if not f.validate():
    print(f.error)  # The value is not upper
```