Option Compare Database
Option Explicit
'Declaração usada para ler e escrever no arquivo INI
'Declare Function WritePrivateProfileString Lib "kernel32" Alias "WritePrivateProfileStringA" (ByVal lpApplicationName As String, ByVal lpKeyName As Any, ByVal lpString As Any, ByVal lpFileName As String) As Long
'Declare Function GetPrivateProfileString Lib "kernel32" Alias "GetPrivateProfileStringA" (ByVal lpApplicationName As String, ByVal lpKeyName As Any, ByVal lpDefault As String, ByVal lpReturnedString As String, ByVal nSize As Long, ByVal lpFileName As String) As Long

'Variáveis usadas somente no módulo
Dim CaminhoINI As String, RetornoINI As String
Dim RetornoINITamanho As Integer
Dim NumeroRegistro As String

Public Const varNomeAplicacao As String = "Folha.mdb"
Public Const varNomeProjeto As String = "Folha de Pagamento"
Function fncInicializarAplicativo() As Boolean
On Error GoTo TratarErro
    If fncExcluirTabelas = True Then
        If fncVincularTabelas = True Then
            Forms!frmInicializarAplicativo!BarradeProgresso.Value = 0
            DoCmd.SetWarnings False
            DoCmd.RunSQL "Update tblAplicativoInicializado Set AplicativoInicializado = True"
            DoCmd.SetWarnings True
        End If
    End If
TratarErro:
    fncTratamentoDeErro
End Function
Function fncExcluirTabelas() As Boolean
Dim i  As Integer, J As Integer
Dim varNomeTabela(100) As String
Dim varNumeroTabela As Integer
fncExcluirTabelas = False
J = 1

inicio:

On Error GoTo TratarErro
    CurrentDb.TableDefs.Refresh
    varNumeroTabela = CurrentDb.TableDefs.Count
    Forms!frmInicializarAplicativo!BarradeProgresso.Max = varNumeroTabela
    For i = 1 To CurrentDb.TableDefs.Count - 1
        'Busca no dicionário do Access se é do tipo tabela
        If Mid(CStr(CurrentDb.TableDefs(i).Name), 1, 4) <> "MSys" And CStr(CurrentDb.TableDefs(i).Name) <> "tblTempBuscaCep" And CStr(CurrentDb.TableDefs(i).Name) <> "tblAplicativoInicializado" And CStr(CurrentDb.TableDefs(i).Name) <> "tblCaminhoBase" And CStr(CurrentDb.TableDefs(i).Name) <> "tblTempCaged" And CStr(CurrentDb.TableDefs(i).Name) <> "tblConsistenciaFalha" Then
            varNomeTabela(J) = CurrentDb.TableDefs(i).Name
            J = J + 1
        End If
        Forms!frmInicializarAplicativo!BarradeProgresso.Value = i
    Next i
    
    For i = 1 To J
        'Exclui todas as tabelas Vinculadas
        If varNomeTabela(i) <> "" Then
            CurrentDb.TableDefs.Delete varNomeTabela(i)
        End If
    Next i
      
      
fncExcluirTabelas = True
      
TratarErro:
    If Err.Number = 3265 Then
        GoTo inicio
    Else
        fncTratamentoDeErro
    End If
End Function
Function fncVincularTabelas() As Boolean
On Error GoTo TratarErro
Dim i As Integer
Dim varBancoDestino As Database

Dim varCaminhoBanco As String
Dim varNomeBanco As String

varCaminhoBanco = fncRetornarCampoTabela("tblCaminhoBase", "CaminhoBase")
varNomeBanco = fncRetornarCampoTabela("tblCaminhoBase", "NomeBase")

Set varBancoDestino = DBEngine.Workspaces(0).OpenDatabase(varCaminhoBanco & "\" & varNomeBanco) ', False, False, ";pwd=senha")
    
fncVincularTabelas = False
    
inicio:
    Forms!frmInicializarAplicativo!BarradeProgresso.Max = varBancoDestino.TableDefs.Count - 1
    For i = 0 To (varBancoDestino.TableDefs.Count - 1)
        'Busca no dicionário do Access se é do tipo tabela
        'If CStr(varBancoDestino.TableDefs(I).Name) <> "MSysACEs" And CStr(varBancoDestino.TableDefs(I).Name) <> "MSysIMEXSpecs" And CStr(varBancoDestino.TableDefs(I).Name) <> "MSysIMEXColumns" And CStr(varBancoDestino.TableDefs(I).Name) <> "MSysCmdbars" And CStr(varBancoDestino.TableDefs(I).Name) <> "MSysModules" And CStr(varBancoDestino.TableDefs(I).Name) <> "MSysModules2" And CStr(varBancoDestino.TableDefs(I).Name) <> "MSysObjects" And CStr(varBancoDestino.TableDefs(I).Name) <> "MSysQueries" And CStr(varBancoDestino.TableDefs(I).Name) <> "MSysRelationships" And CStr(varBancoDestino.TableDefs(I).Name) <> "tblTempBuscaCep" And CStr(varBancoDestino.TableDefs(I).Name) <> "MSysAccessObjects" And CStr(varBancoDestino.TableDefs(I).Name) <> "tblAplicativoInicializado" Then
        If Mid(CStr(varBancoDestino.TableDefs(i).Name), 1, 4) <> "MSys" Then
            'Exclui todas as tabelas Vinculadas
            DoCmd.TransferDatabase acLink, "Microsoft Access", varCaminhoBanco & "\" & varNomeBanco, acTable, varBancoDestino.TableDefs(i).Name, varBancoDestino.TableDefs(i).Name
            'DoCmd.TransferDatabase acLink, "Microsoft Access", varOrigemDoArquivo & varNomeArquivo, acTable, varNomeTabela(i, 3), varNomeTabela(i, 1)
        End If
        Forms!frmInicializarAplicativo!BarradeProgresso.Value = i
    Next
      
fncVincularTabelas = True
      
TratarErro:
    If Err.Number = 3265 Then
        GoTo inicio
    Else
        fncTratamentoDeErro
    End If
    
End Function
Function fncLerINI(SecaoINI As String, CampoINI As String)
On Error GoTo TrataErro

    'Define o caminho do arquivo INI de acordo com o diretório raiz do sistema
    CaminhoINI = Mid(CurrentDb.Properties(0).Value, 1, (Len(CurrentDb.Properties(0).Value) - Len(varNomeAplicacao))) & "Config.ini"

    'Atribuição de valores nas váriaveis de retorno do arquivo INI
    RetornoINI = Space$(255)
'    RetornoINITamanho = GetPrivateProfileString(SecaoINI, CampoINI, "", RetornoINI, Len(RetornoINI), CaminhoINI)
    RetornoINI = Left(RetornoINI, RetornoINITamanho)

    'Função retorna o valor do arquivo INI
    fncLerINI = RetornoINI

TrataErro:
    fncTratamentoDeErro
End Function
