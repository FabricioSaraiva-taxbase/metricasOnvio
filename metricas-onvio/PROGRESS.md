# Frontend Fixes — Progress Tracker

> Para outro modelo continuar: este arquivo rastreia as 6 correções do frontend Next.js.
> Arquivos principais ficam em `frontend/src/`. Backend em `backend/`.

## Checklist

- [x] **1. Separar Data/Hora** — Na tabela de análise detalhada, extrair a hora do campo `Data` para a coluna `Hora`
  - Arquivo: `frontend/src/app/page.tsx` (tabela integrada ao dashboard)
  - Lógica: se `item.Data` contém `T` ou espaço, split e usar parte da hora. Se `item.Hora` já existe, usar direto.

- [x] **2. Status "Interno/Ignorar"** — Renomear badge de "Interno" para "Interno/Ignorar" quando `Cliente_Final` é TAXBASE INTERNO ou IGNORAR
  - Arquivo: `frontend/src/app/page.tsx` (tabela integrada ao dashboard)

- [x] **3. Seletor de Período** — Adicionar opções: Mês Individual, Últimos 90 Dias, Últimos 180 Dias, Período Completo, Personalizado
  - Arquivos: `frontend/src/contexts/FilterContext.tsx`, `frontend/src/components/dashboard/FilterBar.tsx`, `frontend/src/app/page.tsx`
  - Abordagem: buscar múltiplos meses via API existente (`/api/data/get_month/{id}`) e mergear no frontend

- [x] **4. Fundo dos Gráficos no Modo Claro** — Corrigir cores hardcoded dos gráficos Recharts
  - Arquivos: `frontend/src/components/dashboard/EvolutionChart.tsx`, `TopClientsChart.tsx`, `frontend/src/app/globals.css`
  - Adicionar CSS vars `--chart-grid`, `--chart-axis` para ambos os temas

- [x] **5. Mover Análise para Dashboard** — Tabela detalhada no final do Dashboard, remover rota `/analise`
  - Mover conteúdo de `frontend/src/app/analise/page.tsx` para `frontend/src/app/page.tsx`
  - Remover link "Análise" do `frontend/src/components/Navbar.tsx`
  - Deletar `frontend/src/app/analise/page.tsx`

- [x] **6. Renomear Gráficos** — "Evolução Diária" → "Atendimentos por Dia", "Top 10 Clientes" → "Demanda por Cliente"
  - Arquivos: `EvolutionChart.tsx`, `TopClientsChart.tsx`

## Revisões (Feedback do Usuário)

- [x] **7. Corrigir Gráfico de Evolução (Multi-Mês)** — Desabilitar calendário completo em modos multi-mês para evitar mistura de datas e eixos incorretos.
- [x] **8. Labels em Top Clientes** — Exibir valores diretamente nas barras para visualização em TV.
- [x] **9. Fundo Modo Claro** — Forçar background correto nos Cards dos gráficos.
- [x] **10. Aposentar Modo Claro** — Forçar Modo Escuro como padrão e remover botão de toggle.
