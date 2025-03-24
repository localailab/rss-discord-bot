.PHONY: all build start stop restart clean test logs db db-dump

# コンテナ起動
all: build start

# Dockerイメージのビルド
build:
	docker-compose build

# コンテナの起動
start:
	docker-compose up -d

# コンテナの停止
stop:
	docker-compose down

# コンテナの再起動
restart: stop start

# コンテナとボリュームを削除
clean:
	docker-compose down -v
	docker system prune -f

# テストの実行
test:
	docker-compose run --rm rss-bot python -m unittest discover -s tests

# コンテナのログを表示
logs:
	docker-compose logs -f

# データベースにアクセス
db:
	docker exec -it rss-discord-bot sqlite3 /data/rss_data.db

# データベースの内容をダンプ
db-dump:
	docker exec -it rss-discord-bot sqlite3 /data/rss_data.db .dump > db_dump.sql

# テストの実行
test:
	docker-compose run --rm rss-bot python -m unittest discover -s src/tests