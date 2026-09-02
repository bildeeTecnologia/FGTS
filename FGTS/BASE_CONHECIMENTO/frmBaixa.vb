Option Compare Database
Option Explicit
Private Sub btnGerar_Click()
On Error GoTo TratarErro
Dim varCondicao As String
Dim varRstBaixa As DAO.Recordset
Dim i As Integer

    If MsgBox("Deseja realmente dar Baixa nos pagamentos dos funcionários selecionados???", vbQuestion + vbYesNo, varNomeProjeto) = vbYes Then
        Set varRstBaixa = CurrentDb.OpenRecordset("SELECT tblLancamento.EmpresaID, tblLancamento.FuncionarioID, tblLancamento.Comp13, tblLancamento.Competencia, tblLancamento.Pago, tblLancamento.ValorFGTS FROM tblLancamento WHERE (((tblLancamento.EmpresaID)= " & Me.cmbEmpresaDe & ") AND ((tblLancamento.FuncionarioID) Between " & Me.cmbFuncionarioDe & " And " & Me.cmbFuncionarioAte & ") AND ((tblLancamento.Competencia) between format('" & Me.txtCompetenciaDe & "','dd/mm/yyyy') AND format ('" & Me.txtCompetenciaAte & "','dd/mm/yyyy')) AND ((tblLancamento.Pago)=No))")
        If varRstBaixa.RecordCount > 0 Then
            varRstBaixa.MoveLast
            varRstBaixa.MoveFirst
            For i = 1 To varRstBaixa.RecordCount
                DoCmd.SetWarnings False
                DoCmd.RunSQL "UPDATE tblLancamento Set Pago = -1, DataPagto = Format('" & Me.txtDataCalculo & "','dd/mm/yyyy'), ValorPago = Format('" & varRstBaixa!ValorFGTS & "','Currency') WHERE FuncionarioID = " & varRstBaixa!FuncionarioID & " And EmpresaID = " & varRstBaixa!EmpresaID & " and Competencia = Format('" & varRstBaixa!Competencia & "', 'dd/mm/yyyy')"
                DoCmd.SetWarnings True
                varRstBaixa.MoveNext
            Next
            MsgBox "Fim das Baixas...", vbInformation, varNomeProjeto
        Else
            MsgBox "Não existe dados para efetuar as Baixas...", vbInformation, varNomeProjeto
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
    Me.txtDataCalculo = Date

End Sub

Private Sub Form_Activate()
    DoCmd.Restore
End Sub
