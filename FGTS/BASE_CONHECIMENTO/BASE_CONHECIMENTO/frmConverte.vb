Option Compare Database

Private Sub btnConverte_Click()
Dim varRstFuncionario As DAO.Recordset
Dim varTexto As String
Dim varData As String
Dim i, x, d, f, s As Integer
Dim varSefip As String
Dim varDataDem As Date
Dim varFlag As Integer



    Set varRstFuncionario = CurrentDb.OpenRecordset("SELECT tblFuncionario.EmpresaID, tblFuncionario.FuncionarioID, tblFuncionario.Observacao FROM tblFuncionario")
    varRstFuncionario.MoveLast
    varRstFuncionario.MoveFirst
    For i = 1 To varRstFuncionario.RecordCount
    varTexto = IIf(IsNull(varRstFuncionario!Observacao), Empty, varRstFuncionario!Observacao)
    If Mid(varTexto, 1, 1) = "P" Or Mid(varTexto, 1, 1) = "D" Then
        x = 0
        d = 0
        f = 0
        s = 0
        varData = Empty
        varDataDem = 0
        
        For x = 1 To 50
            If IsNumeric(Mid(varTexto, x, 1)) Then
                If s = 0 Then
                    If Mid(varTexto, x, 1) = "4" Or Mid(varTexto, x, 1) = "5" Or Mid(varTexto, x, 1) = "6" Or Mid(varTexto, x, 1) = "7" Or Mid(varTexto, x, 1) = "8" Or Mid(varTexto, x, 1) = "9" Then
                        varData = varData & "0"
                        d = d + 1
                    Else
                        If Mid(varTexto, x, 1) <> "0" Then
                            If Mid(varTexto, x + 1, 1) = "." Or Mid(varTexto, x + 1, 1) = "-" Then
                                varData = varData & "0"
                                d = d + 1
                            End If
                        End If
                    End If
                End If
                s = 1
                varData = varData & Mid(varTexto, x, 1)
                d = d + 1
                If d = 8 Then
                    Exit For
                End If
                If f = 0 Then
                    If Mid(varTexto, x + 1, 1) = "." Or Mid(varTexto, x + 1, 1) = "-" Then
                        If Mid(varTexto, x + 2, 1) = 1 Then
                            If Mid(varTexto, x + 3, 1) = "." Or Mid(varTexto, x + 3, 1) = "-" Then
                                varData = varData & "0"
                                d = d + 1
                            End If
                        ElseIf Mid(varTexto, x + 2, 1) > 1 Then
                            varData = varData & "0"
                            d = d + 1
                        End If
                        f = 1
                    End If
                End If
                
            End If
        Next
        If varData <> "" Then
            varFlag = Mid(varData, 3, 2)
            If varFlag >= 1 And varFlag < 13 Then
                varSefip = IIf(Mid(varTexto, 1, 1) = "P", "J ", "I1")
                varDataDem = Mid(varData, 1, 2) & "/" & Mid(varData, 3, 2) & "/" & Mid(varData, 5, 4)
                DoCmd.SetWarnings False
                DoCmd.RunSQL "UPDATE tblFuncionario Set CodDemSefip = '" & varSefip & "' WHERE FuncionarioID = " & varRstFuncionario!FuncionarioID & " And EmpresaID = " & varRstFuncionario!EmpresaID
                DoCmd.RunSQL "UPDATE tblFuncionario Set DataDemissao = '" & varDataDem & "' WHERE FuncionarioID = " & varRstFuncionario!FuncionarioID & " And EmpresaID = " & varRstFuncionario!EmpresaID
                DoCmd.SetWarnings True
            End If
        End If
    End If
    varRstFuncionario.MoveNext
    Next
    varRstFuncionario.Close
End Sub
