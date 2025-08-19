/**
 * Complete list of supported integration types
 * Matching backend capabilities
 */

export const INTEGRATION_TYPES = [
  // Project Management
  'jira',
  'asana',
  'trello',
  'monday',
  'clickup',
  'basecamp',
  'notion',
  'airtable',
  
  // Customer Support
  'zendesk',
  'freshdesk',
  'intercom',
  'servicenow',
  'freshservice',
  
  // CRM Systems
  'salesforce',
  'hubspot',
  'pipedrive',
  'zoho_crm',
  'insightly',
  
  // Development & DevOps
  'github',
  'gitlab',
  'azure_devops',
  'bitbucket',
  'jenkins',
  'docker_hub',
  'kubernetes',
  
  // Communication & Collaboration
  'slack',
  'microsoft_teams',
  'discord',
  'zoom',
  'google_workspace',
  
  // Cloud Platforms
  'aws',
  'azure',
  'google_cloud_platform',
  'digitalocean',
  'heroku',
  
  // ERP Systems
  'netsuite',
  'sap',
  'dynamics365',
  'odoo',
  'quickbooks',
  
  // Marketing & Analytics
  'google_analytics',
  'mailchimp',
  'marketo',
  'pardot',
  'mixpanel',
  'amplitude',
  'hubspot_marketing',
  
  // E-commerce
  'shopify',
  'woocommerce',
  'magento',
  'bigcommerce',
  
  // Financial
  'stripe',
  'paypal',
  'xero',
  'sage',
  
  // HR & Recruitment
  'workday',
  'bamboohr',
  'greenhouse',
  
  // Custom & Others
  'custom',
  'webhook'
] as const;

export type IntegrationType = typeof INTEGRATION_TYPES[number];

export const INTEGRATION_CATEGORIES = {
  project_management: [
    'jira', 'asana', 'trello', 'monday', 'clickup', 'basecamp', 'notion', 'airtable'
  ],
  customer_support: [
    'zendesk', 'freshdesk', 'intercom', 'servicenow', 'freshservice'
  ],
  crm: [
    'salesforce', 'hubspot', 'pipedrive', 'zoho_crm', 'insightly'
  ],
  development: [
    'github', 'gitlab', 'azure_devops', 'bitbucket', 'jenkins', 'docker_hub', 'kubernetes'
  ],
  communication: [
    'slack', 'microsoft_teams', 'discord', 'zoom', 'google_workspace'
  ],
  cloud: [
    'aws', 'azure', 'google_cloud_platform', 'digitalocean', 'heroku'
  ],
  erp: [
    'netsuite', 'sap', 'dynamics365', 'odoo', 'quickbooks'
  ],
  marketing: [
    'google_analytics', 'mailchimp', 'marketo', 'pardot', 'mixpanel', 'amplitude', 'hubspot_marketing'
  ],
  ecommerce: [
    'shopify', 'woocommerce', 'magento', 'bigcommerce'
  ],
  financial: [
    'stripe', 'paypal', 'xero', 'sage'
  ],
  hr: [
    'workday', 'bamboohr', 'greenhouse'
  ],
  other: [
    'custom', 'webhook'
  ]
} as const;

