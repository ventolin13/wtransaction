from __future__ import absolute_import, unicode_literals

from string import letters, digits
from datetime import datetime, timedelta
from flask import Flask, abort, after_this_request, request, g, url_for, Response

import simplejson as json

from mongoengine import *

from bson import ObjectId

def connect_db():
    connect("bincoin", "db")

class Transaction(Document):
    block_hash =                StringField()
    hash =                      StringField()
    address =                   StringField(required=True)
    amount =                    DecimalField(default=0, precision=8)

    #amount > 0
    vout =                      IntField()
    ins =                       ListField(default=[])
    is_spent =                  BooleanField(default=False)
    type =                      StringField()

    #amount < 0
    outs =                      ListField(default=[])
    in_hash =                   StringField(default="")
    in_created =                DateTimeField()
    fee =                       DecimalField(default=0, precision=8)
    dfee =                      DecimalField(default=0, precision=8)

    created =                   DateTimeField()

    meta = {
                # "indexes": [
                # {"fields": ["-created"]},
                # {"fields": ["hash"]},
                # {"fields": ["address"]},
                # ],
            "db_alias": "db"}

class Tx(Document):
    block_hash =                StringField()
    hash =                      StringField()
    fee =                       DecimalField(default=0, precision=8)
    ins =                       ListField()
    outs =                      ListField()
    created =                   DateTimeField()
    is_duplicate =              BooleanField(default=False)
    status =                    StringField(default="")

    meta = {
                # "indexes": [
                # {"fields": ["-created"]},
                # {"fields": ["hash"]}
                # ],
            "db_alias": "db"}

class Block(Document):
    num =                   IntField(unique=True)
    hash =                  StringField(unique=True)
    phash =                 StringField()
    nhash =                 StringField()
    mroot =                 StringField()
    vtx =                   ListField(default=[])
    created =               DateTimeField()
    lcreated =              DateTimeField(default=datetime.now)
    status =                StringField(default="new")

    meta = {
                # "indexes": [
                # {"fields": ["-num"], 'unique': True},
                # {"fields": ["hash"], 'unique': True}],
            "db_alias": "db"}

class Work(Document):
    main =                  StringField(default="on")
    block_try =             IntField(default=0)
    num =                   IntField(default=100)

    meta = {"db_alias": "db"}

