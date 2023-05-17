# pip install redis

import redis


def getConnect():
    # 创建Redis连接池
    # redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0, password=)
    redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
    # redis_pool = redis.Redis(host='localhost', port=6379, db=0, parser_class=hiredis.Reader)
    # redis_pool = redis.StrictRedis(host='localhost', port=6379, db=0, parser_class=hiredis.Reader)

    # 获取Redis连接
    redis_conn = redis.Redis(connection_pool=redis_pool)
    return redis_conn


def getEffectTime(nameFlag):
    redis_conn = getConnect()
    effectTime = redis_conn.get(nameFlag)
    return effectTime


def setEffectTime(nameFlag, effectTime):
    redis_conn = getConnect()
    result = redis_conn.set(nameFlag, str(effectTime))
    print(result)


def delEffectTime(nameFlag):
    redis_conn = getConnect()
    result = redis_conn.delete(nameFlag)
    print(result)

# def baseDemo():
#     redis_conn = getConnect()
#     # 执行Redis操作
#     result = redis_conn.set('name', 'Alice')
#     print(result)
#     name = redis_conn.get('name')
#     print(name)
#
#     fwh = redis_conn.get('fwh')
#     print(fwh)
#     # redis_conn.delete('name')
#     # print(name)


# if __name__ == '__main__':
#     baseDemo()
