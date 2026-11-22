# Plano Diretor — Agenda Cultural do Rio de Janeiro
*(nome provisório)* · versão 0.1 · 15/11/2026

---

## 1. Missão

Devolver ao espaço público a informação sobre a vida cultural da cidade. A Agenda é uma ferramenta cívica, gratuita e aberta, inspirada no **direito à cidade**. Ela reúne, organiza e publica a programação cultural do Rio em formatos universais, sem cadastro, sem aplicativo proprietário, sem rastreadores e sem depender de redes sociais.

## 2. Princípios

1. **Contra o cercamento da informação.** Tudo o que publicamos é livre para ler, assinar, copiar e reutilizar.
2. **Equidade territorial.** Uma areninha em Santa Cruz tem o mesmo peso editorial de uma casa de shows no Leblon. Medimos o equilíbrio entre regiões e corrigimos ativamente os desequilíbrios.
3. **Gratuidade em destaque.** Eventos gratuitos e de preço popular são sempre sinalizados e podem ser filtrados.
4. **Rigor jornalístico.** Informação conferida, sem duplicatas, com sinopses escritas por nós.
5. **Simplicidade e durabilidade.** Escolhemos a tecnologia mais simples possível: barata, sem servidor e fácil de manter por muitos anos.

## 3. Escopo

- **Território:** município do Rio de Janeiro. A Região Metropolitana (Niterói, Baixada) fica para uma fase posterior, como seção separada.
- **Regiões:** adotamos a mesma divisão usada pela Secretaria Municipal de Cultura: **Centro · Zona Sul · Zona Sudoeste · Zona Norte · Zona Oeste**. Cada evento traz também o bairro.
- **Periodicidade:** edição semanal de **quinta a quarta-feira**, o mesmo ciclo da programação oficial da Prefeitura. O calendário assinável é atualizado continuamente.

## 4. Critérios editoriais

### Entra
Apresentações e atividades culturais **abertas ao público** nas seis áreas:
**Música · Teatro (inclui dança, circo e performance) · Artes Visuais · Cinema · Livros & Debates · Festas & Feiras · Infantil.**

Ajustes de 16/11/2026:
- **Livros & Debates** substitui "Literatura & Debates". Reúne lançamentos, saraus, clubes de leitura, palestras, seminários e rodas de conversa.
- **Festas & Feiras** é a sétima seção: festas populares, cortejos, carnaval de rua e feiras com programação cultural clara. Feiras essencialmente de consumo continuam de fora. A seção só aparece no site quando a edição tem eventos nela.
- **"Na rua"** não é seção, é uma marca transversal, como "Grátis": vale para qualquer atividade ao ar livre ou em espaço público (praça, parque, rua, área externa), de qualquer seção. Tem filtro e calendário próprios. Só é marcada quando a fonte indica que a atividade é ao ar livre.
Também entram exposições em cartaz, rodas de samba e choro, bailes de cultura negra e popular, saraus, cineclubes, lançamentos de livros, festivais e grandes eventos culturais da cidade.

### Fica de fora
- Venda de produtos e feiras essencialmente de consumo (moda, gastronomia, bazar). Exceção: quando há programação cultural clara.
- Cursos e workshops pagos, eventos corporativos, competições esportivas e festas privadas.
- Apresentações internas de escolas, academias e cursos (festivais de fim de ano, competições internas), salvo quando claramente abertas ao público geral.
- Eventos sem data, local ou forma de acesso confirmados.

### Casos a decidir caso a caso
- **Oficinas gratuitas e abertas:** podem entrar numa seção futura de "Formação", fora do fluxo principal.
- **Atividades permanentes** (troca de livros, exposições de longa duração): aparecem como "Em cartaz", sem repetir o evento todos os dias.

### Regras de redação
- Sinopses **próprias**, curtas (2 a 3 linhas), informativas e sem adjetivo publicitário. Datas, horários, preços e locais são fatos e podem vir de qualquer fonte. Textos de terceiros nunca são copiados.
- Quando o mesmo evento aparece em mais de uma fonte, guardamos **um único registro** e anotamos as fontes. A fonte oficial do espaço prevalece.

### Faixas de preço
- **Grátis**, incluindo os eventos com retirada de ingresso ou contribuição voluntária, sinalizados como tal.
- **Preço popular:** inteira até R$ 40.
- **Até R$ 80**
- **Acima de R$ 80**

## 5. Fontes: arquitetura em camadas

O mapa completo está em `dados/fontes.csv`. Ele tem 274 entradas, cada uma com área, bairro, região, esfera (pública, comunitária, privada…), método de coleta e situação de verificação.

