# 📡 RSS Discord Bot



**RSSフィードを定期的にチェックし、新着記事をDiscordに通知するDockerコンテナ化されたボットです。**

---

## 📋 特徴

- 📰 複数のRSSフィードを監視 (BBC News、arXiv、OpenAI、Hugging Face、Google AI)
- 🔔 新着記事をDiscordに自動通知
- 🖼️ 記事のサムネイル画像を表示 (利用可能な場合)
- 📊 SQLiteデータベースで記事履歴を管理
- 🐳 Docker Composeでかんたんデプロイ

---

## 🚀 セットアップとデプロイ

### 1️⃣ 必要な準備

- [DockerとDocker Compose](https://docs.docker.com/get-docker/)をインストール
- Discordでウェブフックを作成 (`各チャンネルの設定 → インテグレーション → ウェブフック`)

### 2️⃣ インストール

```bash
# リポジトリをクローン
git clone https://github.com/localailab/rss-discord-bot.git
cd rss-discord-bot

# .envファイルを作成
cp .env.example .env
# エディタで.envファイルを編集
```

### 3️⃣ 環境変数の設定

`.env`ファイルに以下の変数を設定してください：

```env
# 必須設定
BBC_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url_for_bbc
ARXIV_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url_for_arxiv
AI_COMPANY_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url_for_ai_companies

# オプション設定
CHECK_INTERVAL=300  # RSSフィードをチェックする間隔（秒単位、デフォルト: 300）
DB_PATH=/data/rss_data.db  # データベースファイルのパス
```

### 4️⃣ ボットの起動

```bash
# ビルドして起動
make all

# または直接コマンドを実行
docker-compose build
docker-compose up -d
```

---

## 📝 使い方

### ⚙️ 基本的なコマンド

Makefileを使用して簡単に操作できます：

| コマンド         | 説明                               |
| ---------------- | ---------------------------------- |
| `make all`       | ビルドして起動する                 |
| `make build`     | Dockerイメージをビルド             |
| `make start`     | コンテナを起動                     |
| `make stop`      | コンテナを停止                     |
| `make restart`   | コンテナを再起動                   |
| `make logs`      | ログを確認                         |
| `make db`        | データベースに接続                 |
| `make db-dump`   | データベースをファイルにダンプする |
| `make clean`     | コンテナとボリュームを削除         |

---

## 🗃️ データベース操作

記事履歴をクリアする方法：

```bash
# コンテナに入る
docker exec -it rss-discord-bot /bin/sh

# データベースに接続して記事を削除
sqlite3 /data/rss_data.db
> DELETE FROM articles;
> .quit

# または、データベースファイル自体を削除
rm /data/rss_data.db
```

---

## 🔧 カスタマイズ

新しいRSSフィードを追加したい場合は、`rss_bot.py`の`RSS_FEEDS`リストを編集します：

```python
RSS_FEEDS = [
    # 既存のフィード設定...
    {
        'name': '新しいフィード名',
        'url': 'https://example.com/feed.xml',
        'webhook_url': os.environ.get('NEW_FEED_WEBHOOK_URL', '')
    }
]
```

そして`.env`ファイルに対応するウェブフックURLを追加：

```env
NEW_FEED_WEBHOOK_URL=https://discord.com/api/webhooks/your_new_webhook_url
```

---

## ❓ トラブルシューティング

問題が発生した場合は、まずログを確認してください：

```bash
make logs
# または
docker-compose logs -f
```

一般的な問題：

- ウェブフックURLが正しくない → Discordでウェブフックを再作成
- RSSフィードにアクセスできない → インターネット接続とURLを確認

