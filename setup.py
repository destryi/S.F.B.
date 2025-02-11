import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["os"],
    "includes": ["customtkinter",
        "sqlalchemy",
        "sqlalchemy.dialects.postgresql",
        "datetime"
    ],
    "include_files": ["imagens/consulta.png", "imagens/estoque.png", "imagens/cliente.png", "imagens/lupa.png", "imagens/attimg.png", "imagens/pedido.png","imagens/icon.ico", "imagens/carrinho.png", "imagens/fornecedor.png"]
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Consulta Agropecuaria Oliveira",
    version="0.1",
    description="versao de testes",
    options={"build_exe": build_exe_options},
    executables=[Executable("Consulta.py", base=base)]
)