import sqlite3
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.authorization import AuthorizationManagementClient
import time

start = time.time()

# Azure authentication
credential = DefaultAzureCredential()

# ======================
# CONNECT TO SQLITE
# ======================
# This will create the DB file if it doesn’t exist
conn = sqlite3.connect("mydb.sqlite3")
cursor = conn.cursor()

# Create table if not exists (SQLite syntax)
cursor.execute("""
CREATE TABLE IF NOT EXISTS RoleAssignments (
    RoleAssignmentId TEXT,
    SubscriptionId TEXT,
    PrincipalId TEXT,
    RoleDefinitionId TEXT,
    Scope TEXT,
    UpdatedOn TEXT
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
    cursor.execute("SELECT RoleAssignmentId FROM RoleAssignments WHERE SubscriptionId = ?", (subscription_id,))
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
            """, (
                assignment_id,
                subscription_id,
                assignment.principal_id,
                assignment.role_definition_id,
                assignment.scope,
                datetime.utcnow().isoformat()  # Store as ISO string
            ))
            new_count += 1

    conn.commit()
    print(f"✅ {new_count} new role assignments added for {subscription_id}")

# Close connection
cursor.close()
conn.close()

end_time = time.time()
total_time = end_time - start
print(f"⏱️ Total execution time: {total_time:.2f} seconds")
print("🎯 Backup completed successfully!")