export const INTEGRATION_ICONS = {
  // Project Management
  jira: '🎯',
  asana: '📋',
  trello: '📊',
  monday: '📅',
  clickup: '✅',
  basecamp: '🏕️',
  notion: '📝',
  airtable: '🗂️',
  
  // Customer Support
  zendesk: '🎫',
  freshdesk: '🆘',
  intercom: '💬',
  servicenow: '🔧',
  freshservice: '🛠️',
  
  // CRM Systems
  salesforce: '☁️',
  hubspot: '🧲',
  pipedrive: '📈',
  zoho_crm: '📊',
  insightly: '🔍',
  
  // Development & DevOps
  github: '🐙',
  gitlab: '🦊',
  azure_devops: '🔵',
  bitbucket: '🪣',
  jenkins: '👨‍🏭',
  docker_hub: '🐳',
  kubernetes: '☸️',
  
  // Communication & Collaboration
  slack: '💬',
  microsoft_teams: '👥',
  discord: '🎮',
  zoom: '🎥',
  google_workspace: '📧',
  
  // Cloud Platforms
  aws: '☁️',
  azure: '🔵',
  google_cloud_platform: '☁️',
  digitalocean: '🌊',
  heroku: '💜',
  
  // ERP Systems
  netsuite: '💼',
  sap: '🏢',
  dynamics365: '📊',
  odoo: '🔄',
  quickbooks: '📚',
  
  // Marketing & Analytics
  google_analytics: '📊',
  mailchimp: '🐵',
  marketo: '📧',
  pardot: '🎯',
  mixpanel: '📈',
  amplitude: '📊',
  hubspot_marketing: '🧲',
  
  // E-commerce
  shopify: '🛍️',
  woocommerce: '🛒',
  magento: '🏪',
  bigcommerce: '🏬',
  
  // Financial
  stripe: '💳',
  paypal: '💰',
  xero: '📊',
  sage: '📋',
  
  // HR & Recruitment
  workday: '👔',
  bamboohr: '🎋',
  greenhouse: '🌱',
  
  // Custom & Others
  custom: '⚙️',
  webhook: '🔗'
} as const;

export const INTEGRATION_NAMES = {
  // Project Management
  jira: 'Jira',
  asana: 'Asana',
  trello: 'Trello',
  monday: 'Monday.com',
  clickup: 'ClickUp',
  basecamp: 'Basecamp',
  notion: 'Notion',
  airtable: 'Airtable',
  
  // Customer Support
  zendesk: 'Zendesk',
  freshdesk: 'Freshdesk',
  intercom: 'Intercom',
  servicenow: 'ServiceNow',
  freshservice: 'Freshservice',
  
  // CRM Systems
  salesforce: 'Salesforce',
  hubspot: 'HubSpot',
  pipedrive: 'Pipedrive',
  zoho_crm: 'Zoho CRM',
  insightly: 'Insightly',
  
  // Development & DevOps
  github: 'GitHub',
  gitlab: 'GitLab',
  azure_devops: 'Azure DevOps',
  bitbucket: 'Bitbucket',
  jenkins: 'Jenkins',
  docker_hub: 'Docker Hub',
  kubernetes: 'Kubernetes',
  
  // Communication & Collaboration
  slack: 'Slack',
  microsoft_teams: 'Microsoft Teams',
  discord: 'Discord',
  zoom: 'Zoom',
  google_workspace: 'Google Workspace',
  
  // Cloud Platforms
  aws: 'Amazon Web Services',
  azure: 'Microsoft Azure',
  google_cloud_platform: 'Google Cloud Platform',
  digitalocean: 'DigitalOcean',
  heroku: 'Heroku',
  
  // ERP Systems
  netsuite: 'NetSuite',
  sap: 'SAP',
  dynamics365: 'Dynamics 365',
  odoo: 'Odoo',
  quickbooks: 'QuickBooks',
  
  // Marketing & Analytics
  google_analytics: 'Google Analytics',
  mailchimp: 'MailChimp',
  marketo: 'Marketo',
  pardot: 'Pardot',
  mixpanel: 'Mixpanel',
  amplitude: 'Amplitude',
  hubspot_marketing: 'HubSpot Marketing',
  
  // E-commerce
  shopify: 'Shopify',
  woocommerce: 'WooCommerce',
  magento: 'Magento',
  bigcommerce: 'BigCommerce',
  
  // Financial
  stripe: 'Stripe',
  paypal: 'PayPal',
  xero: 'Xero',
  sage: 'Sage',
  
  // HR & Recruitment
  workday: 'Workday',
  bamboohr: 'BambooHR',
  greenhouse: 'Greenhouse',
  
  // Custom & Others
  custom: 'Custom Integration',
  webhook: 'Webhook'
} as const;