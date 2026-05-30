# PUCSL Solar & Weather Prediction System

An end-to-end Machine Learning pipeline and interactive deployment dashboard designed for the **Public Utilities Commission of Sri Lanka (PUCSL)**. This system provides predictive intelligence for regional weather patterns and solar power generation, helping grid operators minimize load-shedding, manage spinning reserves, and smoothly integrate renewable energy into the national grid.

---

## 🚀 Project Architecture Overview

The system processes historical data (2010–2025) and scales from automated data engineering to multi-model inference and automated corporate reporting.

```text
📁 Root Directory
├── 📁 data/                  # Medallion Architecture Data Layers
│   ├── 📁 bronze/            # Raw, unprocessed station data
│   ├── 📁 silver/            # Cleaned, standardized, and imputed data
│   └── 📁 gold/              # Feature-engineered, model-ready arrays
├── 📁 docs/                  # System documentation
│   ├── api_reference.md
│   ├── data_dictionary.md
│   ├── model_architecture.md
│   └── project_overview.md
├── 📁 src/                   # Source code modules
├── app.py                    # Multi-page Streamlit Dashboard Application
├── create_folders.py         # Workspace environment initializer
├── create_presentation.py    # Automated PPTX reporting engine
└── merge_station_data.py     # Data ingestion and cleaning pipeline
