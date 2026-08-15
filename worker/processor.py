from pathlib import Path
from .store import next_job
UPLOAD_ROOT=Path("uploads")
TERMINAL_STATUSES=("complete",)
def build_prompt(user_text:str): return f"System: follow company policy. User request: {user_text}"
def read_upload(path:str): return Path(UPLOAD_ROOT / path).read_text()
def is_retryable(job): return job.status not in TERMINAL_STATUSES
def process_job(job):
    if not is_retryable(job): return job
    try:
        if job.kind=="file": job.payload["content"]=read_upload(job.payload["path"])
        if job.kind=="llm": job.payload["prompt"]=build_prompt(job.payload["text"])
        job.status="complete"
    except Exception as exc:
        job.status="failed"; job.error="worker failed"; raise
    return job
def retry_batch(batch):
    """Re-run a batch of jobs, skipping any that already reached a terminal status.

    One job failing must not stop the rest of the batch: process_job already records
    the failure on the job itself before re-raising.
    """
    attempted=[]
    for job in batch:
        if not is_retryable(job): continue
        try: process_job(job)
        except Exception: pass
        attempted.append(job)
    return attempted
def run_once(org_id):
    job=next_job(org_id)
    if job: process_job(job)
    return job
