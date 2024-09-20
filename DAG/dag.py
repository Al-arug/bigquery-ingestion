from airflow import models
from airflow.utils.dates import days_ago
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from google.cloud import bigquery
                                                                        

# Define file-to-table mapping
file_table_mappings = [
    {
        'gcs_bucket': 'raw-wwi-aliaruqi',  # Replace with your GCS bucket
        'gcs_file': 'data-evolution-wwi/csv/application.countries/Application.Countries.csv',  # Replace with the first GCS file
        'bq_table': 'data-evolution-ali.raw_wwi.countries',  # Replace with corresponding BigQuery table
    },
    {
        'gcs_bucket': 'raw-wwi-aliaruqi',
        'gcs_file': 'data-evolution-wwi/csv/warehouse.stockgroups/year=2013/month=99/warehouse.stockgroups_201399.csv',
        'bq_table': 'data-evolution-ali.raw_wwi.stockgroup',
    },
    {
        'gcs_bucket': 'raw-wwi-aliaruqi',
        'gcs_file': 'data-evolution-wwi/csv/warehouse.stockitem/year=2013/month=99/warehouse.stockitem_201399.csv',
        'bq_table': 'data-evolution-ali.raw_wwi.stockitems',
    },
     {
        'gcs_bucket': 'raw-wwi-aliaruqi',
        'gcs_file': 'data-evolution-wwi/csv/warehouse.stockitemstockgroups/year=2013/month=99/warehouse.stockitemstockgroups_201399.csv',
        'bq_table': 'data-evolution-ali.raw_wwi.stockitemstockgroup',
    },

]



def fetch_bq_schema(table_id):
    client = bigquery.Client(project='data-evolution-ali')
    table = client.get_table(f"data-evolution-ali.raw_wwi.{table_id}")
    schema = table.schema
    # Convert schema to the format that Airflow expects (list of dictionaries)
    schema_fields = [{"name": field.name, "type": field.field_type, "mode": field.mode} for field in schema]
    return schema_fields



default_args = {
    "owner": "Dataevo",
    "depends_on_past": False,
    "email": [""],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "start_date": days_ago(1),
}



# Define the DAG
with models.DAG(
    'gcs_to_bq_ingestion_multiple_files_dag',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:

    # Dynamically create tasks for each file-table mapping
    for mapping in file_table_mappings:

        table_id = mapping['bq_table'].split('.')[-1]    
        schema_fields = fetch_bq_schema(table_id)

        load_task = GCSToBigQueryOperator(
            task_id=f'gcs_to_bq_{mapping["bq_table"].replace(".", "_")}',  # Unique task_id for each file-table pair
            bucket =mapping['gcs_bucket'],
            source_objects=[mapping['gcs_file']],
            schema_fields = schema_fields,
            destination_project_dataset_table=mapping['bq_table'],
            source_format='CSV',
            field_delimiter = ',',
            skip_leading_rows=1,  # Assuming there's a header row
            write_disposition='WRITE_TRUNCATE',
            autodetect=False,
        )