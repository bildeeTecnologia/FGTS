Option Compare Database
Option Explicit
Private Sub btnLocalizar_Click()
    fncLocalizar
End Sub
Private Sub btnUltimo_Click()
    Me.cmbFuncionario = Empty
    Me.txtFuncionario = Empty
    fncUltimo Me.Name
End Sub
Private Sub btnExcluir_Click()
    fncExcluir
End Sub
Private Sub btnPrimeiro_Click()
    Me.cmbFuncionario = Empty
    Me.txtFuncionario = Empty
    fncPrimeiro Me.Name
End Sub
Private Sub btnProximo_Click()
    Me.cmbFuncionario = Empty
    Me.txtFuncionario = Empty
    fncProximo Me.Name
End Sub
Private Sub btnAnterior_Click()
    Me.cmbFuncionario = Empty
    Me.txtFuncionario = Empty
    fncAnterior Me.Name
    Me.cmbFuncionario.Requery
End Sub
Private Sub btnNovo_Click()
Dim varRstFuncionario As DAO.Recordset

    If IsNull(Me.txtEmpresa) = False Then
        Me.cmbFuncionario.Requery
        Me.cmbFuncionario = Empty
        Me.txtFuncionario = Empty
        Me.FuncionarioID.Enabled = True
        Me.FuncionarioID.Locked = False
        Me.FuncionarioID.SetFocus
        
        fncNovo Me.Name
        Form_frmFuncionario.EmpresaID = Me.txtEmpresa
        Set varRstFuncionario = CurrentDb.OpenRecordset("SELECT * FROM tblFuncionario WHERE (((tblFuncionario.EmpresaID)= " & Me.txtEmpresa & "))")
        If varRstFuncionario.RecordCount > 0 Then
            varRstFuncionario.MoveFirst
            varRstFuncionario.MoveLast
            Me.FuncionarioID = varRstFuncionario!FuncionarioID + 1
        Else
            Me.FuncionarioID = 1
        End If
        
        varRstFuncionario.Close
        
        Me.FuncionarioID.Enabled = True
        Me.FuncionarioID.Locked = False
        Me.FuncionarioID.SetFocus
    Else
        MsgBox "Selecione uma Empresa!!! ", vbExclamation, varNomeProjeto
    End If
    
End Sub
Private Sub btnFechar_Click()
    fncFechar Me.Name
End Sub

Private Sub cmbEmpresa_AfterUpdate()
    Me.cmbFuncionario.Requery
End Sub

Private Sub cmbFuncionario_AfterUpdate()
    Me.txtFuncionario = Me.cmbFuncionario.Column(1)
    Form_frmFuncionario.Requery
    Me.RecordsetClone.FindFirst "[FuncionarioID] = " & Me!cmbFuncionario
    Me.Bookmark = Me.RecordsetClone.Bookmark
End Sub
Private Sub Form_Activate()
    DoCmd.Restore
End Sub
Private Sub txtFuncionario_AfterUpdate()
    Me.cmbFuncionario = Me.txtFuncionario
    Me.cmbFuncionario.Requery
    Form_frmFuncionario.Requery
    Me.Filter = Empty
    Me.RecordsetClone.FindFirst "[FuncionarioID] = " & Me!txtFuncionario
    Me.Bookmark = Me.RecordsetClone.Bookmark

End Sub
