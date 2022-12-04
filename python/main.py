from typing import Union, Optional, Tuple, Dict
from pydantic import BaseModel
import fastapi
from fastapi.responses import StreamingResponse
import Nai
from Nai import NOVELAIAPI, ImagePreset, ImageModel, UCPreset, ImageResolution, ImageSampler
from hydra import compose, initialize
from omegaconf import DictConfig
from CF import CloudFlareAPI

class ImageConfigPreset(BaseModel):
    id: Optional[str] = None
    prompt: str
    quality_toggle: Optional[bool] = None
    seed: Optional[int] = None
    scale: Optional[float] = None
    steps: Optional[int] = None
    uc: Optional[str] = None
    resolution: Optional[str] = None
    sampler: Optional[str] = None
    ucPreset: Optional[str] = None
    models: Optional[str] = None

class MyAPP:
    def __init__(self):
        self._app = fastapi.FastAPI() # インスタンス生成

    @property
    def app(self) -> fastapi.FastAPI:
        return self._app

def load_cf_cfg() -> dict[str, str]:
    with initialize(version_base=None, config_path="conf"):
        cfg: DictConfig = compose(config_name="config")
        return cfg["cloudflare"]

def load_nai_cfg() -> dict[str, str]:
    with initialize(version_base=None, config_path="conf"):
        cfg: DictConfig = compose(config_name="config")
        return cfg["nai"]        

app = MyAPP().app # FastAPI起動


@app.get("/")
async def root():
    return {"message": "Hello World"}
        

@app.post("/generate_image")
async def image_config(config: ImageConfigPreset):
    # NAIAPIのセットアップ
    cfg_nai: dict[str, str] = load_nai_cfg()
    NAI: NOVELAIAPI = NOVELAIAPI(cfg_nai["userid"], cfg_nai["password"])

    # CFのセットアップ
    cfg_cf: dict[str, str] = load_cf_cfg() 
    CF: CloudFlareAPI = CloudFlareAPI(cfg_cf["userid"], cfg_cf["apitoken"])

    # リクエストをパース
    prompt, model, preset = parse_img_config(config)

    # 画像リクエスト送信
    async with NAI as NaiAPI, CF as CfAPI:
        async for img in NaiAPI.generate_image(prompt, model, preset):
            data: Dict[str, bytes] = {"file": img}
            cf_res = await CfAPI._imageUpload(data)
            print(cf_res)
            return cf_res["result"]["variants"]

def parse_img_config(config: ImageConfigPreset = {}) -> Tuple[str, ImageModel, ImagePreset]:
    model: Optional[ImageModel] = None
    preset: ImagePreset = ImagePreset()
    prompt: str = None
    for name, value in config:
        print(name, value)
        # モデル設定
        if name == "models":
            if value != None:
                model = ImageModel[value]
            elif value == None:
                model = ImageModel.Anime_Curated
        # プロンプトの取得
        elif name == "prompt":
            prompt = value
        # プリセット設定
        elif name ==  "id":
            pass
        elif name == "ucPreset" and value != None:
            preset["ucPreset"] = UCPreset[value]
        elif name == "resolution" and value != None:
            preset["resolution"] = ImageResolution[value]
        elif name == "sampler" and value != None:
            preset["sampler"] = ImageSampler[value]
        elif value != None:
            preset[name] = value
    return prompt, model, preset
