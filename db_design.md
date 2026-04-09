Design de Banco de Dados para Backend ClaraIA

- Autenticação e usuários (`/usuarios/signup`, `/usuarios/login`, `/usuarios/logout`)
- Criação, atualização, remoção e listagem de tarefas (`/tasks`)

Ou seja, vamos modelar:
- USUARIO
- BOARD (quadro de tarefas, ligação com usuário)
- TAREFA (ligada a BOARD e USUARIO)
- BOARD_MEMBRO (membros de um board, relação N:N entre BOARD e USUARIO)


Tabelas essenciais
------------------

1) USUARIO
----------
Representa o usuário autenticado utilizado em `/usuarios/signup`, `/usuarios/login` e como responsável de tarefas.

**Campos**
- `email` (PK, VARCHAR, index)
  - Chave primária atual do sistema.
  - Usado diretamente para login e para identificar o usuário em tokens JWT.
- `nome` (VARCHAR)
- `senha_hash` (TEXT)
- `avatar_url` (TEXT, NULL)
  - URL opcional do avatar do usuário, usada para preencher `avatarUrl` nas respostas de login.


2) BOARD
--------
Quadro de tarefas que pertence a um usuário.

**Campos**
- `id_board` (PK, BIGSERIAL)
- `nome` (VARCHAR)
- `usuario_email` (FK -> USUARIO.email, NOT NULL)

**Motivação e relação com o código**
- O modelo `models.Board` já existe com esses campos.
- O campo `id_board` é usado como chave estrangeira principal em `TAREFA`.
- Permite, no futuro, ter múltiplos boards por usuário sem alterar a lógica básica.

3) TAREFA
---------
Tabela central das rotas `/tasks`. Armazena os dados da tarefa com os campos necessários para o frontend atual.

**Campos principais**
- `id_tarefa` (PK, BIGSERIAL)
- `id_board` (FK -> BOARD.id_board, NOT NULL)
- `responsavel_email` (FK -> USUARIO.email, NOT NULL)
- `dependencia_id` (FK -> TAREFA.id_tarefa, NULL)

- `titulo` (VARCHAR, NOT NULL)
  - Corresponde a `title` nos schemas/JSON.
- `descricao` (TEXT, NULL)
  - Corresponde a `description`.
- `status` (VARCHAR, NOT NULL)
  - Corresponde a `status` (BACKLOG, DOING, DONE).
- `tag` (VARCHAR, NULL)
  - Corresponde a `tag` (ex.: `#BACKEND`, `#FRONTEND`).
- `prioridade` (VARCHAR, NULL)
  - Corresponde a `prioridade` (baixo, médio, alto).
  - Campo opcional para definir a prioridade/complexidade da tarefa.
- `data_inicio` (TIMESTAMPTZ, NULL)
  - Corresponde a `startDate`.
- `data_fim` (TIMESTAMPTZ, NULL)
  - Corresponde a `endDate`.

**Motivação e relação com o código**
- O modelo `models.Tarefa` já utiliza:
  - `id_tarefa` como PK.
  - `id_board` para amarrar a tarefa a um board.
  - `responsavel_email` para ligar a tarefa a um `Usuario`.
  - `dependencia_id` para indicar outra tarefa da qual ela depende.
- Os schemas de tarefa (`TaskCreate`, `TaskUpdate`, `TaskOut`) mapeiam esses campos para o contrato da API:
  - `responsibleId` -> `responsavel_email`.
  - `dependencyId` -> `dependencia_id`.
  - `responsible` (objeto) -> join com USUARIO.
  - `dependency` (objeto) -> self-join com TAREFA.
  - `prioridade` -> `prioridade` (opcional).

**Índices recomendados**
- `IDX_tarefa_status (status)`
  - Melhorar filtros futuros por coluna (BACKLOG, DOING, DONE).
- `IDX_tarefa_responsavel (responsavel_email)`
  - Acelera listagens por responsável.
- `IDX_tarefa_board (id_board)`
  - Acelera listagens por board/usuário.


4) BOARD_MEMBRO
---------------
Tabela de associação que representa a relação muitos-para-muitos entre boards e usuários.
Permite que um board tenha múltiplos membros colaboradores além do dono, e que um usuário
seja membro de múltiplos boards.

**Campos**
- `id` (PK, INTEGER, index)
  - Chave primária da tabela de associação.
- `board_id` (FK -> BOARD.id_board, NOT NULL)
  - Referência ao board do qual o usuário é membro.
- `usuario_email` (FK -> USUARIO.email, NOT NULL)
  - Referência ao usuário que é membro do board.
- `tag` (VARCHAR, NULL)
  - Tag opcional associada ao membro neste board.
