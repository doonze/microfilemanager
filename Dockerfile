# how to build?
# docker login
## .....input your docker id and password
#docker build . -t doonze/microfilemanager:master
#docker push doonze/microfilemanager:master

# how to use?
# docker run -d -v /absolute/path:/var/www/html/data -p 80:80 --restart=always --name microfilemanager doonze/microfilemanager:master

FROM php:8.2-cli-alpine

# if run in China
# RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

RUN apk add --no-cache \
    libzip-dev \
    oniguruma-dev

RUN docker-php-ext-install \
    zip 

WORKDIR /var/www/html

COPY microfilemanager.php index.php
COPY translation.json translation.json

CMD ["sh", "-c", "php -S 0.0.0.0:80"]
