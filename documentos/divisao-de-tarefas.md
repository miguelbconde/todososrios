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

### 1. Robô (GitHub, todo dia às 2h07, sem IA)

- Visita as fontes do cadastro e guarda o texto fora do site.
- Extrai a grade da Ingresso.com e os eventos da Sympla, da Fever e da Uhuu (desde 24/11/2026), já triados por regra, e lê as agendas do Sesc RJ e do Arte que Acontece (desde 22/11/2026, por padrão), o roteiro de música clássica da Revista CONCERTO (desde 24/11/2026, por padrão) o calendário oficial da Riotur (desde 25/11/2026, como radar de fatos) e, desde 25/11/2026, a Bilheteria Digital, o AllEvents e o feed do Visit Rio (os dois últimos como radar de fatos).
- Monta a programação a partir da base de fichas, de hoje até dois meses à frente (desde 22/11/2026; antes, edição semanal de quinta a quarta).
- Refaz a grade de todos os cinemas.
- Completa "A boa" nos dias que não têm destaque escolhido pela redação, com regra fixa: o show do dia (preferindo as casas que recebem grandes nomes), um na rua e um da seção da vez, com pelo menos um fora do eixo Centro–Zona Sul quando houver.
- Publica o site, os calendários e os dados abertos.
- Publica de novo sempre que o Claude entrega fichas.
- Escreve o **boletim de saúde** (`dados/coleta/saude.md`).
- **Alarme:** se a ronda falhar, se as plataformas vierem vazias ou se o Claude passar 2 dias sem entregar, registra no boletim e abre um aviso no GitHub ("Alarme do robô"), que se fecha sozinho quando tudo volta ao normal. Esse aviso não chega por e-mail: quem leva o alarme à coordenação é a notificação de celular da tarefa diária do Claude (ver abaixo).
- **Não redige nem publica fichas de evento sozinho** (decisão de 22/11/2026: a confiabilidade do site vem primeiro). O leitor automático da rede municipal na Sympla e dos palcos públicos na Fever fica desligado e só volta como último recurso, se o limite de uso tornar a redação inviável. A grade de cinema continua automática, porque vem pronta da Ingresso.com.

### 2. Claude, tarefa diária (todo dia às 5h43, sem conversa)

- Lê só o que é novo na ronda desde ontem, mais as pendências do dia anterior.
- Às quintas e sextas, incorpora o PDF da Secretaria, se ele estiver na pasta `entrada/`.
- Decide o que entra pelos critérios editoriais, redige **todas as fichas novas que cabem nos critérios, sem teto** (decisão de 22/11/2026), entregando em lotes, passa pela dupla checagem e traduz.
- Escolhe "A boa" dos próximos 7 dias que ainda não têm destaque (3 por dia: o show do dia, um na rua e um da seção da vez, com pelo menos um fora do eixo Centro–Zona Sul quando houver) e mantém "As boas do mês" (3 ou 4 atrações dos próximos dois meses que pedem compra antecipada, pesando atratividade e chance de esgotar).
- Entrega à base. A entrega recusa sozinha a ficha com problema grave, como data inválida, falta de endereço ou dado pessoal.
- Manda à coordenação o relatório de exceções e uma notificação no celular. A primeira linha é "Tudo certo:" ou "ALARME:" (lê os alarmes do boletim e confere se a ronda é do dia). **É o canal de alarme do projeto** (decisão de 23/11/2026).
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
- Se a notificação da manhã começar com "ALARME:", ou se não chegar notificação nenhuma até umas 8h, abrir uma conversa no Projeto e colar o aviso (ou dizer que não chegou).

**Decisões que só ele toma**
- Critérios editoriais, posicionamento público e parcerias.
- Fontes em espera (o Sesc saiu da espera em 22/11/2026).
- Passos de conta: domínios, HTTPS, permissões, plano de uso.

**O que ele não faz**
- Revisar evento a evento, mexer em código ou tomar decisões técnicas.

## Calendário

| Quando | O quê | Quem |
|---|---|---|
| Todo dia, 2h07 (o GitHub costuma atrasar até 1h30) | Coleta, montagem da edição, publicação, boletim, alarme | Robô |
| Todo dia, 5h43 | Fichas de texto corrido, conferência, "A boa", relatório | Claude (tarefa) |
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
| A tarefa do Claude não roda (limite de uso, erro) | O robô segue publicando o que está na base; a notificação da manhã não chega | Abrir conversa se não houver notificação até umas 8h |
| A ronda do robô falha | O site fica como estava; a notificação da manhã começa com "ALARME:" | Abrir conversa |
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
6. ~~Horário~~ (23/11: ronda adiantada para 2h07, para terminar antes da tarefa das 5h43 e a tarefa sempre ler a ronda do dia). **Revisar depois de uma semana** de funcionamento: horário da tarefa, consumo do plano.
