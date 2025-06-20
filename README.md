# Policy Navigator

Policy Navigator is an AI-powered retrieval-augmented generation (RAG) application that enables instant, context-aware responses based on a large collection of internal policy documents. It is specifically tailored for accessing and navigating IOM [HR Policies](https://hrhandbook.iom.int/hr-policy-framework), [Admin Instructions](https://iomint.sharepoint.com/sites/DMSPortal/Instructions/Forms/AllItems.aspx) and [Audits](https://governingbodies.iom.int/). 


This tool provides a user-friendly interface to search, summarize, and interact with complex policy content, significantly improving accessibility and comprehension for end users.

## 🔧 Built On

The solution is based on the official [Azure RAG template](https://github.com/Azure-Samples/rag-postgres-openai-python), extended and customized to meet IOM’s organizational context and needs. All deployement instructions are available in the initial documentation. This version was selected among all the accelerators that are available on the Azure RAG page, because of its simplicity (it use only postgreSQL as a database, leverage it full capacity for vector search, and does not require any additional componnents such as  Azure AI Search ) and its flexibility (it allows to use any Language model). It is therefore not tight  to a specific Azure service, and can be used with any OpenAI compatible endpoint.

Think of this as __a natural language query interface for IOM's policy documents, where users can ask questions in plain language and receive accurate, contextually relevant answers__.


## 🔄 Key Customizations

* 🎨 Frontend Styling
Updated to reflect IOM branding through revised colors, fonts, and layout consistency.

* ❓ IOM-Relevant Questions
The default query examples have been revised to reflect common user needs within IOM HR and administrative operations.

* 📄 PDF-to-Embedding Conversion
Added a script (`scripts/pdfs_to_seed_json.py`) that processes entire collections of PDF documents, extracts their content, and converts them into structured JSON files with embedded vectors for efficient hybrid retrieval (text+similarity).

* 🗃️ Database & Retrieval Adjustments
The underlying database schema and retrieval logic were adapted to support semantic paragraph chunking and ensure better alignment with how IOM policy content is structured and queried. (see [instructions](https://github.com/Azure-Samples/rag-postgres-openai-python/blob/main/docs/customize_data.md) and example [here](https://github.com/Azure-Samples/rag-postgres-openai-python/compare/main...otherdata#diff-0b3400c800b5efbb349e6dd4fab56beadf258fb77aad1a12e8652e151fae7bee))

*  Added a capacity to measure the environemental impact of the queries, by measuring the number of tokens used in the query and the response, and calculating the carbon footprint of the query. This is done using the [Ecologist](https://ecologits.ai/latest/) module and is displayed in the UI.


## 🚫 SharePoint & Microsoft Copilot Limitations

While Microsoft Copilot provides basic document search in SharePoint, it:

*  does not allow semantic or structured querying across IOM's complex instruction hierarchy.
* assumes a perfectly curated and governed sharepoint structure, across microsoft knowledge graph.
* lacks customization for domain-specific vocabulary, policy contexts, or multilingual support.
* does not support hybrid retrieval combining text search with semantic similarity.

Those limitations make it unsuitable for the nuanced and context-rich policy navigation required by IOM staff.

## Setting Up fist Locally

As a requirement you will need to get access to an OpenAI endpoint in Azure - with both a generative and embedding model. You can use the [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quickstart?pivots=programming-language-python) to set this up.


### 1. clone this repository

### 2. set up a virtual environment and install the requirements:

```bash 
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements-dev.txt
pip install -e src/backend
```

### 3. create a data folder - with subfolders for all documents you want to process (PDF and words... Words will be converted to PDF automatically)

### 4. run the pdfs_to_seed_json script to convert all documents in the data folder to a seed.json file:

```bash
python ./scripts/pdfs_to_seed_json.py --data_folder ./data --output_file ./src/backend/fastapi_app/seed_data.json
```

### 5. set up the database 

This project uses PostgreSQL with the pgvector extension for vector storage. This extension is not straightforward to install, so the easiest is to use a prebuilt PostgreSQL Docker  container. This implies to install Docker desktop.

```bash 
docker pull ankane/pgvector  ## an official Docker image with pgvector preinstalled
```

Create you default DB for the project with the following command:

```bash
docker run -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=mysecretpassword -e POSTGRES_DB=policy --name my_postgres -p 5432:5432 -d ankane/pgvector  
```


### Define your envionment variables

Copy `.env.sample` into a `.env` file  and fill the required information.

#### Load your json file into the database

You can use the provided script to load the seed data into the database. Make sure your PostgreSQL server is running and accessible.

```bash 
# Ensure you have PostgreSQL running and accessible
python ./src/backend/fastapi_app/setup_postgres_database.py
python ./src/backend/fastapi_app/setup_postgres_seeddata.py
```


####  Build the frontend:

```bash
cd src/frontend
npm install
npm run build
cd ../../
``

There must be an initial build of static assets before running the backend, since the backend serves static files from the `src/static` directory.

#### Run the FastAPI backend (with hot reloading). This should be run from the root of the project:

```shell
python -m uvicorn fastapi_app:create_app --factory --reload
``

Or you can run "Backend" in the VS Code Run & Debug menu.

####  Run the frontend (with hot reloading):

```bash
cd src/frontend
npm run dev
``

Or you can run "Frontend" or "Frontend & Backend" in the VS Code Run & Debug menu.

### Et voila!

Open the browser at `http://localhost:5173/` and you will see the frontend.

---- 

## Deploy on Azure

Once you have customized the application to your needs, you can deploy it on Azure. The approach is fairly automatised an use biceps files that are within the `infra` folder. You can use the following command to deploy the application:

**IMPORTANT:** In order to deploy and run this example, you'll need:

- **Azure account**. If you're new to Azure, [get an Azure account for free](https://azure.microsoft.com/free/cognitive-search/) and you'll get some free Azure credits to get started. See [guide to deploying with the free trial](docs/deploy_freetrial.md).
- **Azure account permissions**:
  - Your Azure account must have `Microsoft.Authorization/roleAssignments/write` permissions, such as [Role Based Access Control Administrator](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#role-based-access-control-administrator-preview), [User Access Administrator](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#user-access-administrator), or [Owner](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#owner). If you don't have subscription-level permissions, you must be granted [RBAC](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#role-based-access-control-administrator-preview) for an existing resource group and [deploy to that existing group](docs/deploy_existing.md#resource-group).
  - Your Azure account also needs `Microsoft.Resources/deployments/write` permissions on the subscription level.
- **Azure CLI**: Install the [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) 

```bash
# Loging
az login

#Create a new azd environment:
azd env new

## Provision the resources and deploy the code:
azd up
```


Further documentation is available in the `docs/` folder:
