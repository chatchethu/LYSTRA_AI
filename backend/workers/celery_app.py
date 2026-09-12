from celery import Celery
from backend.config import get_settings

settings = get_settings()

def create_celery_app() -> Celery:
    app = Celery(
        'personal_ai',
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=['backend.workers.tasks'],
    )
    app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,  # Prevent task hoarding
        broker_connection_retry_on_startup=True,
        task_default_queue='interactive',
        task_queues={
            'interactive': {'exchange': 'interactive', 'routing_key': 'interactive'},
            'agent_tasks': {'exchange': 'agent_tasks', 'routing_key': 'agent_tasks'},
            'document_processing': {'exchange': 'document_processing', 'routing_key': 'document_processing'},
            'memory_processing': {'exchange': 'memory_processing', 'routing_key': 'memory_processing'},
            'scheduled': {'exchange': 'scheduled', 'routing_key': 'scheduled'},
        },
        task_routes={
            'backend.workers.tasks.process_chat_task': {'queue': 'interactive', 'priority': 9},
            'backend.workers.tasks.execute_agent_task': {'queue': 'agent_tasks', 'priority': 5},
            'backend.workers.tasks.process_file_upload': {'queue': 'document_processing', 'priority': 3},
            'backend.workers.tasks.process_memory': {'queue': 'memory_processing', 'priority': 2},
            'backend.workers.tasks.process_scheduled_tasks': {'queue': 'scheduled', 'priority': 1},
            'backend.workers.tasks.recover_lost_tasks': {'queue': 'scheduled'},
        },
        beat_schedule={
            'process-scheduled-tasks': {
                'task': 'backend.workers.tasks.process_scheduled_tasks',
                'schedule': 60.0,  # every minute
            },
        }
    )
    return app

celery_app = create_celery_app()
