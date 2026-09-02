Option Compare Database
Option Explicit
Global varFuncaoInterna As String
Public varTeclaAtalho() As Variant
Function fncLocalizar()
On Error GoTo TratarErro
    Screen.PreviousControl.SetFocus
    DoCmd.DoMenuItem acFormBar, acEditMenu, 10, , acMenuVer70
TratarErro:
    fncTratamentoDeErro
End Function
Function fncPrimeiro(strNomeDoFormulario As String)
On Error GoTo TratarErro
    DoCmd.GoToRecord acDataForm, strNomeDoFormulario, acFirst
TratarErro:
    fncTratamentoDeErro
End Function
Function fncAnterior(strNomeDoFormulario As String)
On Error GoTo TratarErro
    DoCmd.GoToRecord acDataForm, strNomeDoFormulario, acPrevious
TratarErro:
    fncTratamentoDeErro
End Function
Function fncProximo(strNomeDoFormulario As String)
On Error GoTo TratarErro
    DoCmd.GoToRecord acDataForm, strNomeDoFormulario, acNext
TratarErro:
    fncTratamentoDeErro
End Function
Function fncUltimo(strNomeDoFormulario As String)
On Error GoTo TratarErro
    DoCmd.GoToRecord acDataForm, strNomeDoFormulario, acLast
TratarErro:
    fncTratamentoDeErro
End Function
Function fncNovo(strNomeDoFormulario As String)
On Error GoTo TratarErro
    DoCmd.GoToRecord acDataForm, strNomeDoFormulario, acNewRec
TratarErro:
    fncTratamentoDeErro
End Function
Function fncExcluir()
On Error GoTo TratarErro
    DoCmd.DoMenuItem acFormBar, acEditMenu, 8, , acMenuVer70
    DoCmd.DoMenuItem acFormBar, acEditMenu, 6, , acMenuVer70
Exit_Tratar:
    Exit Function
TratarErro:
    If Err = 3200 Then
        MsgBox "O registro não pode ser excluido por estar relacionado com outra(s) tabela(s).", vbCritical, "Numero 0003.01"
    Else
        fncTratamentoDeErro
    End If
End Function
Function fncFechar(strNomeDoFormulario As String)
On Error GoTo TratarErro
    DoCmd.Close acForm, strNomeDoFormulario
TratarErro:
    fncTratamentoDeErro
End Function
Function fncSair()
On Error GoTo TratarErro
    DoCmd.Quit
TratarErro:
    fncTratamentoDeErro
End Function
Function fncAbrirRelatorio(strNomeDoRelatorio As String)
On Error GoTo Err_AbrirRelatorio
    DoCmd.OpenReport strNomeDoRelatorio, acViewPreview
Exit_AbrirRelatorio:
    Exit Function
Err_AbrirRelatorio:
    'o erro número 2501 é o cancelamento da ação abrir relatório
    If Err <> 2501 Then
        MsgBox Err.Description & "Numero do Access " & Err.Number
        Resume Exit_AbrirRelatorio
    End If
End Function
Function fncCarregarTeclasAtalho()
On Error GoTo TrataErro

    Dim rstTeclaObjeto As DAO.Recordset, i As Integer, varNovoTamanhoMatriz As Integer
    Set rstTeclaObjeto = CurrentDb.OpenRecordset("qryTeclaObjeto")

    i = 0
    Do Until rstTeclaObjeto.EOF
        i = i + 1
        rstTeclaObjeto.MoveNext
    Loop

    If i <> 0 Then
        rstTeclaObjeto.MoveFirst
        varNovoTamanhoMatriz = i

        ReDim varTeclaAtalho(varNovoTamanhoMatriz, 3) As Variant
    Else
        Exit Function
    End If

    For i = 0 To rstTeclaObjeto.RecordCount - 1
        varTeclaAtalho(i, 0) = rstTeclaObjeto!TeclaID
        varTeclaAtalho(i, 1) = rstTeclaObjeto!Nome
        varTeclaAtalho(i, 2) = rstTeclaObjeto!TipoObjetoID

        rstTeclaObjeto.MoveNext
    Next i

    rstTeclaObjeto.Close
    Set rstTeclaObjeto = Nothing

TrataErro:
    fncTratamentoDeErro
End Function
Function fncVerificarSeCodigoEventojaCadastrado(EventoID As Integer) As Boolean
On Error GoTo TratarErro
Dim varRstEvento As DAO.Recordset
    Set varRstEvento = CurrentDb.OpenRecordset("SELECT EventoID FROM tblEvento WHERE EventoID = " & EventoID)
    If varRstEvento.RecordCount > 0 Then
        fncVerificarSeCodigoEventojaCadastrado = True
    Else
        fncVerificarSeCodigoEventojaCadastrado = False
    End If
    varRstEvento.Close
TratarErro:
    fncTratamentoDeErro
End Function
