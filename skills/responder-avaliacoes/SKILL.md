---
name: responder-avaliacoes
description: >
  Escreve respostas curtas e humanas pras avaliações do Google Meu Negócio.
  Mantém o padrão: nome do cliente, agradecimento variado, frase concreta sobre
  o produto/serviço da empresa, emoji opcional. Nada de resposta automática de
  empresa grande.
  Use quando o usuário disser "responder avaliação", "resposta pro Google",
  "tem uma avaliação nova", "me ajuda a responder essas reviews",
  "avaliação do GMB", ou colar texto/print de uma review do Google.
---

# /mazyos:responder-avaliacoes — Respostas pras avaliações do Google

## Dependências

- **Tom de voz:** `_memoria/preferencias.md`
- **Contexto do negócio:** `_memoria/empresa.md`

---

## Padrão de resposta

Respostas são **curtas** (1 a 2 frases), **pessoais** e **concretas**. Nada de resposta automática de empresa grande.

### Regras fixas

1. **Sempre citar o nome do cliente.** Primeiro nome, com capitalização correta (mesmo que o perfil esteja em minúsculo, ex: "jj nascimento" → "JJ"; "alexandre fior" → "Alexandre"). Se o nome for ambíguo ou parecer username, usar um agradecimento genérico caloroso sem forçar o nome.
2. **Sempre agradecer.** Variar: "Obrigado", "Muito obrigado", "Que bom", "Valeu" — pra não parecer robô.
3. **Frase concreta, não genérica.** Puxar algo específico da review ou algo da empresa (produto, processo, cuidado, tradição). Evitar "seu feedback é muito importante pra nós", "estamos sempre à disposição", "agradecemos a preferência".
4. **Emoji no final — opcional, na maioria das vezes sim.** Usar em reviews calorosas/elogiosas. Pular em reviews formais, curtas secas, ou críticas. Nunca mais de 1 emoji.
5. **Tom:** seguir `_memoria/preferencias.md`. Sem jargão de marketing. Sem "premium", "qualidade ímpar", "experiência diferenciada".

### Exemplos genéricos (adaptar ao negócio)

- Cliente (5★ "Produto excelente, recomendo.")
  → *"Obrigado [Nome]! Saber que o produto agradou é o nosso maior orgulho. 🤩"*
- Cliente (5★ "Atendimento ótimo")
  → *"Que bom que gostou do atendimento, [Nome]! Caprichamos em cada detalhe."*
- Cliente (5★ sem texto)
  → *"Muito obrigado pelo carinho, [Nome]."*

### Emojis do repertório

- **Calorosos (elogio):** 🤩 😊 🙏 ❤️
- **Específicos do nicho:** depende do negócio — comida 🔥👏🥩, beleza 💅✨ (com cuidado), serviços 👏🙌
- **Evitar (tom de marketing genérico):** ✨ 🎉 💯 🚀 (a menos que combine com o tom da marca em `_memoria/preferencias.md`)

---

## Workflow

### Passo 1 — Receber a(s) avaliação(ões)

O usuário vai colar texto, print ou lista de reviews. Extrair pra cada uma:
- Nome do autor
- Nota (estrelas)
- Texto da review (se tiver)

Se for print (imagem), ler e transcrever os dados antes de responder.

### Passo 2 — Escrever a resposta

Pra cada review, escrever **uma única resposta** seguindo o padrão acima.

**Calibrar pelo tipo de review:**

| Tipo | Abordagem |
|---|---|
| 5★ elogio específico (produto, atendimento) | Agradecer + eco da coisa elogiada + emoji caloroso |
| 5★ genérica/curta ("ótimo", "recomendo") | Agradecer + frase sobre cuidado/processo + emoji opcional |
| 5★ sem texto | Agradecimento curto pelo carinho, sem inventar contexto |
| 4★ elogio com ressalva | Agradecer + reconhecer o ponto levantado + compromisso simples, sem emoji |
| 3★ ou menos | **Parar e alinhar com o usuário antes de responder** — review negativa merece resposta sob medida. Não responder no automático. |

### Passo 3 — Entregar em formato fácil de copiar

Listar cada resposta abaixo da review, pronta pra colar no GMB. Formato:

```
**[Nome do autor]** — [estrelas] — "[trecho curto da review]"
→ [resposta]
```

Se forem muitas (5+), entregar em bloco corrido com separador claro entre cada uma.

### Passo 4 — Salvar o histórico (opcional)

Se o usuário pedir pra guardar, salvar em `marketing/avaliacoes-google/YYYY-MM-DD-respostas.md` com review + resposta publicada. Só criar a pasta se o usuário quiser registro. Não fazer por padrão.

---

## Regras

- Nunca copiar respostas idênticas pra reviews diferentes. Variar sempre.
- Não prometer nada que não depende só da empresa (logística terceirizada, prazo de fabricante, etc.).
- Não pedir que o cliente entre em contato por DM/telefone na resposta pública, a menos que o usuário peça (gera ruído na resposta).
- Não usar nome completo do cliente na resposta (só primeiro nome).
- Não mencionar concorrentes, mesmo se o cliente mencionar.
- Em reviews negativas: reconhecer, não se defender, oferecer canal privado só se o usuário autorizar.
