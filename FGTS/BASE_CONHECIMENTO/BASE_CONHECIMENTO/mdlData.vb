Option Compare Database
Option Explicit
Global varResp As Integer
Function fncProximoMes(Mes As Integer, Ano As Integer) As Double
On Error GoTo TratarErro
    If Mes <> 12 Then
        Mes = Mes + 1
    Else
        Mes = 1
        Ano = Ano + 1
    End If
        fncProximoMes = CDate(1 & "/" & Mes & "/" & Ano)
TratarErro:
    fncTratamentoDeErro
End Function
Function fncUltimoDiaMes(varData As Date) As String
Dim varAno As Integer, varUltimoDiaMes As String
varAno = Year(varData)

Select Case Month(varData)
Case 1
    varUltimoDiaMes = "31/01" & "/" & varAno
Case 2
    If varAno Mod 4 = 0 Then
        varUltimoDiaMes = "29/02" & "/" & varAno
    Else
        varUltimoDiaMes = "28/02" & "/" & varAno
    End If

Case 3
    varUltimoDiaMes = "31/03" & "/" & varAno
Case 4
    varUltimoDiaMes = "30/04" & "/" & varAno
Case 5
    varUltimoDiaMes = "31/05" & "/" & varAno
Case 6
    varUltimoDiaMes = "30/06" & "/" & varAno
Case 7
    varUltimoDiaMes = "31/07" & "/" & varAno
Case 8
    varUltimoDiaMes = "31/08" & "/" & varAno
Case 9
    varUltimoDiaMes = "30/09" & "/" & varAno
Case 10
    varUltimoDiaMes = "31/10" & "/" & varAno
Case 11
    varUltimoDiaMes = "30/11" & "/" & varAno
Case 12
    varUltimoDiaMes = "31/12" & "/" & varAno
End Select
    fncUltimoDiaMes = Format(varUltimoDiaMes, "dd/MM/yyyy")
End Function
Function fncProximoMesPrimeiroDia(Mes As Integer, Ano As Integer) As Double
On Error GoTo TratarErro
Dim varproximomesprimeirodia As String
    If Mes <> 12 Then
        Mes = Mes + 1
    Else
        Mes = 1
        Ano = Ano + 1
    End If
        If Mes = 1 Or Mes = 2 Or Mes = 3 Or Mes = 4 Or Mes = 5 Or Mes = 6 Or Mes = 7 Or Mes = 8 Or Mes = 9 Then
            varproximomesprimeirodia = 1 & "/" & 0 & Mes & "/" & Ano
        Else
            varproximomesprimeirodia = 1 & "/" & Mes & "/" & Ano
        End If
        
        fncProximoMesPrimeiroDia = CDate(varproximomesprimeirodia)
        
TratarErro:
    fncTratamentoDeErro
End Function
Function fncProximoMesUltimoDia(Mes As Double, Ano As Double) As Double
On Error GoTo TratarErro
Dim varproximomesultimodia As Variant
If Mes <> 12 Then
    Mes = Mes + 1
Else
    Mes = 1
End If
Select Case Mes
Case 1
    varproximomesultimodia = "31/01" & "/" & Ano
Case 2
    If Ano = 2004 Or 2008 Or 2012 Or 2016 Then
        varproximomesultimodia = "29/02" & "/" & Ano
    Else
        varproximomesultimodia = "28/02" & "/" & Ano
    End If
Case 3
    varproximomesultimodia = "31/03" & "/" & Ano
Case 4
    varproximomesultimodia = "30/04" & "/" & Ano
Case 5
    varproximomesultimodia = "31/05" & "/" & Ano
Case 6
    varproximomesultimodia = "30/06" & "/" & Ano
Case 7
    varproximomesultimodia = "31/07" & "/" & Ano
Case 8
    varproximomesultimodia = "31/08" & "/" & Ano
Case 9
    varproximomesultimodia = "30/09" & "/" & Ano
Case 10
    varproximomesultimodia = "31/10" & "/" & Ano
Case 11
    varproximomesultimodia = "30/11" & "/" & Ano
Case 12
    varproximomesultimodia = "31/12" & "/" & Ano
End Select
    fncProximoMesUltimoDia = CDate(varproximomesultimodia)
    'MsgBox CDate(varproximomesultimodia)
TratarErro:
    fncTratamentoDeErro
End Function
Function fncPrimeiroDiaMes(varData As Date) As String
Dim varAno As Integer
    varAno = Year(varData)
    fncPrimeiroDiaMes = CDate(1 & "/" & Month(varData) & "/" & varAno)
End Function
Function fncPrimeiroDiaAno(varAno As Integer) As String
    fncPrimeiroDiaAno = CDate(1 & "/" & 1 & "/" & varAno)
End Function
Function fncUltimoDiaAno(varAno As Integer) As String
    fncUltimoDiaAno = CDate(31 & "/" & 12 & "/" & varAno)
End Function
Function fnc15DiaMes(varData As Date) As String
Dim varAno As Integer
    varAno = Year(varData)
    fnc15DiaMes = CDate(15 & "/" & Month(varData) & "/" & varAno)
End Function

