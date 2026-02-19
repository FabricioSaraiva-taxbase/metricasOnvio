"""
Teste rápido do classificador melhorado.
Valida: blacklist, categorias expandidas e novas categorias.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auditor_logic import AuditorClassifier

classifier = AuditorClassifier()

# ==============================
# TESTES DE BLACKLIST
# ==============================
BLACKLIST_FILES = [
    "DANFE NF 123456.pdf",
    "Nota Fiscal Eletronica - Empresa ABC.pdf",
    "NFe 35210298765432100012345.pdf",
    "NFS-e São Paulo.pdf",
    "Boleto Banco Itau Fev2026.pdf",
    "Fatura Energia Eletrica.pdf",
    "Comprovante de Pagamento DARF.pdf",
    "Contrato Social Consolidado.pdf",
    "Procuração Eletrônica.pdf",
    "Extrato Bancário Janeiro.pdf",
    "Certidão Negativa de Débitos.pdf",
    "Balancete Mensal 01.2026.pdf",
    "Folha de Pagamento Janeiro.pdf",
    "Holerite Funcionario.pdf",
    "Rescisão Contrato Trabalho.pdf",
    "Férias Funcionário João.pdf",
    "Recibo de Aluguel Janeiro.pdf",
    "XML Notas Fiscais.pdf",
    "Duplicata Vencida.pdf",
    "Alvará de Funcionamento.pdf",
]

print("=" * 60)
print("🚫 TESTE 1: BLACKLIST (devem ser IGNORADOS)")
print("=" * 60)
bl_ok = 0
bl_fail = 0
for f in BLACKLIST_FILES:
    result = classifier.is_blacklisted(f)
    status = "✅ BLOQUEADO" if result else "❌ FALHOU"
    if result:
        bl_ok += 1
    else:
        bl_fail += 1
    print(f"  {status} | {f}")

print(f"\n  Resultado: {bl_ok}/{len(BLACKLIST_FILES)} bloqueados corretamente\n")

# ==============================
# TESTES DE CATEGORIAS EXISTENTES (expandidas)
# ==============================
CATEGORY_FILES = [
    ("Recibo EFD Contribuicoes 01.2026.pdf", "EFD_CONTRIBUICOES"),
    ("EFD Contri Empresa ABC.pdf", "EFD_CONTRIBUICOES"),
    ("Sped Contribuições Dez.pdf", "EFD_CONTRIBUICOES"),
    ("GUIA ISS Janeiro.pdf", "ISS"),
    ("ISS Tomado 01.2026.pdf", "ISS"),
    ("EFD REINF Fev.pdf", "REINF"),
    ("DARF IRRF 01.2026.pdf", "IRRF"),
    ("GARE ICMS Janeiro.pdf", "GUIA_ICMS"),
    ("DARE-ICMS 01.2026.pdf", "GUIA_ICMS"),
    ("PGDAS-D Janeiro.pdf", "SIMPLES_NACIONAL"),
    ("DAS Simples Nacional.pdf", "SIMPLES_NACIONAL"),
    ("DEFIS 2025.pdf", "SIMPLES_NACIONAL"),
    ("SPED FISCAL 01.2026.pdf", "SPED_ICMS"),
    ("EFD ICMS IPI Janeiro.pdf", "SPED_ICMS"),
    ("Recibo SPED Fev.pdf", "SPED_ICMS"),
    ("GIA SP Janeiro.pdf", "GIA_ICMS"),
    ("NOVA GIA 01.2026.pdf", "GIA_ICMS"),
    ("DARF PIS Janeiro.pdf", "PIS_COFINS"),
    ("DARF COFINS 01.2026.pdf", "PIS_COFINS"),
    ("Reparcelamento Empresa X.pdf", "PARCELAMENTO"),
    ("DCTF WEB Fev.pdf", "DCTFWEB"),
    ("DCTF-WEB 01.2026.pdf", "DCTFWEB"),
    ("ECF 2025 Empresa.pdf", "IRPJ_CSLL"),
    ("LALUR 2025.pdf", "IRPJ_CSLL"),
    ("ICMS DIFAL Janeiro.pdf", "ICMS_DIFAL"),
    ("Substituição Tributária.pdf", "ICMS_ST"),
]

print("=" * 60)
print("📂 TESTE 2: CATEGORIAS EXPANDIDAS")
print("=" * 60)
cat_ok = 0
cat_fail = 0
for filename, expected in CATEGORY_FILES:
    result = classifier.identify_category(filename)
    status = "✅" if result == expected else "❌"
    if result == expected:
        cat_ok += 1
    else:
        cat_fail += 1
    print(f"  {status} | {filename} → {result} (esperado: {expected})")

print(f"\n  Resultado: {cat_ok}/{len(CATEGORY_FILES)} classificadas corretamente\n")

# ==============================
# TESTES DE NOVAS CATEGORIAS
# ==============================
NEW_CATEGORY_FILES = [
    ("DARF INSS Janeiro.pdf", "INSS"),
    ("GPS Empresa ABC.pdf", "INSS"),
    ("Guia INSS 01.2026.pdf", "INSS"),
    ("GFIP Janeiro.pdf", "FGTS"),
    ("SEFIP 01.2026.pdf", "FGTS"),
    ("FGTS Empresa.pdf", "FGTS"),
    ("IPTU 2026.pdf", "IPTU"),
    ("TFE São Paulo.pdf", "TAXA_LICENCA"),
    ("Taxa de Licença 2026.pdf", "TAXA_LICENCA"),
    ("DARF IRPF Janeiro.pdf", "IRPF"),
    ("IRPF 2025.pdf", "IRPF"),
    ("DARF ITR 2025.pdf", "ITR"),
    ("ITR Fazenda.pdf", "ITR"),
    ("DSTDA Janeiro.pdf", "DSTDA"),
    ("DeSTDA 01.2026.pdf", "DSTDA"),
    ("DIRB.pdf", "DIRB"),
]

print("=" * 60)
print("🆕 TESTE 3: NOVAS CATEGORIAS")
print("=" * 60)
new_ok = 0
new_fail = 0
for filename, expected in NEW_CATEGORY_FILES:
    result = classifier.identify_category(filename)
    status = "✅" if result == expected else "❌"
    if result == expected:
        new_ok += 1
    else:
        new_fail += 1
    print(f"  {status} | {filename} → {result} (esperado: {expected})")

print(f"\n  Resultado: {new_ok}/{len(NEW_CATEGORY_FILES)} classificadas corretamente\n")

# ==============================
# RESUMO FINAL
# ==============================
total_tests = len(BLACKLIST_FILES) + len(CATEGORY_FILES) + len(NEW_CATEGORY_FILES)
total_ok = bl_ok + cat_ok + new_ok
total_fail = bl_fail + cat_fail + new_fail

print("=" * 60)
print(f"📊 RESUMO FINAL: {total_ok}/{total_tests} testes passaram")
if total_fail > 0:
    print(f"   ⚠️ {total_fail} falhas encontradas")
else:
    print("   ✨ Todos os testes passaram!")
print("=" * 60)
