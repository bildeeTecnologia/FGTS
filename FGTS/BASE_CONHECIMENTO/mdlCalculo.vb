Option Compare Database

Function fncCalculoFGTS(EmpresaID, FuncionarioID, Competencia, Comp13, varDataPagto) As Double
On Error Resume Next
Dim varBaseFgts As Double
Dim varRstIndice As DAO.Recordset


'      *====================>>> MODELO Mês a Mês <<<===================*
    Set varRstIndice = CurrentDb.OpenRecordset("SELECT tblLancamento.EmpresaID, tblLancamento.FuncionarioID, tblLancamento.BaseFGTS, tblLancamento.Competencia, tblLancamento.Comp13, tblMulta.DataIndice, tblMulta.Indice FROM tblLancamento INNER JOIN tblMulta ON tblLancamento.Competencia = tblMulta.CompetenciaID  WHERE (((tblLancamento.EmpresaID)= " & EmpresaID & ") AND ((tblLancamento.FuncionarioID)= " & FuncionarioID & ") AND ((tblLancamento.Competencia) = Format('" & Competencia & "','dd/MM/yyyy')) AND (DataIndice = Format('" & varDataPagto & "','dd/MM/yyyy')) and Comp13 = " & Comp13 & ") ORDER BY tblLancamento.Competencia")
        varRstIndice.MoveLast
        varRstIndice.MoveFirst
    If varRstIndice.RecordCount > 0 Then
        
           varBaseFgts = varRstIndice!BaseFGTS

           If Year(varRstIndice!Competencia) = 1994 And Month(varRstIndice!Competencia) = 3 Then
              varBaseFgts = varBaseFgts * 948.93
           End If
           If Year(varRstIndice!Competencia) = 1994 And Month(varRstIndice!Competencia) = 4 Then
              varBaseFgts = varBaseFgts * 1389.94
           End If
           If Year(varRstIndice!Competencia) = 1994 And Month(varRstIndice!Competencia) = 5 Then
              varBaseFgts = varBaseFgts * 1946.13
           End If
           If Year(varRstIndice!Competencia) = 1994 And Month(varRstIndice!Competencia) = 6 Then
              varBaseFgts = varBaseFgts * 2750
           End If

           varValorFgts = Format(varBaseFgts * 0.08, "##,##0.00")

           If Year(varRstIndice!Competencia) > 1967 And Year(varRstIndice!Competencia) < 1986 Then
              varValorFgts = varValorFgts / 2750000000000#
           End If
           If Year(varRstIndice!Competencia) > 1985 And Year(varRstIndice!Competencia) < 1989 Then
              varValorFgts = Format(varValorFgts / 2750000000#, "##,##0.00")
           End If
           If Year(varRstIndice!Competencia) = 1988 And Month(varRstIndice!Competencia) = 12 Then
              varValorFgts = varValorFgts / 2750000
           End If
           If Year(varRstIndice!Competencia) > 1988 And Year(varRstIndice!Competencia) < 1993 Then
              varValorFgts = varValorFgts / 2750000
           End If
           If Year(varRstIndice!Competencia) = 1993 And Month(varRstIndice!Competencia) < 8 Then
              varValorFgts = varValorFgts / 2750000
           End If
           If Year(varRstIndice!Competencia) = 1993 And Month(varRstIndice!Competencia) > 7 Then
              varValorFgts = varValorFgts / 2750
           End If
           If Year(varRstIndice!Competencia) = 1994 And Month(varRstIndice!Competencia) < 7 Then
              varValorFgts = varValorFgts / 2750
           End If

           If varValorFgts < 0.01 Then
                varValorFgts = 0.01
           End If

           varBaseFgts = Format(varBaseFgts * varRstIndice!Indice, "##,##0.00")

'      ***************************************************
           If Year(varRstIndice!Competencia) < 2001 Then
              varBaseFgts = varBaseFgts - varValorFgts
           End If
           If Year(varRstIndice!Competencia) = 2001 And Month(varRstIndice!Competencia) < 10 Then
              varBaseFgts = varBaseFgts - varValorFgts
           End If
           If Year(varRstIndice!Competencia) = 2001 And Month(varRstIndice!Competencia) > 9 Then
              varBaseFgts = Format((varBaseFgts * 1.0625) - varValorFgts, "##,##0.00")
           End If
           
           If Year(varRstIndice!Competencia) > 2001 Then
              varBaseFgts = varBaseFgts - varValorFgts
           End If
      '***************************************************
      
           fncCalculoFGTS = varBaseFgts + varValorFgts
           
        Else
           fncCalculoFGTS = 0
        End If
           

End Function
Function fncCalculoJAM(EmpresaID, FuncionarioID, Competencia, Comp13 As Boolean, varDataPagto) As Double
On Error Resume Next
Dim varBaseFgts As Double
Dim varRstIndice As DAO.Recordset

'      *====================>>> MODELO FGTS + JAM <<<===================*
    Set varRstIndice = CurrentDb.OpenRecordset("SELECT tblLancamento.EmpresaID, tblLancamento.FuncionarioID, tblLancamento.BaseFGTS, tblLancamento.Competencia, tblLancamento.Comp13, tblCoefjam.CompetenciaID, tblCoefjam.Indice  FROM tblLancamento INNER JOIN tblCoefjam ON tblLancamento.Competencia = tblCoefjam.CompetenciaID WHERE (((tblLancamento.EmpresaID)=" & EmpresaID & ") AND ((tblLancamento.FuncionarioID)= " & FuncionarioID & ") AND ((tblLancamento.Competencia)= Format('" & Competencia & "','dd/MM/yyyy')) AND ((tblLancamento.Comp13)= 0))")
        varRstIndice.MoveLast
        varRstIndice.MoveFirst
    If varRstIndice.RecordCount > 0 Then
        varBaseFgts = varRstIndice!BaseFGTS
        If Year(varRstIndice!Competencia) = 1994 And Month(varRstIndice!Competencia) = 3 Then
           varBaseFgts = varBaseFgts * 948.93
        End If
        If Year(varRstIndice!Competencia) = 1994 And Month(varRstIndice!Competencia) = 4 Then
           varBaseFgts = varBaseFgts * 1389.94
        End If
        If Year(varRstIndice!Competencia) = 1994 And Month(varRstIndice!Competencia) = 5 Then
           varBaseFgts = varBaseFgts * 1946.13
        End If
        If Year(varRstIndice!Competencia) = 1994 And Month(varRstIndice!Competencia) = 6 Then
           varBaseFgts = varBaseFgts * 2750
        End If
        If Year(varRstIndice!Competencia) = 2012 Then
             varValorFgts = varRstIndice!Indice
        End If
        
        varValorFgts = Format(varBaseFgts * 0.08, "##,##0.00")
        
        i = i + 1
        
        If i = 1 Then
            fncCalculoJAM = 0
            i = 1
            varValorFGTSJAM = varValorFgts
            varFuncionario = FuncionarioID
        ElseIf varFuncionario <> FuncionarioID Then
            fncCalculoJAM = 0
            i = 1
            varValorFGTSJAM = varValorFgts
            varFuncionario = FuncionarioID
        Else
            If IsNull(varRstIndice!Indice) = False Then
                varBaseFgts = Format(varValorFGTSJAM * varRstIndice!Indice, "##,##0.00")
                
                varValorFGTSJAM = varValorFGTSJAM + varBaseFgts + varValorFgts
                
                fncCalculoJAM = varBaseFgts
            Else
                fncCalculoJAM = 0
            End If
        End If
    Else
        fncCalculoJAM = 0
    End If
    varRstIndice.Close

End Function
Function fncCalculoFGTSMes(EmpresaID, FuncionarioID, Competencia, Comp13) As Double
On Error Resume Next
Dim varBaseFgts As Double
Dim varRstIndice As DAO.Recordset
Dim varDataPagto As String

    Set varRstIndice = CurrentDb.OpenRecordset("SELECT tblLancamento.EmpresaID, tblLancamento.FuncionarioID, tblLancamento.BaseFGTS, tblLancamento.Competencia, tblLancamento.Comp13, tblMulta.DataIndice, tblMulta.Indice FROM tblLancamento INNER JOIN tblMulta ON tblLancamento.Competencia = tblMulta.CompetenciaID  WHERE (((tblLancamento.EmpresaID)= " & EmpresaID & ") AND ((tblLancamento.FuncionarioID)= " & FuncionarioID & ") AND ((tblLancamento.Competencia) = Format('" & Competencia & "','dd/MM/yyyy')) AND Comp13 = " & Comp13 & ") ORDER BY tblLancamento.Competencia")
        varRstIndice.MoveLast
        varRstIndice.MoveFirst
    If varRstIndice.RecordCount > 0 Then
        
           varBaseFgts = varRstIndice!BaseFGTS

           If Year(varRstIndice!Competencia) = 1994 And Month(varRstIndice!Competencia) = 3 Then
              varBaseFgts = varBaseFgts * 948.93
           End If
           If Year(varRstIndice!Competencia) = 1994 And Month(varRstIndice!Competencia) = 4 Then
              varBaseFgts = varBaseFgts * 1389.94
           End If
           If Year(varRstIndice!Competencia) = 1994 And Month(varRstIndice!Competencia) = 5 Then
              varBaseFgts = varBaseFgts * 1946.13
           End If
           If Year(varRstIndice!Competencia) = 1994 And Month(varRstIndice!Competencia) = 6 Then
              varBaseFgts = varBaseFgts * 2750
           End If

           varValorFgts = Format(varBaseFgts * 0.08, "##,##0.00")

           If Year(varRstIndice!Competencia) > 1967 And Year(varRstIndice!Competencia) < 1986 Then
              varValorFgts = varValorFgts / 2750000000000#
           End If
           If Year(varRstIndice!Competencia) > 1985 And Year(varRstIndice!Competencia) < 1989 Then
              varValorFgts = Format(varValorFgts / 2750000000#, "##,##0.00")
           End If
           If Year(varRstIndice!Competencia) = 1988 And Month(varRstIndice!Competencia) = 12 Then
              varValorFgts = varValorFgts / 2750000
           End If
           If Year(varRstIndice!Competencia) > 1988 And Year(varRstIndice!Competencia) < 1993 Then
              varValorFgts = varValorFgts / 2750000
           End If
           If Year(varRstIndice!Competencia) = 1993 And Month(varRstIndice!Competencia) < 8 Then
              varValorFgts = varValorFgts / 2750000
           End If
           If Year(varRstIndice!Competencia) = 1993 And Month(varRstIndice!Competencia) > 7 Then
              varValorFgts = varValorFgts / 2750
           End If
           If Year(varRstIndice!Competencia) = 1994 And Month(varRstIndice!Competencia) < 7 Then
              varValorFgts = varValorFgts / 2750
           End If

           If varValorFgts < 0.01 Then
                varValorFgts = 0.01
           End If

           fncCalculoFGTSMes = varValorFgts
        Else
           fncCalculoFGTSMes = 0
        End If

End Function
Function fncImportaDados()
Dim varLinha As String
Dim varContagemLinha As Double
Dim varMatrizLinha(10000) As String
Dim varCompetencia As String
Dim varEmpresaID As Integer
Dim varFuncionarioID As String
Dim varNome As String
Dim varPIS As String
Dim varCBO As String
Dim varCarteira As String
Dim varSerie As String
Dim varDataNascto As String
Dim varDataAdm As String
Dim varDataDem As String
Dim varBaseFgts As Double
Dim varValorFgts As Double
Dim varDataPagto As String
Dim varCat As String
Dim varCodDem As String
Dim varPago As String
Dim varComp As String
Dim varValorPago As Double
Dim varEmpresa As Double
Dim contadorFunc As Integer
Dim varCaminhoArquivo As String
Dim i As Integer
Dim p As Integer

    Close #1
    
    '*** ATENÇÃO AJUSTAR O NUMERO e ANO DA EMPRESA
    varEmpresaID = 5
    varCaminhoArquivo = "C:\SK\ID_" & varEmpresaID & "_2018.txt"
    
    Open varCaminhoArquivo For Input As #1
        Line Input #1, varLinha
        varContagemLinha = 0
        varInicio = 1
        For i = 1 To Len(varLinha)
            If Mid(varLinha, i, 1) = Chr(10) Then ' Se tiver um enter é uma linha
                varMatrizLinha(varContagemLinha) = Replace(Mid(varLinha, varInicio, i - varInicio), Chr(10), "")
                varContagemLinha = varContagemLinha + 1
                varInicio = i
            End If
        Next
    Close #1
    'Se for 0 quer dizer que o arquivo veio linha por linha
    If varContagemLinha = 0 Then
        Open varCaminhoArquivo For Input As #1
        varContagemLinha = 0
        
        While Not EOF(1)
            Line Input #1, varLinha
            varMatrizLinha(varContagemLinha) = varLinha
            varContagemLinha = varContagemLinha + 1
        Wend
        Close #1
    End If
    Close #1

    contadorFunc = DLast("FuncionarioID", "tblFuncionario", "EmpresaID=" & varEmpresaID)
    
    For i = 0 To varContagemLinha - 1
    
        If Mid(varMatrizLinha(i), 1, 5) = "COMP:" Then
            varCompetencia = "01/" & Mid(varMatrizLinha(i), 7, 7)
        End If
        
        If Mid(varMatrizLinha(i), 1, 10) = "REM SEM 13" Then
        
            i = i + 3
Proximo:
            varCat = Mid(varMatrizLinha(i), 91, 2)
            If varCat <> "11" Then
            
                varPIS = Replace(fncTiraAcentoEspacoCaracteres(Mid(varMatrizLinha(i), 50, 18)), " ", "")
                
                If varPIS = Empty Or IsNull(varPIS) Or IsNumeric(varPIS) = False Then
                    GoTo Proximo1
                Else
            
                    If IsNull(DLast("FuncionarioID", "tblFuncionario", "PIS='" & varPIS & "' and EmpresaID=" & varEmpresaID)) = True Then
                        contadorFunc = contadorFunc + 1
                        varFuncionarioID = contadorFunc
                        varNome = Mid(varMatrizLinha(i), 1, 50)
                        varCBO = Replace(Mid(varMatrizLinha(i), 125, 15), " ", "")
                        varCarteira = 0
                        varSerie = 0
                        varDataNascto = "01/01/1990"
                        varDataAdm = Replace(Mid(varMatrizLinha(i), 75, 14), " ", "")
                        DoCmd.SetWarnings False
                        DoCmd.RunSQL "INSERT INTO tblFuncionario(EmpresaID, FuncionarioID, Nome, PIS, CBO, CarteiraProfissional, SerieProssicional, DataNascimento, DataAdmissao, Observacao) VALUES ( " & varEmpresaID & ", " & varFuncionarioID & ", '" & varNome & "', '" & varPIS & "', '" & varCBO & "', '" & varCarteira & "', '" & varSerie & "', '" & varDataNascto & "', '" & varDataAdm & "', '" & varObservacao & "')"
                        DoCmd.SetWarnings True
                    Else
                        varFuncionarioID = DLast("FuncionarioID", "tblFuncionario", "PIS='" & varPIS & "' and EmpresaID=" & varEmpresaID)
                    End If
                    
                    varCodDem = Replace(Mid(varMatrizLinha(i), 120, 7), " ", "")
                    If varCodDem = "J" Or varCodDem = "I1" Or varCodDem = "I2" Or varCodDem = "I3" Then
                        varDataDem = Replace(Mid(varMatrizLinha(i), 107, 12), " ", "")
                        DoCmd.SetWarnings False
                        DoCmd.RunSQL "UPDATE tblFuncionario Set DataDemissao = '" & varDataDem & "' WHERE EmpresaID  = " & varEmpresaID & " and FuncionarioID = " & varFuncionarioID
                        DoCmd.SetWarnings True
                    End If
                    
                    i = i + 1
                    
                    
                    varBaseFgts = Mid(varMatrizLinha(i), 9, 9)
                    varValorFgts = varBaseFgts * 0.08
                    varPago = 0
                    varValorPago = 0
                    varDataPagto = Empty
                    
                    varComp = 0
                    
                    DoCmd.SetWarnings False
                    DoCmd.RunSQL "INSERT INTO tblLancamento(EmpresaID, FuncionarioID, Competencia, Comp13, BaseFGTS, ValorFGTS, Pago, DataPagto, ValorPago) Values (" & varEmpresaID & ", " & varFuncionarioID & ", '" & varCompetencia & "', " & varComp & ", '" & varBaseFgts & "', '" & varValorFgts & "', '" & varPago & "', '" & varDataPagto & "', '" & varValorPago & "')"
                    DoCmd.SetWarnings True
                
                    
                    If Mid(varCompetencia, 4, 2) = 11 Or Mid(varCompetencia, 4, 2) = 12 Then
                
                        varBaseFgts = Mid(varMatrizLinha(i), 30, 9)
                        varValorFgts = varBaseFgts * 0.08
                        varPago = 0
                        varValorPago = 0
                        varDataPagto = Empty
                        
                        varComp = -1
                        
                        DoCmd.SetWarnings False
                        DoCmd.RunSQL "INSERT INTO tblLancamento(EmpresaID, FuncionarioID, Competencia, Comp13, BaseFGTS, ValorFGTS, Pago, DataPagto, ValorPago) Values (" & varEmpresaID & ", " & varFuncionarioID & ", '" & varCompetencia & "', " & varComp & ", '" & varBaseFgts & "', '" & varValorFgts & "', '" & varPago & "', '" & varDataPagto & "', '" & varValorPago & "')"
                        DoCmd.SetWarnings True
                    End If
                    
                End If 'PIS
            Else
                i = i + 1
            End If 'Cat
            i = i + 1
            GoTo Proximo
        
        End If 'REM SEM 13
        
Proximo1:
    
    Next
        
    MsgBox "Fim da Importação dos Dados!!!", vbInformation + vbCritical
End Function
Function fncImportaDadosFGTSTXT()
Dim varLinha As String
Dim varContagemLinha As Double
Dim varMatrizLinha(10000) As String
Dim varCompetencia As String
Dim varEmpresaID As Integer
Dim varFuncionarioID As Integer
Dim varRstFuncionario As DAO.Recordset
Dim varRstLancamento As DAO.Recordset
Dim varInicio As Integer
Dim varNome As String
Dim varPIS As String
Dim varCBO As String
Dim varCarteira As String
Dim varSerie As String
Dim varDataNascto As String
Dim varDataAdm As String
Dim varCentavos As Double
Dim varBaseFgts As Double
Dim varValorFgts As Double
Dim varDataPagto As String
Dim varObservacao As String
Dim varStrSql As String
Dim varPago As String
Dim varComp As String
Dim varValorPago As Double
Dim i As Integer
Dim p As Integer

    Close #1
    Open "C:\SK\FGTSTXT.TXT" For Input As #1
        Line Input #1, varLinha
        varContagemLinha = 0
        varInicio = 1
        For i = 1 To Len(varLinha)
            If Mid(varLinha, i, 1) = Chr(10) Then ' Se tiver um enter é uma linha
                varMatrizLinha(varContagemLinha) = Replace(Mid(varLinha, varInicio, i - varInicio), Chr(10), "")
                varContagemLinha = varContagemLinha + 1
                varInicio = i
            End If
        Next
    Close #1
    'Se for 0 quer dizer que o arquivo veio linha por linha
    If varContagemLinha = 0 Then
        Open "C:\SK\FGTSTXT.TXT" For Input As #1
        varContagemLinha = 0
        
        While Not EOF(1)
            Line Input #1, varLinha
            varMatrizLinha(varContagemLinha) = varLinha
            varContagemLinha = varContagemLinha + 1
        Wend
        Close #1
    End If
    Close #1
    
    For i = 0 To varContagemLinha - 1
        varEmpresaID = CDbl(Mid(varMatrizLinha(i), 1, 3))
        varFuncionarioID = CDbl(Mid(varMatrizLinha(i), 4, 4))
        varCompetencia = "01/" & Mid(varMatrizLinha(i), 15, 2) & "/" & Mid(varMatrizLinha(i), 11, 4)
        varNome = Mid(varMatrizLinha(i), 17, 30)
        varPIS = Mid(varMatrizLinha(i), 47, 11)
        varCBO = Mid(varMatrizLinha(i), 58, 6)
        varCarteira = Mid(varMatrizLinha(i), 64, 6)
        varSerie = Mid(varMatrizLinha(i), 70, 3)
        varDataNascto = Mid(varMatrizLinha(i), 73, 2) & "/" & Mid(varMatrizLinha(i), 75, 2) & "/" & Mid(varMatrizLinha(i), 77, 4)
        varDataAdm = Mid(varMatrizLinha(i), 81, 2) & "/" & Mid(varMatrizLinha(i), 83, 2) & "/" & Mid(varMatrizLinha(i), 85, 4)
        varBaseFgts = Mid(varMatrizLinha(i), 89, 13) & "," & Mid(varMatrizLinha(i), 102, 2)
        varValorFgts = Mid(varMatrizLinha(i), 104, 11) & "," & Mid(varMatrizLinha(i), 115, 2)
        varDataPagto = Mid(varMatrizLinha(i), 117, 2) & "/" & Mid(varMatrizLinha(i), 119, 2) & "/" & Mid(varMatrizLinha(i), 121, 4)
        varObservacao = Mid(varMatrizLinha(i), 125, 42)
        Set varRstFuncionario = CurrentDb.OpenRecordset("SELECT tblFuncionario.EmpresaID, tblFuncionario.FuncionarioID, tblFuncionario.Nome, tblFuncionario.PIS, tblFuncionario.CBO, tblFuncionario.CarteiraProfissional, tblFuncionario.SerieProssicional, tblFuncionario.DataNascimento, tblFuncionario.DataAdmissao, tblFuncionario.Observacao FROM tblFuncionario WHERE (((tblFuncionario.EmpresaID)= " & varEmpresaID & ") AND ((tblFuncionario.FuncionarioID)= " & varFuncionarioID & "))")
        If varRstFuncionario.RecordCount > 0 Then
            If Mid(varMatrizLinha(i), 15, 2) = 13 Then
                varComp = -1
                varCompetencia = "01/" & "12/" & Mid(varMatrizLinha(i), 11, 4)
            Else
                varComp = 0
            End If
            If varDataPagto <> "00/00/0000" Then
                varPago = -1
                varValorPago = varValorFgts
            Else
                varPago = 0
                varValorPago = 0
                varDataPagto = Empty
            End If
'            If varRstFuncionario!Observacao <> varObservacao Then
                DoCmd.SetWarnings False
                DoCmd.RunSQL "UPDATE tblFuncionario Set Observacao = '" & varObservacao & "' WHERE EmpresaID  = " & varEmpresaID & " and FuncionarioID = " & varFuncionarioID
               'DoCmd.RunSQL "UPDATE tblHoleriteIte Set Pensionist = " & PensionistaID & " WHERE HoleriteID = " & HoleriteID   & " and EventoIDfff   = " & CodigoPensao(i)
                DoCmd.SetWarnings True
'            End If
            
            
            If varBaseFgts <> 0 Then
                Set varRstFuncionario = CurrentDb.OpenRecordset("SELECT tblLancamento.EmpresaID, tblLancamento.FuncionarioID, tblLancamento.Competencia, tblLancamento.Comp13 FROM tblLancamento WHERE (((tblLancamento.EmpresaID)= " & varEmpresaID & ") AND ((tblLancamento.FuncionarioID)= " & varFuncionarioID & ") AND ((tblLancamento.Competencia)=Format('" & varCompetencia & "','dd/MM/yyyy')) AND ((tblLancamento.Comp13)= " & varComp & "))")
                If varRstFuncionario.RecordCount = 0 Then
                    DoCmd.SetWarnings False
                    DoCmd.RunSQL "INSERT INTO tblLancamento(EmpresaID, FuncionarioID, Competencia, Comp13, BaseFGTS, ValorFGTS, Pago, DataPagto, ValorPago) Values (" & varEmpresaID & ", " & varFuncionarioID & ", '" & varCompetencia & "', " & varComp & ", '" & varBaseFgts & "', '" & varValorFgts & "', '" & varPago & "', '" & varDataPagto & "', '" & varValorPago & "')"
                    DoCmd.SetWarnings True
                End If
            End If
        Else
            DoCmd.SetWarnings False
            DoCmd.RunSQL "INSERT INTO tblFuncionario(EmpresaID, FuncionarioID, Nome, PIS, CBO, CarteiraProfissional, SerieProssicional, DataNascimento, DataAdmissao, Observacao) VALUES ( " & varEmpresaID & ", " & varFuncionarioID & ", '" & varNome & "', '" & varPIS & "', '" & varCBO & "', '" & varCarteira & "', '" & varSerie & "', '" & varDataNascto & "', '" & varDataAdm & "', '" & varObservacao & "')"
            DoCmd.SetWarnings True
            If Mid(varMatrizLinha(i), 15, 2) = 13 Then
                varComp = -1
            Else
                varComp = 0
            End If
            If varDataPagto <> "00/00/0000" Then
                varPago = -1
                varValorPago = varValorFgts
            Else
                varPago = 0
                varValorPago = 0
                varDataPagto = Empty
            End If
            If varBaseFgts <> 0 Then
                DoCmd.SetWarnings False
                DoCmd.RunSQL "INSERT INTO tblLancamento(EmpresaID, FuncionarioID, Competencia, Comp13, BaseFGTS, ValorFGTS, Pago, DataPagto, ValorPago) Values (" & varEmpresaID & ", " & varFuncionarioID & ", '" & varCompetencia & "', " & varComp & ", '" & varBaseFgts & "', '" & varValorFgts & "', '" & varPago & "', '" & varDataPagto & "', '" & varValorPago & "')"
                DoCmd.SetWarnings True
            End If
        End If
        varRstFuncionario.Close
    Next
    MsgBox "Fim da Importação dos Dados!!!", vbInformation + vbCritical
End Function

Function fncImportaIndices()
Dim varLinha As String
Dim varContagemLinha As Double
Dim varMatrizLinha(25000) As String

Dim varCompetencia As String

Dim varValor As Double
Dim varIndice As Double
Dim varDataPagto As String
Dim varTipo As String

Dim i As Integer
Dim p As Integer

Dim nStatus As Variant
Dim nMess As String
    
    '***************** IMPORTAÇÃO DA MULTA *****************
    Close #1
    Open "C:\SK\INDICES.TXT" For Input As #1
    varContagemLinha = 0
    While Not EOF(1)
        Line Input #1, varLinha
        varMatrizLinha(varContagemLinha) = varLinha
        varContagemLinha = varContagemLinha + 1
    Wend
    
    Let nStatus = SysCmd(acSysCmdClearStatus)
    
    i = 0
    
    Close #1
    DoCmd.SetWarnings False
    DoCmd.RunSQL "DELETE * FROM tblMulta"
    DoCmd.SetWarnings True
    
    For i = 0 To varContagemLinha - 1
        varCompetencia = "01/" & Mid(varMatrizLinha(i), 5, 2) & "/" & Mid(varMatrizLinha(i), 1, 4)
        varTipo = Mid(varMatrizLinha(i), 9, 2)
        varValorIndice = Mid(varMatrizLinha(i), 21, 1) & "," & Mid(varMatrizLinha(i), 23, 9)
        varDataPagto = Mid(varMatrizLinha(i), 11, 2) & "/" & Mid(varMatrizLinha(i), 14, 2) & "/" & Mid(varMatrizLinha(i), 17, 4)
            
            DoCmd.SetWarnings False
            DoCmd.RunSQL "INSERT INTO tblMulta(CompetenciaID, Campo1, DataIndice, Indice) Values ('" & varCompetencia & "', '" & varTipo & "', '" & varDataPagto & "', '" & varValorIndice & "')"
            DoCmd.SetWarnings True
        
    Next
    
    Let nStatus = SysCmd(acSysCmdClearStatus)
    MsgBox "Fim da Importação dos Indices!!!", vbInformation + vbCritical

End Function

Function fncLancamentos()
Dim varLinha As String
Dim varContagemLinha As Double
Dim varMatrizLinha(10000) As String
Dim varCompetencia As String
Dim varEmpresaID As Integer
Dim varFuncionarioID As Integer
Dim varRstFuncionario As DAO.Recordset
Dim varRstLancamento As DAO.Recordset
Dim varInicio As Integer
Dim varNome As String
Dim varCPF As String
Dim varPIS As String
Dim varCBO As String
Dim varCarteira As String
Dim varSerie As String
Dim varDataNascto As String
Dim varDataAdm As String
Dim varDataDem As String
Dim varCentavos As Double
Dim varBaseFgts As Double
Dim varValorFgts As Double
Dim varDataPagto As String
Dim varObservacao As String
Dim varStrSql As String
Dim varPago As String
Dim varComp As String
Dim varValorPago As Double
Dim varFGSTRescisao As Double
Dim i As Integer
Dim p As Integer
Dim varNamePath As String
Dim varQuantidadeSplit As Integer
Dim varDados As Variant

    
    varNamePath = "C:\SK\AtualizaDados.csv"
    
    varFuncaoInterna = Dir(varNamePath, vbArchive) 'Localiza se existe esse arquivo, caso contrario retorna o nome do arquivo mais proximo
    If "AtualizaDados.csv" <> varFuncaoInterna Then
        MsgBox "Arquivo C:\SK\AtualizaDados.CSV não encontrado!!!", vbInformation + vbCritical
        Exit Function
    End If

    Close #1
    Open varNamePath For Input As #1
    varContagemLinha = 0
    
    While Not EOF(1)
        Line Input #1, varLinha
        varMatrizLinha(varContagemLinha) = varLinha
        varContagemLinha = varContagemLinha + 1
    Wend
    Close #1
    
    For i = 1 To varContagemLinha - 1
        varDados = Split(varMatrizLinha(i), ";")
    
    
        varEmpresaID = varDados(0)
        varFuncionarioID = varDados(1)
        varNome = varDados(2)
        varCPF = varDados(3)
        varPIS = varDados(4)
        varCBO = varDados(5)
        varCarteira = varDados(6)
        varSerie = varDados(7)
        varDataNascto = varDados(8)
        varDataAdm = varDados(9)
        varCompetencia = varDados(10)
        varComp = varDados(11)
        varBaseFgts = varDados(12)
        varValorFgts = varDados(13)
        varPago = varDados(14)
        varDataPagto = varDados(15)
        varValorPago = varDados(16)
        varFGSTRescisao = varDados(17)
        varDataDem = varDados(18)
        
        
        Set varRstFuncionario = CurrentDb.OpenRecordset("SELECT * FROM tblFuncionario WHERE (((tblFuncionario.EmpresaID)= " & varEmpresaID & ") AND ((tblFuncionario.FuncionarioID)= " & varFuncionarioID & "))")
        If varRstFuncionario.RecordCount > 0 Then
            
            If IsNull(varRstFuncionario!CPF) Or varCPF <> varRstFuncionario!CPF Then
                DoCmd.SetWarnings False
                DoCmd.RunSQL "UPDATE tblFuncionario Set CPF = '" & varCPF & "' WHERE EmpresaID  = " & varEmpresaID & " and FuncionarioID = " & varFuncionarioID
                DoCmd.SetWarnings True
            End If
            
            If varDataDem <> "" Then
                DoCmd.SetWarnings False
                DoCmd.RunSQL "UPDATE tblFuncionario Set DataDemissao = '" & varDataDem & "' WHERE EmpresaID  = " & varEmpresaID & " and FuncionarioID = " & varFuncionarioID
                DoCmd.SetWarnings True
            End If
           
            If varBaseFgts <> 0 Then
                Set varRstFuncionario = CurrentDb.OpenRecordset("SELECT tblLancamento.EmpresaID, tblLancamento.FuncionarioID, tblLancamento.Competencia, tblLancamento.Comp13 FROM tblLancamento WHERE (((tblLancamento.EmpresaID)= " & varEmpresaID & ") AND ((tblLancamento.FuncionarioID)= " & varFuncionarioID & ") AND ((tblLancamento.Competencia)=Format('" & varCompetencia & "','dd/MM/yyyy')) AND ((tblLancamento.Comp13)= " & varComp & "))")
                If varRstFuncionario.RecordCount = 0 Then
                    DoCmd.SetWarnings False
                    DoCmd.RunSQL "INSERT INTO tblLancamento(EmpresaID, FuncionarioID, Competencia, Comp13, BaseFGTS, ValorFGTS, Pago, DataPagto, ValorPago) Values (" & varEmpresaID & ", " & varFuncionarioID & ", '" & varCompetencia & "', " & varComp & ", '" & varBaseFgts & "', '" & varValorFgts & "', '" & varPago & "', '" & varDataPagto & "', '" & varValorPago & "')"
                    DoCmd.SetWarnings True
                End If
            End If
        Else
            DoCmd.SetWarnings False
            DoCmd.RunSQL "INSERT INTO tblFuncionario(EmpresaID, FuncionarioID, Nome, CPF, PIS, CBO, CarteiraProfissional, SerieProssicional, DataNascimento, DataAdmissao, Observacao) VALUES ( " & varEmpresaID & ", " & varFuncionarioID & ", '" & varNome & "', '" & varCPF & "', '" & varPIS & "', '" & varCBO & "', '" & varCarteira & "', '" & varSerie & "', '" & varDataNascto & "', '" & varDataAdm & "', '" & varObservacao & "')"
            DoCmd.SetWarnings True
            
            If varBaseFgts <> 0 Then
                DoCmd.SetWarnings False
                DoCmd.RunSQL "INSERT INTO tblLancamento(EmpresaID, FuncionarioID, Competencia, Comp13, BaseFGTS, ValorFGTS, Pago, DataPagto, ValorPago) Values (" & varEmpresaID & ", " & varFuncionarioID & ", '" & varCompetencia & "', " & varComp & ", '" & varBaseFgts & "', '" & varValorFgts & "', '" & varPago & "', '" & varDataPagto & "', '" & varValorPago & "')"
                DoCmd.SetWarnings True
            End If
        varRstFuncionario.Close
        End If
    Next
    MsgBox "Fim da Importação dos Lançamentos!!!", vbInformation + vbCritical
End Function
Function fncImportaCOEFJAM()

Dim varLinha As String
Dim varContagemLinha As Double
Dim varMatrizLinha(25000) As String

Dim varCompetencia As String

Dim varValor As Double
Dim varIndice As Double
Dim i As Integer
Dim nStatus As Variant
Dim nMess As String

    ' ***************** IMPORTAÇÃO DO COEFJAM *****************

    Close #1
    Open "C:\SK\COEFJAM.TXT" For Input As #1
    varContagemLinha = 0
    While Not EOF(1)
        Line Input #1, varLinha
        varMatrizLinha(varContagemLinha) = varLinha
        varContagemLinha = varContagemLinha + 1
    Wend
    
    DoCmd.SetWarnings False
    DoCmd.RunSQL "DELETE * FROM tblCoefjam"
    DoCmd.SetWarnings True

    For i = 0 To varContagemLinha - 1
        varCompetencia = "01/" & Mid(varMatrizLinha(i), 4, 7)

        varValor = "0," & Mid(varMatrizLinha(i), 14, 6)

        Let nMess = "Salvando COEFJAM - Competencia " & varCompetencia
        Let nStatus = SysCmd(acSysCmdSetStatus, nMess)

        DoCmd.SetWarnings False
        DoCmd.RunSQL "INSERT INTO tblCoefjam(CompetenciaID, Indice) Values ('" & varCompetencia & "', '" & varValor & "')"
        DoCmd.SetWarnings True
    Next
    
    MsgBox "Fim da Importação do COEFJAM!!!", vbInformation + vbCritical

End Function
