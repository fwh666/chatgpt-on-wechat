"""
mysql5 链接
import mysql.connector

global cursor

def cursor():
    # 连接数据库
    mydb = mysql.connector.connect(
        host="43.138.30.198",
        user="wechat_test",
        password="ettXnfN8MTXS7SKE",
        database="wechat_test"
    )

    # 查询数据
    # mycursor = mydb.cursor()
    # mycursor.execute("SELECT * FROM fwh_user")
    # myresult = mycursor.fetchall()
    # for x in myresult:
    #     print(x)
    cursor = mydb.cursor()

"""
from common.log import logger
import pymysql
import datetime

# 打开数据库连接
db = pymysql.connect(host='43.138.30.198', port=3306, user='wechat_test', passwd='ettXnfN8MTXS7SKE', db='wechat_test',
                     # db = pymysql.connect(host='127.0.0.1', port=3306, user='wechat_test', passwd='123456', db='wechat_test',
                     charset='utf8mb4')


# 查询方法
def selectUserById(id):
    # 使用cursor方法创建一个游标
    cursor = db.cursor()
    sql = "select * from fwh_user where id =" + str(id)
    cursor.execute(sql)
    data = cursor.fetchall()
    for d in data:
        # id = d[0]
        # name = d[1]
        # age = d[2]
        # sex = d[3]
        # createtime = d[4]
        # print(id, name, age, sex, createtime)
        print(d)
    cursor.close()
    db.close()
    return data


def selectUserBySessionId(sessionId):
    # 使用cursor方法创建一个游标
    try:
        cursor = db.cursor()
        # sql = "select id,nickname,effective_time from fwh_user where sessionID ='%s'" % sessionId.__str__()
        sql = "select effective_time from fwh_user where sessionID ='%s'" % sessionId.__str__()
        cursor.execute(sql)
        # 获取查询结果
        myresult = cursor.fetchone()

        # 将时间字符串转换为datetime类型
        if myresult is not None:
            effective_time = myresult[0].strftime('%Y-%m-%d %H:%M:%S')
            print(effective_time)
        else:
            effective_time = cursor.fetchall()
        cursor.close()
        # db.close()
        return effective_time
        # return data
    except Exception as e:
        logger.error("查询错误", e)
        pass


# 根据昵称查询-可能会出现多个
def selectUserByNickName(nickname):
    try:
        cursor = db.cursor()
        sql = "select effective_time from fwh_user where nickname ='%s'" % nickname.__str__()
        cursor.execute(sql)
        # myresult = cursor.fetchone()
        myresult = cursor.fetchall()
        # 将时间字符串转换为datetime类型
        if myresult is not None:
            # 将查询结果放入集合
            data_set = set()
            for result in myresult:
                # effective_time = result.strftime('%Y-%m-%d %H:%M:%S')
                effective_time = str(result[0])
                data_set.add(effective_time)
            # effective_time = myresult[0].strftime('%Y-%m-%d %H:%M:%S')
            return data_set
        cursor.close()
        # db.close()
        return myresult
        # return data

    except Exception as e:
        logger.error("查询错误", e)
        pass


# 查询方法
def seleteUser():
    # 使用cursor方法创建一个游标
    cursor = db.cursor()
    sql = "select * from fwh_user"
    cursor.execute(sql)
    data = cursor.fetchall()
    for d in data:
        # id = d[0]
        # name = d[1]
        # age = d[2]
        # sex = d[3]
        # createtime = d[4]
        # print(id, name, age, sex, createtime)
        print(d)
    cursor.close()
    # db.close()
    return data


def insertUser(username, password, sessionID, nickname, effective_time, created_time):
    # 使用cursor方法创建一个游标
    cursor = db.cursor()
    sql = "insert into fwh_user(username,password,sessionID,nickname,effective_time,created_time) values (%s,%s,%s,%s,%s,%s) "
    try:
        # 执行sql语句;使用构造参数防止sql注入!
        row = cursor.execute(sql, (username, password, sessionID, nickname, effective_time, created_time))
        logger.info("影响条数:%s" % row)
        # 提交到数据库执行
        db.commit()
    except Exception as e:
        logger.error("插入异常", e)
        # 发生错误时回滚
        db.rollback()
    # 关闭
    cursor.close()
    # db.close()


if __name__ == '__main__':
    # 查询
    # data = selectUserBySessionId('@1aa2b6f04a71fb7ff5fa353454b0f3a992f0d769fd1f94b49086d1eacc64c583')
    # data = selectUserBySessionId('@4a7bf74e47e7e8a431de8676ea49a98a')
    # data = selectUserById(1)
    # data = seleteUser()
    data = selectUserByNickName("AI-Chat")
    print(len(data))
    # print(len(list(data)))
    print(data)

    # 新增
    # now = datetime.datetime.now()
    # # 时间增加七天
    # effective_time = now + datetime.timedelta(days=7)
    # # insertUser('小红', 'password', '734587263458726345', None, datetime.datetime.now(), datetime.datetime.now())
    # insertUser('小红04', 'password', '73458726345872634500', '昵称小红01', effective_time, now)