| Camada | Papel | Exemplos |
|---|---|---|
| **Núcleo** (203) | Espinha dorsal, coletada toda semana | Rede municipal (PDF semanal da SMC), equipamentos estaduais e federais, Sesc, centros culturais, teatros, cinemas de rua, cineclubes, rodas de samba, livrarias, galerias |
| **Radar** (17) | Descobrir o que escapou ao Núcleo; nunca copiar texto | RioShow, Veja Rio, Time Out, agregadores, Agenda do Samba |
| **Plataformas** (24) | Fonte a liberar: extração prioritária dos fatos sobre eventos, devolvidos em formato aberto (ver estratégia abaixo) | Plataformas de ingresso (Sympla, Ingresso.com, Ticketmaster, Eventim etc.) |
| **Arquivada** (30) | Avaliada e deixada de fora, com o motivo anotado | Portais nacionais, feiras de consumo, duplicatas, fontes fora do município |

**Fonte-mestra:** a Secretaria Municipal de Cultura publica toda semana, em `cultura.prefeitura.rio/agendacultural`, um PDF com a programação de **toda a rede municipal**: 13 arenas e areninhas, centros culturais, teatros, museus e bibliotecas, organizada por região. Testamos a edição de 12 a 18/11/2026: são cerca de 60 atividades, quase todas com endereço, horário, preço e classificação. Sozinha, essa fonte cobre mais da metade dos equipamentos das Zonas Norte, Oeste e Sudoeste do nosso mapa.

**Canal aberto de envio:** vamos criar um formulário ou e-mail para espaços, coletivos, rodas e cineclubes enviarem a programação diretamente. É o caminho principal para quem só existe no Instagram e é coerente com a ideia de agenda como bem comum.

### Estratégia diante das plataformas de ingresso (decisão de 19/11/2026, corrigida no mesmo dia)

**A posição.** As plataformas de ingresso guardam como capital próprio uma informação de interesse público (o que acontece na cidade, onde, quando e por quanto) e restringem o acesso a ela para monetizá-la. São o principal ponto de sustentação do regime privado sobre a informação cultural a que o Largo se contrapõe. Nossa resposta é tratar essa informação como bem comum: extraí-la e devolvê-la ao público em formato aberto. A fundamentação está nas diretrizes políticas, seção 2.9.

**O que isso muda:**
1. **Extração como prioridade.** As plataformas deixam de ser só Apoio e passam a ser fonte a liberar. Encontrar meios de extrair a programação do Rio de Sympla, Ingresso.com, Ticketmaster, Eventim e demais é objetivo central do projeto.
2. **Sem parceria nem dependência.** Nenhuma carta, acordo de dados, afiliação ou comissão. Os meios de extração são nossos e documentados em aberto, para que qualquer pessoa possa repeti-los.
3. **O que se extrai: só fatos sobre eventos.** Nome, data, horário, local, preço, classificação e link. Nunca dados de pessoas (compradores, avaliações, perfis). Textos de divulgação não são copiados: as sinopses continuam nossas.
4. **Como se extrai: às claras.** O coletor se identifica como TodosOsRiosBot, com o endereço do projeto; lê só páginas e dados acessíveis sem login; visita com intervalo, sem sobrecarregar ninguém. Usamos o que já está exposto (dados estruturados nas páginas, interfaces de programação públicas, chaves gratuitas quando houver).
5. **Devolução ao comum.** O que for extraído entra na base sob ODbL, com a origem anotada em cada ficha. É a prova prática de que a informação pode circular aberta.
6. **Ir à fonte continua valendo.** A informação nasce em quem programa. Quando dá, a ficha é conferida com o espaço ou o produtor; a fonte do espaço prevalece em caso de divergência. Na ficha, o link principal é o do espaço; o de compra aparece limpo, sem código de comissão.
7. **Expor.** A cada edição, medir quantos eventos só tinham preço ou horário à vista dentro de uma plataforma, e quantos deles acontecem em espaço público ou com dinheiro público. É o retrato do cercamento, publicado junto com o painel de regiões e, agora, junto com os próprios dados liberados.
8. **Propor e politizar.** Somar ao pedido de dados abertos à Prefeitura (Lei de Acesso à Informação) uma proposta pública: a programação feita com dinheiro público deve ser publicada em formato aberto, como contrapartida, independentemente de onde o ingresso é vendido. O exemplo de Lisboa (seção 10) serve de precedente.
9. **Riscos conhecidos.** Datas, horários e preços são fatos, e fatos não têm dono. Mas os termos de uso das plataformas costumam proibir a leitura automática; a lei de direitos autorais protege a seleção e a organização de bases de dados; e as plataformas podem bloquear o coletor. Antes de dar escala ou visibilidade pública à extração, buscar orientação jurídica (clínicas de direito digital de universidades e organizações de direitos digitais costumam atender projetos sem fins lucrativos).

