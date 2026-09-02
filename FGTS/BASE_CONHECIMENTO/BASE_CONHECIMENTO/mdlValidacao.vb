Option Compare Database
Option Explicit
Function fncSelecionarTexto(Campo As Control)
On Error Resume Next

    Campo.SetFocus

Campo.SelStart = 0
    Campo.SelLength = Len(Campo.Text)

End Function
Function fncValidarData(CampoData As Control, Optional DataSuperiorValida As Boolean = False) As Boolean
On Error Resume Next
    
    fncValidarData = True
    If DataSuperiorValida = False Then
        If Not IsDate(CampoData.Text) Or CDate(CampoData.Text) > CDate(Now) Then
            MsgBox "A data não pode ser superior a Data Atual!", vbExclamation, varNomeProjeto
            CampoData.Text = Empty
            fncSelecionarTexto CampoData

            fncValidarData = False
        End If
    End If
End Function
Function fncValidarCPF(CPF As String) As Boolean
On Error GoTo TrataErro

    Dim Soma As Integer
    Dim resto As Integer
    Dim i As Integer
    Dim strCPF As String

    If CPF = "000.000.000-00" Or CPF = "111.111.111-11" Or CPF = "222.222.222-22" Or CPF = "333.333.333-33" Or CPF = "444.444.444-44" Or CPF = "555.555.555-55" Or CPF = "666.666.666-66" Or CPF = "777.777.777-77" Or CPF = "888.888.888-88" Or CPF = "999.999.999-99" Then
        fncValidarCPF = False
        Exit Function
    End If

    'Retira os pontos e os traços do CPF, já que o ACCESS não possui o Replace
    For i = 1 To Len(CPF)
        If Mid(CPF, i, 1) = "." Or Mid(CPF, i, 1) = "-" Then
        Else
            strCPF = strCPF & Mid(CPF, i, 1)
        End If
    Next i

    'Se o CPF não tiver 11 digitos não é valido
    If Len(strCPF) <> 11 Then
        fncValidarCPF = False
        Exit Function
    End If

    Soma = 0

    'Faz a somatório dos digitos com o numeros de suas casas até antes dos digito verificador
    For i = 1 To 9
        Soma = Soma + Val(Mid$(strCPF, i, 1)) * (11 - i)
    Next i

    'Pega o resto da divisão da soma
    resto = 11 - (Soma - (Int(Soma / 11) * 11))

    'Valida o resultado do resto com o valor do primeiro digito
    If resto = 10 Or resto = 11 Then resto = 0
        If resto <> Val(Mid$(strCPF, 10, 1)) Then
        fncValidarCPF = False
        Exit Function
    End If

    Soma = 0

    'Faz a somatório de novo incluindo agora o primeiro digito verificador
    For i = 1 To 10
        Soma = Soma + Val(Mid$(strCPF, i, 1)) * (12 - i)
    Next i

    'Pega o resto da divisão da soma
    resto = 11 - (Soma - (Int(Soma / 11) * 11))

    'Valida o resultado da divisão com o ultimo digito verificador
    If resto = 10 Or resto = 11 Then resto = 0
        If resto <> Val(Mid$(strCPF, 11, 1)) Then
        fncValidarCPF = False
        Exit Function
    End If

    'Se a função conseguir chegar até aqui, o CPF é valido
    fncValidarCPF = True

TrataErro:
    fncTratamentoDeErro
End Function
Function fncValidaCNPJ(CNPJ As String) As Boolean
    Dim A, J, i, d1, d2, strCNPJ As String

    For i = 1 To Len(CNPJ)
        If Mid(CNPJ, i, 1) = "." Or Mid(CNPJ, i, 1) = "/" Or Mid(CNPJ, i, 1) = "-" Then
        Else
            strCNPJ = strCNPJ & Mid(CNPJ, i, 1)
        End If
    Next i

    If Len(strCNPJ) = 8 And Val(strCNPJ) > 0 Then
        A = 0
        J = 0
        d1 = 0

        For i = 1 To 7
            A = Val(Mid(strCNPJ, i, 1))
            If (i Mod 2) <> 0 Then
                A = A * 2
            End If

            If A > 9 Then
                J = J + Int(A / 10) + (A Mod 10)
            Else
                J = J + A
            End If
        Next i

        d1 = IIf((J Mod 10) <> 0, 10 - (J Mod 10), 0)

        If d1 = Val(Mid(strCNPJ, 8, 1)) Then
            fncValidaCNPJ = True
        Else
            fncValidaCNPJ = False
        End If
    Else
        If Len(strCNPJ) = 14 And Val(strCNPJ) > 0 Then
            A = 0
            i = 0
            d1 = 0
            d2 = 0
            J = 5

            For i = 1 To 12 Step 1
                A = A + (Val(Mid(strCNPJ, i, 1)) * J)
                J = IIf(J > 2, J - 1, 9)
            Next i

            A = A Mod 11
            d1 = IIf(A > 1, 11 - A, 0)
            A = 0
            i = 0
            J = 6

            For i = 1 To 13 Step 1
                A = A + (Val(Mid(strCNPJ, i, 1)) * J)
                J = IIf(J > 2, J - 1, 9)
            Next i

            A = A Mod 11
            d2 = IIf(A > 1, 11 - A, 0)

            If (d1 = Val(Mid(strCNPJ, 13, 1)) And d2 = Val(Mid(strCNPJ, 14, 1))) Then
                 fncValidaCNPJ = True
            Else
                 fncValidaCNPJ = False
            End If
        Else
            fncValidaCNPJ = False
        End If
    End If
