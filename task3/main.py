# -*- coding: utf-8 -*-
"""task3：Redis 学习信息与排行榜（Hash / Set / Sorted Set / String）。

参数：SID=12403030104，S=4，A=1，C=4，本人排行榜初始分数 = 70 + C = 74。
键统一前缀 exam:<SID>:。
"""
import time

from redis.cluster import RedisCluster, ClusterNode

SID = "12403030104"
S = 4
A = 1
C = 4
MY_SCORE = 70 + C          # 74
CLASS_NAME = "124030301"  # 本人班级

rc = RedisCluster(
    startup_nodes=[ClusterNode("127.0.0.1", p) for p in (7000, 7001, 7002)],
    decode_responses=True,
    socket_timeout=10,
    protocol=2,            # 服务端 Redis 5.0，不支持 RESP3 的 HELLO
)

K_STUDENT = "exam:%s:student" % SID
K_CHAPTERS = "exam:%s:chapters" % SID
K_SCORES = "exam:%s:scores" % SID
K_SESSION = "exam:%s:session" % SID
MY_MEMBER = "Student:" + SID

print("=" * 60)
print("1. 学生信息维护（Hash）")
rc.delete(K_STUDENT)
rc.hset(K_STUDENT, mapping={
    "studentId": SID,
    "name": "张三",
    "className": CLASS_NAME,
    "courseId": "COURSE-" + SID + "-01",
    "status": "learning",
})
rc.hset(K_STUDENT, "status", "completed")
print("name   =", rc.hget(K_STUDENT, "name"))
print("status =", rc.hget(K_STUDENT, "status"))
full = rc.hgetall(K_STUDENT)
print("完整 Hash:", full)
print("其他字段保留:", all(k in full for k in ("studentId", "className", "courseId")))

print("=" * 60)
print("2. 已完成章节记录（Set）")
rc.delete(K_CHAPTERS)
for ch in ("CH01", "CH02", "CH02", "CH03"):
    rc.sadd(K_CHAPTERS, ch)
    print("提交 %s 后已完成章节数量: %d" % (ch, rc.scard(K_CHAPTERS)))
print("最终全部章节:", sorted(rc.smembers(K_CHAPTERS)))
print("CH02 是否完成:", rc.sismember(K_CHAPTERS, "CH02") == 1)
print("CH04 是否完成:", rc.sismember(K_CHAPTERS, "CH04") == 1)
before = rc.scard(K_CHAPTERS)
rc.sadd(K_CHAPTERS, "CH02")   # 重复提交
after = rc.scard(K_CHAPTERS)
print("重复提交 CH02：前 %d -> 后 %d，数量不变: %s" % (before, after, before == after))

print("=" * 60)
print("3. 成绩排行榜（Sorted Set）")
rc.delete(K_SCORES)
rc.zadd(K_SCORES, {
    MY_MEMBER: MY_SCORE,
    "demo:01": 85,
    "demo:02": 90,
    "demo:03": 60,
    "demo:04": 80,
})

def show_top3(tag):
    print(tag)
    for idx, (member, score) in enumerate(rc.zrevrange(K_SCORES, 0, 2, withscores=True), start=1):
        print("  第%d名: %s 分数 %d" % (idx, member, score))

show_top3("(1) 初始前3名（降序）:")
rc.zincrby(K_SCORES, 20, MY_MEMBER)      # 本人 +20 分
show_top3("(3) 本人分数 +20 后前3名:")
new_score = rc.zscore(K_SCORES, MY_MEMBER)
rank = rc.zrevrank(K_SCORES, MY_MEMBER) + 1
print("(4) 本人更新后分数: %d，名次: 第%d名" % (new_score, rank))

print("=" * 60)
print("4. 会话生命周期（String + TTL）")
rc.delete(K_SESSION)
rc.set(K_SESSION, "session-" + SID, ex=5)
session_type = rc.type(K_SESSION)      # 必须在过期前检查类型
print("(1) 创建后键值:", rc.get(K_SESSION), "| TTL:", rc.ttl(K_SESSION), "| 类型:", session_type)
time.sleep(6)
print("(3) 等待6秒后 是否存在:", rc.exists(K_SESSION) == 1, "| TTL:", rc.ttl(K_SESSION))
print("(4) 过期验证:", "通过" if rc.exists(K_SESSION) == 0 else "未通过")

print("=" * 60)
print("5. 数据类型核验与说明")
types = {
    "Hash": rc.type(K_STUDENT),
    "Set": rc.type(K_CHAPTERS),
    "Sorted Set": rc.type(K_SCORES),
    "String(会话, 过期前检查)": session_type,
}
print("实际类型:", types)
print("""
说明（一句话理由）：
- Hash：学生信息是多个字段（学号/姓名/班级/课程/状态），按字段读写，局部修改方便；
- Set：已完成章节需去重且不关心顺序，重复提交自动忽略；
- Sorted Set：排行榜按分数排序，天然支持取前 N 名和分数/名次查询；
- String：会话是一次性键值，配合 TTL 设置过期时间，适合会话生命周期管理。
""")

rc.close()