**Em funcionamento desde 19/11/2026:** a ronda diária extrai a grade dos cinemas de rua, de arte e públicos na Ingresso.com (vira fichas automáticas, sem IA) e os eventos do Rio na Sympla (a redação escolhe, com os critérios editoriais). Passo a passo em `documentos/protocolo-de-coleta.md`.

**Fever e Shotgun (teste de 22/11/2026):** a Fever está aberta: a página da cidade traz a vitrine do Rio (cerca de 60 ofertas) e cada evento tem dados estruturados com datas, horários, lugar e preço. Entrou na ronda diária no mesmo dia, com triagem automática (saem vales-presente, passeios turísticos e "localização secreta") e leitura da redação, como a Sympla. Achado: o Theatro Municipal vende parte da programação pela Fever (balé, Música no Assyrio, sessões na Sala Mário Tavares). A Shotgun responde a qualquer visita automática com uma verificação anti-robô (da Vercel); pelos nossos limites, não contornamos. Fica em espera: alternativas são a leitura assistida das páginas dos espaços que vendem por lá e o pedido direto aos produtores.

**Primeiro teste (19/11/2026):** Ingresso.com e Sympla estão abertas à extração; Ticketmaster barra robôs na entrada e sua chave oficial é incompatível com dados abertos; Eventim não respondeu da nuvem. Detalhes em `dados/coleta/plataformas-teste.md`.

**Decisões da coordenação editorial (19/11/2026):**
- **Nossos protocolos, não os delas.** O Todos os Rios não pauta sua atuação pelos parâmetros de empresas que operam sobre premissas opostas às suas. Nas plataformas de ingresso, o coletor não segue as regras para robôs que elas publicam. Os limites que valem são os nossos (itens 3 e 4 acima): só fatos sobre eventos, nunca dados de pessoas, identificação aberta, sem sobrecarga, sem login e sem romper barreiras técnicas de acesso (senhas, verificações anti-robô, bloqueios). Este último limite é também o ponto em que o risco jurídico deixa de ser contestação de termos de uso e passa a ser outra coisa. Para as demais fontes (espaços, produtores, poder público), o coletor continua obedecendo às regras para robôs de cada site.
- **Chaves de acesso.** Ferramentas oficiais das plataformas podem ser usadas desde que não restrinjam o uso dos dados. A da Ticketmaster só entra depois de lidos os termos: eles podem ser mudados sem aviso e a licença pode ser cassada a qualquer momento; se proibirem guardar ou redistribuir os dados em formato aberto, a chave fica de fora e a extração segue pelas páginas públicas.

**Equilíbrio territorial (situação atual):** no Núcleo, 55 fontes ficam nas Zonas Norte, Oeste e Sudoeste, contra 127 no Centro e na Zona Sul. A meta da primeira fase é chegar a pelo menos **40%** de fontes fora do eixo Centro–Zona Sul. A cada edição publicaremos um pequeno painel de distribuição por região.

## 6. Ficha de cada evento

Título · área(s) · data(s) e horário · local · endereço · bairro · região · faixa de preço / gratuidade · classificação indicativa · acessibilidade (Libras, audiodescrição, acesso sem escadas), quando informada · sinopse própria · link oficial · fontes consultadas · data da última verificação.

## 7. Como o sistema funciona (visão simples)

```
 Fontes (PDF SMC, sites, envios, leitura assistida)
            │  coleta semanal
            ▼
 Base de eventos (um arquivo de dados aberto)
            │  curadoria: limpar, juntar duplicatas, classificar, escrever sinopses
            ▼
 ┌──────────────┬────────────────────────┬──────────────────────┐
 │ Site público │ Calendários assináveis │ Dados abertos        │
 │ (celular 1º) │ (iPhone, Android, PC)  │ (CSV/JSON p/ reuso)  │
 └──────────────┴────────────────────────┴──────────────────────┘
```

