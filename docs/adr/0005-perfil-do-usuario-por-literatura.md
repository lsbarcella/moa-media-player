# ADR-0005 — Perfil do usuário definido pela literatura

- **Status:** Aceito. O risco de projetar para um idoso "médio" é conhecido e deve ser declarado no TCC.
- **Data:** 26/11/2026
- **Decisor:** autor do TCC

## Contexto

Os documentos nunca descreviam quem é o usuário em termos de visão, audição, motricidade e cognição. Não sabemos se o pai do autor tem tremor, catarata, aparelho auditivo ou perda de memória. Uma conferência com a literatura mostrou que boa parte das diretrizes disponíveis é voltada a **demência** (Sheffield, AMI), o que não se aplica ao nosso caso. Gregor, Newell e Zajicek (*User Sensitive Inclusive Design*, ASSETS 2002) alertam que a diversidade entre idosos é muito grande e que é preciso especificar as características do grupo-alvo.

## Alternativas

| Alternativa | Prós | Contras | Resultado |
| --- | --- | --- | --- |
| P1. Questionário respondido pelo autor | Rápido (cerca de 15 min); não depende dele | É a percepção do autor, não a medida | Não escolhida |
| P2. Observação curta com o usuário | Dados reais; base para o M9 | Depende dele; pode exigir TCLE | Não escolhida |
| **P3. Só literatura** | Imediato; sem questão ética agora | É a mais fraca: projeta para um idoso "típico" | **Escolhida** |
| P4. Questionário e depois observação | Cobre as duas fontes | Mais etapas | **Recomendada pela IA; não escolhida** |

## Decisão

Definir o perfil **pela literatura**. O usuário-alvo é um idoso típico, **sem demência**, com o declínio esperado de:

- **visão:** precisa de texto grande e contraste alto;
- **audição:** perda maior nos agudos (ver ADR-0004);
- **precisão motora:** clique único, alvos grandes, sem duplo clique nem arrastar;
- **memória de trabalho:** poucas escolhas, estado sempre visível, caminho de volta fixo.

**Fora do escopo:** pessoas com demência. As diretrizes de demência servem de inspiração, e não de regra.

## Consequências

- **Positivas:** destrava o desenho sem depender de coleta de dados agora.
- **Negativas e riscos:**
  - O desenho pode ficar ajustado a um idoso "médio" e errar para o usuário real (por exemplo, se ele usa touchpad, tem tremor ou usa aparelho auditivo).
  - Parte da literatura consultada vem de resumos de busca, e os estudos têm amostras pequenas.
  - O M9 (avaliação) passa a ser a **primeira medida real** do usuário. Isso deve ser declarado como limitação: um participante é um estudo de caso, não é generalizável.
- **Mitigação:** controles que o próprio usuário pode ajustar ("Voz mais clara"; controle de tamanho de letra, ainda em aberto) reduzem a dependência de acertar o perfil na primeira tentativa.
- **Já esclarecido pelo autor:** o usuário usa **mouse** (não touchpad), o que reduz um dos riscos apontados pela literatura.
- **Pendências:** as especificações do notebook seguem como decisão em aberto. Se o M9 envolver coleta de dados com o usuário, confirmar com o orientador ou com o CEP da Uninter se é preciso TCLE ou avaliação ética (Resolução CNS 510/2016).

## Validação

Teste de usabilidade do M9 com o usuário real, registrando limitações. Se o resultado contradisser o perfil assumido, revisar este ADR.
