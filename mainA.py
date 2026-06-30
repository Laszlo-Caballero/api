import pandas as pd
import pyodbc
import os

path = os.path.abspath("dbreport.nii")

conn_str = (
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    rf"DBQ={path};"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

tables = cursor.tables()

# for i, t in enumerate(tables):
#     print(i, t.table_name)
#     if i < 10:
#         pass
#     else:
#         print(t.table_name)
#         df = pd.read_sql_query(f"SELECT * FROM {t.table_name}", conn)
#         df.to_csv(f"{t.table_name}.csv", index=False)

query = """
SELECT assayid, assayName FROM patientrecord
group by assayid, assayName
"""

df = pd.read_sql_query(query, conn)

df.to_csv("patientrecord.csv", index=False)


cursor.close()
conn.close()