- **Site estático:** páginas prontas, sem servidor nem banco de dados. Abre rápido mesmo com sinal fraco, não tem rastreador e tem busca e filtros (dia, área, região, bairro, grátis).
- **Instalável como aplicativo (22/11/2026):** no celular, "Adicionar à tela de início" instala o site como app, sem loja nem cadastro: ícone próprio ("R." da marca), abre em tela cheia e, sem internet, mostra a última edição que o aparelho abriu. Com sinal, sempre busca a versão mais nova. Nada é enviado de volta; calendários e dados abertos seguem direto da rede.
- **Compartilhar um evento (22/11/2026):** cada ficha tem o botão "Compartilhar". No celular, abre a lista de apps do próprio aparelho (WhatsApp, Telegram, e-mail etc.); onde ela não existe, abre o WhatsApp. A mensagem leva título, dia e hora, lugar, bairro, preço e um link que abre o site direto naquele evento, com a ficha aberta. Nenhum botão ou código de rede social é carregado no site. Ao lado, o botão "Mais informações" abre uma busca na web (Google) com o título entre aspas, o lugar e a cidade; é só um link, nada do buscador é carregado no site. Na grade de cinema (decisão de 22/11/2026), cada horário é um botão de ingresso que leva direto à compra daquela sessão na Ingresso.com, com link limpo, sem código de parceria; e cada filme tem um "Saiba mais" que busca o título entre aspas com a palavra "filme". A coordenação editorial considera o link de compra uma contrapartida justa, já que a grade vem da extração da Ingresso.com.
- **Calendários assináveis**, no formato universal de agenda: só dois, "A boa" (destaques) e "Todos os eventos" (decisão de 19/11/2026; os calendários por seção e região saíram). A assinatura é direta: um toque para iPhone e Mac, um para o Google Agenda e "copiar endereço" para os demais. A pessoa assina uma vez e recebe as atualizações sozinha. Quem quiser um recorte usa os filtros e "Levar para minha agenda".
- **Hospedagem gratuita (GitHub Pages)**, com uma cópia espelhada no Codeberg, uma plataforma sem fins lucrativos, por resiliência e autonomia. O site é um conjunto de arquivos estáticos e pode mudar de casa a qualquer momento.
- **Custos:** começa em **R$ 0**. O único gasto recomendado é um domínio **.com.br** (R$ 40 por ano no Registro.br) no lançamento público. O domínio dá um endereço próprio e estável que não muda se a hospedagem mudar. Um domínio **.rio** é opcional e simbólico (cerca de US$ 30 por ano, exige endereço na cidade).
- **Licenças abertas, com cláusula de compartilhamento pela mesma licença.** Os textos usam **CC BY-SA 4.0** e a base de dados usa **ODbL 1.0**. Qualquer pessoa ou instituição pode copiar, reutilizar e adaptar, inclusive para fins comerciais. A condição é citar a fonte e manter abertas as obras derivadas. Assim a licença impede que a agenda volte a ser cercada.
- **Protocolo de Acesso Aberto:** uma página pública que formaliza esses compromissos. Ela lista:
  - as licenças;
  - os formatos oferecidos (site, calendários, CSV/JSON);
  - a ausência de rastreadores, cadastro e publicidade;
  - a origem de cada informação;
  - a política de correções;
  - o compromisso de manter os endereços estáveis, para que quem reutiliza os dados não seja pego de surpresa.

### Identidade (proposta em discussão)
**Todos os Rios** — *Agenda cultural do Rio de Janeiro* (decisão de 19/11/2026; substitui o nome provisório Largo). A cidade é um grande rio feito de muitos afluentes: cada areninha, roda, cineclube, teatro e museu é um deles, e a agenda é onde todos se encontram, com o mesmo peso. Endereços: todososrios.rio (principal) e todososrios.com.br (leva ao principal). Versões para visitantes: *What's on in Rio* e *Agenda cultural de Río*. Os destaques do dia se chamam **"A boa"** ("A boa de hoje", "A boa da segunda, 16/11", "A boa do sábado, 21/11"). A forma "Qualé a boa?" foi descartada em 16/11/2026 por soar caricata para um projeto com frente de incidência pública.

### "A boa": destaques e recomendações sem vigilância
Recomendações personalizadas que respeitam os princípios do projeto: **sem cadastro, sem login e sem rastreamento de comportamento.**
- **Escolha explícita:** a pessoa marca o que quer, ou seja, áreas (teatro, música…), tipos de espaço (livrarias, cineclubes, rodas de samba…), regiões ou bairros, "só grátis", dias e horários, e "programa com crianças". Recebe uma lista curta: *as boas de hoje / do fim de semana para você*.
- **As preferências ficam no próprio celular**, guardadas no navegador. Nada é enviado nem armazenado por nós.
- **Calendário sob medida:** as mesmas escolhas geram um endereço de calendário que a pessoa assina no celular (por exemplo "Teatro + Zona Norte + grátis"). A seleção vai embutida no próprio endereço, sem conta.
- **"Uma boa fora do seu radar":** cada lista traz uma sugestão de outra área ou região. Isso evita a bolha e reforça a circulação pela cidade.
- **"A boa" é a seleção de destaques do dia** (decisão de 15/11/2026, nome ajustado em 16/11). Fica no topo do site, antes da programação completa, com 1 a 6 destaques por dia, cada um com uma linha de "por que ir". Os destaques respeitam os filtros escolhidos pela pessoa e também têm calendário próprio para assinar.
- **Curadoria por IA com regras públicas**, conferidas automaticamente a cada edição pelo gerador. Uma regra só é cobrada quando o dia oferece opções para cumpri-la. As regras valem para cada dia:
  - pelo menos 3 regiões e 3 áreas;
  - pelo menos metade dos destaques grátis ou a preço popular;
  - no máximo 1 destaque por espaço;
  - sempre algum espaço público, comunitário ou sem fins lucrativos;
  - só eventos com status "conferido";
  - nunca patrocínio.

  Dentro das regras, pesam a relevância artística, a raridade (estreia, última sessão, evento único) e o valor de memória e território. Os destaques ficam em `destaques.json` e entram no relatório semanal. A coordenação editorial pode vetar ou trocar algum, mas não precisa: se ninguém mexer, eles saem como estão.