End Function
Function fncValidarPIS(NumeroDoPIS) As Boolean
On Error GoTo TratarErro
Dim ftap As String
Dim Total As String
Dim i As Integer
Dim resto As Integer

    If Val(NumeroDoPIS) = 0 Or Len(NumeroDoPIS) <> 11 Then
        fncValidarPIS = False
        Exit Function
    End If
    ftap = "3298765432"
    Total = 0
    For i = 1 To 10
        Total = Total + Val(Mid(NumeroDoPIS, i, 1)) * Val(Mid(ftap, i, 1))
    Next
    resto = Int(Total Mod 11)
    If resto <> 0 Then
        resto = 11 - resto
    End If
    If resto <> Val(Mid(NumeroDoPIS, 11, 1)) Then
        fncValidarPIS = False
        Exit Function
    End If
    fncValidarPIS = True

TratarErro:
    fncTratamentoDeErro
End Function
Function fncTiraCaracteresEspecias(Palavra) As String
Dim Texto As String
Dim Pos_Acento As Integer
Dim Letra As String
Dim x As Integer
Dim CAcento, SAcento As String
On Error GoTo TratarErro

'Função para retirar caracteres especiais e acentos

    CAcento = "àáâãäèéêëìíîïòóôõöùúûüÀÁÂÃÄÈÉÊËÌÍÎÒÓÔÕÖÙÚÛÜçÇñÑ/\?!;:.,[]{}=+-_*><@#%&|ºª"
    SAcento = "aaaaaeeeeiiiiooooouuuuAAAAAEEEEIIIOOOOOUUUUcCnN                          "
    Texto = ""
        
   If Palavra <> "" Then
        For x = 1 To Len(Palavra)
            Letra = Mid(Palavra, x, 1)
            Pos_Acento = InStr(CAcento, Letra)
            If Pos_Acento > 0 Then
                Letra = Mid(SAcento, Pos_Acento, 1)
            End If
            Texto = Texto & Letra
        Next
    End If
    Exit Function
TratarErro:
    fncTratamentoDeErro
End Function
Function fncTiraAcentoEspacoCaracteres(Palavra) As String
Dim Texto As String
Dim Pos_Acento As Integer
Dim Letra, Frase As String
Dim i, J, N, x, A As Integer
Dim strFrase, strLetra As String
Dim CAcento, SAcento, var2letras, var3letras As String
ReDim listapalavra(0)

On Error GoTo TratarErro

'Função para retirar caracteres especiais e acentos

    CAcento = "àáâãäèéêëìíîïòóôõöùúûüÀÁÂÃÄÈÉÊËÌÍÎÒÓÔÕÖÙÚÛÜçÇñÑ/\?!;:.,[]{}=+-_*><@#%&|ºª()"
    SAcento = "aaaaaeeeeiiiiooooouuuuAAAAAEEEEIIIOOOOOUUUUcCnN                            "
    Texto = ""
        
   If Palavra <> "" Then
        For x = 1 To Len(Palavra)
            Letra = Mid(Palavra, x, 1)
            Pos_Acento = InStr(CAcento, Letra)
            If Pos_Acento > 0 Then
                Letra = Mid(SAcento, Pos_Acento, 1)
            End If
            Texto = Texto & Letra
        Next
    End If

'Função para retirar letras triplicadas

For A = 65 To 90
    var3letras = Chr(A) + Chr(A) + Chr(A)
    var2letras = Chr(A) + Chr(A)
    Texto = Replace(Texto, var3letras, var2letras)
Next

'Função para tirar espaco

'Texto = Replace(Texto, " ", "")

