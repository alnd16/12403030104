# -*- coding: utf-8 -*-
"""task1 业务操作：课程查询、章节局部更新、防重复新增、结果核验。
参数：SID=12403030104，S=04 -> S=4，A=1。
"""
from pymongo import MongoClient, ReturnDocument

SID = "12403030104"
S = 4          # 学号最后两位十进制
A = 1          # S mod 3
COURSE1 = "COURSE-" + SID + "-01"

client = MongoClient("mongodb://127.0.0.1:27018/?directConnection=true")
db = client["exam_" + SID]
courses = db["courses"]

print("=" * 60)
print("1. 查询由『张老师』授课且状态为 OPEN 的课程")
pipeline = [
    {"$match": {"teacher": "张老师", "status": "OPEN"}},
    {"$project": {
        "_id": 1,
        "title": 1,
        "chapterCount": {"$size": "$chapters"},
    }},
]
for doc in courses.aggregate(pipeline):
    print(f"课程编号: {doc['_id']} | 课程名称: {doc['title']} | 章节数量: {doc['chapterCount']}")

print("=" * 60)
print("2. 将 01 号课程 CH02 章节标题改为『Redis基础与应用-%d』（局部更新）" % S)
new_title = "Redis基础与应用-%d" % S
res = courses.update_one(
    {"_id": COURSE1, "chapters.chapterId": "CH02"},
    {"$set": {"chapters.$.title": new_title}},
)
print(f"matched={res.matched_count}, modified={res.modified_count}")
doc = courses.find_one({"_id": COURSE1})
for ch in doc["chapters"]:
    if ch["chapterId"] == "CH02":
        print("更新后 CH02 标题:", ch["title"])
print("更新后的完整课程文档:")
print(doc)

print("=" * 60)
print("3. 向 01 号课程新增 CH03（连续执行两次，防重复）")
new_chapter = {"chapterId": "CH03", "title": "Redis高级操作", "hours": 2 + A}
for i in (1, 2):
    res = courses.update_one(
        {"_id": COURSE1, "chapters": {"$not": {"$elemMatch": {"chapterId": "CH03"}}}},
        {"$push": {"chapters": new_chapter}},
    )
    print(f"第{i}次执行: matched={res.matched_count}, modified={res.modified_count}")

print("=" * 60)
print("4. 验证与解释")
doc = courses.find_one({"_id": COURSE1})
ch02_title = next(c["title"] for c in doc["chapters"] if c["chapterId"] == "CH02")
ch03_count = sum(1 for c in doc["chapters"] if c["chapterId"] == "CH03")
print("(1) 修改后 CH02 的标题:", ch02_title)
print("(2) 两次新增后 CH03 的数量:", ch03_count)
print("(3) 最终章节总数:", len(doc["chapters"]))
print("(4) teacher 是否保持原值:", doc["teacher"] == "张老师", "|", doc["teacher"])
print("    status  是否保持原值:", doc["status"] == "OPEN", "|", doc["status"])
print("""
解释：本题适合局部更新（$set 定位数组元素、$push/$not+$elemMatch 追加章节）：
(1) 只修改目标字段，teacher/status/其他章节自动保留，无需客户端读取整文档再拼接；
(2) 单文档更新本身是原子的，并发场景下不会用旧快照覆盖别人刚写入的字段；
(3) 整体替换需要先读出完整文档再写回，存在丢失更新（覆盖并发修改、误删字段）风险，
    且题目明确要求保留其他字段与其他章节，整体替换若拼接遗漏就会违反要求。
""")

# 查询结果（第二次演示幂等）
print("最终 01 号课程:", doc)

client.close()
