《NoSQL数据库》上机测验 —— 代码提交说明
================================================

学号：12403030104
姓名：谭中文（源代码中涉及个人姓名处按要求统一用“张三”代替）
班级：124030301

个人参数
--------
S  = 04 → 4
A  = S mod 3 = 1
B  = S mod 4 = 0
C  = S mod 5 = 4
Stock = 5 + C = 9
Buy   = 1 + A = 2
N = 1000 + 100C + S = 1404（每批 Q = 100）
MongoDB 数据库：exam_12403030104
Redis 键前缀：exam:12403030104:

运行环境
--------
- Windows 11
- Python 3.12（pymongo 4.19.0、redis 8.1.0）
- MongoDB 8.3，以副本集 rs0 运行于 127.0.0.1:27018（事务题要求副本集）
- Redis 5.0 Cluster，三主三从 127.0.0.1:7000-7005，cluster_state:ok

目录说明
--------
task1/  init.py    初始化 courses 集合（与测验卷给定数据一致）
        main.py    查询课程、局部更新章节、防重复新增、核验与解释
        result.txt 运行结果
task2/  init.py    重置 inventory 与 orders
        main.py    原子扣减、结果判断、事务订购函数、T1~T4 测试
        result.txt 运行结果
task3/  main.py    Redis 学生信息、章节集合、成绩排行榜、会话 TTL、类型核验
        result.txt 运行结果
task4/  main.py    逐条写入与普通 Pipeline 分批写入的计时比较（选做）
        result.txt 运行结果

执行方法
--------
1. 启动 MongoDB 副本集（27018）与 Redis 三主三从集群（7000-7005）。
2. task1：
     cd task1
     python init.py        # 初始化数据
     python main.py        # 业务操作与核验（重复执行验证时不要再 init）
3. task2：
     cd task2
     python init.py
     python main.py        # 程序内部按场景单独重置数据
4. task3：
     cd task3
     python main.py
5. task4（选做）：
     cd task4
     python main.py

注意事项
--------
- 所有业务代码均使用个人数据库 exam_12403030104 与个人键前缀 exam:12403030104:。
- 初始化代码与业务操作代码已分开。
- 源代码中未包含数据库账号、密码等连接凭据。
