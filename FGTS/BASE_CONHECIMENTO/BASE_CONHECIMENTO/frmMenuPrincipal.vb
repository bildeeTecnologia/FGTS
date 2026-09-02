Option Compare Database
Option Explicit
Dim varLogoff As Boolean
Dim varMensagem As Boolean

Private Sub btnBaixa_Click()
Dim varRef As String

    If DFirst("Manutencao", "tblUsuario", "UsuarioID = " & Form_frmMenuPrincipal!txtUsuario) = -1 Then
        MsgBox "ATENÇÃO!!! Antes de continuar, aconselho que faça uma Cópia de Segurança ", vbExclamation, varNomeProjeto
        varRef = InputBox(vbCrLf & "DIGITE A SENHA.: ", "FGTS EM ATRASO - SK", 0)
        If varRef = "010203" Then
            fncAbrirFormulario "frmBaixa"
        Else
            MsgBox "SENHA Inválida!!! ", vbExclamation, varNomeProjeto
        End If
    Else
        MsgBox "Usuário NÃO tem Permissão para BAIXAR DADOS!!! ", vbExclamation, varNomeProjeto
    End If

End Sub

Private Sub btnEmpresa_Click()
    fncAbrirFormulario "frmEmpresa"
End Sub
Private Sub btnFuncionario_Click()
    fncAbrirFormulario "frmFuncionario"

End Sub
Private Sub btnImportacao_Click()
    If DFirst("Manutencao", "tblUsuario", "UsuarioID = " & Form_frmMenuPrincipal!txtUsuario) = -1 Then
        fncAbrirFormulario "frmMenuImporta"
    Else
        MsgBox "Usuário NÃO tem Permissão para IMPORTAR DADOS, somente Consultar Lançamentos!!! ", vbExclamation, varNomeProjeto
    End If
End Sub

Private Sub btnLancamento_Click()
    fncAbrirFormulario "frmLancamento"
End Sub
Private Sub btnLogoff_Click()
    Me.txtMensagem = False
    varLogoff = True
    fncLogOff 1
End Sub
Private Sub btnRelatorio_Click()
    fncAbrirFormulario "frmMenuRelatorio"
End Sub
Private Sub btnSair_Click()
    If MsgBox("Deseja realmente abandonar o sistema?", vbQuestion + vbYesNo, varNomeProjeto) = vbYes Then
        Me.txtMensagem = True
        DoCmd.Quit acQuitSaveAll
    End If
End Sub
Private Sub btnSEFIP_Click()
    fncAbrirFormulario "frmSEFIP"
End Sub

Private Sub Form_Unload(Cancel As Integer)
    If varLogoff = False Then
        If Me.txtMensagem = False Then
            If MsgBox(" Deseja realmente abandonar o sistema?", vbQuestion + vbYesNo, varNomeProjeto) = vbNo Then
                Cancel = True
            End If
        End If
    End If
End Sub

Private Sub SuporteOnLIne_Click()
Dim f As String
    Shell fncRetornarCampoConfiguracao("CaminhoPadrao") & "Suporte.exe", vbNormalFocus
End Sub
