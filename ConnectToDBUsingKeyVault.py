from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
import pyodbc
import os

# Service principal creds from environment variables
tenant_id = os.getenv("tenantid")
client_id = os.getenv("appid")
client_secret = os.getenv("appsecret")

# Authenticate to Azure
credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=client_secret
)

# Connect to Key Vault
kv_url = "https://myvault-365283504.vault.azure.net/"
client = SecretClient(vault_url=kv_url, credential=credential)

# Get secret from Key Vault
sql_password = client.get_secret("dbadmin").value

# Connect to Azure SQL
conn_str = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=tcp:server-433655478.database.windows.net,1433;"
    "Database=mydb;"
    f"UID=dbadmin;PWD={sql_password};"
    "Encrypt=yes;TrustServerCertificate=no;"
)

conn = pyodbc.connect(conn_str)
print("✅ Connected to Azure SQL")
