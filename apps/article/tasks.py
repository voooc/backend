from __future__ import absolute_import
from django.core.mail import send_mail
import random
from django.conf import settings
from user.models import VerifyCode
from backend.celery import app


def random_str(random_length=8):
    string = ""
    chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    length = len(chars) - 1
    for i in range(random_length):
        string += chars[random.randint(0, length)]
    print(string)
    return string


@app.task()
def send_register_email(email, username=None, token=None, send_type='register'):
    """
    登录注册等邮件发送
    :param email:
    :param username:
    :param token:
    :param send_type:
    :return:
    """
    code = random_str(4)
    if send_type == 'register':
        VerifyCode.objects.create(code=code, email=email, send_type=send_type)
        email_title = '注册用户验证信息'
        email_body = "你的注册账号验证码为:{0}。如非本人操作请忽略,此验证码10分钟后失效。".format(code)
        print('========发送邮件中')
        send_status = send_mail(subject=email_title, message=email_body, from_email=settings.EMAIL_HOST_USER, recipient_list=[email])
        print(send_status)
        if send_status:
            print('========发送成功')
            pass
    elif send_type == 'forget':
        VerifyCode.objects.create(code=code, email=email, send_type=send_type)
        email_title = '密码重置信息'
        email_body = "你的密码重置验证码为:{0}。如非本人操作请忽略,此验证码10分钟后失效。".format(code)
        print('========发送邮件中')
        send_status = send_mail(subject=email_title, message=email_body, from_email=settings.EMAIL_HOST_USER,
                                recipient_list=[email])
        print(send_status)
        if send_status:
            print('========发送成功')
            pass
    elif send_type == 'update_email':
        VerifyCode.objects.create(code=code, email=email, send_type=send_type)
        email_title = '修改邮箱链接'
        email_body = "你的修改邮箱验证码为:{0}。如非本人操作请忽略,此验证码10分钟后失效。".format(code)
        print('========发送邮件中')
        send_status = send_mail(email_title, email_body, settings.EMAIL_NAME, [email])
        if send_status:
            print('========发送成功')
            pass


@app.task()
def error_email(title=None, body=None, email=None):
    email_title = title
    email_body = body
    send_mail(email_title, email_body, settings.EMAIL_NAME, [email])
