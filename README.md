# Gemini Deep Research 文章作成ツール

Google Gemini の Deep Research エージェントを活用して、トピックを自律的に調査し、包括的な日本語レポートを生成する CLI ツールです。

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. API キーの設定

[Google AI Studio](https://aistudio.google.com/apikey) で API キーを取得し、環境変数に設定してください。

```bash
export GEMINI_API_KEY='your-api-key-here'
```

## 使い方

### 基本的な調査

```bash
python deep_research_writer.py "量子コンピュータの最新動向"
```

### ファイルに保存

```bash
python deep_research_writer.py "再生可能エネルギーの未来" --output output/report.md
```

### リライト指示付き

調査結果を特定のスタイルにリライトできます。

```bash
python deep_research_writer.py "AIの医療応用" --refine "ブログ記事風にわかりやすく書き直して"
```

## オプション

| オプション | 短縮 | 説明 |
|---|---|---|
| `--output` | `-o` | 出力ファイルパス |
| `--stream` | `-s` | ストリーミングモードで進捗を表示 |
| `--refine` | `-r` | 調査結果のリライト指示 |

## 仕組み

1. **Deep Research** (`deep-research-pro-preview-12-2025`) がトピックを自律的に調査
2. Web 上の多数のソースから情報を収集・統合
3. 包括的な日本語レポートを生成
4. (オプション) Gemini モデルで指定スタイルにリライト
