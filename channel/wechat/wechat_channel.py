# encoding:utf-8

"""
wechat channel
"""

import io
import json
import os
import threading
import time
import datetime

import requests

from bridge.context import *
from bridge.reply import *
from channel.chat_channel import ChatChannel
from channel.wechat.wechat_message import *
from common.expired_dict import ExpiredDict
from common.log import logger
from common.singleton import singleton
from common.time_check import time_checker
from config import conf, get_appdata_dir
from lib import itchat
from lib.itchat.content import *
from mysql import selectUserBySessionId, insertUser, selectUserByNicknameSignNature
from plugins import *


@itchat.msg_register([TEXT, VOICE, PICTURE, NOTE])
def handler_single_msg(msg):
    try:
        if checkUserPromise(msg) is None:
            return None
        cmsg = WechatMessage(msg, False)
    except NotImplementedError as e:
        logger.debug("[WX]single message {} skipped: {}".format(msg["MsgId"], e))
        return None

    WechatChannel().handle_single(cmsg)
    return None


def checkUserPromise(msg):
    """
    fwh
            1. 用户在时间内-允许发送
            2. 不再时间内-回复充值使用
            3. 新用户对话-保存有效时间七天

            1. 新用户首次登录-保存有效时间七天
            2. 超过七天-直接返回充值消息
            """
    from_user_id = msg["FromUserName"]
    from_nick_name = msg['User']['NickName']
    from_signature = msg['User']['Signature']


    # 根据用户名+签名确认唯一 确认用户ID
    sessionData = selectUserByNicknameSignNature(from_nick_name, from_signature)
    # sessionData = selectUserBySessionId(from_user_id)
    if sessionData is None or len(sessionData) == 0:
        saveFriend(msg)
        # effective_time = now + datetime.timedelta(days=7)
        # insertUser(from_nick_name, from_user_id, from_user_id, from_nick_name, effective_time, now)
        return msg
    else:
        now = datetime.datetime.now()
        effective_timestamp = datetime.datetime.strptime(sessionData, '%Y-%m-%d %H:%M:%S').timestamp()
        now_timestamp = time.mktime(now.timetuple())
        if effective_timestamp < now_timestamp:
            # 回复自定义消息
            # from bridge import reply
            # itchat.send("您的赞赏是我创作的动力和支持！赞赏后可继续使用，让我们一起成就更多！！", toUserName=from_user_id)
            itchat.send(
                "嘿，{} 我是您的助手萌萌比卡[太阳][太阳]\r\n如果您觉得我的服务对您有帮助，能不能给我一点小小的赞赏呢？[爱心][爱心]\r\n赞赏后，您可以继续享受我的服务。[庆祝][庆祝]\r\n谢谢您的支持[玫瑰][玫瑰]".format(from_nick_name),
                toUserName=from_user_id)
            # 发送微信赞赏码
            img_url = "https://leanoss.fuwenhao.club/IJWU5m4PH8fRAeMJX9zjpfn6qDwJPqdI/zanshagnma.png"
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            for block in pic_res.iter_content(1024):
                image_storage.write(block)
            image_storage.seek(0)
            itchat.send_image(image_storage, toUserName=from_user_id)
            logger.info("UserId: %s ,NickName:%s ,已失效", from_user_id, from_nick_name)
            return None
        elif effective_timestamp > now_timestamp:
            logger.info("UserId: %s ,NickName:%s ,再有效期内，截止到：%s", from_user_id, from_nick_name, sessionData)
            return msg

def saveFriend(friend):
    logger.info("用户信息为:%s", friend)
    UserName = friend['User']['UserName']
    NickName = friend['User']['NickName']
    RemarkName = friend['User']['RemarkName']
    Sex = friend['User']['Sex']
    Province = friend['User']['Province']
    City = friend['User']['City']
    HeadImgUrl = friend['User']['HeadImgUrl']
    ContactFlag = friend['User']['ContactFlag']
    AttrStatus = friend['User']['AttrStatus']
    SnsFlag = friend['User']['SnsFlag']
    Signature = friend['User']['Signature']
    Uin = friend['User']['Uin']
    print(Uin)
    now = datetime.datetime.now()
    effective_time = now + datetime.timedelta(days=7)
    try:
        insertUser(UserName, NickName, RemarkName, Sex, Province, City, datetime.datetime.now(),
                   HeadImgUrl, ContactFlag, AttrStatus, SnsFlag, Signature,effective_time)
    except Exception as e:
        logger.error("保存好友异常,NickName为:{}", NickName, e)
        pass


@itchat.msg_register([TEXT, VOICE, PICTURE, NOTE], isGroupChat=True)
def handler_group_msg(msg):
    try:
        cmsg = WechatMessage(msg, True)
    except NotImplementedError as e:
        logger.debug("[WX]group message {} skipped: {}".format(msg["MsgId"], e))
        return None
    WechatChannel().handle_group(cmsg)
    return None


def _check(func):
    def wrapper(self, cmsg: ChatMessage):
        msgId = cmsg.msg_id
        if msgId in self.receivedMsgs:
            logger.info("Wechat message {} already received, ignore".format(msgId))
            return
        self.receivedMsgs[msgId] = cmsg
        create_time = cmsg.create_time  # 消息时间戳
        if conf().get("hot_reload") == True and int(create_time) < int(time.time()) - 60:  # 跳过1分钟前的历史消息
            logger.debug("[WX]history message {} skipped".format(msgId))
            return
        return func(self, cmsg)

    return wrapper


