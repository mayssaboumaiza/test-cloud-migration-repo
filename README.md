# Cloud Migration Agent - Test Repository

Test infrastructure for cloud migration analysis using multi-agent AI orchestration.

## Architecture

- **IaC**: AWS Terraform (Lambda, DynamoDB, S3, Bedrock, CloudWatch)
- **AI Stack**: CrewAI, LangChain, Bedrock LLM, Titan Embeddings
- **Framework**: Multi-agent orchestration for infrastructure analysis

## Services Deployed

### AWS Infrastructure (main.tf)
- **Lambda**: Agent orchestrator (cloud-migration-agent-orchestrator)
- **DynamoDB**: Agent state persistence (cloud-migration-agent-state)
- **S3**: Agent artifacts storage (cloud-migration-agent-artifacts-*)
- **Bedrock**: Claude 3 Sonnet LLM + Titan Embeddings
- **CloudWatch**: Logging and monitoring

### AI Stack (app.py + config.py)
- **LLM**: ChatBedrock (Claude 3 Sonnet)
- **Embeddings**: BedrockEmbeddings (Amazon Titan Text)
- **Vector Store**: FAISS (local), supports Weaviate, ChromaDB, OpenSearch
- **Agents**: 3 specialized agents (Infrastructure Analyzer, Migration Strategist, Risk Assessor)
- **Framework**: CrewAI for agent orchestration

## File Structure

```
.
├── main.tf              # Terraform infrastructure (AWS)
├── app.py               # CrewAI orchestration + Lambda handler
├── config.py            # LangChain + Bedrock configuration + RAG setup
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Usage

### Local Testing
```bash
python app.py
```

### Deploy to AWS
```bash
terraform init
terraform plan
terraform apply
```

### Environment Variables
```bash
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
export EMBEDDING_MODEL_ID=amazon.titan-embed-text-v1
export DYNAMODB_TABLE=cloud-migration-agent-state
export S3_BUCKET=cloud-migration-agent-artifacts-ACCOUNT_ID
```

## AI Stack Components Detected

During cloud migration analysis, this repo will be detected as having:

### LLM Providers
- [x] ChatBedrock (Claude 3 Sonnet 20240229)

### Embeddings
- [x] BedrockEmbeddings (Amazon Titan Embed Text V1, 1536 dimensions)

### Vector Stores
- [x] FAISS (portable, local)
- [ ] Weaviate (config only, requires setup)
- [ ] ChromaDB (config only, requires setup)
- [ ] OpenSearch (config only, requires connection)

### Frameworks
- [x] CrewAI (multi-agent orchestration)
- [x] LangChain (RAG, chains, memory)

### Cloud Services (Terraform)
- [x] AWS Bedrock (LLM inference)
- [x] AWS Lambda (compute)
- [x] AWS DynamoDB (state storage)
- [x] AWS S3 (artifacts)
- [x] AWS CloudWatch (monitoring)

## Cloud Migration Scenarios

### AWS → GCP
- Bedrock → Vertex AI
- Titan Embeddings → Gecko Embeddings
- DynamoDB → Firestore
- Lambda → Cloud Run
- S3 → Cloud Storage

### AWS → Azure
- Bedrock → Azure OpenAI
- Titan Embeddings → Azure OpenAI Embeddings
- DynamoDB → Cosmos DB
- Lambda → Azure Functions
- S3 → Azure Blob Storage

## Notes

This is a **test repository** designed to validate the Cloud Migrator's ability to:
1. Detect infrastructure code (Terraform)
2. Detect AI stack usage (LLM, embeddings, vector stores)
3. Generate migration plans (service mappings, framework adaptations)
4. Estimate effort and risks

For production use, ensure:
- Bedrock access in your AWS region
- Proper IAM permissions
- Vector store setup (if using on-prem backends)
- Environment variable configuration
