from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.contrib.auth import logout
from django.contrib.auth.hashers import make_password
from article.tasks import send_register_email, send_verify_user
from user.models import User, Departments, VerifyCode, Message, Follows, Roles
from article.models import LikeDetail
from user.serializers import UserCreateSerializer, DepartmentsSerializer, MessageSerializer, UserSerializer, \
    FollowSerializer, FollowCreateSerializer, LikeDetailSerializer, RolesSerializer
from utils.EmailToken import token_confirm
from rest_framework.viewsets import ModelViewSet, GenericViewSet
import time
from rest_framework.decorators import action
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework.throttling import AnonRateThrottle
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from backend.utils.permissions import IsAdminOrReadOnly, IsAdminUser, IsOwnerOrReadOnly, IsSuperUser
from rest_framework import status, mixins
from django_filters.rest_framework import DjangoFilterBackend
from user.filter import LikeFilterBackend
from rest_framework.filters import SearchFilter
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import date
from django.conf import settings


class Login(ObtainJSONWebToken):
    """
    post:
    用户登录

    用户登录, status: 200(成功), return: Token信息
    """
    throttle_classes = [AnonRateThrottle]

    def perform_authentication(self, request):
        """
        重写父类的用户验证方法，不在进入视图前就检查JWT
        """
        pass

    def post(self, request, *args, **kwargs):
        user = User.objects.filter(email=request.data.get('email')).first()
        if user:
            request.data['username'] = user.username
        else:
            return Response(data={'code': -1, 'message': '用户名或密码错误'}, status=status.HTTP_400_BAD_REQUEST)
        roles = [role[0] for role in list(user.roles.values_list('value'))]
        if not user.is_active:
            return Response(data={'code': -1, 'message': '用户没有通过审核'}, status=status.HTTP_400_BAD_REQUEST)
        if request.data.get('type') == 'admin':
            if 'ADMIN' not in roles and 'SUPER' not in roles:
                return Response(data={'message': '您不是管理员，没有权限', 'code': -1}, status=status.HTTP_403_FORBIDDEN)
        # 重写父类方法, 定义响应字段内容
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            if request.data.get('remember'):
                request.session.set_expiry(None)
            else:
                request.session.set_expiry(0)
            user.last_login = date.today()
            user.save()
            return response
        else:
            if response.data.get('non_field_errors'):
                if isinstance(response.data.get('non_field_errors'), list) and len(
                        response.data.get('non_field_errors')) > 0:
                    if response.data.get('non_field_errors')[0].strip() == '无法使用提供的认证信息登录。':
                        return Response(data={'message': '用户名或密码错误', 'code': -1}, status=status.HTTP_400_BAD_REQUEST)
            raise ValidationError(response.data)


