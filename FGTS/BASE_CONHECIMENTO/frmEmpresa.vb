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
'    Me.EmpresaID.Locked = False
'    Me.EmpresaID.SetFocus
End Sub
Private Sub btnFechar_Click()
    fncFechar Me.Name
End Sub
Private Sub Form_Activate()
    DoCmd.Restore
End Sub
