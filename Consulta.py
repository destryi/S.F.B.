#Projeto Sistema de Frente de Balcão 2023
#Criadores: Emerson Oliveira e Rodolpho Santos
#início: 11/04/2023 
#linguagem python
#GUI: customTKinter
#Banco de dados: Postgresql, elephantsql


from tkinter import *
from tkinter.ttk import Notebook, Style
import customtkinter as ctk
import tkinter
from tkinter import ttk
import tkinter.messagebox
import requests
import json
from PIL import Image, ImageTk
import time
import re
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Float
from sqlalchemy import Table
from sqlalchemy import update
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_
from sqlalchemy import *
from datetime import datetime
from sqlalchemy_utils import database_exists, create_database
import psycopg2

#from sqlalchemy.dialects import postgresql

cod_fornecedor_selecionado = 0
cod_produto_selecionado = 0
cod_cliente_selecionado = 0 
cod_venda_selecionado = 0

db_params = {
    'host': 'localhost',
    'port': '5432',
    'database': 'SFB',
    'user': 'postgres',
    'password': '84450000'
}
db_url = f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{db_params["database"]}'

if not database_exists(db_url):
    # Se não existir, crie o banco de dados
    create_database(db_url)

elephant_url = "postgresql://pguiqewf:kcgDVmFQBicXwNr3onE8IcZd50aaO1pA@silly.db.elephantsql.com/pguiqewf"
cloud_engine = create_engine(elephant_url)

if not database_exists(elephant_url):
    # Se não existir, crie o banco de dados
    create_database(elephant_url)

engine = create_engine(db_url)
Base = declarative_base()
vendas_produtos = Table('vendas_produtos', Base.metadata,
    Column('CodV', Integer, ForeignKey('Vendas.CodV')),
    Column('CodP', Integer, ForeignKey('Produtos.CodP')),
    Column('Quantidade', Integer),
    Column('ValorP', String(10))   # Esse valor foi salvo como uma String, e não como chave estrangeira, afim de manter o preço inalterado, da data em que a venda ocorreu
)

class LastModified(Base):
    __tablename__ = 'last_modified'
    
    id = Column(Integer, primary_key=True)
    table_name = Column(String(255), nullable=False)
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())

class FornecedorModel(Base):
    __tablename__ = 'Fornecedores'
    CodF = Column(Integer, primary_key=True)
    RazaoSocial = Column(String(255), unique=True, nullable=False)
    UF = Column(String(2))
    Cidade = Column(String(255))
    Logradouro = Column(String(255))
    Numero = Column(Integer)
    CNPJ = Column(String(14), unique=True, nullable=False) #alterar para 17
    Telefone0 = Column(String(11), nullable=False)
    Telefone1 = Column(String(11))
    Contato = Column(String(255))
    Complemento = Column(String(255))
    IC = Column(String(9))
    Observacoes = Column(String)
    produtos = relationship('ProdutoModel', back_populates='fornecedor')
    Esconder = Column(Integer)
    Data = Column(DateTime, nullable=False)

class ProdutoModel(Base):
    __tablename__ = 'Produtos'
    CodP = Column(Integer, primary_key=True)
    Nome = Column(String(255), nullable=False)
    CodF = Column(Integer, ForeignKey('Fornecedores.CodF'))
    PrecoCompra = Column(Float, nullable=False)
    PrecoVenda = Column(Float, nullable=False)
    ICMS = Column(Float, nullable=False)
    Margem = Column(Float, nullable=False)
    PrecoAntigo = Column(Float, nullable=False)
    DataPreco = Column(DateTime, nullable=False)
    Observacoes = Column(String(150))
    fornecedor = relationship('FornecedorModel', back_populates='produtos')
    vendas = relationship('VendaModel', secondary=vendas_produtos, back_populates='produtos')
    Esconder = Column(Integer)
    Data = Column(DateTime, nullable=False)


class ClienteModel(Base):
    __tablename__ = 'Clientes'
    CodC = Column(Integer, primary_key=True)
    Nome = Column(String(255), nullable=False)
    Documento = Column(String(11),unique=True, nullable=False) #alterar para 11
    Logradouro = Column(String(100))
    Numero = Column(String(6))
    Bairro = Column(String(30))
    Telefone = Column(String(11))
    Complemento = Column(String(150))
    Observacoes = Column(String(150))
    vendas = relationship('VendaModel', back_populates='cliente')
    Esconder = Column(Integer)
    Data = Column(DateTime, nullable=False)

class VendaModel(Base):
    __tablename__ = 'Vendas'
    CodV = Column(Integer, primary_key=True)
    CodP = Column(Integer, ForeignKey('Produtos.CodP'))
    produtos = relationship('ProdutoModel', secondary=vendas_produtos, back_populates='vendas')
    Valor = Column(Float, nullable=False)
    CodC = Column(Integer, ForeignKey('Clientes.CodC'))
    cliente = relationship('ClienteModel', back_populates='vendas')
    Endereco = Column(String(255))
    Entrega = Column(Integer)
    Concluido = Column(Integer)
    Data = Column(DateTime, nullable=False)

Base.metadata.create_all(engine)
Base.metadata.create_all(cloud_engine)


ctk.set_appearance_mode("Dark")  
#começo da programação da GUI
root = ctk.CTk() #janela principal, topo da hierarquia
root.geometry("1280x720") 
root.title("Agropecuária Oliveira")
root.minsize(1280, 720)
root.maxsize(1280, 720)

#"notebook" é responsável pelas abas
style = ttk.Style()
style.theme_use('default')
style.configure('TNotebook.Tab', background="white", bordercolor="white")
style.configure('TNotebook.Tab', background="white", bordercolor="white", lightcolor="white", text_color="white")
style.map("TNotebook.Tab", background= [("selected", "white")])

# Cria o notebook usando o estilo personalizado
notebook = ttk.Notebook(root, style='CustomNotebook.TNotebook')
notebook.grid(row=0, column=1, padx=10, sticky="nsew")

#funções dos sistema

def verifica_conexao(url_conexao):
    try:
        # Tente se conectar ao banco de dados usando a URL de conexão
        conn = psycopg2.connect(url_conexao)
        # Se a conexão for bem-sucedida, há uma conexão com o banco de dados
        return True
    except psycopg2.OperationalError:
        pass
    return False




def recover_db():
    Session = sessionmaker(bind=engine)
    session = Session()
    SessionCloud = sessionmaker(bind=cloud_engine)
    session_cloud = SessionCloud()
    try:

        last_modified_local = session.query(LastModified).order_by(LastModified.modified_at.desc()).first()
        if last_modified_local is None:
            last_modified_local_date = datetime.min
        else:
            last_modified_local_date = last_modified_local.modified_at

        # Verifique a data da última modificação no banco de dados em nuvem                              
        last_modified_cloud = session_cloud.query(LastModified).order_by(LastModified.modified_at.desc()).first()
        last_modified_cloud = last_modified_cloud.modified_at
        print("A ultima atualização no cloud foi em:")
        print(last_modified_cloud)
        print("A ultima atualização local foi em:")
        print(last_modified_local_date)
      
        # Compare as datas de última modificação
        if last_modified_local_date < last_modified_cloud:
            # O banco de dados local está desatualizado
            # Copie os registros mais recentes da nuvem para o local
            

            fornecedores_cloud = session_cloud.query(FornecedorModel).filter(FornecedorModel.Data > last_modified_local_date).order_by(FornecedorModel.CodF).all()
            produtos_cloud = session_cloud.query(ProdutoModel).filter(ProdutoModel.Data > last_modified_local_date).order_by(ProdutoModel.CodP).all()
            clientes_cloud = session_cloud.query(ClienteModel).filter(ClienteModel.Data > last_modified_local_date).order_by(ClienteModel.CodC).all()
            vendas_cloud = session_cloud.query(VendaModel).filter(VendaModel.Data > last_modified_local_date).order_by(VendaModel.CodV).all()

            for fornecedor in fornecedores_cloud:
                Session = sessionmaker(bind=engine)
                session = Session()

                cod_atual = fornecedor.CodF
                already_exist = session.query(FornecedorModel).filter_by(CodF=cod_atual).first()
                if already_exist is None:
                    # Crie uma cópia do objeto local
                    fornecedor_local = FornecedorModel(
                        RazaoSocial=fornecedor.RazaoSocial,
                        #CodF=fornecedor.CodF,
                        UF=fornecedor.UF,
                        Cidade=fornecedor.Cidade,
                        Logradouro=fornecedor.Logradouro,
                        Numero=fornecedor.Numero,
                        CNPJ=fornecedor.CNPJ,
                        Telefone0=fornecedor.Telefone0,
                        Telefone1=fornecedor.Telefone1,
                        Contato=fornecedor.Contato,
                        Complemento=fornecedor.Complemento,
                        IC=fornecedor.IC,
                        Observacoes=fornecedor.Observacoes,
                        Esconder=fornecedor.Esconder,
                        Data=fornecedor.Data
                    )
                    session.add(fornecedor_local)
                    session.commit()
                else:
                    already_exist.RazaoSocial = fornecedor.RazaoSocial 
                    already_exist.UF = fornecedor.UF
                    already_exist.Cidade = fornecedor.Cidade
                    already_exist.Logradouro = fornecedor.Logradouro 
                    already_exist.Numero = fornecedor.Numero 
                    already_exist.Complemento = fornecedor.Complemento 
                    already_exist.Telefone0 = fornecedor.Telefone0 
                    already_exist.Telefone1 = fornecedor.Telefone1 
                    already_exist.Contato = fornecedor.Contato 
                    already_exist.Observacoes = fornecedor.Observacoes 
                    already_exist.CNPJ = fornecedor.CNPJ 
                    already_exist.IC = fornecedor.IC 
                    already_exist.Data = fornecedor.Data
                session.commit()
                session.close()

            for produto in produtos_cloud:
                Session = sessionmaker(bind=engine)
                session = Session()

                cod_atual = produto.CodP
                already_exist = session.query(ProdutoModel).filter_by(CodP=cod_atual).first()
                if already_exist is None:
                    # Crie uma cópia do objeto local
                    produto_local = ProdutoModel(
                        Nome=produto.Nome,
                        #CodP=produto.CodP,
                        CodF=produto.CodF,
                        PrecoCompra = produto.PrecoCompra,
                        PrecoVenda = produto.PrecoVenda,
                        ICMS = produto.ICMS,
                        Margem = produto.Margem,
                        PrecoAntigo = produto.PrecoAntigo,
                        DataPreco = produto.DataPreco,
                        Observacoes = produto.Observacoes,
                        #vendas = produto.vendas,
                        Esconder = produto.Esconder,
                        Data=produto.Data 
                    )
                    session.add(produto_local)
                    session.commit()
                else:
                    already_exist.Nome=produto.Nome
                    already_exist.CodF=produto.CodF
                    already_exist.PrecoCompra = produto.PrecoCompra
                    already_exist.PrecoVenda = produto.PrecoVenda
                    already_exist.ICMS = produto.ICMS
                    already_exist.Margem = produto.Margem
                    already_exist.PrecoAntigo = produto.PrecoAntigo
                    already_exist.DataPreco = produto.DataPreco
                    already_exist.Observacoes = produto.Observacoes
                    #already_exist.vendas = produto.vendas
                    already_exist.Esconder = produto.Esconder
                    already_exist.Data=produto.Data    
                session.commit()         
                session.close()


            for cliente in clientes_cloud:
                Session = sessionmaker(bind=engine)
                session = Session()

                cod_atual = cliente.CodC
                already_exist = session.query(ClienteModel).filter_by(CodC=cod_atual).first()
                # Crie uma cópia do objeto local
                if already_exist is None:
                    cliente_local = ClienteModel(
                        Nome=cliente.Nome,
                        #CodC=cliente.CodC,
                        Documento=cliente.Documento,
                        Logradouro=cliente.Logradouro,
                        Numero=cliente.Numero,
                        Bairro=cliente.Bairro,
                        Telefone=cliente.Telefone,
                        Complemento=cliente.Complemento,
                        Observacoes=cliente.Observacoes,
                        #vendas=cliente.vendas,
                        Esconder=cliente.Esconder,
                        Data=cliente.Data
                    )
                    session.add(cliente_local)
                else:
                    already_exist.Nome=cliente.Nome
                    already_exist.CodC=cliente.CodC
                    already_exist.Documento=cliente.Documento
                    already_exist.Logradouro=cliente.Logradouro
                    already_exist.Numero=cliente.Numero
                    already_exist.Bairro=cliente.Bairro
                    already_exist.Telefone=cliente.Telefone
                    already_exist.Complemento=cliente.Complemento
                    already_exist.Observacoes=cliente.Observacoes
                    #already_exist.vendas=cliente.vendas
                    already_exist.Esconder=cliente.Esconder
                    already_exist.Data=cliente.Data
                session.commit()         
                session.close()

            for venda in vendas_cloud:
                Session = sessionmaker(bind=engine)
                session = Session()

                cod_atual = venda.CodV
                codC = venda.CodC
                already_exist = session.query(VendaModel).filter_by(CodV=cod_atual).first()
                cliente = session.query(ClienteModel).filter_by(CodC=codC).first()

                if already_exist is None:
                    # Crie uma cópia do objeto local
                    venda_cloud = VendaModel(
                        #CodV=venda.CodV,
                        cliente=cliente,
                        Valor=venda.Valor,
                        Endereco=venda.Endereco,
                        Entrega=venda.Entrega,
                        Data=venda.Data,
                    )
                    session.add(venda_cloud)
                    
                    produtos_processados = set()
                    for produto in venda.produtos:
                        # Recupere o produto correspondente no banco de dados em nuvem
                        produto_cloud = session.query(ProdutoModel).filter_by(CodP=produto.CodP).first()
                        venda_produto = session_cloud.query(vendas_produtos).filter_by(CodV=venda_cloud.CodV, CodP=produto_cloud.CodP).first()
                        quantidade = venda_produto.Quantidade
                        if quantidade is None:
                            quantidade = 0
                        preco = venda_produto.ValorP
                        if preco is None:
                            preco = 0

                        print(produto_cloud.Nome)
                        if produto_cloud:
                            # Acesse as informações da tabela associativa vendas_produtos
                            if produto_cloud.Nome not in produtos_processados:
                                produtos_processados.add(produto_cloud.Nome)
                                for _ in range(quantidade):
                                    venda_cloud.produtos.append(produto_cloud)


                            session.add(venda_cloud)    
                            session.commit()
                            # Atualize a quantidade e o valor de venda
                            stmt = update(vendas_produtos).where(and_(vendas_produtos.c.CodP == produto_cloud.CodP, vendas_produtos.c.CodV == venda_cloud.CodV)).values(Quantidade=quantidade, ValorP=preco)
                            session.execute(stmt)
                            session.commit()
                            # Adicione o produto à venda em nuvem
                            
                        produtos_processados.add(produto_cloud)
                        
                    session.commit()

                else:
                    already_exist.Concluido = venda.Concluido
                    session.commit()
                
                session.close()

            Session = sessionmaker(bind=engine)
            session = Session()
            # Marque a data de última modificação no banco de dados em nuvem
            last_modified_local = LastModified(table_name='Produtos', modified_at=datetime.now())
            session.add(last_modified_local)

            
            # Commit as alterações no banco de dados local
            session.commit()
            session.close()

    except Exception as e:
        # Lide com erros, faça rollback se necessário
        print("Erro na recuperação do banco de dados:", e)
        session.rollback()

    finally:
        # Feche as sessões
        session.close()
        session_cloud.close()






