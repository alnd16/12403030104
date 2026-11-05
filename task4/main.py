# -*- coding: utf-8 -*-
"""task4（选做）：Redis 逐条写入与普通 Pipeline 分批写入的性能比较。

参数：SID=12403030104，S=4，A=1，C=4
      N = 1000 + 100*C + S = 1404，每批最多 Q = 100。
    方案甲：逐条 SET，收到返回后再发下一条，不使用 Pipeline/多线程/异步。
    方案乙：普通 Pipeline（transaction=False），每批最多 100 条，批执行取全部结果后再发下一批，正确处理尾批。
"""
import time

from redis.cluster import RedisCluster, ClusterNode

SID = "12403030104"
N = 1000 + 100 * 4 + 4      # 1000 + 100*C + S = 1404
Q = 100

rc = RedisCluster(
    startup_nodes=[ClusterNode("127.0.0.1", p) for p in (7000, 7001, 7002)],
    decode_responses=True,
    socket_timeout=10,
    protocol=2,          # 服务端为 Redis 5.0，不支持 RESP3 的 HELLO
)
print("Redis Cluster 已连接，节点数:", len(rc.get_nodes()))

PREFIX_SEQ = "exam:%s:seq:" % SID
PREFIX_PIPE = "exam:%s:pipe:" % SID


def run_baseline(n):
    """方案甲：逐条写入。计时包括命令构造、发送和回复接收。"""
    t0 = time.perf_counter()
    for i in range(1, n + 1):
        rc.set(PREFIX_SEQ + str(i), "value-%s-%d" % (SID, i))
    return (time.perf_counter() - t0) * 1000.0


def run_pipeline(n, q):
    """方案乙：普通 Pipeline 分批写入。"""
    t0 = time.perf_counter()
    batches = 0
    last_batch = 0
    i = 1
    while i <= n:
        pipe = rc.pipeline(transaction=False)
        cnt = 0
        while cnt < q and i <= n:
            pipe.set(PREFIX_PIPE + str(i), "value-%s-%d" % (SID, i))
            i += 1
            cnt += 1
        pipe.execute()          # 收到本批全部回复后才继续下一批
        batches += 1
        last_batch = cnt
    return (time.perf_counter() - t0) * 1000.0, batches, last_batch


def verify(prefix_list):
    """核验数据是否完整：所有 N 个键都存在。"""
    missing = 0
    for prefix in prefix_list:
        i = 1
        while i <= N:
            pipe = rc.pipeline(transaction=False)
            cnt = 0
            while cnt < Q and i <= N:
                pipe.exists(prefix + str(i))
                i += 1
                cnt += 1
            for ok in pipe.execute():
                if not ok:
                    missing += 1
    return missing


# 清空可能残留的键
for prefix in (PREFIX_SEQ, PREFIX_PIPE):
    i = 1
    while i <= N:
        rc.delete(*[prefix + str(j) for j in range(i, min(i + Q, N + 1))])
        i += Q

time_a = run_baseline(N)
time_b, batches, last_batch = run_pipeline(N, Q)

print("=" * 60)
print("指标 | 程序输出值")
print("命令总数 |", N)
print("Pipeline批次数 |", batches)
print("最后一批数量 |", last_batch)
print("方案甲耗时(ms) | %.2f" % time_a)
print("方案乙耗时(ms) | %.2f" % time_b)

missing = verify([PREFIX_SEQ, PREFIX_PIPE])
print("数据完整性核验：缺失键数 =", missing, "（0 表示两种方式写入均完整）")
print("=" * 60)
if time_b < time_a:
    print("结论：Pipeline 更快。")
else:
    print("结论：测试中 Pipeline 未更快或差异不明显。")
print("""
若差异不明显或 Pipeline 更慢，可能原因：
(1) Redis 在本机、单次 RTT 很小，Pipeline 的批量收益被埋没；
(2) Redis Cluster 中键分布到 3 个主节点，Pipeline 需按节点拆分，回包与聚合有额外开销；
(3) Python 循环构造命令与结果解析耗时占比高，成为瓶颈；
(4) 单批 100 条、1404 条总量不大，启动/切换批次的固定成本相对突出。
""")

rc.close()
