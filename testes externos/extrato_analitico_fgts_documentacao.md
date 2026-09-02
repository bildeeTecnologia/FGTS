# Extrato Analítico FGTS — Documentação de Referência

> **Fonte:** Caixa Econômica Federal, SEFIP/eSocial, Circular CEF nº 372/2005, Manual de Orientações FGTS V18, jurisprudência trabalhista (TRT/TST) e respostas oficiais da CEF via Reclame Aqui.  
> **Documento gerado em:** maio/2026  
> **Aplicação:** RegularizaFGTS — análise e regularização de débitos de FGTS

---

## 1. O que é o Extrato Analítico

O Extrato Analítico do Trabalhador é o documento emitido pela Caixa Econômica Federal que apresenta o **histórico completo de movimentações** de uma conta vinculada de FGTS, incluindo depósitos mensais, depósitos rescisórios, saques, rendimentos (JAM), e eventuais reposições ou estornos.

Ele é solicitado via **Conectividade Social** (pelo empregador) ou nas agências da Caixa, e é o principal documento utilizado para auditorias, ações trabalhistas e regularização de débitos de FGTS.

---

## 2. Cabeçalho da Conta (repete a cada página)

| Campo | Descrição |
|---|---|
| **NOME DO TRABALHADOR** | Nome completo do empregado |
| **NUM. CONTA** | Número da conta vinculada FGTS do trabalhador naquele empregador |
| **CAT** | Categoria do trabalhador (ex: `01` = empregado CLT comum) |
| **TX** | Taxa de recolhimento (ex: `3` = jovem aprendiz; `8` = CLT padrão) |
| **PAG** | Paginação — `1/ 5` = página 1 de 5 do extrato daquela conta |
| **PIS/PASEP** | CPF previdenciário do trabalhador |
| **CART. TRAB.** | Número da Carteira de Trabalho |
| **DTA. ADM.** | Data de admissão no empregador |
| **SITUACAO CTA** | Situação da conta — `OPTANTE` indica optante ao FGTS antes de 1988 |
| **OPCAO RETROAT.** | Retroatividade da opção ao FGTS (`00/00/0000` = não há) |
| **MATRICULA** | Matrícula do trabalhador no empregador |
| **INSCRICAO EMPREGADOR** | CNPJ do empregador |
| **BASE DA CONTA** | UF onde a conta foi criada (ex: `SP`) |
| **VALOR BASE PARA FINS RESCISORIOS** | Base de cálculo para a multa rescisória — `0,00*` indica saldo zerado ou sem cálculo pendente |

---

## 3. Campo DATA DE AFAST. e Código de Movimentação

Essa linha aparece no cabeçalho de cada conta e informa o **motivo do desligamento do trabalhador**:

```
DATA DE AFAST.       MATRICULA
14/12/2018 - I1      13509602846
```

- **DATA DE AFAST.** = último dia de vigência do vínculo empregatício
- O código após o traço (ex: `I1`) = **Código de Movimentação FGTS**, informado pelo empregador via SEFIP/eSocial

### Tabela de Códigos de Movimentação

| Código | Significado | Direito ao saque? |
|---|---|---|
| **I1** | Dispensa sem justa causa (também: rescisão indireta, rescisão antecipada de contrato determinado Lei 9.601/98) | Sim — 100% do saldo + multa 40% |
| **I2** | Rescisão por culpa recíproca ou força maior (requer reconhecimento pela Justiça do Trabalho) | Sim — 60% do saldo + multa 20% |
| **I3** | Término de contrato de experiência / prazo determinado (sem direito à multa) | Sim — saldo sem multa |
| **I4** | Dispensa sem justa causa de empregado doméstico | Sim — 100% + multa |
| **I5** | Acordo entre empregado e empregador (demissão consensual — Reforma Trabalhista 2017) | Sim — 80% do saldo + multa 20% |
| **H** | Dispensa por justa causa | Não |
| **J** | Pedido de demissão | Não (exceto aposentado: código 05) |
| **S2** | Falecimento do trabalhador | Sim — liberado para dependentes/herdeiros |
| **S3** | Falecimento por acidente de trabalho | Sim — dependentes/herdeiros |

