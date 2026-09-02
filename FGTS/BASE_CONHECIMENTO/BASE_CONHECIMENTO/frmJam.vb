Option Compare Database
Option Explicit

Private Sub BtnCalculoJAM_Click()
Dim varRstJAM As DAO.Recordset
Dim i As Integer
Dim varValorJAM As Double


    If IsNull(Me.cmbEmpresaDe.Column(1)) Or IsNull(Me.txtDataCalculo) = True Then
        MsgBox "Favor Selecionar a Empresa....", vbInformation, varNomeProjeto
    Else
        MsgBox "O Processo de Calcular o JAM demora um pouco!!!", vbInformation, varNomeProjeto
    
        Set varRstJAM = CurrentDb.OpenRecordset("SELECT tblEmpresa.EmpresaID, tblFuncionario.FuncionarioID, tblLancamento.Comp13, tblLancamento.Competencia FROM (tblEmpresa INNER JOIN tblFuncionario ON tblEmpresa.EmpresaID = tblFuncionario.EmpresaID) INNER JOIN tblLancamento ON (tblFuncionario.FuncionarioID = tblLancamento.FuncionarioID) AND (tblEmpresa.EmpresaID = tblLancamento.EmpresaID) WHERE (((tblEmpresa.EmpresaID) = " & Me.cmbEmpresaDe.Column(0) & ")) ORDER BY tblFuncionario.FuncionarioID, tblLancamento.Competencia")
    
        varRstJAM.MoveLast
        varRstJAM.MoveFirst
        If varRstJAM.RecordCount > 0 Then
            
            For i = 1 To varRstJAM.RecordCount
            
                varValorJAM = fncCalculoJAM(varRstJAM!EmpresaID, varRstJAM!FuncionarioID, varRstJAM!Competencia, varRstJAM!Comp13, Me.txtDataCalculo)
            
                DoCmd.SetWarnings False
                DoCmd.RunSQL "UPDATE tblLancamento Set ValorJAM = Format('" & varValorJAM & "','Currency') WHERE EmpresaID = " & varRstJAM!EmpresaID & " and FuncionarioID = " & varRstJAM!FuncionarioID & " And Competencia = Format('" & varRstJAM!Competencia & "', 'dd/mm/yyyy')"
                DoCmd.SetWarnings True
            
                varRstJAM.MoveNext
            Next
        
        
        End If
        varRstJAM.Close
        Me.btnGerar.Enabled = True
    End If

End Sub

Private Sub btnGerar_Click()
On Error GoTo TratarErro
Dim varCondicao As String
    
    varCondicao = " EmpresaID <> 0 "
    If IsNull(Me.cmbEmpresaDe.Column(1)) Or IsNull(Me.txtDataCalculo) = True Then
        MsgBox "Favor Selecionar a Empresa....", vbInformation, varNomeProjeto
    Else
        i = 0
        
        If IsNull(Me.cmbFuncionarioDe) = False And IsNull(Me.cmbFuncionarioAte) = False Then
            varCondicao = varCondicao & " AND FuncionarioID >= " & Me.cmbFuncionarioDe & " AND FuncionarioID <= " & Me.cmbFuncionarioAte
        End If
        
        If Me.grpImprimir = 1 Then
            DoCmd.OpenReport "rptJam", acViewNormal, , varCondicao
        Else
            DoCmd.OpenReport "rptJam", acViewPreview, , varCondicao
        End If
    End If
TratarErro:
    fncTratamentoDeErro
End Sub
Private Sub btnFechar_Click()
    fncFechar Me.Name
End Sub

Private Sub cmbEmpresaDe_Click()
    Me.cmbFuncionarioDe.Requery
    Me.cmbFuncionarioAte.Requery
    Me.cmbTxtFuncDe.Requery
    Me.cmbTxtFuncAte.Requery
    Me.txtDataCalculo = DLast("CompetenciaID", "tblCoefjam")
    Me.btnGerar.Enabled = False
    
End Sub

Private Sub cmbFuncionarioAte_AfterUpdate()
    Me.cmbTxtFuncAte = Me.cmbFuncionarioAte.Column(2)
    If Me.cmbFuncionarioDe > Me.cmbFuncionarioAte Then
        MsgBox "Código Funcionario De maior que o Funcionario Até!!!", vbInformation, varNomeProjeto
    End If
End Sub

Private Sub cmbFuncionarioDe_AfterUpdate()
    Me.cmbTxtFuncDe = Me.cmbFuncionarioDe.Column(2)
End Sub

Private Sub cmbTxtFuncAte_AfterUpdate()
    Me.cmbFuncionarioAte = Me.cmbTxtFuncAte.Column(2)
    If Me.cmbFuncionarioDe > Me.cmbFuncionarioAte Then
        MsgBox "Código Funcionario De maior que o Funcionario Até!!!", vbInformation, varNomeProjeto
    End If
End Sub

Private Sub cmbTxtFuncDe_AfterUpdate()
    Me.cmbFuncionarioDe = Me.cmbTxtFuncDe.Column(2)
End Sub


Private Sub Form_Activate()
    DoCmd.Restore
End Sub
