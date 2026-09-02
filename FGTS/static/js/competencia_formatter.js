/**
 * Auto-formatador para campos de competência (MM/YYYY)
 * Formata automaticamente a entrada do usuário enquanto digita
 */

document.addEventListener('DOMContentLoaded', function() {
  // Seleciona todos os campos com a classe competencia-input
  const competenciaFields = document.querySelectorAll('.competencia-input');

  competenciaFields.forEach(field => {
    field.addEventListener('input', function(e) {
      formatarCompetencia(this);
    });

    // Formatar ao perder o foco também
    field.addEventListener('blur', function(e) {
      formatarCompetencia(this);
    });
  });

  // Seleciona campos de múltiplas competências (textarea)
  const competenciasTextareas = document.querySelectorAll('.competencias-input');

  competenciasTextareas.forEach(textarea => {
    textarea.addEventListener('input', function(e) {
      formatarMultiplasCompetencias(this);
    });
  });
});

/**
 * Formata um campo de competência única (MM/YYYY)
 * Aceita: 012025 → 01/2025 ou jáformatado 01/2025
 */
function formatarCompetencia(input) {
  let valor = input.value.replace(/\D/g, ''); // Remove tudo que não é dígito

  // Se tem 4 dígitos, formata como MM/YYYY
  if (valor.length === 4) {
    valor = valor.substring(0, 2) + '/' + valor.substring(2, 4);
    // Adicionar século (20XX se um ano de 00-99)
    const ano = parseInt(valor.substring(3, 5));
    const anoCompleto = ano < 50 ? 2000 + ano : 1900 + ano;
    const mes = valor.substring(0, 2);
    valor = mes + '/' + anoCompleto;
  }
  // Se tem 6 dígitos, formata como MM/YYYY
  else if (valor.length === 6) {
    const mes = valor.substring(0, 2);
    const ano = valor.substring(2, 6);
    // Validar mês (01-12 ou 13 para 13º salário)
    const mesNum = parseInt(mes);
    if (mesNum >= 1 && mesNum <= 13) {
      valor = mes + '/' + ano;
    }
  }
  // Se tem 2 dígitos, é apenas o mês (aguardando mais dígitos)
  else if (valor.length === 2) {
    const mes = valor.substring(0, 2);
    const mesNum = parseInt(mes);
    // Validar se é um mês válido
    if (mesNum >= 1 && mesNum <= 13) {
      valor = mes; // Deixar como está, aguardando ano
    } else {
      // Limpar se não for mês válido
      valor = '';
    }
  }
  // Se tem 7 caracteres e já tem barra, deixar como está
  else if (valor.length > 6 && input.value.includes('/')) {
    // Já formatado, deixar como está
    return;
  }

  input.value = valor;
}

/**
 * Formata múltiplas competências (uma por linha)
 * Cada linha é formatada independentemente
 */
function formatarMultiplasCompetencias(textarea) {
  const linhas = textarea.value.split('\n');
  const linhasFormatadas = linhas.map(linha => {
    const trimmed = linha.trim();
    if (!trimmed) return '';

    let valor = trimmed.replace(/\D/g, ''); // Remove tudo que não é dígito

    // Se tem 4 dígitos, formata como MM/YYYY
    if (valor.length === 4) {
      const mes = valor.substring(0, 2);
      const ano = valor.substring(2, 4);
      const anoCompleto = parseInt(ano) < 50 ? 2000 + parseInt(ano) : 1900 + parseInt(ano);
      return mes + '/' + anoCompleto;
    }
    // Se tem 6 dígitos, formata como MM/YYYY
    else if (valor.length === 6) {
      const mes = valor.substring(0, 2);
      const ano = valor.substring(2, 6);
      const mesNum = parseInt(mes);
      if (mesNum >= 1 && mesNum <= 13) {
        return mes + '/' + ano;
      }
    }
    // Se já temos o formato MM/YYYY ou 13/YYYY, manter como está
    else if (trimmed.includes('/') && trimmed.split('/').length === 2) {
      const [mes, ano] = trimmed.split('/');
      const mesNum = parseInt(mes);
      if ((mesNum >= 1 && mesNum <= 13) && ano.length === 4 && /^\d+$/.test(ano)) {
        return trimmed;
      }
    }

    return trimmed; // Se não conseguiu formatar, retorna como está
  });

  textarea.value = linhasFormatadas.filter(l => l !== '').join('\n');
}
