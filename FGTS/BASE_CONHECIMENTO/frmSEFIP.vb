Option Compare Database
Option Explicit
Private Sub btnGerar_Click()
On Error GoTo TratarErro
Dim varCondicao As String
    
    varCondicao = " EmpresaID = " & Me.cmbEmpresaDe
    If IsNull(Me.cmbEmpresaDe.Column(1)) = True Then
        MsgBox "Favor Prencher os Campos Necessários....", vbInformation, varNomeProjeto
    Else
        fncSEFIP
    End If
    Exit Sub
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
Function fncSEFIP()
Dim varEmpresa As String
Dim varCNPJ As String
Dim varComp As String
Dim varData As String
Dim i As Integer
Dim varPIS As String
Dim varRstEmpresa As DAO.Recordset
Dim varRstFuncionario As DAO.Recordset
Dim varEnderecoEmpresa As String
Dim varCEP As String
Dim varFone As String
Dim varRAt As String
Dim varTerceiro As String
Dim varCodigoRecolhimentoGPS As String

    Open "C:\SK\SEFIP.RE" For Output As #1
    varData = Format(Me.txtCompetencia, "YYYYMM")
    Set varRstEmpresa = CurrentDb.OpenRecordset("SELECT * FROM tblEmpresa WHERE tblEmpresa.EmpresaID = " & Me.cmbEmpresaDe)
    If varRstEmpresa.RecordCount > 0 Then
        varRstEmpresa.MoveLast
        varRstEmpresa.MoveFirst
   
    

'REGISTRO 00

        varEnderecoEmpresa = varRstEmpresa!Endereco & " " & varRstEmpresa!Numero
        varCEP = Replace(fncTiraAcentoEspacoCaracteres(varRstEmpresa!CEP), " ", "")
        varFone = Replace(fncTiraAcentoEspacoCaracteres(varRstEmpresa!FoneContato), " ", "")
        
        Print #1, "00" & Space(51) & "11" & _
        Space(14 - Len(Replace(fncTiraAcentoEspacoCaracteres(varRstEmpresa!CNPJ), " ", ""))) & _
        Replace(fncTiraAcentoEspacoCaracteres(varRstEmpresa!CNPJ), " ", "") & _
        Mid(fncTiraAcentoEspacoCaracteres(varRstEmpresa!RazaoSocial), 1, 30) & _
        Space(30 - Len(Mid(fncTiraAcentoEspacoCaracteres(varRstEmpresa!RazaoSocial), 1, 30))) & _
        "DEPTO PESSOAL" & Space(7) & _
        Mid(fncTiraAcentoEspacoCaracteres(varEnderecoEmpresa), 1, 50) & _
        Space(50 - Len(Mid(fncTiraAcentoEspacoCaracteres(varEnderecoEmpresa), 1, 50))) & _
        Mid(fncTiraAcentoEspacoCaracteres(varRstEmpresa!Bairro), 1, 20) & _
        Space(20 - Len(Mid(fncTiraAcentoEspacoCaracteres(varRstEmpresa!Bairro), 1, 20))) & varCEP & _
        Mid(fncTiraAcentoEspacoCaracteres(varRstEmpresa!Cidade), 1, 20) & _
        Space(20 - Len(Mid(fncTiraAcentoEspacoCaracteres(varRstEmpresa!Cidade), 1, 20))) & _
        varRstEmpresa!UF & _
        Space(12 - (Len(varFone))) & _
        varFone & Space(60) & _
        IIf(Format(Me.txtCompetencia, "MM") <> 13, varData, Format(Me.txtCompetencia, "YYYY") & "13") & _
        "1151" & Space(9) & _
        "1" & Space(15) & "1" & _
        Space(14 - Len(Replace(fncTiraAcentoEspacoCaracteres(varRstEmpresa!CNPJ), " ", ""))) & _
        Replace(fncTiraAcentoEspacoCaracteres(varRstEmpresa!CNPJ), " ", "") & Space(18) & "*"



    End If

'  REGISTRO 10
        
        If varData < "199810" Then
            varRAt = Space(2)
            varTerceiro = Space(4)
            varCodigoRecolhimentoGPS = Space(4)
        Else
            varRAt = Format(varRstEmpresa!RAT, "0") & "0"
            varTerceiro = IIf(IsNull(varRstEmpresa!OutrasEntidades) = True, Space(4), Format(varRstEmpresa!OutrasEntidades, "0000"))
            varCodigoRecolhimentoGPS = "2100"
        End If
        
        Print #1, "10" & "1" & _
        Space(14 - Len(Replace(fncTiraAcentoEspacoCaracteres(varRstEmpresa!CNPJ), " ", ""))) & _
        Replace(fncTiraAcentoEspacoCaracteres(varRstEmpresa!CNPJ), " ", "") & _
        "000000000000000000000000000000000000" & _
        Mid(fncTiraAcentoEspacoCaracteres(varRstEmpresa!RazaoSocial), 1, 40) & _
        Space(40 - Len(Mid(fncTiraAcentoEspacoCaracteres(varRstEmpresa!RazaoSocial), 1, 40))) & _
        Mid(fncTiraAcentoEspacoCaracteres(varEnderecoEmpresa), 1, 50) & _
        Space(50 - Len(Mid(fncTiraAcentoEspacoCaracteres(varEnderecoEmpresa), 1, 50))) & _
        Mid(fncTiraAcentoEspacoCaracteres(varRstEmpresa!Bairro), 1, 20) & _
        Space(20 - Len(Mid(fncTiraAcentoEspacoCaracteres(varRstEmpresa!Bairro), 1, 20))) & _
        Format(varCEP, "00000000") & _
        Mid(fncTiraAcentoEspacoCaracteres(varRstEmpresa!Cidade), 1, 20) & _
        Space(20 - Len(Mid(fncTiraAcentoEspacoCaracteres(varRstEmpresa!Cidade), 1, 20))) & _
        varRstEmpresa!UF & Space(12 - (Len(varFone))) & _
        varFone & "N" & varRstEmpresa!CNAE & "P" & Format(varRAt, "00") & "0" & _
        varRstEmpresa!SImples & Format(varRstEmpresa!FPAS, "000") & _
        varTerceiro & _
        Format(varCodigoRecolhimentoGPS, "0000") & Space(5) & _
        "000000000000000" & "000000000000000" & _
        "000000000000000000000000000000" & Space(16) & _
        "000000000000000000000000000000000000000000000" & Space(4) & "*"







