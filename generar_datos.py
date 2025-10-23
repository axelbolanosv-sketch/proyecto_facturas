"""
generar_datos.py

Genera un archivo Excel con facturas ficticias para realizar pruebas
del sistema de búsqueda.
"""

# The code snippet you provided is a Python script that generates fictitious invoice data and saves it
# to an Excel file for testing purposes. Here is a breakdown of what the code does:
import pandas as pd
from faker import Faker
import random
import os

fake = Faker("es_ES")  # Generador de datos falsos en español

# Configuración de cantidad de registros
NUM_FACTURAS = 15000
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Listas base de emisores, estados y clientes
emisores = ["ACME S.A.", "GlobalCorp Ltda.", "Servicios Tico", "Comercial Delta", "Innova CR"]
estados = ["Pagada", "Pendiente", "Cancelada"]
clientes = [fake.name() for _ in range(200)]

# Generar los registros
facturas = []
for i in range(NUM_FACTURAS):
    emisor = random.choice(emisores)
    codigo = f"F{random.randint(1,999):03d}-{random.randint(1,99999):05d}"
    monto = round(random.uniform(50, 5000), 2)
    fecha = fake.date_between(start_date="-1y", end_date="today").strftime("%Y-%m-%d")
    cliente = random.choice(clientes)
    estado = random.choice(estados)

    facturas.append({
        "Emisor": emisor,
        "CodigoFactura": codigo,
        "Monto": monto,
        "Fecha": fecha,
        "Cliente": cliente,
        "Estado": estado
    })

# Crear DataFrame y guardar en Excel
# The code snippet is creating a Pandas DataFrame from the list of `facturas`, which contains
# generated invoice data. Then, it is saving this DataFrame to an Excel file named "facturas.xlsx" in
# the "data" directory. Finally, it prints a message indicating the path of the generated Excel file
# and the number of invoices (rows) in the DataFrame.
df = pd.DataFrame(facturas)
ruta = os.path.join(DATA_DIR, "facturas.xlsx")
df.to_excel(ruta, index=False)

print(f" Archivo generado: {ruta} ({len(df)} facturas)")