J = -1
strFrase = LCase(Texto + " ")
For i = 1 To Len(strFrase)
    Letra = Mid(strFrase, i, 1)
    If Letra <> " " Then
        Frase = Frase & Letra
    Else
        strLetra = Right(Frase, 1)
        If strLetra <> "" Then
            J = J + 1
            ReDim Preserve listapalavra(J)
            listapalavra(J) = Frase
            Frase = Empty
        End If
    End If
Next

For N = 0 To J
    If listapalavra(N) = "a" Or listapalavra(N) = "na" Or listapalavra(N) = "no" Or listapalavra(N) = "e" Or listapalavra(N) = "o" Or listapalavra(N) = "da" Or listapalavra(N) = "das" Or listapalavra(N) = "de" Or listapalavra(N) = "do" Or listapalavra(N) = "dos" Then
        Frase = Trim(Frase & " " & listapalavra(N))
    Else
        Frase = Trim(Frase & " " & StrConv(listapalavra(N), 3))
    End If
Next
 
fncTiraAcentoEspacoCaracteres = Texto

Exit Function
TratarErro:
    fncTratamentoDeErro
End Function
Function fncEspacoNome(Nome As String) As String
Dim varaux As String
Dim i As Integer
On Error GoTo TratarErro

    For i = 1 To Len(Nome)
        varaux = varaux & (Mid(Nome, i, 1) & "  ")
    Next
    fncEspacoNome = varaux

TratarErro:
    fncTratamentoDeErro
End Function
Function fncEspacoNomeData(Data As Date) As String
Dim varaux, varaux1 As String
Dim i As Integer
On Error GoTo TratarErro

    varaux = CStr(Data)
    varaux = Format(varaux, "dd/mm/yy")
    varaux = Replace(varaux, "/", "")
    For i = 1 To Len(varaux)
        varaux1 = varaux1 & (Mid(varaux, i, 1) & "  ")
    Next
    fncEspacoNomeData = varaux1
    
TratarErro:
    fncTratamentoDeErro
End Function
Function fncValidarFuncionarioRais(EmpresaID As Integer, FuncionarioID As Integer) As String
On Error GoTo TratarErro
Dim varRstFuncionario As DAO.Recordset
Dim varStr As String

    Set varRstFuncionario = CurrentDb.OpenRecordset("SELECT * FROM tblFuncionario WHERE EmpresaID=" & EmpresaID & "AND FuncionarioID=" & FuncionarioID)
    If varRstFuncionario.RecordCount = 1 Then
        If IsNull(varRstFuncionario!PIS) = True Then
            varStr = varStr & "    PIS" & vbCrLf
        End If
        If IsNull(varRstFuncionario!DataNascimento) = True Then
            varStr = varStr & "    Data de Nascimento" & vbCrLf
        End If
        If IsNull(varRstFuncionario!tblNacionalidadeID) = True Then
            varStr = varStr & "    Nacionalidade" & vbCrLf
        End If
        If varRstFuncionario!tblNacionalidadeID <> 10 And IsNull(varRstFuncionario!AnoMigracao) = True Then
            varStr = varStr & "    Ano de Migração" & vbCrLf
        End If
        If IsNull(varRstFuncionario!tblGrauInstrucaoID) = True Then
            varStr = varStr & "    Grau de Instrução" & vbCrLf
        End If
        If IsNull(varRstFuncionario!DeficienteFisico) = True Then
            varStr = varStr & "    Deficiência Física"
        End If
        If IsNull(varRstFuncionario!CPF) = True Then
            varStr = varStr & "    CPF" & vbCrLf
        End If
        If IsNull(varRstFuncionario!CarteiraProfissionalNumero) = True Then
            varStr = varStr & "    Número da Carteira Profissional" & vbCrLf
        End If
        If IsNull(varRstFuncionario!CarteiraProfissionalSerie) = True Then
            varStr = varStr & "    Número de Série da Carteira Profissional" & vbCrLf
        End If
        If IsNull(varRstFuncionario!DataAdmissao) = True Then
            varStr = varStr & "    Data de Admissão" & vbCrLf
        End If
        If IsNull(varRstFuncionario!CodigoAdmissaoRAIS) = True Then
            varStr = varStr & "    Código de Admissão" & vbCrLf
        End If
        If IsNull(varRstFuncionario!SalarioBase) = True Then
            varStr = varStr & "    Salário" & vbCrLf
        End If
        If IsNull(varRstFuncionario!tblTipoCalculoSalarioID) = True Then
            varStr = varStr & "    Tipo de Salário Contratual" & vbCrLf
        End If
        If IsNull(varRstFuncionario!NumeroHoraSemanal) = True Then
            varStr = varStr & "    Horas Semanais" & vbCrLf
        End If
        If IsNull(varRstFuncionario!CBO) = True Then
            varStr = varStr & "    CBO" & vbCrLf
        End If
        If varRstFuncionario!Situacao = 2 Then
           If IsNull(varRstFuncionario!CodigoRescisaoRAIS) = True Then
              varStr = varStr & "    Código de Rescisão RAIS" & vbCrLf
           End If
        End If
        
    End If
    If varStr <> "" Then
        varStr = FuncionarioID & "-" & varRstFuncionario!Nome & ": " & vbCrLf & varStr
    Else
        varStr = ""
    End If
    varRstFuncionario.Close
    fncValidarFuncionarioRais = varStr

