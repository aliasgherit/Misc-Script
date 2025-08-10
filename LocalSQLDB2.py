import sqlite3
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.authorization import AuthorizationManagementClient
import requests
import time

start = time.time()

# ======================
# DB SETUP
# ======================
DB_FILE = "sqldb2.db"
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS RoleAssignments (
    RoleAssignmentId TEXT PRIMARY KEY,
    SubscriptionId TEXT,
    PrincipalId TEXT,
    DisplayName TEXT,
    SignInName TEXT,
    RoleDefinitionName TEXT,
    RoleDefinitionId TEXT,
    Scope TEXT,
    ObjectId TEXT,
    ObjectType TEXT,
    UpdatedOn TEXT
)
""")
conn.commit()

# ======================
# AZURE CREDENTIALS
# ======================
credential = DefaultAzureCredential()
sub_client = SubscriptionClient(credential)

# ======================
# Function: Fetch principal details from Microsoft Graph
# ======================
def get_principal_details_msgraph(principal_id):
    try:
        token = credential.get_token("https://graph.microsoft.com/.default")
        headers = {"Authorization": f"Bearer {token.token}"}

        endpoints = [
            ("User", f"https://graph.microsoft.com/v1.0/users/{principal_id}"),
            ("ServicePrincipal", f"https://graph.microsoft.com/v1.0/servicePrincipals/{principal_id}"),
            ("Group", f"https://graph.microsoft.com/v1.0/groups/{principal_id}")
        ]

        for obj_type, url in endpoints:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                data = r.json()
                display_name = data.get("displayName")
                sign_in_name = data.get("userPrincipalName") or data.get("appId")
                return (display_name, sign_in_name, obj_type)

    except Exception as e:
        print(f"⚠️ Failed to fetch principal details for {principal_id}: {e}")

    return (None, None, "Unknown")

# ======================
# Function: Get Role Definition Name
# ======================
def get_role_definition_name(auth_client, scope, role_definition_id):
    try:
        role_def = auth_client.role_definitions.get(scope, role_definition_id.split("/")[-1])
        return role_def.role_name  # using the attribute from new SDK
    except Exception as e:
        print(f"⚠️ Failed to fetch role definition name for {role_definition_id}: {e}")
        return None

# ======================
# MAIN LOOP
# ======================
for sub in sub_client.subscriptions.list():
    subscription_id = sub.subscription_id
    print(f"Fetching role assignments for subscription: {subscription_id}")

    auth_client = AuthorizationManagementClient(credential, subscription_id)
    scope = f"/subscriptions/{subscription_id}"

    # Fetch existing IDs
    cursor.execute("SELECT RoleAssignmentId FROM RoleAssignments WHERE SubscriptionId = ?", (subscription_id,))
    existing_ids = set(row[0] for row in cursor.fetchall())

    new_count = 0
    for assignment in auth_client.role_assignments.list_for_scope(scope):
        assignment_id = assignment.id
        if assignment_id not in existing_ids:
            display_name, sign_in_name, object_type = get_principal_details_msgraph(assignment.principal_id)
            role_def_name = get_role_definition_name(auth_client, scope, assignment.role_definition_id)

            cursor.execute("""
                INSERT OR REPLACE INTO RoleAssignments 
                (RoleAssignmentId, SubscriptionId, PrincipalId, DisplayName, SignInName, RoleDefinitionName, RoleDefinitionId, Scope, ObjectId, ObjectType, UpdatedOn)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                assignment_id,
                subscription_id,
                assignment.principal_id,
                display_name,
                sign_in_name,
                role_def_name,
                assignment.role_definition_id,
                assignment.scope,
                assignment.principal_id,  # storing principal ID again as ObjectId
                object_type,
                datetime.utcnow().isoformat()
            ))
            new_count += 1

    conn.commit()
    print(f"✅ {new_count} new role assignments added for {subscription_id}")

# ======================
# EXPORT TO CSV
# ======================
import csv
csv_file = "role_assignments_export.csv"

cursor.execute("SELECT * FROM RoleAssignments ORDER BY UpdatedOn DESC")
rows = cursor.fetchall()
col_names = [description[0] for description in cursor.description]

with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(col_names)
    writer.writerows(rows)

print(f"📄 Data exported to {csv_file}")

# ======================
# CLOSE
# ======================
cursor.close()
conn.close()
end_time = time.time()
print(f"⏱️ Total execution time: {end_time - start:.2f} seconds")
print("🎯 Backup completed successfully!")
