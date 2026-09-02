Option Compare Database
Option Explicit
Dim varRst As DAO.Recordset
Public NomeEmpresa As String
Public CurrentStatusMsg
Function fncAbrirFormulario(NomeFormulario As String, Optional Condicao As String)
On Error GoTo TratarErro
    If Condicao <> "" Then
        DoCmd.OpenForm NomeFormulario, acNormal, , Condicao
    Else
        DoCmd.OpenForm NomeFormulario, acNormal
    End If
TratarErro:
    fncTratamentoDeErro
End Function
'Sub fncSelecionarItem(Tabela As String, CampoCodigo As String, CampoDescricao As String, CampoSelecionar As String, Rotulo As String, Optional Condicao As String)
'On Error GoTo TratarErro
'
'    fncAbrirFormulario "frmSelecionar"
'    If Condicao <> Empty Then
'        Form_frmSelecionar.Form.RecordSource = "SELECT " & CampoCodigo & " AS CodigoItem, " & CampoDescricao & " AS DescricaoItem, " & CampoSelecionar & " AS SelecionarItem FROM " & Tabela & " WHERE " & Condicao
'        Form_frmSelecionar.Form.txtCondicao = Condicao
'    Else
'        Form_frmSelecionar.Form.RecordSource = "SELECT " & CampoCodigo & " AS CodigoItem, " & CampoDescricao & " AS DescricaoItem, " & CampoSelecionar & " AS SelecionarItem FROM " & Tabela
'    End If
'    Form_frmSelecionar.rotuloNomeDoFormulario.Caption = "Selecionar " & Rotulo
'    Form_frmSelecionar.txtNomeTabela = Tabela
'    Form_frmSelecionar.Refresh
'
'TratarErro:
'    fncTratamentoDeErro
'End Sub
Function fncRetornarCampoConfiguracao(Campo As String) As Variant
On Error GoTo TratarErro
Dim varRstConf As DAO.Recordset
    Set varRstConf = CurrentDb.OpenRecordset("tblConfiguracao")
        fncRetornarCampoConfiguracao = varRstConf(Campo)
        varRstConf.Close
TratarErro:
    fncTratamentoDeErro
End Function
Function fncNomeBanco(CodigoBanco As Integer) As String
'Dim varRst As DAO.Recordset
    fncNomeBanco = ""
    Set varRst = CurrentDb.OpenRecordset("SELECT Nome FROM tblBanco WHERE BancoID = " & CodigoBanco)
        If varRst.RecordCount > 0 Then
            fncNomeBanco = varRst("Nome")
        End If
        varRst.Close
End Function
Function fncRetornarCampoTabela(Tabela As String, Campo As String, Optional Criterio As String) As Variant
On Error GoTo TratarErro
Dim varRstCT As DAO.Recordset
    If Criterio <> "" Then
        Set varRstCT = CurrentDb.OpenRecordset("SELECT * FROM " & Tabela & " WHERE " & Criterio)
    Else
        Set varRstCT = CurrentDb.OpenRecordset("SELECT * FROM " & Tabela)
    End If
    
    If varRstCT.RecordCount > 0 Then
        fncRetornarCampoTabela = IIf(IsNull(varRstCT(Campo)), 0, varRstCT(Campo))
    Else
        fncRetornarCampoTabela = -1
    End If
    
    varRstCT.Close
TratarErro:
   fncTratamentoDeErro
End Function
Function fncVerificarSeCodigoFuncionarioJaCadastrado(FuncionarioID As Integer, EmpresaID As Integer) As Boolean
On Error GoTo TratarErro
Dim varRstFuncionario As DAO.Recordset
    Set varRstFuncionario = CurrentDb.OpenRecordset("SELECT FuncionarioID FROM tblFuncionario WHERE FuncionarioID = " & FuncionarioID & " AND EmpresaID = " & EmpresaID)
    If varRstFuncionario.RecordCount > 0 Then
        fncVerificarSeCodigoFuncionarioJaCadastrado = True
    Else
        fncVerificarSeCodigoFuncionarioJaCadastrado = False
    End If
    varRstFuncionario.Close
TratarErro:
    fncTratamentoDeErro
End Function
Function fncVerificarSeCodigoEmpresaJaCadastrado(EmpresaID As Integer) As Boolean
On Error GoTo TratarErro
Dim varRstEmpresa As DAO.Recordset

    Set varRstEmpresa = CurrentDb.OpenRecordset("SELECT EmpresaID FROM tblEmpresa WHERE EmpresaID = " & EmpresaID)
    If varRstEmpresa.RecordCount > 0 Then
        fncVerificarSeCodigoEmpresaJaCadastrado = True
    Else
        fncVerificarSeCodigoEmpresaJaCadastrado = False
    End If
    varRstEmpresa.Close
TratarErro:
    fncTratamentoDeErro
End Function

Function fncNomeDaEmpresa() As String
Dim varRstNomeDaEmpresa As DAO.Recordset
    Set varRstNomeDaEmpresa = CurrentDb.OpenRecordset("tblConfiguracao")
        fncNomeDaEmpresa = varRstNomeDaEmpresa!RazaoSocial
    varRstNomeDaEmpresa.Close
End Function
Function fncMensagemBarraStatus(MensagemBarra As String)
    If MensagemBarra <> CurrentStatusMsg Then
        ' Testa se já existe uma mensagem na Statusbar.
        Dim ret As Variant
        ret = SysCmd(acSysCmdSetStatus, MensagemBarra)
        'StatusCalled = True
        CurrentStatusMsg = MensagemBarra
    End If
End Function
Function fncRetornarTipoDeReciboSelecionado() As String
On Error GoTo TratarErro
Dim varRstTipoRecibo As DAO.Recordset
Dim i As Integer
Dim varTipoRecibo As String

    Set varRstTipoRecibo = CurrentDb.OpenRecordset("SELECT * from tblTabelaItem WHERE TabelaID =9 AND Selecionar = true")
    If varRstTipoRecibo.RecordCount > 0 Then
        varRstTipoRecibo.MoveLast
        varRstTipoRecibo.MoveFirst
        For i = 1 To varRstTipoRecibo.RecordCount
            varTipoRecibo = varTipoRecibo & varRstTipoRecibo!Descricao & ", "
            varRstTipoRecibo.MoveNext
        Next
    End If
    varRstTipoRecibo.Close
    
    fncRetornarTipoDeReciboSelecionado = Mid(varTipoRecibo, 1, Len(varTipoRecibo) - 2)

TratarErro:
    fncTratamentoDeErro
End Function
