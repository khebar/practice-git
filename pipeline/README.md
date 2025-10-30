# Daily ETL Pipeline

The module `daily_pipeline.py` schedules the LinkedIn ETL orchestration with a cron-like
expression using APScheduler. To run the scheduler as a long-running process, execute:

```bash
python -m pipeline.daily_pipeline
```

To deploy the workflow using system cron instead of APScheduler, register the following
entry (adjusting the path to the Python interpreter as needed):

```cron
0 2 * * * /usr/bin/env python -m pipeline.daily_pipeline --run-once
```
