targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment (e.g., dev, prod)')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

// Existing Azure AI Foundry endpoint (not provisioned here)
param azureAiProjectEndpoint string
param modelDeploymentName string = 'gpt-4o'
param azureContentUnderstandingEndpoint string = ''
param bingConnectionId string = ''

// API keys (stored in Key Vault)
@secure()
param onemapEmail string
@secure()
param onemapPassword string
@secure()
param uraAccessKey string

var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }
var rgName = 'rg-sgp-geospatial-agentic-ai-app'

resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: rgName
  location: location
  tags: tags
}

module managedIdentity './modules/managed-identity.bicep' = {
  name: 'managed-identity'
  scope: rg
  params: {
    name: 'id-${resourceToken}'
    location: location
    tags: tags
  }
}

module containerRegistry './modules/container-registry.bicep' = {
  name: 'container-registry'
  scope: rg
  params: {
    name: 'cr${resourceToken}'
    location: location
    tags: tags
    managedIdentityPrincipalId: managedIdentity.outputs.principalId
  }
}

module keyVault './modules/key-vault.bicep' = {
  name: 'key-vault'
  scope: rg
  params: {
    name: 'kv-${resourceToken}'
    location: location
    tags: tags
    managedIdentityPrincipalId: managedIdentity.outputs.principalId
    onemapEmail: onemapEmail
    onemapPassword: onemapPassword
    uraAccessKey: uraAccessKey
  }
}

module containerAppsEnv './modules/container-apps-env.bicep' = {
  name: 'container-apps-env'
  scope: rg
  params: {
    name: 'cae-${resourceToken}'
    location: location
    tags: tags
  }
}

// --- MCP Servers (internal only) ---

module mcpOnemap './modules/container-app.bicep' = {
  name: 'mcp-onemap'
  scope: rg
  params: {
    name: 'mcp-onemap'
    location: location
    tags: union(tags, { 'azd-service-name': 'mcp-onemap' })
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerRegistryLoginServer: containerRegistry.outputs.loginServer
    managedIdentityId: managedIdentity.outputs.id
    targetPort: 8000
    external: true
    env: [
      { name: 'MCP_TRANSPORT', value: 'streamable-http' }
      { name: 'ONEMAP_EMAIL', secretRef: 'onemap-email' }
      { name: 'ONEMAP_PASSWORD', secretRef: 'onemap-password' }
    ]
    secrets: [
      { name: 'onemap-email', keyVaultUrl: keyVault.outputs.secretUris.onemapEmail }
      { name: 'onemap-password', keyVaultUrl: keyVault.outputs.secretUris.onemapPassword }
    ]
  }
}

module mcpUra './modules/container-app.bicep' = {
  name: 'mcp-ura'
  scope: rg
  params: {
    name: 'mcp-ura'
    location: location
    tags: union(tags, { 'azd-service-name': 'mcp-ura' })
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerRegistryLoginServer: containerRegistry.outputs.loginServer
    managedIdentityId: managedIdentity.outputs.id
    targetPort: 8000
    external: true
    env: [
      { name: 'MCP_TRANSPORT', value: 'streamable-http' }
      { name: 'URA_ACCESS_KEY', secretRef: 'ura-access-key' }
    ]
    secrets: [
      { name: 'ura-access-key', keyVaultUrl: keyVault.outputs.secretUris.uraAccessKey }
    ]
  }
}

module mcpMoe './modules/container-app.bicep' = {
  name: 'mcp-moe'
  scope: rg
  params: {
    name: 'mcp-moe'
    location: location
    tags: union(tags, { 'azd-service-name': 'mcp-moe' })
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerRegistryLoginServer: containerRegistry.outputs.loginServer
    managedIdentityId: managedIdentity.outputs.id
    targetPort: 8000
    external: true
    env: [
      { name: 'MCP_TRANSPORT', value: 'streamable-http' }
    ]
    secrets: []
  }
}

// --- Backend ---

module backend './modules/container-app.bicep' = {
  name: 'backend'
  scope: rg
  params: {
    name: 'backend'
    location: location
    tags: union(tags, { 'azd-service-name': 'backend' })
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerRegistryLoginServer: containerRegistry.outputs.loginServer
    managedIdentityId: managedIdentity.outputs.id
    targetPort: 8000
    external: true
    env: [
      { name: 'AZURE_AI_PROJECT_ENDPOINT', value: azureAiProjectEndpoint }
      { name: 'MODEL_DEPLOYMENT_NAME', value: modelDeploymentName }
      { name: 'AZURE_CONTENT_UNDERSTANDING_ENDPOINT', value: azureContentUnderstandingEndpoint }
      { name: 'BING_CONNECTION_ID', value: bingConnectionId }
      { name: 'AZURE_CLIENT_ID', value: managedIdentity.outputs.clientId }
      { name: 'ONEMAP_MCP_URL', value: 'http://mcp-onemap/mcp' }
      { name: 'URA_MCP_URL', value: 'http://mcp-ura/mcp' }
      { name: 'MOE_MCP_URL', value: 'http://mcp-moe/mcp' }
      { name: 'CORS_ORIGINS', value: '["https://frontend.${containerAppsEnv.outputs.defaultDomain}"]' }
    ]
    secrets: []
  }
}

// --- Frontend ---

module frontend './modules/container-app.bicep' = {
  name: 'frontend'
  scope: rg
  params: {
    name: 'frontend'
    location: location
    tags: union(tags, { 'azd-service-name': 'frontend' })
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerRegistryLoginServer: containerRegistry.outputs.loginServer
    managedIdentityId: managedIdentity.outputs.id
    targetPort: 8080
    external: true
    env: [
      { name: 'BACKEND_HOST', value: 'backend' }
    ]
    secrets: []
  }
}

output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.outputs.name
output FRONTEND_URL string = 'https://frontend.${containerAppsEnv.outputs.defaultDomain}'
output BACKEND_URL string = 'https://backend.internal.${containerAppsEnv.outputs.defaultDomain}'