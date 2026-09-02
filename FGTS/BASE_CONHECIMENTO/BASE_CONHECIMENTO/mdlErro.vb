Option Compare Database
Option Explicit
Function fncTratamentoDeErro(Optional strNomeDoObjeto As String)
    'Analisa os números de erro que o sistema retornará em cada evento
    Select Case Err.Number
        Case 0
            'Ainda nao entendi, parece que não é um erro
            Exit Function
        Case 1000
            'WebCam desconectada
            MsgBox "A WebCam não está conectada ou não foi localizada !", vbInformation
        Case 3200
            'Não pode ser excluido o registro porque outra tabela relacionada está utilizando
            MsgBox "O registro não pode ser excluido por estar sendo utilizado em outra parte do sistema.", vbInformation
        Case 2105
            MsgBox "Você não pode ir para o Registro Especificado!", vbInformation
        Case 2501
            'Cancelamento da ação abrir relatório
            Exit Function
        Case 2164
            'Não se pode desabilitar um controle enquanto ele mantém o foco
            Exit Function
        Case 2448
            'Não se pode atribuir valor a este objeto
            Exit Function
        Case 2759
            Exit Function
        Case 3265
            'Não existe o campo na coleção especificada, não existe o campo no recordset especificado
            MsgBox "Não existe o campo no local especificado !", vbInformation
        Case 3314
            'Algum Campo Requerido não foi preenchido
            MsgBox "Há campos requeridos não preechidos!", vbInformation
        Case 3704
            'Banco de dados não esta aberto portanto não pode executar isto
            MsgBox "Operação não permitida enquanto o banco de dados não for aberto!", vbInformation
        Case 3705
            'Banco de dados já esta aberto portanto não pode ser aberto novamente
            MsgBox "Ocorreu um erro na comunicação com os dados !", vbInformation
        Case 432
            'Arquivo de skin não encontrado ao carregá-lo no formulário

            'É melhor deixar sem mensagem para que não fique aparecendo cada vez que o usuário abre uma tela
            Exit Function
        Case 76
            'Pasta não encontrada (para o skin, não sei se serve para tudo)
        Case 3021
            'O banco de dados não pode ir para o local especificado (BOF e EOF)
            MsgBox "O banco de dados não pôde ir para o local especificado! ", vbInformation
        Case 13
            'Tipo inválido de dados
            MsgBox "Tipo incorreto de entrada de dados.", vbInformation
        Case 364
            'O objeto foi descarregado e não pode ser aberto (Não tem acesso)
            MsgBox "O usuário atual não tem permissão para prosseguir! ", vbCritical
        Case -2147467259
            'Duplicação de chave primária
            MsgBox "Não é possível inserir este registro pois já existe um registro com mesmo índice!", vbExclamation
        Case -2147217900
            'Erro da sintaxe do SQL, provavelmente falta ou excesso de parametros
            MsgBox "Não é possível executar esta ação, pois ela possui erro de parâmetros!", vbExclamation
        Case 53
            'Arquivo não encontrado
        Case 70
            'Permissão negada. Pode acontecer na hora de excluir um arquivo e ele estiver sendo usado.
        Case 3024
            'Arquivo não localizado
        Case 57097
            ' O valor do text falhou
        Case 3292
            'Comando SQL com erro de sintaxe
            MsgBox "Comando SQL com erro de syntaxe", vbCritical
        Case 3290
            'Comando CREATE TABLE  com erro de sintaxe
            MsgBox "Comando CREATE TABLE com erro de sintaze", vbCritical
        Case Else
            'Erro desconhecido
            MsgBox Err.Number & " - " & Err.Description
            Dim DescricaoDoErro As String, i As Integer
            DescricaoDoErro = ""
            For i = 1 To Len(Err.Description) And Len(Err.Description) < 255
                If Mid(Err.Description, i, 1) <> "'" Then
                        DescricaoDoErro = DescricaoDoErro & Mid(Err.Description, i, 1)
                End If
            Next
            If strNomeDoObjeto = "" Then
                DoCmd.SetWarnings False
                'DoCmd.RunSQL "INSERT INTO tblLog(NumeroDoErro, DescricaoDoErro) values ( '" & Err.Number & "','" & DescricaoDoErro & "')"
                DoCmd.SetWarnings True
            Else
                DoCmd.SetWarnings False
                'DoCmd.RunSQL "INSERT INTO tblLog(NumeroDoErro, DescricaoDoErro, NomeDoObjeto) values ( '" & Err.Number & "','" & DescricaoDoErro & "'," & strNomeDoObjeto & ");"
                DoCmd.SetWarnings True
            End If
    End Select
End Function
