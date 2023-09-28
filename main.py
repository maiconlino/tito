import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
import numpy as np
import pickle 
import lime
import lime.lime_tabular
from pickle import load
from PIL import Image
from matplotlib import pyplot as plt
import re
import os
from google.cloud.sql.connector import Connector
import sqlalchemy
import pymysql
import bcrypt
from concurrent.futures import TimeoutError
import random
from pandas_profiling import ProfileReport
import zipfile

import mysql.connector

app = Flask(__name__)
app.secret_key = '{[L.i.F.e.]*(C.t.I.)}_flask'


loaded_model = pickle.load(open('SVM03-11-2022_02-50-37.sav','rb'))
scalerfile = 'scaler2_03-19-2022_02-19-47.pkl'
scaler = load(open(scalerfile, 'rb'))
X_train = pd.read_csv('X_trainLIME_03-19-2022_03-59-34.csv', sep=';', index_col=False)
Y_train = pd.read_csv('Y_trainLIME_03-19-2022_03-59-34.csv', sep=';', index_col=False)

colunas = ('NU_IDADE_N','TRATAMENTO','RAIOX_TORA','TESTE_TUBE','FORMA','AGRAVDOENC','BACILOSC_E','BACILOS_E2','HIV','BACILOSC_6','DIAS')
prognosis = ''





#BANCOGOOGLE
# # initialize Connector object
# connector = Connector()

# # function to return the database connection
# def getconn() -> pymysql.connections.Connection:
#     conn: pymysql.connections.Connection = connector.connect(
#         "deeptub:us-central1:tito",
#         "pymysql",
#         user="maicon",
#         password="Hacker23Anos!",
#         db="tito"
#     )
#     return conn

# # create connection pool
# pool = sqlalchemy.create_engine(
#     "mysql+pymysql://",
#     creator=getconn,
# )

#BANCOLOCAL - E BANCO AWS LOCAL
# function to return the database connection
def getconn() -> mysql.connector.connection.MySQLConnection:
    conn: mysql.connector.connection.MySQLConnection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="tito"
    )
    return conn

# create connection pool
pool = sqlalchemy.create_engine(
    "mysql+mysqlconnector://",
    creator=getconn,
)

def prognosis_tuberculosis(input_data):
    input_data_numpy = np.asarray(input_data)
    input_reshape = input_data_numpy.reshape(1,-1)
    #print(input_reshape)
    base_x = pd.DataFrame(input_reshape, columns=colunas)
    #print(base_x.head())
        
    test_scaled_set = scaler.transform(base_x)
    test_scaled_set = pd.DataFrame(test_scaled_set, columns=colunas)

    #print(test_scaled_set.head())

    class_names = ["Cura","Óbito"]
    explainer = lime.lime_tabular.LimeTabularExplainer(X_train.values, training_labels=Y_train,class_names=class_names, feature_names=X_train.columns, kernel_width=3, discretize_continuous=True, verbose=False)
    exp = explainer.explain_instance(test_scaled_set.values[0], loaded_model.predict_proba, num_features=11)
    #exp.show_in_notebook()
    lista = exp.as_list()
    lista2 = []
    predictions = loaded_model.predict(test_scaled_set)


    #predictions
    if(predictions[0]==3):
        #retorno = "A probabilidade de **óbito** no prognósitco da Tuberculose é de: {}%"
        #retorno = retorno.format(round(exp.predict_proba[1]*100,2))
        return (predictions[0],round(exp.predict_proba[1]*100,2),lista2,lista)
    else:
        #retorno = "A probabilidade de **cura** no prognósitco da Tuberculose é de: {}%"
        #retorno = retorno.format(round(exp.predict_proba[0]*100,2))
        return (predictions[0],round(exp.predict_proba[0]*100,2),lista2,lista)



@app.route("/")
def index():
    return render_template("index.html")

