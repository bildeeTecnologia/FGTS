Option Compare Database
Option Explicit
Private Sub btnGerar_Click()
On Error GoTo TratarErro
Dim varCondicao As String
    
    varCondicao = " EmpresaID <> 0 "
    If IsNull(Me.cmbEmpresaDe.Column(1)) = True Or IsNull(Me.txtDataCalculo) Then
        MsgBox "Favor Prencher os Campos Necessários....", vbInformation, varNomeProjeto
    Else
        If IsNull(Me.cmbFuncionarioDe) = False And IsNull(Me.cmbFuncionarioAte) = False Then
            varCondicao = varCondicao & " AND FuncionarioID >= " & Me.cmbFuncionarioDe & " AND FuncionarioID <= " & Me.cmbFuncionarioAte
        End If
        
        If Me.opcFuncionario = 3 Then
            varCondicao = varCondicao & " AND (IsNUll(DataDemissao) = False)"
        ElseIf Me.opcFuncionario = 2 Then
            varCondicao = varCondicao & " AND (IsNUll(DataDemissao))"
        End If
        
        
        If Me.grpImprimir = 1 Then
            If Me.grpTipo = 1 Then
                DoCmd.OpenReport "rptMesaMes", acViewNormal, , varCondicao
            Else
                DoCmd.OpenReport "rptMesaMes_Mod1", acViewNormal, , varCondicao
            End If
        Else
            If Me.grpTipo = 1 Then
                DoCmd.OpenReport "rptMesaMes", acViewPreview, , varCondicao
            Else
                DoCmd.OpenReport "rptMesaMes_Mod1", acViewPreview, , varCondicao
            End If
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
    Me.txtDataCalculo = DLast("DataIndice", "tblMulta")

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