TratarErro:
    fncTratamentoDeErro
End Function
Function fncValidarEmpresaRais(EmpresaID As Integer) As String
On Error GoTo TratarErro
Dim varRstEmpresa As DAO.Recordset
Dim varStr As String

    Set varRstEmpresa = CurrentDb.OpenRecordset("SELECT * FROM tblEmpresa WHERE EmpresaID=" & EmpresaID)
    If varRstEmpresa.RecordCount = 1 Then
        If IsNull(varRstEmpresa!Endereco) = True Then
            varStr = varStr & "    Endereço" & vbCrLf
        End If
        If IsNull(varRstEmpresa!Numero) = True Then
            varStr = varStr & "    Número" & vbCrLf
        End If
        If IsNull(varRstEmpresa!Bairro) = True Then
            varStr = varStr & "    Bairro" & vbCrLf
        End If
        If IsNull(varRstEmpresa!CEP) = True Then
            varStr = varStr & "    CEP" & vbCrLf
        End If
        If IsNull(varRstEmpresa!RAISCodigoMunicipio) = True Then
            varStr = varStr & "    Código da Cidade" & vbCrLf
        End If
        If IsNull(varRstEmpresa!Cidade) = True Then
            varStr = varStr & "    Cidade" & vbCrLf
        End If
        If IsNull(varRstEmpresa!UF) = True Then
            varStr = varStr & "    Unidade Federativa(UF)" & vbCrLf
        End If
        If IsNull(varRstEmpresa!CNAE) = True Then
            varStr = varStr & "    CNAE" & vbCrLf
        End If
        If IsNull(varRstEmpresa!RAISNaturezaEstabelecimento) = True Then
            varStr = varStr & "    Natureza Jurídica para a RAIS" & vbCrLf
        End If
        If IsNull(varRstEmpresa!NumeroDeProprietario) = True Then
            varStr = varStr & "    Número de Proprietários" & vbCrLf
        End If
        If IsNull(varRstEmpresa!RAISMesDissidio) = True Then
            varStr = varStr & "    Mês de Dissídio RAIS" & vbCrLf
        End If
        If IsNull(varRstEmpresa!OptanteSimples) = True Then
            varStr = varStr & "    Optante do Simples" & vbCrLf
        End If
        'verificar o sindicato sindical
    End If
    If varStr <> "" Then
        varStr = EmpresaID & "-" & varRstEmpresa!RazaoSocial & ": " & vbCrLf & varStr
    Else
        varStr = ""
    End If
    varRstEmpresa.Close
    fncValidarEmpresaRais = varStr

TratarErro:
    fncTratamentoDeErro
End Function
Function fncValidarEmpresaCentralizadoraSEFIP(EmpresaID As Integer) As String
On Error GoTo TratarErro
Dim varRstEmpresa As DAO.Recordset
Dim varStr As String

    Set varRstEmpresa = CurrentDb.OpenRecordset("SELECT * FROM tblEmpresa WHERE EmpresaID=" & EmpresaID)
    If varRstEmpresa.RecordCount = 1 Then
        If IsNull(varRstEmpresa!CNPJ) = True Then
            varStr = varStr & "    CNPJ/CEI/CPF" & vbCrLf
        End If
        If IsNull(varRstEmpresa!Endereco) = True Then
            varStr = varStr & "    Endereço" & vbCrLf
        End If
        If IsNull(varRstEmpresa!Numero) = True Then
            varStr = varStr & "    Número" & vbCrLf
        End If
        If IsNull(varRstEmpresa!Bairro) = True Then
            varStr = varStr & "    Bairro" & vbCrLf
        End If
        If IsNull(varRstEmpresa!CEP) = True Then
            varStr = varStr & "    CEP" & vbCrLf
        End If
        If IsNull(varRstEmpresa!Cidade) = True Then
            varStr = varStr & "    Cidade" & vbCrLf
        End If
        If IsNull(varRstEmpresa!UF) = True Then
            varStr = varStr & "    Unidade Federativa(UF)" & vbCrLf
        End If
        If IsNull(varRstEmpresa!Telefone1) = True Then
            varStr = varStr & "    Telefone" & vbCrLf
        End If
        If IsNull(varRstEmpresa!CodigoRecolhimentoFGTS) = True Then
            varStr = varStr & "    Código de Recolhimento do FGTS" & vbCrLf
        End If
        If IsNull(varRstEmpresa!Modalidade) = True Then
            varStr = varStr & "    Modalidade" & vbCrLf
        End If
        
    End If
    If varStr <> "" Then
        varStr = EmpresaID & "-" & varRstEmpresa!RazaoSocial & ": " & vbCrLf & varStr
    Else
        varStr = ""
    End If
    varRstEmpresa.Close
    fncValidarEmpresaCentralizadoraSEFIP = varStr

