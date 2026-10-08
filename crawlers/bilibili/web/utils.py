import hashlib
import time
from urllib.parse import urlencode
import httpx
from crawlers.bilibili.web import wrid
from crawlers.utils.logger import logger
from crawlers.bilibili.web.endpoints import BilibiliAPIEndpoints

MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]


class EndpointGenerator:
    def __init__(self, params: dict):
        self.params = params

    # 获取用户发布视频作品数据 生成enpoint
    async def user_post_videos_endpoint(self) -> str:
        # 添加w_rid
        endpoint = await WridManager.wrid_model_endpoint(params=self.params)
        # 拼接成最终结果并返回
        final_endpoint = BilibiliAPIEndpoints.USER_POST + '?' + endpoint
        return final_endpoint

    # 获取视频流地址 生成enpoint
    async def video_playurl_endpoint(self) -> str:
        # 添加w_rid
        endpoint = await WridManager.wrid_model_endpoint(params=self.params)
        # 拼接成最终结果并返回
        final_endpoint = BilibiliAPIEndpoints.VIDEO_PLAYURL + '?' + endpoint
        return final_endpoint

    # 获取指定用户的信息 生成enpoint
    async def user_profile_endpoint(self) -> str:
        # 添加w_rid
        endpoint = await WridManager.wrid_model_endpoint(params=self.params)
        # 拼接成最终结果并返回
        final_endpoint = BilibiliAPIEndpoints.USER_DETAIL + '?' + endpoint
        return final_endpoint

    # 获取综合热门视频信息 生成enpoint
    async def com_popular_endpoint(self) -> str:
        # 添加w_rid
        endpoint = await WridManager.wrid_model_endpoint(params=self.params)
        # 拼接成最终结果并返回
        final_endpoint = BilibiliAPIEndpoints.COM_POPULAR + '?' + endpoint
        return final_endpoint

    # 获取指定用户动态
    async def user_dynamic_endpoint(self):
        # 添加w_rid
        endpoint = await WridManager.wrid_model_endpoint(params=self.params)
        # 拼接成最终结果并返回
        final_endpoint = BilibiliAPIEndpoints.USER_DYNAMIC + '?' + endpoint
        return final_endpoint


class WridManager:
    _cached_mixin_key: str = "ea1db124af3c7062474693fa704f4ff8"
    _cached_time: float = 0.0
    _cache_ttl: float = 1800.0

    @classmethod
    async def get_mixin_key(cls, headers: dict = None) -> str:
        now = time.time()
        if cls._cached_mixin_key and (now - cls._cached_time < cls._cache_ttl):
            return cls._cached_mixin_key

        try:
            req_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Referer": "https://www.bilibili.com/",
            }
            if headers:
                req_headers.update(headers)

            async with httpx.AsyncClient(headers=req_headers, timeout=10.0) as client:
                resp = await client.get("https://api.bilibili.com/x/web-interface/nav")
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    wbi_img = data.get("wbi_img", {})
                    img_url = wbi_img.get("img_url", "")
                    sub_url = wbi_img.get("sub_url", "")
                    if img_url and sub_url:
                        img_key = img_url.split("/")[-1].split(".")[0]
                        sub_key = sub_url.split("/")[-1].split(".")[0]
                        raw_key = img_key + sub_key
                        cls._cached_mixin_key = "".join([raw_key[i] for i in MIXIN_KEY_ENC_TAB])[:32]
                        cls._cached_time = now
                        return cls._cached_mixin_key
        except Exception as e:
            logger.warning(f"获取 Bilibili WBI mixin_key 失败，使用降级值: {e}")

        return cls._cached_mixin_key

    @classmethod
    async def wrid_model_endpoint(cls, params: dict, headers: dict = None) -> str:
        mixin_key = await cls.get_mixin_key(headers)
        params["wts"] = str(int(time.time()))
        sorted_params = dict(sorted(params.items()))
        filtered_params = {
            k: "".join(filter(lambda chr: chr not in "!'()*", str(v)))
            for k, v in sorted_params.items()
        }
        query = urlencode(filtered_params)
        w_rid = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
        filtered_params["w_rid"] = w_rid
        params["wts"] = filtered_params["wts"]
        params["w_rid"] = w_rid
        return urlencode(filtered_params)

# BV号转为对应av号
async def bv2av(bv_id: str) -> int:
    table = "fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF"
    s = [11, 10, 3, 8, 4, 6, 2, 9, 5, 7]
    xor = 177451812
    add_105 = 8728348608
    add_all = 8728348608 - (2 ** 31 - 1) - 1
    tr = [0] * 128
    for i in range(58):
        tr[ord(table[i])] = i
    r = 0
    for i in range(6):
        r += tr[ord(bv_id[s[i]])] * (58 ** i)
    add = add_105
    if r < add:
        add = add_all
    aid = (r - add) ^ xor
    return aid

# 响应分析
class ResponseAnalyzer:
    # 用户收藏夹信息
    @classmethod
    async def collect_folders_analyze(cls, response: dict) -> dict:
        if response['data']:
            return response
        else:
            logger.warning("该用户收藏夹为空/用户设置为不可见")
            return {"code": 1, "message": "该用户收藏夹为空/用户设置为不可见"}
