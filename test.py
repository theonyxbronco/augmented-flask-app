import psycopg2

customer_id = "gayassa123"
name = "jasongay"
phone = "123109434"
email = "memeo@wolf.com"

def save_customer_to_db(customer_id, name, phone, email):
    connection_string = "dbname='Augmented_Subscriptions' user='postgres' password='J3e22hJ3e22h' host='localhost'"
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                sql = "INSERT INTO subscribers (customer_id, name, phone, email) VALUES (%s, %s, %s, %s)"
                cur.execute(sql, (customer_id, name, phone, email))
                conn.commit()  # Commit the transaction
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    return True

save_customer_to_db(customer_id, name, phone, email)
