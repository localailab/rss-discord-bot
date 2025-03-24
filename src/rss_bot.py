import feedparser
import sqlite3
import asyncio
import aiohttp
import datetime
import os
import re
from discord import Webhook, Embed
import logging

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('rss_bot')

# 環境変数から設定を読み込む
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', 300))  # デフォルトは300秒(5分)
DB_PATH = os.environ.get('DB_PATH', '/data/rss_data.db')  # デフォルトのパスを/data内に変更

# RSSフィードの設定
RSS_FEEDS = [
    {
        'name': 'BBC News',
        'url': 'http://feeds.bbci.co.uk/news/world/rss.xml',
        'webhook_url': os.environ.get('BBC_WEBHOOK_URL', '')
    },
    {
        'name': 'arXiv',
        'url': 'http://rss.arxiv.org/rss/cs.LG+cs.AI+cs.CL',
        'webhook_url': os.environ.get('ARXIV_WEBHOOK_URL', '')
    },
    {
        'name': 'OpenAI',
        'url': 'https://openai.com/news/rss.xml',
        'webhook_url': os.environ.get('AI_COMPANY_WEBHOOK_URL', '')
    },
    {
        'name': 'Hugging Face',
        'url': 'https://huggingface.co/blog/feed.xml',
        'webhook_url': os.environ.get('AI_COMPANY_WEBHOOK_URL', '')
    },
    {
        'name': 'Google AI',
        'url': 'https://research.google/blog/rss/',
        'webhook_url': os.environ.get('AI_COMPANY_WEBHOOK_URL', '')
    }
]

def init_database():
    # データベースディレクトリの存在確認
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # テーブルが既に存在するかチェック
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
    exists = cursor.fetchone()

    if exists:
        logger.info(f"データベースのテーブルは既に存在しています: {DB_PATH}")
    else:
        cursor.execute('''
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_name TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            published_date TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
        logger.info(f"データベースに新しいテーブルを作成しました: {DB_PATH}")

    conn.close()


def extract_image_from_feed(entry):
    """フィードエントリから画像URLを抽出する（簡易版）"""
    # メディア情報がある場合はそこから取得
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if 'url' in media:
                return media['url']
    
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        for media in entry.media_thumbnail:
            if 'url' in media:
                return media['url']
    
    # BBCニュース特有の処理
    if hasattr(entry, 'links'):
        for link in entry.links:
            if link.get('type', '').startswith('image/'):
                return link.get('href')
    
    # サマリーから画像URLを正規表現で取得（簡易的な方法）
    if hasattr(entry, 'summary'):
        img_match = re.search(r'<img[^>]+src="([^"]+)"', entry.summary)
        if img_match:
            src = img_match.group(1)
            if src.startswith('//'):
                src = 'https:' + src
            return src
    
    # BBCの記事URLから予測される画像URL（BBCのみ対応）
    if 'bbc.co.uk' in entry.link or 'bbc.com' in entry.link:
        # BBCの記事IDを抽出
        article_id_match = re.search(r'/([a-z0-9-]+)$', entry.link)
        if article_id_match:
            article_id = article_id_match.group(1)
            # BBCの記事サムネイルは通常このパターンに従う
            return f"https://ichef.bbci.co.uk/news/1024/branded_news/{article_id}.jpg"
    
    return None

async def send_to_discord(article, feed_info):
    webhook_url = feed_info.get('webhook_url')
    if not webhook_url:
        logger.error(f"{feed_info['name']}: Webhook URLが設定されていません")
        return False

    try:
        # 記事から画像を抽出
        image_url = extract_image_from_feed(article)
        
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(webhook_url, session=session)
            
            # 新しい記事が公開されたというメッセージを作成
            message_content = f"新しい記事が公開されました！\n【タイトル】: {article.get('title', 'タイトルなし')}\n{article.get('link', '')}"
            
            # 記事の内容を取得して埋め込み
            description = article.get('summary', '')
            if description:
                # HTMLタグを除去（簡易的な方法）
                description = re.sub(r'<.*?>', '', description)
                if len(description) > 200:
                    description = description[:200] + '...'
                
            # 埋め込みを作成
            embed = Embed(
                title=article.get('title', 'タイトルなし'),
                url=article.get('link', ''),
                description=description,
                color=0x3498db
            )
            
            # 画像があれば追加
            if image_url:
                embed.set_image(url=image_url)
            
            # 公開日を追加
            if 'published' in article:
                embed.add_field(name="公開日時", value=article['published'])
            
            # フッターにソース情報を追加
            embed.set_footer(text=f"Source: {feed_info['name']}")
            
            # メッセージとエンベッドを送信
            await webhook.send(content=message_content, embed=embed)
            logger.info(f"{feed_info['name']}: 記事を送信しました: {article.get('title')}")
            return True
    except Exception as e:
        logger.error(f"{feed_info['name']}: Discord送信エラー: {e}")
        return False

def is_article_sent(url):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM articles WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_article(feed_name, article):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO articles (feed_name, title, url, published_date) VALUES (?, ?, ?, ?)",
            (
                feed_name,
                article.get('title', 'タイトルなし'),
                article.get('link', ''),
                article.get('published', datetime.datetime.now().isoformat())
            )
        )
        conn.commit()
        logger.info(f"記事をデータベースに保存しました: {article.get('title')}")
    except sqlite3.IntegrityError:
        logger.warning(f"記事は既に存在します: {article.get('link')}")
    finally:
        conn.close()

async def check_feed(feed_info):
    feed_name = feed_info['name']
    feed_url = feed_info['url']
    feed = feedparser.parse(feed_url)

    sent_count = 0
    for entry in feed.entries:
        if is_article_sent(entry.get('link', '')):
            continue
        sent = await send_to_discord(entry, feed_info)
        if sent:
            save_article(feed_name, entry)
            sent_count += 1
            await asyncio.sleep(1) # Webhook送信後のスリープ

        await asyncio.sleep(0.5)  # 記事取得間隔を0.5秒スリープ

    return sent_count


async def main_loop():
    init_database()
    while True:
        total_sent = 0
        for feed_info in RSS_FEEDS:
            sent_count = await check_feed(feed_info)
            total_sent += sent_count
            logger.info(f"{feed_info['name']}: {sent_count}件の新規記事を送信しました")
            await asyncio.sleep(2)
        logger.info(f"チェック完了: 合計{total_sent}件の記事を送信しました")
        logger.info(f"{CHECK_INTERVAL}秒後に再度チェックします...")
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    logger.info("RSSボットを起動します...")
    asyncio.run(main_loop())