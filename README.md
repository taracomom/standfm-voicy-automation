# StandFM → Voicy → X投稿 自動化プロジェクト

## 📋 プロジェクト概要

**目的**: StandFMの新エピソード公開を検知し、Voicyの最新URLを取得、音声を文字起こしして要約をX投稿する

**技術スタック**: Python + GitHub Actions + Make.com

## 🛠️ セットアップガイド

1.  リポジトリをクローンします。
2.  Python 仮想環境を作成し、アクティベートします。
    ```bash
    python -m venv venv
    # Linux/macOS: source venv/bin/activate
    # Windows: venv\Scripts\activate
    ```
3.  必要なパッケージをインストールします。
    ```bash
    pip install -r requirements.txt
    ```
4.  `.env.example` をコピーして `.env` ファイルを作成し、環境変数を設定します。
    ```bash
    cp .env.example .env
    ```
5.  必要な環境変数を `.env` ファイルに設定してください:
    - `STANDFM_RSS_URL`
    - `MAKE_WEBHOOK_URL`
    - `OPENAI_API_KEY` (オプション)

## 開発手順

### Phase 1: 基本機能
1. RSS監視機能の実装 (`src/rss_checker.py`)
2. Voicyスクレイピング機能 (`src/voicy_scraper.py`)
3. GitHub Actions基本設定 (`.github/workflows/main.yml`)

### Phase 2: 音声処理
1. 音声ダウンロード機能 (`src/audio_processor.py`)
2. Whisper統合 (`src/audio_processor.py`)
3. エラーハンドリング

### Phase 3: 要約・投稿
1. テキスト要約機能 (`src/text_summarizer.py`)
2. Make.com Webhook連携 (`src/webhook_sender.py`)
3. Buffer設定

### Phase 4: 運用・最適化
1. ログ監視
2. エラー通知
3. パフォーマンス最適化
