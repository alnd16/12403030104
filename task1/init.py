# -*- coding: utf-8 -*-
"""task1 初始化：建立 exam_<SID> 数据库的 courses 集合（与测试卷给定数据一致）。
初始化代码与业务操作代码分开；验证业务操作的重复执行效果时不再重新初始化。
"""
from pymongo import MongoClient

SID = "12403030104"

client = MongoClient("mongodb://127.0.0.1:27018/?directConnection=true")
exam_db = client["exam_" + SID]
courses = exam_db["courses"]

courses.delete_many({})
courses.insert_many([
    {
        "_id": "COURSE-" + SID + "-01",
        "title": "NoSQL数据库",
        "teacher": "张老师",
        "status": "OPEN",
        "chapters": [
            {"chapterId": "CH01", "title": "MongoDB基础", "hours": 2},
            {"chapterId": "CH02", "title": "Redis基础", "hours": 2},
        ],
    },
    {
        "_id": "COURSE-" + SID + "-02",
        "title": "数据库原理",
        "teacher": "张老师",
        "status": "CLOSED",
        "chapters": [
            {"chapterId": "CH01", "title": "关系模型", "hours": 2},
        ],
    },
    {
        "_id": "COURSE-" + SID + "-03",
        "title": "机器学习",
        "teacher": "李老师",
        "status": "OPEN",
        "chapters": [
            {"chapterId": "CH01", "title": "分类", "hours": 2},
            {"chapterId": "CH02", "title": "聚类", "hours": 2},
        ],
    },
])

print("初始化完成：", exam_db.name, "courses.count =", courses.count_documents({}))
client.close()
