# Dockerfile optimizado para producción

# Usamos la imagen oficial de Airflow 2.9.2 como nuestra base.
# Esta imagen ya viene con todo lo necesario para correr Airflow.
FROM apache/airflow:2.9.2

# Es una buena práctica de seguridad no correr contenedores como root.
# Nos aseguramos de operar como el usuario 'airflow' que ya viene en la imagen.
USER airflow

# Copiamos nuestro archivo de requerimientos, que ahora contiene TODAS
# las dependencias de Python necesarias para el proyecto.
COPY requirements.txt /

# Ejecutamos UN SOLO comando 'pip install' para instalar todas las dependencias
# de la lista. Esto es más eficiente y limpio que tener varios 'RUN'.
# La opción --no-cache-dir crea una instalación más ligera.
RUN pip install --no-cache-dir -r /requirements.txt

# Finalmente, copiamos nuestro código personalizado (DAGs y posibles utilidades)
# a las carpetas correctas que Airflow espera para poder ejecutarlos.
COPY dags /opt/airflow/dags
COPY src /opt/airflow/src