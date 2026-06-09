# TenKToMillion

日本株を対象に、初期資金 10,000 円から短期売買の検証を行う AI ペーパートレード Bot です。

初期実装では実売買を一切行いません。実注文機能は将来接続用のインターフェースのみを用意し、公式 API 以外の証券サイトスクレイピングやブラウザ自動操作は禁止します。

## 構成

```text
trading-bot/
  backend/   FastAPI + SQLite + APScheduler + pandas
  frontend/  React + Vite + TypeScript + Recharts + TanStack Table
```

## 最短セットアップ Docker

Docker Desktop が起動している状態で、リポジトリ直下から実行します。

```bash
cp trading-bot/backend/.env.example trading-bot/backend/.env
docker compose up --build
```

起動後に以下へアクセスします。

- Dashboard: `http://localhost:5173`
- API: `http://localhost:8000`
- Health: `http://localhost:8000/api/health`

SQLite DB は Docker volume `tenk_data` の `/data/tenk_to_million.db` に永続化されます。コンテナを止めても実績データは残ります。

## 明日から実績を作るための設定

J-Quants APIキーを設定したうえで、公式APIデータを使って動かします。Yahoo系データは障害時の予備データソースです。

```text
DATA_SOURCE=jquants
YAHOO_FINANCE_ENABLED=true
MARKET_SYMBOLS=3778,2160,4565,6920,5253,7014,1514,5586,5595,6526
SCHEDULER_ENABLED=true
```

この設定でDocker起動すると、Asia/Tokyoのスケジュールで自動実行されます。

```text
08:30 候補銘柄抽出
09:10 ペーパートレード
15:30 日次分析
15:45 LLM日次分析
16:00 LLM提案バックテスト
16:15 改善案生成
```

設計上の `09:00〜09:10 監視のみ`、`10:30 新規エントリー停止`、`14:45 強制決済` は、現MVPではペーパートレードのシミュレーション内ルールとして扱っています。実時間でポジションを持ち続ける実売買・常時監視プロセスはまだ実装していません。

手動で当日分を作る場合は、Dashboard のボタンまたは以下を実行します。

```bash
curl -X POST http://localhost:8000/api/bot/run-screening
curl -X POST http://localhost:8000/api/bot/run-paper-trade
curl -X POST http://localhost:8000/api/bot/run-analysis
curl -X POST http://localhost:8000/api/bot/run-optimization
```

## Secret 設定

Yahoo系データ取得にはSecretは不要です。J-Quantsを使う場合は、J-Quants API V2のAPIキーを設定します。

```text
DATA_SOURCE=jquants
JQUANTS_API_KEY=...
```

旧APIの互換用として `JQUANTS_EMAIL` / `JQUANTS_PASSWORD` も読み込みますが、通常は `JQUANTS_API_KEY` を使ってください。

LLM Analystを使う場合はOpenAI APIキーが必要です。未設定の場合、AI分析は明示的に失敗します。

```text
OPENAI_API_KEY=...
OPENAI_ANALYST_MODEL=gpt-4.1-mini
```

LLMは売買注文を出しません。出力はDBへ保存され、提案パラメータは `strategy_experiments` に検証候補として保存されます。提案は即時採用されず、バックテスト結果と採用条件の確認対象になります。

### Secretの安全な配置

APIキーやパスワードをターミナル履歴やチャットに残さないため、`set_secret.py` で `.env` を更新します。

```bash
cd trading-bot/backend
python scripts/set_secret.py OPENAI_API_KEY
python scripts/set_secret.py OPENAI_ANALYST_MODEL --value gpt-4.1-mini
python scripts/set_secret.py DATA_SOURCE --value jquants
python scripts/set_secret.py JQUANTS_API_KEY
```

`OPENAI_API_KEY` は OpenAI Platform の API keys 画面で作成します。表示されたキーはこのスクリプトのプロンプトに貼り付けてください。`.env` は `.gitignore` 対象なのでcommitされません。

`JQUANTS_API_KEY` は J-Quants のAPIキー管理画面で作成します。J-Quantsが使えない場合のみ `DATA_SOURCE=yahoo` に切り替えてください。

`.env` は `.gitignore` 対象です。実際の認証情報はGitHubにcommitしないでください。

## `.env` 例

