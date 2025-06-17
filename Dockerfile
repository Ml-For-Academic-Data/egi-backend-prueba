# Dockerfile optimizado para producción
FROM apache/airflow:2.9.2

# Cambiar temporalmente a root para instalar dependencias del sistema
USER root

# Instalar dependencias del sistema necesarias para mysqlclient
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Volver al usuario airflow
USER airflow

# Copiamos nuestro archivo de requerimientos
COPY requirements.txt /

# Instalamos las dependencias de Python
RUN pip install --no-cache-dir -r /requirements.txt

# Copiamos el código
COPY dags /opt/airflow/dags
COPY src /opt/airflow/src