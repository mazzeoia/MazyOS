import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Política de Privacidade — CREATIVE ADS",
};

export default function PrivacyPage() {
  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "48px 24px", fontFamily: "var(--font-body), sans-serif", color: "#1a1a1a", lineHeight: 1.7 }}>
      <h1 style={{ fontSize: "1.8rem", marginBottom: 8 }}>Política de Privacidade</h1>
      <p style={{ color: "#666", marginBottom: 32 }}>Última atualização: 29 de agosto de 2026</p>

      <p>
        A <strong>Creative Agência Marketing LTDA</strong> (&quot;Creative&quot;, &quot;nós&quot;) opera o serviço
        <strong> CREATIVE ADS</strong> (&quot;Plataforma&quot;), acessível em{" "}
        <em>ads.creativeagenciamkt.com.br</em>. Esta política descreve como coletamos,
        usamos, armazenamos e protegemos suas informações.
      </p>

      <h2>1. Dados que coletamos</h2>
      <ul>
        <li><strong>Dados de cadastro:</strong> e-mail e senha (hash criptográfico).</li>
        <li><strong>Dados do Meta Ads:</strong> ao conectar sua conta Meta, acessamos contas de anúncios, campanhas, conjuntos de anúncios, anúncios e métricas de performance (impressões, cliques, gastos, leads). Esses dados são obtidos via Meta Marketing API com as permissões que você autoriza.</li>
        <li><strong>Token de acesso Meta:</strong> armazenado com criptografia simétrica (Fernet/AES-128) no nosso banco de dados. Usado exclusivamente para consultar e gerenciar suas campanhas.</li>
        <li><strong>Dados de uso:</strong> ações realizadas na plataforma (sincronizações, avaliações, pausas de campanha) registradas em log de auditoria.</li>
      </ul>

      <h2>2. Como usamos seus dados</h2>
      <ul>
        <li>Exibir e gerenciar suas campanhas de anúncios.</li>
        <li>Gerar análises de performance e recomendações de otimização via inteligência artificial.</li>
        <li>Executar ações autorizadas por você (pausar, ativar campanhas).</li>
        <li>Manter logs de auditoria para segurança e transparência.</li>
      </ul>

      <h2>3. Compartilhamento de dados</h2>
      <p>
        Não vendemos, alugamos ou compartilhamos seus dados pessoais com terceiros para
        fins de marketing. Seus dados podem ser compartilhados com:
      </p>
      <ul>
        <li><strong>Meta Platforms, Inc.</strong> — para executar ações nas suas campanhas via API.</li>
        <li><strong>Anthropic (Claude AI)</strong> — dados agregados e anonimizados de campanhas são enviados para gerar análises inteligentes. Nenhum dado pessoal identificável é transmitido.</li>
        <li><strong>Supabase</strong> — provedor de banco de dados e autenticação (infraestrutura).</li>
      </ul>

      <h2>4. Armazenamento e segurança</h2>
      <ul>
        <li>Dados armazenados em servidores seguros com criptografia em trânsito (TLS) e em repouso.</li>
        <li>Tokens Meta criptografados com Fernet (AES-128-CBC + HMAC).</li>
        <li>Acesso restrito à equipe técnica da Creative.</li>
      </ul>

      <h2>5. Seus direitos</h2>
      <p>Conforme a LGPD (Lei Geral de Proteção de Dados), você tem direito a:</p>
      <ul>
        <li>Acessar seus dados pessoais.</li>
        <li>Corrigir dados incompletos ou desatualizados.</li>
        <li>Solicitar exclusão dos seus dados.</li>
        <li>Revogar o consentimento a qualquer momento.</li>
        <li>Solicitar portabilidade dos dados.</li>
      </ul>

      <h2>6. Exclusão de dados</h2>
      <p>
        Você pode solicitar a exclusão de todos os seus dados a qualquer momento
        acessando{" "}
        <a href="/data-deletion" style={{ color: "#e85d04" }}>
          ads.creativeagenciamkt.com.br/data-deletion
        </a>{" "}
        ou enviando e-mail para <strong>contato@creativeagenciamkt.com.br</strong>.
        A exclusão será processada em até 30 dias.
      </p>

      <h2>7. Cookies</h2>
      <p>
        Utilizamos apenas cookies essenciais para manter sua sessão autenticada.
        Não utilizamos cookies de rastreamento ou publicidade.
      </p>

      <h2>8. Alterações nesta política</h2>
      <p>
        Podemos atualizar esta política periodicamente. Alterações significativas
        serão comunicadas por e-mail ou pela plataforma.
      </p>

      <h2>9. Contato</h2>
      <p>
        Creative Agência Marketing LTDA<br />
        E-mail: <strong>contato@creativeagenciamkt.com.br</strong>
      </p>
    </main>
  );
}