- **Fase posterior:** boletim semanal por seção (e-mail ou RSS), para quem quiser receber sem abrir o site.

### Roteiros (decisão de 17/11/2026; antes "Roteiros do Largo")
Passeios a pé organizados pelo próprio projeto, no espírito do direito à cidade. O primeiro formato previsto são roteiros pelo Centro histórico que articulam a história literária com a história afro do Rio, conduzidos por uma parceira convidada pela coordenação editorial (convite em andamento; o nome entra aqui quando ela aceitar). É também a única fonte de renda prevista: todo o resto continua de acesso livre.

Regras, para que os roteiros não comprometam a independência da agenda:
1. **Casa separada da curadoria.** Os roteiros têm retranca própria, identificada como programação do Todos os Rios. Nunca entram em "A boa" nem recebem tratamento de destaque na agenda. A regra "nunca patrocínio" vale também para nós mesmos.
2. **Preço no espírito do projeto.** Preço popular (inteira até R$ 40) ou vagas gratuitas em cada saída. O valor e o número de vagas são definidos pela coordenação editorial com a parceira.
3. **Inscrição sem cadastro nem rastreador.** A página mostra datas, ponto de encontro, vagas e preço. A inscrição é feita por mensagem direta com quem conduz o passeio, e o pagamento vai direto a ela (Pix). O site não guarda dado de ninguém nem tem sistema de pagamento. Se a procura crescer, a regra é revista.
4. **Transparência.** A página diz quem conduz, para onde vai o dinheiro e que os roteiros ajudam a manter o projeto.

**A conferir antes de anunciar passeio pago:** se a atividade exige registro de guia de turismo (Cadastur, Ministério do Turismo) ou se se enquadra como atividade educativa ou cultural.

### Divisão do trabalho: código comum × IA
- **Coleta mecânica (sem IA, custo zero):** baixar o PDF da SMC e ler os sites e os dados estruturados é tarefa de programas comuns. Eles rodam de graça num serviço de automação na nuvem. Só as fontes que bloqueiam acesso automático usam o navegador do computador do projeto.
- **IA apenas onde há julgamento:** classificar, juntar duplicatas, escrever sinopses e fazer a dupla checagem.
- A quota de uso de IA será medida na semana do protótipo e ajustada se necessário (modelos menores nas etapas de rotina, ou um orçamento próprio de uso).

## 8. Dupla checagem ("leitura em dupla")

O processo reproduz o método das redações, em que dois repórteres conferiam a agenda em voz alta: um lia a fonte, o outro conferia o tijolinho.

1. **Repórter A, o redator.** Lê a fonte original e preenche a ficha do evento. Para cada dado (data, hora, local, preço, classificação), guarda o **trecho exato da fonte** de onde o tirou.
2. **Repórter B, o conferente.** É uma instância independente, que não vê o raciocínio de A. Relê a fonte original e confere **campo por campo** o tijolinho final. O veredito de cada campo é *confere*, *diverge* ou *não encontrado na fonte*.
3. **Conferência mecânica, feita por regras e sem IA.** Verifica se:
   - a data cai dentro da semana;
   - o endereço bate com o cadastro do local;
   - o preço é coerente com a faixa indicada;
   - o horário é plausível;
   - o link funciona;
   - o evento não está duplicado.
4. **Mesa de exceções.** Quando há divergência, um terceiro passe relê a fonte. Se a dúvida persistir, o evento é publicado como *"a confirmar"*, com link para a fonte, ou fica retido.
5. **Auditoria por amostragem (opcional).** Toda semana, 10 eventos sorteados vão para a coordenação editorial conferir em cerca de 5 minutos. Isso mede a taxa de erro ao longo do tempo.
6. **Correção pública.** Cada evento tem um link "encontrou um erro?". As correções ficam registradas.

A coordenação editorial não revisa evento a evento. Recebe por semana só o **relatório de exceções** e a amostra de auditoria.

## 9. Rotina semanal (proposta)

