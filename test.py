import psycopg2

connection = None  # Initialize connection to None
try:
    connection = psycopg2.connect(
        user="testuser",
        password="testpass",
        host="localhost",
        port=5432,
        database="testdb"
    )
    cursor = connection.cursor()
    cursor.execute("SELECT version();")
    record = cursor.fetchone()
    print("You are connected to - ", record, "\n")
except Exception as error:
    print("Error while connecting to PostgreSQL", error)
finally:
    if connection is not None:
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")