# 可用的二维码生成接口
# https://api.qrserver.com/v1/create-qr-code/?size=400×400&data=https://www.abc.com
# https://api.isoyu.com/qr/?m=1&e=L&p=20&url=https://www.abc.com
def qrCallback(uuid, status, qrcode):
    # logger.debug("qrCallback: {} {}".format(uuid,status))
    if status == "0":
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(qrcode))
            _thread = threading.Thread(target=img.show, args=("QRCode",))
            _thread.setDaemon(True)
            _thread.start()
        except Exception as e:
            pass

        import qrcode

        url = f"https://login.weixin.qq.com/l/{uuid}"

        qr_api1 = "https://api.isoyu.com/qr/?m=1&e=L&p=20&url={}".format(url)
        qr_api2 = "https://api.qrserver.com/v1/create-qr-code/?size=400×400&data={}".format(url)
        qr_api3 = "https://api.pwmqr.com/qrcode/create/?url={}".format(url)
        qr_api4 = "https://my.tv.sohu.com/user/a/wvideo/getQRCode.do?text={}".format(url)
        print("You can also scan QRCode in any website below:")
        print(qr_api3)
        print(qr_api4)
        print(qr_api2)
        print(qr_api1)

        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)


@singleton
class WechatChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()
        self.receivedMsgs = ExpiredDict(60 * 60 * 24)

    def startup(self):
        itchat.instance.receivingRetryCount = 600  # 修改断线超时时间
        # login by scan QRCode
        # hotReload = conf().get("hot_reload", False)
        hotReload = conf().get("hot_reload", True)
        status_path = os.path.join(get_appdata_dir(), "itchat.pkl")
        itchat.auto_login(
            enableCmdQR=2,
            hotReload=hotReload,
            statusStorageDir=status_path,
            qrCallback=qrCallback,
        )
        self.user_id = itchat.instance.storageClass.userName
        self.name = itchat.instance.storageClass.nickName
        logger.info("Wechat login success, user_id: {}, nickname: {}".format(self.user_id, self.name))
        # start message listener
        itchat.run()

    # handle_* 系列函数处理收到的消息后构造Context，然后传入produce函数中处理Context和发送回复
    # Context包含了消息的所有信息，包括以下属性
    #   type 消息类型, 包括TEXT、VOICE、IMAGE_CREATE
    #   content 消息内容，如果是TEXT类型，content就是文本内容，如果是VOICE类型，content就是语音文件名，如果是IMAGE_CREATE类型，content就是图片生成命令
    #   kwargs 附加参数字典，包含以下的key：
    #        session_id: 会话id
    #        isgroup: 是否是群聊
    #        receiver: 需要回复的对象
    #        msg: ChatMessage消息对象
    #        origin_ctype: 原始消息类型，语音转文字后，私聊时如果匹配前缀失败，会根据初始消息是否是语音来放宽触发规则
    #        desire_rtype: 希望回复类型，默认是文本回复，设置为ReplyType.VOICE是语音回复

    @time_checker
    @_check
    def handle_single(self, cmsg: ChatMessage):
        if cmsg.ctype == ContextType.VOICE:
            if conf().get("speech_recognition") != True:
                return
            logger.debug("[WX]receive voice msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[WX]receive image msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.PATPAT:
            logger.debug("[WX]receive patpat msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            logger.debug("[WX]receive text msg: {}, cmsg={}".format(json.dumps(cmsg._rawmsg, ensure_ascii=False), cmsg))
        else:
            logger.debug("[WX]receive msg: {}, cmsg={}".format(cmsg.content, cmsg))
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=False, msg=cmsg)
        if context:
            self.produce(context)

    @time_checker
    @_check
    def handle_group(self, cmsg: ChatMessage):
        if cmsg.ctype == ContextType.VOICE:
            if conf().get("speech_recognition") != True:
                return
            logger.debug("[WX]receive voice for group msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[WX]receive image for group msg: {}".format(cmsg.content))
        elif cmsg.ctype in [ContextType.JOIN_GROUP, ContextType.PATPAT]:
            logger.debug("[WX]receive note msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            # logger.debug("[WX]receive group msg: {}, cmsg={}".format(json.dumps(cmsg._rawmsg, ensure_ascii=False), cmsg))
            pass
        else:
            logger.debug("[WX]receive group msg: {}".format(cmsg.content))
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=True, msg=cmsg)
        if context:
            self.produce(context)

    # 统一的发送函数，每个Channel自行实现，根据reply的type字段发送不同类型的消息
    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        if reply.type == ReplyType.TEXT:
            itchat.send(reply.content, toUserName=receiver)
            logger.info("[WX] sendMsg={}, receiver={}".format(reply, receiver))
        elif reply.type == ReplyType.ERROR or reply.type == ReplyType.INFO:
            itchat.send(reply.content, toUserName=receiver)
            logger.info("[WX] sendMsg={}, receiver={}".format(reply, receiver))
        elif reply.type == ReplyType.VOICE:
            itchat.send_file(reply.content, toUserName=receiver)
            logger.info("[WX] sendFile={}, receiver={}".format(reply.content, receiver))
        elif reply.type == ReplyType.IMAGE_URL:  # 从网络下载图片
            img_url = reply.content
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            for block in pic_res.iter_content(1024):
                image_storage.write(block)
            image_storage.seek(0)
            itchat.send_image(image_storage, toUserName=receiver)
            logger.info("[WX] sendImage url={}, receiver={}".format(img_url, receiver))
        elif reply.type == ReplyType.IMAGE:  # 从文件读取图片
            image_storage = reply.content
            image_storage.seek(0)
            itchat.send_image(image_storage, toUserName=receiver)
            logger.info("[WX] sendImage, receiver={}".format(receiver))
