# Gestão de Benefícios — DP/RH (Grupo LLE)

Sistema do setor de **DP/RH** para apurar o **Vale Alimentação** (prêmio por
assiduidade) e gerar a planilha da operadora (**Sodexo**).

A partir do **cadastro de funcionários** (faixa de alimentação 1–13), das
planilhas de **faltas** e **atestados**, calcula quanto cada funcionário recebe
— do integral (100%) até zerado — e preenche o modelo da Sodexo.

Construído sobre o mesmo esqueleto dos projetos LLE Acordos e LLE Protestos.

## Como rodar
```bash
pip install -r requirements.txt
streamlit run app.py
```
O **primeiro usuário** cadastrado vira **Gestão de RH** automaticamente.

## Cargos
| Cargo | O que faz |
|---|---|
| **Gestão de RH** | Tudo + gerenciar usuários + excluir (com senha) |
| **Analista de RH** | Tudo operacional + excluir (com senha) — não gerencia usuários |
| **Diretoria** | Só visualiza |

## Fluxo
1. **👥 Funcionários** — importa o cadastro do Sankhya (faixa de alimentação + carga horária).
2. **📤 Modelo Sodexo** — guarda a planilha-base da operadora (atualize quando entra/sai funcionário).
3. **⚙️ Processar** — cria o processo do mês, sobe **faltas**, **atestados** e **férias (PDF)**, revisa faltas e férias (marca/desmarca) e calcula.
4. **📁 Processos** — gera a planilha Sodexo (pede as 3 datas), baixa o resultado e exclui (com senha).
5. **🏠 Início** — dashboard com distribuição do prêmio, valor por faixa e tendência mensal.

## Regras do cálculo (definidas pelo RH)
- **Valor base** = valor da faixa de alimentação (1–13). Faixa 13 = R$ 0 (sem direito).
- **Ligação entre planilhas**: matrícula do Pontotel = "1" + Código do Sankhya
  (tira-se o "1"); confirmação por CPF. (Testado: faltas 157/157, atestados 14/14.)
- **Faltas** = dias de falta cheia (planilha de faltas). **Atraso** = soma dos minutos do período.
- **Desconto** = o **pior** (maior) entre faltas e atraso:
  - 1 falta **ou** 30 min → 50%
  - 2 faltas **ou** 1h → 75%
  - 3 faltas **ou** 1h30 → 100% (zera)
- **Atestado**: **qualquer atestado ZERA** o mês (100%), com ou sem número de dias
  (inclui auxílio-doença, INSS e acidente de trabalho, que vêm sem dias). É automático,
  sem opção de marcação. Na Sodexo, escreve "Atestado" ao lado (Férias tem prioridade).
- **Revisão manual (só faltas)**: o sistema mostra para seleção apenas quem tem
  **30 min de atraso ou mais** (ou falta de dia) — atrasos menores não descontam,
  então ficam ocultos. Desmarcado = recebe integral. Atestado é automático.
- **Férias**: quem está de férias (e mantido marcado na revisão) tem o benefício
  **zerado** no mês. Desmarcado = recebe normalmente. Lido do PDF 'Gozo de Férias
  no Mês' do Sankhya.
- **Exceções** (valor fora da tabela de faixas, ex. diretoria/sócios): mantém o
  valor que está na planilha Sodexo, sem recalcular nem descontar — inclusive se
  a pessoa estiver de férias ("tratar sempre o diferente dessa maneira").

## Planilha da Sodexo (saída)
- Mexe só na aba **"Dados dos Beneficiários-Cartão"** e só na coluna **Valor crédito**.
- Antes de gerar, pede **Data de crédito**, **Data de entrega** e **Mês de referência**.
- **Zerados** ficam em **vermelho**. Ao lado: "**Férias**" para quem zerou por férias e "**Atestado**" para quem zerou por atestado (férias tem prioridade).
- A planilha-base fica **guardada** (Opção C): usa a guardada ou sobe uma atualizada na hora.

## ⚠️ Observações honestas (para o RH validar)
1. **Atraso somado no mês**: pela regra (somar minutos no período), muita gente
   atinge 1h30 e seria zerada. Na planilha de validação real quase ninguém foi
   zerado por atraso — o que se resolve na **revisão manual** (você desmarca esses
   casos). Se a intenção for atraso **por dia** (e não somado no mês), é um ajuste
   simples em `src/servicos/calculo_beneficio.py`.
2. **Atestados "indeterminados"** (auxílio-doença/INSS/acidente, sem nº de dias):
   não inventamos dias — eles são **sinalizados** nos avisos para conferência do RH.
3. **Admissões novas**: beneficiários que estão na Sodexo mas ainda não no cadastro
   ficam com o valor que já estava na planilha, e o sistema avisa.

## Banco em produção
Sem configuração usa SQLite local. Para Postgres (Neon/Supabase/…), cole a
connection string nos Secrets em `[postgres]`. As migrations rodam sozinhas.

## Dashboard
- KPIs do mês + **comparativo mês a mês** (líquido, zerados, descontos com variação).
- **Indicador por departamento** (coluna "Descrição (Departamentos)" do cadastro) com evolução vs mês anterior.
- **Evolução por funcionário**: quem subiu, caiu, entrou ou saiu em relação ao mês anterior.

## Desempenho (Postgres/Neon)
O sistema é otimizado para banco na nuvem:
- A conexão é reaproveitada por thread e só reconecta quando realmente cai
  (sem "ping" a cada operação).
- Uploads e cálculo gravam **em lote** (um único comando para centenas de linhas)
  em vez de linha por linha — o que reduz muito a latência no Neon.
- O dashboard consolida os indicadores em poucas consultas.
- Operações longas mostram um indicador de "processando…".

Dica Neon: use sempre a connection string **pooled** (host com `-pooler`).
