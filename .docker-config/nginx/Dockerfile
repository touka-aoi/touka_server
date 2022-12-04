FROM nginx

#Nginx設定ファイルを削除
RUN rm -f /etc/nginx/conf.d/*

RUN mkdir /etc/nginx/cert

COPY ./cert/* /etc/nginx/cert/