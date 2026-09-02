Option Compare Database
Option Explicit
Private Sub btnGerar_Click()
On Error GoTo TratarErro
Dim varCondicao As String
    
    If IsNull(Me.cmbEmpresaDe) = True And IsNull(Me.cmbEmpresaAte) = True Then
        MsgBox "É Obrigatório Selecionar as Empresas...", vbInformation, varNomeProjeto
    Else
        
        If Me.cmbEmpresaDe = Me.cmbEmpresaAte Then
            varCondicao = " EmpresaID = " & Me.cmbEmpresaDe
            If IsNull(Me.cmbFuncionarioDe) = False And IsNull(Me.cmbFuncionarioAte) = False Then
                varCondicao = varCondicao & " AND FuncionarioID >= " & Me.cmbFuncionarioDe & " AND FuncionarioID <= " & Me.cmbFuncionarioAte
            End If
        Else
            varCondicao = " EmpresaID >= " & Me.cmbEmpresaDe & " AND EmpresaID <= " & Me.cmbEmpresaAte
            If IsNull(Me.cmbPIS) = False Then
                varCondicao = varCondicao & " AND PIS = '" & Me.cmbPIS & "'"
            End If
        End If
            
'        Else
'            If IsNull(Me.cmbPIS) = False Then
'                varCondicao = varCondicao & " PIS = " & Me.cmbPIS
'            End If
'        End If
    
        
        If Me.opcFuncionario = 3 Then
            varCondicao = varCondicao & " AND (IsNUll(DataDemissao) = False)"
        ElseIf Me.opcFuncionario = 2 Then
            varCondicao = varCondicao & " AND (IsNUll(DataDemissao))"
        End If
        
        If Me.grpImprimir = 1 Then
            DoCmd.OpenReport "rptConsolidado", acViewNormal, , varCondicao
        Else
            DoCmd.OpenReport "rptConsolidado", acViewPreview, , varCondicao
        End If
    End If
    
TratarErro:
    fncTratamentoDeErro
End Sub
Private Sub btnFechar_Click()
    fncFechar Me.Name
End Sub
Private Sub cmbEmpresaAte_AfterUpdate()
    
    If Me.cmbEmpresaDe = Me.cmbEmpresaAte Then
        Me.cmbFuncionarioDe.Enabled = True
        Me.cmbFuncionarioAte.Enabled = True
        Me.cmbTxtFuncDe.Enabled = True
        Me.cmbTxtFuncAte.Enabled = True
        Me.cmbPIS.Enabled = False
        Me.cmbFuncPIS.Enabled = False
        Me.rtlPIS.Visible = False
    Else
        Me.cmbFuncionarioDe.Enabled = False
        Me.cmbFuncionarioAte.Enabled = False
        Me.cmbTxtFuncDe.Enabled = False
        Me.cmbTxtFuncAte.Enabled = False
        Me.cmbPIS.Enabled = True
        Me.cmbFuncPIS.Enabled = True
        Me.rtlPIS.Visible = True
        
        Me.cmbFuncionarioDe = Empty
        Me.cmbFuncionarioAte = Empty
        Me.cmbTxtFuncDe = Empty
        Me.cmbTxtFuncAte = Empty

    End If

End Sub

Private Sub cmbEmpresaDe_Click()
    Me.cmbFuncionarioDe.Requery
    Me.cmbFuncionarioAte.Requery
    Me.cmbTxtFuncDe.Requery
    Me.cmbTxtFuncAte.Requery
    Me.txtDataCalculo = DLast("DataIndice", "tblMulta")

End Sub
Private Sub cmbFuncionarioDe_AfterUpdate()
    Me.cmbTxtFuncDe = Me.cmbFuncionarioDe.Column(2)
End Sub
Private Sub cmbTxtFuncDe_AfterUpdate()
    Me.cmbFuncionarioDe = Me.cmbTxtFuncDe.Column(2)
End Sub
Private Sub cmbFuncionarioAte_AfterUpdate()
    Me.cmbTxtFuncAte = Me.cmbFuncionarioAte.Column(2)
    If Me.cmbFuncionarioDe > Me.cmbFuncionarioAte Then
        MsgBox "Código Funcionario De maior que o Funcionario Até!!!", vbInformation, varNomeProjeto
    End If
End Sub
Private Sub cmbTxtFuncAte_AfterUpdate()
    Me.cmbFuncionarioAte = Me.cmbTxtFuncAte.Column(2)
    If Me.cmbFuncionarioDe > Me.cmbFuncionarioAte Then
        MsgBox "Código Funcionario De maior que o Funcionario Até!!!", vbInformation, varNomeProjeto
    End If
End Sub
Private Sub cmbFuncPIS_AfterUpdate()
    cmbPIS = Me.cmbFuncPIS.Column(2)
End Sub

Private Sub cmbPIS_AfterUpdate()
    Me.cmbFuncPIS = Me.cmbPIS.Column(2)
End Sub
Private Sub Form_Activate()
    DoCmd.Restore
End Sub

Private Sub Form_Load()

    Me.txtDataCalculo = DLast("DataIndice", "tblMulta")

End Sub