def sync_db():
    # Crie sessões para ambos os bancos de dados
    SessionLocal = sessionmaker(bind=engine)
    SessionCloud = sessionmaker(bind=cloud_engine)
    session_local = SessionLocal()
    session_cloud = SessionCloud()

    try:
        # Verifique a data da última modificação no banco de dados em nuvem
        last_modified_cloud = session_cloud.query(LastModified).order_by(LastModified.modified_at.desc()).first()
        if last_modified_cloud is None:
            last_modified_cloud_date = datetime.min
        else:
            last_modified_cloud_date = last_modified_cloud.modified_at
        session_cloud.close()
        # Consulte objetos modificados localmente após a data do banco de dados em nuvem
        produtos_modificados_local = session_local.query(ProdutoModel).filter(ProdutoModel.Data > last_modified_cloud_date).all()
        fornecedores_modificados_local = session_local.query(FornecedorModel).filter(FornecedorModel.Data > last_modified_cloud_date).all()
        clientes_modificados_local = session_local.query(ClienteModel).filter(ClienteModel.Data > last_modified_cloud_date).all()
        vendas_modificados_local = session_local.query(VendaModel).filter(VendaModel.Data > last_modified_cloud_date).all()
         
        for fornecedor in fornecedores_modificados_local:
            SessionCloud = sessionmaker(cloud_engine)
            session_cloud = SessionCloud()
            cod_atual = fornecedor.CodF
            already_exist = session_cloud.query(FornecedorModel).filter_by(CodF=cod_atual).first()
            if already_exist is None:
                # Crie uma cópia do objeto local
                fornecedor_cloud = FornecedorModel(
                    RazaoSocial=fornecedor.RazaoSocial,
                    CodF=fornecedor.CodF,
                    UF=fornecedor.UF,
                    Cidade=fornecedor.Cidade,
                    Logradouro=fornecedor.Logradouro,
                    Numero=fornecedor.Numero,
                    CNPJ=fornecedor.CNPJ,
                    Telefone0=fornecedor.Telefone0,
                    Telefone1=fornecedor.Telefone1,
                    Contato=fornecedor.Contato,
                    Complemento=fornecedor.Complemento,
                    IC=fornecedor.IC,
                    Observacoes=fornecedor.Observacoes,
                    Esconder=fornecedor.Esconder,
                    Data=fornecedor.Data
                )
                session_cloud.add(fornecedor_cloud)
                session_cloud.commit()
            else:
                already_exist.RazaoSocial = fornecedor.RazaoSocial 
                already_exist.UF = fornecedor.UF
                already_exist.Cidade = fornecedor.Cidade
                already_exist.Logradouro = fornecedor.Logradouro 
                already_exist.Numero = fornecedor.Numero 
                already_exist.Complemento = fornecedor.Complemento 
                already_exist.Telefone0 = fornecedor.Telefone0 
                already_exist.Telefone1 = fornecedor.Telefone1 
                already_exist.Contato = fornecedor.Contato 
                already_exist.Observacoes = fornecedor.Observacoes 
                already_exist.CNPJ = fornecedor.CNPJ 
                already_exist.IC = fornecedor.IC 
                already_exist.Data = fornecedor.Data
            session_cloud.commit()
            session_cloud.close()



        #Sincronize os objetos modificados para o banco de dados em nuvem
        for produto in produtos_modificados_local:
            SessionCloud = sessionmaker(cloud_engine)
            session_cloud = SessionCloud()

            cod_atual = produto.CodP
            already_exist = session_cloud.query(ProdutoModel).filter_by(CodP=cod_atual).first()
            if already_exist is None:
                # Crie uma cópia do objeto local
                produto_cloud = ProdutoModel(
                    Nome=produto.Nome,
                    CodP=produto.CodP,
                    CodF=produto.CodF,
                    PrecoCompra = produto.PrecoCompra,
                    PrecoVenda = produto.PrecoVenda,
                    ICMS = produto.ICMS,
                    Margem = produto.Margem,
                    PrecoAntigo = produto.PrecoAntigo,
                    DataPreco = produto.DataPreco,
                    Observacoes = produto.Observacoes,
                    vendas = produto.vendas,
                    Esconder = produto.Esconder,
                    Data=produto.Data  # Copie a data de modificação
                )
                session_cloud.add(produto_cloud)
                session_cloud.commit()
            else:
                already_exist.Nome=produto.Nome
                already_exist.CodF=produto.CodF
                already_exist.PrecoCompra = produto.PrecoCompra
                already_exist.PrecoVenda = produto.PrecoVenda
                already_exist.ICMS = produto.ICMS
                already_exist.Margem = produto.Margem
                already_exist.PrecoAntigo = produto.PrecoAntigo
                already_exist.DataPreco = produto.DataPreco
                already_exist.Observacoes = produto.Observacoes
                already_exist.vendas = produto.vendas
                already_exist.Esconder = produto.Esconder
                already_exist.Data=produto.Data  # Copie a data de modificação   
            session_cloud.commit()         
            session_cloud.close()

        for cliente in clientes_modificados_local:
            SessionCloud = sessionmaker(cloud_engine)
            session_cloud = SessionCloud()

            cod_atual = cliente.CodC
            already_exist = session_cloud.query(ClienteModel).filter_by(CodC=cod_atual).first()
            # Crie uma cópia do objeto local
            if already_exist is None:
                cliente_cloud = ClienteModel(
                    Nome=cliente.Nome,
                    CodC=cliente.CodC,
                    Documento=cliente.Documento,
                    Logradouro=cliente.Logradouro,
                    Numero=cliente.Numero,
                    Bairro=cliente.Bairro,
                    Telefone=cliente.Telefone,
                    Complemento=cliente.Complemento,
                    Observacoes=cliente.Observacoes,
                    Esconder=cliente.Esconder,
                    Data=cliente.Data
                )
                session_cloud.add(cliente_cloud)
            else:
                already_exist.Nome=cliente.Nome
                already_exist.CodC=cliente.CodC
                already_exist.Documento=cliente.Documento
                already_exist.Logradouro=cliente.Logradouro
                already_exist.Numero=cliente.Numero
                already_exist.Bairro=cliente.Bairro
                already_exist.Telefone=cliente.Telefone
                already_exist.Complemento=cliente.Complemento
                already_exist.Observacoes=cliente.Observacoes
                already_exist.Esconder=cliente.Esconder
                already_exist.Data=cliente.Data
            session_cloud.commit()         
            session_cloud.close()

        for venda in vendas_modificados_local:
            SessionCloud = sessionmaker(bind=cloud_engine)
            session_cloud = SessionCloud()

            cod_atual = venda.CodV
            codC = venda.CodC
            already_exist = session_cloud.query(VendaModel).filter_by(CodV=cod_atual).first()
            cliente = session_cloud.query(ClienteModel).filter_by(CodC=codC).first()

            if already_exist is None:
                # Crie uma cópia do objeto local
                venda_cloud = VendaModel(
                    CodV=venda.CodV,
                    cliente=cliente,
                    Valor=venda.Valor,
                    Endereco=venda.Endereco,
                    Entrega=venda.Entrega,
                    Data=venda.Data,
                )
                session_cloud.add(venda_cloud)
                
                produtos_processados = set()
                for produto in venda.produtos:
                    # Recupere o produto correspondente no banco de dados em nuvem
                    produto_cloud = session_cloud.query(ProdutoModel).filter_by(CodP=produto.CodP).first()
                    venda_produto = session_local.query(vendas_produtos).filter_by(CodV=venda_cloud.CodV, CodP=produto_cloud.CodP).first()
                    quantidade = venda_produto.Quantidade
                    preco = venda_produto.ValorP
                    print(produto_cloud.Nome)
                    if produto_cloud:
                        # Acesse as informações da tabela associativa vendas_produtos
                        if produto_cloud.Nome not in produtos_processados:
                            produtos_processados.add(produto_cloud.Nome)
                            for _ in range(quantidade):
                                venda_cloud.produtos.append(produto_cloud)


                        session_cloud.add(venda_cloud)    
                        session_cloud.commit()
                        # Atualize a quantidade e o valor de venda
                        stmt = update(vendas_produtos).where(and_(vendas_produtos.c.CodP == produto_cloud.CodP, vendas_produtos.c.CodV == venda_cloud.CodV)).values(Quantidade=quantidade, ValorP=preco)
                        session_cloud.execute(stmt)
                        session_cloud.commit()
                        # Adicione o produto à venda em nuvem
                        
                    produtos_processados.add(produto_cloud)
                    
                session_cloud.commit()

            else:
                already_exist.Concluido = venda.Concluido
                session_cloud.commit()
            
            session_cloud.close()


        SessionCloud = sessionmaker(bind=cloud_engine)
        session_cloud = SessionCloud()
        # Marque a data de última modificação no banco de dados em nuvem
        last_modified_cloud = LastModified(table_name='Produtos', modified_at=datetime.now())
        session_cloud.add(last_modified_cloud)

        # Commit as alterações no banco de dados em nuvem
        session_cloud.commit()

    except Exception as e:
        # Lide com erros, faça rollback se necessário
        print("Erro na sincronização:", e)
        session_cloud.rollback()

    finally:
        # Feche as sessões
        session_local.close()
        session_cloud.close()



def tabconsulta():
    selected_label.grid(row=0, column=0, pady=(0,0), sticky="w", padx=(0,1)) 
    notebook.select(0)
    consultaBtn.configure(fg_color="#567aba", width=130)
    consultaBtn.forget()
    estoqueBtn.forget()
    clienteBtn.forget()
    fornecedorBtn.forget()
    pedidoBtn.forget()
    consultaBtn.grid(row=0, column=0, pady=(10,10), padx=0, sticky="e") 
    fornecedorBtn.configure(fg_color="#d65a60", width=120)
    fornecedorBtn.grid(row=2, column=0, pady=(0,10), padx=10, sticky="")
    estoqueBtn.configure(fg_color="#d65a60", width=120)
    estoqueBtn.grid(row=1, column=0, pady=(0,10), padx=10, sticky="")
    clienteBtn.configure(fg_color="#d65a60", width=120)
    clienteBtn.grid(row=3, column=0, pady=(0,10), padx=10, sticky="")
    pedidoBtn.configure(fg_color="#d65a60", width=120)
    pedidoBtn.grid(row=4, column=0, pady=(0,10), padx=10, sticky="")
        

def tabestoque():
    selected_label.grid(row=1, column=0, pady=(0,10), sticky="w", padx=(0,1))
    notebook.hide(0)
    notebook.select(1)
    estoqueBtn.configure(fg_color="#567aba", width=130)
    estoqueBtn.grid(row=1, column=0, pady=(0,10), padx=0, sticky="e")
    fornecedorBtn.configure(fg_color="#d65a60", width=120)
    fornecedorBtn.grid(row=2, column=0, pady=(0,10), padx=10, sticky="")
    consultaBtn.configure(fg_color="#d65a60", width=120)
    consultaBtn.grid(row=0, column=0, pady=(10,10), padx=10, sticky="")
    clienteBtn.configure(fg_color="#d65a60", width=120)
    clienteBtn.grid(row=3, column=0, pady=(0,10), padx=10, sticky="")
    pedidoBtn.configure(fg_color="#d65a60", width=120)
    pedidoBtn.grid(row=4, column=0, pady=(0,10), padx=10, sticky="")

def tabfornecedor():
    selected_label.grid(row=2, column=0, pady=(0,10), sticky="w", padx=(0,1))
    notebook.hide(0)
    notebook.hide(1)
    notebook.select(2)
    fornecedorBtn.configure(fg_color="#567aba", width=130)
    fornecedorBtn.grid(row=2, column=0, pady=(0,10), padx=0, sticky="e") 
    consultaBtn.configure(fg_color="#d65a60", width=120)
    consultaBtn.grid(row=0, column=0, pady=(10,10), padx=10, sticky="")
    estoqueBtn.configure(fg_color="#d65a60", width=120)
    estoqueBtn.grid(row=1, column=0, pady=(0,10), padx=10, sticky="")
    clienteBtn.configure(fg_color="#d65a60", width=120)
    clienteBtn.grid(row=3, column=0, pady=(0,10), padx=10, sticky="")
    pedidoBtn.configure(fg_color="#d65a60", width=120)
    pedidoBtn.grid(row=4, column=0, pady=(0,10), padx=10, sticky="")

def tabclientes(): 
    selected_label.grid(row=3, column=0, pady=(0,10), sticky="w", padx=(0,1))
    notebook.hide(0)
    notebook.hide(1)
    notebook.hide(2)
    notebook.select(3)
    clienteBtn.configure(fg_color="#567aba", width=130)
    clienteBtn.grid(row=3, column=0, pady=(0,10), padx=0, sticky="e") 
    fornecedorBtn.configure(fg_color="#d65a60", width=120)
    fornecedorBtn.grid(row=2, column=0, pady=(0,10), padx=10, sticky="")
    estoqueBtn.configure(fg_color="#d65a60", width=120)
    estoqueBtn.grid(row=1, column=0, pady=(0,10), padx=10, sticky="")
    consultaBtn.configure(fg_color="#d65a60", width=120)
    consultaBtn.grid(row=0, column=0,pady=(10,10), padx=10, sticky="")
    pedidoBtn.configure(fg_color="#d65a60", width=120)
    pedidoBtn.grid(row=4, column=0, pady=(0,10), padx=10, sticky="")

def tabpedidos(): 
    selected_label.grid(row=4, column=0, pady=(0,10), sticky="w", padx=(0,1))
    notebook.hide(0)
    notebook.hide(1)
    notebook.hide(2)
    notebook.hide(3)
    notebook.select(4)
    pedidoBtn.configure(fg_color="#567aba", width=130)
    pedidoBtn.grid(row=4, column=0, pady=(0,10), padx=0, sticky="e") 
    fornecedorBtn.configure(fg_color="#d65a60", width=120)
    fornecedorBtn.grid(row=2, column=0, pady=(0,10), padx=10, sticky="")
    estoqueBtn.configure(fg_color="#d65a60", width=120)
    estoqueBtn.grid(row=1, column=0, pady=(0,10), padx=10, sticky="")
    clienteBtn.configure(fg_color="#d65a60", width=120)
    clienteBtn.grid(row=3, column=0, pady=(0,10), padx=10, sticky="")
    consultaBtn.configure(fg_color="#d65a60", width=120)
    consultaBtn.grid(row=0, column=0, pady=(10,10), padx=10, sticky="")


def calcular_margem():
    # Obtenha os valores das entradas
    preco_custo_str = preco_custo_entry.get().replace(',', '.')  # Converter ',' para '.'
    icms_str = icms_entry.get().replace(',', '.')  # Converter ',' para '.'
    preco_venda_str = preco_venda_entry.get().replace(',', '.')

    if preco_custo_str and icms_str and preco_venda_str:
        preco_custo = float(preco_custo_str)
        icms = float(icms_str)
        preco_venda = float(preco_venda_str)
        
        # Calcular a margem
        margem = ((preco_venda / (preco_custo * (1 + (icms / 100)))) - 1) * 100

        margem_entry.delete(0, ctk.END)
        margem_entry.insert(0, f'{margem:.2f}')
    else:
       pass


def calcular_preco_venda():

    preco_custo_str = preco_custo_entry.get().replace(',', '.')  # Converter ',' para '.'
    icms_str = icms_entry.get().replace(',', '.')  # Converter ',' para '.'
    margem_str = margem_entry.get().replace(',', '.')

    if preco_custo_str and icms_str and margem_str:
        # Obtenha os valores das entradas
        preco_custo = float(preco_custo_str)  # Converter ',' para '.'
        icms = float(icms_str)  # Converter ',' para '.'
        margem = float(margem_str)  # Converter ',' para '.'

        # Calcule o preço de venda
        preco_venda = preco_custo * (1 + (icms / 100)) * (1 + (margem / 100))

        # Atualize a entrada de preço de venda
        preco_venda_entry.delete(0, ctk.END)
        preco_venda_entry.insert(0, f'{preco_venda:.2f}')  # Formate o valor com 2 casas decimais
    else:
        pass

def format_entry_dot(entry_text):
    # Substituir vírgulas por pontos em números
    entry_text = entry_text.replace(",", ".")
    
    return entry_text

def format_entry_comma(entry_text):
    # Substituir vírgulas por pontos em números
    entry_text = entry_text.replace(".", ",")
    
    return entry_text
 
def entry_precoV(event):
    preco = preco_venda_entry.get()
    preco = re.sub(r'[^\d.,]', '', preco)
    preco = format_entry_dot(preco)
    num_pontos = preco.count('.')
    # Se já houver um ponto, remove os pontos extras
    if num_pontos > 1:
        preco = preco.replace('.', '', num_pontos - 1)
    preco_venda_entry.delete(0, ctk.END)
    preco_venda_entry.insert(0, preco)

def entry_precoC(event):
    preco = preco_custo_entry.get()
    preco = re.sub(r'[^\d.,]', '', preco)
    preco = format_entry_dot(preco)
    num_pontos = preco.count('.')
    # Se já houver um ponto, remove os pontos extras
    if num_pontos > 1:
        preco = preco.replace('.', '', num_pontos - 1)
    preco_custo_entry.delete(0, ctk.END)
    preco_custo_entry.insert(0, preco)

def entry_precoA(event):
    preco = preco_antigo_entry.get()
    preco = re.sub(r'[^\d.,]', '', preco)
    preco = format_entry_dot(preco)
    num_pontos = preco.count('.')
    # Se já houver um ponto, remove os pontos extras
    if num_pontos > 1:
        preco = preco.replace('.', '', num_pontos - 1)
    preco_antigo_entry.delete(0, ctk.END)
    preco_antigo_entry.insert(0, preco)

def entry_margem(event):
    margem = margem_entry.get()
    margem = re.sub(r'[^\d.,]', '', margem)
    margem = format_entry_dot(margem)
    num_pontos = margem.count('.')
    # Se já houver um ponto, remove os pontos extras
    if num_pontos > 1:
        margem = margem.replace('.', '', num_pontos - 1)
    margem_entry.delete(0, ctk.END)
    margem_entry.insert(0, margem)

def entry_icms(event):
    icms = icms_entry.get()
    icms = re.sub(r'[^\d.,]', '', icms)
    icms = format_entry_dot(icms)
    num_pontos = icms.count('.')
    # Se já houver um ponto, remove os pontos extras
    if num_pontos > 1:
        icms = icms.replace('.', '', num_pontos - 1)
    icms_entry.delete(0, ctk.END)
    icms_entry.insert(0, icms)

def formatar_data(data):
    data = re.sub(r'\D', '', data)

    data_formatada = f"{data[:2]}/{data[2:4]}/{data[4:]}"

    return data_formatada


def format_entry_data(event):
    data = data_preco_entry.get()
    data = ''.join(filter(str.isdigit, data))

    if len(data) > 2 and len(data) <= 4:
        data = data[:2] + '/' + data[2:]
    elif len(data) > 4:
        data = data[:2] + '/' + data[2:4] + '/' + data[4:]
    data = data[:10]
    data_preco_entry.delete(0, ctk.END)
    data_preco_entry.insert(0, data)


def formatar_cnpj(cnpj):
    # Remova todos os caracteres não numéricos do CNPJ
    cnpj = re.sub(r'\D', '', cnpj)
    
    # Formate o CNPJ como 'xx.xxx.xxx/xxxx-xx'
    cnpj_formatado = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    
    return cnpj_formatado

def formatar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)

    cpf_formatado = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

    return cpf_formatado

def formatar_telefone(telefone):
    # Remova todos os caracteres não numéricos do telefone
    telefone = re.sub(r'\D', '', telefone) 

    if len(telefone) > 2 and len(telefone) <= 7:
        telefone = '(' + telefone[:2] + ') ' + telefone[2:]
    elif len(telefone) > 7:
        telefone = '(' + telefone[:2] + ') ' + telefone[2:7] + '-' + telefone[7:]
    if len(telefone) == 14:  # Telefone fixo
        telefone = ''.join(filter(str.isdigit, telefone))
        telefone = '(' + telefone[:2] + ') ' + telefone[2:6] + '-' + telefone[6:]
    
    return telefone

def format_cpf(event):
    cpf = documentoC_entry.get()
    cpf = ''.join(filter(str.isdigit, cpf))

    if len(cpf) > 3 and len(cpf) <= 6:
        cpf = cpf[:3] + '.' + cpf[3:]
    elif len(cpf) > 6 and len(cpf) <= 9:
        cpf = cpf[:3] + '.' + cpf[3:6] + '.' + cpf[6:]
    elif len(cpf) > 9:
        cpf = cpf[:3] + '.' + cpf[3:6] + '.' + cpf[6:9] + '-' + cpf[9:]
    cpf = cpf[:14]
    documentoC_entry.delete(0, ctk.END)
    documentoC_entry.insert(0, cpf)


def popularFornecedores():
    Session = sessionmaker(bind=engine)
    session = Session()
    # Consultar os fornecedores do banco de dados
    fornecedortable.delete(*fornecedortable.get_children())

    if fornecedor_excluido_checkbox.get() == 0:
        fornecedores = session.query(FornecedorModel).filter(or_(FornecedorModel.Esconder == 0, FornecedorModel.Esconder == None)).order_by(FornecedorModel.RazaoSocial).all()
    else:
        fornecedores = session.query(FornecedorModel).filter_by(Esconder=1).order_by(FornecedorModel.RazaoSocial).all()

    
    # Preencher a tabela de estoque com os dados dos fornecedores
    for fornecedor in fornecedores:
        fornecedortable.insert('', 'end', values=(
            fornecedor.CodF,
            fornecedor.RazaoSocial,
            fornecedor.Cidade,
            fornecedor.UF,
            fornecedor.Logradouro,
            fornecedor.Numero,
            formatar_telefone(fornecedor.Telefone0),
            formatar_cnpj(fornecedor.CNPJ),
            fornecedor.Observacoes
        ))
    session.close()

def popularProdutos():
    Session = sessionmaker(bind=engine)
    session = Session()
    estoquetable.delete(*estoquetable.get_children())
    if produto_excluido_checkbox.get() == 0:
        produtos = session.query(ProdutoModel).filter(or_(ProdutoModel.Esconder == 0, ProdutoModel.Esconder == None)).order_by(ProdutoModel.Nome).all()
    else:
        produtos = session.query(ProdutoModel).filter_by(Esconder=1).order_by(ProdutoModel.Nome).all()
    

    for produto in produtos:
        fornecedor = session.query(FornecedorModel).filter_by(CodF=produto.CodF).first() 
        estoquetable.insert('', 'end', values=(
            produto.CodP,
            produto.Nome,
            produto.PrecoCompra,
            produto.Margem,
            produto.PrecoVenda,
            produto.PrecoAntigo,
            fornecedor.RazaoSocial,
            produto.Observacoes        
        ))
    session.close()

