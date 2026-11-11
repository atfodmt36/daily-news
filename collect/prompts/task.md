# 工程の指示: 日次の AI ニュース収集

期間 **{{FROM}} から {{TO}}**（いずれも日本時間）に公開された AI 関連の発表を、
下の監視対象すべてについて確認し、結果を 1 つの JSON オブジェクトで返します。

## 対象（この順に確認する。すべての対象を必ず確認する）

| key | items の topic | 備考 |
| --- | --- | --- |
| `microsoft-365-copilot` | Microsoft 365 Copilot | |
| `anthropic` | Claude | Claude のサービス・API・モデル（Claude Code は別対象） |
| `claude-code` | Claude Code | |
| `openai` | ChatGPT | OpenAI のモデル・API・ChatGPT 製品 |
| `codex` | Codex | |
| `jp-gov` | 日本政府・行政 | AI 政策・ガイドライン・法制度など。会議開催・資料公開だけのものは除く |
| `google` | Gemini | Gemini のモデル・API を重点。消費者向けサービスは除く |
| `microsoft-foundry` | Microsoft Foundry | |
| `construction-ai` | 建設×AI | |
| `3d-model-ai` | 3Dモデル×AI | |
| `3dgs-ai` | 3DGS×AI | |
| `jp-models` | 国産モデル | 日本のモデルと、日本語に強いモデルの大型更新 |
| `ai-business` | AIビジネス | 一次レポートに具体的な数値があるものだけ |
| `github-copilot` | GitHub Copilot | 任意対象（時間が足りなければ未確認でよい） |
| `gemini-cli` | Gemini CLI | 任意対象（時間が足りなければ未確認でよい） |

- 対象ごとに、確認先一覧のページ/フィードを 1〜3 個開き、期間内の更新を探します。足りない分は WebSearch で補います
- 見つけた発表は優先度にかかわらず items に入れます（宣伝だけのもの、感想・まとめ記事そのものは入れません。一次情報に遡ります）
- 上の 15 対象以外の大手の発表（Mistral・Meta・NVIDIA 等）を見つけたら topic を「その他」にして入れてよいです

## 出力する JSON

```json
{
  "date": "{{DATE}}",
  "generatedAt": "{{GENERATED_AT}}",
  "checked": [
    {"key": "microsoft-365-copilot", "status": "確認済み", "count": 2, "note": "", "sources": ["https://..."]}
  ],
  "items": [
    {"id": "anthropic-claude-opus-5", "topic": "Claude", "headline": "何が起きたかが分かる日本語の見出し",
     "summary": "日本語 1〜2 文。数値は条件とセットで", "url": "https://一次情報のURL",
     "source": "発表元の名称", "published_at": "2026-11-09T15:00:00+09:00", "unconfirmed": false,
     "status": "ga", "tags": [], "related_urls": []}
  ]
}
```

- `checked` は 15 対象すべてについて 1 件ずつ書きます。確認先を開けて確かめたら status は `"確認済み"`、開けなければ `"未確認"` にし、note に理由と試した方法を書きます。`"確認済み"` のときは sources に実際に開いた URL を 1 件以上書きます
- 固定の確認先が無い対象（建設×AI・3Dモデル×AI・3DGS×AI・国産モデル・AIビジネス）は、確認先一覧に書かれた検索を日本語・英語の両方で実行し、見つけた候補の一次情報を開いて確かめたら `"確認済み"` にしてかまいません（sources には開いた一次情報や公式のニュース一覧の URL）。検索自体が実行できなかったときだけ `"未確認"` にします
- `count` は、その対象について期間内に見つけた発表の件数です（0 は更新なし）。原則として items のうち topic がその対象のものと一致させます
- items の `id` は英小文字・数字・ハイフンの kebab-case で、全体で一意にします
- `url` は一次情報の https URL です。`source` は発表元（企業・機関・媒体）の名称です
- `published_at` は発表の公開時刻（ISO 8601、タイムゾーン付き）。時刻が分からず日付だけの場合はその日の `T00:00:00+09:00` とし、tags に `"date-only"` を付けます
- `status` は ga / preview / beta / announced / deprecated / policy / other のどれか（分かる場合のみ）
- 一次情報で裏が取れない発表は `unconfirmed: true` にします
- items は最大 30 件です
