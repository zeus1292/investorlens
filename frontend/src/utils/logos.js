/**
 * Maps company_id → public domain used by Clearbit Logo API.
 * For companies that are products (BigQuery, Redshift, Azure Synapse),
 * we use the parent company domain since that's what Clearbit has.
 *
 * Logo URL pattern: https://logo.clearbit.com/{domain}
 */
export const COMPANY_DOMAINS = {
  // Cloud Data Platforms
  snowflake:      'snowflake.com',
  databricks:     'databricks.com',
  bigquery:       'google.com',
  redshift:       'amazon.com',
  azure_synapse:  'microsoft.com',
  teradata:       'teradata.com',
  cloudera:       'cloudera.com',
  motherduck:     'motherduck.com',

  // AI/ML Platforms
  c3ai:           'c3.ai',
  palantir:       'palantir.com',
  dataiku:        'dataiku.com',
  datarobot:      'datarobot.com',
  h2oai:          'h2o.ai',
  scale_ai:       'scale.com',
  wandb:          'wandb.ai',
  hugging_face:   'huggingface.co',

  // Data Integration / ETL
  fivetran:       'fivetran.com',
  dbt_labs:       'getdbt.com',
  airbyte:        'airbyte.com',
  informatica:    'informatica.com',
  talend:         'talend.com',
  matillion:      'matillion.com',

  // Data Observability / Governance
  monte_carlo:    'montecarlodata.com',
  atlan:          'atlan.com',
  alation:        'alation.com',
  great_expectations: 'greatexpectations.io',
  collibra:       'collibra.com',

  // Vector / AI Infrastructure
  pinecone:       'pinecone.io',
  weaviate:       'weaviate.io',
  chroma:         'trychroma.com',
  zilliz:         'zilliz.com',
  qdrant:         'qdrant.tech',

  // Emerging / Disruptors
  firebolt:       'firebolt.io',
  clickhouse:     'clickhouse.com',
  starrocks:      'starrocks.io',
  neon:           'neon.tech',
  supabase:       'supabase.com',
};

/**
 * Returns the Clearbit logo domain for a given company_id or display name.
 * Normalises the input so both "Snowflake" and "snowflake" resolve correctly.
 */
export function getCompanyDomain(companyIdOrName) {
  if (!companyIdOrName) return null;
  const key = companyIdOrName
    .toLowerCase()
    .replace(/[\s\-\.]/g, '_')   // spaces/hyphens/dots → underscore
    .replace(/_+/g, '_')         // collapse runs
    .replace(/^_|_$/g, '');      // trim leading/trailing
  return COMPANY_DOMAINS[key] ?? COMPANY_DOMAINS[key.replace(/_/g, '')] ?? null;
}
