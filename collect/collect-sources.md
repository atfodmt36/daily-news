# AI Radar Claude Code collect — 対象ごとの確認先（一次情報）

収集では、対象ごとに下の確認先を先に開き（フィードがあればフィード優先）、
足りない分を WebSearch で補います。ここに無い発表も WebSearch で拾ってよいですが、
一次情報（公式ページ・リリースノート・公式ブログ・公的資料）まで遡って確認します。

- WebFetch が 403 を返すサイト: openai.com・help.openai.com・meti.go.jp。
  代わりに RSS や WebSearch の結果（タイトル・日付・抜粋）で確かめ、確認方法を checked の note に書きます
- Microsoft 365 のメッセージセンター本体はテナントログインが要るため開けません。
  公開アーカイブ（下記）で見つけ、公式ページで裏を取ります。取れなければ tags に "secondary" を付けます
- URL が開けないときは、その対象の checked を「未確認」にし、note に理由と試した方法を書きます

## microsoft-365-copilot（Microsoft 365 Copilot）

- Microsoft 365 Copilot のリリースノート: https://learn.microsoft.com/en-us/microsoft-365/copilot/release-notes
- Microsoft 365 ロードマップ（RSS。タイトル・本文に Copilot を含む項目）: https://www.microsoft.com/releasecommunications/api/v2/m365/rss
- メッセージセンターの公開アーカイブ（RSS。公式ではない）: https://mc.merill.net/rss.xml

機能だけでなく、料金・ライセンス・管理・セキュリティ・提供範囲（プラン・地域・日本語）・搭載モデルの変更を拾います。

## anthropic（Claude。topic は "Claude"）

- Anthropic News: https://www.anthropic.com/news
- Claude Platform のリリースノート: https://platform.claude.com/docs/en/release-notes/overview
- Claude アプリのリリースノート: https://support.claude.com/en/articles/12138966-release-notes

モデル・API に加えてサービス面（claude.ai・アプリの機能、Team/Enterprise の管理機能、料金・プラン、利用制限・文脈長）も見ます。

## claude-code（Claude Code。topic は "Claude Code"）

- GitHub Releases（Atom）: https://github.com/anthropics/claude-code/releases.atom
- CHANGELOG.md（raw）: https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md

版が毎日のように出ます。ウィンドウ内の版を全部確かめ、新機能・権限/Sandbox・MCP・Skills/Subagents・認証・料金/利用制限の変更を拾います。小さな版の連続は 1 件にまとめてよいです。

## openai（OpenAI。topic は "ChatGPT"）

- OpenAI News（RSS）: https://openai.com/news/rss.xml
- API の changelog: https://developers.openai.com/api/docs/changelog
- ChatGPT のリリースノートは 403 のため WebSearch で確認: https://help.openai.com/en/articles/6825453-chatgpt-release-notes

モデル・API・ChatGPT/Codex 製品の発表を見ます（Codex の版情報は codex 対象が主担当）。

## codex（Codex。topic は "Codex"）

- GitHub Releases（Atom。alpha は除く）: https://github.com/openai/codex/releases.atom
- ChatGPT & Codex の Changelog: https://learn.chatgpt.com/docs/changelog

## jp-gov（日本政府・行政。topic は "日本政府・行政"）

- デジタル庁 新着（RSS）: https://www.digital.go.jp/rss/news.xml
- 首相官邸 新着（RSS）: https://www.kantei.go.jp/index-jnews.rdf
- 総務省 報道資料（RSS）: https://www.soumu.go.jp/news.rdf
- 個人情報保護委員会 お知らせ: https://www.ppc.go.jp/news/
- e-Gov パブリックコメント（案件名に「AI」「生成AI」「人工知能」「個人情報」「著作権」を含むもの）: https://public-comment.e-gov.go.jp/pcm/list

AI 政策・ガイドライン・法制度・政府調達・個人情報/著作権/セキュリティに関わるものを拾います。会議の開催・資料公開だけのものは対象外です。

## google（Google。topic は "Gemini"）

- Gemini API の changelog: https://ai.google.dev/gemini-api/docs/changelog
- Vertex AI 生成 AI のリリースノート: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/release-notes
- Google 公式ブログ AI（RSS）: https://blog.google/technology/ai/rss/

Gemini のモデル・API（モデルの追加・更新・価格・提供状態・廃止）を重点に見ます。消費者向けサービスの話は対象外です。

## microsoft-foundry（Microsoft Foundry。topic は "Microsoft Foundry"）

- Microsoft Foundry の新着情報: https://learn.microsoft.com/en-us/azure/foundry/whats-new-foundry
- Microsoft Foundry Blog（RSS）: https://devblogs.microsoft.com/foundry/feed/
- Azure OpenAI の新着情報: https://learn.microsoft.com/en-us/azure/foundry-classic/openai/whats-new

