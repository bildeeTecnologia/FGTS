Option Compare Database
Option Explicit
Private Sub btnLocalizar_Click()
    fncLocalizar
End Sub
Private Sub btnUltimo_Click()
    fncUltimo Me.Name
End Sub
Private Sub btnExcluir_Click()
    fncExcluir
End Sub
Private Sub btnPrimeiro_Click()
    fncPrimeiro Me.Name
End Sub
Private Sub btnProximo_Click()
    fncProximo Me.Name
End Sub
Private Sub btnAnterior_Click()
    fncAnterior Me.Name
End Sub
Private Sub btnNovo_Click()
    fncNovo Me.Name
End Sub

Private Sub btnAlterar_Click() 'Incluir
    If DFirst("Manutencao", "tblUsuario", "UsuarioID = " & Form_frmMenuPrincipal!txtUsuario) = -1 Then
        Form_frmLancamentoItens.AllowAdditions = True
        Form_frmLancamentoItens.AllowDeletions = True
        Form_frmLancamentoItens.AllowEdits = True
'        Form_frmLancamentoItens.Competencia.Locked = False
'        Form_frmLancamentoItens.Comp13.Locked = False
'        Form_frmLancamentoItens.BaseFGTS.Locked = False
'        Form_frmLancamentoItens.ValorFGTS.Locked = False
'        Form_frmLancamentoItens.Pago.Locked = False
'        Form_frmLancamentoItens.DataPagto.Locked = False
'        Form_frmLancamentoItens.ValorPago.Locked = False
    Else
        MsgBox "Usuário NÃO tem Permissão para INCLUIR, somente Consultar!!! ", vbExclamation, varNomeProjeto
    End If
End Sub
Private Sub btnFechar_Click()
    Form_frmLancamentoItens.AllowAdditions = False
    Form_frmLancamentoItens.AllowDeletions = False
    Form_frmLancamentoItens.AllowEdits = False
'    Form_frmLancamentoItens.Competencia.Locked = True
'    Form_frmLancamentoItens.Comp13.Locked = True
'    Form_frmLancamentoItens.BaseFGTS.Locked = True
'    Form_frmLancamentoItens.ValorFGTS.Locked = True
'    Form_frmLancamentoItens.Pago.Locked = True
'    Form_frmLancamentoItens.DataPagto.Locked = True
'    Form_frmLancamentoItens.ValorPago.Locked = True
    fncFechar Me.Name
End Sub

Private Sub cmbEmpresa_Enter()
    Me.cmbFuncionario = Empty
End Sub
Private Sub cmbFuncionario_AfterUpdate()
    Me.txtFuncionario = Me.cmbFuncionario.Column(1)
    Me.frmLancamentoItens.Requery
End Sub
Private Sub cmbFuncionario_Enter()
    Me.cmbFuncionario.Requery
End Sub
Private Sub Form_Activate()
    DoCmd.Restore
End Sub
Private Sub txtFuncionario_AfterUpdate()
    Me.cmbFuncionario = Me.txtFuncionario
    Me.cmbFuncionario.Requery
    Me.frmLancamentoItens.Requery
End Sub
