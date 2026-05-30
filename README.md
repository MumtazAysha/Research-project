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

Medallion Data Pipeline: Implements a structured Bronze ➔ Silver ➔ Gold data lakehouse design pattern to guarantee data traceabilty and clean state transitions.
Advanced Feature Engineering: Implements continuous temporal tracking using Cyclical Sine/Cosine Encodings for hours/months and Lag Features (t-1h, t-2h, t-24h) to capture sudden atmospheric variations.
Multi-Model Inference Engine: Compares structural baselines (Polynomial Regression) against powerful non-linear ensembles (Random Forest & XGBoost Regressor) to predict Global Horizontal Irradiance (GHI) and Grid Yield.
Interactive Dashboard UI: Built with Streamlit, featuring production-ready forecasting modules, district-level geospatial mapping, and automated statistical analysis windows.
Automated Corporate Reporting: Programmatically generates comprehensive 17-slide stakeholder presentation decks using python-pptx directly from pipeline results[cite: 1].
