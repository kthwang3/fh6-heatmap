# FH6 Heatmap

![Downloads](https://img.shields.io/github/downloads/kthwang3/fh6-heatmap/total)
![Release](https://img.shields.io/github/v/release/kthwang3/fh6-heatmap)

Community heatmap + real-time live map for Forza Horizon 6. See where the community drives most — and track your own position on a second monitor while you race.

**Live site:** https://d229cekzpyx88w.cloudfront.net

---

## Download & Setup

### Windows

1. Download `FH6-Livemap.exe` from the [Releases](https://github.com/kthwang3/fh6-heatmap/releases) page
2. Run it — a browser tab opens automatically with the live map
3. In FH6: **Settings → HUD and Gameplay → Data Out**
   - Data Out: **On**
   - Data Out IP Address: `127.0.0.1`
   - Data Out Port: `5301`
4. Start driving — your dot moves on the live map and your position is added to the community heatmap

> **Windows Defender warning:** Windows may flag the .exe as unrecognized. Click **More info → Run anyway**. This is a known false positive for PyInstaller-bundled apps.

### Linux

1. Download `FH6-Livemap-linux` from the [Releases](https://github.com/kthwang3/fh6-heatmap/releases) page
2. Make it executable and run it:
   ```bash
   chmod +x FH6-Livemap-linux
   ./FH6-Livemap-linux
   ```
3. In FH6: **Settings → HUD and Gameplay → Data Out**
   - Data Out: **On**
   - Data Out IP Address: `127.0.0.1`
   - Data Out Port: `5301`
4. Start driving — a browser tab opens automatically with the live map, or open the printed URL manually if it doesn't

### If using Tablet as Second Monitor (on same WiFi)

1. Run `FH6-Livemap.exe` (or `FH6-Livemap-linux`) on your PC as normal
2. **Windows:** Open Windows Defender Firewall → Inbound Rules → find `fh6-livemap.exe` → make sure both Private and Public are checked
   **Linux:** Run `sudo ufw allow 5500 && sudo ufw allow 8765`
3. Find your PC's local IP:
   - Windows: run `ipconfig` in Command Prompt, look for **IPv4 Address** (e.g. `10.0.0.x`)
   - Linux: run `hostname -I`
4. On your tablet, open `http://10.0.0.x:5500/livemap.html` in a browser
5. Bookmark it for easy access

> **Note:** Your tablet and PC must be on the same network. Your PC's IP can change — if the tablet stops connecting, run `ipconfig` again to get the new IP.

---

## Features

- **Community Heatmap** — aggregate heatmap of all recorded positions, filterable by all time / week / day. Updated every hour.
- **Live Map** — real-time dot on the Japan map served locally over localhost. No data leaves your machine for this feature.

---

## Screenshots

### Website
![Website](images/fh6-heatmap-website-182000.png)

### City Heatmap
![City Heatmap](images/fh6-heatmap-city-182000.png)

### Leaderboard
![Leaderboard](images/fh6-heatmap-leaderboard-182000.png)

### Live Map
![Live Map](images/live-map-screenshot.png)

---

## Architecture

### Write Path — Telemetry Ingestion

```mermaid
flowchart TD
    FH6[FH6 Game]
    Parser["FH6-Livemap.exe\n(parser.py)"]
    Browser["Browser\nlocalhost:5500"]
    APIGW["API Gateway\nPOST /position"]
    WriteLambda["Lambda\nmain.py"]
    DDB[("DynamoDB\nfh6-heatmap-table")]

    FH6 -->|"UDP ~60Hz\n324 bytes"| Parser
    Parser -->|"WebSocket\n(localhost only)"| Browser
    Parser -->|"POST every 10s\nor 50m moved"| APIGW
    APIGW --> WriteLambda
    WriteLambda -->|"sessionId + timestamp\n+ position + car"| DDB
```

- **600x API call reduction** — 60Hz UDP sampled to 1 POST per 10 seconds before any network call
- **Serverless ingestion** — 1,000 concurrent users, p95 520ms, 0% failure rate across 23,652 requests

### Read Path — Heatmap Delivery

```mermaid
flowchart TD
    EB["EventBridge\nrate(1 hour)"]
    AggLambda["Lambda\npreaggregate.py"]
    DDB[("DynamoDB\nfh6-heatmap-table")]
    StreamLambda["Lambda\nstream_processor.py"]
    Counters[("DynamoDB\nfh6-heatmap-grid-table\n(counters)")]
    S3[("S3\nfh6-heatmap-s3-kthwang3")]
    CF["CloudFront CDN"]
    Site["Heatmap Website\nd229cekzpyx88w.cloudfront.net"]

    DDB -->|"DynamoDB Streams\n(INSERT events)"| StreamLambda
    StreamLambda -->|"increment col_row counters"| Counters
    EB -->|"scheduled trigger"| AggLambda
    Counters -->|"scan explored cells\n(all-time)"| AggLambda
    DDB -->|"Date GSI query\n(day / week)"| AggLambda
    AggLambda -->|"all-time-grids.json\nweek-grids.json\nday-grids.json"| S3
    S3 --> CF
    CF -->|"cached static JSON\n<200ms warm hit"| Site
```

- **<200ms heatmap load time** — CloudFront-cached static JSON vs ~19s live DynamoDB scan before pre-aggregation
- Pre-aggregation reads the counters table (one item per explored grid cell, max 40,000) + Date GSI queries instead of scanning the full positions table

---

## Infrastructure

All AWS infrastructure is provisioned as code with Terraform. No resources were created manually.

```mermaid
graph TD
    Internet

    subgraph AWS
        subgraph Networking
            APIGW[API Gateway]
            CF[CloudFront]
        end
        subgraph Compute
            Lambda1[Lambda\nmain.py]
            Lambda2[Lambda\npreaggregate.py]
            Lambda3[Lambda\nstream_processor.py]
        end
        subgraph Storage
            DDB[(DynamoDB\npositions table)]
            Counters[(DynamoDB\ncounters table)]
            S3[(S3)]
        end
        subgraph Scheduling
            EB[EventBridge]
        end
        IAM[IAM Roles]
    end

    subgraph CICD[CI/CD]
        GHA[GitHub Actions]
        TF[Terraform]
    end

    Internet -->|HTTPS POST /position| APIGW
    Internet -->|HTTPS| CF
    APIGW --> Lambda1
    Lambda1 --> DDB
    DDB -->|DynamoDB Streams| Lambda3
    Lambda3 --> Counters
    CF --> S3
    EB --> Lambda2
    Counters -->|scan explored cells| Lambda2
    DDB -->|Date GSI query| Lambda2
    Lambda2 --> S3
    GHA -->|s3 sync frontend/| S3
    GHA -->|windows runner build| Releases[GitHub Releases]
    TF -->|provisions| AWS
    IAM -.->|execution role| Lambda1
    IAM -.->|execution role| Lambda2
    IAM -.->|execution role| Lambda3
```

**API Gateway** — public HTTPS endpoint that receives position POSTs from every running `.exe` instance and forwards them to Lambda. Handles request routing, throttling, and TLS termination.

**Lambda (main.py)** — write handler. Parses the incoming position payload and writes one DynamoDB item per sampled point. Stateless, scales automatically with concurrent users.

**Lambda (preaggregate.py)** — aggregation worker. Runs every hour, reads the counters table for all-time data and queries the Date GSI for day/week data, computes three heatmap grids and three car leaderboards, then writes six JSON files to S3.

**Lambda (stream_processor.py)** — stream consumer. Fires on every position INSERT via DynamoDB Streams, computes the grid cell, and atomically increments counters in the counters table. Keeps all-time aggregates live without any scheduled scan.

**DynamoDB (positions table)** — stores every recorded position as an item with sessionId (partition key), timestamp (sort key), X/Z coordinates, car metadata, and date. A Date GSI enables efficient day/week queries without scanning the full table. Pay-per-request billing — no capacity planning needed.

**DynamoDB (counters table)** — stores one item per explored grid cell (capped at 40,000 cells max — the 200×200 grid) with a total hit count and a nested map of car counts per cell. Maintained live by stream_processor. preaggregate reads this instead of scanning 473k+ positions for all-time data.

**S3** — stores the static frontend (`index.html`, map image) and the pre-aggregated JSON files written by the aggregation Lambda. Also stores Terraform state.

**CloudFront** — CDN sitting in front of S3. Caches the pre-aggregated JSON files at edge locations so the heatmap loads in <200ms regardless of where the visitor is. Also serves the frontend over HTTPS.

**EventBridge** — scheduled trigger (`rate(15 minutes)`) that invokes the aggregation Lambda automatically. No polling, no cron job on a server.

**IAM** — Lambda execution roles with least-privilege policies. The write Lambda has DynamoDB write access only. The aggregation Lambda has DynamoDB read access and S3 write access.

**Terraform** — provisions every resource above as code. `terraform apply` from the `terraform/` directory recreates the full stack from scratch.

**GitHub Actions** — two workflows: `deploy.yml` syncs the frontend to S3 on every push to `main`; `release.yml` builds `FH6-Livemap.exe` on a Windows runner and `FH6-Livemap-linux` on an Ubuntu runner, then uploads both to GitHub Releases on every version tag.

---

## Tech Stack

| Category | Tools |
|---|---|
| Language | Python, JavaScript (React) |
| Cloud | API Gateway · Lambda · DynamoDB · S3 · CloudFront · EventBridge · IAM |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Distribution | PyInstaller · GitHub Releases |

---

## Prerequisites

For running the script directly instead of the `.exe`:

- Python 3.10+
- `pip install -r requirements.txt`
- FH6 with Data Out configured (same settings as above)

```bash
python parser.py
```

---

## Deployment

**Frontend**
Push to `main` → GitHub Actions syncs `frontend/` to S3 → CloudFront serves it.

**Lambda**
```bash
cd lambda && zip ../lambda.zip *.py
aws lambda update-function-code --function-name <function-name> --zip-file fileb://lambda.zip
```

**Infrastructure**
```bash
cd terraform && terraform apply
```

**New release**
```bash
git tag vX.X.X
git push origin main --tags
```
GitHub Actions builds `FH6-Livemap.exe` on a Windows runner and attaches it to the release automatically.
