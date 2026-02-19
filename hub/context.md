# Contexto do Projeto: Hub Taxbase & Auditor Fiscal

Este documento serve como guia e contexto para a apresentação do projeto **Hub Taxbase** e seu módulo principal, o **Auditor Fiscal**, para a diretoria do escritório.

## 1. Visão Geral do Hub Taxbase

O **Hub Taxbase** é uma plataforma centralizada e moderna desenvolvida para unificar as ferramentas internas do escritório, oferecendo segurança, controle e agilidade no acesso às informações.

*   **Problema Resolvido**: Anteriormente, ferramentas e scripts ficavam dispersos, sem controle de acesso centralizado e com interfaces pouco amigáveis.
*   **Solução**: Uma aplicação web robusta (Python/Flask) que serve como portal único de entrada para os colaboradores.
*   **Diferenciais**:
    *   **Segurança**: Login unificado e controle de permissões por função (Sócio, Gerente, Analista).
    *   **Design Moderno**: Interface intuitiva, limpa e responsiva, facilitando o uso diário.
    *   **Escalabilidade**: Arquitetura pronta para receber novos módulos e ferramentas conforme a necessidade do escritório.

## 2. O Módulo: Auditor Fiscal

O **Auditor Fiscal** é a ferramenta carro-chefe do Hub, projetada para garantir o compliance fiscal e reduzir drasticamente o risco de multas por não entrega de obrigações acessórias.

### Objetivo Principal
Automatizar a conferência entre o que *deveria* ser entregue (Obrigações) e o que *efetivamente* foi entregue (Arquivos processados), substituindo controles manuais passíveis de erro.

### Como Funciona
1.  **Monitoramento**: O sistema cruza diariamente a base de clientes e suas obrigações esperadas (DCTF, EFD Contribuições, SPED Fiscal, etc.) contra os arquivos de recibo processados pelos robôs.
2.  **Dashboard Inteligente**: Apresenta em tempo real:
    *   Percentual de conclusão da competência atual.
    *   Total de empresas Pendentes vs. OK.
    *   Gráficos de evolução diária e status por tipo de obrigação.
3.  **Ação Imediata**: Permite que o analista ou gerente identifique com um clique quais empresas ainda não entregaram determinada obrigação.

### Funcionalidades Chave
*   **Filtros Dinâmicos**: Visualização por Analista, Grupo Econômico ou Tipo de Obrigação.
*   **Status Detalhado**:
    *   ✅ **Entregue**: Arquivo processado e validado.
    *   ⚠️ **Pendente**: Prazo se aproximando e arquivo não localizado.
    *   🚫 **Ignorado/Suspenso**: Empresas sem movimento ou baixadas (controle manual disponível).
*   **Gestão de Exceções**: Ferramentas para alocar arquivos não identificados manualmente ou descartar arquivos incorretos, mantendo a base limpa.

## 3. Tecnologia e Performance

*   **Backend**: Python (Flask) para lógica de negócios rápida e segura.
*   **Dados**: Google BigQuery para processamento de grandes volumes de dados (milhares de empresas/obrigações) em segundos.
*   **Frontend**: HTML5/CSS3/JavaScript modernos, sem dependência de plataformas lentas ou limitadas.

## 4. Benefícios para o Escritório

1.  **Mitigação de Riscos**: Redução significativa da exposição a multas por atraso ou esquecimento.
2.  **Eficiência Operacional**: A equipe gasta menos tempo conferindo planilhas e mais tempo analisando pendências reais.
3.  **Visibilidade Gerencial**: A diretoria tem uma visão macro e confiável do andamento das entregas fiscais em tempo real.