TratarErro:
    fncTratamentoDeErro
End Function
Function fncValidarEmpresaSEFIP(EmpresaID) As String
On Error GoTo TratarErro
Dim varRstEmpresa As DAO.Recordset
Dim varStr As String

    Set varRstEmpresa = CurrentDb.OpenRecordset("SELECT * FROM tblEmpresa WHERE EmpresaID=" & EmpresaID)
    If varRstEmpresa.RecordCount = 1 Then
        If IsNull(varRstEmpresa!CNPJ) = True Then
            varStr = varStr & "    CNPJ/CEI" & vbCrLf
        End If
        If IsNull(varRstEmpresa!Endereco) = True Then
            varStr = varStr & "    Endereço" & vbCrLf
        End If
        If IsNull(varRstEmpresa!Numero) = True Then
            varStr = varStr & "    Número" & vbCrLf
        End If
        If IsNull(varRstEmpresa!Bairro) = True Then
            varStr = varStr & "    Bairro" & vbCrLf
        End If
        If IsNull(varRstEmpresa!CEP) = True Then
            varStr = varStr & "    CEP" & vbCrLf
        End If
        If IsNull(varRstEmpresa!Cidade) = True Then
            varStr = varStr & "    Cidade" & vbCrLf
        End If
        If IsNull(varRstEmpresa!UF) = True Then
            varStr = varStr & "    Unidade Federativa(UF)" & vbCrLf
        End If
        If IsNull(varRstEmpresa!Telefone1) = True Then
            varStr = varStr & "    Telefone" & vbCrLf
        End If
        If IsNull(varRstEmpresa!CNAE) = True Then
            varStr = varStr & "    CNAE" & vbCrLf
        End If
        If IsNull(varRstEmpresa!PorcentagemRAT) = True Then
            varStr = varStr & "    Porcentagem do RAT" & vbCrLf
        End If
        If IsNull(varRstEmpresa!OptanteSimples) = True Then
            varStr = varStr & "    Simples" & vbCrLf
        End If
        If IsNull(varRstEmpresa!FPAS) = True Then
            varStr = varStr & "    FPAS" & vbCrLf
        End If
        If IsNull(varRstEmpresa!CodigoRecolhimentoGPS) = True Then
            varStr = varStr & "    Código de Recolhimento do GPS" & vbCrLf
        End If
        
    End If
    If varStr <> "" Then
        varStr = EmpresaID & "-" & varRstEmpresa!RazaoSocial & ": " & vbCrLf & varStr
    Else
        varStr = ""
    End If
    varRstEmpresa.Close
    fncValidarEmpresaSEFIP = varStr

TratarErro:
    fncTratamentoDeErro
