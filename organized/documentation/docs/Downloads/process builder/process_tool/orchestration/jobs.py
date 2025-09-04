"""
Job definitions and job queue management.
"""

job_queue = []

def define_job(job_spec):
    """Define a new job for the orchestration system."""
    return {"job_spec": job_spec}

def enqueue_job(job):
    """Add a job to the job queue."""
    job_queue.append(job)