class RegisterEmail(APIView):
    permission_classes = (AllowAny, )

    def post(self, request):
        try:
            email = request.data.get('email')
            if User.objects.filter(email=email):
                return Response(data={'message': '用户已注册', 'code': -1}, status=status.HTTP_400_BAD_REQUEST)
            token = token_confirm.generate_validate_token(email)
            send_register_email.delay(email=email, token=token, send_type="register")
            return Response(data={'message': '请登录到注册邮箱中验证用户，有效期为10分钟'}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(data={'message': '注册失败'}, status=status.HTTP_400_BAD_REQUEST)


class Register(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            username = request.data.get('username')
            email = request.data.get('email')
            captcha = request.data.get('captcha')
            if User.objects.filter(username=username) or User.objects.filter(email=email):
                return Response(data={'message': '用户已注册', 'code': -1}, status=status.HTTP_400_BAD_REQUEST)
            if captcha:
                end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() - 6000))
                if VerifyCode.objects.filter(email=email, code__icontains=captcha):
                    items = VerifyCode.objects.filter(email=email, code__icontains=captcha, send_time__lt=end_time)
                    for item in items:
                        item.delete()
                    exist = VerifyCode.objects.filter(code__icontains=captcha, email=email, send_type='register')
                    if exist:
                        user_serializer = UserCreateSerializer(data=request.data)
                        if user_serializer.is_valid():
                            user_serializer.save()
                            return Response(data={'msg': '请等待管理员对账号进行审核'}, status=status.HTTP_201_CREATED)
                        else:
                            return Response(data={'msg': user_serializer.errors, 'code': -1},
                                            status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response(data={"message": "验证码已过期", 'code': -1}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response(data={"message": "验证码错误", 'code': -1}, status=status.HTTP_400_BAD_REQUEST)
            return Response(data={"message": '请输入验证码', 'code': -1}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response(data={"message": '验证失败请检查后提交', 'code': -1}, status=status.HTTP_400_BAD_REQUEST)


class ResetUserView(APIView):
    """更换邮箱发送验证码"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        email = request.data.get('email')
        username = request.user.username
        if email and username is not None:
            if User.objects.filter(email=email):
                return Response(data={'message': '邮箱已经存在'}, status=status.HTTP_400_BAD_REQUEST)
            send_register_email.delay(email=email, username=username, send_type='update_email')
            return Response(data={'message': u"验证码发送成功，有效期为10分钟"}, status=status.HTTP_200_OK)
        return Response(data={'message': '用户名与邮箱不能为空'}, status=status.HTTP_400_BAD_REQUEST)


class EmailView(APIView):
    """更换邮箱"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            email = request.data.get('email')
            code = request.data.get('code')
            end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() - 600))
            items = VerifyCode.objects.filter(send_time__lt=end_time)
            for item in items:
                item.delete()
            exist = VerifyCode.objects.filter(code__icontains=code, email=email, send_type='update_email')
            if exist:
                user = request.user
                user.email = email
                user.save()
                return Response(data={'message': '修改成功,请重新登录'}, status=status.HTTP_200_OK)
            else:
                return Response(data={'message': '验证码已过期或错误'}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response(data={'message': '验证失败请检查后提交'}, status=status.HTTP_400_BAD_REQUEST)


class Retrieve(APIView):
    """忘记密码"""
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            pwd = request.data.get('password')
            email = request.data.get('email')
            captcha = request.data.get('captcha', '')
            if captcha:
                end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() - 1800))
                if VerifyCode.objects.filter(email=email, code__icontains=captcha):
                    items = VerifyCode.objects.filter(email=email, code__icontains=captcha, send_time__lt=end_time)
                    for item in items:
                        item.delete()
                    exist = VerifyCode.objects.filter(code__icontains=captcha, email=email, send_type='forget')
                    if exist:
                        is_user = User.objects.filter(email=email)
                        if is_user:
                            User.objects.filter(email=email).update(password=make_password(pwd))
                            return Response(data={"message": "密码修改成功"}, status=status.HTTP_200_OK)
                        else:
                            return Response(data={"message": "验证码已过期"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"message": "验证码错误"}, status=status.HTTP_400_BAD_REQUEST)
            return Response(data={"message": '邮箱不存在'}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response(data={"message": '验证失败请检查后提交'}, status=status.HTTP_400_BAD_REQUEST)


class RetrieveEmail(APIView):
    """忘记密码发送验证码"""
    permission_classes = (AllowAny, )

    def post(self, request):
        email = request.data.get('email')
        if email:
            if User.objects.filter(email=email):
                send_register_email.delay(email=email, send_type='forget')
                return Response(data={'message': "验证码发送成功，有效期为10分钟"}, status=status.HTTP_200_OK)
            return Response(data={'message': "邮箱不存在"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data={'message': '邮箱不能为空'}, status=status.HTTP_400_BAD_REQUEST)


class VeifyUserViewSet(
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    permission_classes = [IsSuperUser]
    queryset = User.objects.filter(is_active=False)
    serializer_class = UserSerializer
    authentication_classes = [JSONWebTokenAuthentication]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        user = User.objects.get(id=serializer.data['id'])
        send_verify_user.delay(email=user.email, body='您在{0}网站的注册审核通过了哦~快去登录吧~'.format(settings.HOST), send_type='verify')
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        msg = Message()
        msg.user = user
        msg.message = '欢迎加入本站,在使用过程中有什么疑问,请联系管理员'
        msg.has_read = False
        msg.type = 'system'
        msg.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = User.objects.get(id=instance.id)
        send_verify_user.delay(email=user.email, body='您在{0}网站的注册没有审核通过哦~'.format(settings.HOST), send_type='verify')
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    
    def get(self, request):
        logout(request)
        content = {}
        return Response(data=content)


class DepartmentsViewSet(ModelViewSet):
    """
    create:
    部门--新增

    部门新增, status: 201(成功), return: 新增部门信息

    destroy:
    部门--删除

    部门删除, status: 204(成功), return: None

    update:
    部门--修改

    部门修改, status: 200(成功), return: 修改增部门信息

    list:
    部门--获取列表

    部门列表信息, status: 200(成功), return: 部门信息列表
    """
    permission_classes = [IsAdminOrReadOnly]
    queryset = Departments.objects.all()
    serializer_class = DepartmentsSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)


class RoleViewSet(ModelViewSet):
    """
    create:
    部门--新增

    部门新增, status: 201(成功), return: 新增部门信息

    destroy:
    部门--删除

    部门删除, status: 204(成功), return: None

    update:
    部门--修改

    部门修改, status: 200(成功), return: 修改增部门信息

    list:
    部门--获取列表

    部门列表信息, status: 200(成功), return: 部门信息列表
    """
    permission_classes = [IsSuperUser]
    queryset = Roles.objects.all()
    serializer_class = RolesSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)


class UserInfoView(APIView):
    """
    get:
    当前用户信息

    当前用户信息, status: 200(成功), return: 用户信息和权限

    post:
    修改信息
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_info = request.user.get_user_info()
        user_info['image'] = user_info.get('image')
        user_info['follow'] = User.objects.filter(follow__fan__id=request.user.id).count()
        user_info['fan'] = User.objects.filter(fan__follow_id=request.user.id).count()
        return Response(data={'user': user_info}, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            user = request.user
            username = request.data.get('username')
            if user.username != username:
                if User.objects.filter(username=username):
                    return Response(data={'message': '用户已存在，请重新输入用户名', 'code': -1}, status=status.HTTP_400_BAD_REQUEST)
            user.username = username
            user.desc = request.data.get('desc')
            user.image = request.data.get('image')
            user.save()
            return Response(data={"message": '修改成功'}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UseMessage(mixins.ListModelMixin, mixins.DestroyModelMixin, GenericViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = (IsAuthenticated)  # 未登录禁止访问
    authentication_classes = [JSONWebTokenAuthentication, SessionAuthentication]

    def list(self, request, *args, **kwargs):
        type = self.request.query_params.get('type')
        queryset = Message.objects.filter(user=self.request.user, type=type)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=False, url_path='read_all')
    def read_all(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        message = Message.objects.filter(id__in=ids)
        message.update(has_read=True)
        return Response(status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='count')
    def count(self, request):
        comment = Message.objects.filter(user=request.user, has_read=False, type='comment').count()
        like = Message.objects.filter(user=request.user, has_read=False, type='like').count()
        system = Message.objects.filter(user=request.user, has_read=False, type='system').count()
        follow = Message.objects.filter(user=request.user, has_read=False, type='follow').count()
        data = {'comment': comment, 'like': like, 'system': system, 'follow': follow}
        return Response(data=data)


def send_unread_count(user_id, count):
    room_name = f"notification_{user_id}"
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        room_name,
        {
            "type": "message",
            "count": count
        }
    )


class UserView(mixins.RetrieveModelMixin,
               mixins.UpdateModelMixin,
               mixins.DestroyModelMixin,
               mixins.ListModelMixin,
               GenericViewSet):
    queryset = User.objects.filter(is_active=True).all()
    serializer_class = UserSerializer
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsSuperUser]
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ['username']

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        res = serializer.data
        if request.user:
            is_active = Follows.objects.filter(follow=res['id'], fan=request.user.id).exists()
            res['follow_active'] = is_active
        else:
            res['follow_active'] = False
        res['follow'] = User.objects.filter(follow__fan__id=instance.id).count()
        res['fan'] = User.objects.filter(fan__follow_id=instance.id).count()
        return Response(data=res)


class UserFollow(mixins.CreateModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    lookup_field = 'follow'
    queryset = Follows.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return FollowSerializer
        else:
            return FollowCreateSerializer

    def get_queryset(self):
        if self.request.query_params.get('fan'):
            return Follows.objects.filter(follow=self.request.query_params.get('fan'))
        elif self.request.query_params.get('follow'):
            return Follows.objects.filter(fan=self.request.query_params.get('follow'))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        type = serializer.data['type']
        if type == 'follow':
            if request.user == serializer.data['follow']:
                return Response(data={"message": "不能自己关注自己",'follow_active': False}, status=status.HTTP_201_CREATED)
            else:
                follow_user = User.objects.get(id=serializer.data['follow'])
                follow = Follows(follow=follow_user, fan=request.user)
                follow.save()
                msg = Message(user=follow_user, to_user=request.user,
                              message='{}关注了你'.format(request.user.username), type='follow')
                msg.save()
                return Response(data={'message': '关注成功', 'follow_active': True}, status=status.HTTP_201_CREATED)
        elif type == 'unfollow':
            try:
                Follows.objects.filter(fan__id=request.user.id, follow_id=serializer.data['follow']).delete()
                return Response(data={"message": '取消成功', 'follow_active': False}, status=status.HTTP_202_ACCEPTED)
            except Exception as e:
                print(e)
                return Response(data={"message": '取消失败', 'follow_active': True}, status=status.HTTP_202_ACCEPTED)


class UserLike(mixins.ListModelMixin, GenericViewSet):
    queryset = LikeDetail.objects.all().order_by('-date')
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = LikeDetailSerializer
    filter_backends = (DjangoFilterBackend, LikeFilterBackend)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserTotalCountView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 获取所有用户总数
        count = User.objects.filter(is_active=True).count()
        now_date = date.today()
        now_register = User.objects.filter(date_joined__gte=now_date).count()
        # 获取当日登录用户数量  last_login记录最后登录时间
        now_count = User.objects.filter(last_login__gte=now_date).count()
        return Response({
            'count': count,
            'now_count': now_count,
            'now_register': now_register,
        })