End Function
Function fncValidarEmpresaTomadorObraSEFIP(EmpresaID As Integer, FPAS As Integer) As String
On Error GoTo TratarErro
Dim varRstEmpresa As DAO.Recordset
Dim varStr As String

    Set varRstEmpresa = CurrentDb.OpenRecordset("SELECT * FROM tblEmpresaTomadorObra WHERE TomadorObraID=" & EmpresaID)
    If varRstEmpresa.RecordCount = 1 Then
        If IsNull(varRstEmpresa!tblTipoDocumentoID) = True Then
            varStr = varStr & "    Tipo de Documento" & vbCrLf
        End If
        If IsNull(varRstEmpresa!NumeroDocumento) = True Then
            varStr = varStr & "    CNPJ/CEI" & vbCrLf
        End If
        If IsNull(varRstEmpresa!RazaoSocial) = True Then
            varStr = varStr & "    Razão Social" & vbCrLf
        End If
        If IsNull(varRstEmpresa!EnderecoObra) = True Then
            varStr = varStr & "    Endereço" & vbCrLf
        End If
        If IsNull(varRstEmpresa!NumeroObra) = True Then
            varStr = varStr & "    Número" & vbCrLf
        End If
        If IsNull(varRstEmpresa!BairroObra) = True Then
            varStr = varStr & "    Bairro" & vbCrLf
        End If
        If IsNull(varRstEmpresa!CEPObra) = True Then
            varStr = varStr & "    CEP" & vbCrLf
        End If
        If IsNull(varRstEmpresa!CidadeObra) = True Then
            varStr = varStr & "    Cidade" & vbCrLf
        End If
        If IsNull(varRstEmpresa!UFObra) = True Then
            varStr = varStr & "    Unidade Federativa(UF)" & vbCrLf
        End If
        If FPAS = 155 And IsNull(varRstEmpresa!GPSObra) = True Then
            varStr = varStr & "    GPS da Obra" & vbCrLf
        End If
    End If
    If varStr <> "" Then
        varStr = EmpresaID & "-" & varRstEmpresa!RazaoSocial & ": " & vbCrLf & varStr
    Else
        varStr = ""
    End If
    varRstEmpresa.Close
    fncValidarEmpresaTomadorObraSEFIP = varStr

TratarErro:
    fncTratamentoDeErro
End Function
Function fncValidarFuncionarioSEFIP(EmpresaID As Integer, FuncionarioID As Integer) As String
On Error GoTo TratarErro
Dim varRstFuncionario As DAO.Recordset
Dim varStr As String

    Set varRstFuncionario = CurrentDb.OpenRecordset("SELECT * FROM tblFuncionario WHERE EmpresaID=" & EmpresaID & "AND FuncionarioID=" & FuncionarioID)
    If varRstFuncionario.RecordCount = 1 Then
        If IsNull(varRstFuncionario!PIS) = True Then
            varStr = varStr & "    PIS" & vbCrLf
        End If
        If (varRstFuncionario!PIS) = 0 Then
            varStr = varStr & "    PIS ZERADO " & vbCrLf
        End If
        If IsNull(varRstFuncionario!tblSEFIPCategoriaID) = True Then
            varStr = varStr & "    Categoria do Trabalhador" & vbCrLf
        End If
        If varRstFuncionario!tblSEFIPCategoriaID <> 13 And varRstFuncionario!Proprietario = False Then
            If IsNull(varRstFuncionario!DataAdmissao) = True Or (varRstFuncionario!DataAdmissao) = 0 Then
                varStr = varStr & "    Data de Admissão Zerada" & vbCrLf
            End If
            If IsNull(varRstFuncionario!CarteiraProfissionalNumero) = True Or (varRstFuncionario!CarteiraProfissionalNumero) = 0 Then
                varStr = varStr & "    Número da Carteira Profissional Zerada" & vbCrLf
            End If
            If IsNull(varRstFuncionario!CarteiraProfissionalSerie) = True Or (varRstFuncionario!CarteiraProfissionalSerie) = 0 Then
                varStr = varStr & "    Séria da Carteira Zerada" & vbCrLf
            End If
            If IsNull(varRstFuncionario!DataOpcaoFGTS) = True Or (varRstFuncionario!DataOpcaoFGTS) = 0 Then
                varStr = varStr & "    Data de opção do FGTS" & vbCrLf
            End If
            If IsNull(varRstFuncionario!DataNascimento) = True Or (varRstFuncionario!DataNascimento) = 0 Then
                varStr = varStr & "    Data de Nascimento Zerada" & vbCrLf
            End If
        End If
        If IsNull(varRstFuncionario!Nome) = True Or (varRstFuncionario!Nome) = " " Then
            varStr = varStr & "    Nome do Funcionário em Branco" & vbCrLf
        End If
        If IsNull(varRstFuncionario!CBO) = True Or (varRstFuncionario!CBO) = 0 Then
            varStr = varStr & "    CBO" & vbCrLf
        End If
                
    End If
    If varStr <> "" Then
        varStr = FuncionarioID & "-" & varRstFuncionario!Nome & ": " & vbCrLf & varStr
    Else
        varStr = ""
    End If
    varRstFuncionario.Close
    fncValidarFuncionarioSEFIP = varStr

TratarErro:
    fncTratamentoDeErro
