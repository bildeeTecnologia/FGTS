Option Compare Database
Option Explicit
Private Sub btnConferencia_Click()
    fncAbrirFormulario "frmConferencia"
End Sub

Private Sub btnConsolidado_Click()
    fncAbrirFormulario "frmConsolidado"

End Sub

Private Sub btnFechar_Click()
     fncFechar Me.Name
End Sub

Private Sub btnFGTSJAM_Click()
    fncAbrirFormulario "frmJam"
End Sub

Private Sub btnMesaMes_Click()
    fncAbrirFormulario "frmMesaMes"
End Sub

Private Sub btnTotalAno_Click()
    fncAbrirFormulario "frmPorAno"
End Sub

Private Sub btnTotalFuncionario_Click()
    fncAbrirFormulario "frmPorFuncionario"
End Sub
