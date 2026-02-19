import pandas as pd
import io

# Simulando exatamente o print que você mandou (Datas ISO com milissegundos e fuso Z)
csv_data = """Data
2026-02-06T13:22:55.840Z
2026-02-13T14:17:46.039Z
2026-02-13T14:51:21.960Z
2026-02-13T15:06:40.078Z
2026-02-12T14:31:31.327Z
"""

df = pd.read_csv(io.StringIO(csv_data))

print("--- TENTATIVA 1: dayfirst=True (Culpado Original?) ---")
try:
    s1 = pd.to_datetime(df["Data"], dayfirst=True, errors='coerce')
    print(s1)
    print(f"Falhas (NaT): {s1.isna().sum()}")
except Exception as e:
    print(f"Erro: {e}")

print("\n--- TENTATIVA 2: dayfirst=False (Padrão US/ISO) ---")
try:
    s2 = pd.to_datetime(df["Data"], dayfirst=False, errors='coerce')
    print(s2)
    print(f"Falhas (NaT): {s2.isna().sum()}")
except Exception as e:
    print(f"Erro: {e}")

print("\n--- TENTATIVA 3: Inferência Automática (Sem dayfirst) ---")
try:
    s3 = pd.to_datetime(df["Data"], errors='coerce')
    print(s3)
    print(f"Falhas (NaT): {s3.isna().sum()}")
except Exception as e:
    print(f"Erro: {e}")