End Function
Function fncValidarAutonomosSEFIP(EmpresaID As Integer, AutonomoID As Integer) As String
On Error GoTo TratarErro
Dim varRstAutonomo As DAO.Recordset
Dim varStr As String

    Set varRstAutonomo = CurrentDb.OpenRecordset("SELECT * FROM tblEmpresaAutonomo WHERE EmpresaID=" & EmpresaID & "AND AutonomoID=" & AutonomoID)
    If varRstAutonomo.RecordCount = 1 Then
        If IsNull(varRstAutonomo!Inscricao) = True Then
            varStr = varStr & "    PIS" & vbCrLf
        End If
        If IsNull(varRstAutonomo!SEFIPCategoria) = True Then
            varStr = varStr & "    Categoria do Trabalhador" & vbCrLf
        End If
        If IsNull(varRstAutonomo!Nome) = True Then
            varStr = varStr & "    Nome do Funcionário" & vbCrLf
        End If
        If IsNull(varRstAutonomo!CBO) = True Then
            varStr = varStr & "    CBO" & vbCrLf
        End If
                
    End If
    If varStr <> "" Then
        varStr = AutonomoID & "-" & varRstAutonomo!Nome & ": " & vbCrLf & varStr
    Else
        varStr = ""
    End If
    varRstAutonomo.Close
    fncValidarAutonomosSEFIP = varStr

TratarErro:
    fncTratamentoDeErro
End Function
Function fncVerificaDadosRelacionamentoTabelaItemInconsistente() As String
On Error GoTo TratarErro

Open "C:\SK\Inconsistencia.txt" For Output As #1

Dim rstRelacionamento As DAO.Recordset
Dim rstTabela As DAO.Recordset
Dim rstTabelaResultado As DAO.Recordset
Dim Mensagem As String

    Set rstRelacionamento = CurrentDb.OpenRecordset("SELECT TabelaID, TabelaFilho, CampoFilho FROM tblTabelaRelacionamento")

    If rstRelacionamento.RecordCount <> 0 Then
        rstRelacionamento.MoveFirst
        Do While rstRelacionamento.EOF = False
            
            Set rstTabela = CurrentDb.OpenRecordset("SELECT " & rstRelacionamento!CampoFilho & " as ValorCampo FROM " & rstRelacionamento!TabelaFilho & " WHERE " & rstRelacionamento!TabelaFilho & "." & rstRelacionamento!CampoFilho & " IS NOT NULL")
            If rstTabela.RecordCount <> 0 Then
                Do While rstTabela.EOF = False
                    
                    Set rstTabelaResultado = CurrentDb.OpenRecordset("SELECT TabelaID FROM tblTabelaItem WHERE TabelaID = " & rstRelacionamento!TabelaID & " AND CODIGO = " & rstTabela!ValorCampo)
                    If rstTabelaResultado.RecordCount = 0 Then
                        Print #1, "TabelaID = " & rstRelacionamento!TabelaID & " , TabelaFilho " & rstRelacionamento!TabelaFilho & " , CampoFilho = " & rstRelacionamento!CampoFilho & " , Valor do Registro = " & rstTabela!ValorCampo
                        'mensagem = mensagem & "TabelaID = " & rstRelacionamento!TabelaID & " , TabelaFilho " & rstRelacionamento!TabelaFilho & " , CampoFilho = " & rstRelacionamento!CampoFilho & " , Valor do Registro = " & rstTabela!ValorCampo
                    End If
                    rstTabelaResultado.Close
                    
                rstTabela.MoveNext
                Loop
            End If
            
            rstTabela.Close
        
        rstRelacionamento.MoveNext
        Loop
        Debug.Print Mensagem
    End If
    
rstRelacionamento.Close
Set rstRelacionamento = Nothing
rstTabela.Close
Set rstTabela = Nothing
rstTabelaResultado.Close
Set rstTabelaResultado = Nothing


Close #1
Exit Function

TratarErro:
   fncTratamentoDeErro
