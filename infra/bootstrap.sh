#!/usr/bin/env bash
# One-time setup, run locally after `az login`: creates the resource group and an
# Entra app that GitHub Actions logs in as via OIDC, with Contributor on that
# resource group only. Everything inside the group is then managed by main.bicep.
set -euo pipefail

if [ $# -ne 3 ]; then
  echo "usage: $0 <resource-group> <location> <github-owner/repo>" >&2
  exit 1
fi
RESOURCE_GROUP=$1
LOCATION=$2
REPO=$3

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

RG_ID=$(az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --query id -o tsv)

APP_NAME="github-${REPO//\//-}-deploy"
APP_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv)
if [ -z "$APP_ID" ]; then
  APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
  az ad sp create --id "$APP_ID" >/dev/null
  az ad app federated-credential create --id "$APP_ID" --parameters "{
    \"name\": \"github-main\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:$REPO:ref:refs/heads/main\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }" >/dev/null
fi

az role assignment create --assignee "$APP_ID" --role Contributor --scope "$RG_ID" >/dev/null

cat <<EOF
Done. Now set these on the GitHub repo:

  gh secret set AZURE_CLIENT_ID --body $APP_ID
  gh secret set AZURE_TENANT_ID --body $TENANT_ID
  gh secret set AZURE_SUBSCRIPTION_ID --body $SUBSCRIPTION_ID
  gh variable set AZURE_RESOURCE_GROUP --body $RESOURCE_GROUP
  gh variable set AZURE_FUNCTIONAPP_NAME --body <globally-unique-app-name>
  gh variable set SPOTIFY_CLIENT_ID --body <spotify-client-id>
  gh secret set SPOTIFY_CLIENT_SECRET
EOF