| Quando | O quê |
|---|---|
| Quarta | Coleta: PDF da SMC (sai geralmente na quarta ou quinta), sites do Núcleo, envios recebidos, leitura assistida e varredura do Radar |
| Quarta/quinta | Curadoria: limpeza, deduplicação, classificação e sinopses. Revisão humana opcional |
| Quinta de manhã | Publicação da edição (quinta a quarta). Calendários e site atualizados |
| Durante a semana | Correções e acréscimos pontuais |

A coleta e a curadoria podem rodar como uma **tarefa agendada** feita por mim, com você revisando antes de publicar, se quiser.

## 10. Riscos e limites conhecidos

- **Sites que bloqueiam leitura automática.** O próprio site da SMC recusou acesso a partir do servidor na nuvem e só abriu pelo navegador do computador do projeto. Encaminhamento:
  - **No curto prazo:** coleta pelo app Claude aberto no computador do projeto.
  - **No médio prazo:** pedido formal à Prefeitura, via Lei de Acesso à Informação, para publicar a programação em formato aberto. Isso faz parte da dimensão de ativismo do projeto.
  - **Data.Rio (verificado em 15/11/2026):** não publica agenda de eventos. Tem cadastros de equipamentos culturais, desatualizados (2017 a 2022), que servem para conferir endereços e encontrar lacunas no mapa de fontes.
  - **Precedente:** Lisboa publica sua agenda cultural municipal como dado aberto, com API e licença CC BY 4.0.
- **Instagram.** Não permite coleta automática. Por isso usamos leitura assistida e o canal de envio.
- **Qualidade das fontes oficiais.** O PDF semanal mistura atividades abertas com apresentações escolares e até restos de e-mail. A curadoria filtra isso.
- **Continuidade.** O projeto só vale se for semanal. A arquitetura foi escolhida para custar zero e exigir pouca manutenção.

### Mudança no modo de trabalho (17/11/2026)

O app Claude foi desinstalado do computador do projeto. O trabalho passa a ser feito só pelo navegador. Consequências:
- **O projeto mora no GitHub**, em `github.com/miguelbconde/todososrios` (repositório público, criado em 17/11/2026). Ele substitui a pasta do computador e o `.zip`. O site publicado fica na pasta `docs/` e os documentos em `documentos/`. Imagens de referência de terceiros ficam fora do repositório.
- **Sem o navegador do computador para a coleta.** Os sites que bloqueiam o acesso a partir da nuvem, como o da Secretaria Municipal de Cultura, dependem de a coordenação editorial baixar o PDF semanal e anexá-lo na conversa (cerca de um minuto por semana). O pedido de dados abertos à Prefeitura fica ainda mais importante.
- Os sites que abrem pela nuvem continuam sendo lidos diretamente.

### Protocolo de início de conversa

Sempre que, numa conversa nova, o assunto for a coleta ou as fontes de programação, o Claude lembra a coordenação editorial do que precisa receber:
1. **O PDF semanal da Secretaria Municipal de Cultura** (cultura.prefeitura.rio/agendacultural, sai na quarta ou quinta), anexado na conversa.
2. **O repositório `miguelbconde/todososrios`**: se ele não estiver ligado à conversa, o Claude pede para ligá-lo.
3. **Qualquer programação recebida diretamente** de espaços e coletivos (mensagens, flyers, capturas de tela).

O Claude também avisa quais fontes não conseguiu abrir naquela semana, para que a coordenação decida se vale buscar à mão.

### Coleta automática (em funcionamento desde 19/11/2026)

A coleta mecânica prevista na seção 7 está montada. Um programa comum (`ferramentas/coleta/coletar.py`, sem inteligência artificial) roda toda quarta de manhã no serviço gratuito de automação do GitHub e pode ser disparado a qualquer hora.

