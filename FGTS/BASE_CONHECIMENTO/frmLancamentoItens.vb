Option Compare Database

Private Sub BaseFGTS_AfterUpdate()
    ValorFGTS = BaseFGTS * 0.08

End Sub

Private Sub Competencia_Click()
    Form_frmLancamentoItens.txtEmpresaID = Form_frmLancamento.txtEmpresa
    Form_frmLancamentoItens.txtFuncionarioID = Form_frmLancamento.txtFuncionario
End Sub

Private Sub Pago_AfterUpdate()
    If Pago = True Then
        ValorPago = ValorFGTS
    Else
        ValorPago = 0
    End If
End Sub
