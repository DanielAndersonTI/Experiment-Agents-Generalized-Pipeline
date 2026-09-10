import sys
import traceback
from pathlib import Path

# Garante que a pasta principal esteja no sys.path
sys.path.insert(0, str(Path(__file__).parent))

from main_fewshot import executar_pipeline  # fluxo C1 - Pipeline completo com todos agentes
# ATUAL:
# Troque para executar_pipeline_c2, executar_pipeline ou executar_pipeline_c3 se quiser outra configuração.

# MUDAR PARA:
# Troque para executar_pipeline_c0, executar_pipeline_c2 ou executar_pipeline_c3 se quiser outra configuração.
system_name = "7ep"

requirements = """
- The system must allow librarian registration using username and password.
- The system must not allow registering a librarian with an already existing username.
- The system must require filling in username and password during registration.
- The system must accept only passwords considered strong enough for safe use.
- The system must reject very short passwords.
- The system must allow authenticated librarians to provide username and password to enter the system.
- The system must grant access only when username and password exactly match the existing registration.
- The system must deny access when username or password are incorrect or not provided.
- The system must handle librarian credentials securely, without depending on plain-text passwords for later validation.
- The system must respond clearly to denied access attempts, without exposing sensitive internal processing details.
- The system must maintain authentication as a separate capability, responsible for registration, login, and session validation.
- The system must allow registering books in the collection by title.
- The system must not allow duplicate registration of the same book.
- The system must allow deleting already registered books.
- The system must allow listing all registered books.
- The system must allow consulting a book by identifier.
- The system must allow consulting a book by title.
- The system must allow listing only books available for loan.
- The system must maintain the book catalog as a separate capability.
- The system must allow registering readers eligible for loans.
- The system must not allow duplicate registration of the same reader.
- The system must allow deleting already registered readers.
- The system must allow listing all registered readers.
- The system must allow consulting a reader by identifier.
- The system must allow consulting a reader by name.
- The system must maintain reader management as a separate capability.
- The system must allow registering a book loan for a registered reader.
- The system must record the loan date.
- The system must not allow loans for people not registered as readers.
- The system must not allow loans for unregistered books.
- The system must not allow loans for books already borrowed by another person.
- The system must allow the same reader to borrow multiple books at the same time.
- The system must ensure the same book is loaned to only one reader at a time.
- The system must maintain loan management as a separate capability.
- The loan capability depends on the reader management capability to validate the reader.
- The loan capability depends on the book catalog capability to validate the book.
- The system must allow clearing data and base structure to reset the environment.
- The system must allow recreating the base structure when necessary.
- The system must maintain environment management as a separate capability.
- The system must allow summing two integers informed by the user.
- The system must allow calculating Fibonacci sequence values using more than one calculation approach.
- The system must allow calculating Ackermann function results using more than one calculation approach.
- The system must maintain demo utility as a separate capability.
- The system must record main operations to support traceability and problem analysis.
- The system must maintain audit as a separate capability.
- The authentication, book catalog, reader management, and loan capabilities depend on the audit capability to record their main operations.
"""

reference_services = [
    "Authentication Service",
    "Book Catalog Service",
    "Reader Management Service",
    "Loan Management Service",
    "Environment Management Service",
    "Demo Utility Service",
    "Audit Service"
]

reference_interactions = {
    ("Authentication Service", "Audit Service"),
    ("Book Catalog Service", "Loan Management Service"),
    ("Book Catalog Service", "Audit Service"),
    ("Reader Management Service", "Loan Management Service"),
    ("Reader Management Service", "Audit Service"),
    ("Loan Management Service", "Audit Service"),
    ("Environment Management Service", "Authentication Service"),
    ("Environment Management Service", "Book Catalog Service"),
    ("Environment Management Service", "Reader Management Service"),
    ("Environment Management Service", "Loan Management Service"),
}

print("Iniciando teste do pipeline C0 com DeepSeek...")

try:
    resultados, metricas = executar_pipeline(
        system_name,
        requirements,
        reference_services,
        interaction_reference,
    )

    print("\n=== MÉTRICAS ===")
    for chave, valor in metricas.items():
        if valor is None:
            print(f"{chave}: None")
        else:
            print(f"{chave}:")
            for k, v in valor.items():
                print(f"  {k}: {v}")

    print("\n=== ARQUIVOS SALVOS ===")
    for nome, caminho in resultados.get("arquivos", {}).items():
        print(f"{nome}: {caminho}")

    print("\nTeste concluído com sucesso.")

except Exception as e:
    print("\nERRO DURANTE A EXECUÇÃO:")
    traceback.print_exc()