- **Escada de leitura**, do mais limpo ao mais bruto: feed (RSS) do site; eventos em dados estruturados; calendário de eventos do WordPress; texto da página inicial, das páginas de programação e das páginas de cada evento.
- **Boas maneiras:** o coletor se identifica como TodosOsRiosBot, com o endereço do projeto, e obedece às regras que cada site publica para leitores automáticos.
- **Onde fica o texto recolhido:** num ramo temporário do repositório (`coleta-bruta`), fora do site e da linha principal, substituído a cada ronda. Esses textos pertencem aos sites de origem e não estão sob as licenças abertas do projeto. Na linha principal fica só o resumo da ronda (`dados/coleta/resumo.md`).
- **Primeira ronda (19/11/2026):** 103 fontes com site no cadastro; cerca de 52 lidas com programação e datas, 13 lidas sem datas à vista, 16 sem resposta (várias por endereço errado no cadastro) e 9 que recusam visitas vindas da nuvem, entre elas os teatros estaduais.
- **Ronda no computador:** o mesmo programa, rodado no computador da coordenação editorial, tenta só as fontes que a nuvem não conseguiu ler e gera um arquivo .zip para anexar na conversa. Não instala nada e não lê arquivos do computador.
- **Sesc:** em espera. O site barra leitores de inteligência artificial; a decisão de coletar ou de pedir a programação ao Sesc é da coordenação editorial.
- **Como o Claude lê:** nesta forma de trabalho o Claude não abre os sites diretamente; lê o que o coletor guardou.
- **Peneira:** um segundo programa comum (`ferramentas/coleta/peneirar.py`) separa, do texto recolhido, só os trechos que citam dias da semana da edição. É o que a redação lê; o resto fica de lado.
- **Primeira ronda no computador (19/11/2026):** das 24 fontes que a nuvem não leu, o computador da coordenação leu 5 (Uerj, Real Gabinete, Anita Schwartz, É Tudo Verdade e Imperator); 6 recusam a visita de qualquer lugar; 7 têm endereço que não existe e 6 têm o certificado de segurança vencido ou trocado, sinal de endereço errado no cadastro. O resumo fica em `dados/coleta/resumo-pc.md` e as 24 fontes estão anotadas no cadastro.
- **Primeiro cotejo (19/11/2026):** as duas rondas renderam 49 fichas novas para a edição de 19 a 25/11, de 23 fontes, todas com dia, hora e lugar tirados da fonte e passadas pelo conferente. Limites que apareceram: muitos sites não mostram preço nem horário de visitação na página que o coletor alcança; exposições de galeria quase nunca trazem horário; grades diárias de cinema (Grupo Estação, IMS) ficaram de fora; o IMS Rio está fechado para obras. O que a ronda acha fora do eixo Centro–Zona Sul ainda é pouco: é o retrato do cadastro, não da cidade.
- **Sesc:** o endereço geral do Sesc RJ (`sescrio.org.br`) entrou na mesma lista de espera do endereço de cultura, para o coletor não ler um e pular o outro.

### Atualização diária, versão 2 (decisão de 21/11/2026)

A tarefa diária de 19/11 parou em 20 e 21/11: o plano de uso acabou antes de ela começar, ela ainda apontava para o nome antigo do repositório e, sem ela, nada se publicava. Foi apagada e o sistema foi refeito do zero, com uma regra: **se o Claude falhar num dia, o site não para.**

- **Base permanente:** as fichas da redação ficam em `dados/fichas.json`, com todas as sessões. A edição de quinta a quarta não é mais escrita à mão: o robô a monta a partir da base, de hoje em diante, e às quintas a edição nova abre sozinha.
- **Robô (sem IA, gratuito, no GitHub):** depois da ronda das 4h17, monta a edição, refaz o cinema, completa "A boa" pela regra fixa nos dias sem destaque da redação, publica o site e escreve o boletim de saúde (`dados/coleta/saude.md`). Se a ronda falhar, se as plataformas vierem vazias ou se o Claude passar 2 dias sem entregar, abre um aviso no GitHub, que chega por e-mail.
- **Claude (tarefa diária curta):** lê só o que é novo, redige até 25 fichas por dia, confere, traduz, escolhe "A boa" e entrega com `ferramentas/entregar.py`, que recusa a ficha com problema grave. O que passar do teto fica em `dados/coleta/pendentes.json`, para o dia seguinte. Quem publica é o robô.
- Passo a passo em `documentos/protocolo-de-coleta.md` (versão 3); divisão de tarefas em `documentos/divisao-de-tarefas.md`.

## 11. Próximos passos

1. **Verificar as fontes do Núcleo** (status "a verificar"): confirmar endereços, canais e métodos, e desdobrar as linhas agrupadas.
2. **Protótipo com uma semana real** (19 a 25/11/2026): coletar, montar a base, gerar o site e os calendários para você testar no celular.
3. **Criar o canal de envio** e uma página "Envie sua programação".
4. **Publicar** (você cria uma conta gratuita de hospedagem; eu guio cada passo).
5. **Ampliar o território**: buscar ativamente fontes nas Zonas Norte, Oeste e Sudoeste até a meta de 40%.
6. **Roteiros**: depois do aceite da parceira, criar a retranca e a página dos roteiros (seção 7).
7. **Plataformas de ingresso** (estratégia da seção 5): feito em 19/11, a extração diária da Ingresso.com (fichas automáticas de cinema de rua, de arte e público) e da Sympla (lida pela redação com os critérios editoriais); falta testar a Eventim pela ronda no computador; marcar a origem nas fichas; montar o indicador de cercamento; buscar orientação jurídica; redigir a proposta pública de contrapartida em dados abertos, junto com o pedido à Prefeitura.

