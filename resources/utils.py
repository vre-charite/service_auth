import psycopg2
import os
from config import ConfigClass

def sql_query(query, sql_params={}, fetch=False):
    if os.environ.get("env") != "test":
        connection_info = {
            "database": ConfigClass.RDS_DBNAME,
            "user": ConfigClass.RDS_USER,
            "password": ConfigClass.RDS_PWD,
            "host": ConfigClass.RDS_HOST,
            "port": ConfigClass.RDS_PORT,
        }
        result = None 
        with psycopg2.connect(**connection_info) as ops_db:
            with ops_db.cursor() as cursor:
                cursor.execute(query, sql_params)
                ops_db.commit()
                if fetch:
                    result = cursor.fetchone()
    else:
        ops_db = psycopg2.connect(
            database=ConfigClass.RDS_DBNAME,
            user=ConfigClass.RDS_USER,
            password=ConfigClass.RDS_PWD,
            host=ConfigClass.RDS_HOST,
            port=ConfigClass.RDS_PORT,
        )
        cursor = ops_db.cursor()
        cursor.execute(query, sql_params)
        result = cursor.fetchone();
    return result


def mask_email(email):
    sections = email.split("@")
    first = "".join(["*" for i in sections[0][0:-2]])
    second = "".join([i if i == "." else "*" for i in sections[1]])
    return sections[0][0] + first + sections[0][-1] + "@" + second