## construction-ai（建設×AI。topic は "建設×AI"）

範囲（オーナー指示 2026-11-10）: 「建設」だけでなく、建築・土木・施工・測量・設計の各分野の AI 活用まで広く対象にします。報告上の topic はすべて "建設×AI" に統一します。
キーワード（オーナー指示 2026-11-11）: BIM、CIM、4DGS（4D Gaussian Splatting）、PLATEAU（国土交通省の3D都市モデル）も対象に含めます。
固定のフィードはありません。WebSearch を日本語・英語の両方で実行します。
検索の例: 日本語「建設 AI 発表」「建築 AI 発表」「土木 AI 導入」「施工 AI 開始」「測量 AI 発表」「設計 AI 導入」「i-Construction AI」「建設 DX AIエージェント 開始」「BIM AI 発表」「CIM AI 導入」「PLATEAU AI」「4DGS 建設」＋対象期間の日付、
英語「Autodesk/Bentley/Trimble/Nemetschek AI announcement」「4D Gaussian Splatting construction」＋期間。
日本の建設会社・建設テック企業の発表は日本語検索でないと見つかりにくいので、日本語の検索語を複数試します。
発見の入口として業界メディア（日経クロステック・建設通信新聞等）の記事を使ってよいですが、
items に入れるときはベンダーの公式発表（Autodesk・Bentley・Trimble・Nemetschek・Graphisoft 等の
プレスリリース・公式ブログ）や建設会社・建設テック企業の公式発表まで遡ります。
ニュース記事だけが情報源のものは unconfirmed: true にします。

## 3d-model-ai（3Dモデル×AI。topic は "3Dモデル×AI"）

固定のフィードはありません。WebSearch（主に英語）で 3D 生成・点群・フォトグラメトリの
モデル/サービスの発表を探し、企業ブログ・GitHub リリース・Hugging Face・論文（arXiv）などの一次情報で確認します。

## 3dgs-ai（3DGS×AI。topic は "3DGS×AI"）

固定のフィードはありません。WebSearch（主に英語、"Gaussian Splatting" 等）で
3DGS のモデル・ツール・ライブラリ・主要論文の発表を探し、一次情報で確認します。

## jp-models（国産モデル。topic は "国産モデル"）

固定のフィードはありません。WebSearch（主に日本語）で日本の AI 企業・研究機関の
モデル公開・更新を探し、公式ブログ・ニュースリリース・Hugging Face のモデルページで確認します。
主な対象: Preferred Networks（PLaMo）・Sakana AI・ELYZA・rinna・NTT・富士通・NEC・Stability AI Japan 等。
日本語に強い海外モデル（日本語対応の大型更新）も含みます。

## ai-business（AIビジネス。topic は "AIビジネス"）

固定のフィードはありません。WebSearch（日本語・英語）で AI の人材育成・スキル・生産性指標を探します。
**一次レポートに具体的な数値があるものだけ**を items に入れます（導入事例の定量効果、公式調査の数値など）。
数値のない一般論・意見記事は対象外です。
業務×AI（オーナー指示 2026-11-10）: 人事・経理・総務・法務・営業・カスタマーサポートといった事務寄り・営業部門の業務への AI 適用も対象に含めます（部門特化の AI 製品・サービスの開始、企業名のある導入事例など）。この範囲については、具体的な製品開始や企業名のある導入事例であれば数値が無くても入れてかまいません。一般論・意見記事は引き続き対象外です。
検索の例: 「人事 AI 導入」「経理 AIエージェント 開始」「総務 AI 活用」「法務 AI 発表」「営業 AI 支援 導入」「カスタマーサポート AI 開始」＋対象期間の日付、英語「HR/accounting/legal/sales/customer support AI launch」＋期間。
AIビジネス全般（オーナー指示 2026-11-10）: AI が広がる中での採用（新卒採用・中途採用の動向や方針）、求められるスキル、AI 導入の効果測定（方法と結果）、AI の組織導入の進め方（全社展開・体制・ガバナンスの事例）も対象に含めます。条件は同じで、一次レポートの数値か、企業名のある具体的な方針・事例があるものを入れます。
検索の例: 「新卒採用 AI 影響 調査」「中途採用 AI スキル」「AI 導入 効果測定」「AI 組織導入 事例」「全社 AI 展開 発表」＋対象期間の日付、英語「AI hiring survey」「measuring AI impact report」「enterprise AI rollout case」＋期間。

## github-copilot（GitHub Copilot。任意対象。topic は "GitHub Copilot"）

- GitHub Changelog の Copilot（RSS）: https://github.blog/changelog/label/copilot/feed/

## gemini-cli（Gemini CLI。任意対象。topic は "Gemini CLI"）

- リリースノート: https://geminicli.com/docs/changelogs/
- GitHub Releases（Atom。nightly・preview は除く）: https://github.com/google-gemini/gemini-cli/releases.atom
