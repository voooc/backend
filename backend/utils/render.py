from rest_framework.renderers import JSONRenderer


class CustomRender(JSONRenderer):
    # 重构render方法
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context:
            # 如果返回的data为字典
            if isinstance(data, dict):
                # 响应信息中有message和code这两个key，则获取响应信息中的message和code，并且将原本data中的这两个key删除，放在自定义响应信息里
                # 响应信息中没有则将msg内容改为请求成功 code改为请求的状态码
                msg = data.pop('message', '请求成功')
                code = data.pop('code', 0)
            # 如果不是字典则将msg内容改为请求成功 code改为请求的状态码
            else:
                msg = '请求成功'
                code = 0
            if not data:
                data = {}
            # 自定义返回的格式
            ret = {
                'message': msg,
                'code': code,
                'result': data,
            }
            # 返回JSON数据
            return super().render(ret, accepted_media_type, renderer_context)
        else:
            return super().render(data, accepted_media_type, renderer_context)
