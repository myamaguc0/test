"""送信済みアイテムを集計し、実績の棚卸し用のExcelとテキストを作る。

対象: Windows版の従来のOutlook（Exchange接続）
準備: pip install pywin32 pandas openpyxl
実行: Outlookを起動した状態で python export_sent.py
"""
import re
from collections import defaultdict
from datetime import datetime

import pandas as pd
import win32com.client

# ===== 設定 =====
START = datetime(2026, 4, 1)
END = datetime(2026, 11, 1)          # この日時より前まで
INTERNAL_DOMAINS = {"smm-g.com"}      # 社内とみなすドメイン
OUT_XLSX = "送信メール分析_2026-04_10.xlsx"
OUT_TXT = "AI入力用_案件別要約素材.txt"

# 本文のキーワードから「行動の種類」を判定する（上から順に最初に一致したもの）
ACTIONS = [
    ("提案・見積", ["ご提案", "提案書", "見積", "お見積"]),
    ("依頼・発注", ["ご依頼", "お願いいたします", "発注", "手配"]),
    ("回答・技術支援", ["ご回答", "回答", "ご質問", "確認しました", "手順書"]),
    ("報告・共有", ["ご報告", "共有", "議事録", "議事メモ", "FYI"]),
    ("調整・日程", ["日程", "打合せ", "打ち合わせ", "ご都合", "工程"]),
    ("お詫び・訂正", ["お詫び", "訂正", "申し訳"]),
]

# 引用部分の開始を示す行（ここから下は自分の文章ではない）
QUOTE_MARKERS = re.compile(
    r"^(-{3,}\s*Original Message|From:|差出人:|送信者:|_{10,}|On .+ wrote:)",
    re.MULTILINE,
)
SUBJECT_PREFIX = re.compile(r"^\s*((RE|FW|FWD|返信|転送|件名)\s*[:：]\s*)+", re.IGNORECASE)
PR_SMTP_ADDRESS = "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"
OL_MAIL = 43


def own_text(body):
    """引用を除いた、自分が書いた部分だけを返す。"""
    body = (body or "").replace("\r\n", "\n")
    m = QUOTE_MARKERS.search(body)
    return (body[: m.start()] if m else body).strip()


def thread_of(subject):
    return SUBJECT_PREFIX.sub("", subject or "").strip()


def smtp_of(recipient):
    try:
        return recipient.PropertyAccessor.GetProperty(PR_SMTP_ADDRESS)
    except Exception:
        try:
            return recipient.AddressEntry.GetExchangeUser().PrimarySmtpAddress
        except Exception:
            return recipient.Address or ""


def classify(text):
    for label, words in ACTIONS:
        if any(w in text for w in words):
            return label
    return "その他"


def classify_mail(subject, text):
    """返信では件名の【ご依頼】等が残り続けるため、自分の本文を優先して判定する。"""
    label = classify(text)
    return label if label != "その他" else classify(subject or "")


def build_project_map(inbox):
    """受信トレイ配下のフォルダ分けを使い、会話ID → フォルダ名 の対応表を作る。"""
    conv_to_folder = {}

    def walk(folder, path):
        for sub in folder.Folders:
            p = f"{path}/{sub.Name}" if path else sub.Name
            for it in sub.Items:
                try:
                    conv_to_folder.setdefault(it.ConversationID, p)
                except Exception:
                    pass
            walk(sub, p)

    walk(inbox, "")
    return conv_to_folder


def main():
    ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    print("受信トレイのフォルダ分けを読み込み中...")
    project_map = build_project_map(ns.GetDefaultFolder(6))  # 6 = 受信トレイ

    items = ns.GetDefaultFolder(5).Items  # 5 = 送信済みアイテム
    items.Sort("[SentOn]", True)

    rows = []
    for i, m in enumerate(items):
        if i % 200 == 0:
            print(f"  {i} 件目を処理中...")
        try:
            if m.Class != OL_MAIL:
                continue
            sent = m.SentOn.replace(tzinfo=None)
        except Exception:
            continue
        if sent >= END:
            continue
        if sent < START:
            break

        addrs = [smtp_of(r) for r in m.Recipients]
        domains = sorted({a.split("@")[-1].lower() for a in addrs if "@" in a})
        external = [d for d in domains if d not in INTERNAL_DOMAINS]
        text = own_text(m.Body)
        rows.append({
            "送信日時": sent,
            "月": sent.strftime("%Y-%m"),
            "案件(フォルダ)": project_map.get(m.ConversationID, "未分類"),
            "スレッド": thread_of(m.Subject),
            "件名": m.Subject,
            "宛先": m.To,
            "CC": m.CC,
            "社外ドメイン": ", ".join(external),
            "社外宛": bool(external),
            "宛先数": len(addrs),
            "添付数": m.Attachments.Count,
            "行動の種類": classify_mail(m.Subject, text),
            "自分の本文": text[:1000],
        })

    df = pd.DataFrame(rows)
    print(f"対象メール: {len(df)} 件")

    by_month = df.pivot_table(index="月", columns="社外宛", values="件名",
                              aggfunc="count", fill_value=0)
    by_month.columns = ["社内のみ" if not c else "社外あり" for c in by_month.columns]
    by_project = (df.groupby("案件(フォルダ)")
                    .agg(件数=("件名", "count"), 開始=("送信日時", "min"),
                         終了=("送信日時", "max"), スレッド数=("スレッド", "nunique"))
                    .sort_values("件数", ascending=False))
    by_thread = (df.groupby(["案件(フォルダ)", "スレッド"])
                   .agg(件数=("件名", "count"), 開始=("送信日時", "min"),
                        終了=("送信日時", "max"))
                   .sort_values("件数", ascending=False))
    by_domain = (df.assign(ドメイン=df["社外ドメイン"].str.split(", "))
                   .explode("ドメイン").query("ドメイン != ''")
                   .groupby("ドメイン").size().rename("件数")
                   .sort_values(ascending=False))
    by_action = df.pivot_table(index="行動の種類", columns="月", values="件名",
                               aggfunc="count", fill_value=0)

    with pd.ExcelWriter(OUT_XLSX) as xw:
        df.to_excel(xw, sheet_name="一覧", index=False)
        by_month.to_excel(xw, sheet_name="月別")
        by_project.to_excel(xw, sheet_name="案件別")
        by_thread.head(100).to_excel(xw, sheet_name="スレッド上位100")
        by_domain.to_excel(xw, sheet_name="社外相手別")
        by_action.to_excel(xw, sheet_name="行動の種類別")

    # AIに渡す素材: 案件ごとに、件数の多いスレッドとその最初・最後の自分の本文
    lines = []
    for proj, g in df.groupby("案件(フォルダ)"):
        lines.append(f"\n## 案件: {proj}（送信 {len(g)} 件）")
        for th, tg in g.groupby("スレッド"):
            if len(tg) < 3:
                continue
            tg = tg.sort_values("送信日時")
            lines.append(f"\n### {th}（{len(tg)} 件, "
                         f"{tg['送信日時'].min():%m/%d}〜{tg['送信日時'].max():%m/%d}）")
            for _, r in pd.concat([tg.head(1), tg.tail(1)]).drop_duplicates().iterrows():
                lines.append(f"[{r['送信日時']:%m/%d}] {r['自分の本文'][:400]}")
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"出力しました: {OUT_XLSX}, {OUT_TXT}")


if __name__ == "__main__":
    main()
