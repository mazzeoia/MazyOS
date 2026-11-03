import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Exclusão de Dados — CREATIVE ADS",
};

export default function DataDeletionPage() {
  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "48px 24px", fontFamily: "var(--font-body), sans-serif", color: "#1a1a1a", lineHeight: 1.7 }}>
      <h1 style={{ fontSize: "1.8rem", marginBottom: 8 }}>Solicitação de Exclusão de Dados</h1>
      <p style={{ color: "#666", marginBottom: 32 }}>CREATIVE ADS — Creative Agência Marketing LTDA</p>

      <h2>Como solicitar a exclusão dos seus dados</h2>
      <p>
        Se você deseja que todos os seus dados sejam removidos da plataforma CREATIVE ADS,
        incluindo dados de conta, tokens de acesso Meta e histórico de campanhas, siga
        uma das opções abaixo:
      </p>

      <h3>Opção 1 — Por e-mail</h3>
      <p>
        Envie um e-mail para <strong>contato@creativeagenciamkt.com.br</strong> com o assunto
        &quot;Exclusão de dados&quot; e informe o e-mail cadastrado na plataforma.
      </p>

      <h3>Opção 2 — Pela plataforma</h3>
      <p>
        Acesse <a href="/" style={{ color: "#e85d04" }}>ads.creativeagenciamkt.com.br</a>,
        faça login e entre em contato pelo suporte interno.
      </p>

      <h2>O que será excluído</h2>
      <ul>
        <li>Seu cadastro (e-mail, senha hash).</li>
        <li>Token de acesso Meta armazenado (criptografado).</li>
        <li>Contas de anúncios vinculadas.</li>
        <li>Campanhas sincronizadas e métricas de performance.</li>
        <li>Análises e relatórios gerados.</li>
        <li>Logs de auditoria relacionados à sua conta.</li>
      </ul>

      <h2>Prazo</h2>
      <p>
        A exclusão será processada em até <strong>30 dias</strong> após a solicitação.
        Você receberá uma confirmação por e-mail quando o processo for concluído.
      </p>

      <h2>Observações</h2>
      <ul>
        <li>A exclusão é irreversível. Todos os dados serão removidos permanentemente.</li>
        <li>Após a exclusão, o token Meta será revogado e não teremos mais acesso às suas contas de anúncios.</li>
        <li>Dados que já foram processados pelo Meta Ads (suas campanhas, anúncios) permanecem na plataforma Meta e não são afetados.</li>
      </ul>

      <h2>Contato</h2>
      <p>
        Creative Agência Marketing LTDA<br />
        E-mail: <strong>contato@creativeagenciamkt.com.br</strong>
      </p>
    </main>
  );
}
