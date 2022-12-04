import fetch from 'node-fetch';
import * as dotenv from 'dotenv';
import * as fs from 'fs';
dotenv.config();


process.env.CLOUDFLAREAPI

let url:string = `https://api.cloudflare.com/client/v4/accounts/${process.env.CLOUDFLAREUSERID}`;
let endpoint:string = "/images/v1";

async function _request(endpoint:string, method:string) {
    url = url + endpoint; // エンドポイントの作成

    // APIの送信
    const res = await fetch(
        url, 
        {
            method: method,
            headers: {
                Authorization: `Bearer  ${process.env.CLOUDFLAREAPI}`,
                'Content-Type': 'multipart/form-data',
            },
            body: {
                file: fs.createReadStream("./Gril.png")
            }

        }
    ) 
    console.log(res.status);
}

_request(endpoint, "POST").then(r => console.log(r));
