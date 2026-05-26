import psycopg2
import sshtunnel
import psycopg2.extras
import pandas as pd
sshtunnel.SSH_TIMEOUT = 10.0
sshtunnel.TUNNEL_TIMEOUT = 10.0

class DatabaseManager:
    def __init__(self, ssh_username, ssh_password, postgres_hostname, postgres_host_port, db_user, db_password, db_name):
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.postgres_hostname = postgres_hostname
        self.postgres_host_port = postgres_host_port
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name

    def get_column_value(self,column_name,table_name,primary_key_col,primary_key_value):
        try:
            # Establish SSH tunnel
            with sshtunnel.SSHTunnelForwarder(
                ('ssh.pythonanywhere.com'),
                ssh_username=self.ssh_username,
                ssh_password=self.ssh_password,
                remote_bind_address=(self.postgres_hostname, self.postgres_host_port)
                ) as tunnel:
                # Connect to the database through the tunnel
                connection = psycopg2.connect(
                    user=self.db_user, password=self.db_password,
                    host='127.0.0.1', port=tunnel.local_bind_port,
                    database=self.db_name,
                )
                # Use DictCursor to get results as dictionaries. So this creates a PostgreSQL cursor that returns query results as dictionary-like objects instead of the default tuples
                cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
                # Build and execute the query
                query = f"SELECT {column_name} FROM {table_name} WHERE {primary_key_col} = %s"
                cursor.execute(query, (primary_key_value,))
                result = cursor.fetchone()
                
                if result is None:
                    print(f"No records found for {primary_key_col} = {primary_key_value} in {table_name}")
                    return "Not available"
                
                column_value = result[column_name]
                print(column_value)
                cursor.close()
                connection.close()
                return column_value
                # cursor.close()
                # connection.close()
                # return dict(record)
        except Exception as e:
            print(f"An error occurred: {e}")

    def get_record(self,table_name,primary_key_col,primary_key_value):
        try:
            # Establish SSH tunnel
            with sshtunnel.SSHTunnelForwarder(
                ('ssh.pythonanywhere.com'),
                ssh_username=self.ssh_username,
                ssh_password=self.ssh_password,
                remote_bind_address=(self.postgres_hostname, self.postgres_host_port)
                ) as tunnel:
                # Connect to the database through the tunnel
                connection = psycopg2.connect(
                    user=self.db_user, password=self.db_password,
                    host='127.0.0.1', port=tunnel.local_bind_port,
                    database=self.db_name,
                )
                # Use DictCursor to get results as dictionaries. So this creates a PostgreSQL cursor that returns query results as dictionary-like objects instead of the default tuples
                cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
                query = f"SELECT * FROM {table_name} WHERE {primary_key_col} = %s LIMIT 1"
                print(query)
                cursor.execute(query, (primary_key_value,)) # note: , for tuple validation
                print('database query executed')
                record = cursor.fetchone()
                if record is None:
                    print(f"No records found for {primary_key_col} = {primary_key_value} in {table_name}")
                    return None    
                # print(dict(record))
                cursor.close()
                connection.close()
                return dict(record)
        except Exception as e:
            print(f"An error occurred: {e}")

    def update_multiple_fields(self,table_name, record, primary_key_col):
        """
        Updates a record in a PostgreSQL table using the values in `record` dict.
        
        Args:
            table_name (str): Name of the table.
            record (dict): Dictionary of column-value pairs to update (must include primary_key_col).
            primary_key_col (str): Name of the primary key column.
        
        Returns:
            bool: True if a record was updated, False otherwise.
        """
        try:
            with sshtunnel.SSHTunnelForwarder(
                ('ssh.pythonanywhere.com'),
                ssh_username=self.ssh_username,
                ssh_password=self.ssh_password,
                remote_bind_address=(self.postgres_hostname, self.postgres_host_port)
                ) as tunnel:
                # Connect to the database through the tunnel
                connection = psycopg2.connect(
                    user=self.db_user, password=self.db_password,
                    host='127.0.0.1', port=tunnel.local_bind_port,
                    database=self.db_name,
                )
                # Use DictCursor to get results as dictionaries. So this creates a PostgreSQL cursor that returns query results as dictionary-like objects instead of the default tuples
                cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
                # connection = psycopg2.connect(**db_params)
                cursor = connection.cursor()
                
                # Extract primary key value and remove it from the update fields
                primary_key_value = record[primary_key_col]
                update_fields = {k: v for k, v in record.items() if k != primary_key_col}
                
                if not update_fields:
                    print("No fields to update.")
                    return False
                
                # Build SET clause dynamically
                set_clause = ', '.join([f"{col} = %s" for col in update_fields.keys()])
                values = list(update_fields.values())
                values.append(primary_key_value)  # Add PK value for WHERE clause
                
                query = f"UPDATE {table_name} SET {set_clause} WHERE {primary_key_col} = %s"
                cursor.execute(query, values)
                connection.commit()
                
                if cursor.rowcount == 0:
                    print(f"No record found for {primary_key_col} = {primary_key_value}")
                    return False
                else:
                    print(f"Record with {primary_key_col} = {primary_key_value} updated successfully.")
                    return True
            
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
    
    def update_single_field(self,table_name, column_name, column_value, primary_key_col, primary_key_value):
        """
        Updates a single column value for a record in a PostgreSQL table identified by its primary key.
        
        Args:
            table_name (str): Name of the table.
            column_name (str): Column to update.
            column_value (Any): New value for the column.
            primary_key_col (str): Name of the primary key column.
            primary_key_value (Any): Value of the primary key.
            db_params (dict): Database connection parameters.
        """
        try:
            with sshtunnel.SSHTunnelForwarder(
                ('ssh.pythonanywhere.com'),
                ssh_username=self.ssh_username,
                ssh_password=self.ssh_password,
                remote_bind_address=(self.postgres_hostname, self.postgres_host_port)
                ) as tunnel:
                # Connect to the database through the tunnel
                connection = psycopg2.connect(
                    user=self.db_user, password=self.db_password,
                    host='127.0.0.1', port=tunnel.local_bind_port,
                    database=self.db_name,
                )
                # connection = psycopg2.connect(**db_params)
                cursor = connection.cursor()
                query = f"UPDATE {table_name} SET {column_name} = %s WHERE {primary_key_col} = %s"
                cursor.execute(query, (column_value, primary_key_value))
                connection.commit()
                
                if cursor.rowcount == 0:
                    print(f"No record found for {primary_key_col} '{primary_key_value}'")
                else:
                    print(f"Updated {column_name} for {primary_key_col} '{primary_key_value}' to {column_value}")
            
        except Exception as e:
            print(f"An error occurred: {e}")
    
    def unique_key_check(self,column_name, unique_value, table_name):
        """
        Checks if a unique value exists in a specific column of a PostgreSQL table.
        
        Args:
            column_name (str): The column to check.
            unique_value (Any): The value to check for uniqueness.
            table_name (str): The table to check in.
            db_params (dict): Database connection parameters.
            
        Returns:
            bool: True if the value exists, False otherwise.
        """
        try:
            with sshtunnel.SSHTunnelForwarder(
                ('ssh.pythonanywhere.com'),
                ssh_username=self.ssh_username,
                ssh_password=self.ssh_password,
                remote_bind_address=(self.postgres_hostname, self.postgres_host_port)
                ) as tunnel:
                # Connect to the database through the tunnel
                connection = psycopg2.connect(
                    user=self.db_user, password=self.db_password,
                    host='127.0.0.1', port=tunnel.local_bind_port,
                    database=self.db_name,
                )
                # connection = psycopg2.connect(**db_params)
                cursor = connection.cursor()
                query = f"SELECT 1 FROM {table_name} WHERE {column_name} = %s LIMIT 1"
                cursor.execute(query, (unique_value,))
                exists = cursor.fetchone() is not None
                print(f"Unique key check: {exists}")
                return exists
            
        except Exception as e:
            print(f"Error occurred while performing unique value check in PostgreSQL: {e}")

    def insert_data_collection(self,data):
        try:
            # Establish SSH tunnel
            with sshtunnel.SSHTunnelForwarder(
                ('ssh.pythonanywhere.com'),
                ssh_username=self.ssh_username,
                ssh_password=self.ssh_password,
                remote_bind_address=(self.postgres_hostname, self.postgres_host_port)
                ) as tunnel:
                # Connect to the database through the tunnel
                connection = psycopg2.connect(
                    user=self.db_user, password=self.db_password,
                    host='127.0.0.1', port=tunnel.local_bind_port,
                    database=self.db_name,
                )

                # Perform database operation
                cursor = connection.cursor()
                print("Data:",data)
                values = (
                    data.get('apollo_id'),
                    data.get('first_name'),
                    data.get('last_name'),
                    data.get('name'),
                    data.get('email'),
                    data.get('linkedin_url'),
                    data.get('associated_client_id'),
                    data.get('title'),
                    data.get('seniority'),
                    data.get('headline'),
                    data.get('is_likely_to_engage'),
                    data.get('photo_url'),
                    data.get('email_status'),
                    data.get('twitter_url'),
                    data.get('employment_history'),
                    data.get('employment_summary'),
                    data.get('organization_name'),
                    data.get('organization_website'),
                    data.get('organization_linkedin'),
                    data.get('organization_primary_phone'),
                    data.get('organization_logo'),
                    data.get('organization_primary_domain'),
                    data.get('organization_industry'),
                    data.get('organization_estimated_num_employees'),
                    data.get('organization_phone'),
                    data.get('organization_city'),
                    data.get('organization_state'),
                    data.get('organization_country'),
                    data.get('organization_short_description'),
                    data.get('organization_technology_names'),
                    data.get('filter_criteria'),
                    data.get('target_region'),
                    data.get('created_time')
                )
            
                cursor.execute('''
                INSERT INTO src_guideline (
                    apollo_id, first_name, last_name, name, email, linkedin_url, associated_client_id,
                    title, seniority, headline, is_likely_to_engage, photo_url, email_status,
                    twitter_url, employment_history, employment_summary,
                    organization_name, organization_website, organization_linkedin,
                    organization_primary_phone, organization_logo, organization_primary_domain,
                    organization_industry, organization_estimated_num_employees, organization_phone,
                    organization_city, organization_state, organization_country, organization_short_description,
                    organization_technology_names, filter_criteria, target_region, created_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', values)

                connection.commit()
                print('Entry added successfully to the collection table')
                
                # Close resources
                cursor.close()
                connection.close()
        except Exception as e:
            print(f"An error occurred: {e}")
        return 'Done'

    def insert_data(self, table_name, data):
        try:
            # Establish SSH tunnel
            with sshtunnel.SSHTunnelForwarder(
                ('ssh.pythonanywhere.com'),
                ssh_username=self.ssh_username,
                ssh_password=self.ssh_password,
                remote_bind_address=(self.postgres_hostname, self.postgres_host_port)
            ) as tunnel:
                # Connect to the database through the tunnel
                connection = psycopg2.connect(
                    user=self.db_user, password=self.db_password,
                    host='127.0.0.1', port=tunnel.local_bind_port,
                    database=self.db_name,
                )

                # Perform database operation
                cursor = connection.cursor()

                # Dynamically build SQL from data keys
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['%s'] * len(data))
                values = tuple(data.values())

                insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(insert_query, values)

                connection.commit()
                print(f"Entry added successfully to table '{table_name}'")

                # Close resources
                cursor.close()
                connection.close()
        except Exception as e:
            print(f"An error occurred: {e}")
        return 'Done'
    
    def get_records_with_filter(self, table_name, cols_list, col_values, limit=1):
        try:
            # Establish SSH tunnel
            with sshtunnel.SSHTunnelForwarder(
                ('ssh.pythonanywhere.com'),
                ssh_username=self.ssh_username,
                ssh_password=self.ssh_password,
                remote_bind_address=(self.postgres_hostname, self.postgres_host_port)
            ) as tunnel:
                # Connect to the database through the tunnel
                connection = psycopg2.connect(
                    user=self.db_user,
                    password=self.db_password,
                    host='127.0.0.1',
                    port=tunnel.local_bind_port,
                    database=self.db_name,
                )
                cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

                # Build WHERE clause dynamically
                where_clause = " AND ".join([f"{col} = %s" for col in cols_list])
                query = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT {limit};"
                print("Executing query:", query)

                # Execute query with values
                cursor.execute(query, col_values)

                record = cursor.fetchone()
                cursor.close()
                connection.close()

                if record is None:
                    print("No matching record found.")
                    return None

                return dict(record)

        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_records_from_query(self,sql_query):
        try:
            with sshtunnel.SSHTunnelForwarder(
                ('ssh.pythonanywhere.com'),
                ssh_username=self.ssh_username,
                ssh_password=self.ssh_password,
                remote_bind_address=(self.postgres_hostname, self.postgres_host_port)
            ) as tunnel:

                with psycopg2.connect(
                    user=self.db_user,
                    password=self.db_password,
                    host='127.0.0.1',
                    port=tunnel.local_bind_port,
                    database=self.db_name,
                ) as connection:

                    with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                        print("Executing query:", sql_query)
                        cursor.execute(sql_query)
                        records = cursor.fetchall()
                        print(records)
                        if records is None:
                            print("No matching record found.")
                            return None
                        return records

        except Exception as e:
            print("Database operation failed:", e)
            return None


    def get_records_from_query_v2(self, sql_query):
        try:
            with sshtunnel.SSHTunnelForwarder(
                ('ssh.pythonanywhere.com'),
                ssh_username=self.ssh_username,
                ssh_password=self.ssh_password,
                remote_bind_address=(self.postgres_hostname, self.postgres_host_port)
            ) as tunnel:

                with psycopg2.connect(
                    user=self.db_user,
                    password=self.db_password,
                    host='127.0.0.1',
                    port=tunnel.local_bind_port,
                    database=self.db_name,
                ) as connection:

                    with connection.cursor() as cursor:
                        print("Executing query:", sql_query)
                        cursor.execute(sql_query)
                        
                        if cursor.description:  # Means query returned rows (e.g. SELECT)
                            column_names = [desc[0] for desc in cursor.description]
                            rows = cursor.fetchall()
                            result = [dict(zip(column_names, row)) for row in rows]
                            return result
                        else:
                            connection.commit()  # Commit for UPDATE/DELETE/INSERT
                            return {"status": "success", "rows_affected": cursor.rowcount}

        except Exception as e:
            print("Error during DB query:", str(e))
            return []
        
    def execute_sql_query(self, sql_query):
        try:
            with sshtunnel.SSHTunnelForwarder(
                ('ssh.pythonanywhere.com'),
                ssh_username=self.ssh_username,
                ssh_password=self.ssh_password,
                remote_bind_address=(self.postgres_hostname, self.postgres_host_port)
            ) as tunnel:

                with psycopg2.connect(
                    user=self.db_user,
                    password=self.db_password,
                    host='127.0.0.1',
                    port=tunnel.local_bind_port,
                    database=self.db_name,
                ) as connection:

                    with connection.cursor() as cursor:
                        print("Executing query:", sql_query)
                        cursor.execute(sql_query)
                        
                        if cursor.description:  # Means query returned rows (e.g. SELECT)
                            column_names = [desc[0] for desc in cursor.description]
                            rows = cursor.fetchall()
                            result = [dict(zip(column_names, row)) for row in rows]
                            return result
                        else:
                            connection.commit()  # Commit for UPDATE/DELETE/INSERT
                            return {"status": "success", "rows_affected": cursor.rowcount}

        except Exception as e:
            print("Error during DB query:", str(e))
            return []

db_manager = DatabaseManager(
    ssh_username='magmostafa',
    ssh_password='Drowssap_2024',
    postgres_hostname="magmostafa-4523.postgres.pythonanywhere-services.com",
    postgres_host_port=14523, 
    db_user='super',
    db_password='drowsapp_2025',
    db_name='taippa'
)

# db_manager.unique_key_check("apollo_id","66ff0b8904b8ba0001e3387c","src_guideline_copy_copy")
# print("Done")

# db_manager.insert_data_collection({})

# if __name__ == "__main__":
#     db_manager = DatabaseManager(
#     ssh_username='magmostafa',
#     ssh_password='Drowssap_2024',
#     postgres_hostname="magmostafa-4523.postgres.pythonanywhere-services.com",
#     postgres_host_port=14523, 
#     db_user='super',
#     db_password='drowsapp_2025',
#     db_name='taippa'
#     )
#     db_manager.insert_data()

# def test():
#     with sshtunnel.SSHTunnelForwarder(
#             ('ssh.pythonanywhere.com'),
#             ssh_username='magmostafa',
#             ssh_password='Drowssap_2024',
#             remote_bind_address=(postgres_hostname, postgres_host_port)
#     ) as tunnel:
#         connection = psycopg2.connect(
#             user='super', password='drowsapp_2025',
#             host='127.0.0.1', port=tunnel.local_bind_port,
#             database='taippa',
#         )
#         # Do stuff inside the context manager block
#         cursor = connection.cursor()
#         cursor.execute("INSERT INTO dummy VALUES ('test33345');")
#         connection.commit()
#         print('entry added successfully')
#         cursor.close()
#         connection.close()
#     return 'Done'