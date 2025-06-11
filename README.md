# Policy Navigator

Policy Navigator is an AI-powered retrieval-augmented generation (RAG) application that enables instant, context-aware responses based on a large collection of internal policy documents. It is specifically tailored for accessing and navigating IOM [HR Policies](https://hrhandbook.iom.int/hr-policy-framework) and [Admin Instructions](https://iomint.sharepoint.com/sites/DMSPortal/Instructions/Forms/AllItems.aspx). 


This tool provides a user-friendly interface to search, summarize, and interact with complex policy content, significantly improving accessibility and comprehension for end users.

## 🔧 Built On

The solution is based on the official [Azure RAG template](https://github.com/Azure-Samples/rag-postgres-openai-python), extended and customized to meet IOM’s organizational context and needs. All deployement instructions are available in the initial documentation.

## 🔄 Key Customizations

* 🎨 Frontend Styling
Updated to reflect IOM branding through revised colors, fonts, and layout consistency.

* ❓ IOM-Relevant Questions
The default query examples have been revised to reflect common user needs within IOM HR and administrative operations.

* 📄 PDF-to-Embedding Conversion
Added a script (`scripts/pdfs_to_seed_json.py`) that processes entire collections of PDF documents, extracts their content, and converts them into structured JSON files with embedded vectors for efficient hybrid retrieval (text+similarity).

* 🗃️ Database & Retrieval Adjustments
The underlying database schema and retrieval logic were adapted to support semantic paragraph chunking and ensure better alignment with how IOM policy content is structured and queried. (see [instructions](https://github.com/Azure-Samples/rag-postgres-openai-python/blob/main/docs/customize_data.md) and example [here](https://github.com/Azure-Samples/rag-postgres-openai-python/compare/main...otherdata#diff-0b3400c800b5efbb349e6dd4fab56beadf258fb77aad1a12e8652e151fae7bee))


## 🚫 SharePoint & Microsoft Copilot Limitations

While Microsoft Copilot provides basic document search in SharePoint, it:

*  does not allow semantic or structured querying across IOM's complex instruction hierarchy.
* assumes a perfectly curated and governed sharepoint structure, across microsoft knowledge graph.
* lacks customization for domain-specific vocabulary, policy contexts, or multilingual support.
* does not support hybrid retrieval combining text search with semantic similarity.

Those limitations make it unsuitable for the nuanced and context-rich policy navigation required by IOM staff.

