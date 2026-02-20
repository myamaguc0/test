"""
Gemini Deep Research を活用した文章作成ツール

Google Gemini の Deep Research エージェントを使って、
トピックを自律的に調査し、包括的なレポートを生成します。

使い方:
    python deep_research_writer.py "調査したいトピック"
    python deep_research_writer.py "調査したいトピック" --output report.md
    python deep_research_writer.py "調査したいトピック" --stream
"""

import argparse
import os
import sys
import time

from google import genai

DEEP_RESEARCH_AGENT = "deep-research-pro-preview-12-2025"
GEMINI_MODEL = "gemini-2.5-flash"
POLL_INTERVAL_SEC = 10


def create_client() -> genai.Client:
    """Gemini APIクライアントを作成する。"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("エラー: 環境変数 GEMINI_API_KEY を設定してください。")
        print("  export GEMINI_API_KEY='your-api-key-here'")
        sys.exit(1)
    return genai.Client(api_key=api_key)


def run_deep_research(client: genai.Client, topic: str, stream: bool = False) -> str:
    """Deep Researchエージェントでトピックを調査し、結果を返す。

    Args:
        client: Gemini APIクライアント
        topic: 調査するトピック
        stream: ストリーミングモードで進捗を表示するか

    Returns:
        調査結果のテキスト
    """
    prompt = (
        f"以下のトピックについて徹底的に調査し、"
        f"日本語で包括的なレポートを作成してください。\n\n"
        f"トピック: {topic}\n\n"
        f"レポートには以下を含めてください:\n"
        f"- 概要・背景\n"
        f"- 主要なポイントの詳細な説明\n"
        f"- 最新の動向やデータ\n"
        f"- 参考情報源\n"
    )

    print(f"Deep Research を開始します: {topic}")
    print("（調査には数分かかる場合があります）\n")

    # バックグラウンドでDeep Researchを開始
    interaction = client.interactions.create(
        agent=DEEP_RESEARCH_AGENT,
        input=prompt,
        background=True,
    )
    interaction_id = interaction.id
    print(f"調査ID: {interaction_id}")

    # ポーリングで完了を待つ
    while True:
        interaction = client.interactions.get(interaction_id)

        if interaction.status == "completed":
            print("\n調査が完了しました。\n")
            return interaction.outputs[-1].text

        if interaction.status == "failed":
            error_msg = getattr(interaction, "error", "不明なエラー")
            print(f"\n調査が失敗しました: {error_msg}")
            sys.exit(1)

        # 進捗表示
        print(".", end="", flush=True)
        time.sleep(POLL_INTERVAL_SEC)


def refine_with_gemini(client: genai.Client, research_text: str, instructions: str) -> str:
    """Geminiモデルで調査結果をリライト・整形する。

    Args:
        client: Gemini APIクライアント
        research_text: Deep Researchの調査結果
        instructions: リライトの指示

    Returns:
        整形されたテキスト
    """
    prompt = (
        f"以下の調査レポートを、指示に従って整形・リライトしてください。\n\n"
        f"## 指示\n{instructions}\n\n"
        f"## 調査レポート\n{research_text}"
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return response.text


def save_output(text: str, filepath: str) -> None:
    """テキストをファイルに保存する。"""
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"ファイルに保存しました: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Gemini Deep Research を活用した文章作成ツール"
    )
    parser.add_argument("topic", help="調査するトピック")
    parser.add_argument(
        "--output", "-o",
        help="出力ファイルパス (例: output/report.md)",
    )
    parser.add_argument(
        "--stream", "-s",
        action="store_true",
        help="ストリーミングモードで進捗を表示",
    )
    parser.add_argument(
        "--refine", "-r",
        help="調査結果をリライトする際の追加指示 (例: 'ブログ記事風に書き直して')",
    )
    args = parser.parse_args()

    client = create_client()

    # Deep Researchで調査
    research_result = run_deep_research(client, args.topic, stream=args.stream)

    # リライト指示がある場合は追加処理
    if args.refine:
        print(f"リライト中: {args.refine}\n")
        final_text = refine_with_gemini(client, research_result, args.refine)
    else:
        final_text = research_result

    # 結果の出力
    print("=" * 60)
    print(final_text)
    print("=" * 60)

    # ファイル保存
    if args.output:
        save_output(final_text, args.output)


if __name__ == "__main__":
    main()
