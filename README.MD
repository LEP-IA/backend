# Backend - Gerenciador de Projetos Ágeis com IA

## Visão Geral

Este backend é parte de uma aplicação para gerenciamento de projetos baseada em metodologias ágeis (Scrum, Kanban, etc.), com funcionalidades de inteligência artificial para auxiliar na tomada de decisões, automação de tarefas e análise de desempenho. Ele fornece uma API RESTful para integração com o frontend e outros serviços.

## Principais Funcionalidades

- **Gestão de Projetos:** Criação, edição e exclusão de projetos.
- **Gestão de Sprints:** Planejamento, acompanhamento e encerramento de sprints.
- **Gestão de Tarefas:** CRUD de tarefas, atribuição de responsáveis, definição de prioridades e status.
- **Gestão de Times:** Cadastro de membros, papéis e permissões.
- **Automação com IA:** Sugestão de tarefas, previsão de prazos, análise de produtividade e detecção de gargalos.
- **Relatórios:** Estudamos a possibilidade
- **Autenticação e Autorização:** Controle de acesso baseado em papéis 
- **Notificações:** Alertas automáticos sobre prazos, mudanças e recomendações da IA.

## Tecnologias Utilizadas

- **Linguagem:** Python
- **Framework:** Django / Flask / FastAPI (escolha conforme seu projeto)
- **Banco de Dados:** PostgreSQL 
- **IA:** Integração com modelos de machine learning
- **Autenticação:** JWT 
- **Documentação:** Swagger 

# 📋 Especificação da API

Este documento define os contratos de integração entre o Frontend e o Backend.

## Autenticação (login)
    
POST `/login`

Rota para autenticar o usuário e receber o token de acesso.

**Body (JSON):**

```json
{
  "email": "davi@gmail.com",
  "password": "senha_exemplo_123"
}
```