def listar_pacientes():
    if "identificadorUsuario" in session and session["identificadorUsuario"] != "":
    # Aqui você pode verificar as credenciais do usuário em um banco de dados ou qualquer outra lógica desejada.
        # Abre a conexão
        db_conn = getconn()

        try:
            cursor = db_conn.cursor(dictionary=True)

            # Executa a consulta
            select_Pacientes = "SELECT * FROM tito_pacientes WHERE id_tito_usuarios=%s"
            cursor.execute(select_Pacientes, (session['identificadorUsuario'],))
            pacientes = cursor.fetchall()

        finally:
            # Fecha a conexão
            db_conn.close()

        # Retorna os pacientes
        return pacientes

    else:
         return ""


@app.route("/prognostico")
def prognostico():
    pacientes = listar_pacientes()
    if pacientes != "":
        return render_template("prognostico.html", pacientes=pacientes)
    else:
         return render_template("prognostico.html")

@app.route('/prognostico_form', methods=['POST'])
def processar_formulario():
    # Acessar os dados do formulário
    dados =  request.form
    form_tipo_de_tratamento = dados['form_tipo_de_tratamento']
    form_idade_do_paciente = dados['form_idade_do_paciente']
    form_radiografia_torax = dados['form_radiografia_torax']
    form_teste_tuberculinio = dados['form_teste_tuberculinio']
    form_forma_da_tuberculose = dados['form_forma_da_tuberculose']
    form_agravos_doenca_mental = dados['form_agravos_doenca_mental']
    form_hiv = dados['form_hiv']
    form_bacilosc_e = dados['form_bacilosc_e']
    form_bacilosc_e2 = dados['form_bacilosc_e2']
    form_bacilosc_6 = dados['form_bacilosc_6']
    form_dias_em_tratamento = dados['form_dias_em_tratamento']

    form_paciente = ""
    if 'form_paciente' in request.form:
        form_paciente = dados['form_paciente']
        form_paciente = form_paciente.split('|')[0]



    # Faça o processamento necessário com os dados
    prognosis = prognosis_tuberculosis([form_idade_do_paciente, form_tipo_de_tratamento, form_radiografia_torax, form_teste_tuberculinio, form_forma_da_tuberculose, form_agravos_doenca_mental, form_bacilosc_e, form_bacilosc_e2, form_hiv, form_bacilosc_6, form_dias_em_tratamento])
    
    value=str(prognosis[1])

    #ver se o usuário está logado se sim insere o paciente para aquele usuário
    if "identificadorUsuario" in session and session["identificadorUsuario"] != "":

        if form_paciente != "":
            #existe o paciente selecionado
            # Preparação da query de inserção
            insert_stmt = """
                INSERT INTO tito_classificacoes 
                (idade, tipo_de_tratamento, radiografia_do_torax, teste_tuberculineo, forma_tuberculose, agravos_doenca_mental, hiv, baciloscopia_1_amostra, baciloscopia_2_amostra, baciloscopia_6_mes, dias_em_tratamento, classificacao_predita, probabilidade_predita, id_tito_usuarios, id_tito_pacientes) 
                VALUES 
                ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})
            """.format(
                form_idade_do_paciente, form_tipo_de_tratamento, form_radiografia_torax, form_teste_tuberculinio, form_forma_da_tuberculose, form_agravos_doenca_mental, form_hiv, form_bacilosc_e, form_bacilosc_e2, form_bacilosc_6, form_dias_em_tratamento, prognosis[0], value, session["identificadorUsuario"], form_paciente
            )

            # Abre a conexão
            db_conn = getconn()

            try:
                cursor = db_conn.cursor(dictionary=True)

                # Executar a inserção
                cursor.execute(insert_stmt)
                db_conn.commit()

            finally:
                # Fecha a conexão
                db_conn.close()


        else:     
            # Preparação da query de inserção
            insert_stmt = """
            INSERT INTO tito_classificacoes 
            (idade, tipo_de_tratamento, radiografia_do_torax, teste_tuberculineo, forma_tuberculose, agravos_doenca_mental, hiv, baciloscopia_1_amostra, baciloscopia_2_amostra, baciloscopia_6_mes, dias_em_tratamento, classificacao_predita, probabilidade_predita, id_tito_usuarios) 
            VALUES 
            ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})
        """.format(
            form_idade_do_paciente, form_tipo_de_tratamento, form_radiografia_torax, form_teste_tuberculinio, form_forma_da_tuberculose, form_agravos_doenca_mental, form_hiv, form_bacilosc_e, form_bacilosc_e2, form_bacilosc_6, form_dias_em_tratamento, prognosis[0], value, session["identificadorUsuario"]
        )

        # Abre a conexão
        db_conn = getconn()

        try:
            cursor = db_conn.cursor(dictionary=True)

            # Executar a inserção
            cursor.execute(insert_stmt)
            db_conn.commit()

        finally:
            # Fecha a conexão
            db_conn.close()


        
    else:
        # Preparação da query de inserção
        insert_stmt = """
            INSERT INTO tito_classificacoes 
            (idade, tipo_de_tratamento, radiografia_do_torax, teste_tuberculineo, forma_tuberculose, agravos_doenca_mental, hiv, baciloscopia_1_amostra, baciloscopia_2_amostra, baciloscopia_6_mes, dias_em_tratamento, classificacao_predita, probabilidade_predita) 
            VALUES 
            ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})
        """.format(
            form_idade_do_paciente, form_tipo_de_tratamento, form_radiografia_torax, form_teste_tuberculinio, form_forma_da_tuberculose, form_agravos_doenca_mental, form_hiv, form_bacilosc_e, form_bacilosc_e2, form_bacilosc_6, form_dias_em_tratamento, prognosis[0], value
        )

        # Abre a conexão
        db_conn = getconn()

        try:
            cursor = db_conn.cursor(dictionary=True)

            # Executar a inserção
            cursor.execute(insert_stmt)
            db_conn.commit()

        finally:
            # Fecha a conexão
            db_conn.close()


    

    ListaResultado = []
    for X in prognosis[2]:
        ListaResultado.append(X)
    
    df = pd.DataFrame({"Attributes" : ListaResultado})
    if prognosis[0]==1:
        #print('Classificado como: Cura 🔵')
        #print('<h2>Probabilidade de: ', value,'% </h2> ')
        #st.metric(label=' ',value=str(prognosis[1])+'%')
        #print("Atributos que influenciaram para este resultado por ordem de importância")
        #st.dataframe(prognosis[2])
        #print(df)
        return render_template("resultado_prognostico.html",percentual=value, tipopredito='cura')
    else:
        #print('Classificado como: Óbito 🔴')
        #print('<h2>Probabilidade de: ', value,'% </h2> ')
        #st.metric(label=' ',value=str(prognosis[1])+'%')
        #print("Atributos que influenciaram para este resultado por ordem de importância")
        #st.dataframe(prognosis[2])
        #print(df)
        return render_template("resultado_prognostico.html",percentual=value,  tipopredito='obito')

    # Retorne a resposta ao cliente
    #return f'form_tipo_de_tratamento: {form_tipo_de_tratamento}, form_idade_do_paciente: {form_idade_do_paciente}, form_radiografia_torax: {form_radiografia_torax}, form_teste_tuberculinio: {form_teste_tuberculinio}, form_forma_da_tuberculose: {form_forma_da_tuberculose}, form_agravos_doenca_mental: {form_agravos_doenca_mental}, form_hiv: {form_hiv}, form_bacilosc_e: {form_bacilosc_e}, form_bacilosc_e2: {form_bacilosc_e2}, form_bacilosc_6: {form_bacilosc_6}, form_dias_em_tratamento: {form_dias_em_tratamento}'

