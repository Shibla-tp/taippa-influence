from pyairtable import Table
import psycopg2
import re

# Airtable credentials
AIRTABLE_API_KEY = 'patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3'
BASE_ID = 'app5s8zl7DsUaDmtx'
TABLE_NAME = 'client_info'

# PostgreSQL connection details
conn = psycopg2.connect(
    dbname="taippa",
    user="super",
    password="drowsapp_2025",
    host="magmostafa-4523.postgres.pythonanywhere-services.com",
    port="9999"
)
cursor = conn.cursor()

# Step 1: Fetch records from Airtable
table = Table(AIRTABLE_API_KEY, BASE_ID, TABLE_NAME)
records = table.all()

# Step 2: Extract field names
sample_fields = records[0]['fields'] if records else {}
columns = []
for field_name in sample_fields.keys():
    clean_field = re.sub(r'\W+', '_', field_name.lower())  # clean and normalize
    columns.append((clean_field, 'TEXT'))  # Airtable fields default to TEXT

# Step 3: Create SQL Table
table_name_pg = re.sub(r'\W+', '_', TABLE_NAME.lower())
column_defs = ', '.join([f"{name} {dtype}" for name, dtype in columns])

create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name_pg} (id SERIAL PRIMARY KEY, {column_defs});"
cursor.execute(create_table_sql)
conn.commit()

# Step 4: Insert data
for record in records:
    fields = record['fields']
    values = []
    column_names = []
    for field_name in sample_fields.keys():
        clean_field = re.sub(r'\W+', '_', field_name.lower())
        column_names.append(clean_field)
        values.append(fields.get(field_name, ''))

    placeholders = ', '.join(['%s'] * len(values))
    column_str = ', '.join(column_names)

    insert_sql = f"INSERT INTO {table_name_pg} ({column_str}) VALUES ({placeholders});"
    cursor.execute(insert_sql, values)

conn.commit()
cursor.close()
conn.close()

print("Migration complete.")
