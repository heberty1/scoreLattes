#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is the scoreLattes script.
#
# Copyright (C) 2017 Vicente Helano
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author(s): Vicente Helano <vicente.sobrinho@ufca.edu.br>
#

import xml.etree.ElementTree as ET, sys, codecs, re, argparse
from datetime import date

class Score(object):
    """Pontuação do Currículo Lattes"""
    def __init__(self, root, inicio, fim):
        # Período considerado para avaliação
        self.__curriculo = root
        self.__numero_identificador = 0
        self.__nome_completo = ''
        self.__ano_inicio = inicio
        self.__ano_fim = fim
        self.__formacao = 0
        self.__projetos_pesquisa = 0
        self.__projetos_desenvolvimento = 0
        self.__artigos = 0
        self.__trabalhos = 0
        self.__tabela_de_qualificacao = {
            'FORMACAO-ACADEMICA-TITULACAO' : {'POS-DOUTORADO': 0, 'LIVRE-DOCENCIA': 0, 'DOUTORADO': 0, 'MESTRADO': 0},
            'PROJETO-DE-PESQUISA' : {'PESQUISA': 0, 'DESENVOLVIMENT0': 0},
            'PRODUCAO-BIBLIOGRAFICA' : {
                'ARTIGOS-PUBLICADOS': {'A1': 0, 'A2': 0, 'B1': 0, 'B2': 0, 'B3': 0, 'B4': 0, 'B5': 0, 'C': 0, 'NAO-ENCONTRADO': 0},
                'TRABALHOS-EM-EVENTOS': {
                    'INTERNACIONAL': { 'COMPLETO': 0, 'RESUMO_EXPANDIDO': 0, 'RESUMO': 0 },
                    'NACIONAL': { 'COMPLETO': 0, 'RESUMO_EXPANDIDO': 0, 'RESUMO': 0 },
                    'REGIONAL': { 'COMPLETO': 0, 'RESUMO_EXPANDIDO': 0, 'RESUMO': 0 },
                    'LOCAL': { 'COMPLETO': 0, 'RESUMO_EXPANDIDO': 0, 'RESUMO': 0 },
                    'NAO_INFORMADO': { 'COMPLETO': 0, 'RESUMO_EXPANDIDO': 0, 'RESUMO': 0 },
                },
                'LIVROS-E-CAPITULOS': {
                    'LIVRO-PUBLICADO-OU-ORGANIZADO': {
                        'LIVRO_PUBLICADO': 0,
                        'LIVRO_ORGANIZADO_OU_EDICAO': 0,
                        'NAO_INFORMADO': 0,
                    },
                    'CAPITULO-DE-LIVRO-PUBLICADO': 0,
                },
                'DEMAIS-TIPOS-DE-PRODUCAO-BIBLIOGRAFICA': { 'TRADUCAO': 0 },
            },
            'PRODUCAO-TECNICA': {
                'SOFTWARE': 0,
                'PATENTE': {'DEPOSITADA': 0, 'CONCEDIDA': 0},
                'PRODUTO-TECNOLOGICO': 0,
                'PROCESSOS-OU-TECNICAS': 0,
                'TRABALHO-TECNICO': 0,
            },
            'OUTRA-PRODUCAO': {
                'PRODUCAO-ARTISTICA-CULTURAL': {
                    'APRESENTACAO-DE-OBRA-ARTISTICA': 0,
                    'COMPOSICAO-MUSICAL': 0,
                    'OBRA-DE-ARTES-VISUAIS': 0,
                },
                'ORIENTACOES-CONCLUIDAS': {
                    'ORIENTACOES-CONCLUIDAS-PARA-POS-DOUTORADO': 0,
                    'ORIENTACOES-CONCLUIDAS-PARA-DOUTORADO': 0,
                    'ORIENTACOES-CONCLUIDAS-PARA-MESTRADO': 0,
                    'OUTRAS-ORIENTACOES-CONCLUIDAS': {
                        'MONOGRAFIA_DE_CONCLUSAO_DE_CURSO_APERFEICOAMENTO_E_ESPECIALIZACAO': 0,
                        'TRABALHO_DE_CONCLUSAO_DE_CURSO_GRADUACAO': 0,
                        'INICIACAO_CIENTIFICA': 0,
                        'ORIENTACAO-DE-OUTRA-NATUREZA': 0,
                    },
                },
            },
        }
        self.__pontuacao = {
            'FORMACAO-ACADEMICA-TITULACAO' : 0,
            'PROJETO-DE-PESQUISA': 0,
            'PRODUCAO-BIBLIOGRAFICA': 0,
            'PRODUCAO-TECNICA': 0,
            'OUTRA-PRODUCAO': 0,
        }

        # Calcula pontuação do currículo
        self.__dados_gerais()
        self.__formacao_academica_titulacao()
        self.__projetos_de_pesquisa()
        self.__producao_bibliografica()
        self.__producao_tecnica()
        self.__outra_producao()

    def __dados_gerais(self):
        if 'NUMERO-IDENTIFICADOR' not in self.__curriculo.attrib:
            raise ValueError
        self.__numero_identificador = self.__curriculo.attrib['NUMERO-IDENTIFICADOR']

        dados = self.__curriculo.find('DADOS-GERAIS')
        self.__nome_completo = dados.attrib['NOME-COMPLETO']

    def __formacao_academica_titulacao(self):
        dados = self.__curriculo.find('DADOS-GERAIS')
        formacao = dados.find('FORMACAO-ACADEMICA-TITULACAO')
        if formacao is None:
            return
        barema = {'POS-DOUTORADO': 10, 'LIVRE-DOCENCIA': 8, 'DOUTORADO': 7, 'MESTRADO': 3}
        for key,value in barema.items():
            result = formacao.find(key)
            if result is None:
                continue
            if key == 'LIVRE-DOCENCIA': # neste caso, não há STATUS-DO-CURSO
                self.__tabela_de_qualificacao['FORMACAO-ACADEMICA-TITULACAO'][key] = value
            elif result.attrib['STATUS-DO-CURSO'] == 'CONCLUIDO':
                self.__tabela_de_qualificacao['FORMACAO-ACADEMICA-TITULACAO'][key] = value
        # Calcula a pontuação total da formação acadêmica
        self.__pontuacao['FORMACAO-ACADEMICA-TITULACAO'] = sum(self.__tabela_de_qualificacao['FORMACAO-ACADEMICA-TITULACAO'].values())
            
    def __projetos_de_pesquisa(self):
        dados = self.__curriculo.find('DADOS-GERAIS')
        if dados.find('ATUACOES-PROFISSIONAIS') is None:
            return

        atuacoes = dados.find('ATUACOES-PROFISSIONAIS').findall('ATUACAO-PROFISSIONAL')
        for atuacao in atuacoes:
            atividade = atuacao.find('ATIVIDADES-DE-PARTICIPACAO-EM-PROJETO')
            if atividade is None:
                continue

            participacoes = atividade.findall('PARTICIPACAO-EM-PROJETO')
            for participacao in participacoes:
                projetos = participacao.findall('PROJETO-DE-PESQUISA')
                if projetos is None:
                    continue

                # O ano de início da participação em um projeto
                inicio_part = int(participacao.attrib['ANO-INICIO'])

                for projeto in projetos:
                    # Ignorar projeto ou participação em projeto iniciados fora do período estipulado
                    if projeto.attrib['ANO-INICIO'] != "":
                        if int(projeto.attrib['ANO-INICIO']) < self.__ano_inicio or int(projeto.attrib['ANO-INICIO']) > self.__ano_fim:
                            continue
                    else:
                        if inicio_part < self.__ano_inicio or inicio_part > self.__ano_fim:
                            continue
                      
                    # Ignorar se o proponente não for o coordenador do projeto
                    equipe = (projeto.find('EQUIPE-DO-PROJETO')).find('INTEGRANTES-DO-PROJETO')
                    if equipe.attrib['FLAG-RESPONSAVEL'] != str('SIM'):
                        continue

                    # Verifica se o projeto é financiado
                    financiamento = projeto.find('FINANCIADORES-DO-PROJETO')
                    if financiamento is None:
                        continue

                    # Verifica se há órgão financiador externo, diferente de UFC e UFCA
                    codigos = ['', 'JI7500000002', '001500000997', '008900000002']
                    financiadores = financiamento.findall('FINANCIADOR-DO-PROJETO')
                    fomento_externo = False
                    for financiador in financiadores:
                        if financiador.attrib['CODIGO-INSTITUICAO'] not in codigos:
                            fomento_externo = True
                            break
                    if not fomento_externo:
                        continue
                    
                    if projeto.attrib['NATUREZA'] == 'PESQUISA':
                        if self.__tabela_de_qualificacao['PROJETO-DE-PESQUISA']['PESQUISA'] <= 6: # máximo de 8 pontos
                            self.__tabela_de_qualificacao['PROJETO-DE-PESQUISA']['PESQUISA'] += 2
                    elif projeto.attrib['NATUREZA'] == 'DESENVOLVIMENTO':
                        if self.__tabela_de_qualificacao['PROJETO-DE-PESQUISA']['DESENVOLVIMENT0'] <= 6: # máximo de 8 pontos
                            self.__tabela_de_qualificacao['PROJETO-DE-PESQUISA']['DESENVOLVIMENT0'] += 2

        # Calcula a pontuação total dos projetos de pesquisa
        self.__pontuacao['PROJETO-DE-PESQUISA'] = sum(self.__tabela_de_qualificacao['PROJETO-DE-PESQUISA'].values())

    def __producao_bibliografica(self):
        producao = self.__curriculo.find('PRODUCAO-BIBLIOGRAFICA')
        if producao is None:
            return

        self.__artigos_publicados(producao)
        self.__trabalhos_em_eventos(producao)
        self.__livros_e_capitulos(producao)
        self.__demais_tipos_de_producao(producao)

    ################ TODO: falta usar o Qualis #################
    def __artigos_publicados(self, producao):
        artigos = producao.find('ARTIGOS-PUBLICADOS')
        if artigos is None:
            return
        for artigo in artigos.findall('ARTIGO-PUBLICADO'):
            dados = artigo.find('DADOS-BASICOS-DO-ARTIGO')
            ano = int(dados.attrib['ANO-DO-ARTIGO'])
            if ano >= self.__ano_inicio and ano <= self.__ano_fim: # somente os artigos dirante o período estipulado
                self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['ARTIGOS-PUBLICADOS']['NAO-ENCONTRADO'] += 1
        self.__artigos = sum(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['ARTIGOS-PUBLICADOS'].values())

    def __trabalhos_em_eventos(self, producao):
        trabalhos = producao.find('TRABALHOS-EM-EVENTOS')
        if trabalhos is None:
            return
        for trabalho in trabalhos.findall('TRABALHO-EM-EVENTOS'):
            ano = int(trabalho.find('DADOS-BASICOS-DO-TRABALHO').attrib['ANO-DO-TRABALHO'])
            if ano < self.__ano_inicio or ano > self.__ano_fim: # skip papers out-of-period
                continue
            abrangencia = trabalho.find('DETALHAMENTO-DO-TRABALHO').attrib['CLASSIFICACAO-DO-EVENTO']
            natureza = trabalho.find('DADOS-BASICOS-DO-TRABALHO').attrib['NATUREZA']
            self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS'][abrangencia][natureza] += 1

    def __livros_e_capitulos(self, producao):
        itens = producao.find('LIVROS-E-CAPITULOS')
        if itens is None:
            return
        livros = itens.find('LIVROS-PUBLICADOS-OU-ORGANIZADOS')
        if livros != None:
            for livro in livros.findall('LIVRO-PUBLICADO-OU-ORGANIZADO'):
                ano = int(livro.find('DADOS-BASICOS-DO-LIVRO').attrib['ANO'])
                if ano < self.__ano_inicio or ano > self.__ano_fim: # skip out-of-allowed-period production
                    continue
                if livro.find('DETALHAMENTO-DO-LIVRO').attrib['NUMERO-DE-PAGINAS'] == "":
                    continue
                paginas = int(livro.find('DETALHAMENTO-DO-LIVRO').attrib['NUMERO-DE-PAGINAS'])
                if paginas > 49: # número mínimo de páginas para livros publicados e traduções
                    tipo = livro.find('DADOS-BASICOS-DO-LIVRO').attrib['TIPO']
                    self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['LIVROS-E-CAPITULOS']['LIVRO-PUBLICADO-OU-ORGANIZADO'][tipo] += 1

        capitulos = itens.find('CAPITULOS-DE-LIVROS-PUBLICADOS')
        if capitulos != None:
            for capitulo in capitulos.findall('CAPITULO-DE-LIVRO-PUBLICADO'):
                if capitulo.find('DADOS-BASICOS-DO-CAPITULO').attrib['ANO'] == "":
                    continue
                ano = int(capitulo.find('DADOS-BASICOS-DO-CAPITULO').attrib['ANO'])
                if ano < self.__ano_inicio or ano > self.__ano_fim: # skip out-of-allowed-period production
                    continue
                self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['LIVROS-E-CAPITULOS']['CAPITULO-DE-LIVRO-PUBLICADO'] += 1

    def __demais_tipos_de_producao(self, producao):
        itens = producao.find('DEMAIS-TIPOS-DE-PRODUCAO-BIBLIOGRAFICA')
        if itens is None:
            return
        traducoes = itens.findall('TRADUCAO')
        for traducao in traducoes:
            ano = int(traducao.find('DADOS-BASICOS-DA-TRADUCAO').attrib['ANO'])
            if ano < self.__ano_inicio or ano > self.__ano_fim: # skip out-of-allowed-period production
                continue
            if traducao.find('DETALHAMENTO-DA-TRADUCAO').attrib['NUMERO-DE-PAGINAS'] == "":
                continue
            paginas = int(traducao.find('DETALHAMENTO-DA-TRADUCAO').attrib['NUMERO-DE-PAGINAS'])
            if paginas > 49: # número mínimo de páginas para livros publicados e traduções
                self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['DEMAIS-TIPOS-DE-PRODUCAO-BIBLIOGRAFICA']['TRADUCAO'] += 1

    def __producao_tecnica(self):
        producao = self.__curriculo.find('PRODUCAO-TECNICA')
        if producao is None:
            return

        self.__softwares(producao)
        self.__patentes(producao)
        self.__produtos_tecnologicos(producao)
        self.__processos_ou_tecnicas(producao)
        self.__trabalho_tecnico(producao)

    def __softwares(self, producao):
        softwares = producao.findall('SOFTWARE')
        if softwares is None:
            return
        for software in softwares:
            dados = software.find('DADOS-BASICOS-DO-SOFTWARE')
            ano = dados.attrib['ANO']
            if ano == "":
                continue
            elif self.__ano_inicio <= int(ano) <= self.__ano_fim: # somente os artigos dirante o período estipulado
                self.__tabela_de_qualificacao['PRODUCAO-TECNICA']['SOFTWARE'] += 1

    def __patentes(self, producao):
        patentes = producao.findall('PATENTE')
        if patentes is None:
            return
        for patente in patentes:
            detalhamento = patente.find('DETALHAMENTO-DA-PATENTE')
            registro = detalhamento.find('REGISTRO-OU-PATENTE')
            deposito = (registro.attrib['DATA-PEDIDO-DE-DEPOSITO'])[4:]
            concessao = (registro.attrib['DATA-DE-CONCESSAO'])[4:]
            if concessao != "":
                if self.__ano_inicio <= int(concessao) <= self.__ano_fim:
                    self.__tabela_de_qualificacao['PRODUCAO-TECNICA']['PATENTE']['CONCEDIDA'] += 1
            elif deposito != "":
                if self.__ano_inicio <= int(deposito) <= self.__ano_fim:
                    self.__tabela_de_qualificacao['PRODUCAO-TECNICA']['PATENTE']['DEPOSITADA'] += 1

    def __produtos_tecnologicos(self, producao):
        produtos = producao.findall('PRODUTO-TECNOLOGICO')
        if produtos is None:
            return
        for produto in produtos:
            dados = produto.find('DADOS-BASICOS-DO-PRODUTO-TECNOLOGICO')
            ano = dados.attrib['ANO']
            if ano == "":
                continue

            if self.__ano_inicio <= int(ano) <= self.__ano_fim:
                self.__tabela_de_qualificacao['PRODUCAO-TECNICA']['PRODUTO-TECNOLOGICO'] += 1

    def __processos_ou_tecnicas(self, producao):
        processos = producao.findall('PROCESSOS-OU-TECNICAS')
        if processos is None:
            return
        for processo in processos:
            dados = processo.find('DADOS-BASICOS-DO-PROCESSOS-OU-TECNICAS')
            ano = dados.attrib['ANO']
            if ano == "":
                continue

            if self.__ano_inicio <= int(ano) <= self.__ano_fim:
                self.__tabela_de_qualificacao['PRODUCAO-TECNICA']['PROCESSOS-OU-TECNICAS'] += 1

    def __trabalho_tecnico(self, producao):
        trabalhos = producao.findall('TRABALHO-TECNICO')
        if trabalhos is None:
            return
        for trabalho in trabalhos:
            dados = trabalho.find('DADOS-BASICOS-DO-TRABALHO-TECNICO')
            ano = dados.attrib['ANO']
            if ano == "":
                continue

            if self.__ano_inicio <= int(ano) <= self.__ano_fim:
                self.__tabela_de_qualificacao['PRODUCAO-TECNICA']['TRABALHO-TECNICO'] += 1

    def __outra_producao(self):
        producao = self.__curriculo.find('OUTRA-PRODUCAO')
        if producao is None:
            return

        self.__producao_artistica_cultural(producao)
        self.__orientacoes_concluidas(producao)

    def __producao_artistica_cultural(self, producao):
        obras = producao.find('PRODUCAO-ARTISTICA-CULTURAL')
        if obras is None:
            return

        self.__apresentacao_de_obra_artistica(obras)
        self.__composicao_musical(obras)

    def __apresentacao_de_obra_artistica(self, obras):
        apresentacoes = obras.findall('APRESENTACAO-DE-OBRA-ARTISTICA')
        if apresentacoes is None:
            return

        for apresentacao in apresentacoes:
            dados = apresentacao.find('DADOS-BASICOS-DA-APRESENTACAO-DE-OBRA-ARTISTICA')
            ano = dados.attrib['ANO']
            if ano == "":
                continue

            if self.__ano_inicio <= int(ano) <= self.__ano_fim:
                self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['PRODUCAO-ARTISTICA-CULTURAL']['APRESENTACAO-DE-OBRA-ARTISTICA'] += 1

    def __composicao_musical(self, obras):
        composicoes = obras.findall('COMPOSICAO-MUSICAL')
        if composicoes is None:
            return

        for composicao in composicoes:
            dados = composicao.find('DADOS-BASICOS-DA-COMPOSICAO-MUSICAL')
            ano = dados.attrib['ANO']
            if ano == "":
                continue

            if self.__ano_inicio <= int(ano) <= self.__ano_fim:
                self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['PRODUCAO-ARTISTICA-CULTURAL']['COMPOSICAO-MUSICAL'] += 1

    def __obra_de_artes_visuais(self, obras):
        artes = obras.findall('OBRA-DE-ARTES-VISUAIS')
        if artes is None:
            return

        for arte in artes:
            dados = arte.find('DADOS-BASICOS-DA-OBRA-DE-ARTES-VISUAIS')
            ano = dados.attrib['ANO']
            if ano == "":
                continue

            if self.__ano_inicio <= int(ano) <= self.__ano_fim:
                self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['PRODUCAO-ARTISTICA-CULTURAL']['OBRA-DE-ARTES-VISUAIS'] += 1

    def __orientacoes_concluidas(self, producao):
        orientacoes = producao.find('ORIENTACOES-CONCLUIDAS')
        if orientacoes is None:
            return

        self.__orientacoes_pos_doutorado(orientacoes)
        self.__orientacoes_doutorado(orientacoes)
        self.__orientacoes_mestrado(orientacoes)
        self.__outras_orientacoes_concluidas(orientacoes)

    def __orientacoes_pos_doutorado(self, orientacoes):
        postdocs = orientacoes.findall('ORIENTACOES-CONCLUIDAS-PARA-POS-DOUTORADO')
        if postdocs is None:
            return

        for postdoc in postdocs:
            dados = postdoc.find('DADOS-BASICOS-DE-ORIENTACOES-CONCLUIDAS-PARA-POS-DOUTORADO')
            ano = dados.attrib['ANO']
            if ano == "":
                continue

            if self.__ano_inicio <= int(ano) <= self.__ano_fim:
                self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['ORIENTACOES-CONCLUIDAS']['ORIENTACOES-CONCLUIDAS-PARA-POS-DOUTORADO'] += 1

    def __orientacoes_doutorado(self, orientacoes):
        doutores = orientacoes.findall('ORIENTACOES-CONCLUIDAS-PARA-DOUTORADO')
        if doutores is None:
            return

        for doutor in doutores:
            dados = doutor.find('DADOS-BASICOS-DE-ORIENTACOES-CONCLUIDAS-PARA-DOUTORADO')
            ano = dados.attrib['ANO']
            if ano == "":
                continue

            if self.__ano_inicio <= int(ano) <= self.__ano_fim:
                self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['ORIENTACOES-CONCLUIDAS']['ORIENTACOES-CONCLUIDAS-PARA-DOUTORADO'] += 1

    def __orientacoes_mestrado(self, orientacoes):
        mestres = orientacoes.findall('ORIENTACOES-CONCLUIDAS-PARA-MESTRADO')
        if mestres is None:
            return

        for mestre in mestres:
            dados = mestre.find('DADOS-BASICOS-DE-ORIENTACOES-CONCLUIDAS-PARA-MESTRADO')
            ano = dados.attrib['ANO']
            if ano == "":
                continue

            if self.__ano_inicio <= int(ano) <= self.__ano_fim:
                self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['ORIENTACOES-CONCLUIDAS']['ORIENTACOES-CONCLUIDAS-PARA-MESTRADO'] += 1

    def __outras_orientacoes_concluidas(self, orientacoes):
        estudantes = orientacoes.findall('OUTRAS-ORIENTACOES-CONCLUIDAS')
        if estudantes is None:
            return

        for estudante in estudantes:
            dados = estudante.find('DADOS-BASICOS-DE-OUTRAS-ORIENTACOES-CONCLUIDAS')
            ano = dados.attrib['ANO']
            if ano == "":
                continue

            if self.__ano_inicio <= int(ano) <= self.__ano_fim:
                natureza = dados.attrib['NATUREZA']
                self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['ORIENTACOES-CONCLUIDAS']['OUTRAS-ORIENTACOES-CONCLUIDAS'][natureza] += 1

    def sumario(self):
        print self.__nome_completo
        print self.__numero_identificador
        print "FORMACAO-ACADEMICA-TITULACAO:        ".decode("utf8") + str(self.__pontuacao['FORMACAO-ACADEMICA-TITULACAO']).encode("utf-8")
        print "PROJETO-DE-PESQUISA:                 ".decode("utf8") + str(self.__pontuacao['PROJETO-DE-PESQUISA']).encode("utf-8")
        print "ARTIGOS-PUBLICADOS:                  ".decode("utf8") + str(self.__artigos).encode("utf-8")

        print "TRABALHOS-COMPLETOS-INTERNACIONAIS:  ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['INTERNACIONAL']['COMPLETO']).encode("utf-8")
        print "TRABALHOS-COMPLETOS-NACIONAIS:       ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['NACIONAL']['COMPLETO']).encode("utf-8")
        print "TRABALHOS-COMPLETOS-REGIONAIS:       ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['REGIONAL']['COMPLETO']).encode("utf-8")
        print "TRABALHOS-COMPLETOS-LOCAIS:          ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['LOCAL']['COMPLETO']).encode("utf-8")
        print "TRABALHOS-COMPLETOS-NAO-INFORMADO:   ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['NAO_INFORMADO']['COMPLETO']).encode("utf-8")

        print "TRABALHOS-EXPANDIDOS-INTERNACIONAIS: ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['INTERNACIONAL']['RESUMO_EXPANDIDO']).encode("utf-8")
        print "TRABALHOS-EXPANDIDOS-NACIONAIS:      ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['NACIONAL']['RESUMO_EXPANDIDO']).encode("utf-8")
        print "TRABALHOS-EXPANDIDOS-REGIONAIS:      ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['REGIONAL']['RESUMO_EXPANDIDO']).encode("utf-8")
        print "TRABALHOS-EXPANDIDOS-LOCAIS:         ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['LOCAL']['RESUMO_EXPANDIDO']).encode("utf-8")
        print "TRABALHOS-EXPANDIDOS-NAO-INFORMADO:  ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['NAO_INFORMADO']['RESUMO_EXPANDIDO']).encode("utf-8")

        print "TRABALHOS-RESUMOS-INTERNACIONAIS:    ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['INTERNACIONAL']['RESUMO']).encode("utf-8")
        print "TRABALHOS-RESUMOS-NACIONAIS:         ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['NACIONAL']['RESUMO']).encode("utf-8")
        print "TRABALHOS-RESUMOS-REGIONAIS:         ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['REGIONAL']['RESUMO']).encode("utf-8")
        print "TRABALHOS-RESUMOS-LOCAIS:            ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['LOCAL']['RESUMO']).encode("utf-8")
        print "TRABALHOS-RESUMOS-NAO-INFORMADO:     ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['TRABALHOS-EM-EVENTOS']['NAO_INFORMADO']['RESUMO']).encode("utf-8")

        print "LIVROS-PUBLICADOS:                   ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['LIVROS-E-CAPITULOS']['LIVRO-PUBLICADO-OU-ORGANIZADO']['LIVRO_PUBLICADO']).encode("utf-8")
        print "LIVROS-ORGANIZADOS:                  ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['LIVROS-E-CAPITULOS']['LIVRO-PUBLICADO-OU-ORGANIZADO']['LIVRO_ORGANIZADO_OU_EDICAO']).encode("utf-8")
        print "CAPITULO-DE-LIVRO-PUBLICADO:         ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['LIVROS-E-CAPITULOS']['CAPITULO-DE-LIVRO-PUBLICADO']).encode("utf-8")

        print "TRADUCOES:                           ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-BIBLIOGRAFICA']['DEMAIS-TIPOS-DE-PRODUCAO-BIBLIOGRAFICA']['TRADUCAO']).encode("utf-8")

        print "SOFTWARES:                           ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-TECNICA']['SOFTWARE']).encode("utf-8")
        print "PATENTES-DEPOSITADAS:                ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-TECNICA']['PATENTE']['DEPOSITADA']).encode("utf-8")
        print "PATENTES-CONCEDIDAS:                 ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-TECNICA']['PATENTE']['CONCEDIDA']).encode("utf-8")
        print "PRODUTOS-TECNOLOGICOS:               ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-TECNICA']['PRODUTO-TECNOLOGICO']).encode("utf-8")
        print "PROCESSOS-OU-TECNICAS:               ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-TECNICA']['PROCESSOS-OU-TECNICAS']).encode("utf-8")
        print "TRABALHOS-TECNICOS:                  ".decode("utf8") + str(self.__tabela_de_qualificacao['PRODUCAO-TECNICA']['TRABALHO-TECNICO']).encode("utf-8")

        print "APRESENTACAO-DE-OBRA-ARTISTICA:      ".decode("utf8") + str(self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['PRODUCAO-ARTISTICA-CULTURAL']['APRESENTACAO-DE-OBRA-ARTISTICA']).encode("utf-8")
        print "COMPOSICAO-MUSICAL:                  ".decode("utf8") + str(self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['PRODUCAO-ARTISTICA-CULTURAL']['COMPOSICAO-MUSICAL']).encode("utf-8")
        print "OBRA-DE-ARTES-VISUAIS:               ".decode("utf8") + str(self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['PRODUCAO-ARTISTICA-CULTURAL']['OBRA-DE-ARTES-VISUAIS']).encode("utf-8")


        print "ORIENTACOES-PARA-POS-DOUTORADO:      ".decode("utf8") + str(self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['ORIENTACOES-CONCLUIDAS']['ORIENTACOES-CONCLUIDAS-PARA-POS-DOUTORADO']).encode("utf-8")
        print "ORIENTACOES-PARA-DOUTORADO:          ".decode("utf8") + str(self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['ORIENTACOES-CONCLUIDAS']['ORIENTACOES-CONCLUIDAS-PARA-DOUTORADO']).encode("utf-8")
        print "ORIENTACOES-PARA-MESTRADO:           ".decode("utf8") + str(self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['ORIENTACOES-CONCLUIDAS']['ORIENTACOES-CONCLUIDAS-PARA-MESTRADO']).encode("utf-8")

        print "ORIENTACOES-DE-ESPECIALIZACAO:       ".decode("utf8") + str(self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['ORIENTACOES-CONCLUIDAS']['OUTRAS-ORIENTACOES-CONCLUIDAS']['MONOGRAFIA_DE_CONCLUSAO_DE_CURSO_APERFEICOAMENTO_E_ESPECIALIZACAO']).encode("utf-8")
        print "ORIENTACOES-DE-TCC:                  ".decode("utf8") + str(self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['ORIENTACOES-CONCLUIDAS']['OUTRAS-ORIENTACOES-CONCLUIDAS']['TRABALHO_DE_CONCLUSAO_DE_CURSO_GRADUACAO']).encode("utf-8")
        print "ORIENTACOES-DE-INICIACAO-CIENTIFICA: ".decode("utf8") + str(self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['ORIENTACOES-CONCLUIDAS']['OUTRAS-ORIENTACOES-CONCLUIDAS']['INICIACAO_CIENTIFICA']).encode("utf-8")
        print "ORIENTACOES-DE-OUTRA-NATUREZA:       ".decode("utf8") + str(self.__tabela_de_qualificacao['OUTRA-PRODUCAO']['ORIENTACOES-CONCLUIDAS']['OUTRAS-ORIENTACOES-CONCLUIDAS']['ORIENTACAO-DE-OUTRA-NATUREZA']).encode("utf-8")

        print ''


def main():
    # Define program arguments
    parser = argparse.ArgumentParser(description="Computes scores from Lattes curricula.")
    parser.add_argument('area', metavar='AREA', type=str, nargs=1,
        help="specify Qualis Periodicos area")
    parser.add_argument('istream', metavar='FILE', type=argparse.FileType('r'), default=sys.stdin,
        help="XML file containing a Lattes curriculum")
    parser.add_argument('-v', '--verbose', action='count',
        help="explain what is being done")
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('-p', '--qualis-periodicos', dest='qualis_periodicos_year', default=2015, metavar='YYYY', type=int, nargs=1,
        help="employ Qualis Periodicos from year YYYY")
    parser.add_argument('-s', '--since-year', dest='since', default=-1, metavar='YYYY', type=int, nargs=1,
        help="consider academic productivity since year YYYY")
    parser.add_argument('-u', '--until-year', dest='until', default=date.today().year, metavar='YYYY', type=int, nargs=1,
        help="consider academic productivity until year YYYY")

    # Process arguments
    args = parser.parse_args()

    tree = ET.parse(args.istream)
    root = tree.getroot()
    score = Score(root, args.since[0], args.until[0])
    score.sumario()

# Main
if __name__ == "__main__":
    sys.exit(main())