> **Regra geral:** quando o código de afastamento não é informado ou é informado incorretamente pelo empregador, a Caixa adota automaticamente o código **I1**.

---

## 4. Histórico de Lançamentos

### 4.1. Anatomia de uma linha de lançamento

```
23/01/2023  DEP ATRASO M12/2022 SBPC 10/01/2023    1.400,00
```

| Componente | Conteúdo | Significado |
|---|---|---|
| `23/01/2023` | Data do lançamento | Data em que o valor foi creditado na conta FGTS |
| `DEP ATRASO` | Tipo do lançamento | Depósito realizado **fora do prazo** pelo empregador |
| `M` | Natureza do depósito | Mensal / Rescisório / Verbas (ver tabela 4.2) |
| `12/2022` | Competência | Mês e ano a que o depósito se refere |
| `SBPC 10/01/2023` | Sistema + data de vencimento | Ver explicação na seção 4.3 |
| `1.400,00` | Valor | Valor creditado em reais |

---

### 4.2. Letras de Natureza do Depósito (M, R, V)

| Letra | Nome completo | O que representa |
|---|---|---|
| **M** | **Mensal** | Depósito mensal regular de 8% (ou 3% jovem aprendiz) sobre a remuneração do mês de referência |
| **R** | **Rescisório** | Depósito do FGTS referente ao mês da rescisão do contrato (competência do desligamento) |
| **V** | **Verbas Indenizatórias** | Depósito sobre verbas que integram a base de cálculo do FGTS com natureza indenizatória: aviso prévio indenizado, férias proporcionais, 13º proporcional, etc. |

> **Atenção:** Quando aparece `V 0/ 0 SBPC 0/ 0/ 0`, significa que não há competência mensal definida pois são verbas apuradas no momento da rescisão, sem referência a um mês específico.

---

### 4.3. O que significa SBPC e a data após ele

**SBPC = Sistema de Baixa de Pagamento Complementar**

É o sistema interno da Caixa Econômica Federal que processa depósitos rescisórios e valores em atraso. Indica que o empregador já realizou o depósito, mas a Caixa ainda está validando e efetivando o crédito na conta vinculada do FGTS.

A **data após o SBPC** (ex: `SBPC 10/01/2023`) é a **data de vencimento/processamento** — ou seja, a data limite que o empregador declarou ou negociou para a quitação daquela competência em atraso. Geralmente corresponde ao dia 10 do mês seguinte ao acordado no parcelamento ou autuação.

Quando aparece `SBPC 0/ 0/ 0` significa que não há data de vencimento definida (caso típico de verbas `V`).

---

### 4.4. Tipos de Lançamento — Tabela Completa

