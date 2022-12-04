import fetch from 'node-fetch';

const BASEURL: string = "http://127.0.0.1:8000"

/** HTTPリクエストを送る
 * 
 * 
 * 
 * 
 */
async function PythonRequest(endpoint:string, options?: object) {
    // エンドポイントの設定
    const url = BASEURL + endpoint;
    // HTTPリクエスト
    const res:Response = await fetch(url);
    console.log(Object.prototype.toString.call(res));
    console.log(await res.json());

}

PythonRequest("/");



async function DiscordRequest(endpoint: string, options) {
    // API URLの作成
    const url = 'https://discord.com/api/v10/' + endpoint;
    // ペイロードをJSONに変換(Stringify)
    if (options.body) options.body = JSON.stringify(options.body);
    // fetchでリクエストを行う
    const res = await fetch(url, {
      headers: {
        Authorization: `Bot ${process.env.DISCORD_TOKEN}`,
        'Content-Type': 'application/json; charset=UTF-8',
        'User-Agent': 'DiscordBot (https://github.com/discord/discord-example-app, 1.0.0)'
      },
      ...options
    });
    // エラー処理
    if (!res.ok) {
      const data = await res.json();
      console.log(res.status); // エラー出力
      throw new Error(JSON.stringify(data));
    }
    // レスポンスの返却
    return res;
  }