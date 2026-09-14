# PowerShell presentation demo

Use these commands from Windows PowerShell in the project folder.

## One-time preparation

Open Docker Desktop and wait until it reports that the engine is running.

If the repository is not on the computer yet:

```powershell
git clone https://github.com/shachar-datalabs/Smart_Emergency_Room.git
Set-Location Smart_Emergency_Room
```

Prepare and validate the environment:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\prepare_presentation.ps1
```

To include the complete test suite:

```powershell
.\scripts\prepare_presentation.ps1 -RunTests
```

The preparation script checks Python, Docker, BigQuery, dependencies, local data, Docker Compose and the BigQuery load plan. It creates missing deterministic local outputs when required.

## Live presentation

Sign in to Google Cloud before the presentation if needed:

```powershell
gcloud auth login
gcloud config set project shachar-bigquery-lab
```

Run the complete proof:

```powershell
Set-Location Smart_Emergency_Room
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\run_presentation_demo.ps1
```

The successful result ends with `status: PASS`. The `after` value must equal the `before` value plus one, and the generated `visit_id` must appear in BigQuery.

To open the actual Looker Studio report automatically, paste its URL:

```powershell
.\scripts\run_presentation_demo.ps1 -LookerStudioUrl "PASTE_LOOKER_STUDIO_URL_HERE"
```

## What to say during the run

1. The script first reads the current number of active patients from BigQuery.
2. It starts local Kafka and Spark services in Docker.
3. The simulator publishes one synthetic ARRIVAL event.
4. Spark updates the operational state.
5. The project rebuilds the Gold output and synchronizes the five small BigQuery tables.
6. The validation reads BigQuery again and verifies that the new visit exists.
7. The script always shuts down the temporary Docker services.

## Manual streaming view with two PowerShell windows

Use this only when you want the audience to watch Kafka and Spark separately.

Window 1:

```powershell
Set-Location Smart_Emergency_Room
docker compose up -d
python scripts/run_streaming_pipeline.py --seconds 120
```

Window 2, after Window 1 starts Spark:

```powershell
Set-Location Smart_Emergency_Room
python -m src.simulator.patient_simulator --patients 12 --seed 42 --rate 20 --kafka
Get-Content data\streaming\current_ed_state.jsonl -Tail 10
Get-Content data\streaming\dq_streaming.json
docker compose down
```

## Safe fallback

Keep these items open before presenting:

- `dashboards/smart_emergency_room_looker_dashboard.png`
- `dashboards/smart_er_dashboard.html`
- The Dashboard / BI slide in the presentation
- The GitHub repository

If the network or Docker fails, explain the same flow with the prepared outputs. Do not troubleshoot installations in front of the audience.