@app.route("/artigospublicados")
def artigospublicados():
    return render_template("artigospublicados.html")

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    senha_criptografada = ""
    if request.method == 'POST':
        # Obter os dados do formulário
        form_nome_completo = request.form['form_nome_completo']
        form_cpf = request.form['form_cpf']
        form_email = request.form['form_email']
        form_sen = request.form['form_sen']
        form_senc = request.form['form_senc']
       
        #validacao back-end seguranca se o usuario desativar javascript ou manipula-lo no front
        vazio = False
        if form_nome_completo=="" or form_cpf=="" or form_email=="" or form_sen=="" or form_senc=="":
            vazio = True
        
        lenSenhaMenorQue6 = False
        if len(form_sen)<6:
            lenSenhaMenorQue6 = True
        
        lenSenhaMenorQue6Confirmacao = False
        if len(form_senc)<6:
            lenSenhaMenorQue6Confirmacao = True
 
        senhasIguais = False
        if form_sen==form_senc:
            senhasIguais = True
        # Aqui você pode realizar o processamento necessário, como salvar os dados em um banco de dados
        # ou qualquer outra lógica desejada.

        submissao = True
        jaExisteNoBancoDeDados = False
        if vazio or lenSenhaMenorQue6 or lenSenhaMenorQue6Confirmacao or not(senhasIguais):
            submissao = False
        else:
            submissao = True
            #tudo certo pode cadastrar no banco
            # Gerar um salt (valor aleatório utilizado na criptografia)
            salt = bcrypt.gensalt()
            
            # Criptografar a senha com o salt
            senha_criptografada = bcrypt.hashpw(form_sen.encode('utf-8'), salt)

            # Exibir a senha criptografada
            #print(senha_criptografada.decode('utf-8'))
             # insert statement
            #google
            # insert_stmt = sqlalchemy.text("""INSERT INTO tito_usuarios 
            #             (nomeCompleto, cpf, senhaCriptografada, email, salt) 
            #             VALUES 
            #             (:nomeCompleto, :cpf, :senhaCriptografada, :email, :salt)""",
            # )

            # with pool.connect() as db_conn:
            #     # insert into database
            #     select_Email = sqlalchemy.text("SELECT * from tito_usuarios WHERE email=:email or cpf=:cpf")
            #     result = db_conn.execute(select_Email, parameters={"email": form_email, "cpf": form_cpf}).fetchall()
            #     #result = db_conn.execute(sqlalchemy.text("SELECT * from tito_usuarios WHERE email='"+form_email+"' OR cpf='"+form_cpf+"")).fetchall()
            #     # Do something with the results

            #     db_conn.commit()
            #     for row in result:
            #         if row[4]==form_email or row[2]==form_cpf:
            #             submissao = False
            #             jaExisteNoBancoDeDados = True
            #             break
            #     if not(jaExisteNoBancoDeDados):
            #              db_conn.execute(insert_stmt, parameters={"nomeCompleto": form_nome_completo,"cpf": form_cpf,"senhaCriptografada": senha_criptografada,"email": form_email,"salt": salt})
            #              db_conn.commit()

            # try:
            # # Seu código aqui que pode gerar um TimeoutError
            #     connector.close()  
            # except TimeoutError:
            #     # Tratamento do erro TimeoutError
            #     pass

            #aws local
            # INSERT statement
            insert_stmt = """
                INSERT INTO tito_usuarios 
                (nomeCompleto, cpf, senhaCriptografada, email, salt) 
                VALUES 
                (%(nomeCompleto)s, %(cpf)s, %(senhaCriptografada)s, %(email)s, %(salt)s)
            """

            # Verificação de e-mail e CPF existentes
            select_Email = """
                SELECT * FROM tito_usuarios 
                WHERE email=%(email)s OR cpf=%(cpf)s
            """

            db_conn = getconn()

            try:
                cursor = db_conn.cursor(dictionary=True)

                # Verificar se o e-mail ou CPF já existem no banco de dados
                cursor.execute(
                    select_Email, 
                    {"email": form_email, "cpf": form_cpf}
                )

                result = cursor.fetchall()

                for row in result:
                    if row['email'] == form_email or row['cpf'] == form_cpf:
                        submissao = False
                        jaExisteNoBancoDeDados = True
                        break

                if not jaExisteNoBancoDeDados:
                    # Executar a inserção
                    cursor.execute(
                        insert_stmt, 
                        {
                            "nomeCompleto": form_nome_completo,
                            "cpf": form_cpf,
                            "senhaCriptografada": senha_criptografada,
                            "email": form_email,
                            "salt": salt
                        }
                    )
                    db_conn.commit()

            finally:
                # Fechar a conexão
                db_conn.close()

             
        return render_template('cadastro.html', submissao=submissao, vazio=vazio, lenSenhaMenorQue6=lenSenhaMenorQue6, lenSenhaMenorQue6Confirmacao=lenSenhaMenorQue6Confirmacao, senhasIguais=senhasIguais, teste=senha_criptografada, jaExisteNoBancoDeDados=jaExisteNoBancoDeDados)

    return render_template('cadastro.html')



