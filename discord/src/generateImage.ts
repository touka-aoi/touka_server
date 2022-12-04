import * as fs from "fs";

/** オブジェクトタイプ判定
 * 
 * @param obj 判定するオブジェクト
 */
function searchType(obj: Object){
    const type: any = Object.prototype.toString.call(obj);
    console.log(type);
}

// クエリ
interface RequestProperty {
    method: string;
    body?: any;
    headers?: any;
}

// イメージプリセット
export interface ImagePreset {
    id? : string; // ユーザーID
    prompt?:  string; //プロンプト
    qualityToggle?: boolean; // クォリティトグル
    seed?: number; // シード値
    scale?: number; // 自由度
    steps?: number; // ステップ数
    uc?: string; // ネガティブワード
    resolution?: string; // 解像度
    sampler?: string; // サンプラー
    ucPreset?: string; // プリセット
    models?: string; // モデル
}

/**
 * 
 */
async function _request(url:string, method:string = "GET", body?: Object){

    // リクエストの作成
    const property: RequestProperty = {
        method: method,
        headers: {
            "Content-Type": "application/json",
        }
    }

    if (body) {
        property.body = JSON.stringify(body);
    }

    // リクエストの送信
    const response: Response = await fetch(url, property);

    // エラーチェック
    if (!response.ok) {
        const data: Object = await response.json();
        console.log(response.status); // エラー出力
        throw new Error(JSON.stringify(data));
    }

    console.log(response.headers.get("content-type"));
    
    // データ取得
    const data: any = await treat_request(response);
    searchType(data);
    return data;
}

async function treat_request(res: any){
    const contentType = res.headers.get("content-type");
    switch(contentType) {
        case "application/json":
            return await res.json();
        case "image/png":
            return await res.blob();
        default:
            throw new Error(`unexpected content type. got type : ${contentType}`);
    }
}

export async function generateImage(body: ImagePreset){
    const url = "http://127.0.0.1:8000/generate_image";
    return await _request(url, "POST", body)
}

