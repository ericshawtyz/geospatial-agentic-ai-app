param name string
param location string
param tags object = {}
param managedIdentityPrincipalId string

@secure()
param onemapEmail string
@secure()
param onemapPassword string
@secure()
param uraAccessKey string

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
  }
}

// Key Vault Secrets User role for managed identity
resource kvSecretsRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: kv
  name: guid(kv.id, managedIdentityPrincipalId, '4633458b-17de-408a-b874-0445c86b69e6')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource secretOnemapEmail 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'onemap-email'
  properties: {
    value: onemapEmail
  }
}

resource secretOnemapPassword 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'onemap-password'
  properties: {
    value: onemapPassword
  }
}

resource secretUraAccessKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'ura-access-key'
  properties: {
    value: uraAccessKey
  }
}

output name string = kv.name
output secretUris object = {
  onemapEmail: secretOnemapEmail.properties.secretUri
  onemapPassword: secretOnemapPassword.properties.secretUri
  uraAccessKey: secretUraAccessKey.properties.secretUri
}