@app.route('/validar_email', methods=['POST'])
def validar_email():
    email = request.form.get('email')  # Obtenha o valor do campo de e-mail enviado pelo AJAX
    # Verifique se o e-mail já está cadastrado no banco de dados
    tamResult = 0
    #gogole
    # with pool.connect() as db_conn:
    #              # insert into database
    #              select_Email = sqlalchemy.text("SELECT * from tito_usuarios WHERE email=:email")
    #              result = db_conn.execute(select_Email, parameters={"email": email}).fetchall()
    #              # Do something with the results
    #              db_conn.commit()
    #              tamResult = len(result)
    #              try:
    #                  # Seu código aqui que pode gerar um TimeoutError
    #                  connector.close()  
    #              except TimeoutError:
    #                  # Tratamento do erro TimeoutError
    #                  pass
    
    #aws local
    # Verificação de e-mail existente
    select_Email = """
        SELECT * FROM tito_usuarios 
        WHERE email=%(email)s
    """

    # Abre a conexão
    db_conn = getconn()

    try:
        cursor = db_conn.cursor(dictionary=True)

        # Verificar se o e-mail existe no banco de dados
        cursor.execute(
            select_Email, 
            {"email": email}
        )

        result = cursor.fetchall()

        # Operação de commit
        db_conn.commit()

        tamResult = len(result)

        for row in result:
            # Do something with the results
            pass

    finally:
        # Fecha a conexão
        db_conn.close()

    email_cadastrado = False
    if tamResult>0:
        email_cadastrado = True

    # Retorne a resposta em formato JSON
    return jsonify({'email_cadastrado': email_cadastrado})