```text
APP_ENV=local
DATABASE_PATH=./tenk_to_million.db
DATA_SOURCE=jquants
INITIAL_CASH=10000
JQUANTS_API_KEY=
JQUANTS_EMAIL=
JQUANTS_PASSWORD=
YAHOO_FINANCE_ENABLED=true
OPENAI_API_KEY=
OPENAI_ANALYST_MODEL=gpt-4.1-mini
MARKET_SYMBOLS=3778,2160,4565,6920,5253,7014,1514,5586,5595,6526
SCHEDULER_ENABLED=true
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

`JQuantsCollector` は J-Quants API V2 のAPIキー認証で上場銘柄情報と日足四本値を取得します。`YahooCollector` はYahoo Finance系のチャートデータを利用して日足・5分足相当のデータを取得します。認証情報が未設定、またはYahoo取得が無効な場合は明示的に失敗し、秘密情報をログに出しません。

## 設計書との差分と現在の実装状態

現状は、初期設計の「Mockでも全機能を動かす」段階から進めて、J-Quants実データ前提のローカルMVPに寄せています。

```text
実装済み:
- FastAPI backend / React Vite frontend / SQLite / APScheduler
- J-Quants API V2 x-api-key 認証
- Yahoo系データ取得口
- 候補生成、スコアリング、4戦略比較
- 3資金管理モードの同時ペーパー検証
- 日次レポート、戦略比較、改善案保存、採用済みパラメータ反映
- OpenAI LLM Analyst、JSON検証、提案リプレイバックテスト
- 10:30 新規エントリー停止、14:45 仮想ポジション強制決済ジョブ
- Docker Compose ローカル起動
- GitHub Actions CI

意図的に実装しない/無効化:
- 実売買、証券口座発注、信用取引、空売り、レバレッジ
- 証券サイトスクレイピング、ブラウザ自動操作による注文
- Mockデータソースの実運用選択肢

未完成/今後の強化対象:
- SQLAlchemyモデル分離
- pytest化とテスト粒度の拡張
- 5分足・板・スプレッド・ニュース取得の実データ連携
- 直近3営業日安定性を含む採用判定の高度化
- kabuステーションAPIなど公式実売買API接続
```

`MockCollector` と `MockAnalystClient` は、J-Quants/OpenAIの実キーを使う運用に切り替えたため削除しました。テストでは外部APIに依存しない `FakeCollector` / `FakeAnalystClient` を使い、CIでパイプラインを検証しています。

## ローカル開発

Dockerを使わずに起動する場合です。

### Backend

```bash
cd trading-bot/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.db
uvicorn app.main:app --reload
```

### Frontend

```bash
cd trading-bot/frontend
npm install
npm run dev
```

## テスト・CI

ローカルで主要検証を実行する場合です。

```bash
docker compose run --rm backend python -m unittest discover -s tests
cd trading-bot/frontend
npm run build
cd ../..
docker compose config --quiet
docker compose build backend frontend
```

GitHub Actionsでは以下を実行します。

```text
Backend Tests: Python compile + unittest
Frontend Build: npm ci + npm run build
Docker Build: compose config + backend/frontend image build
Security Checks: Secret文字列スキャン + whitespace check
```

CI用に `.env.example` を `.env` へコピーしてDocker構成を検証します。実際の `.env` とAPIキーはGitHubにcommitしません。

## API一覧

```text
GET  /api/health
GET  /api/dashboard
GET  /api/candidates/today
GET  /api/market-snapshots
GET  /api/trades
GET  /api/positions
GET  /api/reports/daily
GET  /api/strategy/params
GET  /api/strategy/comparison
GET  /api/experiments
GET  /api/llm/reports
GET  /api/llm/reports/latest
GET  /api/llm/runs
POST /api/bot/run-screening
POST /api/bot/run-paper-trade
POST /api/bot/stop-new-entries
POST /api/bot/force-exit-all-positions
POST /api/bot/run-analysis
POST /api/bot/run-optimization
POST /api/bot/set-mode
POST /api/bot/set-data-source
POST /api/bot/set-strategy
POST /api/llm/run-daily-analysis
POST /api/llm/backtest-proposals
```

## 注意事項

- 現物のみ、信用取引・空売り・レバレッジは禁止です。
- 同時保有は 1 銘柄まで、ナンピンは禁止です。
- 初期資金は 10,000 円です。
- 14:45 強制決済を前提に、持ち越しは禁止です。
- 実売買は初期実装では不可です。
- `ENABLE_LIVE_TRADING` は現時点では実装していません。将来追加しても、RiskGuardと公式API接続の検収が終わるまで実注文は行いません。
- 投資判断は自己責任です。このアプリは利益を保証しません。