def popularClientes():
    Session = sessionmaker(bind=engine)
    session = Session()
    clientetable.delete(*clientetable.get_children())

    if cliente_excluido_checkbox.get() == 0:
        clientes = session.query(ClienteModel).filter(or_(ClienteModel.Esconder == 0, ClienteModel.Esconder == None))
    else:
        clientes = session.query(ClienteModel).filter_by(Esconder=1).all()
    
    for cliente in clientes:
        clientetable.insert('', 'end', values=(
            cliente.CodC,
            cliente.Nome,
            cliente.Documento,
            cliente.Logradouro,
            cliente.Numero,
            cliente.Complemento,
            cliente.Bairro,
            cliente.Telefone,
            cliente.Observacoes
        ))
    session.close()



def popular():
    Session = sessionmaker(bind=engine)
    session = Session()
    vl.delete(*vl.get_children())
    produtos = session.query(ProdutoModel).order_by(ProdutoModel.Nome).all()

    for produto in produtos:
        fornecedor = session.query(FornecedorModel).filter_by(CodF=produto.CodF).first()
        if produto.Esconder != 1:
            vl.insert('', 'end', values=(
                produto.CodP,
                produto.Nome,
                produto.PrecoCompra,
                produto.Margem,
                produto.PrecoVenda,
                produto.PrecoAntigo,
                fornecedor.RazaoSocial       
            ))
    session.close()