@app.route('/validar_cpf', methods=['POST'])
def validar_cpf():
    cpf = request.form.get('cpf')  # Obtenha o valor do campo de e-mail enviado pelo AJAX
    # Verifique se o e-mail já está cadastrado no banco de dados
    tamResult = 0
    #google
    # with pool.connect() as db_conn:
    #              # insert into database
    #              select_Cpf = sqlalchemy.text("SELECT * from tito_usuarios WHERE cpf=:cpf")
    #              result = db_conn.execute(select_Cpf, parameters={"cpf": cpf}).fetchall()
    #              # Do something with the results
    #              db_conn.commit()
    #              tamResult = len(result)
    #              try:
    #                  # Seu código aqui que pode gerar um TimeoutError
    #                  connector.close()  
    #              except TimeoutError:
    #                  # Tratamento do erro TimeoutError
    #                  pass
    
    #aws local
    # Verificação de CPF existente
    select_Cpf = """
        SELECT * FROM tito_usuarios 
        WHERE cpf=%(cpf)s
    """

    # Abre a conexão
    db_conn = getconn()

    try:
        cursor = db_conn.cursor(dictionary=True)

        # Verificar se o CPF existe no banco de dados
        cursor.execute(
            select_Cpf, 
            {"cpf": cpf}
        )

        result = cursor.fetchall()

        # Operação de commit
        db_conn.commit()

        tamResult = len(result)

        for row in result:
            # Do something with the results
            pass

    finally:
        # Fecha a conexão
        db_conn.close()


    cpf_cadastrado = False
    if tamResult>0:
        cpf_cadastrado = True

    # Retorne a resposta em formato JSON
    return jsonify({'cpf_cadastrado': cpf_cadastrado})

@app.route('/painelacompanhamento')
def painelacompanhamento():
    if 'username' in session:
        #return f'Olá, {session["username"]}! <a href="/logout">Logout</a>'
        return render_template('index.html')
    return render_template('prognostico.html')

