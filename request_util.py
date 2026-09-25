import requests
import logging

# 每个模块创建一个专属的 Logger，名字就是当前模块路径（如 common.request_util）
logger = logging.getLogger(__name__)


class RequestUtil:
    """
    HTTP 请求工具类：
    - 统一管理 Session（自动保持 Cookie/连接）
    - 统一管理 base_url
    - 统一管理全局 Headers（可选，不传就用 requests 默认）
    - 统一管理超时时间
    - 统一打印请求/响应日志
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 10,
        log_enabled: bool = True,
        headers: dict = None,      # ✅ 用 None 避免可变默认参数陷阱
    ):
        """
        :param base_url: 接口基础地址（必填），如 "http://127.0.0.1:8000"
        :param timeout: 请求超时时间，默认 10 秒
        :param log_enabled: 是否打印日志，默认开启
        :param headers: 全局请求头字典，默认 None（不传就用 requests 默认头）
        """
        self.session = requests.Session()
        self.base_url = base_url.rstrip("/")   # 去掉末尾的 /，防止拼接出现 //
        self.timeout = timeout
        self.log_enabled = log_enabled

        # ✅ 只有真的传了 headers，才更新到 Session
        if headers is not None:
            self.session.headers.update(headers)
        if self.log_enabled:
            if headers is not None:
                logger.info(f"[INIT] 已加载自定义 Headers: {headers}")
            else:
                logger.info("[INIT] 未传 Headers，使用 requests 默认头")

    def request(self, method: str, path: str, **kwargs):
        """所有请求的底层入口：统一拼 URL、统一超时、统一打日志"""
        url = f"{self.base_url}{path}"

        # ✅ 如果调用方没传 timeout，就用全局默认超时
        kwargs.setdefault("timeout", self.timeout)

        # ✅ 请求日志
        if self.log_enabled:
            logger.info(
                f"[REQUEST] {method} {url} | params={kwargs.get('params')} | json={kwargs.get('json')}"
            )

        # 发请求
        resp = self.session.request(method, url, **kwargs)

        # ✅ 响应日志（只打前 300 字，防止刷屏）
        if self.log_enabled:
            logger.info(f"[RESPONSE] {resp.status_code} | {resp.text[:300]}")

        return resp

    # ---------- 各种 HTTP 方法 ----------
    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs):
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs):
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def head(self, path: str, **kwargs):
        return self.request("HEAD", path, **kwargs)

    def options(self, path: str, **kwargs):
        return self.request("OPTIONS", path, **kwargs)

    # ---------- 辅助方法 ----------
    def set_token(self, token: str):
        """登录成功后调用，把 Token 挂到 Session 的全局 Headers 上"""
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        if self.log_enabled:
            logger.info("[INIT] 已更新 Token 到全局 Headers")

    def close(self):
        """关闭 Session，释放连接"""
        self.session.close()
        if self.log_enabled:
            logger.info("[CLOSE] Session 已关闭")