End Function
Function fncValorIntegraContabil(Codigo As Integer, Empresa, Competencia) As Double
On Error Resume Next
Dim varValor As Double

    fncValorIntegraContabil = 0
    
    If Codigo = 15001 Then
        If Month(Competencia) = 12 Then
            varValor = DFirst("ValorGPSAtual", "tblEmpresaGPS", "EmpresaID = " & Empresa & " and month(Competencia) = " & Month(Competencia) & " and year(Competencia)= " & Year(Competencia) & " and gps13 = false")
            fncValorIntegraContabil = Format(varValor + DFirst("ValorGPSAtual", "tblEmpresaGPS", "EmpresaID = " & Empresa & " and month(Competencia) = " & Month(Competencia) & " and year(Competencia)= " & Year(Competencia) & " and gps13 = true"), "##,##0.00")
        Else
            fncValorIntegraContabil = DFirst("ValorGPSAtual", "tblEmpresaGPS", "EmpresaID = " & Empresa & " and month(Competencia) = " & Month(Competencia) & " and year(Competencia)= " & Year(Competencia))
        End If
    ElseIf Codigo = 15002 Then
        If Month(Competencia) = 12 Then
            fncValorIntegraContabil = Format(DFirst("ValorSefip", "tblEmpresaGPS", "EmpresaID = " & Empresa & " and month(Competencia) = " & Month(Competencia) & " and year(Competencia)= " & Year(Competencia) & " and gps13 = False"), "##,##0.00")
        Else
            fncValorIntegraContabil = DFirst("ValorSefip", "tblEmpresaGPS", "EmpresaID = " & Empresa & " and month(Competencia) = " & Month(Competencia) & " and year(Competencia)= " & Year(Competencia))
        End If
    ElseIf Codigo = 15003 Then
        If Month(Competencia) = 12 Then
            fncValorIntegraContabil = Format(DFirst("ValorPIS", "tblEmpresaGPS", "EmpresaID = " & Empresa & " and month(Competencia) = " & Month(Competencia) & " and year(Competencia)= " & Year(Competencia) & " and gps13 = False"), "##,##0.00")
        Else
            fncValorIntegraContabil = DFirst("ValorPIs", "tblEmpresaGPS", "EmpresaID = " & Empresa & " and month(Competencia) = " & Month(Competencia) & " and year(Competencia)= " & Year(Competencia))
        End If
    End If
    

End Function
Function fncValorIntegraParoquia(Codigo As Integer, Empresa, Competencia) As Double
On Error Resume Next
Dim varValor As Double

    fncValorIntegraParoquia = 0
    
    If Codigo = 15001 Then
        If Month(Competencia) = 12 Then
            varValor = DFirst("ValorGPSAtual", "tblEmpresaGPS", "EmpresaID = " & Empresa & " and month(Competencia) = " & Month(Competencia) & " and year(Competencia)= " & Year(Competencia) & " and gps13 = false")
            fncValorIntegraParoquia = Format(varValor + DFirst("ValorGPSAtual", "tblEmpresaGPS", "EmpresaID = " & Empresa & " and month(Competencia) = " & Month(Competencia) & " and year(Competencia)= " & Year(Competencia) & " and gps13 = true"), "##,##0.00")
        Else
            fncValorIntegraParoquia = DFirst("ValorGPSAtual", "tblEmpresaGPS", "EmpresaID = " & Empresa & " and month(Competencia) = " & Month(Competencia) & " and year(Competencia)= " & Year(Competencia))
        End If
    ElseIf Codigo = 15002 Then
        If Month(Competencia) = 12 Then
            fncValorIntegraParoquia = Format(DFirst("ValorSefip", "tblEmpresaGPS", "EmpresaID = " & Empresa & " and month(Competencia) = " & Month(Competencia) & " and year(Competencia)= " & Year(Competencia) & " and gps13 = False"), "##,##0.00")
        Else
            fncValorIntegraParoquia = DFirst("ValorSefip", "tblEmpresaGPS", "EmpresaID = " & Empresa & " and month(Competencia) = " & Month(Competencia) & " and year(Competencia)= " & Year(Competencia))
        End If
    ElseIf Codigo = 15003 Then
        fncValorIntegraParoquia = DFirst("ValorPIs", "tblEmpresaGPS", "EmpresaID = " & Empresa & " and month(Competencia) = " & Month(Competencia) & " and year(Competencia)= " & Year(Competencia))
    End If
    

End Function

Function fncQuantidadeDeSplit(varTexto As String, varCaracter As String) As Integer
On Error GoTo TratarErro

    Dim varTamanho As Variant
     
'    If Right(varTexto, 1) = "," Or Right(varTexto, 1) = ":" Then
'        varTexto = Mid(varTexto, 1, Len(varTexto) - 1) & ";"
'    ElseIf Right(varTexto, 1) = ";" Then
'        'deixa como está...
'    Else
'        varTexto = varTexto & ";"
'    End If
'
'    varTexto = Replace(varTexto, ":", ";")
'    varTexto = Replace(varTexto, ",", ";")
'    varTexto = Replace(varTexto, " ", ";")
    
    varTamanho = Split(varTexto, varCaracter)
    
    fncQuantidadeDeSplit = UBound(varTamanho)
     
Exit Function:
TratarErro:
    fncQuantidadeDeSplit = 0
End Function

