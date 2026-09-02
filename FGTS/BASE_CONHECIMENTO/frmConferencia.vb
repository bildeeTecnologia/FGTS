Option Compare Database
Option Explicit
Private Sub btnGerar_Click()
On Error GoTo TratarErro
Dim varCondicao As String
    
    varCondicao = " EmpresaID = " & Me.cmbEmpresaDe
    If IsNull(Me.cmbEmpresaDe.Column(1)) = True Then
        MsgBox "Favor Prencher as Empresas Correspondentes", vbInformation, varNomeProjeto
    Else
        If IsNull(Me.cmbFuncionarioDe) = False And IsNull(Me.cmbFuncionarioAte) = False Then
            varCondicao = varCondicao & " AND FuncionarioID >= " & Me.cmbFuncionarioDe & " AND FuncionarioID <= " & Me.cmbFuncionarioAte
        End If
'        If IsNull(Me.txtCompetenciaDe) = False And IsNull(Me.txtCompetenciaAte) = False Then
'            varCondicao = varCondicao & " AND DataComp >= " & Format(Me.txtCompetenciaDe, "yyyy/mm") & " AND DataComp <= " & Format(Me.txtCompetenciaDe, "yyyy/mm")
'        End If
        
        If Me.grpImprimir = 1 Then
            DoCmd.OpenReport "rptConferencia", acViewNormal, , varCondicao
        Else
            DoCmd.OpenReport "rptConferencia", acViewPreview, , varCondicao
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
End Sub

Private Sub Form_Activate()
    DoCmd.Restore
End Sub
