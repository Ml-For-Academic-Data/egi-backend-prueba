# Usamos la imagen oficial de Airflow 2.9.2 como nuestra base.
# Esta imagen ya viene con todo lo necesario para correr Airflow.
FROM apache/airflow:2.9.2

# Cambiamos al usuario 'root' temporalmente solo si necesitáramos instalar
# paquetes del sistema operativo (ej: build-essential). Por ahora no es necesario.
# USER root
# RUN apt-get update && apt-get install -y build-essential

# Volvemos al usuario por defecto 'airflow'. Es una buena práctica de seguridad
# no correr contenedores como root.
USER airflow

# Copiamos nuestro archivo de requerimientos de Python al contenedor.
COPY requirements.txt /

# Usando el gestor de paquetes de Python (pip), instalamos todas las librerías
# que definimos. La opción --no-cache-dir crea una instalación más ligera.
RUN pip install --no-cache-dir -r /requirements.txt

# Finalmente, copiamos nuestro código personalizado (DAGs y posibles utilidades)
# a las carpetas correctas que Airflow espera.
COPY dags /opt/airflow/dags
COPY src /opt/airflow/src