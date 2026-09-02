Option Compare Database
Option Explicit
Public varCmdSQl As String
Public varUsuarioLogado As Long
Public varCEP As String
Global varValorFGTSJAM As Double
Global varFuncionario As Integer
Global i As Integer

Function fncVersao() As String
    fncVersao = "01.07.2023"
End Function
Function fncAcesso(lngNumeroDoObjeto As Long, Optional MensagemAcesso As String = "Sim") As Integer
On Error GoTo Err_Acesso

    Dim rstAcesso As DAO.Recordset
    Set rstAcesso = CurrentDb.OpenRecordset("SELECT tblUsuario.UsuarioID, tblUsuarioObjeto.ObjetoID, tblUsuarioObjeto.Acesso, tblObjeto.Nome, tblObjeto.TipoObjetoID FROM (tblUsuario INNER JOIN tblUsuarioObjeto ON tblUsuario.UsuarioID = tblUsuarioObjeto.UsuarioID) INNER JOIN tblObjeto ON tblUsuarioObjeto.ObjetoID = tblObjeto.ObjetoID WHERE (((tblUsuario.UsuarioID)=" & fncUsuarioLogado & "));")
    Do While Not rstAcesso!ObjetoID = lngNumeroDoObjeto
        rstAcesso.MoveNext
    Loop
        fncAcesso = rstAcesso!Acesso
If fncAcesso = -1 Then
    Exit Function
Else
Err_Acesso:
    If MensagemAcesso = "Não" Then
       Exit Function
    End If
    
    'O erro número 3021 é quando não existe o registro no RecordSet
    'Acesso = 0 é quando não existe permissão na tabela
    If Err.Number = 3021 Or fncAcesso = 0 Then
        fncAcesso = 0
        If lngNumeroDoObjeto = 227 Or lngNumeroDoObjeto = 229 Then
        Else
            MsgBox "O usuário atual não tem permissão para prosseguir !", vbCritical, "Acesso Negado"
        End If

        'Registra na tabela Log o usuário que tentou acessar o objeto
        Dim rstObjeto As DAO.Recordset
        Set rstObjeto = CurrentDb.OpenRecordset("tblObjeto")
        Do While Not rstObjeto!ObjetoID = lngNumeroDoObjeto
            rstObjeto.MoveNext
        Loop
                
        Select Case rstObjeto!TipoObjetoID
        Case 2 'Formulário
            fncFechar (rstObjeto!Nome)
        Case 3 'Relatório
            DoCmd.Close acReport, rstObjeto!Nome
        End Select
        rstObjeto.Close
'        varFuncaoInterna = fncInserirLog(5, "Acesso negado", lngNumeroDoObjeto)
    Else
        fncTratamentoDeErro (lngNumeroDoObjeto)
    End If
End If
'Códigos    0 = Acesso Negado   -1 = Acesso Liberado
End Function
Function fncLogOff(lngNumeroDoObjeto As Long)
On Error GoTo TratarErro
    Dim noForms As Integer, cont As Integer

    noForms = Forms.Count
    Do Until noForms = 0
        noForms = noForms - 1
        If Forms(noForms).Name <> "frmLogin" Then
            DoCmd.Close acForm, Forms(noForms).Name
        End If
    Loop
        
    DoCmd.OpenForm "frmLogin", acNormal
    varUsuarioLogado = 0
    fncValidaEfacacess
    DoCmd.SetWarnings False
    DoCmd.RunSQL ("UPDATE tblLogin IN 'c:\sk\efacacess.erp' SET FuncionarioID = 0 ;")
    DoCmd.SetWarnings True
Exit Function
TratarErro:
    fncTratamentoDeErro
End Function
Function fncNomeUsuarioLogado(Optional UsuarioID As String) As String
On Error GoTo TratarErro
Dim rstFuncionario As DAO.Recordset
    If UsuarioID <> "" Then
        Set rstFuncionario = CurrentDb.OpenRecordset("SELECT * FROM tblUsuario where UsuarioID=" & CInt(UsuarioID))
            If rstFuncionario.RecordCount > 0 Then
                fncNomeUsuarioLogado = rstFuncionario!Nome
            End If
        rstFuncionario.Close
    Else
        Set rstFuncionario = CurrentDb.OpenRecordset("tblUsuario")
        Do While Not rstFuncionario!UsuarioID = fncUsuarioLogado
            rstFuncionario.MoveNext
        Loop
        fncNomeUsuarioLogado = rstFuncionario!NomeUsuario
        rstFuncionario.Close
    End If
Exit Function
TratarErro:
    fncTratamentoDeErro
End Function
Function fncUsuarioLogado() As Long
On Error GoTo TratarErro
    If varUsuarioLogado = 0 Then
        'Busca o usuário no efaccess.erp
        Dim varBancoDestino As Database
        Dim rstLogin As DAO.Recordset
        Set varBancoDestino = DBEngine.Workspaces(0).OpenDatabase("c:\sk\efacacess.erp")
        Set rstLogin = varBancoDestino.OpenRecordset("SELECT * FROM tblLogin")
        fncUsuarioLogado = rstLogin!FuncionarioID
    Else
        fncUsuarioLogado = varUsuarioLogado
    End If
TratarErro:
    fncTratamentoDeErro
End Function
Function fncValidaEfacacess() As Byte
On Error GoTo TratarErro
    Dim varBancoDestino As Database
    Dim varNamePath As String
    Dim varDatalimite As String
    Dim varDataAtual As String
    Dim QtdAcesso As Integer
    
    varNamePath = "c:\sk\efacacess.erp"
    
    varFuncaoInterna = Dir(varNamePath, vbArchive) 'Localiza se existe esse arquivo, caso contrario retorna o nome do arquivo mais proximo
    If "efacacess.erp" <> varFuncaoInterna Then
        'Se não existe o arquivo cria o efacacess
        Set varBancoDestino = DBEngine.Workspaces(0).CreateDatabase(varNamePath, dbLangGeneral, dbVersion30)
        'Criar a tabela tblLogin
        varBancoDestino.Execute ("CREATE TABLE tblLogin ( FuncionarioID LONG,CONSTRAINT CHAVEPRIMARIA PRIMARY KEY(FuncionarioID), SistemaID Long, DataValidade Date);")
        'Insere um registro qualquer
        varBancoDestino.Execute ("INSERT INTO tbllogin ( FuncionarioID, SistemaID, DataValidade) Values (1,1,'10/05/2024');")
        varBancoDestino.Close
'        varFuncaoInterna = fncInserirLog(7, "Arquivo de login criado com sucesso!", 1)
        
    End If

    Dim rstLogin As DAO.Recordset
    Set varBancoDestino = DBEngine.Workspaces(0).OpenDatabase("c:\sk\efacacess.erp")
    Set rstLogin = varBancoDestino.OpenRecordset("SELECT * FROM tblLogin")
    varDatalimite = rstLogin!DataValidade
    rstLogin.Close
    Set rstLogin = Nothing
    varBancoDestino.Close
    Set varBancoDestino = Nothing
    
    varDataAtual = Date
    QtdAcesso = DateDiff("D", varDataAtual, varDatalimite)
    If QtdAcesso < 5 Then
       Kill "c:\sk\efacacess.erp"
       MsgBox "Sistema Desatualizado!!! Ligue para (11)99603-6559", vbInformation + vbCritical
       fncSair
    End If

TratarErro:
    fncTratamentoDeErro
End Function
