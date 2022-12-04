import * as fs from "fs";
import * as dotenv from 'dotenv'
dotenv.config()
import fetch from 'node-fetch';
import * as express from 'express';
import {
    InteractionType,
    InteractionResponseType,
    InteractionResponseFlags,
    MessageComponentTypes,
    ButtonStyleTypes,
  } from 'discord-interactions';
import { VerifyDiscordRequest } from './utils';
import { Request, Response, NextFunction } from 'express';
import {
  CHECKWORK,
  SHOWIMAGESETTING,
  NAIGENERATEIMAGE,
  SETIMAGECONFIG,
  HasGuildCommands,
  DeleteGuildCommandsAll,
} from './commands';

import {
  ImagePreset,
  generateImage,
} from "./generateImage"

import { DiscordRequest } from "./utils";

interface UserConfig {
  [id: string]: ImagePreset;
}

/** コンフィグ出力整形関数
 * @param {appImagePreset} obj - コンフィグ
 * @returns {string} res 整形文章
 */
 function createConfigReturn(obj: ImagePreset){
  let res:string = ""; // 出力用string
  // 文字整形
  res += `<@${obj["id"]}>'s image setting\n` 
  for (let [key, value] of Object.entries(obj)) {
    if (key != "id") {
      res += `${key} : ${value}\n`;
    }
  }
  return res;
}

function checkImagePresetType(obj: ImagePreset) {
  // タイプチェック
  for (let [key, value] of Object.entries(obj)) {
    if (key == "quality_toggle") {
      if (value == "True") {
        obj[key] = true;
      } else {
        obj[key] = false;
      }
    }
    if (key == "uc") {
      obj[key] = String(value);
    }
    if (key == "seed" || key == "steps" || key == "scale" ) {
      console.log(typeof value)
      if (!(typeof value == "string")) {
        delete obj[key];
      }
      obj[key] = Number(value)
    }
  }
  return obj;
}

// Express APP 作成
const app: express.Express = express();
// ポート番号指定
const PORT: number = Number(process.env.PORT) || 3000;
// 認証機能をすべてのリクエストに適用
app.use(express.json({ verify: VerifyDiscordRequest(process.env.PUBLIC_KEY) }));

// ユーザー情報
const userConifg: UserConfig = {};

// discordリクエストを処理する
app.post("/interactions", interactionCallback);

async function interactionCallback(req: Request, res: Response) {
  // インタラクションの内容を取得
  const { type, id, data} = req.body;
  // 検証
  if (type === InteractionType.PING) {
    return res.send({ type: InteractionResponseType.PONG });
  }

  // スラッシュコマンドの返答
  if (type === InteractionType.APPLICATION_COMMAND) {
    
    // コマンドタイプ取得
    const { name } = data;

    // スラッシュコマンド test
    if (name == "is_work") {
      // メッセージを送信する
      return res.send({
        type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        data: { content: "toukabot is work!"},
      });
    }

    // Pythonリクエスト
    if (name == "generate_image") {
      // ユーザーid取得
      const userId = req.body.member.user.id;
      const prompt = req.body.data.options[0].value;
      var response: any = "";
      // リクエストボディの作成
      let imageReqestBody: ImagePreset = {};

      // 設定の読み込み
      if (userId in userConifg) {
        imageReqestBody = checkImagePresetType(userConifg[userId]);
      }
      imageReqestBody["prompt"] = prompt;

      // waiting time...
      const wait_res: Response = res.send({
        type: InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
      });

      // 返信用データ取得
      const app_id:string = wait_res.req.body.application_id;
      const interaction_token:string = wait_res.req.body.token

      // API 送信
      response = await generateImage(imageReqestBody);

      // リクエストボディ作成
      const body = {
        embeds : [{
          title : "prompt",
          description : `${prompt}`,
          image: {url: response[0]},
          color: 0x00ff00,
          fields: [
            {
              name: "negative prompt",
              value: `${imageReqestBody["uc"]}`,
              inline: false,
            },
          ]
        }]
      };

      // 更新用エンドポイント
      const endpoint:string = `webhooks/${app_id}/${interaction_token}`;

      // 更新
      try {
        await DiscordRequest(endpoint, { method: 'POST', body: body });
      } catch (err) {
        console.error(err);
      }
    }

    // 画像生成設定コマンド
    if (name == "set_image_config" && id) {
      // ユーザーid取得
      const userId = req.body.member.user.id;
      // コンフィグ取得
      const options = req.body.data.options;
      // リターン用文字列
      let response: string = "config_no_change";

      // ユーザー設定保存
      if (!(userId in userConifg)) {
        userConifg[userId] = {
          id: userId,
        };
      }

      // オプションが選択されている場合
      if (options) {
        // コンフィグの保存
        options.forEach((option) => {
          // 型チェック
          userConifg[userId][option.name] = option.value;
        })
        response = createConfigReturn(userConifg[userId]);
      }
      console.log(userConifg[userId]);

      return res.send({
        type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        data: {
          content: response,
        }
      })
    }

    if (name == "show_image_setting" && id) {
      // ユーザーid取得
      const userId = req.body.member.user.id;
      let response:string = "";
      
      // 設定が保存されていない場合
      if (!(userId in userConifg)) {
        response = `<@${userId}>'s Default Settings`;
      }
      else {
        response = createConfigReturn(userConifg[userId])
      }

      // ユーザーid取得
      return res.send({
        type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        data: {
          content: response,
        }
      })
    }
  }
}


app.listen(PORT, () => {
  // coomands.jsのコマンドリストをインストールする
  HasGuildCommands(process.env.APP_ID, process.env.GUILD_ID, [
    CHECKWORK, // 起動チェック
    NAIGENERATEIMAGE, // NAI生成
    SETIMAGECONFIG, // NAI設定作成
    SHOWIMAGESETTING, // NAI設定参照
  ]);
  
  // スラッシュコマンド全削除
  //DeleteGuildCommandsAll(process.env.APP_ID, process.env.GUILD_ID);

  // 起動メッセージ
  console.log('Listening on port', PORT);
});