## 12. Decisões

**Tomadas (15/11/2026):**
- Escopo: município do Rio.
- Preço popular: inteira até R$ 40.
- Licenças abertas formalizadas num Protocolo de Acesso Aberto (CC BY-SA 4.0 para textos e ODbL 1.0 para dados, ver seção 7).
- Sem revisão humana evento a evento. Em seu lugar, dupla checagem automática, relatório de exceções e auditoria por amostragem (seção 8).
- Fazer pedido formal à Prefeitura (Lei de Acesso à Informação) para que a programação seja publicada como dado aberto.

**Tomadas (17/11/2026):**
- Aparência: Estudo B com a segunda paleta da paisagem vira o site principal, por enquanto (ver guia de design).
- Integração com o Google Agenda: botão de assinatura (o Google só permite assinar pelo computador) e botão "adicionar ao Google Agenda" em cada ficha. Exige cuidar da versão do site para computador.
- Roteiros: passeios próprios, com retranca separada da agenda e fora dos destaques (seção 7).

**Tomadas (19/11/2026):**
- Aparência: o site passa a ter modo claro (areia, mar e sol) e modo escuro (mar no fundo), com botão para alternar; substitui a decisão de 17/11 sobre o Estudo B. Uma linha sinuosa de desenho próprio toma o lugar dos fios duplos, e o dia selecionado vira uma forma orgânica (ver guia de design, versão 1.1).

- Buscadores (19/11/2026): o site tem três endereços, um por idioma (raiz em português, `en/` e `es/`), cada um com título e descrição próprios, aviso ao Google de que são versões do mesmo site, mapa do site e a marcação de eventos que o Google lê (schema.org), uma entrada por sessão; a grade de cinema fica fora dessa marcação. O endereço público está na constante `SITE` de `ferramentas/gerar.py` e precisa ser trocado quando o domínio próprio entrar no ar.
- Site em inglês e espanhol: as sinopses e o "por que ir" dos destaques são traduzidos (por IA, na mesma rodada da redação; o cinema sai traduzido sem IA); os títulos dos eventos ficam sempre no original. O logo volta ao início.
- Site: a busca fica logo abaixo do logo e procura em todos os dias da edição; as seções viram botões de filtro visíveis logo abaixo dela; a grade de cinema aparece num bloco próprio, agrupada por cinema; todos os cinemas da cidade entram, inclusive os de shopping.
- Plataformas de ingresso: a informação que guardam é bem comum. Extraí-la e devolvê-la em formato aberto passa a ser prioridade do projeto, sem parceria nem afiliação, só com fatos sobre eventos e nunca dados de pessoas. Nas plataformas, o coletor segue os nossos limites, não as regras para robôs delas; chaves oficiais só sem restrição ao uso dos dados (seção 5; diretrizes políticas, seção 2.9).

- Nome: **Todos os Rios**, no lugar do provisório Largo. Endereços todososrios.rio e todososrios.com.br, registrados pela coordenação editorial em seu nome (CPF). "A boa" continua; "Roteiros do Largo" passam a se chamar Roteiros.

- Repositório renomeado (19/11/2026): `github.com/miguelbconde/todososrios`; endereço provisório do site `miguelbconde.github.io/todososrios`. O todososrios.com.br tem repositório próprio (`miguelbconde/todososrios-com-br`), só com a página que encaminha para o site; enquanto o .rio não sai, encaminha para o endereço provisório.

**Tomadas (21/11/2026):**
- Atualização diária refeita do zero: robô publica sozinho; o Claude só entrega fichas, com teto diário; alarme por e-mail (seção 10).
- Fichas automáticas da rede municipal: a Sympla traz, com dia, hora e endereço, boa parte da programação de arenas, areninhas e teatros da Prefeitura (organizador "Município do Rio de Janeiro"). O robô publica sozinho a parte segura (shows, tributos, cineclubes, rodas de conversa, comédia, teatros municipais); dança, circo, oficinas e espetáculos de areninha, quase sempre apresentações de escola, ficam com a redação, que também pode vetar o que o robô publicou. O PDF da Secretaria continua sendo a fonte principal da rede, mas a semana já não fica vazia sem ele.

**Pendente:**
- todososrios.rio: a INWX ainda não concluiu o registro (faltava o CPF, informado em 19/11). Quando sair: cadastrar o DNS na INWX, pôr o arquivo CNAME em `docs/`, trocar a constante `SITE` de `ferramentas/gerar.py` e apontar o encaminhamento do .com.br para o .rio.
- todososrios.com.br: DNS cadastrado no Registro.br e Pages ligado em 19/11; falta marcar "Enforce HTTPS" quando ficar disponível.
