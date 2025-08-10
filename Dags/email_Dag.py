from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.providers.amazon.aws.operators.glue import AwsGlueJobOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'uday',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG('gmail_to_llm_rag',
         default_args=default_args,
         schedule_interval='@hourly',
         catchup=False) as dag:

    fetch_gmail = BashOperator(
        task_id='fetch_gmail_emails',
        bash_command='python3 /path/to/scripts/Gmail_MAIN.py'
    )

    clean_emails = AwsGlueJobOperator(
        task_id='run_glue_job',
        job_name='clean_email_glue_job',
        aws_conn_id='aws_default',
        region_name='us-east-1'
    )

    update_vectorstore = BashOperator(
        task_id='update_vectorstore',
        bash_command='python3 /path/to/scripts/update_faiss.py'
    )

    run_rag = BashOperator(
        task_id='run_rag_pipeline',
        bash_command='python3 /path/to/scripts/run_rag_pipeline.py'
    )

    fetch_gmail >> clean_emails >> update_vectorstore >> run_rag