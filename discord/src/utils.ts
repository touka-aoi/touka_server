import fetch from 'node-fetch';
import { verifyKey } from 'discord-interactions';
import { Request, Response, NextFunction } from 'express';

/**
* クライアントキーをセットしたverify用関数を作成する
* @param {string} clientKey クライアントキー
* @return {function} 関数を返す
*/
export function VerifyDiscordRequest(clientKey: string) {
  // 署名検証
  return function (req: Request, res: Response, buf, encoding) {
    const signature = req.get('X-Signature-Ed25519');
    const timestamp = req.get('X-Signature-Timestamp');


    const isValidRequest = verifyKey(buf, signature, timestamp, clientKey);
    if (!isValidRequest) {
      res.status(401).send('Bad request signature');
      throw new Error('Bad request signature');
    }
  };
}

export async function DiscordRequest(endpoint: string, options) {
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