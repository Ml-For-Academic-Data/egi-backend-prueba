import sys
import os
import pandas as pd
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator

# Asegúrate de que Python pueda encontrar módulos personalizados (si usas más adelante)
SRC_PATH = "/opt/airflow/src"
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# Definición de rutas globales
# Montamos EFS en /opt/airflow/data, y el repo se clona en /repo-datos dentro de esa montura
RAW_DATA_PATH = "/opt/airflow/data/repo-datos/data/raw/dataset.csv" 
TEMP_DIR = "/opt/airflow/data/temp"
PROCESSED_DIR = "/opt/airflow/data/processed"

# Crear directorios si no existen
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Funciones reutilizables del pipeline
def handle_missing_values(df):
    """
    Maneja valores faltantes:
    - Categóricas: 'Unknown'
    - Numéricas: mediana
    """
    print("Manejando valores faltantes...")
    for col in df.columns:
        if df[col].isnull().sum() > 0:
            if df[col].dtype == "object":
                df[col] = df[col].fillna("Unknown")
            else:
                df[col] = df[col].fillna(df[col].median())
    return df


def remove_duplicate_rows(df):
    """
    Elimina filas duplicadas completas.
    """
    print("Eliminando filas duplicadas...")
    return df.drop_duplicates()


def filter_numeric_outliers(df, threshold=3):
    """
    Filtra outliers usando Z-score.
    """
    print("Filtrando outliers numéricos...")
    numeric_cols = df.select_dtypes(include='number').columns
    z_scores = (df[numeric_cols] - df[numeric_cols].mean()) / df[numeric_cols].std()
    filtered_df = df[(z_scores.abs() < threshold).all(axis=1)]
    return filtered_df


def create_derived_features(df):
    """
    Crea nuevas características derivadas.
    Ejemplo: suma de columnas numéricas como feature adicional.
    """
    print("Creando características derivadas...")
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    df['total_score'] = df[numeric_cols].sum(axis=1)
    return df


# Tareas del pipeline
def load_data_task():
    """Carga los datos iniciales"""
    df = pd.read_csv(RAW_DATA_PATH)
    df.to_csv(f"{TEMP_DIR}/dataset_temp.csv", index=False)
    print(f"Datos cargados: {df.shape}")


def handle_missing_task():
    """Maneja valores faltantes"""
    df = pd.read_csv(f"{TEMP_DIR}/dataset_temp.csv")
    df_cleaned = handle_missing_values(df)
    df_cleaned.to_csv(f"{TEMP_DIR}/step1_missing_handled.csv", index=False)
    print(f"Valores faltantes manejados: {df_cleaned.shape}")


def remove_duplicates_task():
    """Remueve duplicados"""
    df = pd.read_csv(f"{TEMP_DIR}/step1_missing_handled.csv")
    df_cleaned = remove_duplicate_rows(df)
    df_cleaned.to_csv(f"{TEMP_DIR}/step2_duplicates_removed.csv", index=False)
    print(f"Duplicados removidos: {df_cleaned.shape}")


def filter_outliers_task():
    """Filtra outliers"""
    df = pd.read_csv(f"{TEMP_DIR}/step1_missing_handled.csv")  # Desde step1
    df_cleaned = filter_numeric_outliers(df)
    df_cleaned.to_csv(f"{TEMP_DIR}/step2b_outliers_filtered.csv", index=False)
    print(f"Outliers filtrados: {df_cleaned.shape}")


def create_features_task():
    """Crea features derivadas combinando ambos paths"""
    df1 = pd.read_csv(f"{TEMP_DIR}/step2_duplicates_removed.csv")
    df2 = pd.read_csv(f"{TEMP_DIR}/step2b_outliers_filtered.csv")

    # Usar el que tenga más filas (ejemplo simple)
    df_to_use = df1 if len(df1) > len(df2) else df2

    df_final = create_derived_features(df_to_use)
    df_final.to_csv(f"{PROCESSED_DIR}/cleaned_data.csv", index=False)
    print(f"Features creadas: {df_final.shape}")


def generate_report_task():
    """Genera un reporte simple"""
    df = pd.read_csv(f"{PROCESSED_DIR}/cleaned_data.csv")

    report = f"""
REPORTE DE LIMPIEZA DE DATOS
============================
Total de filas: {len(df)}
Total de columnas: {len(df.columns)}
Valores nulos restantes: {df.isnull().sum().sum()}

Columnas: {', '.join(df.columns.tolist())}
"""

    with open(f"{PROCESSED_DIR}/cleaning_report.txt", "w") as f:
        f.write(report)

    print("Reporte generado")


# Configuración del DAG
default_args = {
    "owner": "airflow",
    "start_date": datetime(2025, 1, 1),
}

with DAG(
    dag_id="mlops_dropout_prediction",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
) as dag:

    start = DummyOperator(task_id="start")

    load_data = PythonOperator(
        task_id="load_data",
        python_callable=load_data_task
    )

    handle_missing = PythonOperator(
        task_id="handle_missing_values",
        python_callable=handle_missing_task
    )

    # Dos ramas paralelas
    remove_duplicates = PythonOperator(
        task_id="remove_duplicates",
        python_callable=remove_duplicates_task
    )

    filter_outliers = PythonOperator(
        task_id="filter_outliers",
        python_callable=filter_outliers_task
    )

    # Unión en create_features
    create_features = PythonOperator(
        task_id="create_features",
        python_callable=create_features_task
    )

    # Tarea final de reporte
    generate_report = PythonOperator(
        task_id="generate_report",
        python_callable=generate_report_task
    )

    end = DummyOperator(task_id="end")

    # Flujo del DAG con ramificación
    start >> load_data >> handle_missing
    handle_missing >> remove_duplicates >> create_features
    handle_missing >> filter_outliers >> create_features
    create_features >> generate_report >> end