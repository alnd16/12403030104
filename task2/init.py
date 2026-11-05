# -*- coding: utf-8 -*-
"""task2 初始化：重置 inventory 与 orders（每个测试场景开始前单独调用）。
参数：Stock = 5 + C = 9，Buy = 1 + A = 2（SID=12403030104，S=4，A=1，C=4）。
"""
from pymongo import MongoClient

SID = "12403030104"
STOCK = 9          # 5 + C
BUY = 2            # 1 + A
BOOK_ID = "BOOK-" + SID

client = MongoClient("mongodb://127.0.0.1:27018/?directConnection=true")
db = client["exam_" + SID]
inventory = db["inventory"]
orders = db["orders"]

inventory.delete_many({})
inventory.insert_one({"_id": BOOK_ID, "title": "NoSQL数据库教材", "stock": STOCK})
orders.delete_many({})

print(f"初始化完成：{db.name} inventory.stock={inventory.find_one({'_id': BOOK_ID})['stock']}，"
      f"orders 数量 = {orders.count_documents({})}")
client.close()
