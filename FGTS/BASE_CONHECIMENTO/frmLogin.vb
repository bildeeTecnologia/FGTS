Option Compare Database
Option Explicit
Private Sub btnFechar_Click()
    fncSair
End Sub
Private Sub btnOk_Click()
On Error GoTo TratarErro
'Verifica se a senha está correta
If Me.textoSenhaDigitada = Me.cmbFuncionario.Column(2) Then
'    If Me.txtCompetência <> Empty Then
        varUsuarioLogado = Me.cmbFuncionario
        
        'Grava no efacacess.erp o usuário logado
        varFuncaoInterna = fncValidaEfacacess
        DoCmd.SetWarnings False
        DoCmd.RunSQL ("UPDATE tblLogin IN 'c:\sk\efacacess.erp' SET FuncionarioID = " & varUsuarioLogado & " ;")
        DoCmd.SetWarnings True
        If fncRetornarCampoConfiguracao("DataVersao") <> fncVersao Then
        DoCmd.SetWarnings False
        DoCmd.RunSQL ("UPDATE tblConfiguracao SET DataVersao = '" & "01.08.2019" & "';")
        DoCmd.SetWarnings True
        
            If MsgBox("Existe uma Nova Versão do Sistema Folha para ser Atualizado, deseja atualizar agora?", vbYesNo + vbCritical, varNomeProjeto) = vbYes Then
                Shell "Y:\RH\UNIVERSIDADE BRASIL\FGTS-ATRASO\FGTS-ATRASO\" & "AtualizaFGTS.exe", vbNormalFocus
                DoCmd.Quit acQuitSaveAll
            Else
                MsgBox " Versão Não Atualizada! ", vbInformation, varNomeProjeto
            End If
        End If
                
       
        DoCmd.OpenForm "frmMenuPrincipal", acNormal
        fncFechar Me.Name
Else
    MsgBox "Senha incorreta", vbCritical, varNomeProjeto
    Me.textoSenhaDigitada.SetFocus
End If

TratarErro:
    fncTratamentoDeErro
End Sub

Private Sub cmbFuncionario_KeyDown(KeyCode As Integer, Shift As Integer)
Dim varSenha As String
    
    If KeyCode = vbKeyF12 Then
        varSenha = InputBox("Senha.: ", "Folha Pagamento SK")
        If varSenha = "»¼³§¢Þþ²Ð¥¿½¹«>" Then
            AlterarPropriedade "AllowBypassKey", dbBoolean, False
            MsgBox "Tecla Shift desativada!", , "Tecla Shift"
        End If
    End If
    If KeyCode = vbKeyF11 Then
        varSenha = InputBox("Senha.: ", "Folha Pagamento SK")
        If varSenha = "»¼³§¢Þþ²Ð¥¿½¹«>" Then
            AlterarPropriedade "AllowBypassKey", dbBoolean, True
            MsgBox "Tecla Shift ativada com sucesso!", , "Tecla Shift"
        End If
    End If
End Sub

Private Sub Form_Activate()
    DoCmd.Restore
End Sub
Function fncVerificarInicializado() As Boolean
On Error GoTo TratarErro
Dim varRstConf As DAO.Recordset
    Set varRstConf = CurrentDb.OpenRecordset("tblAplicativoInicializado")
        If varRstConf!AplicativoInicializado = True Then
            fncVerificarInicializado = True
        Else
            fncVerificarInicializado = False
        End If
    varRstConf.Close
TratarErro:
    fncTratamentoDeErro
End Function

Function AlterarPropriedade(NomePropriedade As String, TipoPropriedade As Variant, ValorPropriedade As Variant) As Integer
Dim Propriedade As Property
Const ErroPropriedadeNaoEncontrada = 3270
' O erro 3270 ocorre na primeira vez q se altera a propriedade, pois ela ainda não está criada
On Error GoTo TratarErro

    CurrentDb.Properties(NomePropriedade) = ValorPropriedade
    AlterarPropriedade = True

Change_Bye:
    Exit Function

TratarErro:
    If Err = ErroPropriedadeNaoEncontrada Then
        ' Propriedade não localizada. Vamos então criá-la.
        ' Exige permissão dbSecWriteDef (somente membro de
        ' Administradores poderá alterar a propriedade.
        Set Propriedade = CurrentDb.CreateProperty(NomePropriedade, TipoPropriedade, ValorPropriedade, True)
        CurrentDb.Properties.Append Propriedade
        Resume Next
    Else
        ' Erro desconhecido.
        AlterarPropriedade = False
        MsgBox "Erro " & Err.Number & vbCrLf & Err.Description, vbExclamation, "Alterar Propriedade"
        Resume Change_Bye
    End If
End Function

