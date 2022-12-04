from typing import Any, Optional, Union

from Nai.utils import create_encryption_key
from Nai.ImagePreset import * 
from .NovelAIError import NAIError

import json
from base64 import b64decode
from aiohttp import ClientResponse, ClientSession

class NOVELAIAPI:
    BASE_URL: str = 'https://api.novelai.net' # リクエストベースURL
    headers: dict = {}

    def __init__(self, _id: str, password: str) -> None:
        """クラス初期化

        Args:
            email (str): ユーザーID
            password (str): パスワード
        """
        self._id = _id # ユーザーID
        self._password = password # ユーザーパスワード
        self.session = None # HTTPセッション
        
    
    async def __aenter__(self):
        """非同期処理開始
        """
        self.session = ClientSession() # セッションの立ち上げ
        await self.session.__aenter__() # 非同期セッションの開始
        await self.login(self._id, self._password)#ログイン処理
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """非同期終了処理
        """
        await self.session.__aexit__(exc_type, exc_val, exc_tb)

    async def _requset(self, method: str, url: str, session: ClientSession, data: Union[dict[str, Any], str], isStream: bool):
        """HTTPリクエスト

        Args:
            method (str): HTTPメソッド
            endpoint (str): エンドポイント
            data (Optional[Union[dict[str, Any], str]]): 送信データ
        """
        # HTTP送信データ
        kwargs = {
            "headers" : self.headers,
            "json" if type(data) is dict else "data" : data
        }

        # HTTPリクエスト
        async with session.request(method, url, **kwargs) as rsp:
            # ストリームなら
            if isStream:
                content = b"" # 初期化
                # ストリーム処理
                async for chunk in rsp.content.iter_any():
                    # ヘッダー処理
                    if content and b"event" in chunk:
                        # event処理
                        event_pos = chunk.find(b"event:")
                        content += chunk[:event_pos]
                        yield rsp, await self.treat_response_stream(rsp, content)
                        content = chunk[event_pos:]
                    # コンテンツ処理
                    else:
                        content += chunk
                # すべてのデータ処理後
                yield rsp, await self.treat_response_stream(rsp, content)

            # シングルなら
            else: 
                yield rsp, await self.treat_response(rsp, rsp) # コンテンツ処理

    async def request(self, method: str, endpoint: str, data: Optional[Union[dict[str, Any], str]]=None):
        """HTTPリクエスト(シングル)

        Args:
            method (str): HTTPメソッド
            endpoint (str): HTTPエンドポイント
            data (Optional[Union[dict[str, Any], str]], optional): 送信データ. デフォルト : None

        Returns:
            _type_: レスポンスデータ
        """
        # シングルレスポンスを返す
        async for i in self.request_stream(method, endpoint, data, False):
            return i

    async def request_stream(self, method: str, endpoint: str, data: Optional[Union[dict[str, Any], str]]=None, isStream=True):
        """HTTPリクエスト(ストリーム)

        Args:
            method (str): HTTPメソッド
            endpoint (str): HTTPエンドポイント
            data (Optional[Union[dict[str, Any], str]], optional): 送信データ. デフォルト : None
            isStream (bool, optional): _description_. ストリーム処理を行うか デフォルト : True

        Yields:
            _type_: レスポンスデータ
        """
        url = f"{self.BASE_URL}{endpoint}" # HTTP送信先
        session = self.session # セッション
        async for i in self._requset(method, url, session, data, isStream):
            yield i
        await session.close()

    async def login(self, _id: str, _password: str) -> None:
        """ログイン処理 (id, パスワード)

        Args:
            _id (str): id
            _password (str): パスワード
        """
        access_key = create_encryption_key(_id, _password) # 暗号化キーの取得
        content = await self._login(access_key) # ログイン処理 
        self.headers["Authorization"] = f"Bearer {content['accessToken']}" # ヘッダーにトークンを登録

    async def _login(self, access_key: str) -> None:
        """ログイン処理 (アクセストークン)

        Args:
            access_key (str): アクセスキー
        """
        rsp, content = await self.request("post", "/user/login", {"key" : access_key}) # HTTPリクエスト

        self.treat_response_object(rsp, content, 201) # レスポンス処理

        return content # コンテンツを返す

    async def generate_image(self, prompt: str, model: ImageModel, preset: ImagePreset):
        """画像生成

        Args:
            prompt (str): プロンプト
            model (ImageModel): 生成モデル
            preset (ImagePreset): 設定
        """ 
        settings = preset.confirm() # 設定読み込み

        quality_toggle = settings["quality_toggle"] 
        # クォリティトグルがオンならプロンプト追加
        if quality_toggle:
            prompt = f"masterpiece, best quality, {prompt}" 

        # HTTPリクエスト
        async for i in self._generate_image(prompt, model, settings):
           yield b64decode(i) #

    async def _generate_image(self, prompt: str, model: ImageModel, parameters: dict[str, Any]):
        """画像生成

        Args:
            prompt (str): プロンプト
            model (ImageModel): モデル
            parameters (dict[str, Any]): パラメータ

        Yields:
            _type_: バイトデータ
        """

        # プロンプトチェック
        assert type(prompt) is str, f"Expected type 'list' for prompts, but got type '{type(prompt)}'"
        # モデルチェック
        assert type(model) is ImageModel, f"Expected type 'ImageModel' for model, but got type '{type(model)}'"
        # パラメータチェック
        assert type(parameters) is dict, f"Expected type 'dict' for parameters, but got type '{type(parameters)}'"

        # HTTPリクエストデータ作成
        args = {
            "input": prompt,
            "model": model.value,
            "parameters": parameters,
        }

        # HTTPリクエスト
        async for rsp, content in self.request_stream("post", "/ai/generate-image", args):
            self.treat_response_object(rsp, content, 201) # レスポンス処理
            yield content

    async def treat_response_stream(self, rsp: ClientResponse, data: bytes) -> Any:
        """ストリームデータ処理

        Args:
            rsp (ClientResponse): レスポンスヘッダ  
            data (bytes): データ

        Returns:
            Any: 処理済みデータ
        """
        data = data.decode()

        if rsp.content_type == "text/event-stream":
            # パース
            stream_data = self.parse_stream_data(data)

            assert "data" in stream_data
            # データを抽出
            data = stream_data["data"]

            # Jsonの場合
            if data.startswith('{') and data.endswith('}'):
                data = json.loads(data)

        return data

    @staticmethod
    def treat_response_object(rsp: ClientResponse, content: Any, status: int) -> Any:
        """HTTPレスポンスのエラーハンドル

        Args:
            rsp (ClientResponse): レスポンスヘッダ
            content (Any): レスポンス
            status (int): HTTPステータス

        Raises:
            NAIError: エラーハンドル

        Returns:
            Any: HTTPレスポンス
        """
        # エラー
        if type(content) is dict and "error" in content:
            raise NAIError(rsp.status, content["error"])
        
        # 成功
        if rsp.status == status:
            return content

    @staticmethod
    async def treat_response(rsp: ClientResponse, data: Any) -> Any:
        """HTTPレスポンス処理

        Args:
            rsp (ClientResponse): レスポンスヘッダ
            data (Any): データ

        Returns:
            Any: エンコードデータ
        """
        # Json
        if rsp.content_type == "application/json":
            return await data.json()

        # Text
        if rsp.content_type == "text/plain" or rsp.content_type == "text/html":
            return await data.text()

        # Audio
        if rsp.content_type == "audio/mpeg" or rsp.content_type == "audio/webm":
            return await data.read()

    @staticmethod
    def parse_stream_data(stream_content: str) -> dict[str, Any]:
        """HTTPストリームパース処理

        Args:
            stream_content (str): データ

        Raises:
            NAIError: パース失敗エラー

        Returns:
            dict[str, Any]: パース後データ
        """
        stream_data = {}

        # 一行ごと処理
        for line in stream_content.strip('\n').splitlines():
            colon = line.find(":")
            if ":" == -1:
                raise NAIError(0, f"Malformed data stream line: {line}")

            stream_data[line[:colon]] = line[colon + 1:].strip()

        return stream_data