#!/usr/bin/env bash
# Publica o site no repositório (usado pelo robô do GitHub).
# Remonta a edição sobre a versão mais recente da linha principal e envia; se alguém enviou algo
# no meio do caminho, recomeça (até 3 vezes). Assim duas rodadas nunca brigam pelos arquivos do site.
# Uso: bash ferramentas/publicar.sh "<mensagem>" [plataformas.json]
set -u
msg="$1"; plat="${2:-}"
git config user.name "todososrios-robo"
git config user.email "todososrios-robo@users.noreply.github.com"
guarda=$(mktemp -d)
# Só a ronda (que passa o arquivo das plataformas) traz resumo novo para preservar. A publicação de fichas
# parte de um retrato antigo do repositório e não pode sobrescrever o resumo da ronda que veio depois.
if [ -n "$plat" ]; then
  cp dados/coleta/resumo.json dados/coleta/resumo.md dados/coleta/plataformas.md "$guarda"/ 2>/dev/null || true
fi
for tentativa in 1 2 3; do
  git fetch -q origin main && git reset -q --hard origin/main
  cp "$guarda"/* dados/coleta/ 2>/dev/null || true
  if ! python3 ferramentas/montar.py $plat; then
    echo "ALARME: o robô não conseguiu montar o site (o site ficou como estava)" >> alarmes.txt
    git reset -q --hard origin/main; cp "$guarda"/* dados/coleta/ 2>/dev/null || true
  fi
  python3 ferramentas/saude.py $plat >> alarmes.txt 2>&1 || echo "ALARME: o boletim de saúde falhou" >> alarmes.txt
  git add dados/coleta dados/edicoes dados/traducoes.json dados/robo.json docs
  git commit -qm "$msg" || { echo "nada mudou"; exit 0; }
  if git push -q origin HEAD:main; then echo "publicado"; exit 0; fi
  echo "a linha principal mudou durante a montagem; recomeçando ($tentativa)"
  sort -u alarmes.txt -o alarmes.txt
done
echo "ALARME: não consegui enviar o site ao repositório depois de 3 tentativas" >> alarmes.txt
exit 1
