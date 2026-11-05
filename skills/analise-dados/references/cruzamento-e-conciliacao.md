# Cruzamento e conciliação de bases

## Sumário
1. Antes de cruzar
2. Escolha do tipo de junção
3. Chaves sujas e casamento aproximado
4. Conciliação de valores
5. Junções por intervalo e por tempo
6. O que entregar

## 1. Antes de cruzar

Responda, para cada lado: qual é a granularidade, qual é a chave, ela é única, tem nulos? A cardinalidade esperada (1:1, m:1, 1:m, m:m) decide se o resultado pode mudar de tamanho. `cruzar.py` faz esse diagnóstico e trava a junção se a cardinalidade observada contrariar a esperada.

Muitos-para-muitos quase sempre é erro de granularidade. Agregue um dos lados até a granularidade do outro ou crie uma tabela ponte explícita; nunca deixe o produto cartesiano inflar somas.

## 2. Escolha do tipo de junção

| Objetivo | Junção |
|---|---|
| Enriquecer fatos com cadastro | left m:1, cardinalidade travada |
| Ver só o que existe nos dois | inner, mas reporte o que ficou de fora |
| Conciliação (o que falta em cada lado) | outer com indicador de origem |
| Filtrar por existência | semi-junção (`isin`) sem trazer colunas |

## 3. Chaves sujas e casamento aproximado

1. Primeiro normalize de forma determinística: espaços, caixa, acentos, pontuação, zeros à esquerda (`--normalizar`). O diagnóstico mostra quanto isso ganha.
2. Depois, para o que sobrou, gere sugestões aproximadas (`--sugerir-aproximado`; usa `rapidfuzz` se instalado, senão `difflib`). Sugestões são para revisão: monte uma tabela de-para validada pelo usuário e só então aplique.
3. Para nomes de empresas e endereços, combine critérios (nome + município + CNPJ raiz) em vez de confiar só na similaridade de texto.
4. Registre a taxa de casamento por etapa: exato, normalizado, aproximado validado, sem par.

## 4. Conciliação de valores

- Totais antes e depois do cruzamento precisam bater (`--somar valor`). Diferença diferente de zero em left m:1 indica duplicação na direita.
- Para conciliar dois sistemas (ex.: financeiro × operacional), compare por chave: só em A, só em B, nos dois com valor igual, nos dois com valor diferente (diferença absoluta e percentual). Defina tolerância (centavos, arredondamento) antes de olhar o resultado.
- Agregue no nível comum (mês × centro de custo, por exemplo) quando as chaves de linha não conversam, e explique a perda de detalhe.

## 5. Junções por intervalo e por tempo

- **Vigência** (preço válido entre data_inicio e data_fim): junte pela chave e filtre `inicio <= data < fim`; confira sobreposição de vigências antes.
- **Último valor conhecido** (cotação, cadastro na data do evento): `pd.merge_asof(fatos.sort_values('data'), ref.sort_values('data'), on='data', by='chave', direction='backward', tolerance=pd.Timedelta('7D'))`. Nunca use valor posterior ao evento em modelo preditivo.
- **Faixas** (idade → faixa etária, valor → faixa de ticket): `pd.cut` com bordas explícitas e rótulo de inclusão.

## 6. O que entregar

- Arquivo cruzado com coluna `_origem` (ambos / só esquerda / só direita).
- Arquivos de exceção de cada lado.
- Auditoria: linhas por lado, chaves nulas e repetidas, cardinalidade observada, cobertura %, ganho com normalização, reconciliação de totais.
- Na resposta ao usuário: a cobertura em uma frase ("98,7% das vendas encontraram loja; 8 vendas apontam para a loja 9999, que não existe no cadastro").