def popularPedidos():
    pedidostable.delete(*pedidostable.get_children())
    # Conectar ao banco de dados
    engine = create_engine('postgresql://postgres:84450000@localhost:5432/SFB')
    
    # Criar uma sessão
    Session = sessionmaker(bind=engine)
    session = Session()
    # Obter o valor do filtro da combobox
    filtro = filtro_combobox.get()
    
    pesquisa_pedido = pesquisapedido_entry.get()
    # Converter a entrada de data para o formato correto
    data_entrada = apos_data.get()
    try:
        data_entrada_formatada = datetime.strptime(data_entrada, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        # Tratamento de erro para data inválida
        data_entrada_formatada = datetime.min.strftime('%Y-%m-%d')

    # Adicionar filtro de data máxima
    data_saida = ate_data.get()
    try:
        data_saida_formatada = datetime.strptime(data_saida, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        # Tratamento de erro para data inválida, use a data atual
        data_saida_formatada = datetime.now()

    # Consultar as informações do banco de dados com base no filtro
    if filtro == 'Data':
        vendas = session.query(VendaModel).\
            join(ClienteModel).\
            filter(
                VendaModel.Data >= data_entrada_formatada,
                VendaModel.Data <= data_saida_formatada,
                ClienteModel.Nome.ilike(f'%{pesquisa_pedido}%')  # Filtrar pelo nome do cliente
            ).order_by(VendaModel.Data).all()
    elif filtro == 'Valor':
        vendas = session.query(VendaModel).\
            join(ClienteModel).\
            filter(
                VendaModel.Data >= data_entrada_formatada,
                VendaModel.Data <= data_saida_formatada,
                ClienteModel.Nome.ilike(f'%{pesquisa_pedido}%')  # Filtrar pelo nome do cliente
            ).order_by(VendaModel.Valor).all()
    elif filtro == 'Cliente':
        vendas = session.query(VendaModel).\
            join(ClienteModel).\
            filter(
                VendaModel.Data >= data_entrada_formatada,
                VendaModel.Data <= data_saida_formatada,
                ClienteModel.Nome.ilike(f'%{pesquisa_pedido}%')  # Filtrar pelo nome do cliente
            ).order_by(VendaModel.CodC).all()
    else:
        vendas = session.query(VendaModel).\
            join(ClienteModel).\
            filter(
                ClienteModel.Nome.ilike(f'%{pesquisa_pedido}%')  # Filtrar pelo nome do cliente
            ).all()
    
    if concluido_checkbox.get() == 0:
        # Preencher a Treeview com os resultados da consulta
        for venda in vendas:
            if venda.Concluido == 1:
                concluido = "concluido"
            elif venda.Entrega != 0:
                concluido = "Aguardando Entrega"
            else:
                concluido = "Não"
                entrega = "Não"
            if venda.Entrega == 1:
                entrega = "Sim"
            else:
                entrega = "Não"

            if venda.Endereco == "":
                endereco = f"{venda.cliente.Logradouro}, {venda.cliente.Numero}"
            else:
                endereco = venda.Endereco

            pedidostable.insert('', 'end', values=(
                venda.CodV,
                venda.cliente.Nome,  
                endereco,
                venda.cliente.Telefone,  
                venda.Valor,
                entrega,
                concluido
            ))
    else:
       for venda in vendas:
            if venda.Concluido == 1:
                concluido = "concluido"
            elif venda.Entrega != 0:
                concluido = "Aguardando Entrega"
            else:
                concluido = "Não"
                entrega = "Não"
            if venda.Entrega == 1:
                entrega = "Sim"
            else:
                entrega = "Não" 
            if venda.Endereco == "":
                endereco = f"{venda.cliente.Logradouro}, {venda.cliente.Numero}"
            else:
                endereco = venda.Endereco

            if venda.Concluido == 1:
                pass      
            else:
                pedidostable.insert('', 'end', values=(
                    venda.CodV,
                    venda.cliente.Nome,  
                    endereco,
                    venda.cliente.Telefone, 
                    venda.Valor,
                    entrega,
                    concluido
                ))         

    # Fechar a sessão
    session.close()

def onReturn(event):
    Session = sessionmaker(bind=engine)
    session = Session()
    vl.delete(*vl.get_children())
    produto_nome = entry_nome.get()
    produtos = session.query(ProdutoModel).filter(ProdutoModel.Nome.ilike(f"%{produto_nome}%")).all()
    for produto in produtos:
        fornecedor = session.query(FornecedorModel).filter_by(CodF=produto.CodF).first()
        vl.insert('', 'end', values=(
            produto.CodP,
            produto.Nome,
            produto.PrecoCompra,
            produto.Margem,
            produto.PrecoVenda,
            produto.PrecoAntigo,
            fornecedor.RazaoSocial       
        ))
    session.close()

def pesquisaProduto(event):
    Session = sessionmaker(bind=engine)
    session = Session()
    estoquetable.delete(*estoquetable.get_children())
    produto_nome = pesquisa_produto.get()
    produtos = session.query(ProdutoModel).filter(ProdutoModel.Nome.ilike(f"%{produto_nome}%")).all()
    for produto in produtos:
        fornecedor = session.query(FornecedorModel).filter_by(CodF=produto.CodF).first()
        estoquetable.insert('', 'end', values=(
            produto.CodP,
            produto.Nome,
            produto.PrecoCompra,
            produto.Margem,
            produto.PrecoVenda,
            produto.PrecoAntigo,
            fornecedor.RazaoSocial,
            produto.Observacoes      
        ))
    session.close()

def pesquisaCliente(event):
    Session = sessionmaker(bind=engine)
    session = Session()
    clientetable.delete(*clientetable.get_children())
    cliente_nome = pesquisacliente_entry.get()
    clientes = session.query(ClienteModel).filter(ClienteModel.Nome.ilike(f"%{cliente_nome}%")).all()
    for cliente in clientes:
        clientetable.insert('', 'end', values=(
            cliente.CodC,
            cliente.Nome,
            cliente.Documento,
            cliente.Logradouro,
            cliente.Numero,
            cliente.Complemento,
            cliente.Bairro,
            cliente.Telefone,
            cliente.Observacoes      
        ))
    session.close()


def pesquisaFornecedor(event):
    Session = sessionmaker(bind=engine)
    session = Session()
    fornecedortable.delete(*fornecedortable.get_children())
    fornecedor_nome = pesquisafornecedor_entry.get()
    fornecedores = session.query(FornecedorModel).filter(FornecedorModel.RazaoSocial.ilike(f"%{fornecedor_nome}%")).all()
    for fornecedor in fornecedores:
        fornecedortable.insert('', 'end', values=(
            fornecedor.CodF,
            fornecedor.RazaoSocial,
            fornecedor.Cidade,
            fornecedor.UF,
            fornecedor.Logradouro,
            fornecedor.Numero,
            formatar_telefone(fornecedor.Telefone0),
            formatar_cnpj(fornecedor.CNPJ),
            fornecedor.Observacoes    
        ))
    session.close()
    

def selecionar(event):
    Session = sessionmaker(bind=engine)
    session = Session()
    item_id = vl.selection()[0]  # obtém o ID do item selecionado
    item = vl.item(item_id)  # obtém um dicionário com os valores do item selecionado
    nome_produto = item["values"][1]  # obtém o nome do produto (coluna 1)
    cod_produto = item["values"][0]
    produto = session.query(ProdutoModel).filter_by(CodP=cod_produto).first()
    preco_produto = item["values"][4]
    preco_formatado = "R$ {:.2f}".format(float(preco_produto))
    fornecedor_produto = item["values"][6]
    nomeprodutolabel.configure(text="")
    nomeprodutolabel.configure(text=nome_produto)  # atualiza a label com o nome do produto selecionado
    precoprodutolabel.configure(text=format_entry_comma(preco_formatado))
    fornecedorprodutolabel.configure(text=fornecedor_produto)
    data_atual = datetime.now()
    data_preco = produto.DataPreco
    data_preco = data_preco.strftime("%d/%m/%Y")
    dataprodutolabel.configure(text=data_preco)
    if not isinstance(data_preco, datetime):
        data_preco = datetime.strptime(data_preco, "%d/%m/%Y")
    diferenca = data_atual - data_preco
    if diferenca.days <= 180:
        texto = "O preço está atualizado"
        cor = "green"
    elif diferenca.days <= 365:
        texto = "O preço está desatualizado a mais de 6 meses"
        cor = "yellow"
    else:
        texto = "O preço está desatualizado a mais de um ano"
        cor = "red"
    dataselecionadoStatus.configure(text=texto, text_color=cor)
    session.close()

def selecionar_cliente(event):
    Session = sessionmaker(bind=engine)
    session = Session()
    global cod_cliente_selecionado
    item = clientetable.selection()[0]
    codigo = clientetable.item(item, "values")[0]
    cod_cliente_selecionado = codigo
    cliente = session.query(ClienteModel).filter_by(CodC=codigo).first()

    if cliente.Telefone is None:
        telefoneC_entry.delete(0, ctk.END)
    else:
        telefoneC_entry.delete(0, ctk.END)
        telefoneC_entry.insert(0, cliente.Telefone)
    nomeC_entry.delete(0, ctk.END)
    nomeC_entry.insert(0, cliente.Nome)
    documentoC_entry.delete(0, ctk.END)
    documentoC_entry.insert(0, formatar_cpf(cliente.Documento))
    logradouroC_entry.delete(0, ctk.END)
    logradouroC_entry.insert(0, cliente.Logradouro)
    numeroC_entry.delete(0, ctk.END)
    numeroC_entry.insert(0, cliente.Numero)
    bairroC_entry.delete(0, ctk.END)
    bairroC_entry.insert(0, cliente.Bairro)
    complementoC_entry.delete(0, ctk.END)
    complementoC_entry.insert(0, cliente.Complemento)
    observacoesC_entry.delete(0, ctk.END)
    observacoesC_entry.insert(0, cliente.Observacoes)

def deletar_produto():
    if verifica_conexao(elephant_url):
        recover_db()
    resposta = tkinter.messagebox.askquestion("Confirmação", "Deletar Produto?")

    if resposta == "yes":
        cod_produto = cod_produto_selecionado
        Session = sessionmaker(bind=engine)
        session = Session()
        
        data = datetime.now()
        produto = session.query(ProdutoModel).filter_by(CodP=cod_produto).first()
        if produto:
            produto.Esconder = 1
            produto.Data = data
            session.commit()
            popular()
            popularProdutos()
        else:
            print("produto não encontrado")
        nova_modificacao = LastModified(table_name='Produtos')
        session.add(nova_modificacao)
        session.commit()
        session.close()
        if verifica_conexao(elephant_url):
            sync_db()

def recuperar_produto():
    if verifica_conexao(elephant_url):
        recover_db()
    resposta = tkinter.messagebox.askquestion("Confirmação", "Recuperar Produto?")

    if resposta == "yes":    
        cod_produto = cod_produto_selecionado
        Session = sessionmaker(bind=engine)
        session = Session()
        
        data = datetime.now()
        produto = session.query(ProdutoModel).filter_by(CodP=cod_produto).first()
        if produto:
            produto.Esconder = 0
            produto.Data = data
            session.commit()
            popular()
            popularProdutos()
        else:
            print("produto não encontrado")
        nova_modificacao = LastModified(table_name='Produtos')
        session.add(nova_modificacao)
        session.commit()
        session.close()
        if verifica_conexao(elephant_url):
            sync_db()

def reset_fornecedores():
    estado_selecionado = "AC"
    estado_data = next((estado for estado in estados if estado['sigla'] == estado_selecionado), None)
    cidades = estado_data['cidades']
    global cod_fornecedor_selecionado
    cod_fornecedor_selecionado = 0
    razaosocial_entry.delete(0, ctk.END)
    UF_option.set("AC")
    UF_option.configure(values=estado_options)
    cidade_option.set(cidades[0])
    cidade_option.configure(values=cidades)
    logradouroF_entry.delete(0, ctk.END)
    numeroF_entry.delete(0, ctk.END)
    complementoF_entry.delete(0, ctk.END)
    telefone1_entry.delete(0, ctk.END)
    telefone2_entry.delete(0, ctk.END)
    contato_entry.delete(0, ctk.END)
    observacoesF_entry.delete(0, ctk.END)  
    cnpj_entry.delete(0, ctk.END)
    inscricao_estadual_entry.delete(0, ctk.END)


# frame lateral para os botões de troca de abas
menuFrame = ctk.CTkFrame(root, height=720, width=120, corner_radius=0)
menuFrame.grid(column=0, row=0, sticky="nsew")
lineframe = ctk.CTkFrame(menuFrame, width=120, height=4, fg_color="#d65a60")
lineframe.grid(row=6, column=0, pady=(240,20))
# botões
consultaimg = ctk.CTkImage(dark_image=Image.open("imagens/consulta.png"), size=(40,40))
consultaBtn = ctk.CTkButton(menuFrame, image=consultaimg, text="Consulta", width=130, height=80, compound="top", fg_color="#567aba", font=ctk.CTkFont(size=15, weight="bold"), text_color="black", hover=True,corner_radius=10, command=tabconsulta)
consultaBtn.grid(row=0, column=0, pady=(10,10), padx=(10,0), sticky="e")
estoqueimg = ctk.CTkImage(Image.open("imagens/estoque.png"), size=(40,40))
estoqueBtn = ctk.CTkButton(menuFrame, image=estoqueimg, text="Produtos", width=120, height=80, compound="top", fg_color="#d65a60", font=ctk.CTkFont(size=15, weight="bold"), text_color="black", hover=True, corner_radius=10, command=tabestoque)
estoqueBtn.grid(row=1, column=0, pady=(0,10))
fornecedorimg = ctk.CTkImage(Image.open("imagens/fornecedor.png"), size=(50,50))
fornecedorBtn = ctk.CTkButton(menuFrame, text="Fornecedores", image=fornecedorimg, width=120, height=80, compound="top", fg_color="#d65a60", font=ctk.CTkFont(size=14, weight="bold"), text_color="black", hover=True, corner_radius=10, command=tabfornecedor)
fornecedorBtn.grid(row=2, column=0, pady=(0,10))
clienteimg = ctk.CTkImage(Image.open("imagens/cliente.png"), size=(40,40))
clienteBtn = ctk.CTkButton(menuFrame, text="Clientes",image=clienteimg, width=120, height=80, compound="top", fg_color="#d65a60", font=ctk.CTkFont(size=15, weight="bold"), text_color="black", hover=True, corner_radius=10, command=tabclientes)
clienteBtn.grid(row=3, column=0, pady=(0,10))
pedidoimg = ctk.CTkImage(Image.open("imagens/pedido.png"), size=(40,40))
pedidoBtn = ctk.CTkButton(menuFrame, text="Pedidos",image=pedidoimg, width=120, height=80, compound="top", fg_color="#d65a60", font=ctk.CTkFont(size=15, weight="bold"), text_color="black", hover=True, corner_radius=10, command=tabpedidos)
pedidoBtn.grid(row=4, column=0, pady=(0,10))
# recoverBtn = ctk.CTkButton(menuFrame, text="Recuperar", width=120, height=80, compound="top", fg_color="#d65a60", font=ctk.CTkFont(size=15, weight="bold"), text_color="black", hover=True, corner_radius=10, command=recover_db)
# recoverBtn.grid(row=5, column=0, pady=(0,10))

selected_label = ctk.CTkLabel(menuFrame, text="", width=3, height=68, corner_radius=0, fg_color="white")
selected_label.grid(row=0, column=0, pady=(10,10), sticky="w", padx=(2,1))

caminho_icone = 'imagens/icon.ico'
root.iconbitmap(caminho_icone)



#########################################
#frame da consulta
#imagem da lupa da pesquisa
lupaimg = ctk.CTkImage(Image.open("imagens/lupa.png").resize((30,23), Image.Resampling.LANCZOS))
#frame principal da Consulta
consultarframe = ctk.CTkFrame(notebook, height=720, width=1120, corner_radius=0, border_width=2, border_color="white")
consultarframe.grid(row=0, column=0, padx=10, pady=(10,10), sticky="nsew")

#frame para borda e entrada de nome do produto
nomeframe = ctk.CTkFrame(consultarframe, height=800, width=220, border_width=2, border_color="white")
nomeframe.grid(rowspan=1, column=0, padx=15, pady=(25,0), sticky="new")
nomelabel = ctk.CTkLabel(nomeframe, text="Nome:", font=ctk.CTkFont(size=24, weight="bold"), text_color="white", image=lupaimg, compound="left")
nomelabel.grid(row=0,column=0,padx=(3,0), pady=(10, 10), sticky="n")
attimg = ctk.CTkImage(Image.open("imagens/attimg.png").resize((30,30), Image.Resampling.LANCZOS))
attbtn = ctk.CTkButton(nomeframe, image=attimg, text="", width=30, height=30, fg_color="#567aba", corner_radius=90, command=popular)
attbtn.grid(row=0, column=2, pady=(10, 10), padx=5)
#Caixa de entrada do nome do produto da pesquisa
entry_nome=ctk.CTkEntry(nomeframe, height=25,width=350,font=ctk.CTkFont(size=22, weight="bold"), placeholder_text="Pesquisar")
entry_nome.grid(row=0, column=1, padx=(5), pady=(10, 10), sticky="nsew")
entry_nome.bind("<KeyRelease>", onReturn)

#frame para a tabela de dados
ttkframe = ctk.CTkFrame(consultarframe, height=800, width=220, border_width=2, border_color="white")
ttkframe.grid(row=2, column=0, padx=15, pady=(15, 15))
#criação da tabela de dados
vl=ttk.Treeview(ttkframe, columns=('Código','Nome','Preço Custo','Margem %','Preço Venda','Preço Antigo','Fornecedor'), show='headings')
vl.column('Código',minwidth=50, width=50)
vl.column('Nome',minwidth=200, width=300)
vl.column('Preço Custo',minwidth=90, width=90)
vl.column('Margem %',minwidth=80, width=80)
vl.column('Preço Venda',minwidth=90, width=90)
vl.column('Preço Antigo',minwidth=90, width=90)
vl.column('Fornecedor',minwidth=90, width=110)
vl.heading('Código',text='Código')
vl.heading('Nome',text='Nome')
vl.heading('Preço Custo',text='Preço Custo')
vl.heading('Margem %',text='Margem %')
vl.heading('Preço Venda',text='Preço Venda')
vl.heading('Preço Antigo',text='Preço Antigo')
vl.heading('Fornecedor',text='Fornecedor')
vl.grid(row=2, column=0, padx=5, pady=(5, 5))
popular()
vl.bind("<<TreeviewSelect>>", selecionar)




preco_total = 0.0

def adicionar_item():
    global preco_total
    
    item_id = vl.selection()[0]  # obtém o ID do item selecionado
    item = vl.item(item_id)  # obtém um dicionário com os valores do item selecionado
    
    # Obtenha a quantidade do item a ser adicionado (supondo que qtdlabel seja uma variável válida)
    quantidade = int(qtdlabel.cget("text"))

    # Calcule o preço do item (supondo que o preço esteja na terceira coluna)
    preco_item = float(item["values"][4]) * quantidade
    
    # Atualize a variável global do preço total
    preco_total += preco_item
    
    # Atualize a label valortotal
    valortotal.configure(text=f'R$ {preco_total:.2f}')

    # Verifique se já existe um item com o mesmo nome em carrinhotable
    existe = False
    for child in carrinhotable.get_children():
        if carrinhotable.item(child)["values"][0] == item["values"][1]:
            existe = True
            # Atualize a quantidade e o valor do item existente
            qtd_atual = carrinhotable.item(child)["values"][1]
            carrinhotable.item(child, values=(
                item["values"][1],  # Nome do produto
                qtd_atual + quantidade,  # Quantidade atualizada
                preco_item + float(carrinhotable.item(child)["values"][2]) # Valor atualizado
            ))
            break 

    if not existe:
        carrinhotable.insert('', 'end', values=(
            item["values"][1],  # Nome do produto
            quantidade,  # Quantidade
            preco_item  # Valor do item
        ))

    reset = 1
    qtdlabel.configure(text=f"{reset:02d}")


def remover_item():
    global preco_total
    
    # Obtenha os itens selecionados na tabela do carrinho
    itens_selecionados = carrinhotable.selection()
    
    for item_id in itens_selecionados:
        item = carrinhotable.item(item_id)
        
        # Calcule o preço do item removido (supondo que o preço esteja na terceira coluna)
        preco_removido = float(item["values"][2])
        
        # Subtrai o preço do item removido da variável global do preço total
        preco_total -= preco_removido
        
        # Atualize a label valortotal
        valortotal.configure(text=f'R$ {preco_total:.2f}')
        
        # Remova o item da tabela do carrinho
        carrinhotable.delete(item_id)



def finalizar_venda():
    if not carrinhotable.get_children():
        tkinter.messagebox.showerror("Erro", "Carrinho vazio")
        return

    ctk.set_appearance_mode("Dark")
    # Create a new window for confirming the sale
    confirm_window = ctk.CTkToplevel(root)
    confirm_window.title("CONFIRMAR VENDA")
    
    # Calculate the total price based on the items in the cart
    total_price = valortotal.cget("text")
    
    # Label for displaying the total price
    total_label = ctk.CTkLabel(confirm_window, text="Valor total", font=ctk.CTkFont(size=20, weight="bold"))
    total_label.pack(pady=(15,5), padx=130)
    
    total_value_label = ctk.CTkLabel(confirm_window, text=total_price, font=ctk.CTkFont(size=30, weight="bold"), text_color="white")
    total_value_label.pack(pady=(0,10))
    
    # Label and ComboBox for selecting a customer
    customer_label = ctk.CTkLabel(confirm_window, text="Cliente", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
    customer_label.pack(pady=(0,10))

    
    Session = sessionmaker(bind=engine)
    session = Session()

    clientes_nome = []

    clientes = session.query(ClienteModel).all()
    for cliente in clientes:
        clientes_nome.append(cliente.Nome)

    def filter_clientes(event):
        filtro = customer_combobox.get().lower()  # Obtém o texto da entrada em letras minúsculas
        clientes_filtrados_nome = []
        clientes_filtrados = session.query(ClienteModel).filter(ClienteModel.Nome.ilike(f'%{filtro}%'))
        for cliente in clientes_filtrados:
            clientes_filtrados_nome.append(cliente.Nome)

        open_dropdown(clientes_filtrados_nome)

    def open_dropdown(clientes_filtrados):
        global listbox
        # Apaga a listbox anterior, se houver
        if 'listbox' in globals():
            listbox.destroy()

        # Cria uma nova listbox com os valores de 'cidades_filtradas'
        listbox = Listbox(confirm_window, width=24, height=min(7, len(clientes_filtrados)))
        for cliente in clientes_filtrados:
            listbox.insert(ctk.END, cliente)
        listbox.place(x=95,y=162)

        # A dropbox permanece não selecionada até que a tecla <down> seja pressionada
        listbox.bind('<Down>', lambda event: listbox.select_set(0))

        def cliente_enter(event):
            customer_combobox.set(listbox.get(listbox.curselection()))
            listbox.destroy()
        # Quando 'enter' é pressionado, o valor de cidade_option é alterado com o valor da cidade selecionada
        listbox.bind('<Return>', cliente_enter)

        def listbox_click(event):
            # Verifica se o clique foi dentro da Listbox
            if event.widget == listbox:
                index = listbox.nearest(event.y)
                if index >= 0:
                    listbox.select_set(index)
                    customer_combobox.set(listbox.get(index))
                    listbox.destroy()

        listbox.bind('<Button-1>', listbox_click)

        def root_click(event):
            # Verifica se o clique foi fora da Listbox ou em outro widget
            if event.widget != listbox:
                listbox.destroy()

        confirm_window.bind('<Button-1>', root_click)


    customer_combobox = ctk.CTkComboBox(confirm_window, width = 180, values=clientes_nome)
    customer_combobox.pack(pady=(0,5))
    customer_combobox.bind("<KeyRelease>", filter_clientes)
    customer_combobox.bind('<Down>', lambda event: listbox.focus_set())
    customer_combobox.bind('<Down>', lambda event: listbox.select_set(0))

    # Checkbox for delivery option
    delivery_checkbox = ctk.CTkCheckBox(confirm_window, text="Entrega?")
    delivery_checkbox.pack()
    
    # Label and Entry for entering the address
    address_label = ctk.CTkLabel(confirm_window, text="Endereço", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
    address_label.pack(pady=(15,5))
    
    address_entry = ctk.CTkEntry(confirm_window)
    address_entry.pack(pady=(5,10))

    def nova_venda():
        if verifica_conexao(elephant_url):
            recover_db()
        if not carrinhotable.get_children():
            tkinter.messagebox.showerror("Erro", "Carrinho vazio")
            return
        resposta = tkinter.messagebox.askquestion("Confirmação", "Finalizar Venda?")

        if resposta == "yes":
            # Get the selected customer name from the combobox
            customer_name = customer_combobox.get()
        
            # Get the delivery value from the checkbox
            entrega = 1 if delivery_checkbox.get() else 0
        
            # Get the address from the entry widget
            endereco = address_entry.get()
            endereco = endereco[:255]
        
            # Create a new session
            Session = sessionmaker(bind=engine)
            session = Session()
        
            # Get the customer object from the database
            cliente = session.query(ClienteModel).filter(ClienteModel.Nome == customer_name).first()
            if not cliente:
                tkinter.messagebox.showerror(title="Erro", message="Cliente não encontrado")
                return
            data = datetime.now()
            # Create a new VendaModel object
            venda = VendaModel(
                Valor=preco_total,
                cliente=cliente,
                Endereco=endereco,
                Entrega=entrega,
                Data=data
            )
            session.add(venda)
            produtos_processados = set()
            # Add the products to the VendaModel object
            for row in carrinhotable.get_children():
                values = carrinhotable.item(row, 'values')
                product_name = values[0]
                quantity = int(values[1]) 

                if product_name not in produtos_processados:
                    produtos_processados.add(product_name)  # Adicione o produto ao conjunto de produtos processados

                    # Get the product from the database
                    produto = session.query(ProdutoModel).filter(ProdutoModel.Nome == product_name).first()
                    precop = produto.PrecoVenda
                    # Check if a matching product was found
                    if produto:
                        # Adicione o produto à venda
                        for _ in range(quantity):
                            venda.produtos.append(produto)
                    else:
                        # Handle the case where the product was not found (e.g., log an error or display a message)
                        print(f"Product '{product_name}' not found in the database.")

                # Adicione o objeto VendaModel à sessão e faça o commit
                session.add(venda)
                session.commit()

                # # Add the VendaModel object to the session and commit
                stmt = update(vendas_produtos).where(and_(vendas_produtos.c.CodP == produto.CodP, vendas_produtos.c.CodV == venda.CodV)).values(Quantidade=quantity, ValorP=precop)
                # Execute a operação de atualização
                session.execute(stmt)
                session.commit()
            esvaziar_carrinho()
            nova_modificacao = LastModified(table_name='Pedidos')
            session.add(nova_modificacao)
            session.commit()
            session.close()
            popularPedidos()
            if verifica_conexao(elephant_url):
                sync_db()
            confirm_window.destroy()
    confirm_button = ctk.CTkButton(confirm_window, text="Confirmar", command=nova_venda)
    confirm_button.pack(pady=(0,15))
    
    # Start the main loop for the confirmation window
    confirm_window.mainloop()

def concluir_venda():
    if verifica_conexao(elephant_url):
        recover_db()
    global cod_venda_selecionado
    cod_venda = cod_venda_selecionado
    Session = sessionmaker(bind=engine)
    session = Session()
    
    venda = session.query(VendaModel).filter_by(CodV=cod_venda).first()
    if venda:
        venda.Concluido = 1
        session.commit()
    cod_venda_selecionado = 0
    session.close()
    popularPedidos()
    sync_db()


#labels e frame para exibir o nome do produto selecionado
produtoselecionadolabel = ctk.CTkLabel(consultarframe, text="Produto:", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
produtoselecionadolabel.grid(row=3, column=0, padx=(15,15), pady=(3,0), sticky="w")
produtoselecionadoframe = ctk.CTkFrame(consultarframe, height=50, width=220, border_width=2, border_color="white")
produtoselecionadoframe.grid(row=4, column=0, padx=25, pady=(2,0), sticky="nsew")
nomeprodutolabel = ctk.CTkLabel(produtoselecionadoframe, text="", font=ctk.CTkFont(size=34, weight="bold"), text_color="white")
nomeprodutolabel.grid(row=0, column=0, padx=15, pady=(5,5))

#labels e frame para exibir o preço do produto selecionado
precoselecionadolabel = ctk.CTkLabel(consultarframe, text="Preço:", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
precoselecionadolabel.grid(row=5, column=0, padx=(15,15), pady=(3,0), sticky="w")
precoselecionadoframe = ctk.CTkFrame(consultarframe, height=50, width=300, border_width=2, border_color="white")
precoselecionadoframe.grid(row=6, column=0, padx=25, pady=(2,0), sticky="nws")
precoprodutomask = ctk.CTkLabel(precoselecionadoframe, text="                     ", font=ctk.CTkFont(size=42, weight="bold"), text_color="white")
precoprodutomask.grid(row=0, column=0, padx=15, pady=(5,5))
precoprodutolabel = ctk.CTkLabel(precoselecionadoframe, text="            ", font=ctk.CTkFont(size=42, weight="bold"), text_color="white")
precoprodutolabel.grid(row=0, column=0, padx=15, pady=(5,5), sticky="w")


#labels e frame para exibir o fornecedor do produto selecionado
fornecedorselecionadolabel = ctk.CTkLabel(consultarframe, text="Fornecedor:", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
fornecedorselecionadolabel.grid(row=7, column=0, padx=(15,15), pady=(3,0), sticky="w")
fornecedorselecionadoframe = ctk.CTkFrame(consultarframe, height=50, width=300, border_width=2, border_color="white")
fornecedorselecionadoframe.grid(row=8, column=0, padx=25, pady=(2,0), sticky="we")
fornecedorprodutolabel = ctk.CTkLabel(fornecedorselecionadoframe, text="            ", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
fornecedorprodutolabel.grid(row=0, column=0, padx=15, pady=(5,5))

#labels e frame para exibir a data do preço do produto selecionado
dataselecionadolabel = ctk.CTkLabel(consultarframe, text="Data Preço:", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
dataselecionadolabel.grid(row=5, columnspan=1, padx=(315,15), pady=(3,0), sticky="w")
dataselecionadoframe = ctk.CTkFrame(consultarframe, height=50, width=300, border_width=2, border_color="white")
dataselecionadoframe.grid(row=6, columnspan=1, padx=(330, 10), pady=(2,0), sticky="wns")
dataprodutolabel = ctk.CTkLabel(dataselecionadoframe, text="01/01/0000", font=ctk.CTkFont(size=42, weight="bold"), text_color="white")
dataprodutolabel.grid(row=0, column=0, padx=15, pady=(5,5))

#labels e frame para exibir a se a data do preço está atualizada
dataselecionadoStatuslabel = ctk.CTkLabel(consultarframe, text="Status do Preço:", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
dataselecionadoStatuslabel.grid(row=9, column=0, padx=(15,15), pady=(3,0), sticky="w")
dataselecionadoStatusframe = ctk.CTkFrame(consultarframe, height=50, width=300, border_width=2, border_color="white")
dataselecionadoStatusframe.grid(row=10, column=0, padx=25, pady=(2,0), sticky="we")
dataselecionadoStatus = ctk.CTkLabel(dataselecionadoStatusframe, text="            ", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
dataselecionadoStatus.grid(row=0, column=0, padx=15, pady=(5,5))

#labels, frame, botões do carrinho de vendas
carrinhoimg = ctk.CTkImage(Image.open("imagens/carrinho.png"),size=(80,80))
carrinhoimglabel = ctk.CTkLabel(consultarframe, image=carrinhoimg,height=70, width=70,compound="top", text="")
carrinhoimglabel.grid(row=0, column=1, columnspan=2, padx=0, pady=(10,5),sticky="ne")
carrinholabel = ctk.CTkLabel(consultarframe, text="Carrinho", font=ctk.CTkFont(size=38, weight="bold"), text_color="white")
carrinholabel.grid(row=0, column=1, padx=15, pady=(10,5),sticky="w")
carrinhoframe = ctk.CTkFrame(consultarframe, height=200, width=220, border_width=2, border_color="white")
carrinhoframe.grid(row=2, column=1, padx=15, pady=(5, 5))


carrinhotable=ttk.Treeview(carrinhoframe, columns=('Produto','Qtd','Valor'), show='headings')
carrinhotable.column('Produto',minwidth=100, width=100)
carrinhotable.column('Qtd',minwidth=30, width=30)
carrinhotable.column('Valor',minwidth=70, width=70)
carrinhotable.heading('Produto',text='Produto')
carrinhotable.heading('Qtd',text='Qtd')
carrinhotable.heading('Valor',text='Valor')
carrinhotable.grid(row=2, columnspan=2, padx=5, pady=(5, 5))


def aumentar_quantidade():
    quantidade_atual = int(qtdlabel.cget("text"))
    quantidade_atual += 1
    qtdlabel.configure(text=f"{quantidade_atual:03d}")

def diminuir_quantidade():
    quantidade_atual = int(qtdlabel.cget("text"))
    if quantidade_atual > 1:
        quantidade_atual -= 1
        qtdlabel.configure(text=f"{quantidade_atual:03d}")

def aumentar10_quantidade():
    quantidade_atual = int(qtdlabel.cget("text"))
    quantidade_atual += 10
    qtdlabel.configure(text=f"{quantidade_atual:03d}")

def diminuir10_quantidade():
    quantidade_atual = int(qtdlabel.cget("text"))
    if quantidade_atual > 11:
        quantidade_atual -= 10
        qtdlabel.configure(text=f"{quantidade_atual:03d}")
    else:
        quantidade_atual = 1
        qtdlabel.configure(text=f"{quantidade_atual:03d}")

def esvaziar_carrinho():
    global preco_total
    preco_total = 0.0
    carrinhotable.delete(*carrinhotable.get_children())
    valortotal.configure(text=f'R$ {preco_total:.2f}')


qtdframe = ctk.CTkFrame(consultarframe, height=50, width=60, border_width=2, border_color="white")
qtdframe.grid(row=6, columnspan=2, padx=(687, 0), pady=(2,0), sticky="wn")
qtdlabel = ctk.CTkLabel(qtdframe,text="001",font=ctk.CTkFont(size=29, weight="bold"),text_color="white")
qtdlabel.pack(padx=3, pady=3)

botaomenos = ctk.CTkButton(consultarframe, text="-", width=30, height=20, font=ctk.CTkFont(size=24, weight="bold"),text_color="white")
botaomenos.grid(row=6, columnspan=2, padx=(650, 0), pady=(2,30), sticky="w")

botaomais = ctk.CTkButton(consultarframe, text="+",width=30, height=20, font=ctk.CTkFont(size=24, weight="bold"),text_color="white")
botaomais.grid(row=6, columnspan=2, padx=(750, 5), pady=(2,30), sticky="w")

botaomenos10 = ctk.CTkButton(consultarframe, text="--", width=30, height=20, font=ctk.CTkFont(size=24, weight="bold"),text_color="white")
botaomenos10.grid(row=6, columnspan=2, padx=(615, 0), pady=(2,30), sticky="w")

botaomais10 = ctk.CTkButton(consultarframe, text="++",width=30, height=20, font=ctk.CTkFont(size=24, weight="bold"),text_color="white")
botaomais10.grid(row=6, columnspan=2, padx=(785, 5), pady=(2,30), sticky="w")

botaoadd = ctk.CTkButton(consultarframe, text="adicionar", width=60, height=30, font=ctk.CTkFont(size=14, weight="bold"),text_color="white")
botaoadd.grid(row=6,rowspan=2, columnspan=2, padx=(675, 5), pady=(20,0), sticky="w")

botaoremover = ctk.CTkButton(consultarframe, text="Remover Item", width=30, height=20, font=ctk.CTkFont(size=24, weight="bold"),text_color="white")
botaoremover.grid(row=2,rowspan=3, column=1, padx=(0, 0), pady=(247,0), sticky="n")

botaoremover.configure(command=remover_item)
botaoadd.configure(command=adicionar_item)
botaomais.configure(command=aumentar_quantidade)
botaomenos.configure(command=diminuir_quantidade)
botaomais10.configure(command=aumentar10_quantidade)
botaomenos10.configure(command=diminuir10_quantidade)

totallabel = ctk.CTkLabel(consultarframe, text="Total:", font=ctk.CTkFont(size=36, weight="bold"), text_color="white")
totallabel.grid(row=4, column=1, padx=5, pady=(10,5),sticky="sw")
valortotal = ctk.CTkLabel(consultarframe, text="R$ 0000,00", font=ctk.CTkFont(size=38, weight="bold"), text_color="white")
valortotal.grid(row=5, rowspan=6, column=1, padx=5, pady=(5,5),sticky="ne") 

botao_finalizar_compra = ctk.CTkButton(consultarframe, text="Finalizar venda", width=30, height=20, font=ctk.CTkFont(size=24, weight="bold"),text_color="white")
botao_finalizar_compra.grid(row=6,rowspan=7, column=1, padx=(0, 0), pady=(0,30))
botao_finalizar_compra.configure(command=finalizar_venda)

botao_limpar_carrinho = ctk.CTkButton(consultarframe, text="Esvaziar carrinho", width=30, height=20, font=ctk.CTkFont(size=18, weight="bold"),text_color="white")
botao_limpar_carrinho.grid(row=7,rowspan=8, column=1, padx=(0, 0), pady=(10,10))
botao_limpar_carrinho.configure(command=esvaziar_carrinho)



def adicionar_produto():
    if verifica_conexao(elephant_url):
        recover_db()
    resposta = tkinter.messagebox.askquestion("Confirmação", "Adicionar novo Produto?")

    if resposta == "yes":
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            fornecedor_nome = fornecedor_option.get()
            fornecedor = session.query(FornecedorModel).filter_by(RazaoSocial=fornecedor_nome).first()
            
            if fornecedor is None:
                raise ValueError("Fornecedor não encontrado")

            nome_produto = nomeP_entry.get()
            if not nome_produto:
                raise ValueError("O campo Nome do Produto é obrigatório")
            nome_produto = nome_produto[:255]

            preco_compra = preco_custo_entry.get()
            if not preco_compra:
                raise ValueError("O campo Preço de Compra é obrigatório")
            else:
                float(preco_compra)

            preco_venda = preco_venda_entry.get()
            if not preco_venda:
                raise ValueError("O campo Preço de Venda é obrigatório")
            else:
                float(preco_venda)

            icms = icms_entry.get()
            if not icms:
                raise ValueError("O campo ICMS é obrigatório")
            else:
                float(icms)

            margem = margem_entry.get()
            if not margem:
                raise ValueError("O campo Margem é obrigatório")
            else:
                float(margem)

            preco_antigo = preco_antigo_entry.get()
            if not preco_antigo:
                raise ValueError("O campo Preço Antigo é obrigatório")
            else:
                float(preco_antigo)

            data_preco_str = data_preco_entry.get()
            try:
                data_preco = datetime.strptime(data_preco_str, "%d/%m/%Y")
            except ValueError:
                raise ValueError("Data inválida. Use o formato dd/mm/yyyy")

            data = datetime.now()

            observacoes = observacoesP_entry.get()
            observacoes = observacoes[:150]

            novo_produto = ProdutoModel(
                Nome=nome_produto,
                CodF=fornecedor.CodF,
                PrecoCompra=preco_compra,
                PrecoVenda=preco_venda,
                ICMS=icms,
                Margem=margem,
                PrecoAntigo=preco_antigo,
                DataPreco=data_preco,
                Observacoes=observacoes,
                Data = data
            )

            session.add(novo_produto)
            session.commit()
            popularProdutos()
            popular()
            global cod_produto_selecionado
            cod_produto_selecionado = novo_produto.CodP    
        except Exception as e:
            tkinter.messagebox.showerror("Erro", str(e))
        nova_modificacao = LastModified(table_name='Produtos')
        session.add(nova_modificacao)
        session.commit()
        session.close()
        if verifica_conexao(elephant_url):
            sync_db()

def alterar_produto():
    if verifica_conexao(elephant_url):
        recover_db()
    resposta = tkinter.messagebox.askquestion("Confirmação", "Alterar Produto?")

    if resposta == "yes":    
        Session = sessionmaker(bind=engine)
        session = Session()
        produto = session.query(ProdutoModel).filter_by(CodP=cod_produto_selecionado).first()
        fornecedor = session.query(FornecedorModel).filter_by(RazaoSocial= fornecedor_option.get()).first()
        data_preco = datetime.strptime(data_preco_entry.get(), "%d/%m/%Y")
        data_atual = datetime.now()
        data_produto_atual = data_atual.strftime('%d/%m/%Y')
        try:
            fornecedor_nome = fornecedor_option.get()
            fornecedor = session.query(FornecedorModel).filter_by(RazaoSocial=fornecedor_nome).first()
            
            if fornecedor is None:
                raise ValueError("Fornecedor não encontrado")

            nome_produto = nomeP_entry.get()
            if not nome_produto:
                raise ValueError("O campo Nome do Produto é obrigatório")
            nome_produto = nome_produto[:255]

            preco_compra = preco_custo_entry.get()
            if not preco_compra:
                raise ValueError("O campo Preço de Compra é obrigatório")

            preco_venda = preco_venda_entry.get()
            if not preco_venda:
                raise ValueError("O campo Preço de Venda é obrigatório")

            icms = icms_entry.get()
            if not icms:
                raise ValueError("O campo ICMS é obrigatório")

            margem = margem_entry.get()
            if not margem:
                raise ValueError("O campo Margem é obrigatório")

            preco_antigo = preco_antigo_entry.get()
            if not preco_antigo:
                raise ValueError("O campo Preço Antigo é obrigatório")

            data_preco_str = data_preco_entry.get()
            try:
                data_preco_str = datetime.strptime(data_preco_str, "%d/%m/%Y")
            except ValueError:
                raise ValueError("Data inválida. Use o formato dd/mm/yyyy")
            
            if (produto.PrecoVenda != preco_venda_entry.get()) and (produto.CodF == fornecedor.CodF):
                produto.PrecoAntigo = produto.PrecoVenda
                produto.Nome = nomeP_entry.get()
                produto.PrecoCompra = preco_custo_entry.get()
                produto.PrecoVenda = preco_venda_entry.get()
                produto.Observacoes = observacoesP_entry.get()
                produto.DataPreco = data_produto_atual
                produto.ICMS = icms_entry.get()
                produto.Margem = margem_entry.get()
                produto.Data = data_atual
                # Commit da transação
                session.commit()
                popularProdutos()
            elif (produto.PrecoVenda != preco_venda_entry.get()) and (produto.CodF != fornecedor.CodF):
                # Atualize os campos do fornecedor com os novos valores
                produto.Nome = nomeP_entry.get()
                produto.PrecoAntigo = produto.PrecoVenda
                produto.CodF = fornecedor.CodF
                produto.PrecoCompra = preco_custo_entry.get()
                produto.PrecoVenda = preco_venda_entry.get()
                produto.Observacoes = observacoesP_entry.get()
                produto.DataPreco = data_produto_atual
                produto.ICMS = icms_entry.get()
                produto.Margem = margem_entry.get()
                produto.Data = data_atual
                # Commit da transação
                session.commit()
                popularProdutos()
            elif (produto.PrecoVenda == preco_venda_entry.get()) and (produto.CodF != fornecedor.CodF):
                produto.Nome = nomeP_entry.get()
                produto.PrecoAntigo = preco_antigo_entry.get()
                produto.CodF = fornecedor.CodF
                produto.PrecoCompra = preco_custo_entry.get()
                produto.Observacoes = observacoesP_entry.get()
                produto.DataPreco = data_preco_str
                produto.ICMS = icms_entry.get()
                produto.Margem = margem_entry.get()
                produto.Data = data_atual
                # Commit da transação
                session.commit()
                popularProdutos()
            else:
                produto.Nome = nomeP_entry.get()
                produto.PrecoAntigo = preco_antigo_entry.get()
                produto.PrecoCompra = preco_custo_entry.get()
                produto.Observacoes = observacoesP_entry.get()
                produto.DataPreco = data_preco_str
                produto.ICMS = icms_entry.get()
                produto.Margem = margem_entry.get()
                produto.Data = data_atual
                # Commit da transação
                session.commit()
                popularProdutos()
        except Exception as e:
            tkinter.messagebox.showerror("Erro", str(e))
        nova_modificacao = LastModified(table_name='Produtos')
        session.add(nova_modificacao)
        session.commit()
        session.close()
        popular()
        if verifica_conexao(elephant_url):
            sync_db()

def combo_fornecedores():
    engine = create_engine('postgresql://postgres:84450000@localhost:5432/SFB')
    Session = sessionmaker(bind=engine)
    session = Session()
    fornecedores = session.query(FornecedorModel).filter(or_(FornecedorModel.Esconder == 0, FornecedorModel.Esconder == None)).all()
    fornecedor_option['values'] = [f.RazaoSocial for f in fornecedores]
    fornecedores_nome = [f.RazaoSocial for f in fornecedores]
    fornecedor_option.set("")
    fornecedor_option.configure(values = fornecedores_nome)
    session.close()

def filter_fornecedores(event):
    # Obtenha o texto digitado na ComboBox
    text= fornecedor_option.get()

    # Consulte o banco de dados para obter os fornecedores que correspondem ao texto digitado
    engine = create_engine('postgresql://postgres:84450000@localhost:5432/SFB')
    Session = sessionmaker(bind=engine)
    session = Session()
    query = session.query(FornecedorModel).filter(FornecedorModel.RazaoSocial.ilike(f'%{text}%'))
    fornecedor_option['values'] = [f.RazaoSocial for f in query.all()]
    fornecedores = [f.RazaoSocial for f in query.all()]
    fornecedor_option.configure(values = fornecedores)
    session.close()

# Frame do estoque fg_color="#1f1e21"
estoqueframe = ctk.CTkFrame(notebook, height=700, width=1120, corner_radius=0, border_width=2, border_color="white")
estoqueframe.grid(row=0, column=0, padx=10, pady=(10,10), sticky="wnse")

# Label "cadastro de produtos"
cadastroTituloframe = ctk.CTkFrame(estoqueframe, height=70, width=250, border_width=2, border_color="white")
cadastroTituloframe.grid(row=0, columnspan=2, padx=15, pady=(10,0), sticky="we") 
cadastro_label = ctk.CTkLabel(cadastroTituloframe, text="Cadastro de Produtos", font=ctk.CTkFont(size=30, weight="bold"), text_color="white")
cadastro_label.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="W")

pesquisalabel = ctk.CTkLabel(cadastroTituloframe, text="", font=ctk.CTkFont(size=24, weight="bold"), text_color="white", image=lupaimg, compound="left")
pesquisalabel.grid(row=0,columnspan=1,padx=(350,0), pady=(10, 10), sticky="w")
pesquisa_produto = ctk.CTkEntry(cadastroTituloframe, height=35, width=450, font=ctk.CTkFont(size=18), placeholder_text="Pesquisar")
pesquisa_produto.grid(row=0, columnspan=2, padx=(375,10), pady=(5,0), sticky="w")
pesquisa_produto.bind("<KeyRelease>", pesquisaProduto)

produto_excluido_checkbox = ctk.CTkCheckBox(cadastroTituloframe, text="Mostrar Excluídos",font=ctk.CTkFont(size=20), command=popularProdutos)
produto_excluido_checkbox.grid(row=0, column= 2, columnspan=2, padx=5, pady=(5, 0),sticky="w")



# cadastro frame
cadastroframe = ctk.CTkFrame(estoqueframe, height=530, width=600, border_width=2, border_color="white")
cadastroframe.grid(row=1, column=0, padx=15, pady=(10,0), sticky="we") 

# botões frame
botoesframe = ctk.CTkFrame(estoqueframe, height=380, width=250, border_width=2, border_color="white")
botoesframe.grid(row=1, column=1, padx=15, pady=(10,0), sticky="w") 

#botão "Recuperar"
botao_recuperar = ctk.CTkButton(botoesframe, text="Recuperar", font=ctk.CTkFont(size=18), fg_color="#567aba", width=230, height=82)
botao_recuperar.grid(row=3, column=0, padx=10, pady=(0,10), sticky="w")
botao_recuperar.configure(command=recuperar_produto)

# Botão "Adicionar"
botao_adicionar = ctk.CTkButton(botoesframe, text="Adicionar", font=ctk.CTkFont(size=18), fg_color="#567aba", width=230, height=82)
botao_adicionar.grid(row=0, column=0, padx=10, pady=10, sticky="w")
botao_adicionar.configure(command=adicionar_produto)

# Botão "Alterar"
botao_alterar = ctk.CTkButton(botoesframe, text="Alterar", font=ctk.CTkFont(size=18), fg_color="#567aba", width=230, height=82)
botao_alterar.grid(row=1, column=0, padx=10, pady=0, sticky="w")
botao_alterar.configure(command=alterar_produto)

# Botão "Excluir"
botao_excluir = ctk.CTkButton(botoesframe, text="Excluir", font=ctk.CTkFont(size=18), fg_color="#567aba", width=230, height=82)
botao_excluir.grid(row=2, column=0, padx=10, pady=10, sticky="w")
botao_excluir.configure(command=deletar_produto)

# Label e Entry para Nome
nome_label = ctk.CTkLabel(cadastroframe, text="Nome*:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
nome_label.grid(row=1, column=0, padx=15, pady=(5, 0), sticky="w")
nomeP_entry = ctk.CTkEntry(cadastroframe, height=25, width=600, font=ctk.CTkFont(size=18))
nomeP_entry.grid(row=2, columnspan=6, padx=(25,15), pady=(5, 0), sticky="we")

# Label e Entry para Fornecedor
fornecedor_label = ctk.CTkLabel(cadastroframe, text="Fornecedor*:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
fornecedor_label.grid(row=3, column=0, padx=15, pady=(5, 0), sticky="w")
fornecedor_option = ctk.CTkComboBox(cadastroframe, height=25, width=600, font=ctk.CTkFont(size=18))
fornecedor_option.grid(row=4, columnspan=6, padx=(25,15), pady=(5, 0), sticky="we")
combo_fornecedores()

# Associe a variável à ComboBox
fornecedor_option.bind("<KeyRelease>", filter_fornecedores)

# Labels e Entries para Preço de Custo, ICMS, Margem, Preço de Venda e Preço Antigo
preco_custo_label = ctk.CTkLabel(cadastroframe, text="Preço de Custo*:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
preco_custo_label.grid(row=5, column=0, padx=15, pady=(5, 0), sticky="w")
preco_custo_entry = ctk.CTkEntry(cadastroframe, height=25, width=145, font=ctk.CTkFont(size=18))
preco_custo_entry.grid(row=6, column=0, padx=25, pady=(5, 0), sticky="w")
preco_custo_entry.bind("<KeyRelease>", entry_precoC)

icms_label = ctk.CTkLabel(cadastroframe, text="ICMS*:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
icms_label.grid(row=5, columnspan=1, padx=175, pady=(5, 0), sticky="w")
icms_entry = ctk.CTkEntry(cadastroframe, height=25, width=80, font=ctk.CTkFont(size=18))
icms_entry.grid(row=6, columnspan=1, padx=190, pady=(5, 0), sticky="w")
icms_entry.bind("<KeyRelease>", entry_icms)

margem_label = ctk.CTkLabel(cadastroframe, text="Margem*:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
margem_label.grid(row=5, columnspan=2, padx=285, pady=(5, 0), sticky="w")
margem_entry = ctk.CTkEntry(cadastroframe, height=25, width=80, font=ctk.CTkFont(size=18))
margem_entry.grid(row=6, columnspan=2, padx=300, pady=(5, 0), sticky="w")
margem_entry.bind("<KeyRelease>", entry_margem)

preco_venda_label = ctk.CTkLabel(cadastroframe, text="Preço de Venda*:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
preco_venda_label.grid(row=5, columnspan=1, padx=(400,0), pady=(5, 0), sticky="w")
preco_venda_entry = ctk.CTkEntry(cadastroframe, height=25, width=145, font=ctk.CTkFont(size=18))
preco_venda_entry.grid(row=6, columnspan=1, padx=(415,0), pady=(5, 0), sticky="w")
preco_venda_entry.bind("<KeyRelease>", entry_precoV)

preco_antigo_label = ctk.CTkLabel(cadastroframe, text="Preço Antigo*:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
preco_antigo_label.grid(row=5, columnspan=1, padx=(570,0), pady=(5, 0), sticky="w")
preco_antigo_entry = ctk.CTkEntry(cadastroframe, height=25, width=145, font=ctk.CTkFont(size=18))
preco_antigo_entry.grid(row=6, columnspan=1, padx=(585,15), pady=(5, 0), sticky="w")
preco_antigo_entry.bind("<KeyRelease>", entry_precoA)

# Labels e Entry para Observações e Data de Preço
observacoes_label = ctk.CTkLabel(cadastroframe, text="Observações:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
observacoes_label.grid(row=7, column=0, padx=15, pady=(5, 0), sticky="w")
observacoesP_entry = ctk.CTkEntry(cadastroframe, height=65, width=600, font=ctk.CTkFont(size=18))
observacoesP_entry.grid(row=8, columnspan=6, padx=(25,15), pady=(5, 0), sticky="we")

data_preco_label = ctk.CTkLabel(cadastroframe, text="Data de Preço*:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
data_preco_label.grid(row=9, column=0, padx=15, pady=(5, 0), sticky="w")
data_preco_entry = ctk.CTkEntry(cadastroframe, height=25, width=160, font=ctk.CTkFont(size=18))
data_preco_entry.grid(row=10, column=0, padx=25, pady=(5, 10), sticky="w")
data_preco_entry.bind("<KeyRelease>", format_entry_data)

preco_custo_entry.bind("<KeyRelease>", lambda event: (entry_precoC(event), calcular_preco_venda()))
icms_entry.bind("<KeyRelease>", lambda event: (entry_icms(event), calcular_preco_venda()))
margem_entry.bind("<KeyRelease>", lambda event: (entry_margem(event), calcular_preco_venda()))
preco_venda_entry.bind("<KeyRelease>", lambda event: (entry_precoV(event), calcular_margem()))


def duplo_click(event):
    item = estoquetable.selection()[0]  # Obtém o item selecionado
    codigo = estoquetable.item(item, "values")[0]  # Obtém o valor da coluna "Código" do item
    global cod_produto_selecionado
    cod_produto_selecionado = estoquetable.item(item, "values")[0]
    # Consulta o banco de dados para obter os dados do fornecedor
    engine = create_engine('postgresql://postgres:84450000@localhost:5432/SFB')
    Session = sessionmaker(bind=engine)
    session = Session()

    produto = session.query(ProdutoModel).filter_by(CodP=codigo).first()
    fornecedor = session.query(FornecedorModel).filter_by(CodF=produto.CodF).first()
    data_preco = produto.DataPreco
    data_preco = data_preco.strftime("%d/%m/%Y")
    # Preencha os elementos da interface com os dados do fornecedor
    nomeP_entry.delete(0, ctk.END)
    nomeP_entry.insert(0, produto.Nome)
    fornecedor_option.set(fornecedor.RazaoSocial)  # Defina o valor da combobox de Fornecedor
    preco_custo_entry.delete(0, ctk.END)
    preco_custo_entry.insert(0, produto.PrecoCompra)  
    icms_entry.delete(0, ctk.END)
    icms_entry.insert(0, produto.ICMS)
    margem_entry.delete(0, ctk.END)
    margem_entry.insert(0, produto.Margem)
    preco_venda_entry.delete(0, ctk.END)
    preco_venda_entry.insert(0, produto.PrecoVenda)
    preco_antigo_entry.delete(0, ctk.END)
    preco_antigo_entry.insert(0, produto.PrecoAntigo)
    observacoesP_entry.delete(0, ctk.END)
    observacoesP_entry.insert(0, produto.Observacoes)
    data_preco_entry.delete(0, ctk.END)
    data_preco_entry.insert(0, data_preco)

    session.close()




estoquetableframe = ctk.CTkFrame(estoqueframe, height=600, width=220, border_width=2, border_color="white")
estoquetableframe.grid(row=6, columnspan=2, padx=15, pady=(10, 5))
estoquetable=ttk.Treeview(estoquetableframe, columns=('Código','Nome','Preço Custo','Margem %','Preço Venda','Preço Antigo','Fornecedor','Observações'), show='headings')
estoquetable.column('Código',minwidth=50, width=50)
estoquetable.column('Nome',minwidth=200, width=300)
estoquetable.column('Preço Custo',minwidth=90, width=90)
estoquetable.column('Margem %',minwidth=80, width=80)
estoquetable.column('Preço Venda',minwidth=90, width=90)
estoquetable.column('Preço Antigo',minwidth=90, width=90)
estoquetable.column('Fornecedor',minwidth=90, width=110)
estoquetable.column('Observações',minwidth=90, width=200)
estoquetable.heading('Código',text='Código')
estoquetable.heading('Nome',text='Nome')
estoquetable.heading('Preço Custo',text='Preço Custo')
estoquetable.heading('Margem %',text='Margem %')
estoquetable.heading('Preço Venda',text='Preço Venda')
estoquetable.heading('Preço Antigo',text='Preço Antigo')
estoquetable.heading('Fornecedor',text='Fornecedor')
estoquetable.heading('Observações',text='Observações')
estoquetable.grid(row=2, columnspan=2, padx=5, pady=(5, 5))
popularProdutos()
estoquetable.bind("<Double-1>", duplo_click)





#############################################################################################################
def adicionar_fornecedor():
    if verifica_conexao(elephant_url):
        recover_db()
    resposta = tkinter.messagebox.askquestion("Confirmação", "Adicionar novo Fornecedor?")

    if resposta == "yes":    
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            razao_social = razaosocial_entry.get()
            if not razao_social:
                raise ValueError("O campo Razão Social é obrigatório")
            verifica_fornecedor = session.query(FornecedorModel).filter_by(RazaoSocial=razao_social).first()
            if verifica_fornecedor is not None:
                if verifica_fornecedor.RazaoSocial == razao_social:
                    raise ValueError("Já existe um Fornecedor com essa Razão Social")
            razao_social = razao_social[:255]
            cnpj = cnpj_entry.get()
            if not cnpj:
                raise ValueError("O campo CNPJ é obrigatório")
            cnpj = ''.join(filter(str.isdigit, cnpj))
            if len(cnpj) != 14:
                raise ValueError("O CNPJ foi inserido incorretamente, verifique e tente novamente")
            verifica_fornecedor = session.query(FornecedorModel).filter_by(CNPJ=cnpj).first()
            if verifica_fornecedor is not None:
                if verifica_fornecedor.CNPJ == cnpj:
                    raise ValueError("Já existe um Fornecedor com esse CNPJ")
            

            telefone0 = telefone1_entry.get()
            if not telefone0:
                raise ValueError("O campo Telefone 1 é obrigatório")
            elif telefone0:
                telefone0 = re.sub(r'\D', '', telefone0)
                if len(telefone0) < 10:
                    raise ValueError("Telefone foi inserido incorretamente")
            
            telefone1 = telefone2_entry.get()
            if len(telefone1) != 0:
                telefone1 = re.sub(r'\D', '', telefone1)
                if len(telefone1) < 10:
                    raise ValueError("Telefone foi inserido incorretamente")

            numero = numeroF_entry.get()
            if not numero:
                numero = 0
            else:
                numero = re.sub(r'\D', '', numero)
                numero = int(numero)
            
            data = datetime.now()

            cidade = cidade_option.get()
            cidade = cidade[:255]

            logradouro = logradouroF_entry.get()
            logradouro = logradouro[:255]

            complemento = complementoF_entry.get()
            complemento = complemento[:255]

            contato = contato_entry.get()
            contato = contato[:255]

            observacoes = observacoesF_entry.get()
            observacoes = observacoes[:255]

            uf = UF_option.get()
            uf = uf[:2]

            novo_fornecedor = FornecedorModel(
                RazaoSocial = razao_social,
                UF = uf,
                Cidade = cidade,
                Logradouro = logradouro,
                Numero = numero,
                CNPJ = cnpj,
                Telefone0 = telefone0,
                Telefone1 = telefone1,
                Contato = contato,
                Complemento = complemento,
                IC = inscricao_estadual_entry.get(),
                Observacoes = observacoes,
                Data = data
            )
            session.add(novo_fornecedor)
            session.commit()
            global cod_fornecedor_selecionado
            cod_fornecedor_selecionado = novo_fornecedor.CodF
            popularFornecedores()
            reset_fornecedores()
            combo_fornecedores()
        except Exception as e:
            tkinter.messagebox.showerror("Erro", str(e))
        nova_modificacao = LastModified(table_name='Fornecedores')
        session.add(nova_modificacao)
        session.commit()
        session.close()
        if verifica_conexao(elephant_url):
            sync_db()


def deletar_fornecedor():
    if verifica_conexao(elephant_url):
        recover_db()
    resposta = tkinter.messagebox.askquestion("Confirmação", "Deletar Fornecedor?")

    if resposta == "yes":    
        codigo_fornecedor = cod_fornecedor_selecionado

        engine = create_engine('postgresql://postgres:84450000@localhost:5432/SFB')
        Session = sessionmaker(bind=engine)
        session = Session()

        fornecedor = session.query(FornecedorModel).filter_by(CodF=codigo_fornecedor).first()
        data = datetime.now()
        if fornecedor:
            fornecedor.Esconder = 1
            fornecedor.Data = data
            session.commit()
            popularFornecedores()
            combo_fornecedores() 

        else:
            print("Fornecedor não encontrado")
        nova_modificacao = LastModified(table_name='Fornecedores')
        session.add(nova_modificacao)
        session.commit()
        session.close()  
        if verifica_conexao(elephant_url):
            sync_db()

def recuperar_fornecedor():
    if verifica_conexao(elephant_url):
        recover_db()
    resposta = tkinter.messagebox.askquestion("Confirmação", "Recuperar Fornecedor?")

    if resposta == "yes":    
        codigo_fornecedor = cod_fornecedor_selecionado

        engine = create_engine('postgresql://postgres:84450000@localhost:5432/SFB')
        Session = sessionmaker(bind=engine)
        session = Session()

        fornecedor = session.query(FornecedorModel).filter_by(CodF=codigo_fornecedor).first()
        data = datetime.now()
        if fornecedor:
            fornecedor.Esconder = 0
            fornecedor.Data = data
            session.commit()
            popularFornecedores()
            combo_fornecedores() 
            
        else:
            print("Fornecedor não encontrado")
        nova_modificacao = LastModified(table_name='Fornecedores')
        session.add(nova_modificacao)
        session.commit()
        session.close()   
        if verifica_conexao(elephant_url):
            sync_db()        

def alterar_fornecedor():
    if verifica_conexao(elephant_url):
        recover_db()
    resposta = tkinter.messagebox.askquestion("Confirmação", "Alterar Fornecedor?")

    if resposta == "yes":    
        engine = create_engine('postgresql://postgres:84450000@localhost:5432/SFB')

        Session = sessionmaker(bind=engine)
        session = Session()
        # Obtenha o código do fornecedor selecionado da variável global
        codigo_fornecedor = cod_fornecedor_selecionado
        fornecedor = session.query(FornecedorModel).filter_by(CodF=codigo_fornecedor).first()
        try:
            razao_social = razaosocial_entry.get()
            if not razao_social:
                raise ValueError("O campo Razão Social é obrigatório")
            
            cnpj = cnpj_entry.get()
            if not cnpj:
                raise ValueError("O campo CNPJ é obrigatório")
            
            cnpj = ''.join(filter(str.isdigit, cnpj))
            if len(cnpj) != 14:
                raise ValueError("O CNPJ foi inserido incorretamente, verifique e tente novamente")

            telefone0 = telefone1_entry.get()
            if not telefone0:
                raise ValueError("O campo Telefone 1 é obrigatório")
            elif telefone0:
                telefone0 = re.sub(r'\D', '', telefone0)
                if len(telefone0) < 10:
                    raise ValueError("Telefone foi inserido incorretamente")
            
            telefone1 = telefone2_entry.get()
            if len(telefone1) != 0:
                telefone1 = re.sub(r'\D', '', telefone1)
                if len(telefone1) < 10:
                    raise ValueError("Telefone foi inserido incorretamente")

            numero = numeroF_entry.get()
            if not numero:
                numero = 0
            else:
                numero = re.sub(r'\D', '', numero)
                numero = int(numero)

            data = datetime.now()

            uf = UF_option.get()
            uf = uf[:2]

            observacoes = observacoesF_entry.get()
            inscricao_estadual = inscricao_estadual_entry.get()

            cidade = cidade_option.get()
            cidade = cidade[:255]

            logradouro = logradouroF_entry.get()
            logradouro = logradouro[:255]

            complemento = complementoF_entry.get()
            complemento = complemento[:255]

            contato = contato_entry.get()
            contato = contato[:255]

            observacoes = observacoesF_entry.get()
            observacoes = observacoes[:255]
            
            if fornecedor:
                # Atualize os campos do fornecedor com os novos valores
                fornecedor.RazaoSocial = razao_social
                fornecedor.UF = uf
                fornecedor.Cidade = cidade
                fornecedor.Logradouro = logradouro
                fornecedor.Numero = numero
                fornecedor.Complemento = complemento
                fornecedor.Telefone0 = telefone0
                fornecedor.Telefone1 = telefone1
                fornecedor.Contato = contato
                fornecedor.Observacoes = observacoes
                fornecedor.CNPJ = cnpj
                fornecedor.IC = inscricao_estadual
                fornecedor.Data = data
            session.commit()
        except Exception as e:
            tkinter.messagebox.showerror("Erro", str(e))
        nova_modificacao = LastModified(table_name='Fornecedores')
        session.add(nova_modificacao)
        session.commit()
        session.close()
        if verifica_conexao(elephant_url):
            sync_db()
        popularFornecedores()


# Frame de fornecedores
fornecedorframe = ctk.CTkFrame(notebook, height=720, width=1120, corner_radius=0, border_width=2, border_color="white")
fornecedorframe.grid(row=0, column=0, padx=10, pady=(10,10), sticky="nsew")

# Label "cadastro de Fornecedores"
fornecedorTituloframe = ctk.CTkFrame(fornecedorframe, height=70, width=250, border_width=2, border_color="white")
fornecedorTituloframe.grid(row=0, column=0,columnspan=2, padx=15, pady=(10,0), sticky="we") 
cadastro_label = ctk.CTkLabel(fornecedorTituloframe, text="Cadastro de Fornecedores", font=ctk.CTkFont(size=30, weight="bold"), text_color="white")
cadastro_label.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="We")
pesquisaFlabel = ctk.CTkLabel(fornecedorTituloframe, text="", font=ctk.CTkFont(size=24, weight="bold"), text_color="white", image=lupaimg, compound="left")
pesquisaFlabel.grid(row=0,column=1,padx=(0,0), pady=(10, 10), sticky="w")
pesquisafornecedor_entry = ctk.CTkEntry(fornecedorTituloframe, height=35, width=350, font=ctk.CTkFont(size=18), placeholder_text="Pesquisar")
pesquisafornecedor_entry.grid(row=0, column=1,columnspan=2, padx=25, pady=(5, 0), sticky="we")
pesquisafornecedor_entry.bind("<KeyRelease>", pesquisaFornecedor)

fornecedor_excluido_checkbox = ctk.CTkCheckBox(fornecedorTituloframe, text="Mostrar Excluídos",font=ctk.CTkFont(size=20), command=popularFornecedores)
fornecedor_excluido_checkbox.grid(row=0, column=3, columnspan=2, padx=5, pady=(5, 0),sticky="w")

# cadastro frame
cadastroFornecedorframe = ctk.CTkFrame(fornecedorframe, height=530, width=530, border_width=2, border_color="white")
cadastroFornecedorframe.grid(row=1, column=0, padx=15, pady=(10,0), sticky="we") 

# botões frame
botoesfornecedorframe = ctk.CTkFrame(fornecedorframe, height=380, width=250, border_width=2, border_color="white")
botoesfornecedorframe.grid(row=1, column=1, padx=(0,10), pady=(10,0), sticky="w") 

# Botão "Recuperar"
botao_recuperar = ctk.CTkButton(botoesfornecedorframe, text="Recuperar", font=ctk.CTkFont(size=18), fg_color="#567aba", width=230, height=82)
botao_recuperar.grid(row=3, column=0, padx=10, pady=(0,10), sticky="w")
botao_recuperar.configure(command=recuperar_fornecedor)

# Botão "Adicionar"
botao_adicionar = ctk.CTkButton(botoesfornecedorframe, text="Confirmar", font=ctk.CTkFont(size=18), fg_color="#567aba", width=230, height=82)
botao_adicionar.grid(row=0, column=0, padx=10, pady=10, sticky="w")
botao_adicionar.configure(command=adicionar_fornecedor)

# Botão "Alterar"
botao_alterar = ctk.CTkButton(botoesfornecedorframe, text="Alterar", font=ctk.CTkFont(size=18), fg_color="#567aba", width=230, height=82, command=alterar_fornecedor)
botao_alterar.grid(row=1, column=0, padx=10, pady=0, sticky="w")

# Botão "Excluir"
botao_excluir = ctk.CTkButton(botoesfornecedorframe, text="Excluir", font=ctk.CTkFont(size=18), fg_color="#567aba", width=230, height=82)
botao_excluir.grid(row=2, column=0, padx=10, pady=10, sticky="w")
botao_excluir.configure(command=deletar_fornecedor)

# Label e Entry para Razão Social
razaosocial_label = ctk.CTkLabel(cadastroFornecedorframe, text="Razão Social*:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
razaosocial_label.grid(row=1, column=0, padx=15, pady=(5, 0), sticky="w")
razaosocial_entry = ctk.CTkEntry(cadastroFornecedorframe, height=25, width=50, font=ctk.CTkFont(size=18))
razaosocial_entry.grid(row=2, column=0, columnspan=5, padx=(25,15), pady=(3, 0), sticky="we")

attbtn = ctk.CTkButton(cadastroFornecedorframe, image=attimg, text="", width=25, height=30, fg_color="#567aba", corner_radius=180, command=reset_fornecedores)
attbtn.grid(row=1,rowspan=2, column=6, pady=(10, 10), padx=5, sticky="N")


def update_cidades(event):
    estado_selecionado = UF_option.get()
    estado_data = next((estado for estado in estados if estado['sigla'] == estado_selecionado), None)
    if estado_data:
        cidades = estado_data['cidades']
        cidade_option['values'] = cidades
        cidade_option.set(cidades[0])
        cidade_option.configure(values=cidades)
    else:
        cidade_option.set('')
        print("erro")

def filter_cidades(event):
    filtro = cidade_option.get().lower()  # Obtém o texto da entrada em letras minúsculas
    estado_selecionado = UF_option.get()
    estado_data = next((estado for estado in estados if estado['sigla'] == estado_selecionado), None)
    if estado_data:
        cidades = estado_data['cidades']
        cidades_filtradas = [cidade for cidade in cidades if filtro in cidade.lower()]
        cidade_option['values'] = cidades_filtradas
        if cidades_filtradas:
            cidade_option.configure(values=cidades_filtradas)  # Define o primeiro valor filtrado como selecionado
            cidade_option.configure
            open_dropdown(cidades_filtradas)
        else:
            cidade_option.set('')  # Limpa o valor do combobox de cidades

def open_dropdown(cidades_filtradas):
    global listbox
    # Apaga a listbox anterior, se houver
    if 'listbox' in globals():
        listbox.destroy()

    # Cria uma nova listbox com os valores de 'cidades_filtradas'
    listbox = Listbox(cadastroFornecedorframe, width=34, height=min(7, len(cidades_filtradas)))
    for cidade in cidades_filtradas:
        listbox.insert(ctk.END, cidade)
    listbox.place(x=25,y=208)

    # A dropbox permanece não selecionada até que a tecla <down> seja pressionada
    listbox.bind('<Down>', lambda event: listbox.select_set(0))

    def cidade_enter(event):
        cidade_option.set(listbox.get(listbox.curselection()))
        listbox.destroy()
    # Quando 'enter' é pressionado, o valor de cidade_option é alterado com o valor da cidade selecionada
    listbox.bind('<Return>', cidade_enter)

    def listbox_click(event):
        # Verifica se o clique foi dentro da Listbox
        if event.widget == listbox:
            index = listbox.nearest(event.y)
            if index >= 0:
                listbox.select_set(index)
                cidade_option.set(listbox.get(index))
                listbox.destroy()

    listbox.bind('<Button-1>', listbox_click)

    def root_click(event):
        # Verifica se o clique foi fora da Listbox ou em outro widget
        if event.widget != listbox:
            listbox.destroy()

    root.bind('<Button-1>', root_click)



with open('cidades.json', 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)
estados = data['estados']
test_list = []
for estado in estados:
    test_list.extend(estado['cidades'])

estado_options = [estado['sigla'] for estado in estados]
estado_var = ctk.StringVar()

# Labels e Entries para Preço de Custo, ICMS, Margem, Preço de Venda e Preço Antigo
UF_label = ctk.CTkLabel(cadastroFornecedorframe, text="UF:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
UF_label.grid(row=3, column=0, padx=15, pady=(3, 0), sticky="w")
UF_option = ctk.CTkComboBox(cadastroFornecedorframe, values=estado_options, command=update_cidades)
UF_option.grid(row=4, column=0, padx=25, pady=(3, 0), sticky="w")
UF_option.bind("<<ComboboxSelected>>", update_cidades)

# Label e Entry para Fornecedor
cidade_label = ctk.CTkLabel(cadastroFornecedorframe, text="Cidade:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
cidade_label.grid(row=5, column=0, padx=(10,10), pady=(3, 0), sticky="w")
cidade_option = ctk.CTkComboBox(cadastroFornecedorframe, height=25, font=ctk.CTkFont(size=18))
cidade_option.grid(row=6, column=0, padx=(25,15), pady=(3, 0), sticky="we")
cidade_option.set(test_list[0])
cidade_option.bind("<KeyRelease>", filter_cidades)
cidade_option.bind('<Down>', lambda event: listbox.focus_set())
cidade_option.bind('<Down>', lambda event: listbox.select_set(0))

logradouro_label = ctk.CTkLabel(cadastroFornecedorframe, text="Logradouro:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
logradouro_label.grid(row=3, column=1,columnspan=4, padx=(0,10), pady=(3, 0), sticky="w")
logradouroF_entry = ctk.CTkEntry(cadastroFornecedorframe, height=25, width=400, font=ctk.CTkFont(size=18))
logradouroF_entry.grid(row=4, column=1, columnspan=4, padx=(15,10), pady=(3, 0), sticky="we")

numero_label = ctk.CTkLabel(cadastroFornecedorframe, text="Número:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
numero_label.grid(row=3, column=0,columnspan=1, padx=(170,10), pady=(3, 0), sticky="w")
numeroF_entry = ctk.CTkEntry(cadastroFornecedorframe, height=25, width=80, font=ctk.CTkFont(size=18))
numeroF_entry.grid(row=4, column=0,columnspan=1, padx=(185,10), pady=(3, 0), sticky="w")

complemento_label = ctk.CTkLabel(cadastroFornecedorframe, text="Complemento:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
complemento_label.grid(row=5, column=1, columnspan=4, padx=(0,10), pady=(3, 0), sticky="w")
complementoF_entry = ctk.CTkEntry(cadastroFornecedorframe, height=25, width=255, font=ctk.CTkFont(size=18))
complementoF_entry.grid(row=6, column=1, columnspan=4, padx=(15,10), pady=(3, 0), sticky="we")


def format_telefone(event, entry):
    telefone = entry.get()
    telefone = ''.join(filter(str.isdigit, telefone))

    if len(telefone) > 2 and len(telefone) <= 7:
        telefone = '(' + telefone[:2] + ') ' + telefone[2:]
    elif len(telefone) > 7:
        telefone = '(' + telefone[:2] + ') ' + telefone[2:7] + '-' + telefone[7:]
    if len(telefone) == 14:  # Telefone fixo
        telefone = ''.join(filter(str.isdigit, telefone))
        telefone = '(' + telefone[:2] + ') ' + telefone[2:6] + '-' + telefone[6:]

    telefone = telefone[:15]
    entry.delete(0, END)
    entry.insert(0, telefone)

telefone1_label = ctk.CTkLabel(cadastroFornecedorframe, text="Telefone 1*:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
telefone1_label.grid(row=9, column=0, padx=(10,0), pady=(3, 0), sticky="w")
telefone1_entry = ctk.CTkEntry(cadastroFornecedorframe, height=25, width=145, font=ctk.CTkFont(size=18))
telefone1_entry.grid(row=10, column=0, padx=(25,15), pady=(3, 0), sticky="we")
#telefone1_entry.bind("<KeyRelease>", format_celular)
telefone1_entry.bind("<KeyRelease>", lambda event: format_telefone(event, telefone1_entry))

telefone2_label = ctk.CTkLabel(cadastroFornecedorframe, text="Telefone 2:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
telefone2_label.grid(row=9, column=1, padx=(0,15), pady=(3, 0), sticky="w")
telefone2_entry = ctk.CTkEntry(cadastroFornecedorframe, height=25, width=145, font=ctk.CTkFont(size=18))
telefone2_entry.grid(row=10, column=1, padx=(15,15), pady=(3, 0), sticky="w")
telefone2_entry.bind("<KeyRelease>", lambda event: format_telefone(event, telefone2_entry))

contato_label = ctk.CTkLabel(cadastroFornecedorframe, text="Contato:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
contato_label.grid(row=9, column=2, columnspan=4, padx=(0,0), pady=(3, 0), sticky="w")
contato_entry = ctk.CTkEntry(cadastroFornecedorframe, height=25, width=230, font=ctk.CTkFont(size=18))
contato_entry.grid(row=10, column=2,columnspan=4, padx=(15,15), pady=(3, 0), sticky="w")

# Labels e Entry para Observações e Data de Preço
observacoes_label = ctk.CTkLabel(cadastroFornecedorframe, text="Observações:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
observacoes_label.grid(row=11, column=1,columnspan=4, padx=(0,15), pady=(3, 0), sticky="w")
observacoesF_entry = ctk.CTkEntry(cadastroFornecedorframe, height=65, width=350, font=ctk.CTkFont(size=18))
observacoesF_entry.grid(row=12, rowspan=13, column=1,columnspan=4, padx=(15,15), pady=(3, 5), sticky="we")

def format_cnpj(event):
    cnpj = cnpj_entry.get()
    cnpj = ''.join(filter(str.isdigit, cnpj))

    if len(cnpj) > 2 and len(cnpj) <= 5:
        cnpj = cnpj[:2] + '.' + cnpj[2:]
    elif len(cnpj) > 5 and len(cnpj) <= 8:
        cnpj = cnpj[:2] + '.' + cnpj[2:5] + '.' + cnpj[5:]
    elif len(cnpj) > 8 and len(cnpj) <= 12:
        cnpj = cnpj[:2] + '.' + cnpj[2:5] + '.' + cnpj[5:8] + '/' + cnpj[8:]
    elif len(cnpj) > 12:
        cnpj = cnpj[:2] + '.' + cnpj[2:5] + '.' + cnpj[5:8] + '/' + cnpj[8:12] + '-' + cnpj[12:]
    cnpj = cnpj[:18]
    cnpj_entry.delete(0, ctk.END)
    cnpj_entry.insert(0, cnpj)


cnpj_label = ctk.CTkLabel(cadastroFornecedorframe, text="C.N.P.J*:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
cnpj_label.grid(row=11, column=0, padx=15,columnspan=1, pady=(3, 0), sticky="w")
cnpj_entry = ctk.CTkEntry(cadastroFornecedorframe, height=25, width=180, font=ctk.CTkFont(size=18))
cnpj_entry.grid(row=12, column=0,columnspan=1, padx=(25,15), pady=(3, 0), sticky="we")
cnpj_entry.bind("<KeyRelease>", format_cnpj)

def format_IC(event):
    IC = inscricao_estadual_entry.get()
    IC = ''.join(filter(str.isdigit, IC))
    IC = IC[:9]
    inscricao_estadual_entry.delete(0, ctk.END)
    inscricao_estadual_entry.insert(0, IC)


inscricao_estadual_label = ctk.CTkLabel(cadastroFornecedorframe, text="Inscrição Estadual:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
inscricao_estadual_label.grid(row=13, column=0,columnspan=1, padx=(15,0), pady=(3, 0), sticky="w")
inscricao_estadual_entry = ctk.CTkEntry(cadastroFornecedorframe, height=25, width=180, font=ctk.CTkFont(size=18))
inscricao_estadual_entry.grid(row=14, column=0,columnspan=1, padx=(25,15), pady=(3, 5), sticky="we")
inscricao_estadual_entry.bind("<KeyRelease>",format_IC)


reset_fornecedores()

def double_click(event):
    item = fornecedortable.selection()[0]  # Obtém o item selecionado
    codigo = fornecedortable.item(item, "values")[0]  # Obtém o valor da coluna "Código" do item
    global cod_fornecedor_selecionado
    cod_fornecedor_selecionado = fornecedortable.item(item, "values")[0]
    # Consulta o banco de dados para obter os dados do fornecedor
    engine = create_engine('postgresql://postgres:84450000@localhost:5432/SFB')
    Session = sessionmaker(bind=engine)
    session = Session()

    fornecedor = session.query(FornecedorModel).filter_by(CodF=codigo).first()

    if fornecedor.Telefone0 is None:
        telefone1_entry.delete(0, ctk.END)
    else:
        telefone1_entry.delete(0, ctk.END)
        telefone1_entry.insert(0, formatar_telefone(fornecedor.Telefone0))

    if fornecedor.Telefone1 is None:
        telefone2_entry.delete(0, ctk.END)
    else:
        telefone2_entry.delete(0, ctk.END)
        telefone2_entry.insert(0, formatar_telefone(fornecedor.Telefone1))
    # Preencha os elementos da interface com os dados do fornecedor
    razaosocial_entry.delete(0, ctk.END)
    razaosocial_entry.insert(0, fornecedor.RazaoSocial)

    UF_option.set(fornecedor.UF)  # Defina o valor da combobox de UF
    cidade_option.set(fornecedor.Cidade)  # Defina o valor da combobox de Cidade
    logradouroF_entry.delete(0, ctk.END)
    logradouroF_entry.insert(0, fornecedor.Logradouro)
    numeroF_entry.delete(0, ctk.END)
    numeroF_entry.insert(0, fornecedor.Numero)
    complementoF_entry.delete(0, ctk.END)
    complementoF_entry.insert(0, fornecedor.Complemento)
    contato_entry.delete(0, ctk.END)
    contato_entry.insert(0, fornecedor.Contato)
    observacoesF_entry.delete(0, ctk.END)
    observacoesF_entry.insert(0, fornecedor.Observacoes)
    cnpj_entry.delete(0, ctk.END)
    cnpj_entry.insert(0, formatar_cnpj(fornecedor.CNPJ))
    inscricao_estadual_entry.delete(0, ctk.END)
    inscricao_estadual_entry.insert(0, fornecedor.IC)

    session.close()


ttkframe = ctk.CTkFrame(fornecedorframe, height=600, width=220, border_width=2, border_color="white")
ttkframe.grid(row=6, columnspan=2, padx=15, pady=(5, 5))
fornecedortable=ttk.Treeview(ttkframe, columns=('Código','Razão Social','Cidade','UF','Logradouro','Número','Telefone','CNPJ','Observações'), show='headings')
fornecedortable.column('Código',minwidth=50, width=50)
fornecedortable.column('Razão Social',minwidth=200, width=300)
fornecedortable.column('Cidade',minwidth=90, width=90)
fornecedortable.column('UF',minwidth=35, width=35)
fornecedortable.column('Logradouro',minwidth=120, width=120)
fornecedortable.column('Número',minwidth=50, width=50)
fornecedortable.column('Telefone',minwidth=90, width=110)
fornecedortable.column('CNPJ',minwidth=110, width=110)
fornecedortable.column('Observações',minwidth=90, width=200)
fornecedortable.heading('Código',text='Código')
fornecedortable.heading('Razão Social',text='Razão Social')
fornecedortable.heading('Cidade',text='Cidade')
fornecedortable.heading('UF',text='UF')
fornecedortable.heading('Logradouro',text='Logradouro')
fornecedortable.heading('Número',text='Número')
fornecedortable.heading('Telefone',text='Telefone')
fornecedortable.heading('CNPJ',text='CNPJ')
fornecedortable.heading('Observações',text='Observações')
fornecedortable.grid(row=2, columnspan=2, padx=5, pady=(5, 5))
popularFornecedores()
fornecedortable.bind("<Double-1>", double_click)

def adicionar_cliente():   
    if verifica_conexao(elephant_url):
        recover_db()
    resposta = tkinter.messagebox.askquestion("Confirmação", "Adicionar novo Cliente?")

    if resposta == "yes":    
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            nome = nomeC_entry.get()
            if not nome:
                raise ValueError("O campo Nome é obrigatório")
            nome = nome[:255]

            documento = documentoC_entry.get()
            documento = re.sub(r'\D', '', documento)
            if not documento:
                raise ValueError("O campo Documento é obrigatório")
            verifica_cliente = session.query(ClienteModel).filter_by(Documento=documento).first()
            if verifica_cliente:
                raise ValueError("Já existe um cliente cadastrado com esse CPF")
            
            if len(documento) != 11:
                raise ValueError("O CPF foi inserido incorretamente")
            
            telefone = telefoneC_entry.get()
            if telefone:
                telefone = re.sub(r'\D', '', telefone)
                if len(telefone) < 10:
                    raise ValueError("Telefone foi inserido incorretamente")

            numero = numeroC_entry.get()
            if not numero:
                numero = 0
            else:
                numero = re.sub(r'\D', '', numero)
                numero = int(numero)    

            data = datetime.now()

            logradouro = logradouroC_entry.get()
            logradouro = logradouro[:100]

            complemento = complementoC_entry.get()
            complemento = complemento[:150]

            observacoes = observacoesC_entry.get()
            observacoes = observacoes[:150]

            bairro = bairroC_entry.get()
            bairro = bairro[:30]


            novo_cliente = ClienteModel(
                Nome = nome,
                Documento = documento,
                Logradouro = logradouro,
                Numero = numero,
                Complemento = complemento,
                Bairro = bairro,
                Telefone = telefone,
                Observacoes = observacoes,
                Data = data
            )
            session.add(novo_cliente)
            session.commit()
            
            global cod_cliente_selecionado
            cod_cliente_selecionado = novo_cliente.CodC
            popularClientes()
        except Exception as e:
            tkinter.messagebox.showerror("Erro", str(e))
        nova_modificacao = LastModified(table_name='Clientes')
        session.add(nova_modificacao)
        session.commit()
        session.close() 
        if verifica_conexao(elephant_url):
            sync_db()   

def alterar_cliente():
    if verifica_conexao(elephant_url):
        recover_db()
    resposta = tkinter.messagebox.askquestion("Confirmação", "Alterar Cliente?")

    if resposta == "yes":    
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            cliente = session.query(ClienteModel).filter_by(CodC = cod_cliente_selecionado).first()
            if not cliente:
                raise ValueError("Cliente não foi encontrado")
                
            nome = nomeC_entry.get()
            if not nome:
                raise ValueError("O campo Nome é obrigatório")
            
            documento = documentoC_entry.get()
            documento = re.sub(r'\D', '', documento)
            if not documento:
                raise ValueError("O campo Documento é obrigatório")
            
            if len(documento) != 11:
                raise ValueError("O CPF foi inserido incorretamente")
            
            telefone = telefoneC_entry.get()
            if telefone:
                telefone = re.sub(r'\D', '', telefone)
                if len(telefone) < 10:
                    raise ValueError("Telefone foi inserido incorretamente")
                
            numero = numeroC_entry.get()
            if not numero:
                numero = 0
            else:
                numero = re.sub(r'\D', '', numero)
                numero = int(numero)

            nome = nome[:255]

            logradouro = logradouroC_entry.get()
            logradouro = logradouro[:100]

            complemento = complementoC_entry.get()
            complemento = complemento[:150]

            observacoes = observacoesC_entry.get()
            observacoes = observacoes[:150]

            bairro = bairroC_entry.get()
            bairro = bairro[:30]



            data = datetime.now()
            
            cliente.Nome = nome
            cliente.Documento = documento
            cliente.Logradouro = logradouro
            cliente.Numero = numero
            cliente.Complemento = complemento
            cliente.Bairro = bairro
            cliente.Telefone = telefone
            cliente.Observacoes = observacoes
            cliente.Data = data

            session.commit()
            popularClientes()
        except Exception as e:
            tkinter.messagebox.showerror("Erro", str(e))

        nova_modificacao = LastModified(table_name='Clientes')
        session.add(nova_modificacao)
        session.commit()
        session.close()   
        if verifica_conexao(elephant_url):
            sync_db() 

def deletar_cliente():
    if verifica_conexao(elephant_url):
        recover_db()
    resposta = tkinter.messagebox.askquestion("Confirmação", "Deletar Cliente?")

    if resposta == "yes":    
        Session = sessionmaker(bind=engine)
        session = Session()
        cliente = session.query(ClienteModel).filter_by(CodC = cod_cliente_selecionado).first()
        data = datetime.now()
        try:
            cliente = session.query(ClienteModel).filter_by(CodC = cod_cliente_selecionado).first()
            if not cliente:
                raise ValueError("Cliente não encontrado")
            
            cliente.Data = data
            cliente.Esconder = 1
            session.commit()
            popularClientes()
        except Exception as e:
            tkinter.messagebox.showerror("Erro", str(e))
        nova_modificacao = LastModified(table_name='Clientes')
        session.add(nova_modificacao)
        session.commit()
        session.close()  
        if verifica_conexao(elephant_url):
            sync_db()


def recuperar_cliente():
    if verifica_conexao(elephant_url):
        recover_db()
    resposta = tkinter.messagebox.askquestion("Confirmação", "Recuperar Cliente?")

    if resposta == "yes":    
        Session = sessionmaker(bind=engine)
        session = Session()
        cliente = session.query(ClienteModel).filter_by(CodC = cod_cliente_selecionado).first()
        data = datetime.now()
        try:
            cliente = session.query(ClienteModel).filter_by(CodC = cod_cliente_selecionado).first()
            if not cliente:
                raise ValueError("Cliente não encontrado")
            
            cliente.Data = data
            cliente.Esconder = 0
            session.commit()
            popularClientes()
        except Exception as e:
            tkinter.messagebox.showerror("Erro", str(e))
        nova_modificacao = LastModified(table_name='Clientes')
        session.add(nova_modificacao)
        session.commit()
        session.close()  
        if verifica_conexao(elephant_url):
            sync_db()        
  
# Frame de clientes
clienteframe = ctk.CTkFrame(notebook, height=720, width=1120, corner_radius=0, border_width=2, border_color="white")
clienteframe.grid(row=0, column=0, padx=10, pady=(10,10), sticky="nsew")

# Label "cadastro de produtos"
clienteTituloframe = ctk.CTkFrame(clienteframe, height=70, width=250, border_width=2, border_color="white")
clienteTituloframe.grid(row=0, column=0,columnspan=2, padx=15, pady=(10,0), sticky="we") 
cadastro_label = ctk.CTkLabel(clienteTituloframe, text="Cadastro de Clientes", font=ctk.CTkFont(size=30, weight="bold"), text_color="white")
cadastro_label.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="We")
pesquisaClabel = ctk.CTkLabel(clienteTituloframe, text="", font=ctk.CTkFont(size=24, weight="bold"), text_color="white", image=lupaimg, compound="left")
pesquisaClabel.grid(row=0,column=1,padx=(0,0), pady=(10, 10), sticky="w")
pesquisacliente_entry = ctk.CTkEntry(clienteTituloframe, height=35, width=450, font=ctk.CTkFont(size=18), placeholder_text="Pesquisar")
pesquisacliente_entry.grid(row=0, column=1,columnspan=2, padx=25, pady=(5, 0), sticky="we")
pesquisacliente_entry.bind("<KeyRelease>", pesquisaCliente)
cliente_excluido_checkbox = ctk.CTkCheckBox(clienteTituloframe, text="Mostrar Excluídos",font=ctk.CTkFont(size=20), command=popularClientes)
cliente_excluido_checkbox.grid(row=0, column=3, columnspan=2, padx=5, pady=(5, 0),sticky="w")

# cadastro frame
cadastroClienteframe = ctk.CTkFrame(clienteframe, height=530, width=550, border_width=2, border_color="white")
cadastroClienteframe.grid(row=1, column=0, padx=15, pady=(10,0), sticky="we") 

# botões frame
botoesclienteframe = ctk.CTkFrame(clienteframe, height=380, width=250, border_width=2, border_color="white")
botoesclienteframe.grid(row=1, column=1, padx=(0,15), pady=(10,0), sticky="w") 

#Botão "Recuperar"
botao_recuperar = ctk.CTkButton(botoesclienteframe, text="Recuperar", font=ctk.CTkFont(size=18), fg_color="#567aba", width=230, height=82)
botao_recuperar.grid(row=3, column=0, padx=10, pady=(0,10), sticky="w")
botao_recuperar.configure(command=recuperar_cliente)

# Botão "Adicionar"
botao_adicionar = ctk.CTkButton(botoesclienteframe, text="Adicionar", font=ctk.CTkFont(size=18), fg_color="#567aba", width=230, height=82)
botao_adicionar.grid(row=0, column=0, padx=10, pady=10, sticky="w")
botao_adicionar.configure(command=adicionar_cliente)

# Botão "Alterar"
botao_alterar = ctk.CTkButton(botoesclienteframe, text="Alterar", font=ctk.CTkFont(size=18), fg_color="#567aba", width=230, height=82)
botao_alterar.grid(row=1, column=0, padx=10, pady=0, sticky="w")
botao_alterar.configure(command=alterar_cliente)

# Botão "Excluir"
botao_excluir = ctk.CTkButton(botoesclienteframe, text="Excluir", font=ctk.CTkFont(size=18), fg_color="#567aba", width=230, height=82)
botao_excluir.grid(row=2, column=0, padx=10, pady=10, sticky="w")
botao_excluir.configure(command=deletar_cliente)

# Label e Entry para Nome
nome_label = ctk.CTkLabel(cadastroClienteframe, text="Nome*:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
nome_label.grid(row=1, column=0, padx=15, pady=(5, 0), sticky="w")
nomeC_entry = ctk.CTkEntry(cadastroClienteframe, height=25, width=430, font=ctk.CTkFont(size=18))
nomeC_entry.grid(row=2, columnspan=1, padx=(25,15), pady=(5, 0), sticky="w")

# Label e Entry para Documento (Antiga Cidade)
documento_label = ctk.CTkLabel(cadastroClienteframe, text="Documento*:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
documento_label.grid(row=1, columnspan=1, padx=(460,10), pady=(5, 0), sticky="w")
documentoC_entry = ctk.CTkEntry(cadastroClienteframe, height=25, width=250, font=ctk.CTkFont(size=18))
documentoC_entry.grid(row=2, columnspan=1, padx=(475,15), pady=(5, 0), sticky="we")
documentoC_entry.bind("<KeyRelease>", format_cpf)

# Labels e Entries para Logradouro, Número, Complemento
logradouro_label = ctk.CTkLabel(cadastroClienteframe, text="Logradouro:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
logradouro_label.grid(row=3, column=0, padx=15, pady=(5, 0), sticky="w")
logradouroC_entry = ctk.CTkEntry(cadastroClienteframe, height=25, width=550, font=ctk.CTkFont(size=18))
logradouroC_entry.grid(row=4, column=0, padx=25, pady=(5, 0), sticky="w")

numero_label = ctk.CTkLabel(cadastroClienteframe, text="Número:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
numero_label.grid(row=3, columnspan=1, padx=(580,10), pady=(5, 0), sticky="w")
numeroC_entry = ctk.CTkEntry(cadastroClienteframe, height=25, width=80, font=ctk.CTkFont(size=18))
numeroC_entry.grid(row=4, columnspan=1, padx=(595,10), pady=(5, 0), sticky="w")

complemento_label = ctk.CTkLabel(cadastroClienteframe, text="Complemento:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
complemento_label.grid(row=7, column=0, padx=(15,10), pady=(5, 0), sticky="w")
complementoC_entry = ctk.CTkEntry(cadastroClienteframe, height=25, width=145, font=ctk.CTkFont(size=18))
complementoC_entry.grid(row=8, column=0, padx=(25,10), pady=(5, 0), sticky="we")

# Labels e Entries para Bairro (Antiga UF), Telefone, Observações
bairro_label = ctk.CTkLabel(cadastroClienteframe, text="Bairro:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
bairro_label.grid(row=5, column=0, padx=15, pady=(5, 0), sticky="w")
bairroC_entry = ctk.CTkEntry(cadastroClienteframe, height=25, width=250, font=ctk.CTkFont(size=18))
bairroC_entry.grid(row=6, column=0, padx=25, pady=(5, 0), sticky="w")

telefone_label = ctk.CTkLabel(cadastroClienteframe, text="Telefone:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
telefone_label.grid(row=5, columnspan=1, padx=(280,10), pady=(5, 0), sticky="w")
telefoneC_entry = ctk.CTkEntry(cadastroClienteframe, height=25, width=225, font=ctk.CTkFont(size=18))
telefoneC_entry.grid(row=6, columnspan=1, padx=(295,0), pady=(5, 0), sticky="w")
telefoneC_entry.bind("<KeyRelease>", lambda event: format_telefone(event, telefoneC_entry))

observacoes_label = ctk.CTkLabel(cadastroClienteframe, text="Observações:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
observacoes_label.grid(row=13, column=0, padx=15, pady=(5, 0), sticky="w")
observacoesC_entry = ctk.CTkEntry(cadastroClienteframe, height=65, width=550, font=ctk.CTkFont(size=18))
observacoesC_entry.grid(row=14, columnspan=1, padx=(25,15), pady=(5, 10), sticky="we")

# ttkframe para a tabela de fornecedores
ttkframe = ctk.CTkFrame(clienteframe, height=600, width=220, border_width=2, border_color="white")
ttkframe.grid(row=6, columnspan=2, padx=15, pady=(10, 5))
clientetable=ttk.Treeview(ttkframe, columns=('Código', 'Nome', 'Documento', 'Logradouro', 'Número', 'Complemento', 'Bairro', 'Telefone', 'Observações'), show='headings')
clientetable.column('Código', minwidth=50, width=50)
clientetable.column('Nome', minwidth=200, width=300)
clientetable.column('Documento', minwidth=90, width=90)
clientetable.column('Logradouro', minwidth=90, width=90)
clientetable.column('Número', minwidth=90, width=90)
clientetable.column('Complemento', minwidth=90, width=90)
clientetable.column('Bairro', minwidth=80, width=80)
clientetable.column('Telefone', minwidth=90, width=110)
clientetable.column('Observações', minwidth=90, width=180)
clientetable.heading('Código', text='Código')
clientetable.heading('Nome', text='Nome')
clientetable.heading('Documento', text='Documento')
clientetable.heading('Logradouro', text='Logradouro')
clientetable.heading('Número', text='Número')
clientetable.heading('Complemento', text='Complemento')
clientetable.heading('Bairro', text='Bairro')
clientetable.heading('Telefone', text='Telefone')
clientetable.heading('Observações', text='Observações')
clientetable.grid(row=2, columnspan=2, padx=5, pady=(5, 5))
clientetable.bind("<Double-1>", selecionar_cliente)
popularClientes()



######################################################################################################
################################### FRAME DE PEDIDOS #################################################
######################################################################################################


def resetarFiltros():
    filtro_combobox.set("Data")
    apos_data.delete(0, ctk.END)
    ate_data.delete(0, ctk.END)
    pesquisapedido_entry.delete(0, ctk.END)
    popularPedidos()

# Frame de Pedidos
pedidosframe = ctk.CTkFrame(notebook, height=720, width=1120, corner_radius=0, border_width=2, border_color="white")
pedidosframe.grid(row=0, column=0, padx=10, pady=(10,10), sticky="nsew")


def pesquisapedido_filtro(event):
    popularPedidos()

# Label "cadastro de produtos"
pedidosTituloframe = ctk.CTkFrame(pedidosframe, height=70, width=250, border_width=2, border_color="white")
pedidosTituloframe.grid(row=0, column=0, columnspan=3, padx=15, pady=(10,0), sticky="we") 
pedidos_label = ctk.CTkLabel(pedidosTituloframe, text="Tabela de Pedidos", font=ctk.CTkFont(size=30, weight="bold"), text_color="white")
pedidos_label.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="We")
pesquisapedido_entry = ctk.CTkEntry(pedidosTituloframe, height=25, width=400, font=ctk.CTkFont(size=18), placeholder_text="Pesquisar")
pesquisapedido_entry.grid(row=0, column=1, padx=25, pady=(5, 0), sticky="we")
pesquisapedido_entry.bind("<KeyRelease>", pesquisapedido_filtro)

def preencher_pedido_selecionado(event):
    # Get the selected item
    item = pedidostable.selection()[0]
    
    # Get the order code from the selected item
    order_code = pedidostable.item(item, 'values')[0]

    endereco = pedidostable.item(item, 'values')[2]

    global cod_venda_selecionado
    cod_venda_selecionado = order_code
    
    # Update the order code label
    pedidoSelecionadoCod_label.configure(text=order_code)
    
    # Create a database session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Query the database for the order information
    order = session.query(VendaModel).filter_by(CodV=order_code).first()
    produtos = session.query(vendas_produtos).filter_by(CodV=order_code).all()
    
    # Update the labels with the order information
    pedidoSelecionadoCliente_label.configure(text=order.cliente.Nome)
    pedidoSelecionadoEndereco_label.configure(text=endereco)
    #valortotalSelecionado_label.configure(text=order.Valor)
    preco = order.Valor
    preco_formatado = "R$ {:.2f}".format(float(preco))
    valortotalSelecionado_label.configure(text=format_entry_comma(preco_formatado))

    if order.Concluido == 1:
        pedidoSelecionadoConcluido_label.configure(text="Concluído", text_color="Green")
    else:
        pedidoSelecionadoConcluido_label.configure(text="Não Concluído", text_color="Yellow")
    
    # Clear the selected order table
    pedidoSelecionadotable.delete(*pedidoSelecionadotable.get_children())
    
    # Fill in the selected order table with the order products
    for product in produtos:
        nomep = session.query(ProdutoModel).filter_by(CodP=product.CodP).first()
        pedidoSelecionadotable.insert('', 'end', values=(nomep.Nome, product.Quantidade, product.ValorP))

filtro_label = ctk.CTkLabel(pedidosframe, text="Ordenar por: ",font=ctk.CTkFont(size=20))
filtro_label.grid(row=1, column=0, padx=32, pady=(5, 0),sticky="w")
filtro_combobox = ctk.CTkComboBox(pedidosframe, values=["Data", "Cliente", "Valor"])
filtro_combobox.grid(row=1, column=0, columnspan=2, padx=145, pady=(5, 0),sticky="w")

def format_filtro_data(event):
    data = apos_data.get()
    data = ''.join(filter(str.isdigit, data))

    if len(data) > 2 and len(data) <= 4:
        data = data[:2] + '/' + data[2:]
    elif len(data) > 4:
        data = data[:2] + '/' + data[2:4] + '/' + data[4:]
    data = data[:10]
    apos_data.delete(0, ctk.END)
    apos_data.insert(0, data)

def format_filtro_data_ate(event):
    data = ate_data.get()
    data = ''.join(filter(str.isdigit, data))

    if len(data) > 2 and len(data) <= 4:
        data = data[:2] + '/' + data[2:]
    elif len(data) > 4:
        data = data[:2] + '/' + data[2:4] + '/' + data[4:]
    data = data[:10]
    ate_data.delete(0, ctk.END)
    ate_data.insert(0, data)    

apos_data_label = ctk.CTkLabel(pedidosframe, text="Após:",font=ctk.CTkFont(size=20))
apos_data_label.grid(row=1, column=0, columnspan=2, padx=(290,0), pady=(5, 0),sticky="w")
apos_data = ctk.CTkEntry(pedidosframe, placeholder_text="DATA")
apos_data.grid(row=1, column=0, columnspan=2, padx=(340,0), pady=(5, 0),sticky="w")
apos_data.bind("<KeyRelease>",format_filtro_data)

ate_data_label = ctk.CTkLabel(pedidosframe, text="Até:",font=ctk.CTkFont(size=20))
ate_data_label.grid(row=1, column=0, columnspan=2, padx=(490,0), pady=(5, 0),sticky="w")
ate_data = ctk.CTkEntry(pedidosframe, placeholder_text="(vazio=ATUAL)")
ate_data.grid(row=1, column=0, columnspan=2, padx=(530,0), pady=(5, 0),sticky="w")
ate_data.bind("<KeyRelease>",format_filtro_data_ate)

concluido_checkbox = ctk.CTkCheckBox(pedidosTituloframe, text="Esconder Concluídos",font=ctk.CTkFont(size=20), command=popularPedidos)
concluido_checkbox.grid(row=0, column=2, padx=10, pady=(5, 0),sticky="w")

botao_filtrar = ctk.CTkButton(pedidosframe, text="Aplicar Filtros", font=ctk.CTkFont(size=18), command=popularPedidos)
botao_filtrar.grid(row=1, column=0, columnspan=2, padx=(700,0), pady=(5, 0),sticky="w")

botao_resetar_filtros = ctk.CTkButton(pedidosframe, text="Resetar Filtros", font=ctk.CTkFont(size=18), command=resetarFiltros)
botao_resetar_filtros.grid(row=1, column=0, columnspan=3, padx=(845,0), pady=(5, 0),sticky="w")

# Tabela de pedidos
pedidostableframe = ctk.CTkFrame(pedidosframe, height=600, width=220, border_width=2, border_color="white")
pedidostableframe.grid(row=2, column=0, columnspan=2, padx=15, pady=(10, 5), sticky="w")
pedidostable=ttk.Treeview(pedidostableframe, columns=('Código', 'Cliente', 'Endereco', 'Telefone', 'Valor', 'Entrega', 'Concluido'), show='headings')
pedidostable.column('Código', minwidth=50, width=50)
pedidostable.column('Cliente', minwidth=200, width=250)
pedidostable.column('Endereco', minwidth=250, width=400)
pedidostable.column('Telefone', minwidth=90, width=110)
pedidostable.column('Valor', minwidth=80, width=80)
pedidostable.column('Entrega', minwidth=70, width=70)
pedidostable.column('Concluido', minwidth=120, width=120)
pedidostable.heading('Código', text='Código')
pedidostable.heading('Cliente', text='Cliente')
pedidostable.heading('Endereco', text='Endereço')
pedidostable.heading('Telefone', text='Telefone')
pedidostable.heading('Valor', text='Valor')
pedidostable.heading('Entrega', text='Entrega')
pedidostable.heading('Concluido', text='Concluido')
pedidostable.grid(row=0, column=0, padx=5, pady=(5, 5))
popularPedidos()
pedidostable.bind("<Double-1>", preencher_pedido_selecionado)



# Tabela do pedido selecionado
pedidoSelecionadotableframe = ctk.CTkFrame(pedidosframe, height=600, width=220, border_width=2, border_color="white")
pedidoSelecionadotableframe.grid(row=3, column=0, columnspan=2, padx=15, pady=(10, 5),sticky="we")
pedidoSelecionadotable=ttk.Treeview(pedidoSelecionadotableframe, columns=('Produto', 'Quantidade', 'Valor'), show='headings')
pedidoSelecionadotable.column('Produto', minwidth=250, width=300)
pedidoSelecionadotable.column('Quantidade', minwidth=100, width=100)
pedidoSelecionadotable.column('Valor', minwidth=130, width=130)
pedidoSelecionadotable.heading('Produto', text='Produto')
pedidoSelecionadotable.heading('Quantidade', text='Quantidade')
pedidoSelecionadotable.heading('Valor', text='Valor(unidade)')
pedidoSelecionadotable.grid(row=0, rowspan=6, column=0, columnspan=5, padx=5, pady=(5, 5), sticky="w")

infopedido_frame = ctk.CTkFrame(pedidoSelecionadotableframe, fg_color="#4b4a4d", border_width=2, border_color="#1f1e21")
#1f1e21
infopedido_frame.grid(row=0, rowspan=10, column=5,columnspan=9, padx=(0,5),pady=5, sticky="nwe")
infopedido_mask = ctk.CTkLabel(infopedido_frame, text="                                                                                                                                                                                ")
infopedido_mask.grid(row=0, padx=5, column=0,sticky="we")

pedidoSelecionadoCod = ctk.CTkLabel(infopedido_frame, text="Código pedido:", font=ctk.CTkFont(size=20, weight="bold"), text_color="white")
pedidoSelecionadoCod.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="w")
pedidoSelecionadoCod_label = ctk.CTkLabel(infopedido_frame, text="CódP", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
pedidoSelecionadoCod_label.grid(row=1, column=0, padx=15, pady=(0, 0), sticky="nw")

pedidoSelecionadoCliente = ctk.CTkLabel(infopedido_frame, text="Cliente:", font=ctk.CTkFont(size=20, weight="bold"), text_color="white")
pedidoSelecionadoCliente.grid(row=2, column=0, padx=5, pady=(5, 0), sticky="w")
pedidoSelecionadoCliente_mask = ctk.CTkLabel(infopedido_frame, text="                  ", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
pedidoSelecionadoCliente_mask.grid(row=3, column=0, padx=(5,5), pady=(0, 0), sticky="nw")
pedidoSelecionadoCliente_label = ctk.CTkLabel(infopedido_frame, text="Nome do Cliente", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
pedidoSelecionadoCliente_label.grid(row=3, column=0, padx=15, pady=(0, 0), sticky="nw")

pedidoSelecionadoEndereco = ctk.CTkLabel(infopedido_frame, text="Endereço do pedido:", font=ctk.CTkFont(size=20, weight="bold"), text_color="white")
pedidoSelecionadoEndereco.grid(row=4, column=0, padx=5, pady=(5, 0), sticky="w")
pedidoSelecionadoEndereco_mask = ctk.CTkLabel(infopedido_frame, text="                                     ", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
pedidoSelecionadoEndereco_mask.grid(row=5, column=0,columnspan=3, padx=5, pady=(0, 0), sticky="nw")
pedidoSelecionadoEndereco_label = ctk.CTkLabel(infopedido_frame, text="Endereço do pedido", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
pedidoSelecionadoEndereco_label.grid(row=5, column=0,columnspan=3, padx=15, pady=(0, 0), sticky="nw")

pedidoSelecionadoConcluido = ctk.CTkLabel(infopedido_frame, text="Status do pedido:", font=ctk.CTkFont(size=20, weight="bold"), text_color="white")
pedidoSelecionadoConcluido.grid(row=6, column=0, padx=5, pady=(5, 0), sticky="w")
pedidoSelecionadoConcluido_label = ctk.CTkLabel(infopedido_frame, text="Status", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
pedidoSelecionadoConcluido_label.grid(row=7, column=0,columnspan=3, padx=15, pady=(0, 10), sticky="nw")


pedidoSelecionadoValor_frame = ctk.CTkFrame(pedidoSelecionadotableframe, height=100, width=220, border_width=2, border_color="white")
pedidoSelecionadoValor_frame.grid(row=6,rowspan=2, column=0, columnspan=5, padx=(15,15), pady=(10, 5),sticky="w")
totalSelecionado_label = ctk.CTkLabel(pedidoSelecionadoValor_frame, text="TOTAL:", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
totalSelecionado_label.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="wn")
valortotalSelecionado_mask = ctk.CTkLabel(pedidoSelecionadoValor_frame, text="                     ", font=ctk.CTkFont(size=28, weight="bold"), text_color="white")
valortotalSelecionado_mask.grid(row=1, column=0, padx=10, pady=(5, 5), sticky="n")
valortotalSelecionado_label = ctk.CTkLabel(pedidoSelecionadoValor_frame, text="R$     ", font=ctk.CTkFont(size=28, weight="bold"), text_color="white")
valortotalSelecionado_label.grid(row=1, column=0, padx=10, pady=(5, 5), sticky="wn")

entreguebtn = ctk.CTkButton(pedidoSelecionadotableframe, text="Marcar como concluído", font=ctk.CTkFont(size=18), fg_color="#567aba", width=220, height=50)
entreguebtn.grid(row=6, column=3, padx=0, pady=30, sticky="s")
entreguebtn.configure(command=concluir_venda)




notebook.add(consultarframe, text="Sistema de Consulta Agropecuária Oliveira                                                                                                                                                                                                                                                                                                                                                                                                                                               ")
notebook.add(estoqueframe, text="Sistema de Produtos Agropecuária Oliveira                                                                                                                                                                                                                                                                                                                                                                                                                                   ")
notebook.add(fornecedorframe, text="Fornecedores Agropecuária Oliveira                                                                                                                                                                                                                                                                                                                                                                                                                                    ")
notebook.add(clienteframe, text="Clientes Agropecuária Oliveira                                                                                                                                                                                                                                                                                                                                                                                                                                   ")
notebook.add(pedidosframe, text="Sistema de Pedidos Agropecuária Oliveira                                                                                                                                                                                                                                                                                                                                                                                                                                               ")


if verifica_conexao(elephant_url):
    recover_db()

popular()
popularClientes()
popularFornecedores()
popularPedidos()

root.mainloop()
