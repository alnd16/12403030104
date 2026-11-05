# -*- coding: utf-8 -*-
"""task2 业务操作：MongoDB 原子扣减与事务验证。

参数：SID=12403030104，S=4，A=1，C=4，
      Stock = 5+C = 9，Buy = 1+A = 2。
事务在副本集实例 rs0（127.0.0.1:27018）上执行，单机模式不支持多文档事务。
"""
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import PyMongoError

SID = "12403030104"
STOCK = 9
BUY = 2
BOOK_ID = "BOOK-" + SID

client = MongoClient("mongodb://127.0.0.1:27018/?directConnection=true")
db = client["exam_" + SID]
inventory = db["inventory"]
orders = db["orders"]

# ---------- 工具：重置数据 ----------
def reset_data(stock):
    inventory.delete_many({})
    inventory.insert_one({"_id": BOOK_ID, "title": "NoSQL数据库教材", "stock": stock})
    orders.delete_many({})


def current_state():
    doc = inventory.find_one({"_id": BOOK_ID})
    return (doc["stock"] if doc else None), orders.count_documents({})


# ---------- 1. 单文档原子扣减 ----------
def atomic_deduct(buy=BUY):
    """条件检查与扣减合并为一次单文档原子更新。
    返回 (ok, reason)：ok=True 扣减成功；False 时 reason 区分库存不足/教材不存在/数据库异常。
    """
    try:
        doc = inventory.find_one_and_update(
            {"_id": BOOK_ID, "stock": {"$gte": buy}},       # 同时筛选教材编号与库存条件
            {"$inc": {"stock": -buy}},
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as e:
        return False, "数据库执行异常: %s" % e
    if doc is None:
        # 用返回结果判断：没匹配到文档 = 库存不足或教材不存在
        return False, "库存不足或教材不存在（未执行扣减）"
    return True, "扣减成功，剩余库存 %d" % doc["stock"]


# ---------- 2. 判断操作结果 ----------
def judge_deduct(buy=BUY):
    """三种结果的判定展示。"""
    ok, reason = atomic_deduct(buy)
    if ok:
        return "扣减成功"
    if reason.startswith("数据库执行异常"):
        return "数据库执行异常"
    return "库存不足或教材不存在"


# ---------- 3. 事务 ----------
class InsufficientStock(Exception):
    pass


class ForcedError(Exception):
    pass


def place_order(request_id, force_error=False, buy=BUY):
    """订购函数：同一会话、同一事务中完成『扣减 + 生成订单』。
    force_error=True 时在扣减成功后、订单插入前主动抛异常，验证回滚。
    只有事务提交成功才返回成功。
    """
    try:
        with client.start_session() as session:
            with session.start_transaction():
                res = inventory.update_one(
                    {"_id": BOOK_ID, "stock": {"$gte": buy}},
                    {"$inc": {"stock": -buy}},
                    session=session,
                )
                if res.matched_count == 0:
                    raise InsufficientStock("库存不足或教材不存在")
                if force_error:
                    raise ForcedError("强制异常：库存已扣减、订单插入前")
                orders.insert_one({
                    "_id": request_id,
                    "bookId": BOOK_ID,
                    "studentId": SID,
                    "quantity": buy,
                }, session=session)
            # 离开 with 时事务提交；提交成功后才返回
        return True, "订购成功（事务已提交）"
    except InsufficientStock as e:
        return False, "扣减失败，未生成订单: %s" % e
    except ForcedError as e:
        return False, "异常回滚: %s" % e
    except PyMongoError as e:
        return False, "数据库执行异常，事务回滚: %s" % e


# ---------- 4. 系统测试 ----------
def run_scenario(name, init_stock, plan):
    """plan: [(request_id, force_error), ...]；返回是否通过预期。"""
    reset_data(init_stock)
    init_state = current_state()
    ok_cnt = fail_cnt = 0
    for rid, force in plan:
        ok, msg = place_order(rid, force)
        if ok:
            ok_cnt += 1
        else:
            fail_cnt += 1
    final_stock, final_orders = current_state()

    # 根据参数计算预期值
    exp_ok = sum(1 for _, f in plan if not f)  # 正常请求数（实际还需库存约束）
    # 按顺序模拟预期：逐个判断在预期库存下能否扣减
    exp_stock = init_stock
    exp_ok_cnt = 0
    for _, force in plan:
        if exp_stock >= BUY:
            exp_stock -= BUY
            if not force:
                exp_ok_cnt += 1
        # force_error 场景扣减也回滚，预期库存不变
        if force:
            exp_stock += BUY
    exp_fail_cnt = len(plan) - exp_ok_cnt
    exp_orders = exp_ok_cnt
    passed = (final_stock == exp_stock and final_orders == exp_orders
              and ok_cnt == exp_ok_cnt and fail_cnt == exp_fail_cnt)

    print("-" * 60)
    print("场景编号:", name)
    print("(2) 初始库存:", init_state[0])
    print("(3) 购买数量:", BUY)
    print("(4) 成功次数:", ok_cnt)
    print("(5) 失败次数:", fail_cnt)
    print("(6) 最终库存:", final_stock, "(预期", exp_stock, ")")
    print("(7) 最终订单数量:", final_orders, "(预期", exp_orders, ")")
    print("(8) 是否通过核验:", "通过" if passed else "不通过")
    return passed


print("=" * 60)
print("原子扣减与事务验证（SID=%s，Stock=%d，Buy=%d）" % (SID, STOCK, BUY))

# T1 正常订购
reset_data(STOCK)
print("\n[判断结果演示] T1 单次正常订购:", judge_deduct())

# T2 库存不足
reset_data(BUY - 1)
print("[判断结果演示] T2 库存不足:", judge_deduct())

t1 = run_scenario("T1正常订购", STOCK, [("req-T1-" + SID, False)])
t2 = run_scenario("T2库存不足", BUY - 1, [("req-T2-" + SID, False)])
t3 = run_scenario("T3中途异常", STOCK, [("req-T3-" + SID, True)])
n_t4 = STOCK // BUY + 1
t4_plan = [("req-T4-" + SID + "-%d" % i, False) for i in range(1, n_t4 + 1)]
t4 = run_scenario("T4连续购买", STOCK, t4_plan)

print("-" * 60)
print("全部场景:", "全部通过" if all([t1, t2, t3, t4]) else "存在不通过")

print("""
解释：
(1) 单次扣减的原子性只保证『一个文档的一次更新』不可分割；而业务要求库存扣减与订单生成
    两个文档操作同时成功或同时不生效（全部生效/全部不生效），跨文档必须使用事务。
    若只有原子扣减，扣减成功而订单插入失败会出现『库存少了却没有订单』的账实不符。
(2) forceError 验证了事务在『扣减已经发生、订单尚未插入』的中间点抛出异常时能够整体回滚：
    库存恢复原值、订单不生成；也验证程序只在事务提交成功后返回订购成功，而不是看到
    扣减语句执行完就认为成功。
""")

client.close()
