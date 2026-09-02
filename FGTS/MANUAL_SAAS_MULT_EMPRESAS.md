# Manual Rápido — Multi-empresas e Isolamento (SaaS)

## 1. Perfis de acesso
- **Usuário padrão**: vinculado a 1 empresa. Vê e cria dados apenas dessa empresa.
- **Gestor multiempresas**: pode operar várias empresas listadas em "Empresas permitidas" (sem trocar de login). Flag `Gestor multiempresas` ligada.
- **Superuser (Django Admin)**: acesso total a todas as empresas.

## 2. Campos novos em Usuário
- `empresa` (FK): empresa principal do usuário (obrigatório para usuários padrão).
- `empresas_permitidas` (M2M): lista de empresas extras para gestores multiempresas.
- `is_multi_empresa` (bool): habilita modo multiempresas.

## 3. Como configurar no Admin
1. Acesse `/admin/usuarios/usuario/`.
2. Edite o usuário:
   - Defina `empresa` (principal).
   - Marque `Gestor multiempresas` se ele deve administrar várias empresas.
   - Em "Empresas permitidas", selecione as empresas extras (além da principal).
3. Salve.

## 4. Regras de isolamento aplicadas
- Listagens e relatórios filtram automaticamente pelas empresas permitidas.
- Exports CSV/PDF respeitam o mesmo filtro.
- Checkout de billing só é permitido para empresas às quais o usuário tem acesso.
- Criação/edição de funcionários força a empresa a ser uma das permitidas.
- Criação de empresas: apenas superuser ou gestor multiempresas.

## 5. Como o gestor multiempresas usa no dia a dia
- Ao abrir listas (empresas, funcionários, lançamentos/relatórios), ele verá itens de todas as empresas permitidas.
- Em formulários, os campos de empresa/funcionário já vêm filtrados para o conjunto permitido.
- Para relatórios, selecione a empresa desejada (somente entre as permitidas) e gere normalmente.

## 6. Checklist pós-configuração
- [ ] Criar/ajustar usuários no admin com empresa principal.
- [ ] Marcar `Gestor multiempresas` para quem precisa administrar múltiplos CNPJs.
- [ ] Preencher "Empresas permitidas" para esses gestores.
- [ ] Testar login com um usuário padrão (dever ver só 1 empresa).
- [ ] Testar login com um gestor (dever ver múltiplas empresas nas listas e formulários).

## 7. Boas práticas
- Mantenha `empresa` sempre preenchida para usuários não-super.
- Conceda `Gestor multiempresas` apenas para quem realmente precisa.
- Use grupos/permissões do Django para complementar (ex.: apenas leitura).
- Para produção, mantenha logs de auditoria (quem acessou qual empresa).

## 8. Suporte
Em caso de dúvidas, acesse o admin e revise o usuário ou entre em contato com o suporte técnico.
