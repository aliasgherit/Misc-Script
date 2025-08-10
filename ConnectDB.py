import pyodbc

server = 'server-433655478.database.windows.net'
database = 'mydb'
username = 'dbadmin'
password = 'Descon123'
driver = '{ODBC Driver 18 for SQL Server}'  # Or another version if you installed a different one

connection_string = f'''
    DRIVER={driver};
    SERVER={server};
    DATABASE={database};
    UID={username};
    PWD={password};
    Encrypt=yes;
    TrustServerCertificate=no;
    Connection Timeout=30;
'''

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

# Example query
cursor.execute("""CREATE TABLE RoleAssignments (
    Id NVARCHAR(100) PRIMARY KEY,
    SubscriptionId NVARCHAR(100),
    RoleName NVARCHAR(200),
    PrincipalName NVARCHAR(200),
    Scope NVARCHAR(500),
    LastModified DATETIME
);
""")
conn.commit()
# rows = cursor.fetchall()

# for row in rows:
#    print(row)