| Descrição no extrato | Significado |
|---|---|
| **DEP RESCISOR** | Depósito rescisório feito no ato da demissão (dentro do prazo) |
| **DEP MULTA RE** | Depósito da multa rescisória de 40% sobre o saldo (demissão sem justa causa) |
| **DEP VERBAS I** | Depósito de verbas indenizatórias no ato da rescisão (dentro do prazo) |
| **DEP ATRASO M[MM/AAAA]** | Depósito mensal da competência indicada, recolhido fora do prazo |
| **DEP ATRASO R[MM/AAAA]** | Depósito rescisório da competência indicada, recolhido fora do prazo |
| **DEP ATRASO V 0/0** | Depósito de verbas indenizatórias rescisórias, recolhido fora do prazo |
| **JAM RECOLHIDO PELA** | Juros e Atualização Monetária pagos pelo empregador junto com depósito em atraso |
| **JAM MULTA RESCISORI** | Juros e Atualização Monetária incidentes sobre a multa rescisória paga em atraso |
| **JAM RECOLH VERBAS IND** | JAM incidente sobre verbas indenizatórias pagas em atraso |
| **CREDITO DE JAM** | Crédito mensal de juros e atualização monetária sobre o saldo da conta (rendimento) |
| **AC CRED DIST RESULTADO ANO BA** | Crédito anual da distribuição dos resultados do FGTS (equivale ao dividendo da conta) |
| **SAQUE DEP** | Saque do saldo principal efetuado pelo trabalhador |
| **SAQUE JAM** | Saque dos rendimentos (JAM) acumulados |
| **AC REPOSICAO DEP** | Reposição de saque cancelado/estornado pela Caixa (principal) |
| **AC REPOSICAO JAM** | Reposição de saque cancelado/estornado pela Caixa (juros) |
| **AC AUT JAM CANCELAMENTO SAQUE** | Atualização automática de juros em razão de cancelamento de saque anterior |
| **DEPOSITO EM ATRASO** | Depósito de competência mensal recolhido fora do prazo (forma expandida) |
| **SALDO ANTERIOR** | Saldo transportado de período anterior (início de página) |
| **SALDO A TRANSPORTAR** | Saldo parcial ao final da página, que continua na próxima |
| **TRANSPORTE** | Continuação do saldo da página anterior |

---

## 5. Exemplos Práticos Comentados

### Exemplo 1 — Depósito mensal em atraso
```
23/01/2023  DEP ATRASO M12/2022 SBPC 10/01/2023    1.400,00
```
Em 23/01/2023 foi creditado na conta o depósito **mensal** da competência **dezembro/2022**, recolhido em atraso pelo empregador. O vencimento negociado/declarado era **10/01/2023**.

---

### Exemplo 2 — Depósito rescisório em atraso
```
17/04/2019  DEP ATRASO R12/2018 SBPC 10/04/2019      257,59
```
Depósito **rescisório** da competência **dezembro/2018**, creditado com atraso em 17/04/2019. O prazo negociado era 10/04/2019.

---

### Exemplo 3 — Verbas indenizatórias em atraso
```
17/04/2019  DEP ATRASO V 0/ 0 SBPC 0/ 0/ 0           230,09
```
Depósito de **verbas indenizatórias** (aviso prévio, 13º, férias proporcionais) da rescisão, recolhido em atraso. Sem competência mensal definida.

---

### Exemplo 4 — Depósito rescisório no prazo (no ato da demissão)
```
21/12/2018  DEP RESCISOR12/2018 SBPC 10/01/2019       212,28
21/12/2018  DEP MULTA RE12/2018 SBPC 10/01/2019       959,28
21/12/2018  DEP VERBAS I 0/ 0 SBPC 0/ 0/ 0            201,82
```
Rescisão processada em 21/12/2018 com depósito do FGTS rescisório, multa de 40% e verbas indenizatórias, todos dentro do prazo legal (vencimento 10/01/2019).

---

## 6. Sinais de Irregularidade — Relevância para Auditoria

A presença de `DEP ATRASO` em qualquer competência é evidência direta de que o empregador **não recolheu o FGTS dentro do prazo legal** (até o dia 20 do mês seguinte à competência), o que configura:

- Débito de FGTS em atraso
- Incidência de **multa e juros** sobre o valor em aberto
- Possível inscrição na **Dívida Ativa da União** se não regularizado
- Passivo trabalhista e previdenciário para o empregador

> O acúmulo de lançamentos `DEP ATRASO` ao longo do extrato indica padrão sistemático de inadimplência, e não casos isolados — o que agrava a situação perante a fiscalização.

---

*Documentação elaborada com base em fontes oficiais: Caixa Econômica Federal, Circular CEF nº 372/2005, Manual de Orientações FGTS V18, respostas oficiais da CEF e jurisprudência trabalhista.*