**Resposta de Sucesso (200 OK):**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "name": "Antonio Davi",
    "email": "davi@gmail.com",
    "avatarUrl": "https://api.dicebear.com/7.x/avataaars/svg?seed=Antonio"
  }
}
```

**Possíveis Erros:**

- `401 Unauthorized`: E-mail ou senha incorretos.
- `400 Bad Request`: Formato de e-mail inválido ou campos vazios.

    
## Cadastro de Usuário (signup)
    
POST `/signup`

Este endpoint é responsável por criar um novo usuário no sistema.

**Request Body (JSON):**

```json
{
  "name": "Antonio Davi",
  "email": "davi@gmail.com",
  "password": "senha_exemplo_123",
  "termsAccepted": true
}
```

**Resposta de Sucesso (201):**

```json
{ "message": "Usuário criado com sucesso" }
```

- **Validação de E-mail:** O campo `email` deve ser único. Se já existir, retornar `409 Conflict`.
- **Termos:** O campo `termsAccepted` é obrigatório e deve ser `true`.
- **Avatar:** Como o cadastro inicial não pede foto, o backend deve salvar o `avatarUrl` como `null` ou atribuir um avatar padrão (ex: DiceBear).
    
## LOGOUT
    
POST `/logout`

Request Body:

```json
{}
```

Exemplo de Resposta (200 OK):

```json
{
  "message": "Logout realizado com sucesso."
}
```
    
## Criação de Tarefa
    
POST `/tasks` (Criação)

**Request Body:**

```json
{
  "title": "Finalizar Telas de Login",
  "description": "Criar componentes React para Login e Cadastro",
  "status": "BACKLOG",
  "tag": "#FRONTEND",
  "startDate": "2026-01-23T10:00:00Z",
  "endDate": "2026-01-25T18:00:00Z",
  "responsibleId": "507f1f77bcf86cd799439011",
  "dependencyId": "65af8e12d3b4c56e89012345"
}
```

- **responsibleId:** Obrigatório. ID do usuário que cuidará da tarefa.
- **dependencyId:** Opcional. ID de outra tarefa que deve ser feita antes.

Resposta de Sucesso: `201 Created`

```json
{
  "id": "65af8e12d3b4c56e89012345", 
  "title": "Finalizar Telas de Login",
  "description": "Criar componentes React para Login e Cadastro",
  "status": "BACKLOG",
  "tag": "#FRONTEND",
  "startDate": "2026-01-23T10:00:00Z",
  "endDate": "2026-01-25T18:00:00Z",
  "responsible": {
    "id": "507f1f77bcf86cd799439011",
    "name": "Antonio Davi",
    "avatarUrl": "https://github.com/davisantos.png"
  },
  "dependency": {
    "id": "65af8e12d3b4c56e89012345",
    "title": "Configurar Repositório"
  }
}
```
    
## Edição de Tarefa
    
Este endpoint substitui os dados de uma tarefa existente pelos novos dados enviados.

**Endpoint:** `PUT /tasks/:id`

**Exemplo:** `PUT /tasks/65af8e12d3b4c56e89012345`

**Request Body (JSON)**

Exemplo de Mudança no campo “status”:

```json
{
  "title": "Finalizar Telas de Login",
  "description": "Criar componentes React para Login e Cadastro",
  "status": "DOING", 
  "tag": "#FRONTEND",
  "startDate": "2023-11-09T00:00:00Z",
  "endDate": "2023-11-10T23:59:59Z",
  "responsibleId": "507f1f77bcf86cd799439011",
  "dependencyId": "65af8e12d3b4c56e89012345"
}
```

**Resposta de Sucesso: `200 OK`**
O Backend retorna o objeto atualizado e com os relacionamentos populados (nome do responsável, título da dependência, etc).

Response Body:

```json
{
  "id": "65af8e12d3b4c56e89012345",
  "title": "Finalizar Telas de Login",
  "description": "Criar componentes React para Login e Cadastro",
  "status": "DOING",
  "tag": "#FRONTEND",
  "startDate": "2023-11-09T00:00:00Z",
  "endDate": "2023-11-10T23:59:59Z",
  "responsible": {
    "id": "507f1f77bcf86cd799439011",
    "name": "Antonio Davi",
    "avatarUrl": "https://github.com/davisantos.png"
  },
  "dependency": {
    "id": "65af8e12d3b4c56e89012345",
    "title": "Setup do Banco de Dados"
  }
}
```
    
## Previsão de prazo e dias gastos

Toda tarefa devolvida pela API (criação, edição e listagens) traz três campos calculados:

- **predictedDays:** previsão do `prazo_model`, em dias úteis. `null` enquanto não houver previsão.
- **predictedEffortHours:** esforço estimado pelo modelo, em horas.
- **daysTaken:** dias que a tarefa levou. Começa a contar ao sair do BACKLOG e congela ao chegar em DONE.

`startDate` é informado ao criar a tarefa (se não vier no `PUT`, o valor salvo é mantido). `endDate` **não é informado**: o backend calcula e ignora o que o cliente enviar. Ele é o último dia útil do prazo previsto contado a partir do `startDate` (sábado e domingo não contam, feriados não são considerados; 1 dia útil termina no mesmo dia). Se o `startDate` mudar, o `endDate` é recalculado com a previsão já salva, sem chamar o modelo de novo. Sem previsão, `endDate` fica `null`. Em BACKLOG `daysTaken` é sempre 0.

**Como a previsão é feita:** ao criar a tarefa (e ao editar responsável, complexidade ou prioridade) o backend chama `POST {PRAZO_MODEL_URL}/estimar-prazo` com:

| Campo enviado | Origem |
|---|---|
| `tarefa_id` | id da tarefa (só identifica; o modelo devolve o mesmo valor e o backend descarta a resposta se for outro) |
| `usuario_id` | e-mail do responsável (só identifica; não entra no cálculo) |
| `area` | `perfil_profissional.area` do responsável (sem perfil ou área livre = "Outro") |
| `horas_semanais` | `board_membro.weekly_hours` do responsável **naquele board** |
| `complexidade` | `tarefa.complexity` (vazia = "Média", até a IA definir) |
| `prioridade` | `tarefa.prioridade` (vazia = "Média") |

Sem `weekly_hours` do responsável no board não há previsão. Se o modelo estiver fora do ar a tarefa é salva normalmente e a previsão é tentada de novo na próxima edição. Variáveis: `PRAZO_MODEL_URL` (vazia desliga a previsão) e `PRAZO_MODEL_TIMEOUT` (segundos, padrão 5).

## Exclusão da tarefa
    
Este endpoint remove permanentemente uma tarefa do sistema.

**Endpoint:** `DELETE /tasks/:id`

**Exemplo:** `DELETE /tasks/65af8e12d3b4c56e89012345`

**Cabeçalhos (Headers)**
Authorization: `Bearer <token>` (Obrigatório)

Resposta de Sucesso: `200 OK`

Response Body:

```json
{ "message": "Tarefa excluída com sucesso" }
```
    
## Listagem de Tarefas
    
GET `/tasks`

**Regras de Status:** O campo `status` será sempre um Enum em caixa alta:

- **BACKLOG:** Tarefa aguardando início.
- **DOING:** Tarefa em execução.
- **DONE:** Tarefa finalizada.

**Relacionamentos:**

- **responsible:** Deve vir populado com `id`, `name` e `avatarUrl`.
- **dependency:** Deve vir populado com `id` e `title`.
- **Se uma tarefa não houver dependência, retornar null.**

Exemplo de Resposta (200 OK):

```json
{
  "tasks": [
    {
      "id": "65af9abc123456789",
      "title": "Configurar Banco de Dados",
      "description": "Criar schemas e realizar a primeira migração do sistema.",
      "status": "DOING", 
      "tag": "#BACKEND",
      "startDate": "2026-01-23T10:00:00Z",
      "endDate": "2026-01-25T18:00:00Z",
      "responsible": {
        "id": "507f1f77bcf86cd799439011",
        "name": "Antonio Davi",
        "avatarUrl": "https://github.com/davisantos.png"
      },
      "dependency": {
        "id": "65af8e12d3b4c56e89012345",
        "title": "Configurar repositório"
      }
    },
    {
      "id": "65af8e12d3b4c56e89012345",
      "title": "Configurar repositório",
      "description": "Configurar GitHub e permissões da equipe.",
      "status": "DONE", 
      "tag": "#DEV",
      "startDate": "2026-01-22T08:00:00Z",
      "endDate": "2026-01-22T12:00:00Z",
      "responsible": {
        "id": "507f1f77bcf86cd799439011",
        "name": "Pedro Henrique",
        "avatarUrl": "https://api.dicebear.com/7.x/avataaars/svg?seed=Pedro"
      },
      "dependency": null
    }
  ]
}
```
    
## Listagem de Usuários
    
GET `/users`

**Regras de Campos:**

- **avatarUrl:** O campo é obrigatório no JSON. Se o usuário não tiver uma imagem definida, o valor retornado deve ser `null`.

**Exemplo de Resposta `(200 OK)`:**

```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "name": "Antonio Davi",
    "email": "davi@gmail.com",
    "avatarUrl": "https://github.com/davisantos.png"
  },
  {
    "id": "65af8e12d3b4c56e89012345",
    "name": "Pedro Henrique",
    "email": "pedro.henrique@gmail.com",
    "avatarUrl": "https://api.dicebear.com/7.x/avataaars/svg?seed=Pedro"
  },
  {
    "id": "75bf9f23e4c5d67f90123456",
    "name": "João Silva",
    "email": "joao.silva@email.com",
    "avatarUrl": null
  }
]
```

