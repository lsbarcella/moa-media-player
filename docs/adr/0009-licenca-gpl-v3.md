# ADR-0009 — Licença: GNU GPL versão 3 (software livre)

- **Status:** Aceito. Versão escolhida: **GPL v3 ou posterior** (`GPL-3.0-or-later`).
- **Data:** 26/11/2026
- **Decisor:** autor do TCC

## Contexto

O autor quer que o Moa Media Player seja **software livre**, e criou o repositório público `lsbarcella/moa-media-player` no GitHub com o texto da **GNU General Public License versão 3** (`LICENSE`). O projeto pretende ser distribuído como pacote `.deb` (marco M8), então a licença precisa ser compatível com todas as dependências.

## Alternativas

| Alternativa | Prós | Contras | Resultado |
| --- | --- | --- | --- |
| **GPL v3** | Copyleft forte: quem distribuir versões modificadas precisa manter o código aberto; compatível com as dependências; reconhecida como software livre | Impede que terceiros o incorporem em software proprietário | **Escolhida** |
| MIT ou BSD | Permissivas, simples | Não garantem que versões derivadas continuem livres | Descartada (o autor quer software livre) |
| LGPL ou MPL | Copyleft mais fraco | Pouco útil para um aplicativo final (são pensadas para bibliotecas) | Descartada |

## Decisão

Licenciar o código do Moa Media Player sob a **GNU GPL versão 3**. O arquivo `LICENSE` na raiz do repositório contém o texto oficial e **não é editado**: o texto da GPL pertence à Free Software Foundation, e alterá-lo o descaracterizaria. O nome do autor e o ano vão em outros lugares, como a própria licença orienta.

- **Titular dos direitos autorais:** Leonardo dos Santos Barcella, **2026**.
- **Versão:** GPL v3 **ou posterior** (identificador SPDX `GPL-3.0-or-later`).
- **Onde aparece:** no README e em um cabeçalho de três linhas no começo de cada arquivo-fonte (`.py` e `.sh`). O teste `tests/test_license_headers.py` falha se um arquivo novo ficar sem o cabeçalho.

**Compatibilidade das dependências** (conferida em 26/11/2026 nos arquivos instalados no Linux Mint e nos metadados do pacote):

| Dependência | Licença | Compatível com a GPL v3? |
| --- | --- | --- |
| mutagen | GPL v2 **ou posterior** (cabeçalho dos arquivos-fonte e metadados `GPL-2.0-or-later`) | Sim, pela cláusula "ou posterior" |
| PyGObject (`python3-gi`) | LGPL 2.1 ou posterior | Sim |
| GTK 3 | LGPL 2.1 ou posterior | Sim |
| GStreamer (plugins base e good) | LGPL 2 ou posterior | Sim |
| `sqlite3` e Python | Domínio público e licença PSF | Sim |

O arquivo de copyright do pacote Debian do mutagen escreve apenas "GPL-2", sem o "+". O texto-fonte e os metadados dizem "ou posterior", e é neles que esta conclusão se apoia. **Isso deve ser conferido de novo se a versão do mutagen mudar.**

## Consequências

- **Positivas:** o projeto é software livre; as dependências atuais não impedem a distribuição como `.deb`.
- **Negativas e riscos:**
  - **Dependências futuras precisam ser compatíveis.** Qualquer biblioteca nova deve ter a licença conferida no mesmo ADR que a introduzir (a regra de "sem dependências novas sem ADR" já exige isso).
  - **O código não pode copiar trechos de fontes com licença incompatível** (por exemplo, código proprietário ou GPL v2 somente).
  - **O que o app faz com o GStreamer:** codecs de áudio com patentes ou licenças próprias (por exemplo, MP3 e AAC) ficam por conta do sistema do usuário e não entram no nosso código. Isso é uma questão a olhar com cuidado no M7 (copiar CDs) e no M8 (empacotamento).
  - **Repositório público:** a documentação (ADRs, CLAUDE.md, diário de IA e ideação) fica visível para qualquer pessoa.
- **Mudanças no projeto:** seção "Licença" no README e regra no CLAUDE.md. Este ADR vale para o **código**; a arte do ícone é tratada à parte (ver Pendências).

## Pendências

- **Documentação** (CLAUDE.md, ADRs, diário de IA, ideação e preview): hoje não tem licença própria declarada. Vale decidir se segue a GPL ou uma licença de documentação livre (por exemplo CC BY-SA 4.0).
- **Licença do ícone da moa e das demais artes.** A GPL cobre o código. O desenho precisa ser **original ou de licença livre** (por exemplo, CC BY-SA 4.0), para o pacote inteiro continuar livre. Não usar imagens de terceiros sem conferir a licença.
- **Nome e marca:** a GPL cobre o código, não o nome. Hoje não há marca registrada, então nada impede que terceiros usem o nome "Moa Media Player" em versões modificadas. Se isso vier a importar, é uma decisão futura.
