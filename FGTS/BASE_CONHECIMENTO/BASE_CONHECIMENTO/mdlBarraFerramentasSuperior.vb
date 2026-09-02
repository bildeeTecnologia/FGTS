Option Compare Database
Option Explicit
Function fncAbrirValeTransporteTipo()
On Error GoTo TratarErro
    DoCmd.OpenForm "frmTabelaitem", acNormal, , "[TabelaID] = " & 27
    Forms![frmTabelaItem]![textoNumeroDaTabela] = 27
    Forms![frmTabelaItem]![rotuloNomeDoFormulario].Caption = "Vale Transporte Tipo"
TratarErro:
    fncTratamentoDeErro
End Function
Function fncAbrirTipoDeEPI()
On Error GoTo TratarErro
    DoCmd.OpenForm "frmTabelaitem", acNormal, , "[TabelaID] = " & 29
    Forms![frmTabelaItem]![textoNumeroDaTabela] = 29
    Forms![frmTabelaItem]![rotuloNomeDoFormulario].Caption = "Tipos de EPI's"
TratarErro:
    fncTratamentoDeErro
End Function
Function fncAbrirAditivo()
On Error GoTo TratarErro
    DoCmd.OpenForm "frmTabelaitem", acNormal, , "[TabelaID] = " & 32
    Forms![frmTabelaItem]![textoNumeroDaTabela] = 32
    Forms![frmTabelaItem]![rotuloNomeDoFormulario].Caption = "Opções de Termo Aditivo"
TratarErro:
    fncTratamentoDeErro
End Function

Function fncAbrirSindicato()
On Error GoTo TratarErro
    DoCmd.OpenForm "frmTabelaitem", acNormal, , "[TabelaID] = " & 12
    Forms![frmTabelaItem]![textoNumeroDaTabela] = 12
    Forms![frmTabelaItem]![rotuloNomeDoFormulario].Caption = "Tipos de Sindicato"
TratarErro:
    fncTratamentoDeErro
End Function
Function fncFeriados()
On Error GoTo TratarErro
    DoCmd.OpenForm "frmTabelaFeriados", acNormal
TratarErro:
    fncTratamentoDeErro
End Function
Function fncAbrirRacaCor()
On Error GoTo TratarErro
    DoCmd.OpenForm "frmTabelaitem", acNormal, , "[TabelaID] = " & 2
    Forms![frmTabelaItem]![textoNumeroDaTabela] = 2
    Forms![frmTabelaItem]![rotuloNomeDoFormulario].Caption = "Raça / Cor"
TratarErro:
    fncTratamentoDeErro
End Function
Function fncAbrirNacionalidade()
On Error GoTo TratarErro
    DoCmd.OpenForm "frmTabelaitem", acNormal, , "[TabelaID] = " & 4
    Forms![frmTabelaItem]![textoNumeroDaTabela] = 4
    Forms![frmTabelaItem]![rotuloNomeDoFormulario].Caption = "Nacionalidade"
TratarErro:
    fncTratamentoDeErro
End Function
Function fncAbrirGrauParentesco()
On Error GoTo TratarErro
    DoCmd.OpenForm "frmTabelaitem", acNormal, , "[TabelaID] = " & 8
    Forms![frmTabelaItem]![textoNumeroDaTabela] = 8
    Forms![frmTabelaItem]![rotuloNomeDoFormulario].Caption = "Grau Parentesco"
TratarErro:
    fncTratamentoDeErro
End Function
Function fncAbrirTipoRecebimentoDeEPI()
On Error GoTo TratarErro
    DoCmd.OpenForm "frmTabelaitem", acNormal, , "[TabelaID] = " & 28
    Forms![frmTabelaItem]![textoNumeroDaTabela] = 28
    Forms![frmTabelaItem]![rotuloNomeDoFormulario].Caption = "Tipos de Recebimento de EPI's"
TratarErro:
    fncTratamentoDeErro
End Function
Function fncAbrirTipoBeneficio()
On Error GoTo TratarErro
    DoCmd.OpenForm "frmTabelaitem", acNormal, , "[TabelaID] = " & 10
    Forms![frmTabelaItem]![textoNumeroDaTabela] = 10
    Forms![frmTabelaItem]![rotuloNomeDoFormulario].Caption = "Tipo Benefício"
TratarErro:
    fncTratamentoDeErro
End Function
Function fncAbrirDepartamento()
On Error GoTo TratarErro
    DoCmd.OpenForm "frmDepartamento", acNormal
TratarErro:
    fncTratamentoDeErro
End Function
Function fncAbrirFeriados()
On Error GoTo TratarErro
    DoCmd.OpenForm "frmFeriados", acNormal
TratarErro:
    fncTratamentoDeErro
End Function

