# Divisão de tarefas do Todos os Rios

*Versão 1 · 21/11/2026 · em vigor. O passo a passo técnico está em `protocolo-de-coleta.md`.*

## Princípio

O site precisa se atualizar sozinho todo dia, com o mínimo de trabalho à mão. Para isso, o trabalho é dividido pelo tipo de esforço que exige:

- **O que é mecânico** (buscar, copiar fatos, montar e publicar o site) fica com um **robô** que roda de graça no GitHub. Ele não usa inteligência artificial e não gasta o plano do Claude.
- **O que pede julgamento** (ler texto corrido, decidir se entra, escrever a sinopse, conferir) fica com o **Claude**, numa tarefa diária curta.
- **O que melhora o sistema** (novas fontes, consertos, decisões) se resolve em **conversa** entre o Claude e a coordenação editorial.
- **O que só uma pessoa pode fazer** fica com a **coordenação editorial**.

Regra de segurança: **se o Claude falhar num dia, o site não para.** O robô continua publicando tudo o que já está na base, corta o que passou, refaz o cinema e escolhe "A boa" por uma regra fixa.

Meta de longo prazo: cada fonte que o robô aprende a ler sozinho sai da fila do Claude. A tarefa diária fica menor, mais barata e mais confiável a cada semana.

## Quem faz o quê

### 1. Robô (GitHub, todo dia às 4h17, sem IA)

- Visita as fontes do cadastro e guarda o texto fora do site.
- Extrai a grade da Ingresso.com e os eventos da Sympla, já triados por regra.
- Monta a edição de quinta a quarta a partir da base de fichas, de hoje em diante. Às quintas, a edição nova abre sozinha.
- Refaz a grade de todos os cinemas.
- Completa "A boa" nos dias que não têm destaque escolhido pela redação, com regra fixa: diversidade de regiões, áreas e espaços, prioridade para o grátis e o barato, para espaços públicos e para fora da Zona Sul.
- Publica o site, os calendários e os dados abertos.
- Publica de novo sempre que o Claude entrega fichas.
- Escreve o **boletim de saúde** (`dados/coleta/saude.md`).
- **Alarme:** se a ronda falhar, se as plataformas vierem vazias ou se o Claude passar 2 dias sem entregar, abre um aviso no GitHub ("Alarme do robô"), que chega por e-mail. O aviso se fecha sozinho quando tudo volta ao normal.
- Transforma em ficha, sozinho, os eventos da rede municipal que a Sympla publica com dia e hora certos e que ele reconhece com segurança: shows, tributos, cineclubes, rodas de conversa, comédia e teatros municipais. Desde 22/11/2026, faz o mesmo com os palcos públicos que vendem pela Fever (Theatro Municipal, Sala Mário Tavares, Sala Cecília Meireles). A sinopse é uma linha de fatos; o Claude pode vetar ou trocar por sinopse própria.

### 2. Claude, tarefa diária (todo dia de manhã, sem conversa)

- Lê só o que é novo na ronda desde ontem, mais as pendências do dia anterior.
- Às quintas e sextas, incorpora o PDF da Secretaria, se ele estiver na pasta `entrada/`.
- Decide o que entra pelos critérios editoriais, redige **todas as fichas novas que cabem nos critérios, sem teto** (decisão de 22/11/2026), entregando em lotes, passa pela dupla checagem e traduz.
- Revê os títulos das fichas automáticas novas: veta o que não cabe e dá sinopse própria às melhores.
- Escolhe "A boa" dos dias que ainda não têm destaque.
- Entrega à base. A entrega recusa sozinha a ficha com problema grave, como data inválida, falta de endereço ou dado pessoal.
- Manda à coordenação o relatório de exceções.
- Não mexe no código, no cadastro nem nas tarefas agendadas.

### 3. Claude, em conversa (quando a coordenação abrir, idealmente uma vez por semana)

