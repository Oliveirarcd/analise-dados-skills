# Qualidade e limpeza de dados

## Sumário
1. Leitura segura
2. O que o perfil precisa responder
3. Problemas comuns e tratamento
4. Padrões brasileiros
5. Registro de tratamento

## 1. Leitura segura

- Inspecione tamanho e esquema antes de carregar tudo: `pd.read_csv(..., nrows=1000)`, `pyarrow.parquet.read_schema`, `openpyxl.load_workbook(read_only=True)`.
- Leia tudo como texto (`dtype=str`) e tipe depois, coluna a coluna. Assim códigos como `00123`, CNPJ e CEP não perdem zeros e datas não viram mês/dia trocados. É o que `io_br.read_table` faz.
- Excel: confira abas, linhas de cabeçalho deslocadas, células mescladas, totais embutidos no meio da tabela e linhas de rodapé ("Total geral"). Remova-os explicitamente e registre.
- Nunca altere o arquivo original. Trabalhe em cópia e grave saídas em pasta separada.

## 2. O que o perfil precisa responder

| Pergunta | Como verificar |
|---|---|
| O que é uma linha? | chave candidata única e sem nulos (`perfil.py` lista) |
| Há duplicatas? | linhas idênticas e chave repetida, separadamente |
| Os tipos estão certos? | números guardados como texto, datas como texto, códigos como número |
| Quanto falta? | % de nulos por coluna e por período (ausência concentrada em um mês é sinal de carga falha) |
| Os valores fazem sentido? | mínimo/máximo, negativos onde não deveria, datas no futuro, outliers por IQR |
| As categorias são consistentes? | grafias diferentes ("SP", "sp ", "São Paulo"), espaços nas pontas |
| Há colunas redundantes? | correlação ≥ 0,95 entre numéricas, colunas constantes |
| O volume bate? | contagem e soma comparadas com o relatório de origem |

## 3. Problemas comuns e tratamento

- **Duplicatas exatas:** remova e registre a quantidade. **Duplicatas de chave com conteúdo diferente:** não escolha uma ao acaso; defina a regra (registro mais recente, maior versão, status válido) e mostre exemplos ao usuário.
- **Nulos:** entenda o mecanismo antes de imputar. "Não se aplica", "não informado" e "zero" são coisas diferentes. Em análise descritiva, prefira mostrar a lacuna; em modelo, impute dentro do pipeline de treino e crie indicador de ausência quando a falta for informativa.
- **Outliers:** classifique em erro (valor impossível: idade 230, data 1900), evento real (Black Friday) ou cauda natural. Só o primeiro é corrigido ou excluído; os outros pedem métodos robustos (mediana, quantis, transformação log) ou análise separada.
- **Texto:** `strip`, normalização de caixa e acentos só em colunas de chave/categoria, nunca em texto livre que será lido. Mantenha a coluna original ao lado da normalizada.
- **Datas:** fixe o fuso (`America/Sao_Paulo` quando aplicável), cuidado com horário de verão em dados antigos, e decida se o evento é por data de competência ou de caixa.
- **Unidades e moeda:** padronize antes de somar (kg × g, R$ × US$, milhar × unidade). Deixe explícita a cotação usada.

## 4. Padrões brasileiros

- CSV de Excel em português costuma vir com `;` como separador, vírgula decimal, ponto de milhar e codificação cp1252.
- `1.234` é ambíguo: em dados brasileiros costuma ser mil duzentos e trinta e quatro. `io_br` trata como decimal se toda a coluna tiver o formato `n.nnn` sem vírgula em lugar nenhum; confira o perfil e use `--texto` ou converta à mão quando a coluna for de milhar.
- CPF/CNPJ: guarde como texto com 11/14 dígitos (`str.zfill`), valide dígito verificador quando a análise depender da identidade. Não exponha CPF em relatórios; use chave substituta.
- Datas `dd/mm/aaaa` sempre com `dayfirst=True`.

## 5. Registro de tratamento

Toda regra aplicada vira uma linha: etapa, regra, linhas afetadas, motivo. O relatório final mostra o funil "recebidas → válidas → usadas". Sem isso, ninguém consegue reproduzir ou contestar o resultado.
