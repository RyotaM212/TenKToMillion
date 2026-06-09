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

まずはAPIキー不要のYahoo系リアルデータで動かすのが最短です。

```text
DATA_SOURCE=yahoo
YAHOO_FINANCE_ENABLED=true
MARKET_SYMBOLS=3778,2160,4565,6920,5253,7014,1514,5586,5595,6526
SCHEDULER_ENABLED=true
```

この設定でDocker起動すると、Asia/Tokyoのスケジュールで自動実行されます。

```text
08:30 候補銘柄抽出
09:10 ペーパートレード
15:30 日次分析
16:00 改善案生成
```

手動で当日分を作る場合は、Dashboard のボタンまたは以下を実行します。

```bash
curl -X POST http://localhost:8000/api/bot/run-screening
curl -X POST http://localhost:8000/api/bot/run-paper-trade
curl -X POST http://localhost:8000/api/bot/run-analysis
curl -X POST http://localhost:8000/api/bot/run-optimization
```

## Secret 設定

Yahoo系データ取得にはSecretは不要です。J-Quantsを使う場合のみ以下が必要です。

```text
DATA_SOURCE=jquants
JQUANTS_EMAIL=...
JQUANTS_PASSWORD=...
```

`.env` は `.gitignore` 対象です。実際の認証情報はGitHubにcommitしないでください。

## `.env` 例

```text
APP_ENV=local
DATABASE_PATH=./tenk_to_million.db
DATA_SOURCE=yahoo
INITIAL_CASH=10000
JQUANTS_EMAIL=
JQUANTS_PASSWORD=
YAHOO_FINANCE_ENABLED=true
MARKET_SYMBOLS=3778,2160,4565,6920,5253,7014,1514,5586,5595,6526
SCHEDULER_ENABLED=true
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

`JQuantsCollector` は公式APIの認証フローで上場銘柄情報と日足四本値を取得します。`YahooCollector` はYahoo Finance系のチャートデータを利用して日足・5分足相当のデータを取得します。認証情報が未設定、またはYahoo取得が無効な場合は明示的に失敗し、秘密情報をログに出しません。

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
POST /api/bot/run-screening
POST /api/bot/run-paper-trade
POST /api/bot/run-analysis
POST /api/bot/run-optimization
POST /api/bot/set-mode
POST /api/bot/set-data-source
POST /api/bot/set-strategy
```

## 注意事項

- 現物のみ、信用取引・空売り・レバレッジは禁止です。
- 同時保有は 1 銘柄まで、ナンピンは禁止です。
- 初期資金は 10,000 円です。
- 14:45 強制決済を前提に、持ち越しは禁止です。
- 実売買は初期実装では不可です。
- 投資判断は自己責任です。このアプリは利益を保証しません。