- Lê o boletim de saúde e o histórico das entregas, e conserta o que quebrou.
- Ensina o robô a ler sozinho mais fontes, começando pelas que mais pesam na tarefa diária.
- Corrige endereços do cadastro e procura fontes novas, com prioridade para as Zonas Norte e Oeste.
- Incorpora o que a coordenação anexar.
- Atualiza os documentos do Projeto e do repositório.

### 4. Coordenação editorial (Miguel)

**Toda semana**
- Até quarta à noite, subir o PDF da Secretaria Municipal de Cultura na pasta `entrada/` do repositório: no site do GitHub, Add file → Upload files → Commit changes. Ou anexar numa conversa.

**Quando acontecer**
- Repassar, numa conversa, programação recebida diretamente que seja importante e não possa ser coletada no automático.
- Ler o relatório de exceções e responder só se quiser mudar algo.
- Se chegar e-mail de "Alarme do robô", abrir uma conversa no Projeto e colar o aviso.

**Decisões que só ele toma**
- Critérios editoriais, posicionamento público e parcerias.
- Fontes em espera (hoje: o Sesc).
- Passos de conta: domínios, HTTPS, permissões, plano de uso.

**O que ele não faz**
- Revisar evento a evento, mexer em código ou tomar decisões técnicas.

## Calendário

| Quando | O quê | Quem |
|---|---|---|
| Todo dia, 4h17 | Coleta, montagem da edição, publicação, boletim, alarme | Robô |
| Todo dia, de manhã | Fichas de texto corrido, conferência, "A boa", relatório | Claude (tarefa) |
| Logo depois da entrega | Nova publicação, já com as fichas do Claude | Robô |
| Quarta à noite | PDF da Secretaria em `entrada/` | Coordenação |
| Quinta | A edição nova abre sozinha; a tarefa do Claude incorpora o PDF | Robô e Claude |
| Uma vez por semana | Revisão da saúde das fontes e melhoria do robô | Claude e coordenação, em conversa |

## Relatório de exceções (formato fixo)

No máximo 10 linhas, em português simples:
1. Data, edição e resultado.
2. Fichas "a confirmar" e o motivo.
3. Eventos que ficaram de fora por falta de dado.
4. Quantos ficaram para o dia seguinte.
5. Fontes que falharam.
6. Decisões editoriais tomadas.
7. Às quintas e sextas: se o PDF da Secretaria estava lá.

## Quando algo falha

| Falha | O que acontece | O que a coordenação faz |
|---|---|---|
| Uma fonte cai | O site segue com as outras; o boletim registra | Nada |
| A tarefa do Claude não roda (limite de uso, erro) | O robô segue publicando o que está na base; o alarme dispara depois de 2 dias | Abrir conversa se o alarme chegar |
| A ronda do robô falha | O site fica como estava; o alarme dispara no mesmo dia | Abrir conversa |
| Falta o PDF na quinta | A edição abre sem a parte nova da rede municipal; o relatório avisa | Subir o PDF; ele entra no dia seguinte |

## Indicadores (no boletim de saúde)

- Fontes lidas com datas, sobre o total visitado.
- Fichas entregues por dia e fichas recusadas.
- Parcela de fichas fora da Zona Sul e de fichas grátis.
- Fichas automáticas da rede municipal (Sympla) e locais que o robô ainda não reconhece.

## Plano de reconstrução

1. ~~Diagnóstico~~ (21/11).
2. ~~Robô publica sozinho, com alarme~~ (21/11).
3. **Fontes organizadas:** feito em parte (21/11). O robô já lê sozinho a rede municipal na Sympla. Os dados organizados dos sites ainda são fracos demais para virar ficha sem erro. Próximos candidatos: temporadas da Sympla e sites que montam a agenda depois de abrir (Circo Voador, Blue Note, Caixa Cultural).
4. ~~Nova tarefa diária enxuta~~ (21/11).
5. ~~Tarefa antiga apagada~~ (21/11).
6. **Revisar depois de uma semana** de funcionamento: horário da tarefa, consumo do plano.