'  REGISTRO 30
    varComp = Format(Me.txtCompetencia, "MMYYYY")
    Set varRstFuncionario = CurrentDb.OpenRecordset("SELECT tblEmpresa.EmpresaID, tblEmpresa.CNPJ, tblFuncionario.FuncionarioID, tblFuncionario.Nome, tblFuncionario.PIS, tblFuncionario.CBO, tblFuncionario.CarteiraProfissional, tblFuncionario.SerieProssicional, tblFuncionario.DataNascimento, tblFuncionario.DataAdmissao, tblLancamento.Competencia, tblLancamento.BaseFGTS FROM (tblEmpresa INNER JOIN tblFuncionario ON tblEmpresa.EmpresaID = tblFuncionario.EmpresaID) INNER JOIN tblLancamento ON (tblFuncionario.FuncionarioID = tblLancamento.FuncionarioID) AND (tblFuncionario.EmpresaID = tblLancamento.EmpresaID) WHERE (tblEmpresa.EmpresaID= " & Me.cmbEmpresaDe & " AND (tblFuncionario.FuncionarioID Between " & Me.cmbFuncionarioDe & "  And " & Me.cmbFuncionarioAte & ") AND (Format(tblLancamento.Competencia, 'mmyyyy') = " & varComp & "))ORDER BY tblFuncionario.PIS, tblFuncionario.DataAdmissao")
    If varRstFuncionario.RecordCount > 0 Then
        varRstFuncionario.MoveLast
        varRstFuncionario.MoveFirst
        varPIS = 0
        For i = 1 To varRstFuncionario.RecordCount
        
'            If varRstFuncionario!PIS = varPIS Then
                Print #1, "301" & _
                Space(14 - Len(Replace(fncTiraAcentoEspacoCaracteres(varRstEmpresa!CNPJ), " ", ""))) & _
                Replace(fncTiraAcentoEspacoCaracteres(varRstEmpresa!CNPJ), " ", "") & _
                Space(15) & varRstFuncionario!PIS & Format(varRstFuncionario!DataAdmissao, "ddmmyyyy") & "01" & _
                Mid(fncTiraAcentoEspacoCaracteres(varRstFuncionario!Nome), 1, 70) & Space(70 - Len(Mid(fncTiraAcentoEspacoCaracteres(varRstFuncionario!Nome), 1, 70))) & _
                Space(11 - Len(Mid(varRstFuncionario!FuncionarioID, 1, 11))) & Mid(varRstFuncionario!FuncionarioID, 1, 11) & _
                Format(varRstFuncionario!CarteiraProfissional, "0000000") & IIf(varRstFuncionario!SerieProssicional = 0, "00001", Format(varRstFuncionario!SerieProssicional, "00000")) & _
                Format(varRstFuncionario!DataAdmissao, "ddmmyyyy") & Format(varRstFuncionario!DataNascimento, "ddmmyyyy") & "0" & Format(Mid(varRstFuncionario!CBO, 1, 4), "0000") & _
                Replace(Format(varRstFuncionario!BaseFGTS, "0000000000000.00"), ",", "") & "000000000000000  05000000000000000000000000000000000000000000000000000000000000" & Space(98) & "*"
'            Else
'                Print #1, "301" & varCNPJ & "               " & varRstFuncionario!PIS & Format(varRstFuncionario!DataAdmissao, "ddmmyyyy") & "01" & _
'                Mid(fncTiraAcentoEspacoCaracteres(varRstFuncionario!Nome), 1, 70) & Space(70 - Len(Mid(fncTiraAcentoEspacoCaracteres(varRstFuncionario!Nome), 1, 70))) & _
'                Space(11 - Len(Mid(varRstFuncionario!FuncionarioID, 1, 11))) & Mid(varRstFuncionario!FuncionarioID, 1, 11) & _
'                Format(varRstFuncionario!CarteiraProfissional, "0000000") & IIf(varRstFuncionario!SerieProssicional = 0, "00001", Format(varRstFuncionario!SerieProssicional, "00000")) & _
'                Format(varRstFuncionario!DataAdmissao, "ddmmyyyy") & Format(varRstFuncionario!DataNascimento, "ddmmyyyy") & "0" & Format(Mid(varRstFuncionario!CBO, 1, 4), "0000") & _
'                Replace(Format(varRstFuncionario!BaseFGTS, "0000000000000.00"), ",", "") & "000000000000000    000000000000000000000000000000000000000000000000000000000000                                                                                                  *"
'                varPIS = varRstFuncionario!PIS
'            End If
        varRstFuncionario.MoveNext
        Next
        varRstEmpresa.Close
        varRstFuncionario.Close
        
        Print #1, "90999999999999999999999999999999999999999999999999999                                                                                                                                                                                                                                                                                                                  *"
        MsgBox "Arquivo gerado com Sucesso....", vbInformation, varNomeProjeto
    Else
        MsgBox "Não existe dados para geração do arquivo SEFIP.RE....", vbInformation, varNomeProjeto
    End If
    
    Close #1

End Function

