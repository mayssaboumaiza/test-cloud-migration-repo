"""Cloud Migration Agent Orchestrator with Bedrock + CrewAI"""

import json
import os
from typing import Any, Dict

from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from crewai import Agent, Task, Crew
import boto3

# Environment configuration
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "cloud-migration-agent-state")
S3_BUCKET = os.getenv("S3_BUCKET", "cloud-migration-agent-artifacts")
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

# Initialize AWS clients
bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
dynamodb = boto3.client("dynamodb", region_name=BEDROCK_REGION)
s3_client = boto3.client("s3", region_name=BEDROCK_REGION)
cloudwatch = boto3.client("cloudwatch", region_name=BEDROCK_REGION)

# Initialize LLM with Bedrock
llm = ChatBedrock(
    model_id=BEDROCK_MODEL_ID,
    region_name=BEDROCK_REGION,
    client=bedrock_client
)

# Initialize Embeddings with Bedrock
embeddings = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v1",
    region_name=BEDROCK_REGION,
    client=bedrock_client
)

# Note: OpenSearch vector store would be initialized for production
# vector_store = OpenSearchVectorSearch(
#     index_name="cloud-migration-vectors",
#     opensearch_url="https://opensearch-domain.region.es.amazonaws.com",
#     embedding_function=embeddings
# )


class CloudMigrationAgentOrchestrator:
    """Orchestrates multi-agent cloud migration analysis"""

    def __init__(self):
        self.llm = llm
        self.embeddings = embeddings
        self.dynamodb_table = DYNAMODB_TABLE
        self.s3_bucket = S3_BUCKET

    def create_agents(self) -> tuple[Agent, Agent, Agent]:
        """Create specialized agents for migration analysis"""

        # Agent 1: Infrastructure Analyzer
        infra_agent = Agent(
            role="Cloud Infrastructure Analyst",
            goal="Analyze cloud infrastructure and identify services",
            backstory="Expert in cloud architecture and IaC parsing",
            llm=self.llm,
            verbose=True
        )

        # Agent 2: Migration Strategist
        strategy_agent = Agent(
            role="Cloud Migration Strategist",
            goal="Develop optimal cloud migration strategies",
            backstory="Specialist in multi-cloud migrations with cost optimization",
            llm=self.llm,
            verbose=True
        )

        # Agent 3: Risk Assessor
        risk_agent = Agent(
            role="Cloud Risk Assessor",
            goal="Assess risks and dependencies in migrations",
            backstory="Expert in cloud security and compliance",
            llm=self.llm,
            verbose=True
        )

        return infra_agent, strategy_agent, risk_agent

    def create_tasks(self, agents: tuple[Agent, Agent, Agent]) -> list[Task]:
        """Create tasks for agents"""

        infra_agent, strategy_agent, risk_agent = agents

        tasks = [
            Task(
                description="Analyze the provided Terraform/CloudFormation files and identify all cloud services",
                agent=infra_agent,
                expected_output="List of services with types and dependencies"
            ),
            Task(
                description="Based on infrastructure analysis, develop migration strategies",
                agent=strategy_agent,
                expected_output="Migration plan with timeline and resource requirements"
            ),
            Task(
                description="Assess risks and compliance requirements for the migration",
                agent=risk_agent,
                expected_output="Risk assessment report with mitigation strategies"
            ),
        ]

        return tasks

    def run_migration_analysis(self, repo_url: str, source_cloud: str, target_cloud: str) -> Dict[str, Any]:
        """Execute migration analysis workflow"""

        agents = self.create_agents()
        tasks = self.create_tasks(agents)

        crew = Crew(
            agents=list(agents),
            tasks=tasks,
            verbose=True,
            process="sequential"
        )

        result = crew.kickoff()

        # Store results in DynamoDB
        self._store_results(repo_url, result)

        return {
            "status": "success",
            "analysis": result,
            "source_cloud": source_cloud,
            "target_cloud": target_cloud
        }

    def _store_results(self, repo_url: str, analysis: str) -> None:
        """Store analysis results in DynamoDB"""
        try:
            dynamodb.put_item(
                TableName=self.dynamodb_table,
                Item={
                    "agent_id": {"S": "migration-orchestrator"},
                    "timestamp": {"N": str(int(__import__("time").time()))},
                    "repo_url": {"S": repo_url},
                    "analysis": {"S": analysis[:3999]}  # DynamoDB 4KB limit
                }
            )
        except Exception as e:
            print(f"Error storing results: {e}")

    def get_cloudwatch_metrics(self) -> Dict[str, Any]:
        """Retrieve CloudWatch metrics"""
        try:
            metrics = cloudwatch.list_metrics(
                Namespace="CloudMigrationAgent"
            )
            return metrics
        except Exception as e:
            print(f"Error retrieving metrics: {e}")
            return {}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler for cloud migration analysis"""

    try:
        repo_url = event.get("repo_url", "")
        source_cloud = event.get("source_cloud", "aws")
        target_cloud = event.get("target_cloud", "gcp")

        orchestrator = CloudMigrationAgentOrchestrator()
        result = orchestrator.run_migration_analysis(repo_url, source_cloud, target_cloud)

        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


if __name__ == "__main__":
    # Local testing
    orchestrator = CloudMigrationAgentOrchestrator()
    result = orchestrator.run_migration_analysis(
        "https://github.com/test/repo",
        "aws",
        "gcp"
    )
    print(json.dumps(result, indent=2))