@app.route('/fazerlogin', methods=['GET', 'POST'])
def login():
    senha_criptografada = ""
    tamResult = 0
    if request.method == 'POST':
        # Obter os dados do formulário
        email = request.form['form_email']
        sen = request.form['form_sen']

       
        #google bd
        # # Aqui você pode verificar as credenciais do usuário em um banco de dados ou qualquer outra lógica desejada.
        # with pool.connect() as db_conn:
        #             # insert into database
                    
        #             select_Cpf = sqlalchemy.text("SELECT senhaCriptografada, nomeCompleto, salt, id FROM tito_usuarios WHERE email=:email")
        #             result = db_conn.execute(select_Cpf, parameters={"email": email}).fetchall()
        #             # Do something with the results
        #             db_conn.commit()
        #             tamResult = len(result)
        #             try:
        #                 # Seu código aqui que pode gerar um TimeoutError
        #                 connector.close()  
        #             except TimeoutError:
        #                 # Tratamento do erro TimeoutError
        #                 pass
                    
        #             if tamResult>0:
        #                 senhaCriptografada = result[0][0]
        #                 if bcrypt.checkpw(sen.encode('utf-8'),senhaCriptografada.encode('utf-8')):
        #                     session['username'] = email
        #                     session['nomeCompleto'] = result[0][1]
        #                     session['identificadorUsuario'] = result[0][3]
        #                     return redirect(url_for('painelacompanhamento'))
        #                 else:
        #                     return render_template('efetuarlogin.html', erro=True)
        #             else:
        #                     return render_template('efetuarlogin.html', erro=True)

        #aws banco local
        # Exemplo de SELECT usando MySQL Connector Python
        # Abre a conexão
        # Abre a conexão
        db_conn = getconn()

        try:
            cursor = db_conn.cursor(dictionary=True)
            select_query = "SELECT senhaCriptografada, nomeCompleto, salt, id FROM tito_usuarios WHERE email=%s"
            cursor.execute(select_query, (email,))
            
            # Obtenha os resultados
            result = cursor.fetchall()

            # Verifique se há resultados
            tamResult = len(result)
            
            if tamResult > 0:
                # Operação de commit
                db_conn.commit()

                senhaCriptografada = result[0]['senhaCriptografada']
                
                if bcrypt.checkpw(sen.encode('utf-8'),senhaCriptografada.encode('utf-8')):
                    session['username'] = email
                    session['nomeCompleto'] = result[0]['nomeCompleto']
                    session['identificadorUsuario'] = result[0]['id']
                    return redirect(url_for('painelacompanhamento'))
                else:
                    return render_template('efetuarlogin.html', erro=True)
            else:
                return render_template('efetuarlogin.html', erro=True)
        finally:
            # Fecha a conexão
            db_conn.close()

        
    return render_template('efetuarlogin.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('nomeCompleto', None)
    session.pop('identificadorUsuario', None)
    return render_template("index.html")


@app.route('/pacientes')
def pacientes():  
    if "identificadorUsuario" in session and session["identificadorUsuario"] != "":
          return render_template("pacientes.html")     
    return render_template("index.html")

@app.route('/pacientes_ver')
def pacientes_ver(): 
    pacientes = listar_pacientes()
    if pacientes != "":
        return render_template("pacientes_ver.html", pacientes=pacientes)
    else:
         return render_template("index.html")

    # if "identificadorUsuario" in session and session["identificadorUsuario"] != "":
    #     # Aqui você pode verificar as credenciais do usuário em um banco de dados ou qualquer outra lógica desejada.
    #     with pool.connect() as db_conn:
    #                     # insert into database
    #                     select_Pacientes = sqlalchemy.text("SELECT * FROM tito_pacientes WHERE id_tito_usuarios=:id_tito_usuarios")
    #                     pacientes = db_conn.execute(select_Pacientes, parameters={"id_tito_usuarios": session['identificadorUsuario']}).fetchall()
    #                     # Do something with the results
    #                     db_conn.commit()
    #                     try:
    #                         # Seu código aqui que pode gerar um TimeoutError
    #                         connector.close()  
    #                     except TimeoutError:
    #                         # Tratamento do erro TimeoutError
    #                         pass
    #                     return render_template("pacientes_ver.html", pacientes=pacientes)
    # return render_template("index.html")

def listar_evolucao_do_pacinete_medico(paciente_id):
    if "identificadorUsuario" in session and session["identificadorUsuario"] != "":
    # Aqui você pode verificar as credenciais do usuário em um banco de dados ou qualquer outra lógica desejada.
        # Abre a conexão
        db_conn = getconn()

        try:
            cursor = db_conn.cursor(dictionary=True)

            # Executa a consulta
            select_Pacientes = "SELECT * FROM tito_classificacoes WHERE id_tito_usuarios=%s AND id_tito_pacientes=%s ORDER BY dataHora"
            cursor.execute(select_Pacientes, (session['identificadorUsuario'], paciente_id))
            pacientes = cursor.fetchall()

        finally:
            # Fecha a conexão
            db_conn.close()

        # Retorna os pacientes
        return pacientes

    else:
         return ""

@app.route('/acompanhamento')
def acompanhamento(): 
    pacientes = listar_pacientes()
    if pacientes != "":
        return render_template("pacientes_ver.html", pacientes=pacientes)
    else:
         return render_template("pacientes_ver.html")
         
@app.route('/visualizacao')
def visualizacao(): 
    # # Especifique o caminho para o arquivo ZIP
    # caminho_arquivo_zip = 'dataset/SINAN-TB_Brazil_2001-01_2019-04v4.csv.zip'

    # # Extrair o arquivo CSV do ZIP
    # with zipfile.ZipFile(caminho_arquivo_zip, 'r') as zip_ref:
    #     # Assumindo que o arquivo CSV está na raiz do ZIP
    #     nome_arquivo_csv = zip_ref.namelist()[0]
    #     zip_ref.extractall()

    # # Carregar o arquivo CSV usando o pandas
    # df = pd.read_csv(nome_arquivo_csv, ";")
    #profile = ProfileReport(df)
    #profile.to_file(output_file='relatorio.html')

    # Ler o conteúdo do arquivo HTML
    # with open('relatorio.html', 'r') as file:
    #    relatorio_html = file.read()

    # Renderizar o template com o conteúdo do relatório
    return render_template('visualizacao.html')


     
    
@app.route('/moduloacompanhamento')
def moduloacompanhamento():
    paciente_id = request.args.get('pt')
    paciente_nomecript = request.args.get('nomecript')
    # validar se o id do paciente passado está relacionado ao profissional de saúde
    predicoes_do_paciente_especifico = listar_evolucao_do_pacinete_medico(paciente_id)
    if predicoes_do_paciente_especifico !="":
        return render_template("moduloacompanhamento.html", predicoes_do_paciente_especifico=predicoes_do_paciente_especifico, paciente_nomecript=paciente_nomecript) 
    #pegar as predições realizadas
    else:
        return render_template("moduloacompanhamento.html") 

@app.route('/cadastrarpaciente', methods=['GET', 'POST'])
def cadastrarpaciente():
    senha_criptografada = ""
    if request.method == 'POST':
        # Obter os dados do formulário
        form_apelido = request.form['form_apelido']
        form_dataDiagnostico = request.form['form_dataDiagnostico']
        form_apelidoCript = form_apelido + str(random.randint(10**9, 10**10 - 1))
       

        #validacao back-end seguranca se o usuario desativar javascript ou manipula-lo no front
        vazio = False
        if form_apelido=="" or form_dataDiagnostico=="":
            vazio = True

        if vazio:
            submissao = False
        else:
            submissao = True

             # insert statement
            # Abre a conexão
        db_conn = getconn()

        try:
            cursor = db_conn.cursor(dictionary=True)

            # Preparação da consulta
            insert_stmt = """
                INSERT INTO tito_pacientes 
                (nomeCompletoAbreviadoComIdCriptografado, apelidoAlias, dataDoDiagnostico, id_tito_usuarios) 
                VALUES 
                (%s, %s, %s, %s)
            """

            # Executa a inserção
            cursor.execute(
                insert_stmt,
                (
                    form_apelidoCript,
                    form_apelido,
                    form_dataDiagnostico,
                    session['identificadorUsuario']
                )
            )

            db_conn.commit()

        finally:
            # Fecha a conexão
            db_conn.close()

             
        return render_template('pacientes.html', submissao=submissao, paciente=form_apelidoCript)

    return render_template('pacientes.html')


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


