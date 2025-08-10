import os
import pyodbc
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.authorization import AuthorizationManagementClient

credential = DefaultAzureCredential()


SQL_SERVER = "server-433655478.database.windows.net"
SQL_DATABASE = "mydb"
SQL_USERNAME = "dbadmin"
SQL_PASSWORD = "Descon123"

# ======================
# CONNECT TO SQL
# ======================
conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USERNAME};PWD={SQL_PASSWORD}"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
IF NOT EXISTS (
    SELECT * FROM sysobjects WHERE name='RoleAssignments' AND xtype='U'
)
CREATE TABLE RoleAssignments (
    RoleAssignmentId NVARCHAR(200) PRIMARY KEY,
    SubscriptionId NVARCHAR(100),
    PrincipalId NVARCHAR(100),
    RoleDefinitionId NVARCHAR(200),
    Scope NVARCHAR(500),
    UpdatedOn DATETIME
)
""")
conn.commit()

# ======================
# GET SUBSCRIPTIONS
# ======================
sub_client = SubscriptionClient(credential)
subscriptions = sub_client.subscriptions.list()

for sub in subscriptions:
    subscription_id = sub.subscription_id
    print(f"Fetching role assignments for subscription: {subscription_id}")

    auth_client = AuthorizationManagementClient(credential, subscription_id)
    scope = f"/subscriptions/{subscription_id}"

    # ======================
    # FETCH EXISTING IDS (for delta)
    # ======================
    cursor.execute("SELECT RoleAssignmentId FROM RoleAssignments WHERE SubscriptionId = ?", subscription_id)
    existing_ids = set(row[0] for row in cursor.fetchall())

    # ======================
    # FETCH ROLE ASSIGNMENTS FROM AZURE
    # ======================
    new_count = 0
    for assignment in auth_client.role_assignments.list_for_scope(scope):
        assignment_id = assignment.id
        if assignment_id not in existing_ids:
            cursor.execute("""
                INSERT INTO RoleAssignments (RoleAssignmentId, SubscriptionId, PrincipalId, RoleDefinitionId, Scope, UpdatedOn)
                VALUES (?, ?, ?, ?, ?, ?)
            """, assignment_id, subscription_id, assignment.principal_id,
                 assignment.role_definition_id, assignment.scope, datetime.utcnow())
            new_count += 1

    conn.commit()
    print(f"✅ {new_count} new role assignments added for {subscription_id}")

# Close connection
cursor.close()
conn.close()

print("🎯 Backup completed successfully!")
